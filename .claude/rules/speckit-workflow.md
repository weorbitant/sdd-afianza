---
paths:
  - "specs/**"
  - ".specify/**"
---

# Speckit workflow — Afianza

## Recommended flow (nueva feature spec-driven)

```
/speckit-specify                # 1. Redactar spec desde descripción natural
/speckit-clarify                # 2. Resolver dudas obvias detectadas por el LLM
/speckit-atlassian-sync-push    # 3. Subir Stories + Open Questions a Jira (NO sube subtasks)
/speckit-ready                  # 4. Readiness gate — evalúa spec contra rubric; gate advisory hacia plan
/speckit-plan                   # 5. Plan técnico + data model + contratos API
/speckit-tasks                  # 6. Desglosar en tareas (viven en repo, NO en Jira)
/speckit-implement              # 7. Implementar tarea a tarea
```

> Los comandos `/speckit-*` usan el plan activo referenciado en la sección SPECKIT al final de `CLAUDE.md`.
> Modelo completo de refinement: ver `.specify/REFINEMENT.md`.
> Custom layer = `decisions.md` (1 por feature). Nada más.

## Comandos activos

| Command | Purpose |
|---------|---------|
| `/speckit-specify` | Crear o actualizar spec desde descripción en lenguaje natural |
| `/speckit-clarify` | Resolver dudas abiertas en la spec |
| `/speckit-ready` | Readiness gate: evalúa spec contra `.specify/quality-rubric.md` (8 criterios) y emite `readiness-report.md` con verdict y plan de acción. Read-only, advisory |
| `/speckit-analyze` | Detectar inconsistencias entre spec/plan/tasks |
| `/speckit-plan` | Generar plan técnico, data model y contratos API |
| `/speckit-tasks` | Desglosar el plan en tareas de implementación |
| `/speckit-atlassian-sync-push [epic-key]` | Subir User Stories + Open Questions a Jira (NO subtasks — las tareas viven en `tasks.md`) |
| `/speckit-decisions-extract` | Extraer decisiones estructurales a ADRs (formato Nygard) en `specs/<feature>/decisions/` |
| `/speckit-implement` | Implementar tarea a tarea con generación de código |
| `/ce-plan` | Investigación técnica paralela antes de planificar |
| `/ce-brainstorm` | Brainstorming técnico para una feature |
| `/ops-suite` | Operaciones de infra (queues, deploys, logs, DB) |
| Auto: superpowers | TDD, debugging, code review — se activa automáticamente |
| `/azure-*` | Entra, AKS, RBAC, diagnósticos, despliegues |
