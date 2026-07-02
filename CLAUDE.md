# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workspace Overview

This is a **polyrepo** — independent services that form the Afianza data platform. Each has its own `package.json`, git history, and service-level `CLAUDE.md` with detailed guidance.

All repos live flat at the workspace root. The name prefix marks the domain — `af-*` shared libs, `pc-*` client portal, `pgi-*` advisor backoffice, `pd-*` data platform.

```
# Shared NestJS libraries (@afianza-ac/*) — libraries, not running services (no DB, no HTTP server)
af-nest-module-auth/             # Azure AD JWT auth (passport + JWKS) — stable
af-nest-module-auth-v2/          # Entra External ID / CIAM (WIP — new auth work goes here)

# Portal del Cliente (pc-)
pc-app-portalcliente-web/        # Client portal SPA
pc-service-portalcliente-api/    # Client portal API (NestJS + PostgreSQL)

# Portal del Asesor / Backoffice (pgi-)
pgi-app-pgi-web/                 # Internal backoffice SPA (React 19 + Vite)
pgi-service-pgi-api/             # Client & employee management API (NestJS + PostgreSQL)

# Plataforma del Dato (pd-)
pd-service-data-factory/         # Data aggregation hub: Sage, AEAT, Jira, Azure AD, HubSpot
pd-service-obligations-api/      # Fiscal obligations management (NestJS + PostgreSQL)
```

Each service has its own `CLAUDE.md` — always read it before working in that service.
- `pd-service-data-factory` and `pc-app-portalcliente-web` store their CLAUDE.md at `.claude/CLAUDE.md` (non-standard — read it explicitly).
- `af-nest-module-auth/` and `af-nest-module-auth-v2/` have no service-level CLAUDE.md — rely on workspace root guidance. They are shared libraries: changes affect all consumers, so check dependents before publishing.

> **Not checked out locally:** `pd-service-jira-adapter` and `pd-service-azuread-adapter` are deployed services with their own repos in `github.com/afianza-ac`, but are intentionally **not cloned in this workspace**. `data-factory` still exchanges AMQP events with them — clone them on demand if you need to inspect their side of a cross-service flow.

## Document subsystem (gd-* / http2bus / bus2storage) — not cloned locally

A document-management pipeline lives in `github.com/afianza-ac` but is **not cloned in this workspace** — clone on demand to inspect any side of the flow:

- `gd-service-gestor-documental-api` — the "gestor documental". Ingests via REST `POST /v1/documents/upload` (multipart; SHA-256 staging `DocumentIngestion` → `Document`) or AMQP (SharePoint). Stores in Azure Blob, publishes `document_persisted`.
- `gd-service-document-classifier-api` — AI classification + metadata extraction (Ollama) for Spanish fiscal documents. Downstream of the gestor.
- `pd-service-http2bus` — generic HTTP→AMQP gateway. `POST /http-handler/:source/:version/:entity/:eventType`, auth per source, publishes routing key `http2bus.<source>.<version>.<entity>.<event>`. **JSON bodies only** today.
- `pd-service-bus2storage` — consumes the bus and archives raw payloads to S3.

## Plataforma del Dato (pd-*) — shared infra

- **Kubernetes namespace** `plataformadato`: `kubectl --context=dev get pods -n plataformadato` (or `--context=prod`).
- **RabbitMQ**: vhost `data_platform`, exchange `internal`. `pd-*` services publish with routing key `pd-<service>.v1.<entity>.<event>`.

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