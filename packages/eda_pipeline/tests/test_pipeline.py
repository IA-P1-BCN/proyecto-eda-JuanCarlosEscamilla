"""Tests del CLI del pipeline (stub de US2)."""

from eda_pipeline.cli import STEPS, main


def test_pasos_definidos():
    assert set(STEPS) == {"download", "profile", "clean", "enrich", "charts", "validate", "export"}


def test_run_all_sin_error(capsys, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["--step", "all"]) == 0
    salida = capsys.readouterr().out
    assert "[validate]" in salida and "[export]" in salida
