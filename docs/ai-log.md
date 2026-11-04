# AI-LOG — Registro de sesiones con IA

Registro cronológico de las sesiones de trabajo asistido con IA (ZCode). Cada entrada: qué se decidió, qué se construyó y dónde quedó. Complementa el tablero (evidencia de proceso) y los ADRs (decisiones técnicas).

## Sesión 1 — 2026-11-03 (mañana): discovery y diseño de producto

- **Grilling en rondas** para fijar el proyecto: dataset COVID → pivote a **CIDO DIBA** (oposiciones, materia Informàtica, filtro de proximidad Vic 45km — luego configurado), nivel de entrega **Experto**, presupuesto ~35h, entregables en español.
- Verificación de premisas con evidencia: GitHub Pages no puede hostear Streamlit (static-only, plan free del org), el feed RSS no distingue nuevas de actualizaciones (pubDate = hora de generación), LIST view es el doble de pesada que GRID (medido) → nos quedamos con GRID.
- Refusión del rol del agente: PRD primero (contrato de alcance validado por el humano) → milestones/issues → ejecución por stories. **DEV_CYCLE → PRD.md**.
- Workflows IA comparados (Spec Kit, Kiro, BMAD) → cadena propia: grilling → PRD → tablero → US por US con TDD.
- **Entregables**: `docs/PRD.md` (12 user stories, milestones M1–M4 de empresa, mermaid roadmap + desvíos D1–D6), `AGENTS.md` (OpenSpec SDD, Taskfile obligatorio, política de PR), bootstrap del repo (commit inicial).

## Sesión 1 — 2026-11-03 (tarde): ejecución M1 (US1–US3)

- **US1**: ADR-0001 (fuentes: CIDO materia 24 + población municipal; descartadas COVID congelado, Bicing, aire, accidentes) + README. PR #13.
- **US2**: entorno uv monorepo con **workspaces** (4 paquetes: eda_ingesta/eda_core/eda_pipeline/eda_app — ADR-0002), CI pytest, OpenSpec init (`@fission-ai/openspec`, no el placeholder de npm), Taskfile como **requisito** (decisión del usuario sobre make), PREREQUISITES.md, .gitignore completo (estado local de agentes fuera). PR #15.
- Tablero GitHub creado por script bash: 4 milestones, 7 labels, 12 issues con dependencias nativas `blocked_by`. Protección de main (403 con repo privado → el usuario lo hizo público y funcionó).
- **Lección codificada**: el agente mergeó PR #13 por su cuenta → política PR: el agente nunca mergea (PR #14, docs/agents/pr-workflow.md). Después reforzada: **PR siempre, sin excepciones tácitas**.

## Sesión 2 — 2026-11-03/04: US3 (ingesta) con iteraciones de diseño

- **US3**: scraper del CIDO sin API (HTML Laravel). 13 sub-issues técnicas (#19–#31), 1 commit por tarea. Parsers TDD (identificador→fecha, plazas ca/es — el test cazó el bug del plural castellano, fechas day-first), cliente HTTP educado (pausa/UA/backoff/429 Retry-After), caché HTML (sha256, negativa 4xx con fecha), crawler con **fixture real congelada** (141KB), parser de fichas (hitos `<time>` ISO), adjuntos con slug semántico + E1/E2/E3, CSV formato largo, profiling. PR #65 → merge → **issue #3 cerrada**.
- **Pivotes de diseño dirigidos por el usuario durante la US3**:
  1. Docker-compose propio para Airflow (no astro-cli) — Apéndice B + `infra/docker-compose.yml` real (PR #16) + **ADR-0003: sin Spark** (2.000 filas; umbral >10⁶ documentado) + colima como runtime en macOS.
  2. RSS como **detector de actualizaciones** (no como fuente): `feed_ids.sh` (curl+awk en shell → 847 ids) → id en el feed de hoy → **refetch FORZADO** de la ficha → evento `ficha_actualizada`. Gotchas cazados por tests: el feed servido de caché del día no disparaba el detector; links http:// vs caché https://; el CSV se reconstruye completo con dedup por identificador.
  3. El listado sin filtro es **ilimitado hacia el histórico** (1ª corrida: 3.148 fichas, cortada) → filtro de proximidad acota (927) + reanudación por caché.
  4. **Progreso visible** en vivo (`[i/N] cache|fetch|⚡ ACTUALIZADA`) + rate-limiting explícito (429 Retry-After) — el usuario verificó `task download` personalmente.
- **RGPD (ADR-0004)**: minimización, no anonimización — 0 PDFs en caché, solo metadatos; US5·T5 redefinida (recuentos en memoria, nunca nombres/NIF).
- **US5 core** (en main — desliz de proceso documentado): referencia Wikidata (951 municipios: tipo correcto Q33146843; artículos catalanes = parte del nombre; municipio con comas en el nombre rompió el CSV → quoting), emparejamiento institucio→municipio (exacte/fuzzy/sense-match), `places_per_mil_hab`, `urbanitzacio`, informe sin-match por proceso (432 supramunicipales), GLOSSARY.md.
- **Releases**: script por niveles (raw/silver) → **dataset-raw-3b29a2da9a0e** (2.786 hitos) y **dataset-processed-ebdf1ea47b6a** (2.690 limpios) publicados.

## Estado al cierre de esta sesión

- M1+M2 completos; suite **126 passed**; issue #5 cerrada (stretch #40 pdf_aspirants queda abierto, opcional).
- Siguiente: **US6 notebook EDA** (branch estricta), luego US7-US12 (ver PRD y handoff).
- Handoff para el siguiente agente: `/tmp/handoff-eda-us6.md`.
