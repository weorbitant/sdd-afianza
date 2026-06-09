# Conexion a obligations en local

Usa el script `connect.sh` del skill, que lee las credenciales automaticamente:

```bash
bash ~/.claude/skills/db-connect/scripts/connect.sh obligations local
```

Eso abre un shell psql interactivo contra la base de datos `mp-service-obligations-api-local` en `localhost:5432`.

---

**Credenciales (de `.env-sample`):**

| Campo    | Valor                          |
|----------|-------------------------------|
| Host     | `localhost`                    |
| Puerto   | `5432`                         |
| Database | `mp-service-obligations-api-local` |
| User     | `postgresql`                   |
| Password | `Password123`                  |

---

**Fallback manual** (si el script falla o psql no está disponible):

```bash
PGPASSWORD='Password123' psql -h localhost -p 5432 -U postgresql -d mp-service-obligations-api-local
```

O con node (desde el directorio del servicio):

```bash
cd /Users/sito/Documents/afianza/plataforma-del-dato/pd-service-obligations-api
node -e "
const { Client } = require('pg');
const c = new Client({ host:'localhost', port:5432, database:'mp-service-obligations-api-local', user:'postgresql', password:'Password123' });
c.connect().then(() => c.query('SELECT NOW()')).then(r => { console.table(r.rows); c.end(); }).catch(e => { console.error(e.message); c.end(); });
"
```

---

**Prerequisito**: la infra local debe estar levantada. Si no:

```bash
cd /Users/sito/Documents/afianza/plataforma-del-dato/pd-service-obligations-api
npm run infra:up
```
