"""Smoke test del paquete core."""


def test_version():
    import eda_core

    assert eda_core.__version__ == "0.1.0"
