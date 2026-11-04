# Change: Informe de calidad de datos, presentación 5 min, release dataset-v1.0 y cierre (US12)

## Why

La historia de usuario US12 (`#12`) cierra el producto de datos documentando con transparencia la calidad del dataset (qué faltaba, qué se corrigió, qué quedó pendiente y por qué, síntesis de ADRs `0001`–`0005`, taxonomía E1/E2/E3 y la pregunta explícita `"¿Qué NO sabemos aún?"`), generando una presentación ejecutiva de <5 minutos en Quarto revealjs (`task slides`) centrada en un único hallazgo principal para público no técnico, publicando el release `dataset-v1.0` con el cron activado en `.github/workflows/dataset.yml`, y dejando `README.md` y `docs/PRD.md` cerrados al 100%.

## What Changes

- **Informe de calidad (`#61`)**: Crea `docs/informe-calidad-datos.md` con auditoría completa de nulos, duplicados eliminados, resumen de ADRs `0001`–`0005`, tabla E1/E2/E3 con acción sugerida por clase, desglose de procesos sin match municipal (`reports/calidad-municipios.csv`) y sección explícita `"¿Qué NO sabemos aún?"`.
- **Presentación revealjs de 5 min (`#62`)**: Crea `docs/presentacion/slides.qmd`, la tarea `slides` en `Taskfile.yml` (`task slides`) y renderiza `docs/presentacion/slides.html`.
- **Release `dataset-v1.0` y cron (`#63`)**: Activa el `schedule` diario en `.github/workflows/dataset.yml` (documentando el límite de 60 días de inactividad de GitHub Actions) y publica el release `dataset-v1.0`.
- **Cierre documental (`#64`)**: Actualiza `README.md` y `docs/PRD.md` al estado final (100% completado).

## Impact

- Specs afectadas: `comunicacion-calidad` (nueva capacidad).
- Archivos afectados: `docs/informe-calidad-datos.md`, `docs/presentacion/slides.qmd`, `Taskfile.yml`, `.github/workflows/dataset.yml`, `README.md`, `docs/PRD.md`, `packages/eda_pipeline/tests/test_us12_entregables.py`.
- Referencias: `#12`, `#61`, `#62`, `#63`, `#64`.
