"""Hash canónico del dataset (openspec: fix-dataset-release-hash).

CIDO firma cada enlace con un token `&<64 hex>` nuevo en cada descarga; el release
solo debe publicarse cuando cambian los datos, no los tokens ni el orden de filas.
"""

import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
SCRIPT = RAIZ / ".github" / "scripts" / "dataset-hash.sh"

CABECERA = "proceso_id,hito_fecha,hito_url,fuente_url\n"
TOK_A = "a" * 64
TOK_B = "0123456789abcdef" * 4


def _fila(pid: str, fecha: str, tok: str) -> str:
    return f"{pid},{fecha},https://bop.diba.cat/x.pdf&1&{tok},https://cido.diba.cat/oposicions/1\n"


def _hash(tmp_path: Path, nombre: str, contenido: str) -> str:
    f = tmp_path / nombre
    f.write_text(contenido, encoding="utf-8")
    out = subprocess.run(["bash", str(SCRIPT), str(f)], check=True, capture_output=True, text=True)
    return out.stdout.strip()


def test_tokens_y_orden_no_cambian_hash(tmp_path):
    a = _hash(tmp_path, "a.csv", CABECERA + _fila("P1", "2024-01-01", TOK_A) + _fila("P2", "2024-02-01", TOK_A))
    b = _hash(tmp_path, "b.csv", CABECERA + _fila("P2", "2024-02-01", TOK_B) + _fila("P1", "2024-01-01", TOK_B))
    assert len(a) == 12
    assert a == b


def test_hito_nuevo_cambia_hash(tmp_path):
    base = CABECERA + _fila("P1", "2024-01-01", TOK_A)
    a = _hash(tmp_path, "a.csv", base)
    b = _hash(tmp_path, "b.csv", base + _fila("P1", "2024-03-01", TOK_A))
    assert a != b


def test_release_usa_hash_canonico():
    script = (RAIZ / ".github" / "scripts" / "dataset-release.sh").read_text(encoding="utf-8")
    assert "dataset-hash.sh" in script
