# ADR-0008: Validate percentage as a single-bucket team total (asesor + técnico = 100%)

**Status**: Accepted
**Date**: 2026-05-28
**Story**: US1
**Sources**: spec.md#clarifications-2026-05-28, spec.md#FR-003
**Supersedes**: [ADR-0004](0004-percentage-validation-grouped-by-role.md)

## Context

Initial interpretation of FR-003 (see [ADR-0004](0004-percentage-validation-grouped-by-role.md)) had asesores summing to 100% and técnicos summing to 100% independently — a two-bucket model. The PO clarified that conceptually the team is **one** unit of work load distributed across all operative members.

Example the PO described: 1 asesor 60% + 1 asesor 20% + 1 técnico 20% = 100% — a valid configuration that the two-bucket model would reject (asesores at 80, técnicos at 20).

## Decision

Validate the **sum of all members with role ASESOR or TECNICO** as a single bucket against 100%. Responsable and coordinador are management roles and **do not enter the sum** (they carry an implicit 100% with no constraint).

The validation runs only on `POST /commit` (see [ADR-0007](0007-draft-commit-team-model.md)).

## Consequences

- ✅ Matches the PO's mental model: "the team handles 100% of work, split across operative members".
- ✅ Simpler API surface: one validation, one error code, one frontend indicator.
- ✅ More flexible team compositions (e.g. a junior técnico can absorb 10% while two senior asesores cover 80% + 10%).
- ⚠️ Acceptance scenarios (US1 AC-2, US2 ACs) needed rewriting to match the new rule.
- ⚠️ If in the future business wants to differentiate workload accounting per role (e.g. asesor hours vs técnico hours), this decision would need to be revisited.

## Alternatives Considered

- **Two-bucket model**: asesores 100% + técnicos 100% independently. Rejected — doesn't match how the business reasons about team load.

## Supersedes

- [ADR-0004](0004-percentage-validation-grouped-by-role.md) — original two-bucket model.
