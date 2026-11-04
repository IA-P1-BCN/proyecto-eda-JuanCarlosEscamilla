# ingesta-cido — Delta

## ADDED Requirements

### Requirement: Respeto al portal

El scraper SHALL limitar la frecuencia de petición (pausa configurable entre llamadas) y SHALL identificarse con un User-Agent propio que declare el propósito. Ante error transitorio (5xx/timeout) SHALL reintentar con backoff exponencial.

#### Scenario: pausa entre fichas

- **WHEN** el crawler recorre las fichas de un listado
- **THEN** entre dos peticiones consecutivas transcurre al menos la pausa configurada

#### Scenario: reintento ante fallo transitorio

- **WHEN** una petición falla con 503 o timeout
- **THEN** se reintenta con espera creciente y, agotados los intentos, el fallo se registra como E1 sin abortar el resto del crawl

### Requirement: Caché resumible e idempotente

El scraper SHALL cachear cada HTML descargado en `data/raw/html/` y SHALL consultar la caché antes de la red. Re-ejecutar el pipeline SHALL NOT duplicar filas ni re-descargar contenido ya cacheado.

#### Scenario: segunda ejecución sin red

- **WHEN** el pipeline se ejecuta dos veces sin limpiar la caché
- **THEN** la segunda ejecución no emite peticiones por contenido ya cacheado y produce el mismo CSV crudo

### Requirement: Formato largo de hitos

El parser SHALL convertir cada ficha en filas de hito (1 fila = 1 hito BOP/DOGC con su fecha y descripción) y SHALL extraer la fecha de convocatoria del identificador (`20230127O46` → 2023-01-27). Un identificador inválido SHALL producir fila en el log de calidad, no un crash.

#### Scenario: proceso con 8 hitos

- **WHEN** una ficha contiene 8 entradas de hito
- **THEN** el CSV crudo recibe 8 filas de hito para ese proceso, todas con el mismo id de proceso

#### Scenario: identificador corrupto

- **WHEN** una ficha trae un identificador que no codifica una fecha válida
- **THEN** la fila se marca en el log de calidad y el pipeline continúa

### Requirement: Clasificación de errores de enlace

Cada adjunto SHALL registrarse con su slug semántico y un estado: `E1` (caído: 404/timeout tras reintentos), `E2` (enlace genérico a intranet del ayuntamiento, no al documento), `E3` (documento no parseable). El resumen SHALL exportarse para el informe de calidad con acción sugerida por clase.

#### Scenario: adjunto caído

- **WHEN** un adjunto responde 404 tras reintentos
- **THEN** se registra E1 con la URL y el id de proceso, y el crawl continúa

#### Scenario: intranet genérica

- **WHEN** un enlace apunta al portal del ayuntamiento en vez del documento concreto
- **THEN** se registra E2 y se sugiere la acción "pedir enlace directo"

### Requirement: Detección incremental por RSS

El scraper SHALL usar el feed `cido.diba.cat/rss/oposicions/oposicions` como canal de novedades: 1 petición diaria, diff de identificadores contra la caché, y descarga de SOLO las fichas nuevas (filtrando materia en la ficha, no en el feed). El feed no cubre el histórico completo (1.000 items ≈ 2 meses): el crawler de listados SHALL conservarse para el bootstrap y el full re-scan manual.

#### Scenario: día sin novedades

- **WHEN** el scan RSS no devuelve identificadores nuevos
- **THEN** se emiten 0 peticiones de fichas y el CSV no cambia

#### Scenario: proceso nuevo publicado hoy

- **WHEN** el feed incluye un proceso cuyo id no está en caché
- **THEN** se descarga su ficha, se comprueba su materia y solo si es Informàtica (24) se añade al dataset
