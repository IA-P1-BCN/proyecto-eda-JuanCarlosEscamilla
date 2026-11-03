# PR workflow — quién mergea y con qué granularidad

## Regla 1: el merge es humano

- El agente **nunca mergea PRs** (ni `gh pr merge`, ni `--admin`): su trabajo termina en branch → commits → PR abierto con checklist de review como comentario.
- El usuario revisa y mergea personalmente. El bypass `--admin` (proyecto solo: el autor no puede aprobar su propio PR) es siempre **decisión consciente del usuario**, nunca del agente.
- Origen de la regla: el agente mergeó el PR #13 por su cuenta el 2026-11-03; el usuario lo cuestionó y se codificó la pauta.

## Regla 2: granularidad — ampliar antes que abrir

- **Evita PRs cortos innecesarios**: si el cambio es pequeño (pocos ficheros) y pertenece al área de un PR **ya abierto** (docs, tooling, convenciones), **extiéndelo** con un commit más en lugar de abrir otro.
- Las features no relacionadas mantienen su propio PR — un PR, un tema. La granularidad no justifica mezclar cosas que el reviewer querría aprobar por separado.
- Si un PR abierto acumula temas distintos a los de su título, es señal de que tocaba dividir antes, no después.

## Contenido mínimo de un PR

1. **Título** convencional y ligado a lo que entrega (story, ADR o convención).
2. **Body**: qué incluye · fuente de verdad (PRD / ADR / issue) · **review checklist**.
3. Si la story tiene **Acceptance Criteria** en su issue (`docs/agents/acceptance-criteria.md`), el checklist ES recorrer esos pasos y tacharlos.
4. CI en verde antes de pedir el merge.

## Flujo

```
issue → branch conventional → commits → PR abierto (checklist) → STOP
                                                      ↓
                                    el usuario revisa y mergea (con --admin si procede)
```
