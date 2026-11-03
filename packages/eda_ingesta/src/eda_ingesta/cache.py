"""Caché HTML resumible: descarga una vez, relee siempre.

Clave = sha256 de la URL, ficheros .html bajo una raíz configurable
(`data/raw/html/` en producción). Solo se cachean respuestas 200 — un 404
o un 5xx agotado NO envenenan la caché y pueden recuperarse en la siguiente
ejecución. Los contadores hits/misses alimentan el log "fetched: N" del AC.
"""

from __future__ import annotations

import hashlib
import json
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

    def _ruta_meta(self, url: str) -> Path:
        return self.raiz / (hashlib.sha256(url.encode()).hexdigest() + ".meta")

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

    def meta(self, url: str) -> dict:
        ruta = self._ruta_meta(url)
        if not ruta.exists():
            return {}
        try:
            return json.loads(ruta.read_text())
        except json.JSONDecodeError:
            return {}

    def put_meta(self, url: str, meta: dict) -> None:
        self.raiz.mkdir(parents=True, exist_ok=True)
        self._ruta_meta(url).write_text(json.dumps(meta, ensure_ascii=False))


class DescargaCacheada:
    """Fachada cache-first sobre el cliente educado.

    get(url) devuelve la Respuesta con `hit=True` si vino de disco (cero red).
    - 200 → se cachea (contenido).
    - 4xx → caché NEGATIVA con fecha: el mismo día cuenta como hit (la
      idempotencia no re-descarga enlaces muertos); al día siguiente se
      reintenta — la recuperación es posible.
    - 5xx agotado → sin caché: reintento inmediato del llamador puede prosperar.
    """

    def __init__(self, cliente: ClienteHttp, cache: CacheHtml, hoy=date.today,
                 ttl_dias: int = 7):
        self.cliente = cliente
        self.cache = cache
        self.hoy = hoy
        self.ttl_dias = ttl_dias
        self.forzadas = 0

    def _ruta_err(self, url: str) -> Path:
        return self.cache.raiz / (hashlib.sha256(url.encode()).hexdigest() + ".err")

    def get(self, url: str, *, forzar: bool = False) -> Respuesta:
        """forzar=True (id presente en el feed de hoy) → refetch completo para
        detectar actualizaciones; el contenido previo se compara y el resultado
        marca actualizado=True si cambió."""
        hoy_iso = self.hoy().isoformat()

        if forzar:
            previo = self.cache.get(url)
            self.forzadas += 1
            r = self.cliente.get(url)
            if r.status == 200:
                actualizado = previo is not None and previo != r.contenido
                self.cache.put(url, r.contenido)
                self.cache.put_meta(url, {"checked": hoy_iso})
                return Respuesta(url=r.url, status=r.status, contenido=r.contenido,
                                 hit=False, actualizado=actualizado)
            return Respuesta(url=r.url, status=r.status, contenido=r.contenido, hit=False)

        ruta_err = self._ruta_err(url)
        if ruta_err.exists() and ruta_err.read_text().strip() == hoy_iso:
            self.cache.hits += 1  # fallo conocido hoy: sin red
            return Respuesta(url=url, status=404, contenido=b"", hit=True)

        contenido = self.cache.get(url)
        if contenido is not None:
            meta = self.cache.meta(url)
            if meta.get("checked") == hoy_iso:
                return Respuesta(url=url, status=200, contenido=contenido, hit=True)
            # validada hace >= TTL → re-fetch para detectar ACTUALIZACIONES
            # (hitos BOP nuevos en procesos antiguos); el servidor no soporta
            # ETag/Last-Modified → hay que pedir el cuerpo y comparar
            dias = (self.hoy() - date.fromisoformat(meta.get("checked", hoy_iso))).days
            if dias < self.ttl_dias:
                return Respuesta(url=url, status=200, contenido=contenido, hit=True)

        r = self.cliente.get(url)
        if r.status == 200:
            if contenido is not None and r.contenido == contenido:
                self.cache.put_meta(url, {"checked": hoy_iso})  # sin cambios
                self.cache.hits += 1
                return Respuesta(url=url, status=200, contenido=contenido, hit=True)
            actualizado = contenido is not None  # había copia y cambió → ACTUALIZACIÓN
            self.cache.put(url, r.contenido)
            self.cache.put_meta(url, {"checked": hoy_iso})
            return Respuesta(url=r.url, status=r.status, contenido=r.contenido,
                             hit=False, actualizado=actualizado)
        elif 400 <= r.status < 500:
            self.cache.raiz.mkdir(parents=True, exist_ok=True)
            ruta_err.write_text(hoy_iso)
        return Respuesta(url=r.url, status=r.status, contenido=r.contenido, hit=False)
