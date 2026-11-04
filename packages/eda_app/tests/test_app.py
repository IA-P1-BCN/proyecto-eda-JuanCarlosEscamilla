"""Tests del dashboard (US9·T1): la carga de datos y los KPIs, sin servidor."""

from pathlib import Path

import pandas as pd

from eda_app.app import cargar_datos, calcular_kpis

FILAS = [
    {"proceso_id": "P1", "fecha_convocatoria": "2023-01-27", "institucio": "Ajuntament de Berga",
     "sistema": "Oposició", "tipus_personal": "Funcionari", "grupo": "A1", "plazas": "2",
     "estado": "resuelta", "materies": "Informàtica", "durada_mesos": "10.5",
     "municipi": "berga", "poblacio_municipi": "17000", "dist_km_vic": "40.0",
     "urbanitzacio": "intermedi", "places_per_mil_hab": "0.1176"},
    {"proceso_id": "P2", "fecha_convocatoria": "2026-02-12", "institucio": "Ajuntament de Vic",
     "sistema": "Concurs", "tipus_personal": "Laboral", "grupo": "C1", "plazas": "1",
     "estado": "abierta", "materies": "Informàtica", "durada_mesos": "",
     "municipi": "vic", "poblacio_municipi": "50000", "dist_km_vic": "0.1",
     "urbanitzacio": "urbano", "places_per_mil_hab": "0.02"},
]


def _csv(tmp_path):
    ruta = tmp_path / "oposicions_enriquit.csv"
    pd.DataFrame(FILAS).to_csv(ruta, index=False)
    return ruta


def test_cargar_datos_normaliza(tmp_path):
    df = cargar_datos(_csv(tmp_path))
    assert len(df) == 2
    assert pd.api.types.is_numeric_dtype(df["durada_mesos"])
    assert pd.api.types.is_datetime64_any_dtype(df["fecha"])


def test_kpis_filtrados(tmp_path):
    df = calcular_kpis(cargar_datos(_csv(tmp_path)), municipio="Todos", grupo="Todos",
                       estado="abierta")
    assert df["proceso_id"].nunique() == 1   # solo la abierta


def test_kpis_filtrados_por_rango_anios(tmp_path):
    datos = cargar_datos(_csv(tmp_path))
    df = calcular_kpis(datos, municipio="Todos", grupo="Todos", estado="Todos",
                       rango_anios=(2025, 2026))
    assert list(df["proceso_id"].unique()) == ["P2"]
