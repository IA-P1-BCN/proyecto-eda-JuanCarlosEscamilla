"""Smoke test del paquete de ingesta."""


def test_version():
    import eda_ingesta

    assert eda_ingesta.__version__ == "0.1.0"
