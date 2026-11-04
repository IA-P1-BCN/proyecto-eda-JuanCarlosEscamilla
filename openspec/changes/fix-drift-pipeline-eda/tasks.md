# Tasks: fix-drift-pipeline-eda

## 1. Pipeline CLI, validación y exportación (TDD)

- [x] 1.1 Implementar `validar_dataset` y `exportar_dataset` en `eda_core.build` con tests en `test_build.py`
- [x] 1.2 Conectar `validate`, `export`, `scan` y `all` en `eda_pipeline.cli` con tests en `test_cli.py` y regenerar `reports/profiling.md`

## 2. Gráficos, helpers de `eda_core` y notebook EDA (TDD)

- [x] 2.1 Añadir helpers analíticos (`resumen_outliers_iqr`, `ranking_per_capita`) y media móvil en `eda_core.graficos` con tests
- [x] 2.2 Actualizar `notebooks/eda.ipynb` para importar `eda_core`, corregir `"intermedi"`, completar features/bivariado/conclusiones y ejecutar `nbconvert --execute`

## 3. Dashboard Streamlit (TDD)

- [x] 3.1 Añadir filtro por rango de fechas/años y gráficos interactivos Plotly en `eda_app.app` con tests en `test_app.py`

## 4. Alineación de documentación

- [x] 4.1 Actualizar `README.md`, `docs/PRD.md`, `docs/adr/0001-eleccion-fuentes.md` y enlaces de código
