# Connecting to the obligations database (local)

## Preferred method — connect.sh

The skill provides a script that reads credentials from `.env` automatically:

```bash
bash ~/.claude/skills/db-connect/scripts/connect.sh obligations local
```

> **Note:** The script at `~/.claude/skills/db-connect/scripts/connect.sh` does not currently exist on disk. See the fallback below.

---

## Fallback — manual psql

Credentials come from `.env-sample` (obligations uses this file instead of `.env`):

| Variable | Value |
|----------|-------|
| Host | `localhost` |
| Port | `5432` |
| Database | `mp-service-obligations-api-local` |
| User | `postgresql` |
| Password | `Password123` |

```bash
PGPASSWORD='Password123' psql \
  -h localhost \
  -p 5432 \
  -U postgresql \
  -d mp-service-obligations-api-local
```

---

## Fallback — Node.js (if psql not installed)

Run from inside `plataforma-del-dato/pd-service-obligations-api/` (so `pg` is available in `node_modules`):

```bash
node -e "
const { Client } = require('pg');
const c = new Client({
  host: 'localhost',
  port: 5432,
  database: 'mp-service-obligations-api-local',
  user: 'postgresql',
  password: 'Password123'
});
c.connect()
  .then(() => c.query('SELECT NOW()'))
  .then(r => { console.table(r.rows); c.end(); })
  .catch(e => { console.error(e.message); c.end(); });
"
```

Replace `SELECT NOW()` with your actual query.

---

## Pre-requisite

The local PostgreSQL container must be running. If it is not:

```bash
cd plataforma-del-dato/pd-service-obligations-api
npm run infra:up
```
