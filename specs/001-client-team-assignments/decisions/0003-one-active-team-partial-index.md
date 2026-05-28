# ADR-0003: Enforce one active team per client+department via service guard + partial unique index

**Status**: Accepted
**Date**: 2026-05-25
**Story**: US1
**Sources**: research.md#R-003, spec.md#FR-005

## Context

FR-005 mandates that a client cannot have more than one active team per department (unicity over `client_id + department WHERE end_date IS NULL`). MikroORM 6 does not generate partial unique indexes natively — it requires raw SQL in the migration.

We need to choose between enforcing at the service layer, the DB layer, or both.

## Decision

Belt-and-suspenders: enforce at **both** layers.

1. **Service guard** in `ClientTeamsService.createTeam()` checks for an existing active team and throws `ACTIVE_TEAM_EXISTS` with a clean error message before attempting the insert.
2. **Partial unique index** `idx_client_team_active ON client_team (client_id, department) WHERE end_date IS NULL` enforces the constraint at the DB layer to prevent race conditions.

## Consequences

- ✅ Race-condition safety: even under concurrent requests, the DB rejects the second insert.
- ✅ Clean error UX: the service guard catches the common case and returns a human-readable error before hitting the DB.
- ⚠️ The migration includes raw SQL for the partial index (`addSql` with `CREATE UNIQUE INDEX ... WHERE`), which MikroORM doesn't auto-generate.

## Alternatives Considered

- **Service guard only**: simpler but loses race-condition safety under concurrent traffic.
- **DB constraint only**: race-safe but produces an opaque `unique violation` error that requires translation at the application layer. Worse UX.
