# Acceptance Criteria (AC) — formato de las user stories

## Regla

Cada user story (issue) define su **DoD como Acceptance Criteria: pasos numerados, secuenciales y verificables**. Un reviewer debe poder ejecutar los pasos en orden y tachar cada uno sin interpretar nada. Si un paso no se puede seguir tal cual está escrito, el AC está mal escrito.

- El **AC vive en el cuerpo de la issue** y es la fuente de verdad del DoD (el PRD mantiene el alcance, no los pasos).
- Los pasos se escriben **desde el punto de vista del que verifica** (normalmente con `task ...`, URLs o rutas concretas — nunca "funciona bien").
- El resultado esperado va **después de una flecha** (`→`) en el mismo paso.
- Si una US tiene parte *stretch*, sus pasos van en un bloque final separado y NO cuentan para cerrar la issue.
- Al abrir el PR: la review consiste en recorrer los pasos; el PR merguea cuando todos están tachados (o los no-stretch).

## Plantilla (sección del cuerpo de la issue)

```md
**Alcance**: <una frase — el qué y el porqué, remite al PRD>

**Acceptance Criteria** (verificar en orden):
1. `task sync && task test` → todos los tests en verde
2. `task download` → crea `data/raw/…` con N ficheros
3. …

**Stretch** (no bloquea el cierre):
- …

**Bloqueado por**: #N, #M
```

## Anti-patrones (cómo NO escribir un AC)

| ❌ Malo | ✅ Bueno |
|---|---|
| "La suite de tests está verde" | "`task test` → N passed, 0 failed" |
| "El dashboard funciona" | "`task dashboard` → abre localhost:8501; mover el filtro de municipio cambia los KPIs" |
| "El código es limpio" | "`grep -c 'def ' notebook.ipynb` devuelve 0 fuera de funciones de plotting" |
| "Se respeta el portal" | "los timestamps del log de descarga están separados ≥ la pausa configurada" |

## Proceso

1. La issue se crea **con su AC ya escrito** (en la misma PR que la abre el agente, o por el PO antes de arrancar la story).
2. Cambios de alcance durante la story → se actualiza el AC **en el PR que los introduce**, nunca después del merge.
3. La issue cierra solo cuando el checklist de AC está completo (los stretch no bloquean).
