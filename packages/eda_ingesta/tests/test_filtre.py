"""Tests del filtro configurable (materia + proximidad Vic 45km) y del corte/reanudación."""

from pathlib import Path

from eda_ingesta.crawl import Filtre, url_listado
from eda_ingesta.download import run


def test_filtre_por_defecto_vic_45km_materia24():
    f = Filtre()
    assert f.materia == 24 and f.poblacio == "Vic" and f.km == 45
    assert f.latitud == "41,929968" and f.longitud == "2,254264"


def test_url_listado_lleva_todos_los_parametros_y_sin_token():
    url = url_listado(Filtre())
    assert "filtreMateria%5Boptions%5D%5B%5D=24" in url
    assert "filtreProximitat%5Bpoblacio%5D=Vic" in url
    assert "filtreProximitat%5Bkm%5D=45" in url
    assert "showAs=GRID" in url
    assert "_token" not in url  # nunca credenciales en URLs versionadas


def test_url_listado_pagina_anade_page():
    assert "page=3" in url_listado(Filtre(), pagina=3)


def test_filtre_personalizado_cambia_la_url():
    url = url_listado(Filtre(materia=7, poblacio="Girona", km=20, latitud="41,98", longitud="2,82"))
    assert "filtreMateria%5Boptions%5D%5B%5D=7" in url
    assert "filtreProximitat%5Bpoblacio%5D=Girona" in url
    assert "km%5D=20" in url


def test_corte_guarda_parcial_y_avisa(tmp_path):
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "test_download_rig", Path(__file__).parent / "test_download.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)

    class CorteATercera(mod.CIDOFalso):
        llamadas_buenas = 0

        def __call__(self, url, headers):
            type(self).llamadas_buenas += 1
            if type(self).llamadas_buenas > 12:  # listados + feed + ~9 fichas
                raise KeyboardInterrupt
            return super().__call__(url, headers)

    eventos: list[dict] = []
    r = run(tmp_path, fetch=CorteATercera(), max_paginas=2, progreso=eventos.append, pausa=0)
    assert r.cortado is True
    assert any(e["fase"] == "corte" for e in eventos)
    assert (tmp_path / "oposicions.csv").exists()  # parcial guardado para reanudar
    assert "INTERRUMPIDO" in "".join(e.get("detalle", "") for e in eventos if e["fase"] == "corte")
