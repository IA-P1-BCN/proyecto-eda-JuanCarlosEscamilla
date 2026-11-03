"""Tests del scan RSS incremental (T2.4) — feed real recortado, cero red."""

from pathlib import Path

from eda_ingesta.client import Respuesta
from eda_ingesta.rss import URL_FEED, parse_feed, scan_rss

FIX = (Path(__file__).parent / "fixtures" / "feed_oposicions_recortado.xml").read_text()


class DescargaFalsa:
    def __init__(self, cuerpo=FIX):
        self.llamadas = 0
        self._cuerpo = cuerpo

    def get(self, url):
        self.llamadas += 1
        return Respuesta(url=url, status=200, contenido=self._cuerpo.encode())


def test_parse_feed_extrae_ids_y_links_de_todos_los_items():
    pares = parse_feed(FIX)
    assert len(pares) == 15
    ids, urls = zip(*pares)
    assert all(len(i) == 11 and i[8] == "O" for i in ids)  # AAAAMMDDO##
    assert all(u.startswith("http") and "/oposicions/" in u for u in urls)
    assert "20260212O24" in ids  # el item de Alcover visto en la investigación


def test_scan_filtra_conocidos_y_devuelve_solo_nuevos():
    conocidos = {i for i, _ in parse_feed(FIX)[:12]}
    nuevos = scan_rss(DescargaFalsa(), conocidos)
    assert len(nuevos) == 3
    assert all(i not in conocidos for i, _ in nuevos)


def test_scan_sin_novedades_no_devuelve_nada():
    conocidos = {i for i, _ in parse_feed(FIX)}
    assert scan_rss(DescargaFalsa(), conocidos) == []


def test_scan_item_sin_identificador_se_salta():
    roto = FIX.replace("20260212O24", "sin-referencia")
    assert len(parse_feed(roto)) == 14


def test_scan_es_cacheable_una_peticion_por_ejecucion():
    d = DescargaFalsa()
    scan_rss(d, set())
    scan_rss(d, set())
    assert d.llamadas == 1  # el feed pasa por la caché — 1 petición aunque scan 2 veces


def test_scan_solo_lee_el_feed_de_oposicions():
    d = DescargaFalsa()
    scan_rss(d, set())
    assert d.llamadas and URL_FEED in URL_FEED  # la URL única del diseño
