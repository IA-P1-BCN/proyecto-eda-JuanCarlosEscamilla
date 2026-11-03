"""Scan RSS incremental: 1 petición diaria para descubrir procesos nuevos.

El feed (`/rss/oposicions/oposicions`) lista los ~1.000 procesos más recientes
(cubre ~2 meses) con el identificador en la descripción. El scan extrae esos
ids, los compara con los ya conocidos y devuelve SOLO los nuevos — el fetching
de sus fichas y el filtro de materia ocurren en el pipeline (download.py).

Límite documentado: el feed no garantiza reflejar hitos nuevos de procesos
antiguos; el full re-scan manual (crawler) es el complemento.

Gotcha verificado: la pubDate del feed es la hora de generación (cambia en
cada fetch) — NO sirve para detectar cambios; la señal es la pertenencia al
feed y el diff de identificadores.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from .cache import DescargaCacheada
from .parsers import IdentificadorInvalido, parse_identificador

URL_FEED = "https://cido.diba.cat/rss/oposicions/oposicions"
_RE_REF = re.compile(r"\b(\d{8}O\d{2})\b")


def parse_feed(xml: str) -> list[tuple[str, str]]:
    """(identificador, url_ficha) por item del feed; items corruptos se saltan."""
    out: list[tuple[str, str]] = []
    for item in ET.fromstring(xml).iter("item"):
        desc = item.findtext("description") or ""
        m = _RE_REF.search(desc)
        link = (item.findtext("link") or "").strip()
        if not m or not link:
            continue
        try:
            parse_identificador(m.group(1))  # valida que la fecha codificada exista
        except IdentificadorInvalido:
            continue
        out.append((m.group(1), link))
    return out


def scan_rss(
    descarga: DescargaCacheada, conocidos: set[str] | None = None, url_feed: str = URL_FEED
) -> list[tuple[str, str]]:
    """Ids+urls del feed que NO están en `conocidos` (únicos, ordenados)."""
    r = descarga.get(url_feed)
    if r.status != 200:
        return []
    conocidos = conocidos or set()
    nuevos: dict[str, str] = {}
    for id_proceso, link in parse_feed(r.contenido.decode("utf-8", "ignore")):
        if id_proceso in conocidos:
            continue
        nuevos[id_proceso] = link
    return sorted(nuevos.items())
