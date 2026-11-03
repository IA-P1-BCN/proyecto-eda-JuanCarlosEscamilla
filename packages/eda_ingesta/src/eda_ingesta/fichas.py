"""Parser de fichas del CIDO: HTML → dimensión proceso + hitos en formato largo.

Campos verificados sobre fichas reales congeladas (tests/fixtures):
- dt/dd consecutivos: Identificador, Sistema, Tipus de personal, Grup, Matèries…
- hitos: filas <tr> con <time datetime="ISO"> + título en la 4ª celda + doc link
- institució: parte [1] del <title> ("título | Ens | Processos selectius | CIDO")
- estat: token de estado en el texto de la página (Resolt / Termini obert / …)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .parsers import IdentificadorInvalido, parse_identificador

_MATERIA_IT = "informàtica"
_RE_ESTADO = re.compile(
    r"\b(Resolt|Termini obert|Termini pendent|Termini tancat|Procés no vigent)\b", re.IGNORECASE
)


@dataclass
class Hito:
    fecha: date | None
    titulo: str
    url: str | None


@dataclass
class Proceso:
    identificador: str | None
    fecha_convocatoria: date | None
    titulo: str
    url: str
    institucio: str
    sistema: str | None
    tipus_personal: str | None
    grup: str | None
    titulacio: str | None
    materies: list[str] = field(default_factory=list)
    estat: str | None = None
    hitos: list[Hito] = field(default_factory=list)


def _campos_dt_dd(sopa: BeautifulSoup) -> dict[str, str]:
    pares: dict[str, str] = {}
    nodos = sopa.find_all(["dt", "dd"])
    for i in range(len(nodos) - 1):
        if nodos[i].name == "dt" and nodos[i + 1].name == "dd":
            pares[nodos[i].get_text(" ", strip=True)] = nodos[i + 1].get_text(" ", strip=True)
    return pares


def parse_ficha(html: str, url: str) -> Proceso:
    sopa = BeautifulSoup(html, "html.parser")
    titulo = sopa.title.get_text(" ", strip=True) if sopa.title else ""
    partes = [p.strip() for p in titulo.split("|")]
    institucio = partes[1] if len(partes) >= 3 else ""

    campos = _campos_dt_dd(sopa)
    identificador = campos.get("Identificador")
    fecha_convocatoria = None
    if identificador:
        try:
            fecha_convocatoria = parse_identificador(identificador)
        except IdentificadorInvalido:
            fecha_convocatoria = None  # raw capturado; el log de calidad registrará

    materies = [
        m.strip()
        for m in campos.get("Matèries", "").split(",")
        if m.strip()
    ]

    hitos: list[Hito] = []
    for tr in sopa.find_all("tr"):
        t = tr.find("time")
        if t is None:
            continue
        tds = tr.find_all("td")
        titulo_hito = tds[3].get_text(" ", strip=True) if len(tds) >= 4 else ""
        a = tr.find("a", href=True)
        hitos.append(
            Hito(
                fecha=date.fromisoformat(t["datetime"][:10]),
                titulo=titulo_hito,
                url=urljoin(url, a["href"]) if a else None,
            )
        )

    texto = sopa.get_text(" ", strip=True)
    m_estat = _RE_ESTADO.search(texto)

    return Proceso(
        identificador=identificador,
        fecha_convocatoria=fecha_convocatoria,
        titulo=titulo.split("|")[0].strip(),
        url=url,
        institucio=institucio,
        sistema=campos.get("Sistema de selecció"),
        tipus_personal=campos.get("Tipus de personal"),
        grup=campos.get("Grup de titulació o assimilat"),
        titulacio=campos.get("Titulació requerida"),
        materies=materies,
        estat=m_estat.group(1) if m_estat else None,
        hitos=hitos,
    )


def es_informatica(proceso: Proceso) -> bool:
    """Filtro de materia: la ficha manda (el feed RSS no filtra)."""
    return any(_MATERIA_IT in m.lower() for m in proceso.materies)
