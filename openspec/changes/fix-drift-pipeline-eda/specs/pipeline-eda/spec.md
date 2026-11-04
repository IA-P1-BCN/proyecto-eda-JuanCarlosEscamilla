# pipeline-eda — Delta

## ADDED Requirements

### Requirement: Validación y exportación del dataset enriquecido

El pipeline SHALL validar que el dataset enriquecido cumple el contrato de la spec (≥1.000 filas, ≥8 columnas, cero columnas de datos personales) en el paso `validate`, y SHALL verificar/exportar los artefactos listos para consumo del notebook y del dashboard en el paso `export`.

#### Scenario: dataset enriquecido válido

- **WHEN** se ejecuta `eda-pipeline --step validate` sobre un CSV enriquecido con ≥1.000 filas y las columnas del glosario
- **THEN** la validación devuelve resumen exitoso con filas, columnas y procesos únicos

#### Scenario: ejecución de `--step all` sin red

- **WHEN** se ejecuta `eda-pipeline --step all`
- **THEN** no realiza peticiones de red (`download`/`scan`) y ejecuta los pasos de procesamiento (`clean`, `enrich`, `validate`, `export`) si existe el CSV crudo

### Requirement: Dashboard con filtros completos y gráficos interactivos

El dashboard Streamlit (`eda_app`) SHALL permitir filtrar por institución/municipio, grupo de titulación, estado y rango de año/fecha de convocatoria, y SHALL mostrar KPIs y gráficos interactivos Plotly a partir del dataset enriquecido.

#### Scenario: filtrado combinado con rango de años

- **WHEN** se invoca `calcular_kpis` con filtros de municipio, grupo, estado y rango de años
- **THEN** devuelve únicamente las filas que cumplen todos los criterios

### Requirement: Notebook narrativo importando de `eda_core`

El notebook `notebooks/eda.ipynb` SHALL importar la paleta, estilo y funciones reutilizables desde `eda_core` (ADR-0002), usar las categorías canónicas del glosario (`urbano`, `intermedi`, `rural`) y ejecutarse de arriba abajo sin errores.

#### Scenario: ejecución completa del notebook

- **WHEN** se ejecuta `notebooks/eda.ipynb` de principio a fin sobre `data/processed/oposicions_enriquit.csv`
- **THEN** todas las celdas terminan sin error y las 3 preguntas de negocio quedan respondidas con cifras reales
