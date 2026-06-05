# Decisiones técnicas (ADRs) — DEVPT-518


> Decisiones consolidadas. Formato Nygard simplificado. Cada sección era un ADR independiente; se han fusionado para reducir proliferación de ficheros.

---

## ⚠️ Aviso v2 (2026-06-04)

La spec se reescribió en v2 (`spec.md`). Varios ADRs heredados quedan **Superseded** por las nuevas decisiones (resumen en `er-diagram.md` → tabla "Estado de los ADRs heredados"). Los ADRs siguen aquí como histórico — su `**Status**` ha sido actualizado donde corresponde. **No usar el body de ADRs `Superseded` como guía técnica actual** — leer la spec v2 y este aviso primero.

Cambios principales en v2 que afectan a múltiples ADRs:

- Fechas normalizadas a primer/último día del mes en API normal; onboarding (subscriber AMQP) conserva fechas tal cual.
- Schema simplificado: `ClientTeam` sin `start_date`/`end_date`, `ClientTeamAssignment` sin denormalizados, `is_main` reemplaza a `is_primary_advisor`.
- Eliminado `causes_baja` + `successorId` — la reasignación de tareas a obligations se infiere automáticamente del flujo close+open vía AMQP.
- Sin migración explícita de `client_assignment` legacy — coexistencia, los responsables vuelven a meter equipos cuando abran la ficha.
- Sin partial unique `(client, employee)` — múltiples roles activos por persona permitidos (FR-013 v2).

---

## 0001-hybrid-date-granularity


**Status**: Accepted — refinado en spec v2 (2026-06-04). La granularidad "híbrida" sigue siendo el modelo, pero ahora se materializa así: API normal **normaliza automáticamente** a primer/último día del mes (rechaza meses pasados); el subscriber AMQP de onboarding conserva fechas tal cual. Ver `spec.md` v2 FR-002, FR-003, FR-004.
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

- **Single bucket (all members sum to 100%) (→ “cobertura única” en terminología actual)**: not the original interpretation; adopted later — see [ADR-0008](0008-single-bucket-percentage-validation.md).

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


**Status**: **Superseded** by spec v2 (2026-06-04). No hay migración explícita en v2: la tabla `client_assignment` queda congelada y los equipos se vuelven a meter desde la UI nueva al abrir la ficha por primera vez (o vía evento de onboarding AMQP). Body conservado como histórico de las opciones evaluadas.
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

## 0007-draft-commit-team-validation

**Status**: Superseded by [ADR-0013](#0013-immediate-persistence-per-member)
**Date**: 2026-05-28
**Story**: US1
**Sources**: spec.md#clarifications-2026-05-28

## Context

La spec original (sesión 2026-05-28) definía un modelo borrador+commit: `POST/PATCH/DELETE /members` no validaban suma, y un endpoint explícito `POST /commit` cerraba la composición, validaba el 100% y publicaba el evento AMQP.

## Decision

Endpoint `POST /commit` valida `getDepartmentCoverageStatus`, marca el team activo y publica `pgi-api.v1.client-assignment.updated` (un evento por miembro). `POST /validate` informativo para el frontend.

## Superseded by

[ADR-0013](#0013-immediate-persistence-per-member) — La sesión 2026-05-29 invalidó el modelo borrador. La persistencia es inmediata por miembro; no hay endpoint `/commit`.


---

## 0008-single-bucket-percentage-validation

**Status**: Superseded by [ADR-0012](#0012-two-bucket-per-department-validation)
**Date**: 2026-05-28
**Story**: US1
**Sources**: spec.md#clarifications-2026-05-28

## Context

Tras descartar ADR-0004 (dos coberturas por rol), se reframeó el team como una unidad: todos los miembros operativos (asesores + técnicos) sumando 100% conjunto. Responsable y coordinador 100% implícito, fuera de la suma.

## Decision

`ClientAssignmentsService.validatePercentageSum(clientId, department, teamId)` sumaba `ASESOR + TECNICO` activos del team y exigía `=== 100`.

## Superseded by

[ADR-0012](#0012-two-bucket-per-department-validation) — La PO confirmó el 2026-06-01 (frame `08-multi-equipo/01-multi-equipo-fiscal-larsa-costa.png`) que la suma es: (a) por **departamento del cliente** (no por team individual) y (b) **dos coberturas independientes** (asesores 100% + técnicos 100% por separado).


---

## 0012-two-bucket-per-department-validation

**Status**: Accepted
**Date**: 2026-06-01
**Supersedes**: [ADR-0008](#0008-single-bucket-percentage-validation)
**Origin**: Sesión PO 2026-06-01 (post-meeting), confirmada con frame `08-multi-equipo/01-multi-equipo-fiscal-larsa-costa.png`

## Context

Modelo de validación de FR-003. ADR-0008 (single cobertura por team) no encaja con el caso real mostrado en los diseños: 2 equipos Fiscal del mismo cliente con 4 asesores distribuidos al 25% cada uno = 100% en conjunto del departamento.

## Decision

La validación del 100% es:

1. **Por departamento del cliente** — agregando entre TODOS los teams activos del mismo `(client_id, department)`.
2. **Dos coberturas independientes**:
   - Cobertura asesores: suma `%` de asignaciones `role=asesor` activas del departamento = 100%.
   - Cobertura técnicos: suma `%` de asignaciones `role=tecnico` activas del departamento = 100% (o "no aplicable" si no hay ningún técnico).
3. Responsable y coordinador NO entran en la suma (100% implícito).
4. Validación advisory tras cada `POST/PATCH/DELETE /members` — NO bloquea persistencia (banner amarillo). Solo bloquea: (i) composición mínima (1 responsable + 1+ asesor) y (ii) transición `incomplete → active`.

Estado derivado expuesto vía `GET /clients/:clientId/department/:dept/coverage-status`.

## Consequences

- ✅ Refleja la realidad operativa multi-equipo (varios equipos del mismo departamento son válidos).
- ✅ Frontend muestra dos barras independientes (asesores / técnicos) por departamento, no por team.
- ⚠️ Query de validación agrega cross-team — ver [ADR-0017](#0017-coverage-validation-locking-and-transactionality) para evitar race conditions.


---

## 0013-immediate-persistence-per-member

**Status**: Accepted
**Date**: 2026-05-29
**Supersedes**: [ADR-0007](#0007-draft-commit-team-validation)
**Origin**: Sesión PO 2026-05-29 (design conformance, frames `05-vista-equipo-incompleto/*`)

## Context

ADR-0007 definía modelo borrador+commit. Los diseños 2026-05-29 muestran toast inmediato tras cada add/edit/delete de miembro y banner advisory cuando el cobertura no llega al 100% — sin botón "Confirmar equipo".

## Decision

Cada `POST/PATCH/DELETE /members` persiste al instante. El team tiene estado derivado `incomplete` | `active` | `closed`:

- `active` ⇔ (asesores=100 + técnicos∈{100, n/a} + hasPrimaryAdvisor + composición mínima cumplida).
- `incomplete` mientras alguna condición falle (no bloquea persistencia de miembros).
- AMQP publish (FR-014) **suprimido** mientras `incomplete`. Se emite al entrar en `active` y en cada cambio dentro de `active`.

Endpoints `/validate` y `/commit` eliminados.

## Consequences

- ✅ UX coherente con diseños (sin doble click, sin estado oculto).
- ✅ Reduce superficie de API.
- ⚠️ Plataforma del Dato no ve estados intermedios — gracia consistente con FR-014.
- ⚠️ Tasks T017/T018/T035 stale — referencian `commitTeam`/borrador y deben reescribirse.


---

## 0014-amqp-cross-service-rollout

**Status**: **Partially superseded** by spec v2 (2026-06-04). Sigue vigente la idea de payload ampliado con `teamId`, `percentage` e `isMain`, pero **`causesBaja` desaparece del payload** (la reasignación de tareas se infiere de fechas). Las CHECK constraints que listaba se reducen a `is_main = false OR role = 'asesor'` (las otras dependían de `causes_baja` o columnas eliminadas). Body conservado como histórico.
**Date**: 2026-06-01
**Origin**: Research R2 + R3 + R5 + T1 del plan.md

## Context

DEVPT-518 amplía el evento AMQP `pgi-api.v1.client-assignment.updated` con `teamId`, `percentage`, `isPrimaryAdvisor`, `causesBaja`. Consumers afectados: `pd-service-data-factory` (informes) y `pd-service-jira-adapter` (sync Jira Assets).

Además, la ruta de entrada `client_onboarding_persisted` consumida por `pgi-service-pgi-api/client-subscriber` crea filas en `client_assignment` automáticamente (verificado en código, en producción desde mayo 2026).

## Decision

### Payload AMQP — aditivo, backward-compatible

Campos nuevos como **opcionales** en JSON (no bump de routing key, no `v2`):

```typescript
{
  // existentes
  clientId, employeeId, role, department, dateFrom, dateTo, updatedAt, updatedBy,
  // nuevos (opcionales hasta consumers alineados)
  teamId?: string;
  percentage?: number;          // 1..100
  isPrimaryAdvisor?: boolean;
  causesBaja?: boolean;
}
```

Consumers viejos ignoran campos extra (Postel's law).

### Orden de deploy

1. `pd-service-data-factory` — añade columnas + subscriber tolerante.
2. `pd-service-jira-adapter` — añade filtro `isPrimaryAdvisor=true` (fallback legacy: trata fila única como principal).
3. `pgi-service-pgi-api` — publisher empieza a emitir el payload completo.

### Onboarding bridge (D10 parcial)

`applyFromClientOnboarding(...)` mantiene compat creando filas con `team_id = NULL` y `percentage = 100`. PERO debe **cerrar la fila activa existente** del par `(clientId, employeeId)` con `dateTo = endOfPreviousMonth` ANTES del upsert — el partial unique de FR-021 (ver M1b) bloquea doble asignación activa de la misma persona en el mismo cliente.

Pseudo-código del fix:

```typescript
async applyFromClientOnboarding(onboarding) {
  await this.em.transactional(async txEm => {
    for (const service of onboarding.services) {
      for (const { role, employeeId } of service.roles) {
        const existing = await txEm.findOne(ClientAssignment, {
          client: onboarding.clientId,
          employee: employeeId,
          dateTo: null,
        }, { disableIdentityMap: true });

        if (existing) {
          existing.dateTo = endOfPreviousMonth(now);
          existing.updatedBy = 'system:onboarding';
          await txEm.persistAndFlush(existing);
        }

        await txEm.upsert(ClientAssignment, {
          client: onboarding.clientId,
          employee: employeeId,
          role,
          department: mapServiceToDepartment(service),
          dateFrom: firstOfCurrentMonth(now),
          percentage: 100,
          teamId: null,                  // D10 pendiente PO
          updatedBy: 'system:onboarding',
        });
      }
    }
  });
}
```

Test de regresión obligatorio: `apply-from-client-onboarding.regression.spec.ts`, caso "empleado ya activo en otro rol del mismo cliente".

## Consequences

- ✅ Zero downtime durante el rolling deploy.
- ✅ Onboarding sigue funcionando con la nueva BD; los responsables verán filas huérfanas (sin team) hasta agruparlas — documentado en quickstart.
- ⚠️ D10 sigue parcial — PO puede decidir más adelante crear "Equipo inicial" automático; sería un cambio aditivo en este mismo método.


---

## 0015-coverage-validation-locking-and-transactionality

**Status**: Accepted
**Date**: 2026-06-01
**Origin**: Research R4 + T4 + T8 del plan.md

## Context

[ADR-0012](#0012-two-bucket-per-department-validation) agrega `percentage` cross-team del mismo `(client_id, department)`. Sin locking, dos `POST /members` concurrentes pueden ambos leer suma=80, ambos insertar +20 y dejar la BD en suma=120 sin que ninguno haya visto el conflicto. Lo mismo aplica a la transición `incomplete → active` que dispara AMQP publish: dos transacciones simultáneas pueden ambas calcular "ahora estamos active" y emitir doble evento.

Adicionalmente, `POST /teams/:id/close` muta el team + N asignaciones; un fallo a mitad deja el team parcialmente cerrado.

## Decision

### Coverage-status computation

El cálculo de `getDepartmentCoverageStatus(clientId, department)` dentro de una transacción que puede disparar transición debe adquirir `SELECT ... FOR UPDATE` sobre la fila padre `client` antes de leer las asignaciones. Esto serializa concurrent `POST/PATCH/DELETE /members` sobre el mismo cliente+departamento y garantiza "exactamente un evento por transición".

### Close team

`POST /teams/:id/close` ejecuta la mutación completa (team.endDate + N assignments.dateTo) dentro de un único `em.transactional(async txEm => { ... })`. AMQP publish va **post-commit** (en el `.then()` del transactional). Si el commit falla, no se emite ningún evento.

## Consequences

- ✅ Imposible perder eventos por race ni emitir duplicados por transición.
- ✅ Cierre de team atómico.
- ⚠️ Lock sobre `client` puede serializar editores concurrentes del mismo cliente — aceptable (latencia <200ms, baja contención esperada).
- ⏳ Pendiente outbox pattern (D-005) para garantizar at-least-once delivery sin ack manual del publisher. Por ahora, post-commit publish es suficiente para MVP.

## Alternatives Considered

- **Cálculo en memoria post-flush**: no detecta race entre transacciones, descartado.
- **Trigger BD**: violaría Constitution V (la lógica vive en el servicio).


---

## 0016-migration-split-and-db-invariants

**Status**: **Superseded** by spec v2 (2026-06-04). No hay secuencia M1a/M1b/M2 en v2: no se modifica `client_assignment` (queda congelada) y la tabla nueva `client_team_assignment` se crea en una sola migración limpia. Los CHECK constraints heredados se reducen a `is_main = false OR role = 'asesor'` (sin `chk_causes_baja_only_when_closed`). Body conservado como histórico de aprendizaje sobre migration sequencing.
**Date**: 2026-06-01
**Origin**: Revisión técnica T2 + T6 + T10 del plan.md

## Context

La migración inicial (M1) añadía columnas + partial uniques en una sola pasada. T10 detectó que si los datos legacy violan FR-021 (un mismo empleado con dos asignaciones activas en el mismo cliente entre departamentos distintos), el CREATE INDEX falla a mitad y deja la BD en estado parcial.

T2 detectó que sin CHECK constraints, un bug en el servicio puede marcar `isPrimaryAdvisor=true` en un coordinador o setear `causesBaja=true` en una fila activa silenciosamente.

T6 detectó que sin garantía "al menos un primary team activo por (cliente, departamento)", `jira-adapter` no tiene team que sincronizar.

## Decision

### Split en dos migraciones

- **M1a** (DDL + backfill + audit):
  - `ADD COLUMN client_assignment.is_primary_advisor`, `causes_baja`.
  - `ADD COLUMN client_team.is_primary`.
  - CHECK `chk_primary_advisor_only_asesor`: `is_primary_advisor = false OR role = 'asesor'`.
  - CHECK `chk_causes_baja_only_when_closed`: `causes_baja = false OR date_to IS NOT NULL`.
  - Backfill idempotente: promueve asesor más antiguo a primary por `(client, dept)` si no hay ninguno; idem teams.
  - Audit query: si existe `(client_id, employee_id)` con >1 fila activa, `RAISE EXCEPTION` — bloquea M1b hasta limpieza manual con PO.
- **M1b** (partial uniques DESPUÉS del backfill):
  - `(client_id, employee_id) WHERE date_to IS NULL` (FR-021).
  - `(client_id, department) WHERE is_primary_advisor = true AND date_to IS NULL`.
  - `(client_id, department) WHERE is_primary = true AND end_date IS NULL`.

### Auto-promote primer team

Al crear el primer `ClientTeam` para un `(clientId, department)`, el servicio marca `isPrimary = true` automáticamente. Subsequent teams default `false`. El responsable puede demote/promote después vía PATCH.

### Migration M2 (data-factory) — preventiva

M2 añade `team_id`, `percentage`, **y también `is_primary_advisor` + `causes_baja`** aunque US4 implemente esos campos después. Coste cero hoy (defaults), evita una segunda migración cross-service.

## Consequences

- ✅ Si los datos legacy son inconsistentes, M1a aborta limpio antes de tocar índices.
- ✅ CHECK constraints garantizan invariantes incluso si el servicio falla.
- ✅ Jira-adapter siempre tiene un team principal que sincronizar.
- ⚠️ Dos migraciones en lugar de una — más artefactos pero más seguro.


---

## 0017-successor-required-on-causes-baja-close

**Status**: **Superseded** by spec v2 (2026-06-04). El flujo de baja con sucesor explícito desaparece: cualquier reemplazo (close + open en la misma fecha normalizada) dispara eventos AMQP que `pd-service-obligations-api` consume para reasignar tareas automáticamente según el asesor vigente en la `dueDate` de cada tarea. Sin flag `causesBaja`, sin endpoint dedicado, sin `successorId` en el body. Body conservado como histórico del razonamiento previo.
**Date**: 2026-06-01
**Origin**: Revisión técnica T3 del plan.md

## Context

FR-010 dice "si un asesor causa baja, sus tareas abiertas se reasignan automáticamente al asesor sucesor definido para ese cliente en el siguiente período". El plan inicial inferiría el sucesor silenciosamente buscando el asesor con `dateFrom > current.dateTo` más antiguo.

T3 detectó que la inferencia silenciosa puede asignar tareas a alguien equivocado si el período siguiente no se ha definido aún o si hay varios candidatos.

## Decision

`DELETE /members/:id` con `causesBaja=true` requiere `successorId` en el body. Si se omite:

- HTTP 400 `SUCCESSOR_REQUIRED`.
- Respuesta incluye `suggestedSuccessorId` calculado por temporalidad (asesor activo más antiguo con `dateFrom > current.dateTo` en el mismo `(client, department)`, o `null` si no hay candidato).
- Frontend pre-rellena el diálogo con la sugerencia; el responsable confirma o cambia.

## Consequences

- ✅ Decisión de sucesor explícita, auditable.
- ✅ Frontend puede ayudar sin obligar.
- ⚠️ Si no hay candidato (no se ha definido período siguiente), responsable debe designar uno fuera del flujo o crear primero el siguiente miembro.


---

## 0018-frontend-state-tanstack-query

**Status**: Accepted
**Date**: 2026-06-01
**Origin**: Research R6 del plan.md

## Context

`pgi-app-pgi-web` usa TanStack Query como convención. La composición del team con validación reactiva del cobertura podría tentar a introducir Zustand para borrador + commit. ADR-0013 elimina el borrador.

## Decision

- **TanStack Query** para queries (`/teams`, `/members`, `/coverage-status`) y mutations (`POST/PATCH/DELETE /members`).
- `optimisticUpdate` para el slider de porcentaje (UX fluida).
- Cobertura se calcula client-side a partir del query cache para barras advisory en vivo; validación dura es server-side.
- **Sin Zustand** — la composición del equipo es estado de servidor cacheado.

## Consequences

- ✅ Convención del repo respetada (Constitution V).
- ✅ Sin store cliente para estado inherentemente servidor.


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


---

## OPEN-001-change-log-shape

**Status**: Accepted (cerrada 2026-06-04, antes Open desde 2026-06-03)
**Date**: 2026-06-04
**Story**: US-05 (Log de cambios sobre el equipo). US-07 fusionada en US-05.
**Sources**: er-diagram.md (tabla `ClientTeamAssignmentChange`), data-model.md §1.3, spec.md OQ-003.

## Context

El ER inicial definía `ClientTeamAssignmentChange` con `before jsonb` / `after jsonb` + `event_type` enum + `actor` string libre, diferido a US2/US3. Durante la sesión de refinamiento del 2026-06-04 (al promover esta tabla a US-05) se cerraron todos los puntos abiertos.

## Decisión

1. **`before/after` como columnas explícitas**, una por campo (`employee_id_before`/`_after`, `role_before`/`_after`, `percentage_before`/`_after`, `is_main_before`/`_after`, `date_from_before`/`_after`, `date_to_before`/`_after`). Sin `jsonb`. Razón: la UI consulta cambio a cambio y los devs prefieren tipado fuerte; los huecos NULL según `action` son aceptables.

2. **`action` enum** con valores: `opened` | `closed` | `percentage_changed` | `role_changed` | `main_changed` | `voided`. El valor `voided` cubre FR-007 v2 (machacado de tramos del mes en curso — `date_to = date_from - 1 día`).

3. **Sin denormalización de `client_id` / `department`**. Se acceden vía JOIN con `client_team_assignment` → `client_team`. Razón: consistencia con la decisión de la propia `client_team_assignment` (FR-013 v2 minimal constraints) y evitar drift.

4. **Audit propio**: `created_at`, `updated_at`, `created_by`, `updated_by`. El "quién" del cambio vive **exclusivamente** aquí — `client_team_assignment` ya no tiene `created_by`/`updated_by` (decisión simétrica para single-source-of-truth). `updated_at`/`updated_by` quedan NULL salvo corrección posterior del registro (patrón estándar de audit legal).

5. **Producer**: cada operación de US-01/02/03/04 que muta `client_team_assignment` inserta filas en `client_team_assignment_change` dentro de la **misma transacción**. Atomicidad obligatoria.

6. **API**: `GET /api/v1/clients/{clientId}/team-assignment-changes?department=...&from=...&to=...` (read-only). Sin endpoints de mutación.

7. **US-07 eliminada**: la auditoría completa que estaba prevista como historia diferida queda absorbida por US-05; no son dos vistas distintas.

## Puntos que se rechazaron explícitamente

- `correlation_id` / `request_id` para agrupar cambios de una misma request → la UI puede agrupar visualmente por `created_at` cercano. Mantenemos shape mínimo.
- `actor_type` enum + `actor_id` separados → `created_by` como string libre con convención (`email` o `system:onboarding`) es suficiente para filtrar.
- Separar `occurred_at` / `recorded_at` → para esta feature siempre coinciden (la inserción en `change` es síncrona con la mutación). Si en el futuro entran eventos AMQP retrasados, se reabre.


---

## NOTE-001-amqp-versioning-when-payload-changes

**Status**: **Resolved** by spec v2 (2026-06-04). El payload no se amplía sobre el routing key legacy: se introduce un routing key **completamente nuevo** `pgi-api.v1.client-team-assignment.opened` / `.closed` para una entidad distinta (`client-team-assignment`). El legacy `pgi-api.v1.client-assignment.updated` queda en pgi-api hasta que se desactive (la tabla `client_assignment` queda congelada — no genera nuevos eventos). Sin estrategia de versioning v1+v2 en paralelo, sin breaking change sobre la key vieja.
**Date**: 2026-06-03

Cuando US2 amplíe el payload de `pgi-api.v1.client-assignment.updated` con `teamId`, `percentage` e `isPrimaryAdvisor` (FR-018), decidir estrategia de versioning:

- ¿Bumpear a `pgi-api.v2.client-assignment.updated` y publicar v1+v2 en paralelo durante transición?
- ¿O cambiar nombre de entidad a `client-team-assignment` (como sugiere `er-diagram.md` nota 5)?

Inconsistencia a corregir cuando se aborde: `er-diagram.md` nota 5 dice "nuevo routing key `pgi-api.v1.client-team-assignment.updated`" — si es breaking change debería ser **v2**, no v1 con otro nombre.

US1 NO toca payloads — esta nota solo deja constancia para no improvisar cuando llegue el momento.

