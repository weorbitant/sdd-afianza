---
name: db-connect
description: Use when connecting to an Afianza service database for inspection, debugging, or ad-hoc queries. Covers local, dev, and prod environments for all services (pgi, pc, pd). Use before running psql or querying any service's PostgreSQL database.
---

# DB Connect — Afianza Service Databases

## Overview

Afianza uses **external Azure PostgreSQL** instances — not k8s-internal. Connect directly via psql (no port-forwarding needed for dev/prod).

## Hosts

| Environment | Host | Port |
|-------------|------|------|
| local | `localhost` | `5432` |
| dev | `af-psql-dev.afianza-ac.es` | `5432` |
| prod | `af-psql-pro.afianza-ac.es` | `5432` |

## Service → Database registry

| Service | Short alias | Database name |
|---------|------------|---------------|
| `pgi-service-pgi-api` | `pgi-api` | `pd-service-backoffice-api-{env}` |
| `pc-service-portalcliente-api` | `pc-api` | `pc-service-portalcliente-api-{env}` |
| `pd-service-obligations-api` | `obligations` | `mp-service-obligations-api-{env}` |
| `pd-service-data-factory` | `data-factory` | `pd-service-data-factory-{env}` *(no .env locally — see note below)* |
| `pd-service-jira-adapter` | `jira-adapter` | `pd-service-jira-adapter-{env}` *(no .env locally — see note below)* |

`{env}` = `local` / `dev` / `prod`

> **Note:** `pgi-api` uses the legacy database name `pd-service-backoffice-api-{env}` — NOT `pgi-*`.

## Credentials

Read from the service's `.env` file. Never hardcode passwords in commands persisted to disk.

| Environment | User | Where to find password |
|-------------|------|----------------------|
| local | read from `.env` (varies by service — e.g. `pgi-api` usa `pgi_service_pgi_api_user`, `pc-api` usa `postgresql`) | `Password123` (standard dev default) |
| dev | `postgres` | Service `.env` → `POSTGRES_PASSWORD` |
| prod | `postgres` | Service `.env` → `POSTGRES_PASSWORD` |

**`.env` file paths** (relative to workspace root `~/Documents/afianza/`):

```
asesores/pgi-service-pgi-api/.env
cliente/pc-service-portalcliente-api/.env
plataforma-del-dato/pd-service-obligations-api/.env-sample   ← filename es .env-sample, no .env
```

> **data-factory y jira-adapter no tienen `.env` local** — los repos no están clonados. Para conectar, clona el repo primero o lee las credenciales desde k8s: `kubectl get secret <service>-secret -n <env> -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d`

## Connect

**Always use `connect.sh`** — reads credentials from the service `.env` automatically:

```bash
# Interactive psql shell (reads .env, no manual credential copy-paste)
bash ~/.claude/skills/db-connect/scripts/connect.sh <alias> [env]

# Examples
bash ~/.claude/skills/db-connect/scripts/connect.sh pgi-api dev
bash ~/.claude/skills/db-connect/scripts/connect.sh pc-api local
bash ~/.claude/skills/db-connect/scripts/connect.sh obligations prod
```

Script: `.claude/skills/db-connect/scripts/connect.sh`

**Manual fallback** (only if connect.sh fails):

```bash
# Read password from .env first, then:
PGPASSWORD='<pass>' psql -h <host> -p 5432 -U <user> -d <database>

# If psql not installed, use node pg from inside any service directory
node -e "
const { Client } = require('pg');
const c = new Client({ host:'<host>', port:5432, database:'<db>', user:'<user>', password:'<pass>' });
c.connect().then(() => c.query('<sql>')).then(r => { console.table(r.rows); c.end(); }).catch(e => { console.error(e.message); c.end(); });
"
```

## Common mistakes

- **Wrong DB name for pgi-api**: database is `pd-service-backoffice-api-{env}`, not `pgi-service-pgi-api-{env}`
- **Wrong user**: local → `postgresql`, dev/prod → `postgres`
- **No psql available**: fall back to `node -e` using the `pg` module (already in service `node_modules`)
- **VPN required**: dev/prod hosts are only reachable on the Afianza network — confirm connectivity first with `nc -zv af-psql-dev.afianza-ac.es 5432`
