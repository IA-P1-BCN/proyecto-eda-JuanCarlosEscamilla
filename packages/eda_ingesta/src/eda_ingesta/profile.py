"""Profiling de la zona raw: reporte markdown para el informe de calidad (US12).

Lee `data/raw/oposicions.csv` + `data/raw/calidad.jsonl` y escribe
`reports/profiling.md` (crea reports/ si falta). Sin datos → reporte que lo
dice, sin explotar.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd


def run(raiz: Path, destino: Path | None = None) -> Path:
    raiz = Path(raiz)
    destino = Path(destino) if destino else Path("reports") / "profiling.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    ruta_csv = raiz / "oposicions.csv"

    lineas: list[str] = ["# Profiling — zona raw (CIDO materia 24)", ""]

    if not ruta_csv.exists():
        lineas += ["## Sin datos", "", "El pipeline no ha generado aún `oposicions.csv`.", ""]
        destino.write_text("\n".join(lineas), encoding="utf-8")
        return destino

    df = pd.read_csv(ruta_csv, dtype=str).fillna("")
    procesos = df["proceso_id"].nunique()
    lineas += [
        "## Totales",
        "",
        f"- filas (hitos): {len(df)}",
        f"- procesos únicos: {procesos}",
        f"- con plaza publicada: {(df['plazas'] != '').sum()}",
        f"- rango fecha_convocatoria: {df['fecha_convocatoria'].min()} → {df['fecha_convocatoria'].max()}",
        "",
        "## Nulos por columna (top 10)",
        "",
        "| columna | vacíos |",
        "|---|---|",
    ]
    vacios = (df == "").sum().sort_values(ascending=False).head(10)
    lineas += [f"| {col} | {n} |" for col, n in vacios.items()]

    lineas += ["", "## doc_slug", "", "| slug | hitos |", "|---|---|"]
    for slug, n in Counter(v for v in df["doc_slug"] if v).most_common(15):
        lineas += [f"| {slug} | {n} |"]

    lineas += ["", "## materies", "", "| materia | procesos |", "|---|---|"]
    for materia, n in Counter(
        m.strip() for v in df["materies"] for m in v.split(",") if m.strip()
    ).most_common(10):
        lineas += [f"| {materia} | {n} |"]

    lineas += ["", "## Calidad (log E1/E2/E3)", ""]
    ruta_log = raiz / "calidad.jsonl"
    if ruta_log.exists():
        conteo = Counter(json.loads(l)["tipo"] for l in ruta_log.read_text().splitlines() if l.strip())
        for tipo in sorted(conteo):
            lineas += [f"- {tipo}: {conteo[tipo]}"]
    else:
        lineas += ["- sin eventos (silencio = ok)"]

    lineas += [""]
    destino.write_text("\n".join(lineas), encoding="utf-8")
    return destino
