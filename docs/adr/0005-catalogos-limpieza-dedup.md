---
status: accepted
date: 2026-11-04
---

# Catálogos de limpieza y dedup de hitos

El CSV crudo trae rarezas reales (814 procesos, 2.786 filas): `estat` con 5 valores más vacíos (47), `grup` en formato antiguo sin número ("A - Grau universitari"), 96 hitos duplicados por (proceso, fecha, título), 363 plazas vacías, 1.413 materias multi-valor. Decidimos normalizar **a catálogos cerrados** y deduplicar **conservando la primera aparición**:

- `normalizar_estat` → canónico castellano (resuelta/abierta/pendiente/cerrada/no vigente); fuera de catálogo → `None` (los None van al informe de calidad, no se inventan valores)
- `normalizar_grupo` → código (`A1`…`C2`, formato antiguo `A`/`B`); sin separador ' - ' → `None`
- `dedup_hitos` por (proceso_id, hito_fecha, hito_titulo), primera aparición gana (la variante posterior suele ser la plantilla sin datos)
- `durada_mesos` = resolución (último hito con "resoluc") − convocatoria, a 30.44 días/mes; sin resolución → `None` (proceso abierto o incompleto — la ausencia es un dato honesto, no un error)

## Considered Options

| Alternativa | Por qué no |
|---|---|
| Imputar estados/plazas desconocidos con la moda | Inventa datos que el portal no dio; el CEO tomaría decisiones sobre ficción |
| Borrar filas con `grup` ilegible | Pérdida silenciosa; `None` + log de calidad conserva la trazabilidad |
| Dedup manteniendo la última aparición | La primera es la publicación real; la última suele ser el duplicado de plantilla |

## Consecuencias

- La ausencia (`None`) es un valor de primera clase: el informe de calidad (US12) cuenta los `None` por columna.
- La duración solo es computable para procesos con hito de resolución (309 resueltas del crudo → ~236 en familia IT): el EDA lo declarará explícitamente.
- Nota de numeración: los ADRs 0002-0004 se asignaron a arquitectura/spark/RGPD; este es el ADR de limpieza que el PRD de US4 anticipaba como "ADR-0002..0004".
