# ADR-0004: Validate percentages grouped by role (ASESOR / TECNICO)

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
