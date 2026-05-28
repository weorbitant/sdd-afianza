# ADR-0002: Use RabbitMQ event for manual task reassignment

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
