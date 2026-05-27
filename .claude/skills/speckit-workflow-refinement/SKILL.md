---
name: speckit-workflow-refinement
description: "Refinamiento completo: fetch épica de Jira → spec → clarify → checklist → preview HTML → push stories. Invocar con la clave de la Epic."
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
fetch-epic → [if figma] fetch-designs → specify → do-while(clarify) → checklist → export HTML → gate → jira-push
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

### [1/7] fetch-epic

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [1/7] fetch-epic
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-atlassian-sync-fetch <epic_key>`.
Guarda el contenido formateado como `EPIC_CONTENT`.

### [2/7] fetch-designs (condicional)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [2/7] fetch-designs
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Si `figma_url` está presente**: invoca `/speckit-figma-export-fetch <figma_url>`.
**Si no**: muestra "↷ Sin Figma URL — paso omitido." y continúa.

### [3/7] specify

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [3/7] specify
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-specify` pasando `EPIC_CONTENT` como descripción de la feature.
Si hay diseños del paso anterior, inclúyelos como contexto adicional.

### [4/7] clarify (bucle)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [4/7] clarify
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ejecuta el bucle clarify (máximo 5 iteraciones):

1. Invoca `/speckit-clarify`.
2. Pregunta al usuario: "¿Quedan preguntas abiertas sin resolver en la spec? (yes / no)"
   - `yes` → repite desde el punto 1 (nueva iteración)
   - `no` → sale del bucle

Si se alcanzan 5 iteraciones sin resolver todas las dudas, avisa y continúa:
> "⚠️ Se alcanzó el límite de iteraciones. Quedan dudas abiertas — revísalas manualmente en spec.md antes de planificar."

### [5/7] checklist

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [5/7] checklist
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-checklist <epic_key>`.

### [6/7] export-spec (HTML preview)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [6/7] export-spec → HTML
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

### [7/7] jira-push

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [7/7] jira-push
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
- Si el Atlassian MCP no está conectado, aborta en el paso [1/7] con instrucciones de reconexión.
- Si `/speckit-figma-export-fetch` no está disponible y se proporcionó figma_url, avisa y omite el paso.
