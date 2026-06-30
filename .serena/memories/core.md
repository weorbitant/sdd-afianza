# Afianza — Core Project Map

## Type
Polyrepo workspace — independent NestJS microservices + React SPAs forming the Afianza data platform.

## Root layout
```
asesores/          → pgi-* (backoffice advisor portal)
cliente/           → pc-* (client-facing portal)
plataforma-del-dato/ → pd-* (data platform services)
shared/            → af-nest-module-auth/, af-nest-module-auth-v2/
specs/             → feature specs (speckit workflow)
.claude/rules/     → workspace-wide Claude Code rules (auto-loaded)
```

## Sub-namespace → services
- `asesores/pgi-service-pgi-api` — backoffice API (NestJS + PostgreSQL + RabbitMQ)  
- `asesores/pgi-app-pgi-web` — backoffice SPA (React 19 + Vite)  
- `cliente/pc-service-portalcliente-api` — client portal API (NestJS + PostgreSQL)  
- `cliente/pc-app-portalcliente-web` — client portal SPA  
- `plataforma-del-dato/pd-service-data-factory` — aggregation hub (Sage, AEAT, Jira, AzureAD, HubSpot); CLAUDE.md at `.claude/CLAUDE.md` (non-standard path)  
- `plataforma-del-dato/pd-service-obligations-api` — fiscal obligations  

Deployed but **not checked out locally** (clone from `github.com/afianza-ac` if needed): `pd-service-jira-adapter` (Jira Assets sync), `pd-service-azuread-adapter` (Microsoft Graph sync).  

## Invariants
- Each service has its own `package.json` and git history within this monorepo.
- Always read the service-level `CLAUDE.md` before working in a service.
- `pd-service-data-factory` stores CLAUDE.md at `.claude/CLAUDE.md`.
- Auth: all services use `@afianza-ac/nest-module-auth` (Azure AD JWT via JWKS).
- Package manager: **npm** (all services have `package-lock.json`).
- No commits to `main` — always feature branch.

## Module memories
- Backoffice (pgi-*): `mem:asesores/core`
- Data platform (pd-*): `mem:plataforma-del-dato/core`
- Shared auth libs: `mem:shared/core`
- Cross-service AMQP patterns: `mem:conventions` → AMQP section
