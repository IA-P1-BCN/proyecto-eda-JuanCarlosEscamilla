---
status: accepted
date: 2026-11-03
---

# Sin Spark: pandas + umbral de escala documentado

Se propuso añadir Apache Spark (junto a docker-compose y Airflow) para dar realismo de producción al pipeline. Con ~2.000 filas de hitos (237 procesos), Spark es contraproducente: en modo local es **más lento** que pandas (overhead de JVM y shuffle), añade una dependencia pesada (imágenes docker con JVM, sesión Spark, API distinta) y costaría +4-6h de un presupuesto ya ajustado. Decidimos: **pandas en `eda_core`**, y el umbral de migración **documentado como contrato**: si el dataset creciera más allá del umbral, se migra el paso `enrich` sin cambiar el spec `ingesta-cido` ni el contrato del pipeline.

| Dato | Valor |
|---|---|
| Filas a procesar | ~2.000 hitos |
| Umbral realista donde Spark gana a pandas | ~10⁷-10⁸ filas o clúster multi-nodo |
| Coste de añadirlo aquí | +4-6h + JVM en imagen (~1GB) + debugging Java |
| Decisión | pandas; revisión de motor solo al superar el umbral |

**Trigger de revisión**: >10⁶ filas (p. ej. re-scrapear todas las materias del CIDO con histórico) → evaluar Polars primero, Spark solo si hay clúster. Un data engineer con 2.000 filas no propone Spark; documenta a partir de cuándo lo haría.
