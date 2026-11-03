# GLOSSARY — Vocabulario del proyecto (ES)

Fuente de verdad de los términos; `docs/agents/domain.md` manda usarlos tal cual. Las columnas nuevas se añaden AQUÍ en el mismo PR que las crea.

## Columnas del dataset enriquecido (data/processed/)

| Columna | Definición | Origen |
|---|---|---|
| `proceso_id` | Identificador CIDO `AAAAMMDDO##` — codifica la fecha de convocatoria | CIDO |
| `fecha_convocatoria` | Fecha de convocatoria parseada del identificador | ingesta (parsers) |
| `institucio` | Entidad convocante tal cual el portal | CIDO |
| `municipi` | Municipio emparejado con la referencia de población (minúsculas) | merge población |
| `poblacio_municipi` | Habitantes del municipio (Wikidata, corte 2026-11) | referencia |
| `dist_km_vic` | Distancia geodésica municipio→Vic (epicentro configurable) | haversine |
| `estado` | Catálogo canónico: `resuelta` / `abierta` / `pendiente` / `cerrada` / `no vigente` — vacío = sin estado en la ficha | limpieza (ADR-0005) |
| `grupo` | Código de grupo de titulación: `A1` `A2` `B` `C1` `C2` (formato antiguo: `A`/`B`) | limpieza |
| `plazas` | Plazas publicadas; vacío = bolsa sin cuantificar (363 casos) | título parseado |
| `durada_mesos` | Meses convocatoria→último hito de resolución (30.44 d/mes); vacío = abierto o sin resolución | limpieza |
| `places_per_mil_hab` | **Plazas del proceso por cada 1.000 habitantes del municipio** — la normalización justa (pregunta 2) | enriquecimiento |
| `urbanitzacio` | `urbano` ≥20k hab · `intermedi` 5k-20k · `rural` <5k | enriquecimiento |
| `doc_slug` | Tipo de documento según su URL (`dogc`, `listexamop`, `publtaubor`, `proves…`) | adjuntos |

## Términos de dominio

| Término | Significado |
|---|---|
| **CIDO** | Cercador d'Informació i Documentació Oficial (DIBA) — el portal de origen |
| **BOPB / DOGC** | Boletines oficiales donde se publican los hitos de un proceso |
| **E1 / E2 / E3** | Enlace caído / intranet genérica / PDF no parseable (ver ADR-0001) |
| **ficha_actualizada** | Refetch forzado (feed RSS) detectó contenido nuevo en una ficha conocida |
| **bronze / silver** | Niveles del data lake: crudo (`data/raw`) / procesado (`data/processed`); se publican como releases versionadas |
