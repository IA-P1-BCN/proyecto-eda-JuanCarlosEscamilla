"""Tests del paso clean sobre el dataset (US4) — fixtures sucias → CSV procesado."""

import csv

from eda_core.build import exportar_dataset, limpiar_dataset, validar_dataset
from fixtures_sucias import FILAS_SUCIAS


def _escribir_raw(tmp_path, filas):
    ruta = tmp_path / "oposicions.csv"
    with ruta.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    return ruta


def test_limpiar_aplica_catalogos_y_dedup(tmp_path):
    ruta_raw = _escribir_raw(tmp_path, FILAS_SUCIAS)
    destino = tmp_path / "processed" / "oposicions_procesado.csv"

    resumen = limpiar_dataset(ruta_raw, destino)

    assert destino.exists()
    with destino.open() as f:
        filas = list(csv.DictReader(f))
    # dedup: la fila R5 (duplicada) desaparece
    assert resumen["filas_raw"] == len(FILAS_SUCIAS)
    assert resumen["duplicados_eliminados"] == 1
    # catálogos: ningún estado fuera del catálogo (los vacíos → "")
    estados = {f["estado"] for f in filas}
    assert estados <= {"resuelta", "abierta", "pendiente", "cerrada", "no vigente", ""}
    # grupos normalizados a código
    grupos = {f["grupo"] for f in filas if f["grupo"]}
    assert grupos <= {"A", "A1", "A2", "B", "C1", "C2"}


def test_limpiar_anyade_durada_mesos(tmp_path):
    ruta_raw = _escribir_raw(tmp_path, FILAS_SUCIAS)
    destino = tmp_path / "processed" / "oposicions_procesado.csv"
    limpiar_dataset(ruta_raw, destino)
    with destino.open() as f:
        filas = list(csv.DictReader(f))
    duradas = {f["durada_mesos"] for f in filas if f["durada_mesos"]}
    assert duradas  # la fila base (conv 2023-01-27 → res 2023-12-14) es computable
    assert any(float(d) > 10 for d in duradas)


def test_validar_dataset_verifica_contrato_spec(tmp_path):
    ruta = tmp_path / "enriquit.csv"
    cols = [
        "proceso_id", "fecha_convocatoria", "institucio", "sistema",
        "tipus_personal", "grupo", "plazas", "estado", "materies",
        "hito_fecha", "hito_titulo", "doc_slug", "durada_mesos",
        "municipi", "poblacio_municipi", "dist_km_vic", "urbanitzacio",
        "places_per_mil_hab",
    ]
    with ruta.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i in range(10):
            w.writerow({c: f"v{i}" for c in cols} | {"proceso_id": f"P{i // 2}"})

    res_ok = validar_dataset(ruta, min_filas=10)
    assert res_ok["ok"] is True
    assert res_ok["filas"] == 10
    assert res_ok["columnas"] == 18
    assert res_ok["procesos"] == 5

    res_corto = validar_dataset(ruta, min_filas=1000)
    assert res_corto["ok"] is False
    assert any("filas" in e for e in res_corto["errores"])


def test_exportar_dataset_genera_dimension_procesos(tmp_path):
    ruta_raw = _escribir_raw(tmp_path, FILAS_SUCIAS)
    procesado = tmp_path / "processed" / "oposicions_procesado.csv"
    limpiar_dataset(ruta_raw, procesado)

    destino_dim = tmp_path / "processed" / "procesos_resumen.csv"
    res = exportar_dataset(procesado, destino_dim)
    assert destino_dim.exists()
    assert res["procesos_exportados"] >= 1
    with destino_dim.open() as f:
        filas_dim = list(csv.DictReader(f))
    ids = [r["proceso_id"] for r in filas_dim]
    assert len(ids) == len(set(ids))
