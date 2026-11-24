## ADDED Requirements

### Requirement: Release del dataset solo con cambio de contenido

El release del dataset (`dataset-release.sh`, ejecutado a diario por `.github/workflows/dataset.yml`) SHALL identificar cada versión con un hash del contenido canónico del CSV: sin los tokens de firma `&<64 hex>` que CIDO regenera en cada descarga y con las filas ordenadas. SHALL NOT publicar un release nuevo si ese hash ya tiene release.

#### Scenario: solo cambian los tokens de firma

- **WHEN** el CSV nuevo difiere del último publicado solo en los tokens `&<64 hex>` de `hito_url` o en el orden de las filas
- **THEN** el hash canónico es el mismo y no se crea release

#### Scenario: hay un hito nuevo

- **WHEN** el CSV nuevo contiene un hito que no estaba en el último publicado
- **THEN** el hash canónico cambia y se publica un release `dataset-<nivel>-<hash>`
