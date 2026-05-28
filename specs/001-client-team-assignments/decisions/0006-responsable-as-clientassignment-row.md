# ADR-0006: Represent the responsable as a ClientAssignment row with role=responsable

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
