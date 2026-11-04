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


_COLUMNAS_REQUERIDAS = {
    "proceso_id", "fecha_convocatoria", "institucio", "sistema",
    "tipus_personal", "grupo", "plazas", "estado", "materies",
    "hito_fecha", "hito_titulo", "doc_slug", "durada_mesos",
}
_COLUMNAS_PROHIBIDAS_RGPD = {"nif", "dni", "nombre", "apellidos", "aspirante"}


def validar_dataset(ruta_csv: Path, *, min_filas: int = 1000, min_columnas: int = 8) -> dict:
    """Quality gate del dataset procesado/enriquecido (contrato CLIENT_SPECS + ADR-0004)."""
    ruta_csv = Path(ruta_csv)
    if not ruta_csv.exists():
        return {"ok": False, "filas": 0, "columnas": 0, "procesos": 0,
                "errores": [f"no existe {ruta_csv}"]}
    with ruta_csv.open(encoding="utf-8") as f:
        lector = csv.DictReader(f)
        cols = list(lector.fieldnames or [])
        filas = list(lector)

    errores: list[str] = []
    if len(filas) < min_filas:
        errores.append(f"filas insuficientes: {len(filas)} < {min_filas}")
    if len(cols) < min_columnas:
        errores.append(f"columnas insuficientes: {len(cols)} < {min_columnas}")
    faltantes = _COLUMNAS_REQUERIDAS - set(cols)
    if faltantes:
        errores.append(f"faltan columnas requeridas: {sorted(faltantes)}")
    prohibidas = {c for c in cols if c.lower() in _COLUMNAS_PROHIBIDAS_RGPD}
    if prohibidas:
        errores.append(f"violación RGPD (ADR-0004): {sorted(prohibidas)}")

    procesos = len({r["proceso_id"] for r in filas if r.get("proceso_id")})
    return {
        "ok": len(errores) == 0,
        "filas": len(filas),
        "columnas": len(cols),
        "procesos": procesos,
        "errores": errores,
    }


def exportar_dataset(ruta_enriquit: Path, destino: Path | None = None) -> dict:
    """Exporta la tabla dimensión de procesos (1 fila = 1 proceso_id único)."""
    ruta_enriquit = Path(ruta_enriquit)
    if not ruta_enriquit.exists():
        return {"filas_hitos": 0, "procesos_exportados": 0, "ruta_procesos": ""}
    destino = Path(destino) if destino else ruta_enriquit.parent / "procesos_resumen.csv"
    with ruta_enriquit.open(encoding="utf-8") as f:
        lector = csv.DictReader(f)
        cols = [c for c in (lector.fieldnames or [])
                if c not in ("hito_fecha", "hito_titulo", "doc_slug")]
        filas = list(lector)

    vistos: dict[str, dict] = {}
    for fila in filas:
        pid = fila.get("proceso_id", "")
        if pid and pid not in vistos:
            vistos[pid] = {c: fila.get(c, "") for c in cols}

    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(vistos.values())

    return {
        "filas_hitos": len(filas),
        "procesos_exportados": len(vistos),
        "ruta_procesos": str(destino),
    }
