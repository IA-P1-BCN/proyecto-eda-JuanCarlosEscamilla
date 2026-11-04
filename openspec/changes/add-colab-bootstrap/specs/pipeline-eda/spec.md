## MODIFIED Requirements

### Requirement: Notebook narrativo importando de `eda_core`

El notebook `notebooks/eda.ipynb` SHALL importar la paleta, estilo y funciones reutilizables desde `eda_core` (ADR-0002), usar las categorías canónicas del glosario (`urbano`, `intermedi`, `rural`), incluir auto-bootstrap condicional para Google Colab (`google.colab`) que importe `eda_core` desde el monorepo y descargue el dataset desde el release `dataset-v1.0`, y ejecutarse de arriba abajo sin errores.

#### Scenario: ejecución completa del notebook

- **WHEN** se ejecuta `notebooks/eda.ipynb` de principio a fin sobre `data/processed/oposicions_enriquit.csv`
- **THEN** todas las celdas terminan sin error y las 3 preguntas de negocio quedan respondidas con cifras reales

#### Scenario: compatibilidad con Google Colab y badge en README

- **WHEN** se inspeccionan `README.md` y `notebooks/eda.ipynb`
- **THEN** `README.md` incluye el badge `colab-badge.svg` hacia `notebooks/eda.ipynb` y la primera celda de código del notebook configura `packages/eda_core/src` y descarga `oposicions_enriquit.csv` del release cuando se ejecuta en `google.colab`
