---
name: speckit-workflow-refinement
description: "Refinamiento completo: fetch épica de Jira → designs → spec → clarify → challenge functional → checklist → preview HTML → push stories. Invocar con la clave de la Epic."
argument-hint: "<epic-key> [figma-url]  e.g. /speckit-workflow-refinement DEVPT-518"
compatibility: Requires spec-kit project structure with .specify/ directory and Atlassian MCP connected
metadata:
  author: afianza-local
  source: workflows/refinement/workflow.yml
user-invocable: true
---

# Feature Refinement Workflow

Ejecuta el ciclo completo de refinamiento: desde la Epic de Jira hasta las User Stories publicadas.

## Flujo

```
fetch-epic → [if figma] fetch-designs → specify → do-while(clarify) → challenge functional → checklist → export HTML → gate → jira-push
```

## User Input

```text
{{ARGS}}
```

Extrae del input:
- **epic_key** (requerido): clave de Epic de Jira (e.g. `DEVPT-518`). Si no viene, pregunta.
- **figma_url** (opcional): URL de Figma. Si no viene, omite el paso de diseños sin preguntar.

---

## Execution Steps

### Setup

Muestra el encabezado del workflow:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  REFINEMENT WORKFLOW
  Epic: <epic_key>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### [1/8] fetch-epic

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [1/8] fetch-epic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-atlassian-sync-fetch <epic_key>`.
Guarda el contenido formateado como `EPIC_CONTENT`.

### [2/8] fetch-designs (condicional)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [2/8] fetch-designs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Si `figma_url` está presente**: invoca `/speckit-figma-export-browser <figma_url>`.
**Si no**: muestra "↷ Sin Figma URL — paso omitido." y continúa.

### [3/8] specify

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [3/8] specify
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-specify` pasando `EPIC_CONTENT` como descripción de la feature.
Si hay diseños del paso anterior, inclúyelos como contexto adicional.

### [4/8] clarify (bucle)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [4/8] clarify
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ejecuta el bucle clarify (máximo 5 iteraciones):

1. Invoca `/speckit-clarify`.
2. Pregunta al usuario: "¿Quedan preguntas abiertas sin resolver en la spec? (yes / no)"
   - `yes` → repite desde el punto 1 (nueva iteración)
   - `no` → sale del bucle

Si se alcanzan 5 iteraciones sin resolver todas las dudas, avisa y continúa:
> "⚠️ Se alcanzó el límite de iteraciones. Quedan dudas abiertas — revísalas manualmente en spec.md antes de planificar."

### [5/8] challenge functional

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [5/8] challenge functional
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-challenge functional`. La skill ejecuta un adversarial review con `business-logic-reviewer` sobre los 10 buckets (real-world events, work reassignment, state transitions, forgotten actors, quantitative edges, notifications, visibility/permissions, implied rules, prioritization, design conformance). Genera `challenge-report.md` con las decisiones D* y los gaps G*.

#### GATE: review-challenge

Muestra:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏸ GATE — review-challenge
  Revisa challenge-report.md. Las decisiones D* deberían quedar
  reflejadas en spec.md > Open Questions (acepta el prompt de la
  skill o cherry-pick manual antes de continuar).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

- `approve` → Open Questions actualizadas, continuar.
- `reject` → abort: "Workflow detenido en [review-challenge]. Faltan decisiones por capturar antes de seguir."

#### GATE: planning-readiness-gate

Muestra:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏸ GATE — planning-readiness
  Comprueba la tabla "Open Questions" en spec.md. ¿Hay decisiones
  marcadas como bloqueantes para el data model o la arquitectura
  que aún no tienen respuesta?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

- `ready` → no hay bloqueantes críticos, continuar al checklist.
- `blocked` → abort: "Workflow detenido. Decisiones estructurales pendientes — escalar a PO antes de seguir."

### [6/8] checklist

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [6/8] checklist
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-checklist <epic_key>`. Genera checklist de **calidad de redacción** (clarity, consistency, measurability, completeness) — los gaps de negocio ya quedaron capturados en challenge funcional, aquí sólo se valida que los requisitos estén bien escritos.

### [7/8] export-spec (HTML preview)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [7/8] export-spec → HTML
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-md-html-export-export spec`.
Muestra la ruta del fichero HTML generado.

### GATE: review-spec

Muestra:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏸ GATE — review-spec
  Revisa la spec en HTML.
  ¿Todo correcto para subir a Jira?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Espera respuesta explícita:
- `approve` → continúa
- `reject` → abort: "Workflow detenido en [review-spec]. Corrige spec.md y vuelve a ejecutar desde el paso clarify."

### [8/8] jira-push

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [8/8] jira-push
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-atlassian-sync-push <epic_key>`.

### Fin

Muestra resumen:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ REFINEMENT COMPLETADO
  Epic:    <epic_key>
  Stories: creadas en Jira
  Spec:    specs/<feature>/spec.md
  HTML:    specs/<feature>/spec.html
  Siguiente: /speckit-workflow-planning
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Behavior rules

- Nunca saltes un gate sin confirmación explícita del usuario.
- Si el usuario escribe "stop" o "abort", detén el workflow inmediatamente.
- Si el Atlassian MCP no está conectado, aborta en el paso [1/8] con instrucciones de reconexión.
- Si `/speckit-figma-export-browser` no está disponible (Claude-in-Chrome no conectado) y se proporcionó figma_url, avisa y omite el paso.
- En [5/8] challenge functional, si el reviewer no encuentra gaps significativos, deja pasar igualmente — challenge limpio es un resultado válido, no un error.
