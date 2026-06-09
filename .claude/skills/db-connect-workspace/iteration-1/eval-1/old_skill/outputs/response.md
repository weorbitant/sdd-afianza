# Response: conectarse a pgi-api en dev

## Comando recomendado

Usa el script `connect.sh` — lee las credenciales del `.env` automáticamente, sin copiar passwords manualmente:

```bash
bash ~/.claude/skills/db-connect/scripts/connect.sh pgi-api dev
```

Eso abrirá una shell psql interactiva contra la base de datos correcta en dev.

---

## Detalles del destino

| Parámetro  | Valor                                   |
|------------|-----------------------------------------|
| Host       | `af-psql-dev.afianza-ac.es`            |
| Port       | `5432`                                  |
| Database   | `pd-service-backoffice-api-dev`         |
| User       | `postgres`                              |
| Password   | Lee de `asesores/pgi-service-pgi-api/.env` → `POSTGRES_PASSWORD` |

> **Ojo con el nombre de la base de datos**: es `pd-service-backoffice-api-dev`, NO `pgi-service-pgi-api-dev`. Es un nombre legacy que confunde.

---

## Antes de conectarte — verifica VPN

Dev/prod solo son accesibles desde la red Afianza. Comprueba conectividad primero:

```bash
nc -zv af-psql-dev.afianza-ac.es 5432
```

Si falla, activa la VPN y reintenta.

---

## Fallback manual (si connect.sh no está disponible)

Lee primero el password del `.env`:

```bash
grep POSTGRES_PASSWORD asesores/pgi-service-pgi-api/.env
```

Luego conéctate:

```bash
PGPASSWORD='<pass-del-.env>' psql \
  -h af-psql-dev.afianza-ac.es \
  -p 5432 \
  -U postgres \
  -d pd-service-backoffice-api-dev
```

---

## Una vez dentro — inspeccionar la tabla de clientes

```sql
-- Ver estructura
\d "client"

-- Ver primeras filas
SELECT * FROM "client" LIMIT 20;

-- Salir
\q
```

El nombre exacto de la tabla puede variar (`client`, `clients`, `Client`) — puedes listar todas con `\dt` para confirmar.
