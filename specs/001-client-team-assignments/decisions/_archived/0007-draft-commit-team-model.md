# ADR-0007: Use draft + explicit commit model for team management

**Status**: Accepted
**Date**: 2026-05-28
**Story**: US1
**Sources**: spec.md#clarifications-2026-05-28, contracts/client-teams.md

## Context

When constructing a team incrementally (add 1st asesor at 60%, add 2nd asesor at 40%), validating "sum = 100%" on every `POST /members` is impossible: between adding the 1st and the 2nd, the team is transiently invalid by definition. We need a strategy that allows the team to exist in an invalid state during construction and only enforce the rule at the right moment.

## Decision

Two-phase model:

1. **Draft phase**: `POST /members`, `PATCH /members/:id`, `DELETE /members/:id` operate freely without validating the 100% sum. They only validate per-row constraints (range 1–100, role uniqueness for responsable/coordinador, date boundary).
2. **Commit phase**: `POST /v1/client-teams/:clientId/:teamId/commit` runs the full validation (sum = 100, ≥ 1 asesor) and:
   - On success: marks the team as confirmed and publishes one `backoffice-api.v1.client-assignment.updated` event per active member.
   - On failure: returns `400 PERCENTAGE_VALIDATION_FAILED` or `MIN_ASESOR_REQUIRED` and leaves the team in draft.

`POST /validate` exists as a read-only helper for the frontend's live indicator.

## Consequences

- ✅ Natural UX: responsable can construct a team in any order without intermediate errors.
- ✅ Single source of "the team is now official" → events are only emitted on commit, downstream consumers (Plataforma del Dato) see consistent state.
- ✅ Validation rules concentrated in one method (`ClientTeamsService.commitTeam`); fewer places to maintain.
- ⚠️ A team can exist in BD in an invalid state ("orphan draft") if the responsable abandons construction. Acceptable: drafts are scoped per client+department and are visible only to editors.
- ⚠️ Frontend must distinguish "Save draft" (PATCH member) from "Confirm team" (POST commit) explicitly.

## Alternatives Considered

- **Validate on every add/edit/remove**: simpler API but impossible to build a multi-member team incrementally; would require sending all members in a single request.
- **POST /validate as advisory + auto-commit on last update**: implicit transitions are surprising; explicit commit is clearer.
