# ADR-0001: Use hybrid date granularity for assignment periods

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
