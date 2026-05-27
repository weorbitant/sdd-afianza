---
name: speckit-workflow-implementation
description: "Implementación: implement → revisión → PR. Deploy y QA gestionados por ops-suite."
argument-hint: "[base-branch]  e.g. /speckit-workflow-implementation main"
compatibility: Requires spec-kit project structure with .specify/ directory and an active feature with tasks.md
metadata:
  author: afianza-local
  source: workflows/implementation/workflow.yml
user-invocable: true
---

# Feature Implementation Workflow

Ejecuta la implementación desde las tareas aprobadas hasta la Pull Request.

## Flujo

```
implement → gate → create-pr
```

## User Input

```text
{{ARGS}}
```

Extrae del input:
- **base_branch** (opcional, default `main`): rama base para el PR.

---

## Execution Steps

### Setup

Verifica que existen `spec.md`, `plan.md` y `tasks.md` en el feature activo. Si falta alguno, aborta:
> "Faltan artefactos. Ejecuta primero `/speckit-workflow-refinement` y `/speckit-workflow-planning`."

Muestra:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  IMPLEMENTATION WORKFLOW
  Base branch: <base_branch>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### [1/2] implement

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [1/2] implement
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-implement`.

### GATE: review-implementation

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏸ GATE — review-implementation
  Revisa el código generado.
  ¿Todo listo para abrir el PR?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Espera respuesta explícita:
- `approve` → continúa
- `reject` → abort: "Workflow detenido en [review-implementation]. Corrige el código y vuelve a ejecutar desde este paso."

### [2/2] create-pr

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  [2/2] create-pr
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Invoca `/speckit-git-pr-create <base_branch>`.

### Fin

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ IMPLEMENTATION COMPLETADO
  PR: <pr-url>
  Siguiente: ops-suite deploy → QA → prod
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Behavior rules

- Nunca saltes el gate sin confirmación explícita del usuario.
- Si el usuario escribe "stop" o "abort", detén el workflow inmediatamente.
- Si estás en rama `main`, avisa antes de continuar: "⚠️ Estás en main. Crea una rama feature antes de implementar."
