"""Carga y emparejamiento de la referencia de población municipal (US5·T1).

Fuente: Wikidata (SPARQL, ver .github/scripts/poblacio_wikidata.sh) — 951
municipios de Cataluña con población y coordenadas. Datos AGREGADOS públicos
(sin nada personal) → versionados en data/reference/.
"""

from __future__ import annotations

import csv
import unicodedata
from pathlib import Path

import difflib


def _norm(texto: str) -> str:
    """minúsculas sin acentos — para emparejar nombres de municipio."""
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip()


def municipi_desde_institucio(institucio: str) -> str | None:
    """'Ajuntament d\\'Alcover' → 'alcover'. None si no es un ajuntament municipal
    (Diputació, consells comarcals, entitats supramunicipals → sin match)."""
    if not institucio:
        return None
    t = _norm(institucio)
    # solo se quita el 'ajuntament …' — los artículos (la/les/el) SON parte del
    # nombre oficial ('la Roca del Vallès', 'el Vendrell'); 'del' = de+el → se
    # sustituye por 'el ' (contracción, no artículo)
    for prefix, repl in (("ajuntament del ", "el "), ("ajuntament de ", ""),
                         ("ajuntament d'", ""), ("ajuntament ", "")):
        if t.startswith(prefix):
            return (repl + t[len(prefix):]).strip() or None
    return None


def cargar_poblacio(ruta: Path) -> dict[str, dict]:
    """CSV de referencia → {municipio_normalizado: {poblacio, lat, lon, dist_km_vic, municipi}}"""
    out = {}
    with Path(ruta).open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            out[_norm(fila["municipi"])] = {
                "municipi": fila["municipi"],
                "poblacio": int(fila["poblacio"]),
                "lat": float(fila["lat"]),
                "lon": float(fila["lon"]),
                "dist_km_vic": float(fila["dist_km_vic"]),
            }
    return out


def enllacar_institucio(institucio: str, municipis: dict[str, dict]) -> tuple[dict | None, str]:
    """Empareja una institució con la referencia.

    Devuelve (match, método): exacto | fuzzy (≥0.85, marcado para revisión) | none.
    """
    municipi = municipi_desde_institucio(institucio)
    if municipi is None:
        return None, "no-es-ajuntament"
    if municipi in municipis:
        return municipis[municipi], "exacte"
    fuzzy = difflib.get_close_matches(municipi, municipis.keys(), n=1, cutoff=0.85)
    if fuzzy:
        return municipis[fuzzy[0]], "fuzzy"
    return None, "sense-match"
