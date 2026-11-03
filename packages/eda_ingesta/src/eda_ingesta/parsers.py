"""Parsers puros del CIDO: identificador, plazas y fechas (sin I/O, 100% testeables)."""

from __future__ import annotations

import re
from datetime import date

# Identificador CIDO: AAAAMMDD + 'O' + ordinal (p.ej. 20230127O46)
_IDENT_RE = re.compile(r"^(\d{4})(\d{2})(\d{2})O(\d{2})$")

# Plazas en título/slug: número + 'plaça/placa/plaza' o plurales 'places/plazas' (ca/es)
_PLAZAS_RE = re.compile(r"(?<!\d)(\d{1,3})[-\s]+pla[çcz](?:as|es|a)?\b", re.IGNORECASE)

# Fecha dd/mm/yyyy (convención ca/es: DÍA primero); paddeo opcional
_FECHA_RE = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})/(\d{4})(?!\d)")


class IdentificadorInvalido(ValueError):
    """El identificador no codifica una fecha de convocatoria válida."""


class FechaInvalido(ValueError):
    """El texto no es una fecha dd/mm/yyyy válida."""


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


def parse_plazas(texto: str | None) -> int | None:
    """Extrae el número de plazas de un título o slug (ca/es).

    Devuelve None cuando no aparece número — es el caso esperado en bolsas de
    treball ('Borsa de treball de places de…' no cuantifica). Los guiones y
    guiones bajos de los slugs se normalizan a espacios antes de buscar.
    """
    if not texto:
        return None
    m = _PLAZAS_RE.search(re.sub(r"[-_]+", " ", texto))
    return int(m.group(1)) if m else None


def parse_fecha(raw: str) -> date:
    """Parsea una fecha dd/mm/yyyy estricta (día primero, convención ca/es)."""
    m = _FECHA_RE.fullmatch((raw or "").strip())
    if m is None:
        raise FechaInvalido(f"no es dd/mm/yyyy: {raw!r}")
    dia, mes, anio = (int(g) for g in m.groups())
    try:
        return date(anio, mes, dia)
    except ValueError as exc:
        raise FechaInvalido(f"fecha imposible en {raw!r}") from exc


def parse_fechas_texto(texto: str | None) -> list[date]:
    """Extrae todas las fechas dd/mm/yyyy válidas de un texto.

    Las fechas imposibles (32/13/2026) se saltan: el llamador puede comparar
    coincidencias del patrón contra el resultado para registrarlas en el log
    de calidad. La parte horaria de un datetime ('03/11/2026 21:29:29') se
    ignora — solo interesa la fecha.
    """
    if not texto:
        return []
    fechas = []
    for m in _FECHA_RE.finditer(texto):
        dia, mes, anio = (int(g) for g in m.groups())
        try:
            fechas.append(date(anio, mes, dia))
        except ValueError:
            continue
    return fechas
