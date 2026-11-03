"""Tests de la caché HTML resumible (T2.2) — tmp_path, transporte falso, cero red."""

import pytest

from eda_ingesta.cache import CacheHtml, DescargaCacheada
from test_client import TransporteFalso, cliente


def descarga(tmp_path, respuestas, **kw):
    t = TransporteFalso(respuestas)
    d = DescargaCacheada(cliente(t, pausa=0), CacheHtml(tmp_path))
    return d, t


def test_primera_miss_segunda_hit_sin_nueva_peticion(tmp_path):
    d, t = descarga(tmp_path, [(200, b"<html>ficha</html>")])
    r1 = d.get("http://x/ficha")
    assert r1.contenido == b"<html>ficha</html>" and r1.hit is False
    assert d.cache.misses == 1 and d.cache.hits == 0

    r2 = d.get("http://x/ficha")
    assert r2.contenido == b"<html>ficha</html>" and r2.hit is True
    assert d.cache.hits == 1
    assert len(t.llamadas) == 1  # la red SOLO una vez — idempotencia visible


def test_urls_distintas_ficheros_distintos(tmp_path):
    d, _ = descarga(tmp_path, [(200, b"a"), (200, b"b")])
    assert d.get("http://x/1").contenido == b"a"
    assert d.get("http://x/2").contenido == b"b"
    assert d.get("http://x/1").contenido == b"a"  # cada url con su caché


def test_contenido_binario_intacto(tmp_path):
    d, _ = descarga(tmp_path, [(200, b"\x00\xff\xfe<html>\xc3\xa7</html>")])
    assert d.get("http://x/bin") .contenido == b"\x00\xff\xfe<html>\xc3\xa7</html>"
    assert d.get("http://x/bin").contenido == b"\x00\xff\xfe<html>\xc3\xa7</html>"


def test_fichero_creado_en_la_raiz_indicada(tmp_path):
    d, _ = descarga(tmp_path, [(200, b"x")])
    d.get("http://x/a")
    assert list(tmp_path.glob("*.html"))  # el HTML vive en la raíz pedida


def test_4xx_cache_negativa_mismo_dia_y_recuperacion_al_siguiente(tmp_path):
    from datetime import date, timedelta

    t = TransporteFalso([(404, b""), (200, b"aparecio")])
    from eda_ingesta.cache import CacheHtml
    from eda_ingesta.client import ClienteHttp

    cliente = ClienteHttp(fetch=t, dormir=lambda s: None, ahora=lambda: 0.0)
    d = DescargaCacheada(cliente, CacheHtml(tmp_path))

    r1 = d.get("http://x/ghost")
    assert r1.status == 404 and r1.hit is False  # 1ª vez: red
    r2 = d.get("http://x/ghost")
    assert r2.status == 404 and r2.hit is True   # mismo día: caché negativa, sin red
    assert len(t.llamadas) == 1

    d.hoy = lambda: date.today() + timedelta(days=1)  # día siguiente: se reintenta
    r3 = d.get("http://x/ghost")
    assert r3.status == 200 and r3.contenido == b"aparecio"


def test_5xx_agotado_no_se_cachea(tmp_path):
    d, t = descarga(tmp_path, [(503, b""), (503, b""), (503, b""), (200, b"ok")])
    with pytest.raises(Exception):  # ClienteAgotado tras 3 intentos
        d.get("http://x/caido")
    r = d.get("http://x/caido")  # reintento posterior del llamador: puede prosperar
    assert r.status == 200 and len(t.llamadas) == 4
