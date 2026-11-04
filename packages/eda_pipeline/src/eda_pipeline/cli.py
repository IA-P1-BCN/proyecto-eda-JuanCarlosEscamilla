"""CLI del pipeline: un comando, todo el proceso.

Los pasos reales (download, profile, clean, enrich, validate, export) se
implementan en US3+ con TDD; cada uno vive en su paquete (eda_ingesta, eda_core).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from eda_core import build
from eda_core.enrich import enriquir_dataset
from eda_core.graficos import generar_estaticos, generar_interactivos
from eda_ingesta import download, profile
from eda_ingesta.crawl import Filtre

STEPS = ("download", "profile", "clean", "enrich", "charts", "validate", "export")

PASOS_ALL = ("clean", "enrich", "validate", "export")  # all: sin red (download/scan son explícitos)



def _progreso(e: dict) -> None:
    """Progreso a stderr: [i/N] cache|fetch status KB url — visible en vivo."""
    import sys

    if e["fase"] == "ficha":
        print(f'[{e["i"]}/{e["n"]}] {"cache" if e.get("hit") else "fetch"} '
              f'{e.get("status", "")} {e["url"][:70]}', file=sys.stderr)
    elif e["fase"] == "listado":
        print(f'[listado p{e["pagina"]}] {e["fichas"]} fichas', file=sys.stderr)
    elif e["fase"] == "aviso":
        print(f'[aviso] {e["detalle"]}', file=sys.stderr)
    elif e["fase"] == "corte":
        print(f'[⚠ CORTE] {e["detalle"]}', file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eda-pipeline", description=__doc__)
    parser.add_argument(
        "--step",
        choices=(*STEPS, "scan", "all"),
        default="all",
        help="paso a ejecutar (por defecto: all)",
    )
    parser.add_argument("--pausa", type=float, default=1.0,
                        help="segundos de pausa entre peticiones al CIDO (default 1.0)")
    parser.add_argument("--max-paginas", type=int, default=None,
                        help="limita páginas del listado (bootstrap parcial para pruebas)")
    parser.add_argument("--materia", type=int, default=24,
                        help="materia CIDO (24 = Informàtica. Noves tecnologies)")
    parser.add_argument("--poblacio", default="Vic", help="epicentro de proximidad (default Vic)")
    parser.add_argument("--km", type=int, default=45, help="radio km desde el epicentro (default 45)")
    parser.add_argument("--lat", default="41,929968", help="latitud del epicentro")
    parser.add_argument("--lon", default="2,254264", help="longitud del epicentro")
    args = parser.parse_args(argv)

    # "all" ejecuta SOLO los pasos sin efectos de red; download/scan son explícitos
    pasos = PASOS_ALL if args.step == "all" else (args.step,)
    raiz = Path("data/raw")
    ruta_raw = raiz / "oposicions.csv"
    ruta_proc = Path("data/processed/oposicions_procesado.csv")
    ruta_enriq = Path("data/processed/oposicions_enriquit.csv")
    for paso in pasos:
        if paso == "download":
            filtre = Filtre(materia=args.materia, poblacio=args.poblacio, km=args.km,
                            latitud=args.lat, longitud=args.lon)
            r = download.run(raiz, filtre=filtre, pausa=args.pausa,
                             max_paginas=args.max_paginas, progreso=_progreso)
            print(f"[download] descubiertas={r.fichas_descubiertas} procesos={r.procesos} "
                  f"hitos={r.hitos} descartadas={r.descartadas_materia} "
                  f"cache={r.cache_hits} fetched={r.fetched}")
        elif paso == "scan":
            filtre = Filtre(materia=args.materia, poblacio=args.poblacio, km=args.km,
                            latitud=args.lat, longitud=args.lon)
            r = download.run(raiz, filtre=filtre, pausa=args.pausa,
                             max_paginas=args.max_paginas, progreso=_progreso)
            print(f"[scan] descubiertas={r.fichas_descubiertas} procesos={r.procesos} "
                  f"hitos={r.hitos} actualizadas={r.actualizadas} "
                  f"cache={r.cache_hits} fetched={r.fetched}")
        elif paso == "clean":
            if not ruta_raw.exists() and args.step == "all":
                print(f"[clean] omitido (no existe {ruta_raw})")
                continue
            resumen = build.limpiar_dataset(ruta_raw, ruta_proc)
            print(f"[clean] {resumen}")
        elif paso == "enrich":
            if not ruta_proc.exists() and args.step == "all":
                print(f"[enrich] omitido (no existe {ruta_proc})")
                continue
            resumen = enriquir_dataset(ruta_proc,
                                       Path("data/reference/poblacio_municipis.csv"),
                                       ruta_enriq,
                                       informe_sin_match=Path("reports/calidad-municipios.csv"))
            print(f"[enrich] {resumen}")
        elif paso == "charts":
            staticos = generar_estaticos(ruta_enriq)
            inter = generar_interactivos(ruta_enriq)
            print(f"[charts] {len(staticos)} estáticos + {len(inter)} interactivos en reports/charts/")
        elif paso == "profile":
            destino = profile.run(raiz)
            print(f"[profile] reporte en {destino}")
        elif paso == "validate":
            res = build.validar_dataset(ruta_enriq)
            print(f"[validate] ok={res['ok']} filas={res['filas']} "
                  f"columnas={res['columnas']} procesos={res['procesos']} "
                  f"errores={res['errores']}")
        elif paso == "export":
            res = build.exportar_dataset(ruta_enriq)
            print(f"[export] filas_hitos={res['filas_hitos']} "
                  f"procesos_exportados={res['procesos_exportados']} "
                  f"ruta_procesos={res['ruta_procesos']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
