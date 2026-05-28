# ADR-0005: Adopt Modelo A — teams scoped to a single client, created from the client ficha

**Status**: Accepted
**Date**: 2026-05-28
**Story**: All
**Sources**: spec.md#OQ-005, spec.md#clarifications-2026-05-28

## Context

OQ-005 was the critical open question of the spec: should a team be created per client (Modelo A) or as a standalone entity reusable across multiple clients (Modelo B)?

The decision drives the entire data model and dictates whether team management lives inside the client ficha or in a dedicated screen.

## Decision

For the MVP: **Modelo A**. Teams are created directly from the client ficha and are exclusive to one client. If the same composition is needed for another client, it is recreated from that client's ficha.

The data model uses `ClientTeam` with a NOT NULL FK to `Client`, materializing this scoping at the schema level.

## Consequences

- ✅ Matches how responsables think today ("the team of this client") — lower onboarding cost.
- ✅ Simpler authorization model: permission per client+department, no team-to-client mapping permissions.
- ✅ The MVP UI lives entirely in the client ficha (matches FR-015).
- ⚠️ Composition duplication: the same employees re-entered per client. Acceptable for MVP because composition changes are rare.
- 🔁 Future Modelo B remains possible without destructive migration — `ClientTeam` is already a first-class entity. A future pivot table `team_assignment (team_id, client_id, ...)` would be additive; the `client_id` FK on `ClientTeam` can be relaxed later without breaking existing rows.

## Alternatives Considered

- **Modelo B (reusable teams from a dedicated screen)**: more powerful but requires a new screen, new permissions, more code. Rejected for MVP; documented as future evolution.
