"""Parsers puros del CIDO: identificador, plazas y fechas (sin I/O, 100% testeables)."""

from __future__ import annotations

import re
from datetime import date

# Identificador CIDO: AAAAMMDD + 'O' + ordinal (p.ej. 20230127O46)
_IDENT_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})O(\d{2})$")


class IdentificadorInvalido(ValueError):
    """El identificador no codifica una fecha de convocatoria válida."""


def parse_identificador(raw: str) -> date:
    """Extrae la fecha de convocatoria del identificador del proceso.

    Lanza IdentificadorInvalido si no encaja con AAAAMMDDO## o la fecha no existe;
    el llamador decide si registra en el log de calidad o aborta.
    """
    match = _IDENT_RE.match(raw.strip() if raw else "")
    if match is None:
        raise IdentificadorInvalido(f"formato no reconocido: {raw!r}")
    anio, mes, dia, _ordinal = (int(g) for g in match.groups())
    try:
        return date(anio, mes, dia)
    except ValueError as exc:
        raise IdentificadorInvalido(f"fecha imposible en {raw!r}") from exc
