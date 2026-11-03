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
