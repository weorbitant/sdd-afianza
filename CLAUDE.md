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

## Sub-namespaces

- `plataforma-del-dato/` → `pd-*` services (data factory, obligations, azure ad, jira adapter)
- `cliente/` → `pc-*` client portal (web SPA + API)
- `asesores/` → `pgi-*` backoffice (web + API)

## Rules

Workspace-wide guidance lives in `.claude/rules/`. Files without `paths:` frontmatter load every session; path-scoped files load only when Claude touches matching files.

**Service-specific patterns (architecture, MikroORM, migrations, testing, RabbitMQ) live in each service's own `CLAUDE.md`** — the workspace does not duplicate them. Always read the service-level `CLAUDE.md` before working in a service.

| File | Scope | Topic |
|------|-------|-------|
| `commands.md`           | always         | Common npm commands cheat-sheet (services define their own) |
| `git.md`                | always         | Conventional commits, branching, gh CLI |
| `atlassian.md`          | always         | Jira cloudId + hostname trap |
| `po-communication.md`   | always         | How to draft PO questions in Jira |
| `mcps.md`               | always         | Active MCPs and RTK token optimization |
| `polyrepo-cross-service.md` | always     | Verificar en código antes de especular sobre flujos AMQP cross-service |
| `rest-api-design.md`    | `specs/**/contracts/**`, `**/application/rest/**` | Principios REST: recursos no acciones, status codes RFC, embebido de agregados |