"""Estilo compartido de gráficos (US7·T1) — un solo punto de cambio visual.

Cada gráfico nombra la PREGUNTA de negocio que responde en su título
(convención del PRD US7). matplotlib usa backend Agg (CI sin display).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

if "inline" not in matplotlib.get_backend().lower():
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

PALETA = ["#2563eb", "#dc2626", "#16a34a", "#f59e0b", "#7c3aed", "#0d9488"]


def aplicar_estilo(ax, titulo: str, xlabel: str | None = None,
                   ylabel: str | None = None, leyenda: bool = False):
    """Aplica título (= la pregunta que responde el gráfico), ejes y rejilla."""
    ax.set_title(titulo, fontsize=12, fontweight="bold", loc="left")
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    if leyenda:
        ax.legend(frameon=True)
    return ax


def guardar(fig, nombre: str, directorio: Path | str = "reports/charts") -> Path:
    """Guarda un PNG a 150 dpi en reports/charts/ y devuelve la ruta."""
    directorio = Path(directorio)
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / f"{nombre}.png"
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    return ruta
