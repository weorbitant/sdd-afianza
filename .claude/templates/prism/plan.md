# Plan — [FEATURE NAME]

**Feature**: `specs/[###-feature-name]/`
**Date**: [DATE]
**Spec**: [link]
**ADRs**: [ADR-001, ADR-002 — list key decisions made]
**Phase**: `DESIGN`

---

## Summary

[1 paragraph. Core requirement + chosen technical approach. Reference ADRs for non-trivial decisions.]

---

## Technical context

| Item | Value |
|------|-------|
| Language / Runtime | [e.g., Node 22 + NestJS 10] |
| Primary dependencies | [list] |
| Storage | [PostgreSQL / Redis / none] |
| Testing | [Jest / Vitest / ...] |
| Target services | [pgi-api, pd-service-data-factory, ...] |
| Performance target | [e.g., < 200ms p95 for list endpoint] |
| Constraints | [from NFR in spec] |

---

## Architecture decisions (ADR references)

| Decision | ADR | Status |
|----------|-----|--------|
| [e.g., Temporal model for assignments] | ADR-001 | accepted |
| [e.g., Optimistic locking strategy] | ADR-002 | accepted |

---

## Risk assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| [e.g., N+1 query with large teams] | medium | high | PoC planned → `poc.md` |
| [Risk 2] | low | medium | [strategy] |

**PoC required?**: `yes / no`
If yes → `specs/[###]/poc.md` must be `go` before starting Phase 6 (TASKS).

---

## Data model

<!-- High-level only. Full schema in data-model.md. -->

```
[entity diagram or table list]
```

Key invariants:
- [Invariant 1 — e.g., "Exactly one is_main per (client, department) at any point in time"]
- [Invariant 2]

---

## AMQP contracts

<!-- Full schema in contracts/amqp/. Summary here. -->

**Publishes**:
- `[routing-key]` → [when triggered, payload summary]

**Consumes**:
- `[routing-key]` from [service] → [what this service does with it]

---

## REST contracts

<!-- Full OpenAPI in contracts/rest/. Summary here. -->

| Method | Path | Service | Notes |
|--------|------|---------|-------|
| POST | `/[resource]` | [service] | [notes] |

---

## Source structure

```text
specs/[###-feature-name]/
├── spec.md
├── plan.md              ← this file
├── discovery.md
├── adrs/
│   ├── ADR-001-[title].md
│   └── ADR-002-[title].md
├── poc.md               (if PoC required)
├── data-model.md
├── contracts/
│   ├── rest/
│   └── amqp/
└── tasks.md

[service]/src/
├── domain/
├── application/
│   ├── rest/
│   └── amqp/
└── infrastructure/
```

---

## Security & compliance (technical)

### PII & encryption
- **Tables/columns storing PII**: [schema.table.column — N/A if none]
- **Encryption at rest**: [yes/no — mechanism]
- **Logs**: [confirm PII is NOT logged, or document what is redacted]

### Auth
- **Guard on new endpoints**: [e.g., `AzureAdJwtGuard`]
- **Scopes/claims required**: [list]
- **RBAC roles touched**: [list]

### RabbitMQ
- **New publications**:
  - Routing key: `[service].v1.[entity].[event]`
  - Idempotence on consumer side: [strategy]
- **PII in payload**: [yes/no — justify if yes]

---

## Tech debt created

<!-- Be honest. Every plan creates some debt. -->

| Debt item | Reason accepted | Tracking |
|-----------|----------------|---------|
| [e.g., Legacy table not migrated] | [PO decision — cost of migration] | [ADR-NNN / OQ-NNN] |

---

## Migration notes

<!-- How we transition from current state to new state without breaking prod. -->

- **Schema changes**: [safe to run while service is live? rollback plan?]
- **Data migration**: [required / not required]
- **Feature flag**: [yes/no — key name if yes]
- **Deployment order**: [service A before B? why?]
