"""Tests del emparejamiento de población municipal (US5·T1)."""

from eda_ingesta.poblacio import cargar_poblacio, municipi_desde_institucio, enllacar_institucio


def test_municipi_desde_institucio_todos_los_formatos():
    assert municipi_desde_institucio("Ajuntament d'Alcover") == "alcover"
    assert municipi_desde_institucio("Ajuntament de Berga") == "berga"
    assert municipi_desde_institucio("Ajuntament de la Roca del Vallès") == "la roca del valles"
    assert municipi_desde_institucio("Ajuntament del Vendrell") == "el vendrell"
    assert municipi_desde_institucio("Ajuntament de les Borges Blanques") == "les borges blanques"
    assert municipi_desde_institucio("Diputació de Barcelona") is None   # supramunicipal
    assert municipi_desde_institucio("") is None


def test_cargar_poblacion_desde_la_referencia_real():
    municipis = cargar_poblacio("data/reference/poblacio_municipis.csv")
    assert len(municipis) >= 900        # 951 en la referencia congelada
    alcover = municipis["alcover"]
    assert alcover["poblacio"] > 4000   # Alcover ~5.000 hab
    vic = municipis["vic"]
    assert vic["poblacio"] > 40000 and vic["dist_km_vic"] < 5   # epicentro
    manresa = municipis["manresa"]
    assert 40 < manresa["dist_km_vic"] < 45   # dentro del radio


def test_enlazar_exacto_fuzzy_y_sin_match():
    municipis = {"alcover": {"municipi": "Alcover", "poblacio": 5000},
                 "sant sadurni d anoia": {"municipi": "Sant Sadurní d'Anoia", "poblacio": 13000}}
    m, metode = enllacar_institucio("Ajuntament d'Alcover", municipis)
    assert metode == "exacte" and m["poblacio"] == 5000
    # fuzzy: institució con una errata mínima vs la referencia
    m, metode = enllacar_institucio("Ajuntament de Sant Sadurni d'Anoia", municipis)
    assert metode == "fuzzy" and m["poblacio"] == 13000
    m, metode = enllacar_institucio("Diputació de Barcelona", municipis)
    assert m is None and metode == "no-es-ajuntament"
