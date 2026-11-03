# Prerequisites

Lo que necesitas instalado antes de tocar el repo. Regla del proyecto: los comandos **nunca se documentan crudos** — se entran como tasks en [`Taskfile.yml`](Taskfile.yml) y se descubren con `task --list` (convención en [`AGENTS.md`](AGENTS.md)).

## Siempre (día 1)

| Herramienta | Para qué | Instalar | Verificar |
|---|---|---|---|
| **[uv](https://docs.astral.sh/uv/)** | Gestor de paquetes/entornos del monorepo (un venv, un lockfile). Instala también Python ≥3.12 si falta | `brew install uv` | `uv --version` |
| **[go-task](https://taskfile.dev)** | Task runner + documentación viva de comandos | `brew install go-task` | `task --version` |
| **git** | Control de versiones (viene en macOS/Linux) | — | `git --version` |

> No necesitas instalar Python a mano: `uv sync` descarga y fija el intérprete correcto.

## Por fase (llegan con su user story)

| Herramienta | Fase | Para qué | Instalar |
|---|---|---|---|
| **[Quarto](https://quarto.org)** | US8, US12 | Informe ejecutivo → PDF + deck revealjs 5min | `brew install --cask quarto` |
| **Docker Desktop** | US11 | Airflow local (orquestador one-click) | `brew install --cask docker` |
| **[astro-cli](https://www.astronomer.io/docs/astro/cli/install-cli)** | US11 | CLI que dockeriza Airflow (`astro dev start`) | `brew install astro-cli` |
| **[gh](https://cli.github.com)** | opcional | Tablero de Projects y PRs por CLI (para agentes/contribuidores) | `brew install gh` |

## Primer check (2 min)

```bash
task sync     # descarga Python si hace falta + instala todo el monorepo
task test     # → N passed = entorno correcto
```

Si `task test` pasa, tienes todo lo del día 1. El resto se instala cuando su fase lo pida — el README lo avisará.
