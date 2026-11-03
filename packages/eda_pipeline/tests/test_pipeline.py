"""Tests del CLI del pipeline (stub de US2)."""

from eda_pipeline.cli import STEPS, main


def test_pasos_definidos():
    assert set(STEPS) == {"download", "scan", "profile", "clean", "enrich", "validate", "export"}


def test_run_all_sin_error(capsys):
    assert main(["--step", "all"]) == 0
    assert "pendiente de implementar" in capsys.readouterr().out
