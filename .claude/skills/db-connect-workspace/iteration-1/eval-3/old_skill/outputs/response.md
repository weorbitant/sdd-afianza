# Response: Connecting to data-factory DB in dev

Para conectarte a la base de datos de `pd-service-data-factory` en dev, el skill usa `connect.sh`. El comando sería:

```bash
bash ~/.claude/skills/db-connect/scripts/connect.sh data-factory dev
```

**Sin embargo, hay un problema:** el repo `pd-service-data-factory` no está clonado localmente. El script necesita leer las credenciales del fichero `.env` en:

```
plataforma-del-dato/pd-service-data-factory/.env
```

Ese fichero no existe, así que el script fallará con:

```
Error: credentials file not found at .../plataforma-del-dato/pd-service-data-factory/.env

Possible reasons:
  - The repo may not be cloned locally (data-factory, jira-adapter)
  - The .env file may not exist yet (copy from .env.example or .env-sample)

Alternative: read credentials from k8s:
  kubectl get secret <service>-secret -n <env> -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
```

---

## Alternativa: obtener credenciales desde Kubernetes

Puesto que el repo no está clonado, la vía más directa es leer el secret del cluster de dev:

```bash
# Obtener la password de PostgreSQL desde el secret de k8s
kubectl get secret pd-service-data-factory-secret -n dev \
  -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
```

> Necesitas tener `kubectl` configurado apuntando al cluster de dev y VPN activa.

Con la password, conecta directamente:

```bash
PGPASSWORD='<password-del-secret>' psql \
  -h af-psql-dev.afianza-ac.es \
  -p 5432 \
  -U postgres \
  -d pd-service-data-factory-dev
```

---

## Checklist antes de conectar

- [ ] VPN activa (los hosts `af-psql-dev.afianza-ac.es` solo son accesibles en red Afianza)
- [ ] Verificar conectividad: `nc -zv af-psql-dev.afianza-ac.es 5432`
- [ ] `psql` instalado (`which psql`); si no, usar el fallback con `node -e` desde cualquier servicio con `pg` en `node_modules`

---

## Alternativa sin psql (node fallback)

Si no tienes `psql`, desde cualquier directorio de servicio que tenga `pg` instalado (ej. `asesores/pgi-service-pgi-api/`):

```bash
node -e "
const { Client } = require('pg');
const c = new Client({
  host: 'af-psql-dev.afianza-ac.es',
  port: 5432,
  database: 'pd-service-data-factory-dev',
  user: 'postgres',
  password: '<password>'
});
c.connect()
  .then(() => c.query('SELECT NOW()'))
  .then(r => { console.table(r.rows); c.end(); })
  .catch(e => { console.error(e.message); c.end(); });
"
```
