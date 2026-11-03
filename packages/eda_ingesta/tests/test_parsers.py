"""Tests del parser del identificador CIDO (task 1.1 — escrito ANTES que la función).

El identificador codifica la fecha de convocatoria: `20230127O46` → 27/01/2023.
Formato: AAAAMMDD + 'O' + ordinal de 2 dígitos.
"""

from datetime import date

import pytest

from eda_ingesta.parsers import IdentificadorInvalido, parse_identificador


@pytest.mark.parametrize(
    ("raw", "esperada"),
    [
        ("20230127O46", date(2023, 1, 27)),
        ("20260212O24", date(2026, 2, 12)),
        ("20201231O01", date(2020, 12, 31)),
    ],
)
def test_parse_identificador_valido(raw, esperada):
    assert parse_identificador(raw) == esperada


@pytest.mark.parametrize(
    "raw",
    [
        "",                      # vacío
        "20230127",              # sin ordinal
        "20231327O46",           # mes 13 no existe
        "20230230O46",           # 30 de febrero
        "abcdefghO46",           # no numérico
        "20230127X46",           # separador que no es 'O'
    ],
)
def test_parse_identificador_invalido(raw):
    with pytest.raises(IdentificadorInvalido):
        parse_identificador(raw)


# ── 1.2 parse_plazas ──────────────────────────────────────────────────
# Material real: títulos del feed RSS y de las fichas (ca/es).
from eda_ingesta.parsers import FechaInvalido, parse_fecha, parse_fechas_texto, parse_plazas  # noqa: E402


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("1 plaça d'Auxiliar administratiu de gestió de l'Escola de Música Municipal", 1),
        ("1 placa de tècnic de projectes de cooperació internacional", 1),
        ("2 places d'auxiliar administratiu", 2),
        ("10 places de tècnic superior informàtica", 10),
        ("123 places de policia local", 123),
        ("12 plazas de policía local", 12),
        ("1-placa-de-tecnic-superior-informatica", 1),  # slug con guiones
        ("2_places_de_gestio", 2),                      # slug con guion bajo
    ],
)
def test_parse_plazas_valido(texto, esperado):
    assert parse_plazas(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "Borsa de treball de places de dinamitzador juvenil",  # 'places' sin número
        "plaça de pediatra",                                   # sin número
        "Borsa de treball de l'Hospital",                      # sin plazas
        "",                                                    # vacío
        None,                                                  # ausente
    ],
)
def test_parse_plazas_sin_numero_devuelve_none(texto):
    assert parse_plazas(texto) is None


# ── 1.3 parse_fechas ──────────────────────────────────────────────────
# Convención ca/es: DÍA primero (01/12/2026 = 1 de diciembre).

@pytest.mark.parametrize(
    ("raw", "esperada"),
    [
        ("01/12/2026", date(2026, 12, 1)),
        ("1/2/2026", date(2026, 2, 1)),
        (" 03/11/2026 ", date(2026, 11, 3)),
    ],
)
def test_parse_fecha_valido(raw, esperada):
    assert parse_fecha(raw) == esperada


@pytest.mark.parametrize(
    "raw",
    ["32/13/2026", "20230127", "2026-01-27", "abc", "", None],  # imposible, sin barras, ISO, basura
)
def test_parse_fecha_invalido(raw):
    with pytest.raises(FechaInvalido):
        parse_fecha(raw)


def test_parse_fechas_texto_extrae_y_salta_imposibles():
    texto = "Finalització: 01/12/2026 · Publicació: 03/11/2026 21:29:29 · Correcció 32/13/2026"
    assert parse_fechas_texto(texto) == [date(2026, 12, 1), date(2026, 11, 3)]


def test_parse_fechas_texto_vacio():
    assert parse_fechas_texto("") == []
    assert parse_fechas_texto("12/2026 sin año completo") == []
