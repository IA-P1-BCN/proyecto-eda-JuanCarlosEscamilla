"""Escritura de la zona raw: CSV en formato largo + log de calidad JSONL.

Formato largo: 1 fila por hito, con los campos del proceso desnormalizados
(proceso_id repetido por hito). Procesos sin hitos → 1 fila con hito_* vacío
(así ningún proceso desaparece del dataset). El log de calidad solo se escribe
si hay eventos — silencio = cero problemas.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .adjuntos import clasificar_doc
from .fichas import Proceso
from .parsers import parse_plazas

COLUMNAS_RAW = [
    "proceso_id",
    "fecha_convocatoria",
    "titulo",
    "institucio",
    "sistema",
    "tipus_personal",
    "grup",
    "titulacio",
    "materies",
    "estat",
    "plazas",
    "hito_fecha",
    "hito_titulo",
    "doc_slug",
    "hito_url",
    "fuente_url",
]


def _fila(proceso: Proceso, hito) -> dict[str, str]:
    fecha = (
        hito.fecha.isoformat() if hito and hito.fecha else ""
    )
    hito_url = hito.url if hito else None
    return {
        "proceso_id": proceso.identificador or "",
        "fecha_convocatoria": (
            proceso.fecha_convocatoria.isoformat() if proceso.fecha_convocatoria else ""
        ),
        "titulo": proceso.titulo,
        "institucio": proceso.institucio,
        "sistema": proceso.sistema or "",
        "tipus_personal": proceso.tipus_personal or "",
        "grup": proceso.grup or "",
        "titulacio": proceso.titulacio or "",
        "materies": ", ".join(proceso.materies),
        "estat": proceso.estat or "",
        "plazas": str(parse_plazas(proceso.titulo)) if parse_plazas(proceso.titulo) is not None else "",
        "hito_fecha": fecha,
        "hito_titulo": hito.titulo if hito else "",
        "doc_slug": clasificar_doc(hito_url) if hito_url else "",
        "hito_url": hito_url or "",
        "fuente_url": proceso.url,
    }


def escribir_csv_raw(procesos: list[Proceso], ruta: Path) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS_RAW)
        w.writeheader()
        for proceso in procesos:
            if proceso.hitos:
                for hito in proceso.hitos:
                    w.writerow(_fila(proceso, hito))
            else:
                w.writerow(_fila(proceso, None))
    return ruta


def escribir_log_calidad(eventos: list[dict], ruta: Path) -> Path:
    """JSONL de eventos de calidad; sin eventos no hay fichero (silencio = ok)."""
    if not eventos:
        return ruta
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as f:
        for evento in eventos:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return ruta
