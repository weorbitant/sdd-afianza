# ADR-0009: Run legacy data migration as part of US1 deployment

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
