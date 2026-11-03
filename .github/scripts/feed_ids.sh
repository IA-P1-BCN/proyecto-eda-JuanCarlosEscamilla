#!/usr/bin/env bash
# Obtiene los ids (Número de referència) del RSS general del CIDO con curl+awk
# y los compara con el feed de ayer: imprime nuevos y persistentes.
# Salida: data/raw/feed_hoy.tsv (id<TAB>url) — lo consume `task download`.
set -euo pipefail
URL_FEED="https://cido.diba.cat/rss/oposicions/oposicions"
DEST="data/raw"
mkdir -p "$DEST"

curl -sS -m 60 "$URL_FEED" \
| awk '
  /<item>/ {ref=""; link=""}
  match($0, /[0-9]{8}O[0-9]{2}/) {ref = substr($0, RSTART, 11)}
  /<link>/ {line = $0; gsub(/.*<link>/, "", line); gsub(/<\/link>.*/, "", line); link = line}
  /<\/item>/ {if (ref != "" && link != "") print ref "\t" link}
' | sort -u > "$DEST/feed_hoy.tsv"

HOY=$(wc -l < "$DEST/feed_hoy.tsv" | tr -d ' ')
echo "feed hoy: $HOY procesos con referencia"

if [ -f "$DEST/feed_ayer.tsv" ]; then
  comm -13 <(cut -f1 "$DEST/feed_ayer.tsv" | sort) <(cut -f1 "$DEST/feed_hoy.tsv" | sort) > "$DEST/feed_nuevos.txt" || true
  echo "nuevos en el feed vs ayer: $(wc -l < "$DEST/feed_nuevos.txt" | tr -d ' ')"
else
  echo "primera ejecución: sin referencia de ayer"
fi
