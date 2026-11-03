"""Paso `download` del pipeline: bootstrap (crawler) + scan RSS → CSV crudo + log.

Orquesta los módulos de ingesta:
1. bootstrap: crawl del listado (materia 24) — pasa por la caché, resumible
2. scan RSS: diff de ids conocidos (CSV previo) → solo fichas nuevas
3. fetch + parse de cada ficha (filtro de materia EN la ficha)
4. escritura del CSV en formato largo + log de calidad JSONL (E1/E2/…)

El transporte se inyecta para tests; en producción el ClienteHttp real.
Re-ejecutar con caché caliente = 0 peticiones y CSV byte-idéntico (AC #3).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .adjuntos import clasificar_estado
from .cache import CacheHtml, DescargaCacheada
from .client import ClienteAgotado, ClienteHttp
from .crawl import Filtre, crawl_listado
from .escribir import COLUMNAS_RAW, escribir_csv_raw, escribir_log_calidad, fila_proceso_hito
from .fichas import es_informatica, parse_ficha
from .rss import scan_rss


@dataclass
class Resumen:
    fichas_descubiertas: int = 0
    cache_hits: int = 0
    fetched: int = 0
    procesos: int = 0
    descartadas_materia: int = 0
    hitos: int = 0
    cortado: bool = False


def _cliente(fetch=None, dormir=None, ahora=None) -> ClienteHttp:
    if fetch is not None:
        return ClienteHttp(
            fetch=fetch,
            dormir=dormir or (lambda s: None),
            ahora=ahora or (lambda: 0.0),
        )
    return ClienteHttp()


def _ids_conocidos(ruta_csv: Path, raiz: Path) -> set[str]:
    """Ids vistos: los del CSV (IT) + el estado de feed (incluye no-IT descartadas)."""
    ids: set[str] = set()
    if ruta_csv.exists():
        with ruta_csv.open(encoding="utf-8") as f:
            ids |= {fila["proceso_id"] for fila in csv.DictReader(f) if fila["proceso_id"]}
    estado = raiz / "ids_conocidos.txt"
    if estado.exists():
        ids |= set(estado.read_text().split())
    return ids


def _guardar_estado(raiz: Path, ids: set[str]) -> None:
    if not ids:
        return
    raiz.mkdir(parents=True, exist_ok=True)
    (raiz / "ids_conocidos.txt").write_text("\n".join(sorted(ids)) + "\n")


def _descarga(raiz: Path, fetch=None, dormir=None, ahora=None, pausa: float = 1.0) -> DescargaCacheada:
    cliente = _cliente(fetch, dormir, ahora)
    cliente.pausa = pausa
    return DescargaCacheada(cliente, CacheHtml(raiz / "html"))


def _procesar_ficha(
    descarga: DescargaCacheada, url: str, resumen: Resumen, eventos: list[dict],
    progreso=None, i: int = 0, n: int = 0, pausa: float = 0.0,
):
    """Descarga y parsea una ficha; devuelve el Proceso o None (con evento en el log).

    Emite un evento de progreso DESPUÉS de la descarga (con hit/status reales).
    """
    try:
        r = descarga.get(url)
    except ClienteAgotado:
        if progreso:
            progreso({"fase": "ficha", "i": i, "n": n, "url": url, "hit": False,
                      "status": "agotado", "pausa": pausa})
        eventos.append({"tipo": "E1", "url": url, "detalle": "agotado tras reintentos"})
        return None
    if progreso:
        progreso({"fase": "ficha", "i": i, "n": n, "url": url, "hit": r.hit,
                  "status": r.status, "pausa": pausa})
    if r.status >= 400:  # E1 (404/5xx) — logueado la 1ª vez; en hits de caché negativa se calla
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
    raiz: Path, *, filtre=Filtre(), max_paginas: int | None = None, pausa: float = 1.0,
    progreso=None,
    fetch=None, dormir=None, ahora=None,
) -> Resumen:
    """Bootstrap completo: crawler + RSS + fichas → CSV crudo + log de calidad.

    `progreso` (opcional) recibe un dict por página del listado y por ficha
    (fase, url, hit, status, i/n, pausa) — el CLI lo imprime en stderr.
    Un Ctrl-C (KeyboardInterrupt) guarda el CSV parcial y marca cortado=True:
    la caché conserva el progreso y re-ejecutar continúa donde quedó.
    """
    raiz = Path(raiz)
    eventos: list[dict] = []
    cliente = _cliente(fetch, dormir, ahora)
    cliente.pausa = pausa
    descarga = DescargaCacheada(cliente, CacheHtml(raiz / "html"))
    ruta_csv = raiz / "oposicions.csv"
    conocidos = _ids_conocidos(ruta_csv, raiz)
    resumen = Resumen()
    procesos: list = []
    urls_fichas: list[str] = []
    urls: set[str] = set()

    try:
        urls_fichas = crawl_listado(descarga, filtre, max_paginas, progreso=progreso)
        nuevos_rss = scan_rss(descarga, conocidos)
        urls = set(urls_fichas) | {u for _, u in nuevos_rss}
        _guardar_estado(raiz, conocidos | {i for i, _ in nuevos_rss})

        resumen.fichas_descubiertas = len(urls)
        total = len(urls)
        for i, url in enumerate(sorted(urls), 1):
            proceso = _procesar_ficha(descarga, url, resumen, eventos,
                                      progreso=progreso, i=i, n=total, pausa=pausa)
            if proceso is not None:
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
    nuevos_rss = scan_rss(descarga, conocidos)
    urls = set(urls_fichas) | {u for _, u in nuevos_rss}
    _guardar_estado(raiz, conocidos | {i for i, _ in nuevos_rss})

    resumen = Resumen(fichas_descubiertas=len(urls))
    procesos = []
    total = len(urls)
    for i, url in enumerate(sorted(urls), 1):
        proceso = _procesar_ficha(descarga, url, resumen, eventos,
                                  progreso=progreso, i=i, n=total, pausa=pausa)
        if proceso is not None:
            procesos.append(proceso)
            resumen.hitos += len(proceso.hitos)
    resumen.procesos = len(procesos)
    resumen.cache_hits = descarga.cache.hits
    resumen.fetched = descarga.cache.misses

    escribir_csv_raw(procesos, ruta_csv)
    resumen.cache_hits = descarga.cache.hits
    resumen.fetched = descarga.cache.misses
    escribir_log_calidad(eventos, raiz / "calidad.jsonl")
    return resumen


def run_scan(raiz: Path, *, pausa: float = 1.0, progreso=None, fetch=None, dormir=None, ahora=None) -> Resumen:
    """Refresco incremental: 1 petición al feed → añade SOLO fichas IT nuevas."""
    raiz = Path(raiz)
    eventos: list[dict] = []
    descarga = _descarga(raiz, fetch, dormir, ahora, pausa)
    ruta_csv = raiz / "oposicions.csv"
    conocidos = _ids_conocidos(ruta_csv, raiz)
    nuevos = scan_rss(descarga, conocidos)
    total = len(nuevos)
    for i, (_id, url) in enumerate(nuevos, 1):
        if progreso:
            progreso({"fase": "ficha", "i": i, "n": total, "url": url, "pausa": pausa})
    _guardar_estado(raiz, conocidos | {i for i, _ in nuevos})

    resumen = Resumen(fichas_descubiertas=len(nuevos))
    if not nuevos:
        resumen.cache_hits = descarga.cache.hits
        resumen.fetched = descarga.cache.misses
        return resumen

    añadidos = []
    for _id, url in nuevos:
        proceso = _procesar_ficha(descarga, url, resumen, eventos)
        if proceso is not None:
            añadidos.append(proceso)
            resumen.hitos += len(proceso.hitos)
    resumen.procesos = len(añadidos)

    if añadidos:
        ya_habia = ruta_csv.exists()
        with ruta_csv.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNAS_RAW)
            if not ya_habia:
                w.writeheader()
            for proceso in añadidos:
                for hito in proceso.hitos or [None]:
                    w.writerow(fila_proceso_hito(proceso, hito))
    escribir_log_calidad(eventos, raiz / "calidad.jsonl")
    return resumen
