"""Cliente HTTP educado: pausa entre peticiones, User-Agent propio, backoff.

El transporte se inyecta (`fetch`) para que los tests corran sin red y con
reloj fake. El fetch por defecto usa urllib con el User-Agent del proyecto.
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import NamedTuple

USER_AGENT = "eda-oposicions/0.1 (EDA bootcamp Factoria F5; +https://github.com/IA-P1-BCN/proyecto-eda-JuanCarlosEscamilla)"

# Transporte: url + headers → (status, contenido). Los fallos transitorios se
# señalan lanzando excepción (timeout/red/5xx); el cliente decide los reintentos.
Fetch = Callable[[str, dict[str, str]], tuple[int, bytes]]


class Respuesta(NamedTuple):
    url: str
    status: int
    contenido: bytes
    hit: bool = False  # True si vino de caché (la marca DescargaCacheada)


class ClienteAgotado(RuntimeError):
    """Se agotaron los reintentos ante fallos transitorios."""

    def __init__(self, url: str, intentos: int):
        self.url = url
        self.intentos = intentos
        super().__init__(f"{url}: agotados {intentos} intentos")


class ClienteHttp:
    """get(url) con pausa mínima entre peticiones y reintentos con backoff.

    - Pausa: espera mínima entre dos peticiones consecutivas (educación).
    - Reintentos: solo ante fallos transitorios (red/timeout/5xx); los 4xx son
      permanentes y se devuelven tal cual para que el llamador los clasifique.
    - Backoff: espera creciente (base * 2**intento) entre reintentos.
    """

    _TRANSITORIOS = (TimeoutError, urllib.error.URLError, OSError)

    def __init__(
        self,
        fetch: Fetch | None = None,
        *,
        pausa: float = 1.0,
        reintentos: int = 3,
        backoff: float = 0.5,
        user_agent: str = USER_AGENT,
        dormir: Callable[[float], None] = time.sleep,
        ahora: Callable[[], float] = time.monotonic,
    ):
        self._fetch: Fetch = fetch if fetch is not None else _fetch_por_defecto
        self._headers = {"User-Agent": user_agent}
        self.pausa = pausa
        self.reintentos = reintentos
        self.backoff = backoff
        self._dormir = dormir
        self._ahora = ahora
        self._ultima: float | None = None

    def get(self, url: str) -> Respuesta:
        for intento in range(self.reintentos):
            self._esperar_pausa()
            self._ultima = self._ahora()  # la pausa mide entre inicios de petición
            try:
                status, contenido = self._fetch(url, dict(self._headers))
            except self._TRANSITORIOS:
                if intento < self.reintentos - 1:
                    self._dormir(self.backoff * 2**intento)
                continue
            if status >= 500:
                if intento < self.reintentos - 1:
                    self._dormir(self.backoff * 2**intento)
                continue
            return Respuesta(url=url, status=status, contenido=contenido)
        raise ClienteAgotado(url=url, intentos=self.reintentos)

    def _esperar_pausa(self) -> None:
        if self._ultima is None:
            return
        restante = self.pausa - (self._ahora() - self._ultima)
        if restante > 0:
            self._dormir(restante)


def _fetch_por_defecto(url: str, headers: dict[str, str]) -> tuple[int, bytes]:
    """Fetch real con urllib. Devuelve el status tal cual (incluidos 5xx) —
    la política de reintentos vive en el cliente, no en el transporte. Los
    fallos de red/timeout sí se lanzan como excepciones (transitorios)."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
