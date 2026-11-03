"""CLI del pipeline: un comando, todo el proceso.

Los pasos reales (download, profile, clean, enrich, validate, export) se
implementan en US3+ con TDD; cada uno vive en su paquete (eda_ingesta, eda_core).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from eda_ingesta import download

STEPS = ("download", "scan", "profile", "clean", "enrich", "validate", "export")

PENDIENTES = ("profile", "clean", "enrich", "validate", "export")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eda-pipeline", description=__doc__)
    parser.add_argument(
        "--step",
        choices=(*STEPS, "all"),
        default="all",
        help="paso a ejecutar (por defecto: all)",
    )
    args = parser.parse_args(argv)

    # "all" ejecuta SOLO los pasos sin efectos de red; download/scan son explícitos
    pasos = PENDIENTES if args.step == "all" else (args.step,)
    raiz = Path("data/raw")
    for paso in pasos:
        if paso == "download":
            r = download.run(raiz)
            print(f"[download] descubiertas={r.fichas_descubiertas} procesos={r.procesos} "
                  f"hitos={r.hitos} descartadas={r.descartadas_materia} "
                  f"cache={r.cache_hits} fetched={r.fetched}")
        elif paso == "scan":
            r = download.run_scan(raiz)
            print(f"[scan] nuevos={r.fichas_descubiertas} añadidos={r.procesos} "
                  f"hitos={r.hitos} cache={r.cache_hits} fetched={r.fetched}")
        else:
            print(f"[pipeline] paso '{paso}': pendiente de implementar (US4+)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
