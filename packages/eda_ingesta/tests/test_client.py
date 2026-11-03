"""Tests del cliente HTTP educado (T2.1) — transporte falso, reloj fake, cero red."""

import pytest

from eda_ingesta.client import ClienteAgotado, ClienteHttp


class TransporteFalso:
    """Simula la red: respuestas en cola, reloj propio, registra llamadas."""

    def __init__(self, respuestas):
        self.cola = list(respuestas)  # (status, bytes) o Exception
        self.llamadas: list[tuple[str, dict]] = []
        self.ahora = 0.0
        self.suenos: list[float] = []

    def __call__(self, url, headers):
        self.llamadas.append((url, dict(headers)))
        self.ahora += 0.1  # cada petición "tarda" 100 ms
        item = self.cola.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    def dormir(self, segundos):
        self.suenos.append(segundos)
        self.ahora += segundos


def cliente(transporte, **kw):
    return ClienteHttp(
        fetch=transporte,
        dormir=transporte.dormir,
        ahora=lambda: transporte.ahora,
        **kw,
    )


def test_pausa_entre_peticiones():
    t = TransporteFalso([(200, b"a"), (200, b"b")])
    c = cliente(t, pausa=1.0)
    c.get("http://x/1")
    c.get("http://x/2")
    # primera petición: sin espera; entre 1ª y 2ª: pausa - tiempo de la 1ª (0.1)
    assert len(t.suenos) == 1
    assert t.suenos[0] == pytest.approx(0.9)


def test_user_agent_presente_en_cada_peticion():
    t = TransporteFalso([(200, b"a"), (200, b"b")])
    c = cliente(t)
    c.get("http://x/1")
    c.get("http://x/2")
    for _url, headers in t.llamadas:
        assert headers["User-Agent"].startswith("eda-oposicions/")


def test_reintenta_5xx_con_backoff_exponencial():
    t = TransporteFalso([(503, b""), (503, b""), (200, b"ok")])
    c = cliente(t, pausa=0, reintentos=3, backoff=0.5)
    r = c.get("http://x/")
    assert r.status == 200 and r.contenido == b"ok"
    assert len(t.llamadas) == 3
    assert t.suenos == pytest.approx([0.5, 1.0])  # backoff creciente entre reintentos


def test_agota_reintentos_y_lanza_tipado():
    t = TransporteFalso([(503, b""), (503, b""), (503, b"")])
    c = cliente(t, pausa=0, reintentos=3, backoff=0.5)
    with pytest.raises(ClienteAgotado) as e:
        c.get("http://x/")
    assert e.value.intentos == 3
    assert len(t.llamadas) == 3


def test_404_no_reintenta_es_permanente():
    t = TransporteFalso([(404, b"no hay")])
    c = cliente(t, pausa=0, reintentos=3)
    r = c.get("http://x/")
    assert r.status == 404
    assert len(t.llamadas) == 1


def test_timeout_es_transitorio():
    t = TransporteFalso([TimeoutError("lento"), TimeoutError("lento"), (200, b"ok")])
    c = cliente(t, pausa=0, reintentos=3, backoff=0.5)
    r = c.get("http://x/")
    assert r.status == 200
    assert len(t.llamadas) == 3
