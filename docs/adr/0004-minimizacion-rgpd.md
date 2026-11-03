---
status: accepted
date: 2026-11-03
---

# Minimización RGPD: los datos personales de aspirantes nunca entran en la pipeline

Los PDFs de bolsas y resultados (BOPB/DOGC) contienen nombres, apellidos y NIF (parcialmente enmascarados) de aspirantes. Son públicos por obligación administrativa de publicidad activa, pero **republicarlos en un repositorio externo crearía un fichero propio de datos personales de terceros sin legitimación** (RGPD art. 6 + LOPDGDD). La anonimización no es la vía: anonimizar nombres de forma efectiva es técnicamente frágil (re-identificación, umbrales de agregación) y ya supondría haber tratado el dato.

**Decisión**: minimización — **el dato personal no entra en la pipeline**:

1. Los PDFs de aspirantes **no se descargan a disco ni se cachean** — si se procesan (US5 stretch), es **en memoria**, y el contenido se descarta tras el cálculo.
2. Del PDF solo se extraen **recuentos** (`n_aspirantes`) y **estadísticas agregadas** (media/mediana/max de puntuación). Nunca: nombres, NIF (ni enmascarados), ni puntuaciones individuales ligadas a identidad.
3. El dataset y los releases publican **exclusivamente metadatos del proceso** (puesto, institución, grupo, plazos, enlaces, estado) — son datos de la entidad convocante, no de personas físicas.
4. Los errores de enlace (E1/E2/E3) registran URLs, no contenido de documentos.

**Consecuencia para US5**: el stretch `pdf_aspirants` queda redefinido — descarga en memoria, conteo de filas + agregados, `del contenido`. Si esto no fuese posible, el stretch muere sin sustituto: la pregunta de negocio "competencia por plaza" se responde igualmente con los recuentos.
