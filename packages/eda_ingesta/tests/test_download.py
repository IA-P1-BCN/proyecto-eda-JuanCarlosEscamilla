"""Tests del paso download del pipeline (T4.1) — CIDO simulado completo, cero red."""

import csv
from pathlib import Path

from eda_ingesta.download import run, run_scan

FIX = Path(__file__).parent / "fixtures"
P1 = (FIX / "listado_materia24_p1.html").read_text()
P2 = (FIX / "listado_materia24_p2.html").read_text()
FEED = (FIX / "feed_oposicions_recortado.xml").read_text()
FICHA_IT = (FIX / "ficha_it_diba_14783298.html").read_text()
FICHA_AL = (FIX / "ficha_borsa_alcover_21078364.html").read_text()

FICHA_SINTETICA_IT = """<html><head><title>1 plaça de fake informàtic | Ajuntament de Fakeville | Processos selectius | Cercador CIDO</title></head><body>
<dl><dt>Identificador</dt><dd>20260601O01</dd><dt>Sistema de selecció</dt><dd>Oposició o prova</dd><dt>Tipus de personal</dt><dd>Funcionari interí</dd><dt>Grup de titulació o assimilat</dt><dd>C1 - FP</dd><dt>Matèries</dt><dd>Informàtica</dd></dl>
<table><tr><td><time datetime="2026-06-01">01/06/2026</time></td><td>DOGC</td><td>1</td><td>Anunci de la plaça</td><td><a href="https://portaldogc.gencat.cat/x">PDF</a></td></tr></table>
</body></html>"""

FICHA_SINTETICA_NO_IT = FICHA_SINTETICA_IT.replace("Informàtica", "Administració general").replace(
    "fake informàtic", "fake administratiu")


class CIDOFalso:
    """Enruta URLs como el portal real: listados, feed, fichas congeladas y sintéticas."""

    def __init__(self, feed=FEED):
        self.llamadas = 0
        self._feed = feed

    def __call__(self, url, headers):
        self.llamadas += 1
        if "rss/oposicions" in url:
            return 200, self._feed.encode()
        if "page=" in url:
            return 200, P2.encode()
        if "oposicions?" in url:
            return 200, P1.encode()
        if "14783298" in url:
            return 200, FICHA_IT.encode()
        if "21078364" in url:
            return 200, FICHA_AL.encode()
        if "90000001" in url:
            return 200, FICHA_SINTETICA_IT.encode()
        if "90000002" in url:
            return 200, FICHA_SINTETICA_NO_IT.encode()
        return 404, b"no existe"


def test_run_bootstrap_completo(tmp_path):
    r = run(tmp_path, fetch=CIDOFalso(), max_paginas=2)
    # 48 crawler (https) + 11 del feed (http) + 2 sintéticas ya en p2 = 61 URLs únicas
    # (el feed no filtra materia: sus fichas no-IT se descartan en el parseo)
    assert r.fichas_descubiertas == 61
    assert r.procesos == 2
    assert r.descartadas_materia == 2
    assert r.hitos >= 20  # IT_DIBA aporta ~45 filas <time> de tabla
    assert r.fetched >= 5  # 2 listados + feed + fichas nuevas
    ruta = tmp_path / "oposicions.csv"
    assert ruta.exists()
    filas = list(csv.DictReader(ruta.open()))
    assert {f["proceso_id"] for f in filas} == {"20230127O46", "20260601O01"}


def test_run_idempotente_segunda_ejecucion_sin_red(tmp_path):
    t = CIDOFalso()
    run(tmp_path, fetch=t, max_paginas=2)
    llamadas_tras_primera = t.llamadas
    csv_primera = (tmp_path / "oposicions.csv").read_bytes()

    r2 = run(tmp_path, fetch=t, max_paginas=2)
    assert r2.fetched == 0                    # cero peticiones de red
    assert r2.cache_hits >= 50                # las 50 URLs de la 2ª ejecución, sin red
    assert t.llamadas == llamadas_tras_primera
    assert (tmp_path / "oposicions.csv").read_bytes() == csv_primera  # byte-idéntico


def test_scan_rss_sin_novedades_toca_nada(tmp_path):
    t = CIDOFalso()
    run(tmp_path, fetch=t, max_paginas=2)
    antes = t.llamadas
    filas_antes = len(list(csv.DictReader((tmp_path / "oposicions.csv").open())))

    r = run_scan(tmp_path, fetch=t)
    assert r.fichas_descubiertas == 0
    assert r.fetched == 0                     # el feed salió de caché
    assert t.llamadas == antes
    assert len(list(csv.DictReader((tmp_path / "oposicions.csv").open()))) == filas_antes


def test_scan_rss_añade_ficha_nueva_it(tmp_path):
    # seed: CSV solo con los ids conocidos del feed, excepto uno que "se publica hoy"
    conocidos = {"20260212O24", "20261016O14", "20261028O10", "20260701O16"}
    seed = tmp_path / "oposicions.csv"
    with seed.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["proceso_id"] + ["x"] * 15)
        for c in conocidos:
            w.writerow([c] + [""] * 15)

    # el feed "de hoy" incluye el item nuevo (sintético) que no está sembrado
    item_nuevo = """<item><title>1 plaça de fake informatic</title>
      <description><![CDATA[<p><strong>Número de referència: </strong> 20260601O01</p>]]></description>
      <link>http://cido.diba.cat/oposicions/90000001/placa-fake-informatica-a</link></item>"""
    feed2 = FEED.replace("</channel>", item_nuevo + "\n</channel>")

    r = run_scan(tmp_path, fetch=CIDOFalso(feed=feed2))
    assert r.fichas_descubiertas >= 8         # 11 del feed + 1 nueva − 4 sembradas
    assert r.procesos == 1                    # solo la sintética IT se añade
    filas = list(csv.DictReader(seed.open()))
    assert any(f["proceso_id"] == "20260601O01" for f in filas)
