"""CLI del pipeline: un comando, todo el proceso.

Los pasos reales (download, profile, clean, enrich, validate, export) se
implementan en US3+ con TDD; cada uno vive en su paquete (eda_ingesta, eda_core).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from eda_ingesta import download, profile

STEPS = ("download", "scan", "profile", "clean", "enrich", "validate", "export")

PENDIENTES = ("clean", "enrich", "validate", "export")


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eda-pipeline", description=__doc__)
    parser.add_argument(
        "--step",
        choices=(*STEPS, "all"),
        default="all",
        help="paso a ejecutar (por defecto: all)",
    )
    parser.add_argument("--pausa", type=float, default=1.0,
                        help="segundos de pausa entre peticiones al CIDO (default 1.0)")
    parser.add_argument("--max-paginas", type=int, default=None,
                        help="limita páginas del listado (bootstrap parcial para pruebas)")
    args = parser.parse_args(argv)

    # "all" ejecuta SOLO los pasos sin efectos de red; download/scan son explícitos
    pasos = PENDIENTES if args.step == "all" else (args.step,)
    raiz = Path("data/raw")
    for paso in pasos:
        if paso == "download":
            r = download.run(raiz, pausa=args.pausa, max_paginas=args.max_paginas,
                             progreso=_progreso)
            print(f"[download] descubiertas={r.fichas_descubiertas} procesos={r.procesos} "
                  f"hitos={r.hitos} descartadas={r.descartadas_materia} "
                  f"cache={r.cache_hits} fetched={r.fetched}")
        elif paso == "scan":
            r = download.run_scan(raiz, pausa=args.pausa, progreso=_progreso)
            print(f"[scan] nuevos={r.fichas_descubiertas} añadidos={r.procesos} "
                  f"hitos={r.hitos} cache={r.cache_hits} fetched={r.fetched}")
        elif paso == "profile":
            destino = profile.run(raiz)
            print(f"[profile] reporte en {destino}")
        else:
            print(f"[pipeline] paso '{paso}': pendiente de implementar (US4+)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
