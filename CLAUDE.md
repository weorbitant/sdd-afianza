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
/speckit-specify                # 1. Redactar spec desde descripción natural
/speckit-clarify                # 2. Resolver dudas obvias detectadas por el LLM
/speckit-challenge functional   # 3. Revisar gaps de negocio + sacar QUESTION-PO antes de planificar
/speckit-atlassian-sync-push    # 4. Subir Stories + Open Questions a Jira (NO sube subtasks)
/speckit-ready                  # 5. Readiness gate — evalúa spec contra rubric; gate advisory hacia plan
/speckit-plan                   # 6. Plan técnico + data model + contratos API
/speckit-challenge technical    # 7. Revisar gaps de modelado + secuencia de despliegue
/speckit-tasks                  # 8. Desglosar en tareas (viven en repo, NO en Jira)
/speckit-implement              # 9. Implementar tarea a tarea
```

> Los comandos `/speckit-*` usan el plan activo referenciado en la sección SPECKIT al final de este fichero.
> Modelo completo de refinement: ver `.specify/REFINEMENT.md`.
> Custom layer = `decisions.md` (1 por feature). Nada más.

### Active plugins in this project
| Command | Purpose |
|---------|---------|
| `/speckit-specify` | Crear o actualizar spec desde descripción en lenguaje natural |
| `/speckit-clarify` | Resolver dudas abiertas en la spec |
| `/speckit-challenge [mode]` | Revisión adversarial. `functional` = gaps de negocio + PO questions; `technical` = feasibility + delivery sequence; `all` (default si hay plan.md) = ambos. Read-only |
| `/speckit-ready` | Readiness gate: evalúa spec contra `.specify/quality-rubric.md` (8 criterios) y emite `readiness-report.md` con verdict y plan de acción. Read-only, advisory |
| `/speckit-analyze` | Detectar inconsistencias entre spec/plan/tasks (complementario al challenge) |
| `/speckit-plan` | Generar plan técnico, data model y contratos API |
| `/speckit-tasks` | Desglosar el plan en tareas de implementación |
| `/speckit-atlassian-sync-push [epic-key]` | Subir User Stories + Open Questions a Jira (NO subtasks — las tareas viven en `tasks.md`) |
| `/speckit-decisions-extract` | Extraer decisiones estructurales a ADRs (formato Nygard) en `specs/<feature>/decisions/` |
| `/speckit-implement` | Implementar tarea a tarea con generación de código |
| `/ce-plan` | Investigación técnica paralela antes de planificar |
| `/ce-brainstorm` | Brainstorming técnico para una feature |
| `/ops-suite` | Operaciones de infra (queues, deploys, logs, DB) |
| Auto: superpowers | TDD, debugging, code review — se activa automáticamente |
| `/azure-*` | Entra, AKS, RBAC, diagnósticos, despliegues |

### Trabajar con extensiones de Spec-Kit

Las extensiones locales viven en **`.specify/extensions/<name>/`** (in-place, versionadas en git). Cada una tiene:

```
.specify/extensions/<name>/
├── extension.yml                 # manifiesto (id, version, commands)
├── commands/speckit.<name>.md    # comando real (lo que ejecuta el LLM)
└── agents/*.md                   # opcional — prompts para sub-agents que invoque el comando
```

Cuando Spec-Kit instala una extensión genera **dos artefactos adicionales** que NO se editan a mano:

1. **Binding skill** en `.claude/skills/speckit-<command>/SKILL.md` — Claude Code descubre el slash command leyendo esto.
2. **Entrada en `.specify/extensions/.registry`** — el CLI de Spec-Kit la usa para `list/update/remove`.

#### Crear una extensión nueva

1. **Editar in-place** en `.specify/extensions/<new-name>/` siguiendo el layout. Mira `atlassian-sync/` como referencia.
2. **NUNCA** ejecutar `specify extension add .specify/extensions/<new-name> --dev` — el CLI hace `rmtree(dest)` antes del copytree y borra los ficheros cuando source == dest. Bug conocido.
3. **Registrar manualmente** (lo que el CLI haría):
   ```bash
   # 1. Generar el binding skill
   mkdir -p .claude/skills/speckit-<command>
   cat > .claude/skills/speckit-<command>/SKILL.md <<HEADER
   ---
   name: speckit-<command>
   description: "<copy from extension.yml>"
   argument-hint: "<args hint>"
   compatibility: Requires spec-kit project structure with .specify/ directory
   metadata:
     author: afianza-local
     source: <name>:commands/speckit.<command>.md
   user-invocable: true
   ---
   HEADER
   tail -n +6 .specify/extensions/<name>/commands/speckit.<command>.md >> .claude/skills/speckit-<command>/SKILL.md

   # 2. Calcular manifest_hash y añadir entrada a .specify/extensions/.registry
   shasum -a 256 .specify/extensions/<name>/extension.yml

   # 3. Añadir <name> a .specify/extensions.yml > installed:
   ```

#### Editar una extensión existente

- **Edita directamente** los ficheros en `.specify/extensions/<name>/`.
- **Si el cambio es solo en `commands/speckit.<command>.md`**: regenera el binding (paso 1 de arriba — `tail` + heredoc).
- **Si el cambio es en `extension.yml`**: regenera `manifest_hash` (paso 2) y actualiza la entrada en `.registry`.
- **Si el cambio es solo en `agents/*.md`**: el comando los lee en runtime, no requiere regeneración del binding.

#### Comandos útiles del CLI

```bash
specify extension list                   # ver instaladas — útil para verificar manifest_hash
specify extension info <name>            # detalle de una extensión
specify extension disable <name>         # desactivar sin borrar (útil para A/B testing)
specify extension enable <name>          # re-activar
# Evitar: `add`, `update`, `remove` sobre extensiones in-place — el CLI no espera ese layout
```

#### Diferencia entre commands, skills y presets

- **Spec-Kit command** (`.specify/extensions/<ext>/commands/*.md`) — fuente de verdad del slash command.
- **Claude Code skill** (`.claude/skills/<name>/SKILL.md`) — binding que Claude Code lee para exponer el `/<name>`. Auto-generado por el CLI, regenerable a mano.
- **Spec-Kit preset** (`.specify/presets/<name>/`) — paquete que **sobrescribe templates** base (`spec-template.md`, `plan-template.md`, etc.). NO contiene lógica ejecutable, solo modifica el formato de los artefactos generados.

Regla: nuevo comportamiento ejecutable → extensión. Cambio de formato en spec/plan/tasks → preset.

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
