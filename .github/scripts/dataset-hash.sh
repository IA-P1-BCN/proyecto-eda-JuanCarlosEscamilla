#!/usr/bin/env bash
# Hash de contenido (12 chars) de un CSV del dataset, estable entre descargas:
# quita los tokens de firma `&<64 hex>` que CIDO regenera en cada fetch y ordena
# las filas (cabecera primero). Uso: dataset-hash.sh <csv>
set -euo pipefail
CSV="$1"
if command -v sha256sum >/dev/null; then SHA=(sha256sum); else SHA=(shasum -a 256); fi
{ head -n 1 "$CSV"; tail -n +2 "$CSV" | sed -E 's/&[0-9a-f]{64}//g' | LC_ALL=C sort; } \
  | "${SHA[@]}" | cut -c1-12
