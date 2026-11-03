"""Tests de limpieza de categorías (T2) — casos reales del CSV crudo."""

import pytest

from eda_core.clean import normalizar_estat, normalizar_grupo


@pytest.mark.parametrize(
    ("raw", "esperado"),
    [
        ("Resolt", "resuelta"),
        ("Termini obert", "abierta"),
        ("Termini pendent", "pendiente"),
        ("Termini tancat", "cerrada"),
        ("Procés no vigent", "no vigente"),
        ("", None),          # 47 casos reales: la ficha no pintó estado
        ("estat inventat", None),   # fuera de catálogo → None (va al log)
        (" - sin código", None),    # separador sin código delante
    ],
)
def test_normalizar_estat_a_catalogo(raw, esperado):
    assert normalizar_estat(raw) == esperado


@pytest.mark.parametrize(
    ("raw", "esperado"),
    [
        ("A1 - Grau universitari (correspondència amb llicenciatures)", "A1"),
        ("C1 - Batxillerat, FP 2n grau, cicles formatius grau superior", "C1"),
        ("A2 - Grau universitari (correspondència amb diplomatures)", "A2"),
        ("A - Grau universitari", "A"),      # formato antiguo SIN número
        ("B - Tècnic superior", "B"),
        ("", None),                                  # vacío → None
        ("Titulació universitària oficial", None),   # no es un grupo (sin ' - ')
        (" - sin código", None),                     # guion sin código delante
    ],
)
def test_normalizar_grupo_a_codigo(raw, esperado):
    assert normalizar_grupo(raw) == esperado


# ── T3: duración del proceso (convocatoria → resolución) ──
from datetime import date

from eda_core.clean import durada_mesos, fecha_resolucion  # noqa: E402

HITOS_RESUELTA = [
    {"hito_fecha": "2023-01-27", "hito_titulo": "Bases específiques. Convocatòria. Temari"},
    {"hito_fecha": "2023-03-14", "hito_titulo": "Llista d'admesos i exclosos"},
    {"hito_fecha": "2023-12-14", "hito_titulo": "Resolució final de la província. Publicació"},
]


def test_fecha_resolucion_del_ultimo_hito_con_resolucio():
    assert fecha_resolucion(HITOS_RESUELTA) == date(2023, 12, 14)


def test_sin_hito_de_resolucion():
    sin = [h for h in HITOS_RESUELTA if "resoluc" not in h["hito_titulo"].lower()]
    assert fecha_resolucion(sin) is None


def test_durada_mesos_convocatoria_a_resolucion():
    # 2023-01-27 → 2023-12-14 = 321 días ≈ 10.5 meses
    assert durada_mesos(date(2023, 1, 27), HITOS_RESUELTA) == pytest.approx(10.5, abs=0.1)


def test_durada_none_sin_resolucion_ni_convocatoria():
    assert durada_mesos(None, HITOS_RESUELTA) is None
    assert durada_mesos(date(2023, 1, 27), []) is None
    assert durada_mesos(date(2023, 1, 27), [{"hito_fecha": "2023-03-14",
                                             "hito_titulo": "Bases"}]) is None
