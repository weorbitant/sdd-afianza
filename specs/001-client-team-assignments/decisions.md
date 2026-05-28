# Decisions: 001-client-team-assignments

**Feature**: [spec.md](./spec.md)
**Epic**: DEVPT-518

Single living log of technical decisions for this feature. Tag each entry with the story it belongs to (or `All` if cross-cutting).

---

## Key Decisions

| # | Date | Story | Decision | Alternatives Considered | Reason |
|---|------|-------|----------|------------------------|--------|
| D-001 | 2026-05-28 | DEVPT-519 | Draft + explicit `POST /commit` endpoint validates the 100% sum | (a) Per-member PATCH validation; (b) DB trigger | Allows UI to build team incrementally; commit is the single source of truth |
| D-002 | 2026-05-28 | DEVPT-519 | `responsable` materialized as `ClientAssignment` with `role: responsable`, percentage implicit 100%, excluded from sum | (a) `ClientTeam.responsable_id` column; (b) Separate `team_responsables` table | Uniform table for all roles, single audit trail |
| D-003 | 2026-05-28 | DEVPT-519 | FR-013 legacy migration as a MikroORM migration on deploy, transactional + idempotent | (a) Standalone CLI script; (b) Background job post-deploy | Small dataset (<10k rows), atomic deployment artifact |
| D-004 | 2026-05-28 | All | Unicity per FR-005 via partial unique index `(client_id, department_id) WHERE end_date IS NULL` | (a) Application-level check; (b) Trigger | DB-level enforcement is the only race-safe option |
| D-005 | 2026-05-28 | All | *[PENDING]* RabbitMQ publish failure strategy after DB commit | (a) Sync retry with backoff; (b) Outbox pattern + relay; (c) Accept eventual inconsistency | To be resolved after 1-day spike — affects all events from `pgi-service-pgi-api` |

---

## Assumptions

| # | Scope | Assumption | Status |
|---|-------|------------|--------|
| A-T-001 | technical | PostgreSQL 17 supports partial unique indexes with `WHERE` | ✓ verified |
| A-T-002 | technical | MikroORM 6.x supports transactional migrations with rollback on error | ✓ verified |
| A-T-003 | technical | `clients` and `departments` tables are stable; no FK changes needed | ✓ verified |
| A-P-001 | product | One responsable will not edit the same client team from two browser sessions simultaneously | unverified — justifies optimistic locking |
| A-P-002 | product | Active assignments per client+department bounded ≤10 in practice | unverified — UI does not paginate |

---

## Decision Changes

| # | Date | Previous (ref) | New | Reason |
|---|------|----------------|-----|--------|
| *(none yet)* | | | | |

---

## Notes

- IDs are stable. Cite from commits and PRs as `see decisions.md D-001`.
- Story-scoped decisions tag the Jira key (e.g., `DEVPT-519`); cross-cutting decisions tag `All`.
- Pending decisions are blockers for the affected stories' implementation.
