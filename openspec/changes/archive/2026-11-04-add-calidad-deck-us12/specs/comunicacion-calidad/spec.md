## ADDED Requirements

### Requirement: Informe de calidad de datos trazable a los ADRs y taxonomía E1/E2/E3

El proyecto SHALL incluir `docs/informe-calidad-datos.md` documentando qué faltaba en el origen, qué se corrigió en la limpieza, qué quedó pendiente y por qué (resumiendo los ADRs `0001`–`0005`), el resumen de errores de enlace `E1`/`E2`/`E3` con acción sugerida por clase, y una sección explícita `"¿Qué NO sabemos aún?"`.

#### Scenario: Verificación de secciones obligatorias del informe de calidad

- **WHEN** se inspecciona `docs/informe-calidad-datos.md`
- **THEN** contiene el resumen de los ADRs `0001` a `0005`, la tabla `E1`/`E2`/`E3` con acción sugerida y la sección `"¿Qué NO sabemos aún?"`

### Requirement: Presentación ejecutiva Quarto revealjs de 5 minutos

El proyecto SHALL proporcionar una presentación en `docs/presentacion/slides.qmd` reproducible mediante `task slides` (formato Quarto `revealjs`) centrada en un hallazgo principal para público no técnico y diseñada para presentarse en menos de 5 minutos.

#### Scenario: Regeneración de slides con `task slides`

- **WHEN** se ejecuta `task slides`
- **THEN** Quarto renderiza `docs/presentacion/slides.html` sin errores
