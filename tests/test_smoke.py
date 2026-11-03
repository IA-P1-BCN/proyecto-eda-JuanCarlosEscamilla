"""Smoke test del esqueleto: el paquete importa y el pipeline responde."""

import eda
from eda.pipeline import STEPS, main


def test_version():
    assert eda.__version__ == "0.1.0"


def test_pipeline_steps_definidos():
    assert set(STEPS) == {"download", "profile", "clean", "enrich", "validate", "export"}


def test_pipeline_run_all_sin_error(capsys):
    assert main(["--step", "all"]) == 0
    out = capsys.readouterr().out
    assert "pendiente de implementar" in out
