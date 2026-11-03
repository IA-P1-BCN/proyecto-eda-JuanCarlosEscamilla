"""Paso `download` del pipeline: bootstrap + refresco diario → CSV crudo + log.

Flujo (task download, pensado para correrse cada día):
1. Bootstrap: crawler del listado filtrado (Filtre: materia + proximidad) —
   pasa por la caché, re-ejecutar es barato y REANUDABLE.
2. RSS = DETECTOR de novedades/actualizaciones (1 petición, cacheada del día):
   cada id que aparece hoy en el feed → refetch FORZADO de su ficha; si el
   contenido cambió (hitos BOP nuevos en procesos conocidos) queda como evento
   `ficha_actualizada` en el log de calidad. Id nuevo → ficha nueva.
3. Fichas fuera del feed de hoy → caché normal (TTL para las viejas).
4. Escritura del CSV en formato largo + log JSONL (E1/E2/ficha_actualizada).

Un Ctrl-C (KeyboardInterrupt) guarda el CSV parcial y marca cortado=True:
la caché conserva el progreso y re-ejecutar continúa donde quedó.
El transporte se inyecta para tests; en producción es el ClienteHttp real.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .adjuntos import clasificar_estado
from .cache import CacheHtml, DescargaCacheada
from .client import ClienteAgotado, ClienteHttp
from .crawl import Filtre, crawl_listado
from .escribir import escribir_csv_raw, escribir_log_calidad
from .fichas import es_informatica, parse_ficha
from .rss import URL_FEED, parse_feed


@dataclass
class Resumen:
    fichas_descubiertas: int = 0
    cache_hits: int = 0
    fetched: int = 0
    procesos: int = 0
    descartadas_materia: int = 0
    hitos: int = 0
    actualizadas: int = 0
    cortado: bool = False


def _cliente(fetch=None, dormir=None, ahora=None) -> ClienteHttp:
    if fetch is not None:
        return ClienteHttp(
            fetch=fetch,
            dormir=dormir or (lambda s: None),
            ahora=ahora or (lambda: 0.0),
        )
    return ClienteHttp()


def _descarga(raiz: Path, *, ttl_dias: int = 7, hoy=None, fetch=None,
              dormir=None, ahora=None) -> DescargaCacheada:
    cliente = _cliente(fetch, dormir, ahora)
    return DescargaCacheada(cliente, CacheHtml(raiz / "html"),
                            hoy=hoy or date.today, ttl_dias=ttl_dias)


def _items_feed_tsv(raiz: Path) -> list[tuple[str, str]] | None:
    """Items del feed desde data/raw/feed_hoy.tsv (producido por feed_ids.sh).
    None si el TSV no existe o está vacío → el llamador usa el fallback Python."""
    tsv = raiz / "feed_hoy.tsv"
    if not tsv.exists():
        return None
    pares = []
    for linea in tsv.read_text().splitlines():
        if "\t" in linea:
            i, u = linea.split("\t", 1)
            pares.append((i.strip(), u.strip()))
    return pares or None


def _url_por_id(ruta_csv: Path) -> dict[str, str]:
    """Mapa id → fuente_url del CSV previo (para el refetch forzado del feed)."""
    if not ruta_csv.exists():
        return {}
    with ruta_csv.open(encoding="utf-8") as f:
        return {fila["proceso_id"]: fila["fuente_url"]
                for fila in csv.DictReader(f) if fila["proceso_id"]}


def _procesar_ficha(
    descarga: DescargaCacheada, url: str, resumen: Resumen, eventos: list[dict],
    progreso=None, i: int = 0, n: int = 0, pausa: float = 0.0, forzar: bool = False,
):
    """Descarga y parsea una ficha; devuelve el Proceso o None (con evento en el log).

    Emite el evento de progreso DESPUÉS de la descarga (con hit/status reales)
    y registra `ficha_actualizada` cuando el refetch forzado detecta cambios.
    """
    try:
        r = descarga.get(url, forzar=forzar)
    except ClienteAgotado:
        if progreso:
            progreso({"fase": "ficha", "i": i, "n": n, "url": url, "hit": False,
                      "status": "agotado", "pausa": pausa})
        eventos.append({"tipo": "E1", "url": url, "detalle": "agotado tras reintentos"})
        return None
    if progreso:
        progreso({"fase": "ficha", "i": i, "n": n, "url": url, "hit": r.hit,
                  "status": r.status, "actualizado": r.actualizado, "pausa": pausa})
    if r.actualizado:
        resumen.actualizadas += 1
        eventos.append({"tipo": "ficha_actualizada", "url": url,
                        "detalle": "contenido cambió — hitos nuevos probablemente"})

    if r.status >= 400:  # E1 (404/5xx) — logueado solo si vino de red, no de caché negativa
        if not r.hit:
            eventos.append({"tipo": "E1", "url": url, "detalle": f"status {r.status}"})
        return None
    estado = clasificar_estado(url, status=r.status)
    if estado:  # E2: portal genérico con 200
        eventos.append({"tipo": estado, "url": url, "detalle": "portal genérico"})
        return None
    try:
        proceso = parse_ficha(r.contenido.decode("utf-8", "ignore"), url)
    except Exception as e:  # noqa: BLE001 — HTML inesperado va al log, no tumba el pipeline
        eventos.append({"tipo": "ficha_no_parseable", "url": url, "detalle": str(e)[:120]})
        return None
    if not es_informatica(proceso):
        resumen.descartadas_materia += 1
        return None
    return proceso


def run(
    raiz: Path, *, filtre: Filtre = Filtre(), max_paginas: int | None = None,
    pausa: float = 1.0, ttl_dias: int = 7, progreso=None,
    fetch=None, dormir=None, ahora=None, hoy=None,
) -> Resumen:
    raiz = Path(raiz)
    eventos: list[dict] = []
    descarga = _descarga(raiz, ttl_dias=ttl_dias, hoy=hoy, fetch=fetch,
                         dormir=dormir, ahora=ahora)
    ruta_csv = raiz / "oposicions.csv"
    previas = _url_por_id(ruta_csv)
    resumen = Resumen()
    procesos: list = []

    try:
        urls_listado = crawl_listado(descarga, filtre, max_paginas, progreso=progreso)

        # ── RSS = detector: preferencia al TSV del script shell (curl+awk) ──
        items = _items_feed_tsv(raiz)
        if items is None:  # sin TSV → fetch + parse en Python (fallback)
            r_feed = descarga.get(URL_FEED, forzar=True)  # el detector SIEMPRE fresco
            items = parse_feed(r_feed.contenido.decode("utf-8", "ignore")) if r_feed.status == 200 else []
        urls_feed = {u for _, u in items}
        resumen.fichas_descubiertas = len(set(urls_listado) | urls_feed)

        # conocidas que aparecen hoy en el feed → refetch FORZADO (actualizaciones)
        conocidas_feed = sorted({u for i, u in items if i in previas})
        for i, url in enumerate(conocidas_feed, 1):
            _procesar_ficha(descarga, url, resumen, eventos,
                            progreso=progreso, i=i, n=len(conocidas_feed),
                            pausa=pausa, forzar=True)

        # TODAS las fichas (conocidas re-parseadas desde caché + nuevas) — el CSV
        # se reconstruye completo para no perder procesos fuera del feed de hoy
        pendientes = set(urls_listado) | urls_feed
        total = len(pendientes)
        ids_vistos: set[str] = set()
        for i, url in enumerate(sorted(pendientes), 1):
            forzar = url in urls_feed
            proceso = _procesar_ficha(descarga, url, resumen, eventos,
                                      progreso=progreso, i=i, n=total, pausa=pausa,
                                      forzar=forzar)
            if proceso is not None:
                if proceso.identificador and proceso.identificador in ids_vistos:
                    continue  # el mismo proceso llegó por feed (http→https) y listado
                ids_vistos.add(proceso.identificador)
                procesos.append(proceso)
                resumen.hitos += len(proceso.hitos)
    except KeyboardInterrupt:
        resumen.cortado = True
        if progreso:
            progreso({"fase": "corte",
                      "detalle": (f"INTERRUMPIDO tras {resumen.cache_hits} cache + "
                                  f"{resumen.fetched} fetched — reanuda con task download: "
                                  "la caché continúa donde quedó")})
    resumen.procesos = len(procesos)
    resumen.cache_hits = descarga.cache.hits
    resumen.fetched = descarga.cache.misses

    escribir_csv_raw(procesos, ruta_csv)
    escribir_log_calidad(eventos, raiz / "calidad.jsonl")
    return resumen
