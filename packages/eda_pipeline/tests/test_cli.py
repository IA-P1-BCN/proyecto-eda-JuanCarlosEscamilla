"""Tests del despacho del CLI (T4.3): los pasos llegan al módulo correcto."""

from pathlib import Path

import pytest

from eda_pipeline import cli
from eda_ingesta.download import Resumen


def test_download_step_llama_al_modulo(monkeypatch, capsys, tmp_path):
    visto = {}

    def fake_run(raiz, **kw):
        visto["raiz"] = raiz
        return Resumen(fichas_descubiertas=61, procesos=2, hitos=44, fetched=64)

    monkeypatch.setattr(cli.download, "run", fake_run)
    assert cli.main(["--step", "download"]) == 0
    assert visto["raiz"] == Path("data/raw")
    assert "descubiertas=61" in capsys.readouterr().out


def test_profile_step_escribe_reporte(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(cli.profile, "run", lambda raiz: tmp_path / "profiling.md")
    assert cli.main(["--step", "profile"]) == 0
    assert "profiling.md" in capsys.readouterr().out


def test_all_no_toca_red(monkeypatch, capsys):
    """'all' ejecuta solo pasos pendientes: download/scan/profile NO se llaman."""
    for mod, nombre in ((cli.download, "run"), (cli.profile, "run")):
        monkeypatch.setattr(mod, nombre, lambda *a, **k: pytest.fail("no debe llamarse"))
    assert cli.main(["--step", "all"]) == 0
    assert "pendiente de implementar (US4+)" in capsys.readouterr().out
