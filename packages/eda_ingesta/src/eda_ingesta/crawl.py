"""Crawler del listado del CIDO: descubre fichas por materia y pagina hasta agotar.

Bootstrap de la ingesta: recorre las páginas del listado filtrado (materia 24)
y devuelve las URLs de ficha. Usa la caché de descarga — re-ejecutar el
bootstrap no re-pide las páginas ya guardadas. El scan RSS (rss.py) es el
complemento diario; este crawler es también el "full re-scan" manual.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .cache import DescargaCacheada

BASE = "https://cido.diba.cat"
URL_LISTADO = BASE + "/oposicions"
_RE_FICHA = re.compile(r"^/oposicions/\d+/[a-z0-9\-]+$")
_RE_TOTAL = re.compile(r"(\d+)\s+resultat")


def url_listado(materia: int = 24, pagina: int | None = None) -> str:
    """URL del listado filtrado por materia (Informàtica. Noves tecnologies = 24)."""
    url = (
        f"{URL_LISTADO}?ordenacio=DEFAULT&ordre=DESC&showAs=GRID"
        f"&filtreMateria%5Boptions%5D%5B0%5D={materia}"
    )
    return url + f"&page={pagina}" if pagina else url


def _sopa(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def extraer_fichas(html: str, base: str = BASE) -> list[str]:
    """URLs absolutas de fichas de la página (únicas y ordenadas)."""
    enlaces = {
        urljoin(base, a["href"])
        for a in _sopa(html).find_all("a", href=True)
        if _RE_FICHA.match(a["href"])
    }
    return sorted(enlaces)


def extraer_siguiente(html: str) -> str | None:
    """URL de la página siguiente del listado (None si es la última)."""
    for a in _sopa(html).find_all("a", href=True):
        href = a["href"]
        if href.startswith("/oposicions?") and "page=" in href:
            return urljoin(BASE, href)
    return None


def total_resultados(html: str) -> int | None:
    m = _RE_TOTAL.search(html)
    return int(m.group(1)) if m else None


def crawl_listado(
    descarga: DescargaCacheada,
    materia: int = 24,
    max_paginas: int | None = None,
    progreso: Callable[[dict], None] | None = None,
) -> list[str]:
    """Recorre el listado y devuelve todas las URLs de ficha (únicas, ordenadas).

    Para por: no hay página siguiente, una página sin fichas nuevas o
    max_paginas alcanzado. Cada página pasa por la caché — re-ejecutar no
    re-pide lo descargado. `progreso` recibe un dict por página
    (fase=listado, url, fichas) para UI/registrar.

    Regresión real (2026-11-03): el 'next' de las páginas 2+ del portal PIERDE
    el filtreMateria → el crawler caminaba el listado completo (1.536 procesos
    en vez de 237). Si la URL de paginación pierde el filtro, se reconstruye
    con url_listado(materia, page=N).
    """
    fichas: set[str] = set()
    paginas = 0
    url: str | None = url_listado(materia)
    while url and (max_paginas is None or paginas < max_paginas):
        r = descarga.get(url)
        if r.status != 200:
            break  # el log de calidad (T3.2/T3.3) registrará el fallo
        html = r.contenido.decode("utf-8", "ignore")
        nuevas = extraer_fichas(html)
        if not nuevas:
            break
        fichas |= set(nuevas)
        paginas += 1
        if progreso:
            progreso({"fase": "listado", "url": url, "pagina": paginas, "fichas": len(nuevas)})
        url = extraer_siguiente(html)
        if url and "filtreMateria" not in url:
            m = re.search(r"page=(\d+)", url)
            if progreso:
                progreso({"fase": "aviso", "detalle": "paginación perdió el filtro; reconstruida",
                          "url": url})
            url = url_listado(materia, int(m.group(1))) if m else None
    return sorted(fichas)
