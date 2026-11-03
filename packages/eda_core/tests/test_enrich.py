"""Tests del enriquecimiento (US5·T2/T3) — merge población + features."""

import csv
from pathlib import Path

from eda_core.enrich import enriquir_dataset

MUNICIPIS = {
    "berga": {"municipi": "Berga", "poblacio": 17000, "dist_km_vic": 40.0},
    "alcover": {"municipi": "Alcover", "poblacio": 5200, "dist_km_vic": 115.0},
    "tavertet": {"municipi": "Tavertet", "poblacio": 120, "dist_km_vic": 12.0},
}


def _raw(tmp_path):
    ruta = tmp_path / "oposicions.csv"
    filas = [
        {"proceso_id": "P1", "fecha_convocatoria": "2023-01-27", "institucio": "Ajuntament de Berga",
         "sistema": "Oposició o prova", "tipus_personal": "Funcionari", "grup": "A1 - Grau",
         "plazas": "2", "estado": "resuelta", "materies": "Informàtica", "durada_mesos": "10.5",
         "hito_fecha": "2023-01-27", "hito_titulo": "Bases", "doc_slug": "dogc"},
        {"proceso_id": "P2", "fecha_convocatoria": "2026-02-12", "institucio": "Ajuntament de Tavertet",
         "sistema": "Concurs", "tipus_personal": "Laboral", "grup": "C2 - ESO",
         "plazas": "1", "estado": "abierta", "materies": "Informàtica", "durada_mesos": "",
         "hito_fecha": "2026-02-12", "hito_titulo": "Oferta", "doc_slug": "dogc"},
        {"proceso_id": "P3", "fecha_convocatoria": "2026-10-01", "institucio": "Diputació de Barcelona",
         "sistema": "Borsa", "tipus_personal": "Laboral", "grup": "C1 - FP",
         "plazas": "1", "estado": "abierta", "materies": "Informàtica", "durada_mesos": "",
         "hito_fecha": "2026-10-01", "hito_titulo": "Oferta", "doc_slug": "dogc"},
    ]
    with ruta.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    return ruta


def test_enriquir_anyade_features_de_poblacion(tmp_path):
    destino = tmp_path / "oposicions_enriquit.csv"
    resumen = enriquir_dataset(_raw(tmp_path), "data/reference/poblacio_municipis.csv",
                               destino, municipis_override=MUNICIPIS)
    with destino.open() as f:
        filas = {f["proceso_id"]: f for f in csv.DictReader(f)}
    # P1: 2 plazas / 17.000 hab = 0.1176 por mil hab
    assert float(filas["P1"]["places_per_mil_hab"]) == pytest.approx(0.1176, abs=0.001)
    assert filas["P1"]["municipi"] == "Berga"
    assert filas["P1"]["urbanitzacio"] == "intermedi"      # 5k-20k
    assert filas["P2"]["urbanitzacio"] == "rural"          # 120 hab
    assert float(filas["P2"]["places_per_mil_hab"]) == pytest.approx(8.3333, abs=0.001)


def test_enriquir_informa_los_sin_match(tmp_path):
    destino = tmp_path / "oposicions_enriquit.csv"
    informe = tmp_path / "calidad-municipios.csv"
    resumen = enriquir_dataset(_raw(tmp_path), "data/reference/poblacio_municipis.csv",
                               destino, municipis_override=MUNICIPIS,
                               informe_sin_match=informe)
    assert resumen["sin_match"] == 1   # P3: Diputació = supramunicipal
    with informe.open() as f:
        sin = list(csv.DictReader(f))
    assert sin[0]["proceso_id"] == "P3"
    assert sin[0]["motiu"] == "no-es-ajuntament"


import pytest  # noqa: E402
