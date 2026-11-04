# Proposal: fix-drift-pipeline-eda

## Why

El informe de drift (`2026-11-04_DRIFT_REPORT.md`) detectó divergencias entre las especificaciones (`docs/PRD.md`, `docs/adr/`, `GLOSSARY.md`) y la implementación actual en `eda_pipeline`, `eda_core`, `eda_app` y `notebooks/eda.ipynb`. Antes de cerrar US11 y US12 es necesario alinear código, tests y documentación.

## What Changes

- **`eda_pipeline` (`cli.py`) y `eda_core` (`build.py`)**: implementar los pasos `validate` y `export` del pipeline, soportar `--step scan` como alias incremental (usado por `.github/workflows/dataset.yml`), y ejecutar `clean → enrich → validate → export` en `--step all` cuando exista `data/raw/oposicions.csv`.
- **`eda_core` (`graficos.py`, `viz.py`)**: añadir el heatmap de estacionalidad (mes × año) y la media móvil de 12 meses sobre la evolución mensual (US7), y exponer helpers reutilizables para el notebook (`resumen_outliers_iqr`, `ranking_per_capita`).
- **`eda_app` (`app.py`)**: añadir filtro por rango de año/fecha (`fecha_convocatoria`) y renderizar los gráficos interactivos Plotly y KPIs por grupo/per cápita/calendario en el dashboard (US9).
- **`notebooks/eda.ipynb`**: importar `PALETA`, `aplicar_estilo` y helpers desde `eda_core` (ADR-0002), corregir `"intermedio"` → `"intermedi"` en el boxplot bivariado, añadir las relaciones bivariadas y ≥3 features nuevas de US6, redactar las conclusiones definitivas con datos reales y re-ejecutar el notebook de principio a fin.
- **Documentación y reportes (`README.md`, `docs/PRD.md`, `docs/adr/0001-eleccion-fuentes.md`, `reports/profiling.md`)**: regenerar `reports/profiling.md` con los 2.786 hitos reales y alinear el alcance documentado (filtro Vic 45 km, 814 procesos, Wikidata, enlaces explícitos a `packages/`).

## Capabilities

### New Capabilities

- `pipeline-eda`: validación, exportación, gráficos, dashboard y uso de `eda_core` desde el notebook.

### Modified Capabilities

(ninguna)

## Impact

- Código: `packages/eda_core`, `packages/eda_pipeline`, `packages/eda_app`, `notebooks/eda.ipynb`.
- Docs: `README.md`, `docs/PRD.md`, `docs/adr/0001-eleccion-fuentes.md`, `reports/profiling.md`.
