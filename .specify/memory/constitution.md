<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.0 → 1.0.1
Modified principles: n/a
Added sections: n/a
Removed sections: n/a
Fixes:
  - Development Workflow: corrected specs directory from `.specify/specs/` to `specs/` (project root)
Templates reviewed:
  ✅ .specify/templates/plan-template.md — uses `specs/[###-feature]/` (correct, already aligned)
  ✅ .specify/templates/spec-template.md — Mandatory sections consistent with project constraints
  ✅ .specify/templates/tasks-template.md — Phasing and parallel execution model matches layered arch
Deferred TODOs: none
-->

# Afianza Constitution

## Core Principles

### I. Strict 3-Layer Architecture (NON-NEGOTIABLE)

Every backend service MUST follow the `application → domain → infrastructure` call flow.

- `application/` — Controllers, AMQP subscribers, DTOs. MUST contain zero business logic.
- `domain/` — Business logic, MikroORM entities, domain services. MUST NOT import infrastructure directly.
- `infrastructure/` — External API clients and adapters. MUST only be called from domain.
- DTOs MUST NOT cross into the domain layer; map at the application boundary.
- There are no NestJS feature modules — all providers are registered in `AppModule` (monolithic by design).
- Skipping a layer or calling infrastructure from application is a **blocking violation** in any code review.

**Rationale**: Enforces testability, replaceability of infrastructure, and prevents logic leakage into controllers
or raw API calls inside business code.

### II. Real-Container Testing (NON-NEGOTIABLE)

The EntityManager MUST never be mocked. Integration tests MUST use `@testcontainers/postgresql` with a real
`postgres:17-alpine` container.

- Services that do not use EntityManager: standard Jest mocks are acceptable.
- Controller tests: Supertest + mock domain services; validate DTO validation and 400 error cases.
- First test run per session takes ~10 s for container startup — this is expected and acceptable.
- Unit tests for pure domain logic (no DB) are welcome but do not replace integration tests.

**Rationale**: Mocking the ORM hides real behavior (identity map, transactions, constraint violations).
Real containers catch bugs that mock-based tests systematically miss.

### III. MikroORM Unit of Work Discipline

MikroORM's Identity Map MUST be used correctly to avoid stale-reference accumulation in long-lived
processes (AMQP consumers, cron jobs).

- **Reads**: `findOne(..., { disableIdentityMap: true })` — no fork required.
- **Writes**: `const em = this.em.fork()` MUST precede any `upsert / create / assign / flush`.
- **Multi-write transactions**: `em.fork()` followed by `em.transactional(async txEm => { ... })`.
- `@EnsureRequestContext()` MUST NOT be used in AMQP or cron contexts — it silently reuses the global EM.
- `em.upsert()` for concurrent/AMQP contexts; `em.create()` only inside serialized transactions.
- Migrations: MUST run `npx mikro-orm migration:check` before editing any entity. After creating a
  migration, `npx mikro-orm migration:create --dump` MUST return "No changes required". Applied
  migrations MUST NEVER be modified.

**Rationale**: Violating these patterns causes silent data corruption and hard-to-reproduce bugs under
concurrent load.

### IV. Event-Driven Cross-Service Communication

Inter-service communication MUST use RabbitMQ via the `internal` topic exchange on vhost `data_platform`.

- Routing key pattern: `<service>.v1.<entity>.<event>` (e.g., `backoffice-api.v1.employee.updated`).
- Queue naming: `<service>:<event>:process`.
- Domain services publish via `this.rabbitMQService.publish('publicationName', data)`.
- AMQP subscribers live in `src/application/amqp/` and MUST NOT contain business logic.
- Direct HTTP calls between backend services are prohibited — use events.
- Shared contracts (types, event schemas) MUST live in `@afianza-ac/lib-core-definitions`.

**Rationale**: Loose coupling between services prevents cascading failures and allows independent
deployment and scaling.

### V. Simplicity and Intentional Complexity

Code MUST be as simple as the problem requires. Complexity MUST be justified.

- YAGNI: do not build abstractions for hypothetical future needs.
- Every new abstraction layer (repository pattern, decorator, factory, etc.) requires explicit
  justification in the PR description.
- Prefer direct, readable code over clever indirection.
- Feature branches MUST be named `feat/<name>` or `fix/<name>`. Direct commits to `main` are prohibited.
- Commits MUST follow Conventional Commits: `<type>(<scope>): <description>` (lowercase subject).
- One commit per logical concern; squash review fixes into originals before merging.

**Rationale**: The polyrepo has ~10 services. Unnecessary abstraction multiplies across all of them,
compounding maintenance cost.

## Technology Standards

**Language**: TypeScript (all services). Code, variables, and comments MUST be in English.

**Backend framework**: NestJS (all API services). No NestJS feature modules — monolithic AppModule.

**ORM**: MikroORM with PostgreSQL (`postgres:17-alpine` in dev/test). See Principle III for patterns.

**Frontend**: React 19 + Vite (`pgi-app-pgi-web`). TypeScript required.

**Messaging**: RabbitMQ — `@afianza-ac/nest-module-rabbitmq` abstraction. See Principle IV.

**Auth**: Azure AD / Entra External ID via `@afianza-ac/nest-module-auth` (or v2 for CIAM flows).

**Package manager**: npm (all services use `package-lock.json`). pnpm/yarn MUST NOT be introduced.

**Security**: OWASP Top 10 compliance. Input validation via class-validator DTOs at application layer.

## Development Workflow

**Branches**: `feat/<name>`, `fix/<name>`, `docs/<name>`, `chore/<name>`. Never commit to `main`.

**Pre-commit gate**: `npm run lint` MUST pass.

**Pre-push gate**: `npm run build && npm test` MUST pass.

**PRs**: Titles, descriptions, and all written artifacts in English. Use `gh` CLI for all GitHub operations.

**Service-level CLAUDE.md**: Always read the service-level `CLAUDE.md` before working in any service.
`pd-service-data-factory` stores it at `.claude/CLAUDE.md` (non-standard path).

**Cross-service features**: Specs and plans live at the workspace root under `specs/`. Each involved
service gets its own tasks in the same plan, clearly scoped to its directory.

**Specs directory layout for multi-service features**:

```text
specs/[###-feature-name]/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── contracts/
└── tasks.md   (organized by service, then by user story)
```

## Governance

This constitution supersedes any conflicting guidance in README files or oral conventions.

- Amendments require: a description of what changed, the reason, and a migration plan if existing code
  is affected.
- `CONSTITUTION_VERSION` follows semantic versioning: MAJOR for removed/redefined principles, MINOR for
  new principles or sections, PATCH for clarifications and wording fixes.
- All PRs touching cross-cutting concerns (auth, RabbitMQ patterns, MikroORM, migrations) MUST pass a
  Constitution Check before merging.
- Complexity violations (Principle V) MUST be documented in the plan's Complexity Tracking table.
- This file is the authoritative reference for the `## Constitution Check` gate in `plan-template.md`.

**Version**: 1.0.1 | **Ratified**: 2026-05-25 | **Last Amended**: 2026-05-26
