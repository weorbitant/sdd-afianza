# Conexión a pgi-api en dev

Para conectarte a la base de datos de `pgi-api` en el entorno **dev**, usa el script `connect.sh` incluido en la skill:

```bash
bash ~/.claude/skills/db-connect/scripts/connect.sh pgi-api dev
```

El script lee las credenciales automáticamente desde el `.env` del servicio — no necesitas copiar la contraseña a mano.

---

## Datos de la conexión (por si necesitas el comando manual)

| Parámetro | Valor |
|-----------|-------|
| Host | `af-psql-dev.afianza-ac.es` |
| Puerto | `5432` |
| Base de datos | `pd-service-backoffice-api-dev` ⚠️ (no `pgi-*`) |
| Usuario | `postgres` |
| Contraseña | `POSTGRES_PASSWORD` en `asesores/pgi-service-pgi-api/.env` |

**Fallback manual** (solo si connect.sh falla):

```bash
# 1. Lee la contraseña del .env
PGPASSWORD=$(grep POSTGRES_PASSWORD ~/Documents/afianza/asesores/pgi-service-pgi-api/.env | cut -d= -f2)

# 2. Conecta
PGPASSWORD="$PGPASSWORD" psql -h af-psql-dev.afianza-ac.es -p 5432 -U postgres -d pd-service-backoffice-api-dev
```

Una vez dentro de psql, para inspeccionar la tabla de clientes:

```sql
-- Listar todas las tablas
\dt

-- Ver estructura de la tabla de clientes
\d client

-- Consultar filas
SELECT * FROM client LIMIT 20;
```

---

## Antes de conectar

Dev y prod solo son accesibles desde la red Afianza (VPN). Verifica conectividad primero:

```bash
nc -zv af-psql-dev.afianza-ac.es 5432
```

Si el comando cuelga o da error, activa la VPN antes de continuar.
