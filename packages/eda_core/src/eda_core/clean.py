"""Limpieza del dataset crudo (US4): normalización de categorías y dedup.

Funciones puras, test-first (tests/test_clean.py, fixtures_sucias.py):
los valores fuera de catálogo devuelven None — el llamador decide si los
manda al log de calidad. Decisiones registradas en docs/adr/0005.
"""

from __future__ import annotations

import re
from datetime import date

# Estat crudo del CIDO → catálogo canónico en castellano (deliverable ES)
_ESTAT_CATALOGO = {
    "Resolt": "resuelta",
    "Termini obert": "abierta",
    "Termini pendent": "pendiente",
    "Termini tancat": "cerrada",
    "Procés no vigent": "no vigente",
}

# Grupo de titulación: código inicial ('A1', 'A2', 'B', 'C1', 'C2', 'A'…)
_RE_GRUP = re.compile(r"^([A-Z][0-9]?)\s+-\s+")


def normalizar_estat(raw: str | None) -> str | None:
    """Estat crudo → estado canónico. Fuera de catálogo/vacío → None."""
    if not raw:
        return None
    return _ESTAT_CATALOGO.get(raw.strip())


def normalizar_grupo(raw: str | None) -> str | None:
    """Extrae el código de grupo ('A1 - Grau universitari…' → 'A1').

    El formato antiguo del portal va sin número ('A - Grau universitari').
    Sin el separador ' - ' no es un grupo → None.
    """
    if not raw:
        return None
    m = _RE_GRUP.match(raw.strip())
    return m.group(1) if m else None


# ── T3: duración del proceso ──
_RE_RESOLUCIO = re.compile(r"resoluc", re.IGNORECASE)


def fecha_resolucion(hitos: list[dict]) -> date | None:
    """Fecha del ÚLTIMO hito que es una resolución (cierra el proceso).

    Los hitos llegan como dicts del CSV crudo (hito_fecha, hito_titulo).
    Sin hito de resolución → None: la duración no es computable.
    """
    fechas = [
        date.fromisoformat(h["hito_fecha"])
        for h in hitos
        if h.get("hito_fecha") and _RE_RESOLUCIO.search(h.get("hito_titulo", ""))
    ]
    return max(fechas) if fechas else None


def durada_mesos(fecha_convocatoria: date | None, hitos: list[dict]) -> float | None:
    """Meses entre la convocatoria y la resolución (media de 30.44 días/mes).

    None si falta la convocatoria o no hay hito de resolución — la ausencia
    es un dato honesto (proceso aún abierto o incompleto en el portal).
    """
    if fecha_convocatoria is None:
        return None
    resolucion = fecha_resolucion(hitos)
    if resolucion is None:
        return None
    return round((resolucion - fecha_convocatoria).days / 30.44, 1)
