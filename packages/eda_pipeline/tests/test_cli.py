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


def test_all_no_toca_red(monkeypatch, capsys, tmp_path):
    """'all' ejecuta el pipeline local (clean→enrich→validate→export) sin tocar red."""
    monkeypatch.chdir(tmp_path)
    for mod, nombre in ((cli.download, "run"), (cli.profile, "run")):
        monkeypatch.setattr(mod, nombre, lambda *a, **k: pytest.fail("no debe llamarse"))
    assert cli.main(["--step", "all"]) == 0
    salida = capsys.readouterr().out
    assert "[validate]" in salida and "[export]" in salida


def test_validate_y_export_steps(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.build, "validar_dataset",
        lambda ruta: {"ok": True, "filas": 2690, "columnas": 18, "procesos": 814, "errores": []},
    )
    monkeypatch.setattr(
        cli.build, "exportar_dataset",
        lambda ruta: {"filas_hitos": 2690, "procesos_exportados": 814,
                      "ruta_procesos": "data/processed/procesos_resumen.csv"},
    )
    assert cli.main(["--step", "validate"]) == 0
    assert "ok=True" in capsys.readouterr().out
    assert cli.main(["--step", "export"]) == 0
    assert "procesos_exportados=814" in capsys.readouterr().out


def test_scan_step_alias_de_download_incremental(monkeypatch, capsys):
    monkeypatch.setattr(
        cli.download, "run",
        lambda raiz, **kw: Resumen(fichas_descubiertas=10, procesos=8, hitos=25, fetched=1),
    )
    assert cli.main(["--step", "scan"]) == 0
    assert "[scan]" in capsys.readouterr().out
