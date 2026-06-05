# Quickstart — Client Team Assignments v2

Guía de arranque local para implementar la feature DEVPT-518 (v2).

## Prerequisitos

- Node.js 20.x, npm 10.x
- Docker (para Postgres + RabbitMQ de testcontainers / infra dev)
- Acceso al repo polirepo Afianza
- VPN o conexión a Azure si vas a tocar la versión cloud (opcional para implementación local)

## Levantar el backend (`pgi-service-pgi-api`)

```bash
cd asesores/pgi-service-pgi-api
npm install
npm run infra:up               # Postgres + RabbitMQ vía Docker compose
npm run migrations:up          # aplica migraciones existentes
npm run start:dev              # NestJS en modo watch
```

API disponible en `http://localhost:3010/api` (o el puerto configurado en `.env`).

## Levantar el frontend (`pgi-app-pgi-web`)

```bash
cd asesores/pgi-app-pgi-web
npm install
npm run dev                    # Vite en http://localhost:5173
```

Configurar `.env.local` apuntando al backend local:

```
VITE_PGI_API_URL=http://localhost:3010/api
```

## Crear nuevas migraciones (cuando implementes)

```bash
cd asesores/pgi-service-pgi-api
# Asegúrate de tener la entity creada/modificada antes
npx mikro-orm migration:check                    # debe mostrar diffs si hay
npm run migrations:create -- --name add-client-team-audit-fields
# Editar la migración generada y verificar el SQL
npx mikro-orm migration:create --dump            # debe devolver "No changes required"
```

## Ejecutar tests

### Unit (helpers de dominio puros)

```bash
cd asesores/pgi-service-pgi-api
npx jest --testPathPattern=src/domain/services/client-team
```

### Integración (con testcontainers — arranca Postgres real)

```bash
npx jest --testPathPattern=test/integration/client-team
# Cold start ~10s la primera vez (descarga postgres:17-alpine)
```

### E2E (Playwright)

```bash
cd asesores/pgi-app-pgi-web
npm run test:e2e
```

## Mockear el contract para empezar el FE sin esperar al BE

El contract OpenAPI está en `specs/001-client-team-assignments/contracts/rest/`. Para servirlo como mock:

```bash
npx @stoplight/prism-cli mock specs/001-client-team-assignments/contracts/rest/client-teams.openapi.yaml --port 4010
# en otra terminal
npx @stoplight/prism-cli mock specs/001-client-team-assignments/contracts/rest/client-team-assignments.openapi.yaml --port 4011
```

En el `.env.local` del FE apuntar a `http://localhost:4010` mientras el BE no esté listo.

## Probar el subscriber AMQP de onboarding localmente

```bash
# Asumiendo RabbitMQ levantado vía infra:up
# Publicar un mensaje de prueba conforme al schema:
docker exec -i pgi-rabbitmq rabbitmqadmin publish \
  exchange=internal \
  routing_key=client-onboarding-assignment \
  payload='{
    "eventId": "...",
    "clientId": "...",
    "department": "fiscal",
    "members": [
      { "employeeId": "...", "role": "responsable", "dateFrom": "2026-05-20" },
      { "employeeId": "...", "role": "asesor", "dateFrom": "2026-05-20", "isMain": true }
    ]
  }'
```

Schema completo en `contracts/amqp/client-onboarding-assignment.schema.json`.

## Ramificación por user story

Una rama por US, prefijo `feat/dev-518-`:

```bash
git checkout -b feat/dev-518-us01-team-creation
# ...trabajar...
gh pr create --base main --title "feat(pgi-api): US-01 alta inicial del equipo"
```

## Verificar contra spec

Cada US tiene sus acceptance scenarios en `spec.md §5`. Antes de abrir PR:
1. Implementar los acceptance scenarios como tests E2E (uno por scenario).
2. Correr `npm run lint && npm run build && npm test`.
3. Cross-check con `data-model.md` que las migraciones no rompen invariantes documentados.

## Referencias rápidas

| Documento | Para qué sirve |
|---|---|
| `spec.md` | Autoridad funcional. Historias, criterios de aceptación. |
| `plan.md` | Plan técnico (este árbol de carpetas, gates, perf goals). |
| `er-diagram.md` | Modelo ER autoritativo. |
| `data-model.md` | Schema detallado, migraciones, errores. |
| `research.md` | Decisiones de Phase 0 con rationale (R-01..R-05). |
| `decisions.md` | ADRs heredados con avisos v2. |
| `contracts/rest/*` | OpenAPI — fuente de verdad del contract REST. |
| `contracts/amqp/*` | JSON Schemas — fuente de verdad de payloads AMQP. |
| `designs/` | Frames de UI (heredados v1 — revisar relevancia). |

## Cosas a coordinar antes de mergear MVP

- **Producer de onboarding**: confirmar routing key real (OQ-005). Hoy hipotetizamos `client-onboarding-assignment`.
- **DROP COLUMN de `client_team.start_date/end_date`**: auditar consumers en `pd-service-data-factory` y `pd-service-jira-adapter` antes del Deploy B (ver research.md R-03).
- **obligations-api** (US-06, P2): ticket espejo en el proyecto de obligations para implementar el subscriber `client-team-assignment.opened/closed`. Hablar con team lead.
