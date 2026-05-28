# Research: Asignaciones Múltiples en Ficha de Cliente

**Feature**: 001-client-team-assignments | **Date**: 2026-05-25

---

## R-001 — Date Granularity for Assignment Periods (FR-012)

### Context

The `ClientAssignment` entity stores `dateFrom` / `dateTo` as PostgreSQL `date` columns. The spec left date granularity as a TODO with three options: daily, monthly, or hybrid.

### Alternatives Considered

| Option | Storage | Validation | Migration cost | Edge cases |
|---|---|---|---|---|
| **Daily** | Exact date | % sum per day | None | Complex: what if assignment changes mid-month? Two separate days with different advisors |
| **Monthly** | First-of-month convention (e.g. `2026-06-01` = "June 2026") | % sum per month | None (schema unchanged; service enforces convention) | Simpler; aligns with billing |
| **Hybrid** | Exact date stored; service enforces `dateFrom = 1st of month` for new records | % sum per month | None | Allows future migration to daily without schema change |

### Decision: **Hybrid (first-of-month convention)**

- `dateFrom` MUST be the first day of a month (enforced by service validation on create/update)
- `dateTo` MUST be the last day of a month, or `null` for open-ended assignments (enforced by service)
- Schema: no change — keep `columnType: 'date'`
- Validation: `ClientTeamsService.validateMonthBoundary(date)` helper
- Historical display: show dates as "Jun 2026 – Ago 2026" (format in frontend)

### Rationale

1. Obligations in `pd-service-obligations-api` run on a monthly cycle; monthly granularity aligns with how advisors are actually scheduled.
2. No schema migration needed — existing rows with daily dates are grandfathered; only new records enforce the convention.
3. The hybrid retains exact date storage, so pivoting to daily in future requires zero DB migration.
4. FR-003 (100% validation) is much simpler computed per month than per day.

---

## R-002 — Manual Task Reassignment: HTTP vs RabbitMQ

### Context

FR-010 requires a "manual reassignment" option where a coordinator can transfer specific tasks to another team member. Tasks live in `pd-service-obligations-api`. Constitution IV prohibits direct HTTP calls between backend services.

### Finding: ObligationsApi adapter already performs HTTP mutations

The existing `infrastructure/obligations-api/ObligationsApi` in `pgi-service-pgi-api` already calls obligations-api HTTP endpoints for mutations: `updateObligationState`, `updateTask`, `updateSubmission`. This is a pre-existing pattern (predates the constitution's 2026-05-25 ratification).

### Alternatives Considered

| Option | Pro | Con |
|---|---|---|
| **RabbitMQ event** `pgi-api.v1.task-reassignment.requested` | Constitution IV compliant | New AMQP consumer in obligations-api; async (response not immediate) |
| **HTTP via existing ObligationsApi adapter** | Consistent with existing pattern; synchronous response | Violates Constitution IV technically; documented in Complexity Tracking |

### Decision: **RabbitMQ event** (constitution-compliant)

Even though the existing `ObligationsApi` adapter makes HTTP mutations, the recommended approach for manual reassignment is a RabbitMQ event, because:

1. This is a new feature written post-constitution — it should model the correct pattern.
2. The HTTP adapter mutations are legacy technical debt (should be migrated to events in future).
3. Reassignment is not latency-critical; async processing is acceptable.
4. A new AMQP subscriber in obligations-api is minimal code.

**Event schema**: `pgi-api.v1.task-reassignment.requested`
```json
{
  "clientId": "uuid",
  "department": "FISCAL | LABORAL",
  "fromEmployeeId": "uuid",
  "toEmployeeId": "uuid",
  "taskIds": ["uuid", "uuid"]  // null = all PENDING tasks for this client+dept+fromEmployee
}
```

Routing key: `backoffice-api.v1.task-reassignment.requested`
Queue in obligations-api: `obligations-api:task-reassignment:process`

### Existing path for automatic reassignment (no change needed)

When an assignment changes (new employee for same role/dept), the existing flow already handles automatic task reassignment:
```
pgi-service publishes client_assignment_updated
  → data-factory receives → publishes client_assignment_persisted
  → obligations-api: refreshAdvisorForClient() updates PENDING tasks
```
Only PENDING tasks are updated (IN_PROGRESS, SUBMITTED, CANCELLED preserve their original advisor). This is intentional per DEVPT-472.

---

## R-003 — Soft Uniqueness: One Active Team per Client+Department

### Context

FR-005: "Un responsable NO PUEDE tener más de un equipo activo por departamento." A partial unique index (`WHERE endDate IS NULL`) would enforce this at DB level, but MikroORM 6.x requires raw SQL for partial indexes.

### Decision: **Service-layer guard + raw migration index**

In `ClientTeamsService.createTeam()`, check for an existing active team before creation. Additionally, create a partial unique index in the migration for belt-and-suspenders:

```sql
CREATE UNIQUE INDEX idx_client_team_active
  ON client_team (client_id, department)
  WHERE end_date IS NULL;
```

The service-layer guard gives a clean error message; the DB constraint prevents race conditions.

---

## R-004 — Percentage Validation: single-bucket team total

### Context

FR-003 (revised 2026-05-28): All team members (ASESOR + TECNICO combined) must sum to exactly 100% per (client, department). RESPONSABLE and COORDINADOR are management roles and do not enter the sum (implicit 100% each, max 1 per team).

### Decision: **Validate at commit time in domain service**

Validation runs only on `POST /commit` (not on add/edit/remove — those operate on the draft):

1. Fetch all **active** assignments for (client, department, team) where role IN (ASESOR, TECNICO) → sum of `percentage` must equal 100.
2. Guard: at least 1 active ASESOR must exist (FR-011) → else `MIN_ASESOR_REQUIRED`.

"Active" = no `dateTo`, or `dateTo >= today`.

Returns structured error:
```json
{
  "error": "PERCENTAGE_VALIDATION_FAILED",
  "sum": 90,
  "required": 100,
  "membersIncluded": ["ASESOR", "TECNICO"]
}
```

---

## R-005 — Frontend: Live % Sum Validation with TanStack Form

### Decision: **Field array with single derived sum**

The team management form uses `useForm` from `@tanstack/react-form` with a field array for members. A derived selector computes the **total sum of ASESOR + TECNICO percentages** (RESPONSABLE and COORDINADOR excluded). A `<PercentageSumIndicator>` component shows one live sum with color feedback (green = 100%, red = other).

Validation: Zod schema validates each `percentage` (1–100 integer) + form-level cross-field validation that the team total is 100. Submit ("Confirmar equipo") is disabled if sum ≠ 100.

---

## Summary of Resolved Decisions

| ID | Topic | Decision |
|---|---|---|
| R-001 | Date granularity (FR-012) | **Hybrid**: store exact date, enforce first-of-month convention in service |
| R-002 | Manual task reassignment | **RabbitMQ event** `pgi-api.v1.task-reassignment.requested` |
| R-003 | One active team enforcement | Service guard + partial unique index in migration |
| R-004 | % validation logic | Single-bucket: validate at commit time, sum of all members (ASESOR + TECNICO) = 100% |
| R-005 | Frontend live validation | TanStack Form field array + derived sum + Zod cross-field |
