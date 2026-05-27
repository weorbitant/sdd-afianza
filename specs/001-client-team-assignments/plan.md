# Implementation Plan: Asignaciones Múltiples en Ficha de Cliente

**Branch**: `001-client-team-assignments` | **Date**: 2026-05-25 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-client-team-assignments/spec.md`

---

## Summary

Extend the existing flat `ClientAssignment` model with team grouping (`ClientTeam`), percentage-based load tracking, 100% sum validation per role group per department, historical period tracking, team lifecycle (create → close), and manual task reassignment via RabbitMQ. Changes span `pgi-service-pgi-api` (new entity + domain service), `pgi-app-pgi-web` (new team management UI in client ficha), and `pd-service-obligations-api` (new AMQP subscriber for manual reassignment).

**Date granularity decision (FR-012)**: Hybrid — store exact dates (PostgreSQL `date`), enforce first-of-month for `dateFrom` and last-of-month for `dateTo` via service validation. No schema change vs today.

---

## Technical Context

**Language/Version**: TypeScript 5.7.3

**Primary Dependencies**:
- Backend: NestJS 10, MikroORM 6.4.3 (PostgreSQL), `@afianza-ac/lib-core-definitions@0.0.124`, `@afianza-ac/nest-module-rabbitmq@1.3.5`
- Frontend: React 19, TanStack React Query v5, TanStack React Form v1.1, Zod v4.1, shadcn/ui (Radix UI), React Router v7.2

**Storage**: PostgreSQL (MikroORM, `postgres:17-alpine` in dev/test)

**Testing**: Jest + `@testcontainers/postgresql` (backend); Vitest + `@testing-library/react` (frontend)

**Target Platform**: Linux server (NestJS API) + Web SPA (React + Vite)

**Project Type**: Web service + Web application (polyrepo — changes across 3 services)

**Performance Goals**: < 200ms p95 on team read/write endpoints (consistent with existing assignment endpoints)

**Constraints**:
- Strict 3-layer architecture (application → domain → infrastructure) — no exceptions
- No NestJS feature modules — all providers in AppModule
- `em.fork()` before all writes; `disableIdentityMap: true` for reads
- Cross-service communication via RabbitMQ only (one exception justified below)
- `lib-core-definitions` changes require publishing a new npm version — avoid unless necessary

**Scale/Scope**: 2 departments × ~hundreds of clients × up to 10 members per team. No high-throughput requirement; assignment operations are infrequent (HR-cadence).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-design.*

| Principle | Status | Notes |
|---|---|---|
| I. Strict 3-Layer Architecture | ✅ PASS | `ClientTeam` entity in domain; `ClientTeamsService` in domain/services; `ClientTeamsController` in application/rest; no layer skipping |
| II. Real-Container Testing | ✅ PASS | New service tests use `@testcontainers/postgresql` with real postgres:17-alpine |
| III. MikroORM Unit of Work | ✅ PASS | All writes use `em.fork()`; reads use `disableIdentityMap: true`; partial unique index added via migration |
| IV. Event-Driven Cross-Service | ✅ PASS | Manual task reassignment uses new RabbitMQ event `backoffice-api.v1.task-reassignment.requested`; no new HTTP calls |
| V. Simplicity / YAGNI | ✅ PASS | Extends existing `ClientAssignment` entity (2 new columns); new `ClientTeam` entity is minimal; no new abstractions |

**No constitution violations.**

---

## Project Structure

### Documentation (this feature)

```text
specs/001-client-team-assignments/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output — FR-012 resolved, task reassignment approach decided
├── data-model.md        # Phase 1 output — entity definitions, validation rules, migration SQL
├── quickstart.md        # Phase 1 output — smoke tests, run instructions
└── contracts/
    ├── client-teams.md              # New team management REST endpoints
    └── client-assignments-history.md # Extended assignment endpoints + RabbitMQ events
```

### Source Code

```text
# pgi-service-pgi-api (backend)
asesores/pgi-service-pgi-api/src/
├── domain/
│   ├── models/
│   │   ├── client-team.ts              [NEW] ClientTeam entity
│   │   └── client-assignment.ts        [EDIT] + percentage, + team FK
│   └── services/
│       ├── client-teams/
│       │   └── client-teams.service.ts [NEW] createTeam, closeTeam, getTeams, validateTeam
│       └── client-assignments/
│           └── client-assignments.service.ts [EDIT] + validatePercentageSum, + addMember, + removeMember, + reassignTasks event
├── application/
│   └── rest/
│       ├── client-teams/               [NEW]
│       │   ├── client-teams.controller.ts
│       │   └── dto/
│       │       ├── create-team-params.dto.ts
│       │       ├── close-team-params.dto.ts
│       │       ├── add-member-params.dto.ts
│       │       ├── patch-percentage-params.dto.ts
│       │       ├── reassign-tasks-params.dto.ts
│       │       └── client-team.dto.ts
│       └── client-assignments/         [EDIT] extend response DTO with percentage + teamId
│           └── dto/
│               └── client-assignment-dto.ts [EDIT]
└── migrations/
    └── MigrationXXXX.ts                [NEW] ClientTeam table + percentage column

# pgi-app-pgi-web (frontend)
asesores/pgi-app-pgi-web/src/
└── features/
    ├── client-teams/                   [NEW feature module]
    │   ├── domain/
    │   │   ├── models/client-team.model.ts
    │   │   └── repositories/client-teams.repository.ts
    │   ├── application/use-cases/
    │   │   ├── get-client-teams.use-case.ts
    │   │   ├── create-team.use-case.ts
    │   │   ├── close-team.use-case.ts
    │   │   ├── add-member.use-case.ts
    │   │   ├── update-member-percentage.use-case.ts
    │   │   ├── remove-member.use-case.ts
    │   │   ├── reassign-tasks.use-case.ts
    │   │   └── composition-root.ts
    │   ├── infrastructure/
    │   │   ├── client-teams.repository-impl.ts
    │   │   └── dto/client-team.dto.ts
    │   └── presentation/
    │       └── components/
    │           ├── team-section/            # Main team UI for client ficha tab
    │           │   ├── team-section.tsx
    │           │   ├── team-header.tsx
    │           │   ├── team-member-row.tsx
    │           │   └── percentage-sum-indicator.tsx
    │           ├── team-form/               # Add/edit member form
    │           │   └── team-member-form.tsx
    │           ├── close-team-dialog/
    │           │   └── close-team-dialog.tsx
    │           ├── team-history/
    │           │   └── team-history-accordion.tsx
    │           └── task-reassignment-dialog/
    │               └── task-reassignment-dialog.tsx
    └── client-assignments/                 [EDIT]
        ├── domain/models/client-assignment.model.ts  [EDIT] + percentage, + teamId
        └── infrastructure/dto/client-assignment-dto.ts [EDIT] + percentage, + teamId

# pd-service-obligations-api (backend)
plataforma-del-dato/pd-service-obligations-api/src/
├── application/
│   └── amqp/
│       └── task-reassignment-subscriber/   [NEW]
│           └── task-reassignment.subscriber.ts
└── domain/
    └── services/
        └── tasks/
            └── tasks.service.ts            [EDIT] + reassignTasksBetweenAdvisors()
```

---

## Complexity Tracking

> No constitution violations requiring justification.

---

## Post-Design Constitution Re-check

All 5 principles pass. The design:
- Keeps domain logic in domain services (% validation, date boundary checks, one-active-team guard)
- Uses real containers for all integration tests
- Follows MikroORM UoW patterns throughout
- Uses RabbitMQ for the new cross-service task reassignment operation
- Adds minimal new code — 1 new entity, 2 new columns, 1 new feature module in frontend
