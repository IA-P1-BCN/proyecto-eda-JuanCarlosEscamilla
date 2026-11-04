#!/usr/bin/env bash
# Publica el dataset como release asset SOLO si el contenido cambió.
# Mismo script para local (task dataset-release) y GitHub Actions — cero drift.
# Requiere: gh autenticado (local: tu token; Actions: GITHUB_TOKEN).
set -euo pipefail

# Nivel: raw (bronze) | processed (silver) | v1.0 (gold final) — task dataset-release DATA=v1.0
NIVEL="${1:-raw}"
case "$NIVEL" in
  raw)       CSV="data/raw/oposicions.csv"; PROFILING="reports/profiling.md"; TAG_FIJO="" ;;
  processed) CSV="data/processed/oposicions_procesado.csv"; PROFILING="reports/profiling-processed.md"; TAG_FIJO="" ;;
  v1.0|gold) CSV="data/processed/oposicions_enriquit.csv"; PROFILING="docs/informe-calidad-datos.md"; TAG_FIJO="dataset-v1.0" ;;
  *) echo "nivel desconocido: $NIVEL (raw|processed|v1.0)" >&2; exit 1 ;;
esac
REPO="${GITHUB_REPOSITORY:-IA-P1-BCN/proyecto-eda-JuanCarlosEscamilla}"

[ -f "$CSV" ] || { echo "no existe $CSV — ejecuta antes: task download / task pipeline" >&2; exit 1; }

# Tag content-addressed (salvo tag semántico explícito dataset-v1.0)
HASH=$(sha256sum "$CSV" | cut -c1-12)
TAG="${TAG_FIJO:-dataset-$NIVEL-$HASH}"
FILAS=$(( $(wc -l < "$CSV") - 1 ))

if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
  echo "sin cambios: $TAG ya existe (idempotente)"
  exit 0
fi

FECHA=$(date +%F)
NOTAS="Dataset $NIVEL en formato largo generado desde cido.diba.cat (materia: Informàtica. Noves tecnologies, radio ${FILTRO_DESC:-Vic 45km}).

- filas de hito: $FILAS
- corte: $FECHA
- reproducible con: \`task pipeline\` (ver PREREQUISITES.md)
- profiling adjunto (nulos, doc_slug, E1/E2/E3)
- origen y decisiones: docs/adr/0001-eleccion-fuentes.md"

gh release create "$TAG" "$CSV" ${PROFILING:+ "$PROFILING"} \
  --repo "$REPO" \
  --title "Dataset $TAG — $FILAS hitos" \
  --notes "$NOTAS"
echo "✓ release $TAG publicado ($FILAS filas, corte $FECHA)"
