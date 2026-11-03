"""CLI del pipeline: un comando, todo el proceso.

Los pasos reales (download, profile, clean, enrich, validate, export) se
implementan en US3+ con TDD; cada uno vive en su paquete (eda_ingesta, eda_core).
"""

from __future__ import annotations

import argparse
import sys

STEPS = ("download", "profile", "clean", "enrich", "validate", "export")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eda-pipeline", description=__doc__)
    parser.add_argument(
        "--step",
        choices=(*STEPS, "all"),
        default="all",
        help="paso a ejecutar (por defecto: all)",
    )
    args = parser.parse_args(argv)

    pending = STEPS if args.step == "all" else (args.step,)
    for step in pending:
        print(f"[pipeline] paso '{step}': pendiente de implementar (US3+)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
