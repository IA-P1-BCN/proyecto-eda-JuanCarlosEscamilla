"""Tests del estilo compartido (US7·T1) — cambiar la función cambia todos los gráficos."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sin display en tests/CI
import matplotlib.pyplot as plt

from eda_core.viz import PALETA, aplicar_estilo, guardar


def test_aplicar_estilo_configura_titulo_ejes():
    fig, ax = plt.subplots()
    ax.bar(["a", "b"], [1, 2])
    aplicar_estilo(ax, "P1 — ¿Cuánto tarda?", xlabel="meses", ylabel="procesos", leyenda=True)
    assert ax.get_title(loc="left") == "P1 — ¿Cuánto tarda?"
    assert ax.get_xlabel() == "meses"
    assert ax.get_ylabel() == "procesos"
    assert ax.get_legend() is not None
    plt.close(fig)


def test_guardar_crea_png_en_el_directorio(tmp_path):
    fig, ax = plt.subplots()
    ax.plot([1, 2], [3, 4])
    ruta = guardar(fig, "p1_test", tmp_path)
    plt.close(fig)
    assert ruta.exists() and ruta.stat().st_size > 1000
    assert ruta.suffix == ".png"


def test_paleta_suficiente_para_categorias():
    assert len(PALETA) >= 5
