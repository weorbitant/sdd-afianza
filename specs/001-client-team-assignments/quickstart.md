# Quickstart — DEVPT-518 dev local

Pasos para arrancar la feature en desarrollo local. Asume conocimiento previo del workflow de cada servicio (ver `CLAUDE.md` de cada uno).

## Prerequisitos

- Docker corriendo (para PostgreSQL + RabbitMQ).
- Node 20 + npm.
- Acceso a las 4 ramas: `feat/001-client-team-assignments` en cada uno de los 4 servicios afectados.

## Orden de arranque

### 1. `pgi-service-pgi-api` (owner)

```bash
cd asesores/pgi-service-pgi-api
npm install
npm run infra:up                      # PostgreSQL + RabbitMQ
npm run migrations:up                 # aplica migration M1 (FR-016, FR-021)
npm run backfill:primary-advisor      # script idempotente — promueve primer asesor a principal por (cliente, dept)
npm run start:dev
```

Verificar logs: el endpoint `/api/v1/clients/{id}/teams` debe responder. Los endpoints REST nuevos están en `src/application/rest/client-teams/` y `src/application/rest/client-assignments/`.

### 2. `pd-service-data-factory`

```bash
cd plataforma-del-dato/pd-service-data-factory
npm install
npm run infra:up
npm run migrations:up                 # aplica migration M2 (añade team_id + percentage)
npm run start:dev
```

El subscriber AMQP escucha en `data-factory:client-assignment:process` queue.

### 3. `pd-service-jira-adapter`

```bash
cd plataforma-del-dato/pd-service-jira-adapter
npm install
npm run start:dev
```

Sin migraciones nuevas (sólo cambio de lógica en el filtro a `isPrimaryAdvisor=true`).

### 4. `pgi-app-pgi-web` (frontend)

```bash
cd asesores/pgi-app-pgi-web
npm install
npm run dev                           # Vite en :5173
```

Acceder a `http://localhost:5173/clientes/{clientId}` para ver la nueva ficha con composición multi-equipo.

## Comandos de regresión obligatorios

Antes de pushear cualquier cambio:

### Onboarding pipeline preserved

El consumer `client_onboarding_persisted` NO debe romperse. Test específico:

```bash
cd asesores/pgi-service-pgi-api
npx jest --testPathPattern=apply-from-client-onboarding.regression
```

Debe pasar — verifica que `applyFromClientOnboarding` sigue creando filas legacy (`team_id = NULL`, `percentage = 100`) sin tocar la nueva lógica.

### Cross-service AMQP contract

```bash
cd plataforma-del-dato/pd-service-data-factory
npx jest --testPathPattern=client-assignment-subscriber.contract
```

Verifica que un payload legacy (sin `teamId`/`percentage`/`isPrimaryAdvisor`) se procesa sin error.

### Unique constraints

```bash
cd asesores/pgi-service-pgi-api
npx jest --testPathPattern=client-assignment.unique-constraints
```

Verifica que `(client, employee) WHERE date_to IS NULL` bloquea la doble asignación activa (FR-021).

## Limitaciones conocidas del MVP

1. **D5 (routing tareas por rol)** sin resolver — todas las tareas auto siguen yendo al asesor principal del dept. Si la PO define mapping por `ObligationCategory`, se aborda en sprint siguiente.
2. **D10 (onboarding ↔ team)** parcial — onboarding sigue creando filas con `team_id = NULL`. El responsable verá filas huérfanas en la vista del cliente hasta agruparlas. Pendiente decisión PO sobre crear "Equipo inicial" automático.
3. **Pantalla "Mis Clientes" y buscador del PGI** fuera de scope (FR-015). Sólo la ficha de cliente refleja la nueva composición.
4. **TaxDown / subcontratados** — no contemplado.
5. **Vista de anomalías** (clientes con servicio sin equipo válido) — backlog futuro.

## Troubleshooting

- **Error `PERSON_ALREADY_ACTIVE_IN_CLIENT` al añadir miembro**: la persona ya tiene otra asignación activa en este cliente (incluso en otro dept). Cerrar la anterior primero. Esto es FR-021 (decisión PO 2026-06-01: opción B).
- **Banner amarillo "no 100%" persistente**: comprobar `/api/v1/clients/{id}/department/{dept}/bucket-status` — el bucket de asesores o técnicos del dept está incompleto. La validación es por dept, no por team individual.
- **Eventos AMQP no llegan a data-factory**: revisar orden de deploy (R3 de research.md). Si data-factory tiene la versión vieja del subscriber, los nuevos campos se ignoran silenciosamente.

## Siguientes pasos

Una vez merged este MVP:
- Llevar D5 y D10 a la siguiente sesión PO.
- Evaluar si el feature de "asignaciones múltiples masivas" (mover carteras) entra en DEVPT-518 o se hace una épica aparte.
- Plan técnico para informes en `pd-service-data-factory` que aprovechen `team_id` + `percentage` (no en scope DEVPT-518).
