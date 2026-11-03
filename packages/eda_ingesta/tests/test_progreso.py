"""Tests de progreso visible + filtro de paginación (T4.4)."""

from pathlib import Path

from eda_ingesta.client import Respuesta
from eda_ingesta.crawl import crawl_listado
from eda_ingesta.download import run

FIX = Path(__file__).parent / "fixtures"
P1 = (FIX / "listado_materia24_p1.html").read_text()
P2 = (FIX / "listado_materia24_p2.html").read_text()


class DescargaFalsa:
    """Sirve p1 para el listado sin page= y p2 para los que traen page=."""

    def __init__(self, paginas):
        self.urls: list[str] = []
        self._paginas = paginas

    def get(self, url: str) -> Respuesta:
        self.urls.append(url)
        cuerpo = self._paginas["p2"] if "page=" in url else self._paginas["p1"]
        return Respuesta(url=url, status=200, contenido=cuerpo.encode())


def test_crawl_reporta_progreso_por_pagina():
    eventos: list[dict] = []
    crawl_listado(DescargaFalsa({"p1": P1, "p2": P2}), progreso=eventos.append, max_paginas=2)
    paginas = [e for e in eventos if e["fase"] == "listado"]
    assert len(paginas) == 2
    assert paginas[0]["fichas"] == 48 and paginas[1]["fichas"] == 2


def test_crawl_preserva_el_filtro_de_materia_en_paginacion():
    """Regresión REAL: la paginación del portal pierde filtreMateria.

    El 'next' de la página 2+ llegó sin el filtro → el crawler caminaba el
    listado completo (1.536 procesos) en vez de los 237 de Informàtica.
    Debe reconstruir la URL con el filtro antes de pedir la página.
    """
    p1_roto = P1.replace(
        "filtreMateria%5Boptions%5D%5B0%5D=24&amp;page=2", "page=2"
    )
    assert "filtreMateria" not in p1_roto.split("page=2")[0][-200:] or "page=2" in p1_roto
    d = DescargaFalsa({"p1": p1_roto, "p2": P2})
    crawl_listado(d)
    segundas = [u for u in d.urls if "page=" in u]
    assert segundas, "debe pedir la página 2"
    assert all("filtreMateria" in u for u in segundas), "el filtro debe reconstruirse"


def test_run_emite_progreso_por_ficha_con_pausa(tmp_path):
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "test_download_rig", Path(__file__).parent / "test_download.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    eventos: list[dict] = []
    run(tmp_path, fetch=mod.CIDOFalso(), max_paginas=2, progreso=eventos.append, pausa=0.25)
    fichas = [e for e in eventos if e["fase"] == "ficha"]
    assert fichas, "debe haber eventos de ficha"
    assert all("url" in e and "hit" in e and "status" in e for e in fichas)
    assert fichas[0]["pausa"] == 0.25
