"""Tests del scan RSS incremental (T2.4) — feed real recortado, cero red."""

from pathlib import Path

from eda_ingesta.cache import CacheHtml, DescargaCacheada
from eda_ingesta.client import ClienteHttp
from eda_ingesta.rss import parse_feed, scan_rss

FIX = (Path(__file__).parent / "fixtures" / "feed_oposicions_recortado.xml").read_text()


class TransporteFalso:
    def __init__(self, cuerpo=FIX):
        self.llamadas = 0
        self._cuerpo = cuerpo

    def __call__(self, url, headers):
        self.llamadas += 1
        return 200, self._cuerpo.encode()


def descarga(tmp_path, transporte):
    cliente = ClienteHttp(fetch=transporte, dormir=lambda s: None, ahora=lambda: 0.0)
    return DescargaCacheada(cliente, CacheHtml(tmp_path))


def test_parse_feed_extrae_ids_y_links_de_los_items_con_referencia(tmp_path):
    pares = parse_feed(FIX)
    assert len(pares) == 11  # 4 de los 15 items del feed real NO llevan Número de referència
    ids, urls = zip(*pares)
    assert all(len(i) == 11 and i[8] == "O" for i in ids)  # AAAAMMDDO##
    assert all(u.startswith("http") and "/oposicions/" in u for u in urls)
    assert "20260212O24" in ids  # el item de Alcover visto en la investigación


def test_scan_filtra_conocidos_y_devuelve_solo_nuevos(tmp_path):
    conocidos = {i for i, _ in parse_feed(FIX)[:8]}
    nuevos = scan_rss(descarga(tmp_path, TransporteFalso()), conocidos)
    assert len(nuevos) == 3
    assert all(i not in conocidos for i, _ in nuevos)


def test_scan_sin_novedades_no_devuelve_nada(tmp_path):
    conocidos = {i for i, _ in parse_feed(FIX)}
    assert scan_rss(descarga(tmp_path, TransporteFalso()), conocidos) == []


def test_scan_item_sin_identificador_se_salta(tmp_path):
    roto = FIX.replace("20260212O24", "sin-referencia")
    assert len(parse_feed(roto)) == 10


def test_scan_es_cacheable_una_peticion_aun_llamando_dos_veces(tmp_path):
    t = TransporteFalso()
    d = descarga(tmp_path, t)
    scan_rss(d, set())
    scan_rss(d, set())
    assert t.llamadas == 1  # el feed pasa por la caché — 1 petición de red total
