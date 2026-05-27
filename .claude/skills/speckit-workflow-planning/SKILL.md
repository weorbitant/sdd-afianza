---
name: speckit-workflow-planning
description: "Planificación técnica: plan → preview HTML → tasks → analyze → preview HTML. Produce artefactos listos para implementar."
argument-hint: "[scope]  e.g. /speckit-workflow-planning backend-only"
compatibility: Requires spec-kit project structure with .specify/ directory and an active feature with spec.md
metadata:
  author: afianza-local
  source: workflows/planning/workflow.yml
user-invocable: true
---

# Feature Planning Workflow

Ejecuta el ciclo completo de planificación técnica desde una spec aprobada.

## Flujo

```
plan → export HTML → gate → tasks → analyze → export HTML → gate
```

## User Input

```text
{{ARGS}}
```

Extrae del input:
- **scope** (opcional, default `full`): `full` | `backend-only` | `frontend-only`. Si no viene, usa `full`.

---

## Execution Steps

### Setup

Verifica que existe `spec.md` en el feature activo. Si no, aborta:
> "No se encontró spec.md. Ejecuta primero `/speckit-workflow-refinement`."

Muestra:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PLANNING WORKFLOW
  Scope: <scope>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### [1/5] plan

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [1/5] plan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-plan <scope>`.

### [2/5] export-plan (HTML preview)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [2/5] export-plan → HTML
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-md-html-export-export plan`.
Muestra la ruta del fichero HTML generado.

### GATE: review-plan

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏸ GATE — review-plan
  Revisa el plan técnico en HTML.
  ¿El enfoque y la arquitectura son correctos?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Espera respuesta explícita:
- `approve` → continúa
- `reject` → abort: "Workflow detenido en [review-plan]. Corrige plan.md y vuelve a ejecutar desde este paso."

### [3/5] tasks

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [3/5] tasks
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-tasks`.

### [4/5] analyze

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [4/5] analyze
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-analyze`.

### [5/5] export-tasks (HTML preview)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [5/5] export-tasks → HTML
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-md-html-export-export tasks`.
Muestra la ruta del fichero HTML generado.

### GATE: review-analyze

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏸ GATE — review-analyze
  Revisa el análisis y las tareas en HTML.
  ¿Hay issues CRITICAL que resolver antes de implementar?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Espera respuesta explícita:
- `approve` → continúa
- `reject` → abort: "Workflow detenido en [review-analyze]. Resuelve los issues CRITICAL y vuelve a ejecutar desde el paso tasks."

### Fin

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ PLANNING COMPLETADO
  Plan:   specs/<feature>/plan.md
  Tasks:  specs/<feature>/tasks.md
  HTML:   specs/<feature>/plan.html
          specs/<feature>/tasks.html
  Siguiente: /speckit-workflow-implementation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Behavior rules

- Nunca saltes un gate sin confirmación explícita del usuario.
- Si el usuario escribe "stop" o "abort", detén el workflow inmediatamente.
- Si `/speckit-md-html-export-export` no está disponible, omite los pasos de export y avisa.
