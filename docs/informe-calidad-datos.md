# Informe de Calidad de Datos — Oposicions CIDO (Materia IT, radio Vic 45 km)

> **Corte**: `2026-11-04` · **Fuente**: `cido.diba.cat/oposicions` (`filtreMateria=24`, epicentro Vic 45 km) + `data/reference/poblacio_municipis.csv` (Wikidata SPARQL).
> **Insumos automáticos**: [`reports/profiling.md`](../reports/profiling.md), [`reports/calidad-municipios.csv`](../reports/calidad-municipios.csv), `data/raw/calidad.jsonl`.

---

## 1. Resumen ejecutivo de la auditoría

| Métrica | Zona Raw (`oposicions.csv`) | Zona Processed (`oposicions_enriquit.csv`) | Cambio / Regla aplicada |
|---|---:|---:|---|
| **Filas (hitos BOP/DOGC)** | 2.786 | 2.690 | −96 duplicados exactos por `(proceso_id, hito_fecha, hito_titulo)` (ADR-0005) |
| **Procesos únicos** | 814 | 814 | 100 % conservados (ningún proceso descartado en limpieza) |
| **Columnas** | 15 | 18 | +`durada_mesos`, `poblacio`, `urbanitzacio`, `places_per_mil_hab`, `dist_km_vic` |
| **Procesos con duración computable** | — | 149 (18,3 %) | Solo procesos con fecha de convocatoria y al menos un hito de resolución publicada |
| **Procesos con match municipal** | — | 382 (46,9 %) | 432 procesos corresponden a entes supramunicipales o patronatos sin población municipal propia |
| **Rango temporal de convocatorias** | `2004-06-09` → `2026-10-28` | `2004-06-09` → `2026-10-28` | Extraído del prefijo `YYYYMMDD` de `proceso_id` validado contra los hitos |

---

## 2. Síntesis de decisiones de arquitectura y calidad (ADRs 0001–0005)

| ADR | Decisión | Qué problema de calidad o diseño resuelve |
|---|---|---|
| **[ADR-0001](adr/0001-eleccion-fuentes.md)** — *Elección de fuentes* | Fuente principal CIDO DIBA (materia 24, formato largo: 1 fila = 1 hito BOP/DOGC) enriquecida con población municipal de Wikidata SPARQL (`951` municipios de Cataluña). | Supera el umbral de `≥1.000` filas con datos reales y vivos (frente a datasets estáticos/congelados como COVID Tracking 2021) y evita que los grandes municipios dominen por mero volumen bruto. |
| **[ADR-0002](adr/0002-monorepo-uv-workspaces.md)** — *Monorepo uv con workspaces* | Separación estricta en `eda_ingesta`, `eda_core`, `eda_pipeline` y `eda_app`, con tests junto a cada paquete (`packages/*/tests`). | Garantiza que las reglas de limpieza y enriquecimiento estén testeadas en `eda_core` y sean compartidas de forma idéntica entre el CLI, el DAG de Airflow, el notebook y el dashboard. |
| **[ADR-0003](adr/0003-sin-spark-umbral-escala.md)** — *Sin Spark: pandas + umbral de escala* | Procesamiento tabular con `pandas` en memoria; umbral de revisión fijado en `>10⁶` filas (evaluar Polars primero y Spark solo en clúster multi-nodo). | Evita el sobrecoste de JVM/shuffle en un dataset de ~2.700 filas, manteniendo ejecuciones completas de limpieza + enriquecimiento + validación por debajo de 1 segundo. |
| **[ADR-0004](adr/0004-minimizacion-rgpd.md)** — *Minimización RGPD / LOPDGDD* | **Cero datos personales en el repositorio y en los CSV**: nunca se extraen, cachean ni publican nombres, apellidos, DNI/NIF (ni siquiera enmascarados) ni puntuaciones individuales de aspirantes. | Cumplimiento estricto de RGPD (art. 6) y LOPDGDD. El validador (`validar_dataset`) bloquea automáticamente cualquier columna sospechosa (`dni`, `nif`, `nombre_aspirante`, `cognoms`, etc.). |
| **[ADR-0005](adr/0005-catalogos-limpieza-dedup.md)** — *Catálogos cerrados y deduplicación* | Normalización a catálogos cerrados (`estat`, `grup`), deduplicación conservando la **primera aparición** y prohibición de imputar valores inventados (la ausencia queda como `None`/vacío trazable). | Evita sesgar las conclusiones del CEO con modas artificiales o plantillas vacías publicadas con posterioridad al anuncio original. |

---

## 3. ¿Qué faltaba en origen, qué se corrigió y qué quedó pendiente?

### 3.1 Qué faltaba o venía sucio en el HTML crudo
1. **Fechas de convocatoria ausentes como campo explícito**: CIDO no expone una etiqueta `<dt>Data de convocatòria</dt>` en todas las fichas; en 473 procesos viene codificada en el identificador (`YYYYMMDDO<n>`, p. ej. `20230127O46` → `2023-01-27`), mientras que en **341 procesos (1.403 filas de hito)** el identificador usa un formato no estándar o el primer hito no permite reconstruirla con certeza.
2. **Plazas incrustadas en el título en texto libre**: el número de plazas se publica dentro del titular en catalán/castellano (`"1 plaça de..."`, `"3 places de..."`, `"Borsa de treball..."`). En **363 filas de hito** (principalmente bolsas de trabajo sin cupo fijo de plazas) no existe cifra numérica de plazas.
3. **Categorías heterogéneas y formatos antiguos**:
   - `grup` combinaba nomenclatura moderna (`A1 - Grau universitari`, `C1 - Batxillerat / FP`) con nomenclatura histórica (`A - Llicenciatura`, `B - Diplomatura`) y **100 filas vacías**.
   - `estat` presentaba 5 variantes en catalán más **47 filas vacías**.
4. **Hitos duplicados en las tablas de seguimiento**: **96 filas** repetían exactamente `(proceso_id, hito_fecha, hito_titulo)` dentro de la misma ficha (reediciones de anuncios o plantillas duplicadas).
5. **`doc_slug` ausente en enlaces que no siguen el patrón de documentos DIBA**: **2.277 filas** enlazan a boletines generales o páginas sin slug semántico extraíble, mientras que 483 enlazan a DOGC (`dogc`) y 26 a slugs específicos (`proves`, `informat`, `proposta`, `entrevistes`, `sistemes`, `decret`, `resolucio`, `deserta`).

### 3.2 Qué se corrigió automáticamente en `eda_ingesta` y `eda_core`
- **Extracción y validación de fechas (`parse_fecha_id`, `parse_fecha_es`)**: conversión a ISO `YYYY-MM-DD` validando fechas imposibles (como `31/02`).
- **Extracción de plazas (`parse_plazas`)**: parser regex bilingüe que extrae el entero de plazas y devuelve `None` honesto cuando es una bolsa abierta sin número fijo.
- **Normalización a catálogos cerrados (`normalizar_estat`, `normalizar_grupo`)**: mapeo determinista a códigos limpios (`A1`, `A2`, `B`, `C1`, `C2`, `AP`, `A`) y estados en castellano (`resuelta`, `abierta`, `pendiente`, `cerrada`, `no vigente`).
- **Deduplicación (`dedup_hitos`)**: eliminación de las 96 filas duplicadas conservando la primera aparición publicada (2.786 → 2.690 filas).
- **Cálculo de duración (`calcular_duracion_mesos`)**: diferencia en meses (`días / 30,44`) entre la convocatoria y el último hito con resolución (`"resoluc"`, `"nomenament"`, `"adjudicac"`), evitando contar procesos aún abiertos como si duraran cero meses.
- **Cruce municipal y normalización demográfica (`enriquir_dataset`)**: normalización de nombres de ayuntamientos (artículos en catalán, variantes con guion/paréntesis) contra los 951 municipios de Wikidata, generando `poblacio`, `urbanitzacio` (`rural` <5k, `intermedi` 5k–20k, `urbano` >20k), `places_per_mil_hab` y `dist_km_vic` (fórmula de Haversine).

### 3.3 Qué quedó pendiente (no imputado) y por qué
- **Nulos conservados por diseño (ADR-0005)**:
  - `fecha_convocatoria` (1.351 filas en procesado / 341 procesos), `plazas` (363 filas), `titulacio` (413 filas), `sistema` (284 filas), `grup` (100 filas), `estat` (47 filas) y `tipus_personal` (46 filas).
  - **Por qué**: imputar el grupo de titulación o el número de plazas con la moda o la mediana falsearía el reparto real de perfiles y de oferta pública. Cada análisis filtra explícitamente las filas con dato válido y reporta el tamaño muestral `n`.
- **Entidades sin match municipal (`reports/calidad-municipios.csv`: 432 procesos / 1.095 filas)**:
  - **419 procesos (`no-es-ajuntament`)**: convocados por universidades (UVic, UManresa), consorcios hospitalarios y sanitarios (Consorci Hospitalari de Vic, Parc Taulí, Consorci Sanitari de Terrassa/Maresme, Althaia), consejos comarcales (Osona, Bages, Berguedà, Selva, Garrotxa, Moianès, Vallès) o centros de investigación (IRTA, IRIS-CC). No son un municipio y, por tanto, **no tienen denominador de población municipal** para calcular `places_per_mil_hab`.
  - **13 procesos (`sense-match`)**: organismos autónomos o patronatos con nombre compuesto (p. ej. `Ajuntament de Sabadell - Organisme Autònom Informàtica (IAS)`, `Ajuntament de Terrassa - Terrassa Cicle de l'Aigua, EPEL`, `Ajuntament de Bigues i Riells` antes del cambio oficial a *Bigues i Riells del Fai*). Quedan registrados en [`reports/calidad-municipios.csv`](../reports/calidad-municipios.csv) para ampliar el diccionario de alias municipales en la siguiente iteración.

---

## 4. Taxonomía de errores de enlace (`E1` / `E2` / `E3`) y acción sugerida

El módulo [`packages/eda_ingesta/src/eda_ingesta/adjuntos.py`](../packages/eda_ingesta/src/eda_ingesta/adjuntos.py) y el paso `download` clasifican los enlaces de fichas y documentos adjuntos en tres clases accionables que se registran en `data/raw/calidad.jsonl`:

| Clase | Definición técnica | Estado en el corte actual (`calidad.jsonl`) | Acción sugerida por clase |
|---|---|---|---|
| **`E1` — Enlace caído (`404` / `5xx` / timeout)** | El servidor del boletín o del ente responde con código HTTP `>= 400` o agota los 3 reintentos con backoff exponencial. | **0 eventos persistentes** en las fichas CIDO del corte actual (caché negativa diaria `.err` evita martillear URLs caídas el mismo día y permite reintento al día siguiente). | **Reintento automático diferido (TTL 24 h)** en el DAG de Airflow; si un enlace acumula >7 días en `E1`, marcar el hito como `enlace_historico_muerto` y buscar el edicto equivalente en el buscador del DOGC/BOPB por fecha y código de proceso. |
| **`E2` — Intranet o portal genérico (`200 OK` sin documento)** | La URL devuelve `200 OK`, pero apunta a la portada genérica del ayuntamiento o sede electrónica (`/seu-electronica`, `/portal`, `/inici`, `/ca` o raíz `/` sin ruta a edicto ni PDF). | **0 fichas descartadas por `E2`** en el listado CIDO; en los hitos adjuntos, las URLs genéricas de sede electrónica quedan identificadas sin `doc_slug`. | **No descargar como PDF**; conservar únicamente el metadato del hito (fecha y título publicado en CIDO) y, si se requiere el documento, usar un crawler secundario específico de sedes electrónicas municipales (e-TAULER / AOC). |
| **`E3` — PDF no parseable / formato inesperado** | El documento adjunto responde `200 OK` pero no es un PDF válido (`%PDF-`), está escaneado como imagen sin capa de texto (OCR requerido) o su estructura tabular no permite extraer el recuento en memoria. | **Pendiente / Oportunista** (el stretch de extracción de PDFs en memoria bajo ADR-0004 se desactiva ante `E3` sin romper el pipeline). | **Degradación elegante (*graceful degradation*)**: descartar el buffer en memoria (cumpliendo ADR-0004), dejar `n_aspirantes = None` y registrar la URL en `calidad.jsonl` para aplicar OCR en memoria únicamente sobre edictos estandarizados del BOPB. |

---

## 5. ¿Qué NO sabemos aún?

Responder explícitamente a **"¿qué NO sabemos aún?"** es imprescindible para no sobre-interpretar los hallazgos del EDA:

1. **No sabemos cuántos aspirantes compiten por cada plaza (`competencia = aspirantes / plaza`)**:
   - Las fichas HTML del CIDO solo publican la oferta (plazas, grupo, hitos y enlaces a boletines), nunca el número de inscritos ni de admitidos. Ese dato vive dentro de los PDFs de listas de admitidos/excluidos de cada ayuntamiento, con formatos heterogéneos y sujetos a la restricción RGPD (ADR-0004).
2. **No sabemos cuánto tardan en resolverse el 81,7 % de los procesos (665 de 814)**:
   - Solo **149 procesos (18,3 %)** tienen simultáneamente fecha de convocatoria conocida e hito de resolución publicado en el CIDO. Del resto, una parte sigue abierta/en curso y otra parte se resolvió en la web del ayuntamiento sin que el CIDO llegara a registrar el último edicto. Por tanto, la mediana de **3,9 meses** describe a los procesos con ciclo completo documentado en CIDO, y podría existir un **sesgo de supervivencia/cierre**.
3. **No sabemos el salario bruto ni el complemento específico de cada plaza**:
   - CIDO informa el grupo de titulación (`A1`, `A2`, `C1`, `C2`) y el tipo de personal (`Funcionari`, `Laboral`), pero no las retribuciones económicas, que dependen de la Relación de Puestos de Trabajo (RPT) de cada corporación local.
4. **No sabemos cuántas plazas acaban desiertas o cuántos interinos consolidan plaza**:
   - Salvo cuando la palabra `"deserta"` aparece en el título o slug del hito (solo 1 caso explícito en `doc_slug`), el CIDO no distingue entre una resolución con nombramiento efectivo y una convocatoria declarada desierta o amortizada.
5. **No sabemos el peso real del empleo IT en los entes supramunicipales por habitante**:
   - Los **419 procesos** de universidades (UVic, UManresa), hospitales/consorcios sanitarios (Parc Taulí, CHV, CST) y consejos comarcales dan servicio a toda una comarca o región sanitaria, por lo que no pueden asignarse únicamente al padrón del municipio donde tienen su sede física.
