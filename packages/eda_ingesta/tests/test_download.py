"""Tests del paso download del pipeline (T4.1) — CIDO simulado completo, cero red."""

import csv
from pathlib import Path

from eda_ingesta.download import run

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
            return 200, self._feed.encode(), {}
        if "page=" in url:
            return 200, P2.encode(), {}
        if "oposicions?" in url:
            return 200, P1.encode(), {}
        if "14783298" in url:
            return 200, FICHA_IT.encode(), {}
        if "21078364" in url:
            return 200, FICHA_AL.encode(), {}
        if "90000001" in url:
            return 200, FICHA_SINTETICA_IT.encode(), {}
        if "90000002" in url:
            return 200, FICHA_SINTETICA_NO_IT.encode(), {}
        return 404, b"no existe", {}


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


def test_run_idempotente_segunda_ejecucion_mismo_dia(tmp_path):
    from datetime import date

    hoy_fijo = lambda: date(2026, 11, 3)  # noqa: E731 — sin rollo de medianoche
    t = CIDOFalso()
    run(tmp_path, fetch=t, max_paginas=2, hoy=hoy_fijo)
    csv_primera = (tmp_path / "oposicions.csv").read_bytes()
    llamadas_tras_primera = t.llamadas

    r2 = run(tmp_path, fetch=t, max_paginas=2, hoy=hoy_fijo)
    assert r2.actualizadas == 0               # contenido idéntico → sin eventos
    assert r2.fetched == 0                    # cero misses en caché; fichas desde caché
    assert t.llamadas == llamadas_tras_primera + 1  # solo el RSS detector toca la red
    assert r2.cache_hits >= 50                # todo lo demás desde caché
    assert (tmp_path / "oposicions.csv").read_bytes() == csv_primera  # byte-idéntico


def test_feed_detecta_ficha_actualizada(tmp_path):
    """El feed de hoy incluye un id YA conocido cuyo contenido cambió:
    refetch FORZADO → evento ficha_actualizada + CSV refleja el nuevo hito."""
    import json
    from datetime import date

    hoy_fijo = lambda: date(2026, 11, 3)  # noqa: E731
    t = CIDOFalso()
    run(tmp_path, fetch=t, max_paginas=2, hoy=hoy_fijo)  # bootstrap: cachea la ficha IT
    antes = len(list(csv.DictReader((tmp_path / "oposicions.csv").open())))

    # la ficha IT "cambia" (nuevo hito) y el feed de hoy la incluye (id 20230127O46)
    ficha_v2 = FICHA_IT.replace(
        "</table>",
        """<tr><td><time datetime="2026-11-04">04/11/2026</time></td><td>BOP</td><td>99</td>
           <td>Resolució provisional</td><td><a href="https://www.diba.cat/documents/x.pdf">PDF</a></td></tr></table>""")
    item_feed = """<item><title>Borsa IT actualizada</title>
      <description><![CDATA[<p><strong>Número de referència: </strong> 20230127O46</p>]]></description>
      <link>https://cido.diba.cat/oposicions/14783298/borsa-de-treball-de-places-de-tecnic-superior-informatica-diversos-perfils-especialitzats-diputacio-de-barcelona</link></item>"""
    feed2 = FEED.replace("</channel>", item_feed + "\n</channel>")

    class T2(CIDOFalso):
        def __init__(self):
            super().__init__(feed=feed2)

        def __call__(self, url, headers):
            if "14783298" in url:
                return 200, ficha_v2.encode(), {}
            return super().__call__(url, headers)
    t2 = T2()

    r = run(tmp_path, fetch=t2, max_paginas=2, hoy=hoy_fijo)
    assert r.actualizadas == 1
    eventos = [json.loads(l) for l in (tmp_path / "calidad.jsonl").read_text().splitlines()]
    assert any(e["tipo"] == "ficha_actualizada" for e in eventos)
    despues = len(list(csv.DictReader((tmp_path / "oposicions.csv").open())))
    assert despues == antes + 1  # el nuevo hito entra en formato largo
    assert t2.llamadas > 0       # hubo refetch forzado (red sí, aunque cacheaba)
