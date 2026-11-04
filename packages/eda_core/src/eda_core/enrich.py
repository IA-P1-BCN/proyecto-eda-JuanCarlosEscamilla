"""Enriquecimiento (US5·T2/T3): merge con población municipal + features.

El CSV procesado (1 fila por hito, proceso desnormalizado) se enriquece por
`institucio`:
- match con la referencia de población (data/reference/poblacio_municipis.csv)
- `places_per_mil_hab` = plazas del proceso / (población/1000) — la comparación
  honesta entre municipios grandes y pequeños (pregunta 2 del PRD)
- `urbanitzacio`: urbano ≥20k · intermedi 5k-20k · rural <5k hab (criterio
  documentado en ADR-0005/GLOSSARY; alternativas habituales del INE)
- Los procesos sin match (no-ajuntament o municipio ausente) NO se descartan:
  siguen en el dataset con los campos vacíos, y quedan listados en el informe
  de municipios sin match (no silencio).
"""

from __future__ import annotations

import csv
from pathlib import Path

from eda_ingesta.poblacio import cargar_poblacio, enllacar_institucio


def _urbanitzacio(poblacio: int) -> str:
    if poblacio >= 20000:
        return "urbano"
    if poblacio >= 5000:
        return "intermedi"
    return "rural"


def enriquir_dataset(
    ruta_procesado: Path,
    ruta_referencia: Path,
    destino: Path,
    municipis_override: dict | None = None,
    informe_sin_match: Path | None = None,
) -> dict:
    municipis = municipis_override or cargar_poblacio(ruta_referencia)

    with ruta_procesado.open(encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    sin_match: list[dict] = []
    matcheados = 0
    for fila in filas:
        match, metodo = enllacar_institucio(fila["institucio"], municipis)
        fila["municipi"] = match["municipi"] if match else ""
        fila["poblacio_municipi"] = str(match["poblacio"]) if match else ""
        fila["dist_km_vic"] = str(match["dist_km_vic"]) if match else ""
        fila["urbanitzacio"] = _urbanitzacio(match["poblacio"]) if match else ""
        plazas = int(fila["plazas"]) if fila["plazas"].isdigit() else 0
        fila["places_per_mil_hab"] = (
            f"{plazas / (match['poblacio'] / 1000):.4f}" if match else ""
        )
        if match:
            matcheados += 1
        else:
            sin_match.append({"proceso_id": fila["proceso_id"],
                              "institucio": fila["institucio"],
                              "motiu": metodo})

    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    if informe_sin_match is not None and sin_match:
        únicos = {e["proceso_id"]: e for e in sin_match}  # 1 fila por PROCESO, no por hito
        informe_sin_match.parent.mkdir(parents=True, exist_ok=True)
        with informe_sin_match.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["proceso_id", "institucio", "motiu"])
            w.writeheader()
            w.writerows(únicos.values())

    return {"filas": len(filas), "matcheados": matcheados,
            "sin_match_filas": len(sin_match),
            "sin_match_procesos": len({e["proceso_id"] for e in sin_match})}
