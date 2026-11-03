"""Tests del paso clean sobre el dataset (US4) — fixtures sucias → CSV procesado."""

import csv

from eda_core.build import limpiar_dataset
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
