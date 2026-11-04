"""Tests del DAG de Airflow (US11·T1, #57): 6 etapas encadenadas sobre eda_ingesta y eda_core."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from eda_ingesta.download import Resumen

RUTA_DAG = Path(__file__).resolve().parents[3] / "airflow" / "dags" / "eda_oposicions.py"


def _cargar_modulo_dag():
    spec = importlib.util.spec_from_file_location("eda_oposicions_dag", RUTA_DAG)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_estructura_dag_seis_tareas_en_orden():
    """El DAG eda_oposicions define las 6 tareas encadenadas en orden."""
    assert RUTA_DAG.exists(), f"Falta {RUTA_DAG}"
    mod = _cargar_modulo_dag()
    assert mod.DAG_ID == "eda_oposicions"
    assert mod.ORDEN_TAREAS == (
        "scan_download",
        "profile",
        "clean",
        "enrich",
        "validate",
        "export",
    )


def test_callables_dag_invocan_modulos_monorepo(monkeypatch, tmp_path):
    """Cada función de tarea del DAG invoca la función correspondiente de eda_ingesta/eda_core."""
    mod = _cargar_modulo_dag()
    llamadas: list[str] = []

    monkeypatch.setattr(
        mod.download,
        "run",
        lambda raiz, **kw: (
            llamadas.append("scan_download"),
            Resumen(fichas_descubiertas=814, procesos=814, hitos=2786, cache_hits=1106, fetched=0),
        )[1],
    )
    monkeypatch.setattr(
        mod.profile,
        "run",
        lambda raiz, destino=None: (llamadas.append("profile"), tmp_path / "profiling.md")[1],
    )
    monkeypatch.setattr(
        mod.build,
        "limpiar_dataset",
        lambda orig, dest: (llamadas.append("clean"), {"filas_limpias": 2690})[1],
    )
    monkeypatch.setattr(
        mod,
        "enriquir_dataset",
        lambda *a, **kw: (llamadas.append("enrich"), {"con_match": 2258})[1],
    )
    monkeypatch.setattr(
        mod.build,
        "validar_dataset",
        lambda ruta: (llamadas.append("validate"), {"ok": True, "filas": 2690, "errores": []})[1],
    )
    monkeypatch.setattr(
        mod.build,
        "exportar_dataset",
        lambda ruta, dest=None: (llamadas.append("export"), {"procesos_exportados": 814})[1],
    )

    mod.task_scan_download(raiz_base=tmp_path)
    mod.task_profile(raiz_base=tmp_path)
    mod.task_clean(raiz_base=tmp_path)
    mod.task_enrich(raiz_base=tmp_path)
    mod.task_validate(raiz_base=tmp_path)
    mod.task_export(raiz_base=tmp_path)

    assert llamadas == ["scan_download", "profile", "clean", "enrich", "validate", "export"]


def test_compose_monta_monorepo_y_reports():
    """infra/docker-compose.yml configura PYTHONPATH y monta airflow/dags, packages, data y reports."""
    compose = (Path(__file__).resolve().parents[3] / "infra" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "PYTHONPATH:" in compose
    assert "/opt/airflow/packages/eda_ingesta/src" in compose
    assert "/opt/airflow/packages/eda_core/src" in compose
    assert "../airflow/dags:/opt/airflow/dags" in compose
    assert "../packages:/opt/airflow/packages" in compose
    assert "../data:/opt/airflow/data" in compose
    assert "../reports:/opt/airflow/reports" in compose

