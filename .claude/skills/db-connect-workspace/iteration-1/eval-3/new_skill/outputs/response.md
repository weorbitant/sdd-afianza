# Conectar a la BD de data-factory en dev

El repo `pd-service-data-factory` no está clonado localmente, así que no hay `.env` disponible. Hay dos opciones:

---

## Opción 1 — Leer credenciales desde k8s (recomendada)

Obtén la password directamente del secreto de Kubernetes en el namespace `dev`:

```bash
kubectl get secret pd-service-data-factory-secret -n dev \
  -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d
```

Con la password en mano, conéctate:

```bash
PGPASSWORD='<password-obtenida>' psql \
  -h af-psql-dev.afianza-ac.es \
  -p 5432 \
  -U postgres \
  -d pd-service-data-factory-dev
```

---

## Opción 2 — Clonar el repo y usar connect.sh

```bash
# Clona el repo en la ruta esperada del workspace
git clone <repo-url> /Users/sito/Documents/afianza/plataforma-del-dato/pd-service-data-factory

# Copia el .env de dev (o pídelo al equipo)
cp .env.dev plataforma-del-dato/pd-service-data-factory/.env

# Luego usa el script estándar
bash ~/.claude/skills/db-connect/scripts/connect.sh data-factory dev
```

---

## Datos de conexión

| Campo    | Valor                              |
|----------|------------------------------------|
| Host     | `af-psql-dev.afianza-ac.es`        |
| Puerto   | `5432`                             |
| Usuario  | `postgres`                         |
| Base de datos | `pd-service-data-factory-dev` |

> **VPN requerida** — verifica conectividad antes de conectar:
> ```bash
> nc -zv af-psql-dev.afianza-ac.es 5432
> ```

---

## Si no tienes psql instalado

Puedes lanzar una query puntual desde cualquier servicio que tenga `pg` en `node_modules`:

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
