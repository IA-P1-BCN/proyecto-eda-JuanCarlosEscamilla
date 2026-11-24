# Change: Hash de contenido estable para el release diario del dataset

## Why

`dataset-release.sh` publica un release solo si cambia el `sha256` del CSV, pero hashea los bytes crudos. CIDO firma cada enlace de BOP/DOGC con un token `&<64 hex>` que se regenera en cada descarga, así que el hash cambia todos los días aunque los datos no cambien (p. ej. `dataset-raw-f26f5a4f74c3` del 2026-11-22 es idéntico a `dataset-raw-870ecfe9264f` salvo esos tokens). El resultado es un release, un tag y un "Updated" en el repo cada día.

## What Changes

- **`.github/scripts/dataset-hash.sh`** (nuevo): imprime un hash de 12 caracteres sobre una forma canónica del CSV (sin tokens `&<64 hex>`, filas ordenadas, cabecera primero).
- **`.github/scripts/dataset-release.sh`**: usa `dataset-hash.sh` en vez de `sha256sum` sobre los bytes crudos. El asset publicado sigue siendo el CSV original.

## Impact

- Specs afectadas: `ingesta-cido`.
- Archivos afectados: `.github/scripts/dataset-hash.sh`, `.github/scripts/dataset-release.sh`, `packages/eda_pipeline/tests/test_dataset_hash.py`.
- Los tags `dataset-raw-*` existentes no cambian. El primer run tras el merge publicará un release más (el hash canónico difiere del crudo) y a partir de ahí solo cuando cambien los datos.
