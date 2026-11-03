"""Caché HTML resumible: descarga una vez, relee siempre.

Clave = sha256 de la URL, ficheros .html bajo una raíz configurable
(`data/raw/html/` en producción). Solo se cachean respuestas 200 — un 404
o un 5xx agotado NO envenenan la caché y pueden recuperarse en la siguiente
ejecución. Los contadores hits/misses alimentan el log "fetched: N" del AC.
"""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path

from .client import ClienteHttp, Respuesta


class CacheHtml:
    def __init__(self, raiz: Path | str):
        self.raiz = Path(raiz)
        self.hits = 0
        self.misses = 0

    def _ruta(self, url: str) -> Path:
        return self.raiz / (hashlib.sha256(url.encode()).hexdigest() + ".html")

    def get(self, url: str) -> bytes | None:
        ruta = self._ruta(url)
        if ruta.exists():
            self.hits += 1
            return ruta.read_bytes()
        self.misses += 1
        return None

    def put(self, url: str, contenido: bytes) -> None:
        self.raiz.mkdir(parents=True, exist_ok=True)
        self._ruta(url).write_bytes(contenido)


class DescargaCacheada:
    """Fachada cache-first sobre el cliente educado.

    get(url) devuelve la Respuesta con `hit=True` si vino de disco (cero red).
    - 200 → se cachea (contenido).
    - 4xx → caché NEGATIVA con fecha: el mismo día cuenta como hit (la
      idempotencia no re-descarga enlaces muertos); al día siguiente se
      reintenta — la recuperación es posible.
    - 5xx agotado → sin caché: reintento inmediato del llamador puede prosperar.
    """

    def __init__(self, cliente: ClienteHttp, cache: CacheHtml, hoy=date.today):
        self.cliente = cliente
        self.cache = cache
        self.hoy = hoy

    def _ruta_err(self, url: str) -> Path:
        return self.cache.raiz / (hashlib.sha256(url.encode()).hexdigest() + ".err")

    def get(self, url: str) -> Respuesta:
        ruta_err = self._ruta_err(url)
        if ruta_err.exists() and ruta_err.read_text().strip() == self.hoy().isoformat():
            self.cache.hits += 1  # fallo conocido hoy: sin red
            return Respuesta(url=url, status=404, contenido=b"", hit=True)

        contenido = self.cache.get(url)
        if contenido is not None:
            return Respuesta(url=url, status=200, contenido=contenido, hit=True)

        r = self.cliente.get(url)
        if r.status == 200:
            self.cache.put(url, r.contenido)
        elif 400 <= r.status < 500:
            self.cache.raiz.mkdir(parents=True, exist_ok=True)
            ruta_err.write_text(self.hoy().isoformat())
        return Respuesta(url=r.url, status=r.status, contenido=r.contenido, hit=False)
