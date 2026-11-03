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

# Transporte: url + headers → (status, contenido, cabeceras). Los fallos
# transitorios (red/timeout) se lanzan; los 4xx/5xx vuelven como status para
# que el cliente aplique su política (429 honra Retry-After, 5xx backoff).
Fetch = Callable[[str, dict[str, str]], tuple[int, bytes, dict[str, str]]]


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
                status, contenido, cabeceras = self._fetch(url, dict(self._headers))
            except self._TRANSITORIOS:
                if intento < self.reintentos - 1:
                    self._dormir(self.backoff * 2**intento)
                continue
            if status == 429:  # rate-limiting del servidor: manda él
                if intento < self.reintentos - 1:
                    self._dormir(_retry_after(cabeceras, self.backoff * 2**intento))
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


def _retry_after(cabeceras: dict[str, str], por_defecto: float) -> float:
    """Retry-After en segundos (numérico); si viene como fecha u otra cosa, fallback."""
    valor = cabeceras.get("Retry-After") or cabeceras.get("retry-after")
    try:
        return max(0.0, float(valor))
    except (TypeError, ValueError):
        return por_defecto


def _fetch_por_defecto(url: str, headers: dict[str, str]) -> tuple[int, bytes, dict[str, str]]:
    """Fetch real con urllib. Devuelve status/cabeceras tal cual — la política
    de reintentos vive en el cliente, no en el transporte. Los fallos de
    red/timeout sí se lanzan como excepciones (transitorios)."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers or {})
