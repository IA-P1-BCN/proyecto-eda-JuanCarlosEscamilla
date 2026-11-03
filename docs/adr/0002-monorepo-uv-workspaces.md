---
status: accepted
date: 2026-11-03
---

# Monorepo uv con workspaces: lógica separada por paquetes

El código crecería cruzando tres fronteras naturales (ingesta externa, lógica de negocio, apps desplegables) y el requisito de "pipeline de un comando + código reutilizable" pide módulos testables e importables — un único `src/` lo mezclaría todo. Decidimos: **monorepo uv con workspaces**, layout empresa `libs/ + apps/`:

- `packages/eda_ingesta` (lib): scraper CIDO, caché, población municipal, profiling — US3
- `packages/eda_core` (lib): **lógica de negocio** — limpieza, enriquecimiento, features — US4-US5
- `packages/eda_pipeline` (app): CLI `eda-pipeline` que orquesta ingesta+core — el "un comando"
- `packages/eda_app` (app): dashboard Streamlit desplegable en Render — US9

## Considered Options

| Opción | Por qué no / por qué sí |
|---|---|
| Un solo `src/eda` | Más simple, pero mezcla ingestar/negocio/app y el Dockerfile del dashboard llevaría el scraper de pasajero |
| Repo multi-proyecto (varios repos) | Sobre-ingeniería brutal para 1 semana; el evaluador perdería la vista de conjunto |
| **Monorepo uv workspaces** (elegida) | Un lockfile, un `uv sync`, tests por paquete, cada app despliega solo sus deps; estructura idéntica a la de una empresa de datos |

## Consecuencias

- El notebook (US6) vive en la raíz y **importa de `eda_core`** — narrativa, no lógica.
- Las referencias `src/eda/` en PRD/issues se materializan según esta tabla (esta nota vale como mapeo).
- El Dockerfile de US10 construye solo `eda-app` (+ sus deps por workspace), no todo el repo.
- `pytest` descubre tests de todos los paquetes (`packages/*/tests`); CI no cambia.
- Cada paquete lleva su `pyproject.toml` y sus tests juntos — test-first por paquete.
