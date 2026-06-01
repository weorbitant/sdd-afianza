# AMQP Event Contract — `client-assignment.updated`

**Exchange**: `internal` (topic) on vhost `data_platform`
**Routing key**: `pgi-api.v1.client-assignment.updated`
**Publisher**: `pgi-service-pgi-api`
**Consumers**: `pd-service-data-factory`, `pd-service-jira-adapter`

## Payload schema

```typescript
interface ClientAssignmentUpdatedPayload {
  // Identification
  clientId: string;       // UUID
  employeeId: string;     // UUID
  role: 'responsable' | 'coordinador' | 'asesor' | 'tecnico';
  department: 'fiscal' | 'laboral';

  // Temporal
  dateFrom: string;       // ISO date YYYY-MM-DD (always first day of month)
  dateTo: string | null;  // ISO date YYYY-MM-DD (last day of month) or null if active

  // Audit
  updatedAt: string;      // ISO timestamp
  updatedBy: string;      // email or `system:onboarding`

  // NEW (introduced by DEVPT-518, optional during transition)
  teamId?: string;             // UUID — null/missing for legacy onboarding rows
  percentage?: number;         // 1..100; missing implies 100 (legacy default)
  isPrimaryAdvisor?: boolean;  // only meaningful when role=asesor
  causesBaja?: boolean;        // only meaningful when dateTo is set
}
```

## Publication triggers

The publisher emits this event when:
- A new `ClientAssignment` is created (active row).
- An existing active `ClientAssignment` changes `percentage` or `isPrimaryAdvisor`.
- An active `ClientAssignment` is closed (`dateTo` set, optionally with `causesBaja`).
- A team is closed (cascades — one event per active member of that team).

The publisher does **NOT** emit when the team or assignment is in `incomplete` department status. The event is suppressed and the data is held until the department reaches `active` state (FR-014 — Plataforma del Dato sólo recibe estados completos).

## Consumer behavior

### `pd-service-data-factory`

Subscriber updates its local `client_assignment` row (which already has `team_id` and `percentage` columns after migration M2). Used for downstream report aggregation.

- Handles missing `teamId`/`percentage` gracefully (preserves legacy behavior).
- Idempotent: same payload twice produces same DB state (uses business key).

### `pd-service-jira-adapter`

Subscriber filters to `isPrimaryAdvisor=true` (or to the only active row if `isPrimaryAdvisor` is missing — legacy compat) before mirroring to Jira Assets ("Clientes" object type). Non-primary rows are stored locally but not pushed to Jira.

- Handles missing fields: treats the row as the single primary if no flag exists.
- Honors the existing local-snapshot short-circuit (no Jira write if attribute already matches).

## Backward compatibility

During the rolling deploy (R3 of `research.md`):

1. `pd-service-data-factory` deployed first with extended subscriber. Tolerates events without new fields.
2. `pd-service-jira-adapter` deployed next, also tolerant.
3. `pgi-service-pgi-api` deployed last with extended publisher. Begins emitting full payload.

If a consumer sees a payload without the new fields, behavior is identical to pre-DEVPT-518 (legacy 1:1 semantics).

## Related events (not modified)

- `client_onboarding_persisted` — consumed by `pgi-service-pgi-api/client-subscriber`. NOT touched by this feature (FR-017 / D10 pending). May trigger this event indirectly via `applyFromClientOnboarding`.

## Testing

- **Producer side**: integration test in pgi-api that verifies `publish` is called with the full payload on each trigger above. Uses Jest mock of `RabbitMQService.publish`.
- **Consumer side (data-factory)**: integration test with testcontainers + AMQP mock subscriber that asserts new columns get populated.
- **Consumer side (jira-adapter)**: unit test that verifies the filter to `isPrimaryAdvisor=true` only mirrors one row per (client, dept, role).
- **Backward compat**: contract test that consumers process a legacy payload (without new fields) without errors.
