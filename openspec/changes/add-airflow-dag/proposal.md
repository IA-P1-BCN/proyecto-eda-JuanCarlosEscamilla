# Change: Orquestación del pipeline EDA con Apache Airflow (US11)

## Why

La historia de usuario US11 (`#11`) requiere que el pipeline completo de ingesta, perfilado, limpieza, enriquecimiento, validación y exportación se ejecute de forma orquestada e idempotente dentro de Apache Airflow en contenedores Docker (`task airflow-up`), reutilizando los módulos de `eda_ingesta` y `eda_core` sin duplicar lógica.

## What Changes

- **DAG `airflow/dags/eda_oposicions.py` (`#57`)**: Define el DAG `eda_oposicions` (`schedule=None`, `catchup=False`) con 6 tareas encadenadas (`scan_download >> profile >> clean >> enrich >> validate >> export`) que invocan directamente las funciones de `eda_ingesta` y `eda_core`.
- **Integración en `infra/docker-compose.yml` (`#58`)**: Monta `./reports:/opt/airflow/reports`, configura `working_dir: /opt/airflow` y asegura la disponibilidad de `beautifulsoup4` en el contenedor para que todos los paquetes del monorepo importen y escriban en las rutas relativas esperadas.
- **Verificación end-to-end e idempotencia (`#59`)**: Ejecución completa de las 6 tareas en verde y comprobación de que re-ejecutar el DAG mantiene constante el número de filas procesadas (2.690).
- **Documentación y comandos (`#60`)**: Actualización de `README.md` con las instrucciones de `task airflow-up` / `task airflow-down` y marcado de US11 como completada.

## Impact

- Specs afectadas: `orquestacion-airflow` (nueva capacidad).
- Código afectado: `airflow/dags/eda_oposicions.py`, `infra/docker-compose.yml`, `packages/eda_pipeline/tests/test_dag.py`, `README.md`.
- Referencias: `#11`, `#57`, `#58`, `#59`, `#60`.
