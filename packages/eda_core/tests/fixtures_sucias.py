"""Filas crudas SUCIAS para los tests de limpieza (T1) — cada rareza es REAL,
observada en data/raw/oposicions.csv (814 procesos, 2.786 filas de hito).

Una fila = una línea del CSV crudo (formato largo, proceso desnormalizado).
Documenta el porqué de cada rareza: si el portal cambia, estos casos son el
contrato de lo que la limpieza debe tolerar.
"""

from copy import deepcopy

_FILA_BASE = {
    "proceso_id": "20230127O46",
    "fecha_convocatoria": "2023-01-27",
    "titulo": "1 plaça de tècnic superior informàtica",
    "institucio": "Diputació de Barcelona",
    "sistema": "Oposició o prova",
    "tipus_personal": "Funcionari interí",
    "grup": "A1 - Grau universitari (correspondència amb llicenciatures)",
    "titulacio": "Titulació universitària oficial",
    "materies": "Informàtica",
    "estat": "Resolt",
    "plazas": "1",
    "hito_fecha": "2023-01-27",
    "hito_titulo": "Bases específiques. Convocatòria. Temari",
    "doc_slug": "dogc",
    "hito_url": "https://portaldogc.gencat.cat/x",
    "fuente_url": "https://cido.diba.cat/oposicions/14783298/borsa-it",
}


def fila(**cambios):
    """Copia de la fila base con las mutaciones pedidas."""
    f = deepcopy(_FILA_BASE)
    f.update(cambios)
    return f


FILAS_SUCIAS = [
    # base limpia de referencia
    fila(),
    # R1: estat vacío (47 casos reales — la ficha no pintó estado)
    fila(proceso_id="20260212O24", estat="", hito_fecha="2026-02-12",
         hito_titulo="Oferta pública", fuente_url="https://cido.diba.cat/oposicions/21078364/x"),
    # R2: grup SIN número (formato antiguo del portal)
    fila(proceso_id="20240301O11", grup="A - Grau universitari",
         hito_fecha="2024-03-01", hito_titulo="Anunci DOGC"),
    # R3: grup B técnico
    fila(proceso_id="20240302O12", grup="B - Tècnic superior",
         hito_fecha="2024-03-02", hito_titulo="Bases"),
    # R4: materies MULTI-valor (1.413 casos reales)
    fila(proceso_id="20240303O13", materies="Ensenyament universitari, Informàtica",
         hito_fecha="2024-03-03", hito_titulo="Convocatòria"),
    # R5: HITO DUPLICADO — misma (proceso, fecha, título) repetida (96 casos reales)
    fila(proceso_id="20230127O46", hito_fecha="2023-01-27",
         hito_titulo="Bases específiques. Convocatòria. Temari",
         doc_slug="plantillapublicacioweb", hito_url="https://www.diba.cat/documents/duplicado"),
    # R6: resolución — el hito que cierra el proceso (fuente de durada_mesos)
    fila(proceso_id="20230127O46", hito_fecha="2023-12-14",
         hito_titulo="Resolució final de la província. Publicació a la taula",
         doc_slug="publtaubor", hito_url="https://www.diba.cat/documents/res"),
    # R7: plazas vacía (363 casos reales — bolsa sin cuantificar)
    fila(proceso_id="20240304O14", plazas="", estat="Termini obert",
         hito_fecha="2024-03-04", hito_titulo="Oferta"),
    # R8: proceso NO VIGENTE (histórico muerto — el PO decidió mantenerlo fuera)
    fila(proceso_id="20090226O12", estat="Procés no vigent",
         fecha_convocatoria="2009-02-26", hito_fecha="2009-02-26",
         hito_titulo="Bases antigas"),
    # R9: hito sin fecha imposible de parsear (fecha vacía dentro del hito)
    fila(proceso_id="20240305O15", hito_fecha="", hito_titulo="Hito sin fecha",
         estat="Termini tancat"),
]
