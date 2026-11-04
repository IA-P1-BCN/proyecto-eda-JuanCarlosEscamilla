"""DAG de Apache Airflow `eda_oposicions` (US11, #11 / #57).

Encadena las 6 etapas del pipeline EDA invocando los módulos del monorepo
(`eda_ingesta` y `eda_core`):
    scan_download >> profile >> clean >> enrich >> validate >> export
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from eda_core import build
from eda_core.enrich import enriquir_dataset
from eda_ingesta import download, profile
from eda_ingesta.crawl import Filtre

DAG_ID = "eda_oposicions"
ORDEN_TAREAS = (
    "scan_download",
    "profile",
    "clean",
    "enrich",
    "validate",
    "export",
)

# Raíz del proyecto: en el contenedor es /opt/airflow (dags/eda_oposicions.py -> parents[1]);
# en el repositorio local es parents[2] (airflow/dags/eda_oposicions.py -> parents[2]).
_CANDIDATO_CONTENEDOR = Path(__file__).resolve().parents[1]
RAIZ_PROYECTO = (
    _CANDIDATO_CONTENEDOR
    if (_CANDIDATO_CONTENEDOR / "data").exists()
    else Path(__file__).resolve().parents[2]
)


def _base(raiz_base: Path | None = None) -> Path:
    return Path(raiz_base) if raiz_base is not None else RAIZ_PROYECTO


def task_scan_download(raiz_base: Path | None = None, **_: object) -> dict[str, int]:
    """Paso 1: ingesta incremental con caché + detector RSS (scan / download)."""
    base = _base(raiz_base)
    res = download.run(base / "data" / "raw", filtre=Filtre(), pausa=0.5)
    print(
        f"[scan_download] descubiertas={res.fichas_descubiertas} procesos={res.procesos} "
        f"hitos={res.hitos} actualizadas={res.actualizadas} "
        f"cache={res.cache_hits} fetched={res.fetched}"
    )
    return {
        "procesos": res.procesos,
        "hitos": res.hitos,
        "cache_hits": res.cache_hits,
        "fetched": res.fetched,
    }


def task_profile(raiz_base: Path | None = None, **_: object) -> str:
    """Paso 2: perfilado del dataset crudo en reports/profiling.md."""
    base = _base(raiz_base)
    destino = profile.run(
        base / "data" / "raw",
        destino=base / "reports" / "profiling.md",
    )
    print(f"[profile] reporte generado en {destino}")
    return str(destino)


def task_clean(raiz_base: Path | None = None, **_: object) -> dict[str, int]:
    """Paso 3: limpieza, catalogación de hitos y deduplicación."""
    base = _base(raiz_base)
    res = build.limpiar_dataset(
        base / "data" / "raw" / "oposicions.csv",
        base / "data" / "processed" / "oposicions_procesado.csv",
    )
    print(f"[clean] {res}")
    return res


def task_enrich(raiz_base: Path | None = None, **_: object) -> dict[str, int]:
    """Paso 4: cruce con población municipal (Wikidata/IDESCAT) y métricas per cápita."""
    base = _base(raiz_base)
    res = enriquir_dataset(
        base / "data" / "processed" / "oposicions_procesado.csv",
        base / "data" / "reference" / "poblacio_municipis.csv",
        base / "data" / "processed" / "oposicions_enriquit.csv",
        informe_sin_match=base / "reports" / "calidad-municipios.csv",
    )
    print(f"[enrich] {res}")
    return res


def task_validate(raiz_base: Path | None = None, **_: object) -> dict[str, object]:
    """Paso 5: validación del contrato del dataset enriquecido y cumplimiento RGPD."""
    base = _base(raiz_base)
    res = build.validar_dataset(base / "data" / "processed" / "oposicions_enriquit.csv")
    print(f"[validate] {res}")
    if not res["ok"]:
        raise ValueError(f"Validación fallida: {res['errores']}")
    return res


def task_export(raiz_base: Path | None = None, **_: object) -> dict[str, object]:
    """Paso 6: exportación de la tabla resumen por proceso para dashboard y análisis."""
    base = _base(raiz_base)
    res = build.exportar_dataset(
        base / "data" / "processed" / "oposicions_enriquit.csv",
        base / "data" / "processed" / "procesos_resumen.csv",
    )
    print(f"[export] {res}")
    return res


try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator

    with DAG(
        dag_id=DAG_ID,
        description="Pipeline EDA oposicions CIDO (scan_download -> profile -> clean -> enrich -> validate -> export)",
        start_date=datetime(2026, 1, 1),
        schedule=None,
        catchup=False,
        tags=["eda", "cido", "oposicions"],
    ) as dag:
        t_scan = PythonOperator(task_id="scan_download", python_callable=task_scan_download)
        t_profile = PythonOperator(task_id="profile", python_callable=task_profile)
        t_clean = PythonOperator(task_id="clean", python_callable=task_clean)
        t_enrich = PythonOperator(task_id="enrich", python_callable=task_enrich)
        t_validate = PythonOperator(task_id="validate", python_callable=task_validate)
        t_export = PythonOperator(task_id="export", python_callable=task_export)

        t_scan >> t_profile >> t_clean >> t_enrich >> t_validate >> t_export
except ImportError:  # Entorno local/CI sin apache-airflow instalado
    dag = None
