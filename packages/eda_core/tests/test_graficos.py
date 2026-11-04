"""Tests de los gráficos del informe (US7·T2/T3) — CSV sintético, Agg, sin display."""

import csv
from pathlib import Path

import pandas as pd

from eda_core.graficos import (
    generar_estaticos,
    generar_interactivos,
    ranking_per_capita,
    resumen_outliers_iqr,
)

_FILAS = []
for i, (muni, pob, urb, dur, grupo, mes) in enumerate([
    ("Berga", 17000, "intermedi", 10.5, "A1", 3), ("Vic", 50000, "urbano", 6.0, "A1", 4),
    ("Tavertet", 120, "rural", 18.0, "C1", 6), ("Cardedeu", 18000, "intermedi", 4.2, "C1", 9),
    ("Manresa", 77000, "urbano", 12.1, "A2", 10), ("Olot", 35000, "urbano", 5.5, "C2", 2),
    ("Ripoll", 11000, "intermedi", 15.0, "A1", 11), ("Gurb", 2500, "rural", 8.0, "B", 5),
]):
    _FILAS.append({"proceso_id": f"P{i}", "fecha_convocatoria": f"2024-{mes:02d}-15",
                   "institucio": f"Ajuntament de {muni}", "sistema": "Oposició o prova",
                   "tipus_personal": "Funcionari", "grupo": grupo, "plazas": "1",
                   "estado": "resuelta", "materies": "Informàtica",
                   "hito_fecha": "2025-01-15", "hito_titulo": "Resolució",
                   "doc_slug": "dogc", "durada_mesos": str(dur),
                   "municipi": muni.lower(), "poblacio_municipi": str(pob),
                   "dist_km_vic": "30.0", "urbanitzacio": urb,
                   "places_per_mil_hab": f"{1 / (pob / 1000):.4f}"})


def _csv(tmp_path):
    ruta = tmp_path / "oposicions_enriquit.csv"
    with ruta.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(_FILAS[0].keys()))
        w.writeheader()
        w.writerows(_FILAS)
    return ruta


def test_genera_6_estaticos_con_nombre_de_pregunta(tmp_path):
    rutas = generar_estaticos(_csv(tmp_path), tmp_path / "charts")
    assert len(rutas) >= 6
    nombres = [r.stem for r in rutas]
    assert any(n.startswith("p1_") for n in nombres)
    assert any(n.startswith("p2_") for n in nombres)
    assert any(n.startswith("p3_") for n in nombres)
    assert all((tmp_path / "charts" / r.name).stat().st_size > 5000 for r in rutas)


def test_genera_3_interactivos_html(tmp_path):
    rutas = generar_interactivos(_csv(tmp_path), tmp_path / "charts")
    assert len(rutas) >= 3
    for r in rutas:
        contenido = r.read_text()
        assert r.suffix == ".html" and "plotly" in contenido.lower()


def test_resumen_outliers_iqr_detecta_cola():
    s = pd.Series([2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 64.0])
    res = resumen_outliers_iqr(s)
    assert res["n_outliers"] == 1
    assert res["max_outlier"] == 64.0
    assert res["limite_superior"] < 64.0


def test_ranking_per_capita_calcula_tasas(tmp_path):
    df = pd.read_csv(_csv(tmp_path), dtype=str).fillna("")
    top = ranking_per_capita(df, min_poblacion=1000, top_n=5)
    assert len(top) <= 5
    assert {"municipi", "urbanitzacio", "procesos", "por_1k", "plazas_por_1k"} <= set(top.columns)
    assert "tavertet" not in top["municipi"].values  # 120 hab < 1000
