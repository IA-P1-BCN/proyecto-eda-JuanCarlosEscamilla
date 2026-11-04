# Proyecto EDA — Oposicions CIDO 🎓

Análisis exploratorio de datos (EDA) sobre los **procesos selectivos de informática** en los ayuntamientos de la provincia de Barcelona. Bootcamp Factoría F5 · alcance y plan en [`docs/PRD.md`](docs/PRD.md).

## ¿De dónde salen los datos?

| Fuente | Qué aporta | URL |
|---|---|---|
| **CIDO (Diputació de Barcelona)** — fuente principal | Procesos selectivos (oposiciones y bolsas de trabajo) de los ayuntamientos de la provincia, filtrados por la materia *Informàtica. Noves tecnologies*: 237 procesos con sus hitos publicados (BOP/DOGC) | [cido.diba.cat/oposicions](https://cido.diba.cat/oposicions?filtreMateria%5Boptions%5D%5B%5D=24) |
| **INE / DIBA** — enriquecimiento | Población por municipio, para comparar plazas per cápita entre municipios grandes y pequeños | ine.es · diba.cat |

Los datos se descargan con un scraper propio (no hay API pública) y se cachean en `data/raw/` — nadie vuelve a pedir al portal lo que ya está en disco. La decisión completa, con las alternativas descartadas, está en [ADR-0001](docs/adr/0001-eleccion-fuentes.md).

## Cómo ejecutarlo

Requisitos previos: **[`PREREQUISITES.md`](PREREQUISITES.md)** (`uv` + `go-task` el día 1; Quarto/Docker/astro llegan con su fase).

```bash
task sync        # instala el monorepo completo (un venv, un lockfile)
task test        # tests de todos los paquetes
task pipeline    # descarga → limpia → exporta, en un comando
task dashboard   # dashboard Streamlit local
task --list      # todas las tareas disponibles (documentación viva)
```

## Estructura (monorepo uv — [ADR-0002](docs/adr/0002-monorepo-uv-workspaces.md))

```
packages/
├── eda_ingesta/    # lib: scraper CIDO + caché + población + profiling (US3)
├── eda_core/       # lib: lógica de negocio — limpieza, enriquecimiento, features (US4-5)
├── eda_pipeline/   # app: CLI "eda-pipeline" que orquesta todo
└── eda_app/        # app: dashboard Streamlit para Render (US9)
docs/
├── PRD.md          # alcance, 12 user stories, roadmap
├── adr/            # decisiones registradas (fuentes, arquitectura, limpieza…)
└── business/       # spec original del bootcamp
notebooks/          # (US6) análisis narrativo — importa de eda_core, no contiene lógica
```

## Estado del proyecto

*(se actualiza con cada user story — fuente: [tablero](https://github.com/orgs/IA-P1-BCN/projects/48))*

- [x] US1 — Fuentes evaluadas y elegidas ([ADR-0001](docs/adr/0001-eleccion-fuentes.md))
- [x] US2 — Entorno monorepo uv con workspaces ([ADR-0002](docs/adr/0002-monorepo-uv-workspaces.md)), CI, OpenSpec
- [x] US3 — Scraper CIDO (bootstrap + scan RSS) + profiling · `task download` / `task scan-rss`
- [ ] US4-US5 — Limpieza TDD + normalización per cápita
- [x] US6 — Notebook EDA · [x] US7 — Gráficos informe+dashboard (task charts) · US8 pendiente
- [ ] US9-US12 — Dashboard, Render, Airflow, calidad + presentación
