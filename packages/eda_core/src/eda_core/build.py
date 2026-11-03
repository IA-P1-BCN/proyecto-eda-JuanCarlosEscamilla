"""Orquestación del paso `clean`: CSV crudo → dataset procesado (US4).

Aplica las funciones TDD de clean.py fila a fila y las funciones de proceso
(dedup + durada por proceso). Escribe data/processed/oposicions_procesado.csv
y devuelve un resumen contable para el informe de calidad (US12).
"""

from __future__ import annotations

import csv
from pathlib import Path

from .clean import dedup_hitos, durada_mesos, normalizar_estat, normalizar_grupo


def limpiar_dataset(ruta_raw: Path, destino: Path) -> dict:
    with ruta_raw.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    filas_raw = len(filas)
    filas = dedup_hitos(filas)
    duplicados = filas_raw - len(filas)

    # durada por proceso: los hitos de un proceso agrupados (el CSV es largo)
    hitos_por_proceso: dict[str, list[dict]] = {}
    convocatorias: dict[str, str] = {}
    for fila in filas:
        hitos_por_proceso.setdefault(fila["proceso_id"], []).append(fila)
        if fila["fecha_convocatoria"]:
            convocatorias[fila["proceso_id"]] = fila["fecha_convocatoria"]
    duradas = {
        pid: durada_mesos(
            __import__("datetime").date.fromisoformat(conv) if conv else None, hitos
        )
        for pid, conv in convocatorias.items()
        for hitos in [hitos_por_proceso.get(pid, [])]
    }

    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "proceso_id", "fecha_convocatoria", "institucio", "sistema",
            "tipus_personal", "grupo", "plazas", "estado", "materies",
            "hito_fecha", "hito_titulo", "doc_slug", "durada_mesos",
        ])
        w.writeheader()
        for fila in filas:
            w.writerow({
                "proceso_id": fila["proceso_id"],
                "fecha_convocatoria": fila["fecha_convocatoria"],
                "institucio": fila["institucio"],
                "sistema": fila["sistema"],
                "tipus_personal": fila["tipus_personal"],
                "grupo": normalizar_grupo(fila["grup"]) or "",
                "plazas": fila["plazas"],
                "estado": normalizar_estat(fila["estat"]) or "",
                "materies": fila["materies"],
                "hito_fecha": fila["hito_fecha"],
                "hito_titulo": fila["hito_titulo"],
                "doc_slug": fila["doc_slug"],
                "durada_mesos": duradas.get(fila["proceso_id"], ""),
            })

    return {"filas_raw": filas_raw, "filas_limpias": len(filas),
            "duplicados_eliminados": duplicados, "procesos": len(convocatorias)}
