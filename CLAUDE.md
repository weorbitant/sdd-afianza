# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workspace Overview

This is a **polyrepo** — independent services that form the Afianza data platform. Each has its own `package.json`, git history, and service-level `CLAUDE.md` with detailed guidance.

```
# Shared / Auth
af-nest-module-auth/          # Shared NestJS library: Azure AD JWT auth (passport + JWKS)
af-nest-module-auth-v2/       # Next-gen auth module: Entra External ID / CIAM (WIP)
af-service-auth-idp/          # IDP Adapter: Authorization Code Flow + JWT interno (NestJS)

# Portal del Cliente (pc-)
pc-app-portalcliente-web/     # Client portal SPA
pc-service-portalcliente-api/ # Client portal API (NestJS + PostgreSQL)

# Portal del Asesor / Backoffice (pgi-)
pgi-app-pgi-web/              # Internal backoffice SPA (React 19 + Vite)
pgi-service-pgi-api/          # Client & employee management API (NestJS + PostgreSQL)

# Plataforma del Dato (pd-)
pd-service-obligations-api/   # Fiscal obligations management (NestJS + PostgreSQL)
pd-service-azuread-adapter/   # Azure AD / Microsoft Graph integration (NestJS)
pd-service-data-factory/      # Data aggregation hub: Sage, AEAT, Jira, Azure AD, HubSpot (NestJS)
pd-service-jira-adapter/      # Jira integration adapter (NestJS)
```

Each service has its own `CLAUDE.md` — always read it before working in that service.
- `pd-service-data-factory` stores its CLAUDE.md at `.claude/CLAUDE.md` (non-standard — read it explicitly).
- `af-nest-module-auth/`, `af-nest-module-auth-v2/` and `pd-service-azuread-adapter/` have no service-level CLAUDE.md — rely on workspace root guidance.

## Common Commands (all backend services)

Run from inside the service directory:

```bash
npm run infra:up                    # Start PostgreSQL + RabbitMQ via Docker
npm run start:dev                   # Dev server with watch
npm run build                       # Compile (nest build)
npm test                            # Jest
npx jest --testPathPattern=<path>   # Single test file
npm run lint:fix                    # ESLint with auto-fix
npm run format                      # Prettier
npm run migrations:create           # New MikroORM migration
npm run migrations:up               # Apply migrations
```

Frontend (`pgi-app-pgi-web`):

```bash
npm run dev          # Vite dev server
npm run build        # TypeScript check + Vite build
npx vitest run src/path/to/file.test.tsx  # Single test file
```

**Package manager**: All services use **npm** (`package-lock.json`).

## Architecture — Backend Services

All NestJS services follow the same **strict 3-layer architecture** with no NestJS modules (monolithic by design, all providers in `AppModule`):

```
application/     # Controllers + AMQP subscribers + DTOs. No business logic.
domain/          # Business logic, MikroORM entities, domain services.
infrastructure/  # External API clients. Never called directly from application.
config/          # Per-environment configs (default, local, development, production, test).
migrations/      # MikroORM auto-generated migrations + snapshot JSON.
```

**Call flow**: `application → domain → infrastructure` — never skip layers, never call infrastructure from application, never let DTOs cross into domain.

## Cross-Service Communication (RabbitMQ)

- **vhost**: `data_platform`
- **Exchange**: `internal` (topic-based)
- **Routing key pattern**: `<service>.v1.<entity>.<event>` (e.g., `backoffice-api.v1.employee.updated`)
- **Queue naming**: `<service>:<event>:process`
- Domain services publish via `this.rabbitMQService.publish('publicationName', data)`.
- AMQP subscribers live in `src/application/amqp/`.

## Shared Internal Libraries (`@afianza-ac/`)

| Package | Purpose |
|---------|---------|
| `lib-core-definitions` | Shared domain types/contracts across services |
| `nest-module-auth` | Azure AD JWT middleware (passport + JWKS) |
| `nest-module-config` | Per-environment config loader |
| `nest-module-logger` | Structured logging |
| `nest-module-rabbitmq` | RabbitMQ abstraction (`brokerConfig()` helper) |
| `ui` | Afianza design system component library |

## MikroORM EntityManager Patterns (critical — applies to all services)

MikroORM uses **Unit of Work + Identity Map**. Long-lived processes (AMQP consumers) accumulate references if the EM is never cleared.

- **Reads**: `findOne(..., { disableIdentityMap: true })` — no fork needed.
- **Writes**: `const em = this.em.fork()` before any `upsert/create/assign/flush`.
- **Multi-write transactions**: `em.fork()` + `em.transactional(async txEm => { ... })`.
- **Never use `@EnsureRequestContext()`** in AMQP/cron contexts — it silently reuses the global EM.
- **`em.upsert()`** for concurrent contexts (AMQP); **`em.create()`** only inside serialized transactions.

## Migrations — Critical Rules

- After creating a migration, always verify: `npx mikro-orm migration:create --dump` must return "No changes required".
- **Never modify already-applied migrations** — checksum mismatches break tracking.
- When touching entities, run `npx mikro-orm migration:check` **before** editing any entity to confirm the snapshot on `main` is in sync.

## Testing

- **Never mock EntityManager** — use `@testcontainers/postgresql` with a real `postgres:17-alpine` container.
- Services without EntityManager: standard Jest mocks.
- Controller tests: Supertest + mock domain services, test DTO validation + 400 error cases.
- Integration tests: first run per session takes ~10s for container startup.

## Git & Commit Conventions

- **Never commit to `main`** — always create a feature branch (`feat/<name>`, `fix/<name>`, etc.).
- **Conventional Commits** enforced by commitlint + Husky: `<type>(<scope>): <description>` (lowercase subject).
- Pre-commit: `npm run lint`. Pre-push: `npm run build && npm test`.
- One commit per logical concern. Squash review fixes into originals before merging.
- **GitHub CLI**: use `gh` for all GitHub operations (PRs, issues, branches).
- PR titles, descriptions, and all written artifacts in **English**.

## Claude Setup — Afianza

### Recommended workflow

**Nueva feature (spec-driven)**:
```
/speckit-specify              # 1. Redactar spec desde descripción natural
/speckit-clarify              # 2. Resolver dudas abiertas (NEEDS CLARIFICATION)
/speckit-plan                 # 3. Generar plan técnico + data model + contratos API
/speckit-tasks                # 4. Desglosar en tareas de implementación
/speckit-atlassian-sync-push  # 5. Subir stories + tareas a Jira (opcional)
/speckit-implement            # 6. Implementar tarea a tarea (genera código)
```

> Los comandos `/speckit-*` usan el plan activo referenciado en la sección SPECKIT al final de este fichero.

### Active plugins in this project
| Command | Purpose |
|---------|---------|
| `/speckit-specify` | Crear o actualizar spec desde descripción en lenguaje natural |
| `/speckit-clarify` | Resolver dudas abiertas en la spec |
| `/speckit-plan` | Generar plan técnico, data model y contratos API |
| `/speckit-tasks` | Desglosar el plan en tareas de implementación |
| `/speckit-atlassian-sync-push [epic-key]` | Subir User Stories + tareas a Jira como Stories y Sub-tasks |
| `/speckit-implement` | Implementar tarea a tarea con generación de código |
| `/ce-plan` | Investigación técnica paralela antes de planificar |
| `/ce-brainstorm` | Brainstorming técnico para una feature |
| `/ops-suite` | Operaciones de infra (queues, deploys, logs, DB) |
| Auto: superpowers | TDD, debugging, code review — se activa automáticamente |
| `/azure-*` | Entra, AKS, RBAC, diagnósticos, despliegues |

### Active MCPs in this project
| MCP | Purpose |
|-----|---------|
| Notion (afianza workspace) | Project docs and notes |
| Atlassian | Jira — tickets, issues, status changes |
| Pencil | App and screen design (.pen files) |

### Token optimization
RTK is active — all Bash commands are automatically proxied through `rtk` to reduce token usage. No action needed.

### Sub-namespaces
- `plataforma-del-dato/` → `pd-*` services (data factory, obligations, azure ad, jira adapter)
- `cliente/` → `pc-*` client portal (web SPA + API)
- `asesores/` → `pgi-*` backoffice (web + API)

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan at:
`specs/001-client-team-assignments/plan.md`
<!-- SPECKIT END -->
