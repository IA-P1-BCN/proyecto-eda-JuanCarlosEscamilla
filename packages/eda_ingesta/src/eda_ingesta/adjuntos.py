"""Clasificación de adjuntos: slug semántico + taxonomía de errores E1/E2/E3.

- Slug semántico: el tipo de documento vive en la URL cuando existe
  (listexamop, publtaubor, restexambo, proves…, dogc). Si no, None —
  el documento puede existir sin token (p.ej. bases_…pdf genérico).
- Estados:
  E1 — caído: 404/5xx tras reintentos o ClienteAgotado (acción: revisar)
  E2 — enlace genérico al portal/intranet del ayuntamiento, no al documento
       (acción: pedir enlace directo)
  E3 — documento descargado pero no parseable (se asigna en US5, PDFs)
"""

from __future__ import annotations

import re
from urllib.parse import unquote

_DOGC = ("portaldogc.gencat.cat", "dogc.gencat.cat")
_TOKENS = (
    "publtaubor",
    "restexambo",
    "listexamop",
    "listexam",
    "provescastel",
    "provescatala",
    "convosoposicio",
    "plantillapublicacioweb",
)
_RE_TALENT = re.compile(r"_([a-z]{6,})_(?:co|noindex|web)")
_PORTALES_GENERICOS = ("seuelectronica.", "eadministracio.", "/web/seleccio")


def clasificar_doc(url: str) -> str | None:
    """Token semántico del documento según la URL; None si no lleva ninguno."""
    u = unquote(url).lower()
    if any(d in u for d in _DOGC):
        return "dogc"
    for token in _TOKENS:
        if token in u:
            return token
    m = _RE_TALENT.search(u)
    return m.group(1) if m else None


def clasificar_estado(url: str, *, status: int | None = None, agotado: bool = False) -> str | None:
    """Estado del enlace: E1 (muerto), E2 (portal genérico) o None (ok)."""
    if agotado or (status is not None and status >= 400):
        return "E1"
    u = unquote(url).lower()
    if any(p in u for p in _PORTALES_GENERICOS):
        return "E2"
    return None
