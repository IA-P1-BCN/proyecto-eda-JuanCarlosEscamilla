---
status: accepted
date: 2026-11-03
---

# Elección de fuentes: CIDO DIBA (materia Informàtica) + población municipal

Necesitábamos un dataset real, sucio y con suficiente material para un EDA completo (≥1.000 filas, ≥8 columnas, tipos mixtos), y que además soportara un pipeline con orquestación diaria creíble. Decidimos: **fuente principal = procesos selectivos del CIDO (Diputació de Barcelona)** filtrados por la materia *Informàtica. Noves tecnologies* y proximidad (radio de 45 km desde Vic: 814 procesos y 2.786 hitos a 04/11/2026), enriquecida con **población por municipio (Wikidata SPARQL, `data/reference/poblacio_municipis.csv`)** para normalizar plazas per cápita.

## Considered Options

| Fuente | Filas potenciales | Tipos mixtos | Suciedad real | Fuente viva (pipeline diario) | Veredicto |
|---|---|---|---|---|---|
| **CIDO DIBA — oposicions, materia IT** (elegida) | 237 procesos × 5-12 hitos ≈ 1.500-2.500 (formato largo) | ✅ fechas, categorías, texto, numérico | ✅ fecha codificada en el ID, plazas solo en el título, enlaces caídos, PDFs heterogéneos | ✅ nuevas convocatorias e hitos BOP continuamente | **Elegida**: original (nadie lo ha analizado), interés real, URL con filtros estables |
| COVID Tracking Project (sugerida por la spec) | 20.780 × 56 | ✅ | ✅ | ❌ congelada en marzo 2021 → un DAG diario sería teatro | Descartada como principal |
| Bicing (estaciones, aj. Barcelona) | ~500 estaciones × snapshots | Parcial | Media | ✅ | Descartada: poco interés analítico para el equipo |
| Calidad del aire / accidentes BCN | Media/alta | ✅ | Media | Parcial | Descartadas: datasets ya muy trabajados por la comunidad |

## Consecuencias

- **No hay API**: el CIDO es HTML (Laravel) → el pipeline necesita un scraper educado, cacheado e idempotente (US3), no un simple `requests.get` de JSON.
- **El cumplimiento de ≥1.000 filas depende de expandir hitos** a formato largo (1 fila = 1 hito de proceso). Si el resultado final quedara corto, el plan B es ampliar a materias tecnológicas adyacentes — decisión del PO con ADR nuevo.
- **Sin datos de aspirantes en las fichas**: los recuentos vienen de los PDFs adjuntos de bolsa/resultados (oportunista, ver US5); los enlaces caídos se clasifican E1/E2/E3 y se reportan en el informe de calidad.
- La URL base con filtro de materia es estable: `cido.diba.cat/oposicions?filtreMateria%5Boptions%5D%5B%5D=24`.
