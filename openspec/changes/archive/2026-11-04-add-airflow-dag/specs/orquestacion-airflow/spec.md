## ADDED Requirements

### Requirement: DAG `eda_oposicions` de 6 etapas sobre módulos del monorepo

El sistema SHALL proporcionar un DAG de Apache Airflow con identificador `eda_oposicions` en `airflow/dags/eda_oposicions.py` que encadene secuencialmente las 6 tareas `scan_download >> profile >> clean >> enrich >> validate >> export` invocando las funciones de `eda_ingesta` y `eda_core`.

#### Scenario: Estructura y dependencias del DAG

- **WHEN** se carga la definición de `airflow/dags/eda_oposicions.py`
- **THEN** existe el DAG `eda_oposicions` con las 6 tareas `scan_download`, `profile`, `clean`, `enrich`, `validate` y `export` conectadas en ese orden exacto

#### Scenario: Ejecución idempotente del pipeline en Airflow

- **WHEN** se ejecuta el DAG `eda_oposicions` dos veces consecutivas sobre la caché existente
- **THEN** las 6 tareas finalizan con éxito y el fichero `data/processed/oposicions_enriquit.csv` conserva exactamente el mismo número de filas sin duplicados
