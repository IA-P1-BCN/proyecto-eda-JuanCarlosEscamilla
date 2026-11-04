# Proposal: add-scraper-cido

## Why

El CIDO DIBA no ofrece API: los 237 procesos de informática y sus hitos solo existen como HTML. Sin ingesta reproducible no hay pipeline, ni Airflow, ni análisis — y re-scrapear a mano cada sesión es lo que una empresa jamás haría.

## What Changes

- Nuevo paquete `eda_ingesta` con scraper educado del CIDO (materia 24): pausa entre peticiones, User-Agent propio, reintentos con backoff.
- Caché HTML resumible en `data/raw/html/` — una segunda ejecución no re-descarga lo ya descargado (idempotencia verificable por test).
- Parseo de fichas a **formato largo**: 1 fila = 1 hito de proceso (BOP/DOGC), más tabla de procesos como dimensión.
- Registro de adjuntos con slug semántico (`publtaubor`, `restexambo`, `listexamop`…) y **taxonomía de errores de enlace**: E1 caído, E2 intranet genérica, E3 no parseable.
- Parser del identificador CIDO (`20230127O46` → fecha de convocatoria) y extractor de plazas del título (catalán/castellano).
- `pipeline --step download` conecta el CLI (`eda_pipeline`) con el paquete de ingesta.
- Profiling inicial (nulos/tipos/valores raros) exportado como insumo del informe de calidad.

## Capabilities

### New Capabilities

- `ingesta-cido`: comportamiento de la ingesta del CIDO — respeto al portal, caché/idempotencia, formato largo de hitos, clasificación de errores de enlace.

### Modified Capabilities

(ninguna — primer capability del sistema)

## Impact

- Código: `packages/eda_ingesta` (nuevo), `packages/eda_pipeline` (conecta el paso download).
- Datos: crea `data/raw/` (gitignored, ~237 fichas + listados).
- Riesgos: HTML sin contrato (mitigado con tests sobre fixtures congeladas + caché), enlaces caídos (taxonomía E1/E2/E3 → informe de calidad).
