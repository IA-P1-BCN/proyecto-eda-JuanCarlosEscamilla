#!/usr/bin/env bash
# Publica el dataset como release asset SOLO si el contenido cambió.
# Mismo script para local (task dataset-release) y GitHub Actions — cero drift.
# Requiere: gh autenticado (local: tu token; Actions: GITHUB_TOKEN).
set -euo pipefail

# Nivel: raw (bronze) | processed (silver) — task dataset-release DATA=processed
NIVEL="${1:-raw}"
case "$NIVEL" in
  raw)       CSV="data/raw/oposicions.csv"; PROFILING="reports/profiling.md" ;;
  processed) CSV="data/processed/oposicions_procesado.csv"; PROFILING="reports/profiling-processed.md" ;;
  *) echo "nivel desconocido: $NIVEL (raw|processed)" >&2; exit 1 ;;
esac
REPO="${GITHUB_REPOSITORY:-IA-P1-BCN/proyecto-eda-JuanCarlosEscamilla}"

[ -f "$CSV" ] || { echo "no existe $CSV — ejecuta antes: task download / task clean" >&2; exit 1; }

# Tag content-addressed: mismo contenido = mismo tag = release duplicado imposible
HASH=$(sha256sum "$CSV" | cut -c1-12)
TAG="dataset-$NIVEL-$HASH"
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
