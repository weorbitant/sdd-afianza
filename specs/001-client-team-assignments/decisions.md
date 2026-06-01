# Decisiones técnicas (ADRs) — DEVPT-518


> Decisiones consolidadas. Formato Nygard simplificado. Cada sección era un ADR independiente; se han fusionado para reducir proliferación de ficheros.


---

## 0001-hybrid-date-granularity


**Status**: Accepted
**Date**: 2026-05-25
**Story**: All
**Sources**: research.md#R-001, spec.md#FR-012, spec.md#clarifications-2026-05-25

## Context

`ClientAssignment.dateFrom` / `dateTo` are PostgreSQL `date` columns. The spec left date granularity as a TODO with three options: daily, monthly, or hybrid. The choice affects:

- How obligations and rentability calculations run (monthly cycle in `pd-service-obligations-api`).
- Whether the schema needs a migration (text vs date).
- The complexity of the 100% percentage validation (per day vs per month).

## Decision

Store the exact date in the existing `date` columns, but **enforce in the service layer** that `dateFrom` is the first day of a month and `dateTo` is the last day of a month (when set). Percentage and rentability calculations operate at month granularity.

Helper: `ClientTeamsService.validateMonthBoundary(date, mode: 'start' | 'end')` rejects with `DATE_NOT_MONTH_BOUNDARY`.

## Consequences

- ✅ No schema migration required — existing rows with daily dates are grandfathered.
- ✅ FR-003 validation is much simpler computed per month than per day.
- ✅ Aligns with how advisors are scheduled in practice (monthly billing cycle).
- ✅ Future pivot to daily granularity requires zero DB migration — just relax service validation.
- ⚠️ Frontend must format dates as "Jun 2026 – Aug 2026" instead of the literal stored date for user-facing display.

## Alternatives Considered

- **Daily**: complex edge cases (mid-month advisor switches require two same-month rows); rejected because rentability runs monthly.
- **Monthly (column type change to varchar 'YYYY-MM')**: would require schema migration; rejected because hybrid keeps the column unchanged.


---

## 0002-rabbitmq-for-task-reassignment


**Status**: Accepted
**Date**: 2026-05-25
**Story**: US4
**Sources**: research.md#R-002, .specify/memory/constitution.md#IV

## Context

FR-010 requires a manual reassignment option where a coordinator transfers specific tasks to another team member. Tasks live in `pd-service-obligations-api`. Constitution Principle IV (Event-Driven Cross-Service Communication) prohibits direct HTTP calls between backend services.

The existing `ObligationsApi` adapter in `pgi-service-pgi-api` already performs HTTP mutations (`updateObligationState`, `updateTask`, `updateSubmission`) — a legacy pattern predating the constitution's ratification on 2026-05-25.

## Decision

New task reassignment work publishes a RabbitMQ event `backoffice-api.v1.task-reassignment.requested`. A new AMQP subscriber in `pd-service-obligations-api` consumes it and reassigns tasks asynchronously.

The legacy `ObligationsApi` HTTP adapter remains untouched in this feature (documented as technical debt in plan.md → Complexity Tracking).

## Consequences

- ✅ Constitution IV compliant — no new HTTP between backend services.
- ✅ Async processing is acceptable (reassignment is not latency-critical).
- ✅ Models the correct pattern for new code, even though legacy HTTP exists.
- ⚠️ Slightly more code than direct HTTP (new subscriber in obligations-api).
- ⚠️ Response is async (202 Accepted) — frontend must surface progress separately.

## Alternatives Considered

- **HTTP via existing ObligationsApi adapter**: consistent with current legacy pattern and synchronous, but violates Constitution IV. Rejected: new features should not entrench legacy debt.
- **Mixed approach (HTTP for some operations, AMQP for others)**: increases cognitive load. Rejected: uniformity wins.


---

## 0004-percentage-validation-grouped-by-role


**Status**: Superseded by [ADR-0008](0008-single-bucket-percentage-validation.md)
**Date**: 2026-05-25
**Story**: US1
**Sources**: research.md#R-004 (original)

## Context

FR-003 originally required that asesores sum to 100% and técnicos sum to 100% independently, both per (client, department, team).

## Decision

`ClientAssignmentsService` validated before any flush:

1. Sum active ASESOR percentages → must equal 100.
2. Sum active TECNICO percentages → if any técnico exists, must equal 100.
3. Guard: at least 1 active ASESOR after removals (FR-011).

Validation ran synchronously before `em.persistAndFlush()`.

## Consequences

- ⚠️ Treated asesores and técnicos as independent load pools.
- ⚠️ Frontend needed two `PercentageSumIndicator` instances, one per role group.

## Alternatives Considered

- **Single bucket (all members sum to 100%)**: not the original interpretation; adopted later — see [ADR-0008](0008-single-bucket-percentage-validation.md).

## Superseded by

[ADR-0008](0008-single-bucket-percentage-validation.md) — Clarification on 2026-05-28 reframed the team as one unit splitting 100% of the work across all operative members. Two-bucket model is no longer the source of truth.


---

## 0005-team-scoped-to-client-modelo-a


**Status**: Accepted
**Date**: 2026-05-28
**Story**: All
**Sources**: spec.md#OQ-005, spec.md#clarifications-2026-05-28

## Context

OQ-005 was the critical open question of the spec: should a team be created per client (Modelo A) or as a standalone entity reusable across multiple clients (Modelo B)?

The decision drives the entire data model and dictates whether team management lives inside the client ficha or in a dedicated screen.

## Decision

For the MVP: **Modelo A**. Teams are created directly from the client ficha and are exclusive to one client. If the same composition is needed for another client, it is recreated from that client's ficha.

The data model uses `ClientTeam` with a NOT NULL FK to `Client`, materializing this scoping at the schema level.

## Consequences

- ✅ Matches how responsables think today ("the team of this client") — lower onboarding cost.
- ✅ Simpler authorization model: permission per client+department, no team-to-client mapping permissions.
- ✅ The MVP UI lives entirely in the client ficha (matches FR-015).
- ⚠️ Composition duplication: the same employees re-entered per client. Acceptable for MVP because composition changes are rare.
- 🔁 Future Modelo B remains possible without destructive migration — `ClientTeam` is already a first-class entity. A future pivot table `team_assignment (team_id, client_id, ...)` would be additive; the `client_id` FK on `ClientTeam` can be relaxed later without breaking existing rows.

## Alternatives Considered

- **Modelo B (reusable teams from a dedicated screen)**: more powerful but requires a new screen, new permissions, more code. Rejected for MVP; documented as future evolution.


---

## 0006-responsable-as-clientassignment-row


**Status**: Accepted
**Date**: 2026-05-28
**Story**: US1
**Sources**: spec.md#clarifications-2026-05-28

## Context

`ClientAssignmentRole` enum already includes `responsable`, `coordinador`, `asesor`, `tecnico`. Acceptance scenarios (US1) name the responsable as the actor but don't make explicit how the role is materialized in the data model: as a `ClientAssignment` row, or implicitly as `ClientTeam.createdBy`?

## Decision

The responsable is materialized as a `ClientAssignment` row with `role = responsable`. The team has at most one such row. The responsable's percentage is implicit 100% and does not enter the team's percentage sum (see [ADR-0008](0008-single-bucket-percentage-validation.md)).

`ClientTeam.createdBy` is preserved as the audit trail for who created the team initially, but it is not the canonical source for "current responsable".

## Consequences

- ✅ Uniform handling: every member of the team is a row, queryable with one shape.
- ✅ Historical audit: changes of responsable produce new rows (existing audit of `ClientAssignment` works).
- ✅ Permissions for responsable can be derived from the same join used for other roles.
- ⚠️ Adding/changing the responsable must enforce "max 1 responsable per team" — handled in service guard (`ROLE_ALREADY_FILLED`).
- ⚠️ The responsable row carries `percentage = 100` but is excluded from the sum validation — a small special case in the validation logic.

## Alternatives Considered

- **`createdBy` field only**: simpler but loses historical visibility of responsable changes and requires a different code path for "is X the responsable?" queries.
- **Hybrid (createdBy + optional ClientAssignment row)**: too flexible; opens the door to "responsable in two places" inconsistency.


---

## 0009-legacy-data-migration-in-us1


**Status**: Accepted
**Date**: 2026-05-28
**Story**: US1
**Sources**: spec.md#FR-013, spec.md#clarifications-2026-05-28

## Context

Existing `client_assignment` rows on production are 1-to-1 (one asesor per client+department). After deploying this feature, those legacy rows have `team_id = NULL` because they predate the `ClientTeam` table.

We need to decide how the new UI treats legacy data: hide it until the responsable creates an explicit team? Show it as a virtual team? Auto-migrate at first ficha open? Or do a bulk migration on deploy?

The legacy data is **valid by construction** for the new single-bucket rule: a single asesor with default `percentage = 100` already sums to 100%.

## Decision

The migration `Migration20260528122459` includes a bulk data block that runs at deploy time:

1. For every `(client_id, department)` with active assignments (`date_to IS NULL`), create one `ClientTeam` row with `start_date = MIN(date_from)`, `end_date = NULL`, `created_by = 'system-migration'`.
2. Back-fill `client_assignment.team_id` on those active assignments.

The block is idempotent (re-running produces the same state) and non-destructive (historical closed rows are not touched).

## Consequences

- ✅ Zero manual work post-deploy: every responsable sees their team active when they open any client ficha.
- ✅ Single migration, single transaction, predictable rollout.
- ✅ `created_by = 'system-migration'` makes the audit trail distinguishable from human-created teams.
- ⚠️ The migration must run before any user opens a ficha — handled by standard `migrations:apply` step in the release pipeline.
- ⚠️ Historical closed assignments (`date_to IS NOT NULL`) remain with `team_id = NULL`. They are immutable by spec and shouldn't be retro-assigned to teams that didn't exist when they were active.

## Alternatives Considered

- **Lazy at first ficha open**: backend creates the implicit team on the first GET. Rejected — adds a side effect to a read endpoint, makes the migration state non-deterministic across clients.
- **Hide legacy rows until manual team creation**: confusing UX (active assignments invisible in the new UI), and risks responsables thinking they need to re-input what's already in BD.
- **Defer to a separate post-deploy script**: extra moving piece in the release process; the SQL fits perfectly in the same migration.


---

## 0010-optimistic-concurrency-version-column


**Status**: Accepted
**Date**: 2026-06-01
**Supersedes**: N/A
**Superseded by**: N/A
**Origin**: Revisión técnica 2026-06-01, T5 (feasibility-F5)

## Context

FR-022 introduce optimistic concurrency en `ClientTeam` y `ClientAssignment` para resolver C2 de la sesión PO (último editor pisa silenciosamente al primero). La propuesta inicial del plan usaba `updatedAt` (timestamp con sub-second precision) comparado vía header `If-Match` para detectar conflictos.

La revisión técnica (T5) detectó que:
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


---

## 0011-cross-service-team-id-logical-fk


**Status**: Accepted
**Date**: 2026-06-01
**Supersedes**: N/A
**Superseded by**: N/A
**Origin**: Revisión técnica 2026-06-01, T7 (feasibility-F7)

## Context

La feature DEVPT-518 introduce `ClientTeam` en `pgi-service-pgi-api`. El modelo `ClientAssignment` en `pd-service-data-factory` necesita reflejar el `team_id` para que los informes de rentabilidad puedan agregar por equipo (FR-014 + FR-018, FR-019).

Decisión a documentar: cómo se modela ese `team_id` en data-factory cuando la fuente de verdad (`ClientTeam`) vive en pgi-api, otro servicio.

Constitution IV (event-driven cross-service) prohíbe HTTP calls directos entre servicios. Cualquier consistencia entre tablas cross-service depende del AMQP pipeline.

## Decision

`pd-service-data-factory/client_assignment.team_id` es una **columna `uuid NULL`** sin foreign key constraint. Es un **correlation id lógico** — útil para join en queries de informes pero NO valida integridad referencial entre BDs.

Política de huérfanos:
- Si un evento llega con un `teamId` que data-factory no conoce (porque el team fue creado en pgi-api pero el evento de creación de team aún no llegó / no se emite): **persistir el valor tal cual** y emitir log warn `unknown team_id for client_assignment {id}: {teamId}`.
- Si un team se cierra/elimina en pgi-api y data-factory tiene asignaciones con ese `team_id`: **mantener el valor** — el histórico es válido y los informes que agregan por team siguen funcionando con teams cerrados.
- **NO** se crea entidad `ClientTeam` en data-factory. Si en el futuro hace falta, se añade vía nueva migración + nuevo evento `client-team.updated`.

## Alternatives considered

### A. FK real cross-service (descartado por imposible)

Postgres no soporta FK entre bases de datos. Habría que mover ambos modelos a la misma BD — fuera de scope (rompe boundaries de servicio).

### B. No tener `team_id` en data-factory, derivar via jira-adapter (descartado)

**Pro**: cero acoplamiento entre data-factory y conceptos de equipo.
**Con**: informes de rentabilidad NO pueden agregar por equipo sin pedir a otro servicio. Eficiencia y simplicidad de queries cae.

### C. `team_id` como logical FK + log warn en huérfanos (**elegida**)

**Pro**: informes pueden agregar por team sin coordinación cross-service. Cero coste de validación referencial. Huérfanos observables pero no rompen ingest.
**Con**: posibilidad de drift silencioso si pgi-api borra teams sin notificar (mitigado: pgi-api no borra teams, solo cierra con endDate — los teams cerrados no son huérfanos, son históricos válidos).

## Consequences

- **Migración M2** mantiene `team_id uuid NULL` sin FK constraint.
- `pd-service-data-factory/client-assignment.subscriber` añade log warn cuando recibe payload con teamId no conocido localmente (puede ocurrir en rolling deploy si data-factory está más atrasado).
- Si en una iteración futura se necesita validar integridad, se introduce evento `client-team.created/closed` aparte y data-factory mantiene una proyección local de `ClientTeam`. Por ahora, YAGNI (Constitution V).
- No hay migración para "limpiar" huérfanos — los huérfanos son inputs válidos del sistema.
