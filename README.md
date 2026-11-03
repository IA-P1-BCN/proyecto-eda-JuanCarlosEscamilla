# Proyecto EDA — Oposicions CIDO 🎓

Análisis exploratorio de datos (EDA) sobre los **procesos selectivos de informática** en los ayuntamientos de la provincia de Barcelona. Bootcamp Factoría F5 · alcance y plan en [`docs/PRD.md`](docs/PRD.md).

## ¿De dónde salen los datos?

| Fuente | Qué aporta | URL |
|---|---|---|
| **CIDO (Diputació de Barcelona)** — fuente principal | Procesos selectivos (oposiciones y bolsas de trabajo) de los ayuntamientos de la provincia, filtrados por la materia *Informàtica. Noves tecnologies*: 237 procesos con sus hitos publicados (BOP/DOGC) | [cido.diba.cat/oposicions](https://cido.diba.cat/oposicions?filtreMateria%5Boptions%5D%5B%5D=24) |
| **INE / DIBA** — enriquecimiento | Población por municipio, para comparar plazas per cápita entre municipios grandes y pequeños | ine.es · diba.cat |

Los datos se descargan con un scraper propio (no hay API pública) y se cachean en `data/raw/` — nadie vuelve a pedir al portal lo que ya está en disco. La decisión completa, con las alternativas descartadas, está en [ADR-0001](docs/adr/0001-eleccion-fuentes.md).

## Cómo ejecutarlo

*(en construcción — se completa en US2 con `uv`, el pipeline de un comando y el notebook)*

```bash
# previsto para US2:
uv sync              # instala las dependencias (requirements.txt)
pytest               # tests de las funciones de limpieza
python -m eda.pipeline   # descarga → limpia → exporta, en un comando
```

## Estructura

```
docs/PRD.md            # alcance, 12 user stories, roadmap
docs/adr/              # decisiones registradas (elección de fuentes, limpieza…)
docs/business/         # spec original del bootcamp
src/eda/               # código del pipeline (scraper, limpieza, análisis)
data/                  # crudo y procesado (gitignored)
```
