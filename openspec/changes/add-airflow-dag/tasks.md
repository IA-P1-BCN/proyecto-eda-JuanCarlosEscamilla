## 1. Implementación US11

- [x] 1.1 Crear tests y DAG `airflow/dags/eda_oposicions.py` con las 6 tareas `scan_download >> profile >> clean >> enrich >> validate >> export` (#57)
- [ ] 1.2 Actualizar `infra/docker-compose.yml` con volumen `reports`, `working_dir: /opt/airflow` y dependencias para importar el monorepo (#58)
- [ ] 1.3 Verificar ejecución end-to-end e idempotencia del DAG en el stack Docker de Airflow (#59)
- [ ] 1.4 Actualizar `README.md` con instrucciones de Airflow y checklist de US11 (#60)
