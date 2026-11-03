"""Tests del crawler de listados (T2.3) — fixtures congeladas, cero red."""

from pathlib import Path

from eda_ingesta.crawl import (
    crawl_listado,
    extraer_fichas,
    extraer_siguiente,
    total_resultados,
    url_listado,
)

FIXTURES = Path(__file__).parent / "fixtures"
P1 = (FIXTURES / "listado_materia24_p1.html").read_text()
P2 = (FIXTURES / "listado_materia24_p2.html").read_text()


class DescargaFalsa:
    """Sirve p1 para la primera página y p2 para las que traen page=2+."""

    def __init__(self):
        self.urls: list[str] = []

    def get(self, url):
        self.urls.append(url)
        html = P2 if "page=" in url else P1
        from eda_ingesta.client import Respuesta

        return Respuesta(url=url, status=200, contenido=html.encode())


def test_extrae_48_fichas_reales_de_la_pagina_congelada():
    fichas = extraer_fichas(P1)
    assert len(fichas) == 48
    assert len(set(fichas)) == 48
    assert all(f.startswith("https://cido.diba.cat/oposicions/") for f in fichas)
    assert any("/14783298/" in f for f in fichas)  # primera ficha conocida (IT, DIBA)


def test_total_resultados_de_la_pagina():
    assert total_resultados(P1) == 237


def test_siguiente_pagina_decodificada():
    sig = extraer_siguiente(P1)
    assert sig is not None and "page=2" in sig
    assert "&amp;" not in sig  # bs4 decodifica entidades


def test_ultima_pagina_sin_siguiente():
    assert extraer_siguiente(P2) is None


def test_url_listado_lleva_el_filtro_de_materia():
    url = url_listado()
    assert "filtreMateria" in url and "24" in url and url.startswith("https://cido.diba.cat")


def test_crawl_recorre_hasta_agotar_y_deduplica():
    d = DescargaFalsa()
    fichas = crawl_listado(d)
    assert len(fichas) == 50  # 48 reales + 2 sintéticas de p2, sin duplicados
    assert len(d.urls) == 2   # exactamente 2 páginas: para al no haber next


def test_crawl_respeta_max_paginas():
    d = DescargaFalsa()
    fichas = crawl_listado(d, max_paginas=1)
    assert len(fichas) == 48 and len(d.urls) == 1
