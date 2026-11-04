# Tasks: add-scraper-cido

## 1. Parsers puros (TDD — tests primero)

- [x] 1.1 `parse_identificador`: `20230127O46` → `date(2023,1,27)`; inválidos → error tipado
- [x] 1.2 `parse_plazas`: "1 placa de…", "2 places de…" (ca/es) → int; sin plaza → None
- [x] 1.3 `parse_fechas`: dd/mm/yyyy → date; rangos del listado de hitos

## 2. Descarga educada y caché

- [x] 2.1 Cliente HTTP con pausa + User-Agent + reintentos backoff (test con servidor local)
- [x] 2.2 Caché HTML en `data/raw/html/` (clave = URL) y consulta antes de red
- [x] 2.3 Crawler de listados (~5 páginas, materia 24) → cola de fichas

- [x] 2.4 Scan RSS incremental: 1 petición → diff ids → fetch solo nuevos → filtro materia en ficha

## 3. Parseo de fichas y formato largo

- [x] 3.1 Parser de ficha → proceso (dimensión) + hitos (formato largo)
- [x] 3.2 Registro de adjuntos con slug semántico + estados E1/E2/E3
- [x] 3.3 Escritura de CSV crudo + log de calidad

## 4. Integración y profiling

- [x] 4.1 `pipeline --step download` llama a eda_ingesta y llena `data/raw/`
- [x] 4.2 Profiling inicial (nulos/tipos/raros) → `reports/`
- [x] 4.3 Test de idempotencia end-to-end (segunda ejecución, cero peticiones nuevas)
