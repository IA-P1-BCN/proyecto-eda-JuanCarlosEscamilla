"""Tests del parser de fichas (T3.1) — dos fichas reales congeladas, valores verificados."""

from datetime import date
from pathlib import Path

from eda_ingesta.fichas import es_informatica, parse_ficha

FIX = Path(__file__).parent / "fixtures"
URL_IT = "https://cido.diba.cat/oposicions/14783298/borsa-de-treball-de-places-de-tecnic-superior-informatica-diversos-perfils-especialitzats-diputacio-de-barcelona"
URL_AL = "https://cido.diba.cat/oposicions/21078364/1-placa-dauxiliar-administratiu-de-gestio-de-lescola-de-musica-municipal-ajuntament-dalcover"


def test_ficha_it_diba_campos_dimension():
    p = parse_ficha((FIX / "ficha_it_diba_14783298.html").read_text(), URL_IT)
    assert p.identificador == "20230127O46"
    assert p.fecha_convocatoria == date(2023, 1, 27)
    assert p.titulo.startswith("Borsa de treball de places de Tècnic Superior Informàtica")
    assert p.institucio == "Diputació de Barcelona"
    assert p.sistema == "Oposició o prova"
    assert p.tipus_personal == "Funcionari interí"
    assert p.grup.startswith("A1")
    assert p.materies == ["Informàtica"]
    assert p.estat == "Resolt"
    assert p.url == URL_IT


def test_ficha_it_diba_hitos_formato_largo():
    p = parse_ficha((FIX / "ficha_it_diba_14783298.html").read_text(), URL_IT)
    assert len(p.hitos) >= 20  # 45 filas <time> en el HTML real
    primero = p.hitos[0]
    assert primero.fecha == date(2023, 1, 27)
    assert primero.titulo == "Bases específiques. Convocatòria. Temari"
    assert primero.url is not None and "diba.cat/documents" in primero.url
    assert all(h.fecha is not None and h.titulo for h in p.hitos)


def test_ficha_alcover_otra_materia():
    p = parse_ficha((FIX / "ficha_borsa_alcover_21078364.html").read_text(), URL_AL)
    assert p.identificador == "20260212O24"
    assert p.fecha_convocatoria == date(2026, 2, 12)
    assert p.institucio == "Ajuntament d'Alcover"
    assert p.sistema == "Concurs oposició o valoració de mèrits i prova"
    assert p.tipus_personal == "Laboral"
    assert p.grup.startswith("C2")
    assert p.materies == ["Administració general"]
    assert p.estat == "Termini obert"
    assert len(p.hitos) == 4  # el 5º <time> es el plazo de presentación (dt/dd), no un hito
    assert p.hitos[0].fecha == date(2026, 2, 12)
    assert "portaldogc.gencat.cat" in p.hitos[0].url  # primera publicación: DOGC


def test_es_informatica_filtra_por_materies():
    it = parse_ficha((FIX / "ficha_it_diba_14783298.html").read_text(), URL_IT)
    al = parse_ficha((FIX / "ficha_borsa_alcover_21078364.html").read_text(), URL_AL)
    assert es_informatica(it) is True
    assert es_informatica(al) is False


def test_identificador_corrupto_no_crasha():
    roto = (FIX / "ficha_it_diba_14783298.html").read_text().replace("20230127O46", "20239999OXX")
    p = parse_ficha(roto, URL_IT)
    assert p.fecha_convocatoria is None  # raw capturado; el log de calidad registrará
