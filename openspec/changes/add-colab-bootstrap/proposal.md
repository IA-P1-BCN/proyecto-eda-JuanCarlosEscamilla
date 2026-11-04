# Change: Badge Open in Colab y auto-bootstrap para ejecutar el notebook en Google Colab

## Why

Cuando un usuario abre `notebooks/eda.ipynb` en Google Colab desde GitHub, Colab descarga únicamente el archivo `.ipynb` sin los paquetes del monorepo (`packages/eda_core`) ni el CSV enriquecido publicado en el release `dataset-v1.0`. Añadir el badge en `README.md` y un bloque de auto-bootstrap condicional (`if "google.colab" in sys.modules:`) permite ejecutar *Run All* en Colab importando el `eda_core` real del monorepo (cumpliendo ADR-0002, sin duplicar lógica ni usar fallbacks en el notebook).

## What Changes

- **`README.md`**: Añade el badge oficial `Open in Colab` apuntando a `notebooks/eda.ipynb` en `main`.
- **`notebooks/eda.ipynb`**: Añade en la celda inicial de configuración un bloque condicional `if "google.colab" in sys.modules:` que clona el repositorio para exponer `packages/eda_core/src` en `sys.path` y descarga `oposicions_enriquit.csv` desde el release `dataset-v1.0`.

## Impact

- Specs afectadas: `pipeline-eda`.
- Archivos afectados: `README.md`, `notebooks/eda.ipynb`, `packages/eda_pipeline/tests/test_us12_entregables.py`.
