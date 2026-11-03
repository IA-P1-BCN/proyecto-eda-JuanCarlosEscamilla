"""Caché HTML resumible: descarga una vez, relee siempre.

Clave = sha256 de la URL, ficheros .html bajo una raíz configurable
(`data/raw/html/` en producción). Solo se cachean respuestas 200 — un 404
o un 5xx agotado NO envenenan la caché y pueden recuperarse en la siguiente
ejecución. Los contadores hits/misses alimentan el log "fetched: N" del AC.
"""

from __future__ import annotations

import hashlib
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
    Solo se guardan respuestas 200: los fallos quedan re-descargables.
    """

    def __init__(self, cliente: ClienteHttp, cache: CacheHtml):
        self.cliente = cliente
        self.cache = cache

    def get(self, url: str) -> Respuesta:
        contenido = self.cache.get(url)
        if contenido is not None:
            return Respuesta(url=url, status=200, contenido=contenido, hit=True)
        r = self.cliente.get(url)
        if r.status == 200:
            self.cache.put(url, r.contenido)
        return Respuesta(url=r.url, status=r.status, contenido=r.contenido, hit=False)
