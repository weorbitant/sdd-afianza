# Afianza — Core Project Map

## Type
Polyrepo workspace — independent NestJS microservices + React SPAs forming the Afianza data platform.

## Root layout
All repos live flat at the workspace root; the name prefix marks the domain.
```
af-nest-module-auth/, af-nest-module-auth-v2/  → af-* shared auth libraries
pc-app-portalcliente-web/, pc-service-portalcliente-api/  → pc-* client-facing portal
pgi-app-pgi-web/, pgi-service-pgi-api/  → pgi-* backoffice advisor portal
pd-service-data-factory/, pd-service-obligations-api/  → pd-* data platform services
specs/             → feature specs (speckit workflow)
.claude/rules/     → workspace-wide Claude Code rules (auto-loaded)
```

## Services
- `pgi-service-pgi-api` — backoffice API (NestJS + PostgreSQL + RabbitMQ)  
- `pgi-app-pgi-web` — backoffice SPA (React 19 + Vite)  
- `pc-service-portalcliente-api` — client portal API (NestJS + PostgreSQL)  
- `pc-app-portalcliente-web` — client portal SPA; CLAUDE.md at `.claude/CLAUDE.md` (non-standard path)  
- `pd-service-data-factory` — aggregation hub (Sage, AEAT, Jira, AzureAD, HubSpot); CLAUDE.md at `.claude/CLAUDE.md` (non-standard path)  
- `pd-service-obligations-api` — fiscal obligations  

Deployed but **not checked out locally** (clone from `github.com/afianza-ac` if needed): `pd-service-jira-adapter` (Jira Assets sync), `pd-service-azuread-adapter` (Microsoft Graph sync).  

## Invariants
- Each service has its own `package.json`, git repo, and git history — this is a polyrepo, the repos sit flat at the workspace root.
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
