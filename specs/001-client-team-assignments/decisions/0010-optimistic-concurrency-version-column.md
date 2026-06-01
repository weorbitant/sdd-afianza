# ADR-0010 — Optimistic concurrency: dedicated `version` column instead of `updatedAt`

**Status**: Accepted
**Date**: 2026-06-01
**Supersedes**: N/A
**Superseded by**: N/A
**Origin**: Challenge technical 2026-06-01, T5 (feasibility-F5)

## Context

FR-022 introduce optimistic concurrency en `ClientTeam` y `ClientAssignment` para resolver C2 de la sesión PO (último editor pisa silenciosamente al primero). La propuesta inicial del plan usaba `updatedAt` (timestamp con sub-second precision) comparado vía header `If-Match` para detectar conflictos.

El technical challenge (T5) detectó que:
- `updatedAt` se actualiza vía `onUpdate: () => new Date()` en MikroORM.
- Dos writes en el mismo milisegundo pueden producir el mismo `updatedAt` y bypassear el check.
- No hay rationale documentado para preferir timestamp sobre version integer monotónico.

## Decision

Usar **columna `version: integer`** dedicada para optimistic concurrency en `ClientTeam` y `ClientAssignment`, con el decorator `@Property({ version: true })` de MikroORM 6.

- Cada write incrementa `version` atómicamente.
- El header HTTP `If-Match: <version>` lleva el integer.
- Conflict detectado cuando `version` en el header ≠ `version` en BD.

`updatedAt` sigue existiendo pero ya NO se usa para concurrencia (solo audit).

## Alternatives considered

### A. `updatedAt` timestamp (descartado)

**Pro**: ya existe, sin migración adicional.
**Con**: granularidad sub-segundo no garantiza unicidad bajo concurrencia real (importante en consumers AMQP que pueden procesar mensajes en batches con timestamps colapsados).

### B. `clock_timestamp()` de PostgreSQL en lugar del de aplicación (descartado)

**Pro**: granularidad mayor (microsegundos).
**Con**: sigue siendo timestamp — colisión teóricamente posible. Y depende de extensión específica de Postgres.

### C. `version: integer` con `@Property({ version: true })` (**elegida**)

**Pro**: MikroORM maneja el increment atómico, contract simple (integer ascendente), zero ambigüedad.
**Con**: requiere columna nueva + migración. Mínimo.

## Consequences

- **Migración M1a** (ver `data-model.md`) DEBE añadir `version: smallint DEFAULT 1 NOT NULL` a ambas tablas.
- Contratos `client-teams-api.md` y `client-assignments-api.md` cambian header `If-Match: <updatedAt>` a `If-Match: <version>`.
- Frontend (`pgi-app-pgi-web`) actualiza los DTO + manejo del 409.
- Tests de integración con concurrencia real (dos transacciones simultáneas via testcontainers) verifican que el conflict se detecta correctamente.
