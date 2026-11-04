"""Tests de entregables de US12 (#12, #61, #62, #63, #64)."""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]


def test_informe_calidad_datos_cumple_ac():
    """AC 1-3 de US12 (#61): docs/informe-calidad-datos.md existe y contiene todas las secciones."""
    ruta = RAIZ / "docs" / "informe-calidad-datos.md"
    assert ruta.exists(), f"Falta {ruta}"
    texto = ruta.read_text(encoding="utf-8")

    # Resume los ADRs 0001 a 0005
    for adr in ("0001", "0002", "0003", "0004", "0005"):
        assert adr in texto, f"Falta referencia al ADR-{adr}"

    # Incluye taxonomía E1/E2/E3 con acción sugerida
    for clase in ("E1", "E2", "E3"):
        assert clase in texto, f"Falta clase de error {clase}"
    assert "Acción sugerida" in texto or "acción sugerida" in texto.lower()

    # Responde explícitamente a "¿qué NO sabemos aún?"
    assert "¿Qué NO sabemos aún?" in texto or "¿qué NO sabemos aún?" in texto


def test_slides_revealjs_y_taskfile():
    """AC 4-5 de US12 (#62): Taskfile define `slides` y docs/presentacion/slides.qmd genera revealjs."""
    taskfile = (RAIZ / "Taskfile.yml").read_text(encoding="utf-8")
    assert "slides:" in taskfile
    assert "quarto render docs/presentacion/slides.qmd" in taskfile

    qmd = RAIZ / "docs" / "presentacion" / "slides.qmd"
    assert qmd.exists(), f"Falta {qmd}"
    contenido = qmd.read_text(encoding="utf-8")
    assert "revealjs" in contenido
    assert (RAIZ / "docs" / "presentacion" / "slides.html").exists()

