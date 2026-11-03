"""Tests de clasificación de adjuntos (T3.2) — URLs reales de las fichas congeladas."""

from eda_ingesta.adjuntos import clasificar_doc, clasificar_estado

# slugs semánticos de DIBA /talent/ (vistos en la ficha 21300157 y 14783298)
URL_LISTEXAM = "https://www.diba.cat/documents/d/talent/r0726-2026_0011504_listexamop_co_90224022_noindex"
URL_PUBLTAUBOR = "https://www.diba.cat/documents/d/talent/2026_0011504_publtaubor_co_90229090_noindex"
URL_PLANTILLA = "https://www.diba.cat/documents/d/talent/r-07-26plantillapublicaciowebconvosoposicio"
URL_PDF_BASES = "https://www.diba.cat/documents/1115741/39297391/bases_s.02.23_-_t%C3%A8cnic_superior_inform%C3%A0tica+signades.pdf/x1?t=1"
URL_DOGC = "https://portaldogc.gencat.cat/utilsEADOP/AppJava/PdfProviderServlet?documentId=1036691&type=01&language=ca_ES"
URL_TRAMIT = "https://seuelectronica.diba.cat/tramits-ciutadania/"


def test_slug_semantico_en_ruta_talent():
    assert clasificar_doc(URL_LISTEXAM) == "listexamop"
    assert clasificar_doc(URL_PUBLTAUBOR) == "publtaubor"


def test_plantilla_publicacion_web_es_token_conocido():
    assert clasificar_doc(URL_PLANTILLA) == "plantillapublicacioweb"


def test_dogc_por_dominio():
    assert clasificar_doc(URL_DOGC) == "dogc"
    assert clasificar_doc("https://dogc.gencat.cat/ca/document-del-dogc/?documentId=1040597") == "dogc"


def test_pdf_generico_sin_slug_desconocido():
    assert clasificar_doc(URL_PDF_BASES) is None  # existe (200) pero sin token; no es E3 aún


def test_e1_enlaces_muertos_tras_reintentos_o_agotados():
    assert clasificar_estado(URL_LISTEXAM, status=404) == "E1"
    assert clasificar_estado(URL_LISTEXAM, status=503) == "E1"
    assert clasificar_estado(URL_LISTEXAM, agotado=True) == "E1"  # ClienteAgotado sin status


def test_e2_intranet_generica_del_ayuntamiento():
    assert clasificar_estado(URL_TRAMIT, status=200) == "E2"
    assert clasificar_estado("https://alcover.eadministracio.cat/catalog/t/xxx", status=200) == "E2"


def test_documento_valido_sin_error():
    assert clasificar_estado(URL_PUBLTAUBOR, status=200) is None
    assert clasificar_estado(URL_DOGC, status=200) is None
