"""Tests del profiling (T4.2) — CSV + log pequeños, reporte markdown."""

from pathlib import Path

from eda_ingesta.escribir import COLUMNAS_RAW, escribir_csv_raw, escribir_log_calidad
from eda_ingesta.profile import run as run_profile
from eda_ingesta.fichas import parse_ficha

FIX = Path(__file__).parent / "fixtures"
URL_IT = "https://cido.diba.cat/oposicions/14783298/borsa-de-treball-de-places-de-tecnic-superior-informatica-diversos-perfils-especialitzats-diputacio-de-barcelona"


def _csv_con_datos(tmp_path):
    p = parse_ficha((FIX / "ficha_it_diba_14783298.html").read_text(), URL_IT)
    ruta = escribir_csv_raw([p], tmp_path / "oposicions.csv")
    escribir_log_calidad(
        [{"tipo": "E1", "url": "http://x/1", "detalle": "404"},
         {"tipo": "E2", "url": "http://x/2", "detalle": "portal genérico"}],
        tmp_path / "calidad.jsonl",
    )
    return ruta


def test_genera_reports_profiling_md(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _csv_con_datos(tmp_path)
    destino = run_profile(tmp_path)
    assert destino.exists() and destino.name == "profiling.md"
    texto = destino.read_text()
    for seccion in ("Totales", "Nulos", "doc_slug", "Calidad"):
        assert seccion in texto


def test_totales_y_calidad_en_el_reporte(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _csv_con_datos(tmp_path)
    texto = run_profile(tmp_path).read_text()
    assert "procesos únicos: 1" in texto
    assert "E1: 1" in texto and "E2: 1" in texto
    assert "Informàtica" in texto  # materies del dataset


def test_sin_csv_no_explota(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    texto = run_profile(tmp_path).read_text()
    assert "Sin datos" in texto
