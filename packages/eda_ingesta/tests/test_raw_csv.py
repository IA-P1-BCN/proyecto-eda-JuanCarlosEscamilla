"""Tests del CSV crudo + log de calidad (T3.3) — tmp_path, fixtures reales parseadas."""

import json
from datetime import date
from pathlib import Path

import pytest

from eda_ingesta.escribir import (
    COLUMNAS_RAW,
    escribir_csv_raw,
    escribir_log_calidad,
)
from eda_ingesta.fichas import parse_ficha

FIX = Path(__file__).parent / "fixtures"
URL_IT = "https://cido.diba.cat/oposicions/14783298/borsa-de-treball-de-places-de-tecnic-superior-informatica-diversos-perfils-especialitzats-diputacio-de-barcelona"
URL_AL = "https://cido.diba.cat/oposicions/21078364/1-placa-dauxiliar-administratiu-de-gestio-de-lescola-de-musica-municipal-ajuntament-dalcover"


@pytest.fixture
def procesos():
    return [
        parse_ficha((FIX / "ficha_it_diba_14783298.html").read_text(), URL_IT),
        parse_ficha((FIX / "ficha_borsa_alcover_21078364.html").read_text(), URL_AL),
    ]


def test_columnas_definidas_y_estables():
    assert COLUMNAS_RAW[0] == "proceso_id"
    for col in ("fecha_convocatoria", "institucio", "sistema", "grup", "plazas",
                "hito_fecha", "hito_titulo", "doc_slug", "hito_url", "fuente_url"):
        assert col in COLUMNAS_RAW


def test_csv_formato_largo_una_fila_por_hito(tmp_path, procesos):
    ruta = escribir_csv_raw(procesos, tmp_path / "oposicions.csv")
    lineas = ruta.read_text().strip().split("\n")
    total_hitos = sum(len(p.hitos) for p in procesos)
    assert len(lineas) - 1 == total_hitos  # cabecera + hitos


def test_fila_de_un_hito_tiene_columnas_llenas(tmp_path, procesos):
    ruta = escribir_csv_raw(procesos, tmp_path / "oposicions.csv")
    import csv

    with ruta.open() as f:
        filas = list(csv.DictReader(f))
    alcover = [f for f in filas if f["proceso_id"] == "20260212O24"]
    assert alcover[0]["plazas"] == "1"          # del título '1 plaça d'…'
    assert alcover[0]["institucio"] == "Ajuntament d'Alcover"
    assert alcover[0]["hito_fecha"] == "2026-02-12"
    assert alcover[0]["doc_slug"] == "dogc"     # primera publicación en DOGC
    assert alcover[0]["fuente_url"] == URL_AL
    diba = [f for f in filas if f["proceso_id"] == "20230127O46"]
    assert diba[0]["plazas"] == ""              # 'places de' sin número → None
    assert diba[0]["hito_fecha"] == "2023-01-27"


def test_proceso_sin_hitos_aparece_con_hito_vacio(tmp_path, procesos):
    procesos[0].hitos = []
    ruta = escribir_csv_raw(procesos, tmp_path / "oposicions.csv")
    import csv

    with ruta.open() as f:
        filas = list(csv.DictReader(f))
    diba = [f for f in filas if f["proceso_id"] == "20230127O46"]
    assert len(diba) == 1 and diba[0]["hito_fecha"] == "" and diba[0]["doc_slug"] == ""


def test_log_calidad_jsonl(tmp_path):
    eventos = [
        {"tipo": "E1", "url": "http://x/caido", "detalle": "404"},
        {"tipo": "identificador_invalido", "url": "http://x/ficha", "detalle": "formato"},
    ]
    ruta = escribir_log_calidad(eventos, tmp_path / "calidad.jsonl")
    lineas = ruta.read_text().strip().split("\n")
    assert len(lineas) == 2
    assert json.loads(lineas[0])["tipo"] == "E1"


def test_log_vacio_no_crea_fichero(tmp_path):
    ruta = tmp_path / "calidad.jsonl"
    escribir_log_calidad([], ruta)
    assert not ruta.exists()
