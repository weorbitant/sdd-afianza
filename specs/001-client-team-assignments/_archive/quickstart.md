# Quickstart — US1 Implementation

**Scope**: US1 (Crear y gestionar el equipo de un cliente).
**Prereqs**: Node 22, Docker, acceso al repo, branch `feat/001-client-team-assignments-us1` creada desde `main`.

## 1. Bring up infra

```bash
cd asesores/pgi-service-pgi-api
npm install
npm run infra:up      # PostgreSQL 17 + RabbitMQ via Docker
```

## 2. Verify migration baseline

> Antes de tocar entidades. Si arroja drift, parar y avisar.

```bash
npx mikro-orm migration:check
# Exit code 0 = snapshot in sync con `main`.
```

## 3. Backend changes (in order)

1. **Entities** — `src/domain/models/client-team.ts` + `client-assignment.ts`. Añadir `version`, `createdBy`, `isPrimaryAdvisor`, `createdAt` (assignment).
2. **Generate migration**:
   ```bash
   npm run migrations:create
   ```
   Revisar el SQL generado: debe matchear `data-model.md § Migraciones`. Editar a mano los partial unique y CHECK si MikroORM no los emite (lo habitual).
3. **Backfill migration** — crear `Migration20260603xxxy-backfill-legacy-team-id.ts` siguiendo R-007.
4. **Helpers de dominio** — `helpers/assert-month-boundary.helper.ts`, `compute-team-status.helper.ts`, `sum-coverage-percentage.helper.ts`, `assert-provided-service-active.helper.ts`, `assert-no-conflicting-active-assignment.helper.ts`. Cada uno con su `*.helper.spec.ts` (unit, sin EM).
5. **Servicios** — `client-teams.service.ts` y `client-team-assignments.service.ts`. Wrap escrituras en `em.fork()` + `em.transactional()` (Constitution III).
6. **Controllers** — endpoints según `contracts/*.openapi.yaml`. Guards `AzureAdJwtGuard` + role guard custom.
7. **AMQP publish** — reutilizar `rabbitMQService.publish('clientAssignmentUpdated', ...)` solo cuando `compute-team-status` devuelve `active` tras la operación.

## 4. Tests

```bash
# Unit tests de helpers (sub-segundo)
npx jest src/domain/services/client-teams/helpers
npx jest src/domain/services/client-team-assignments/helpers

# Integration con testcontainers (~10s arranque)
npx jest src/domain/services/client-teams/client-teams.service.spec.ts
npx jest src/domain/services/client-team-assignments/client-team-assignments.service.spec.ts

# Controllers (Supertest + mock domain)
npx jest src/application/rest/client-teams
npx jest src/application/rest/client-team-assignments

# E2E (testcontainers + supertest contra la app)
npx jest --config test/jest-e2e.json
```

**Must pass** antes de PR:
```bash
npm run lint
npm run build
npm test
```

## 5. Frontend changes (`pgi-app-pgi-web`)

```bash
cd asesores/pgi-app-pgi-web
npm install
npm run dev
```

1. `src/features/client-team/` — nuevo módulo.
2. `useClientTeam` (GET `/clients/{id}/teams`) — TanStack Query con `staleTime: 0` para reflejar persistencia inmediata.
3. `useUpsertAssignment` (POST/PATCH/DELETE) — invalida la query y maneja 409 mostrando toast *"El equipo ha cambiado, recarga..."*.
4. UI: banner amarillo cuando `team.status === 'incomplete'`. Botón Guardar deshabilitado mientras falte composición mínima (responsable + 1+ asesor + isPrimaryAdvisor).
5. Modal de cierre con doble confirmación (FR-009) **fuera de scope US1** (entra en US4).

## 6. Smoke test manual (golden path)

1. Login con usuario con permiso `CLIENT_ASSIGNMENT_EDIT`.
2. Abrir ficha de un cliente sin equipo en Fiscal con `ProvidedService` activo.
3. `POST /clients/{id}/teams` con `department=fiscal`, `startDate=2026-07-01`.
4. `POST /client-teams/{teamId}/assignments` × 2: un responsable, un asesor con `isPrimaryAdvisor=true`, `percentage=100`.
5. `GET /clients/{id}/teams` → status `active`, cobertura asesores = 100%.
6. Verificar publicación AMQP en RabbitMQ management UI: routing key `pgi-api.v1.client-assignment.updated` × 2.

## 7. Pre-PR checklist

- [ ] Branch `feat/001-client-team-assignments-us1` (no commits a `main`).
- [ ] Conventional Commits en cada commit (`feat(client-team): ...`).
- [ ] `npm run lint && npm run build && npm test` verdes.
- [ ] `npx mikro-orm migration:create --dump` devuelve "No changes required".
- [ ] CLAUDE.md actualizado si cambia algo de arquitectura (no se espera).
- [ ] PR description en inglés, link a DEVPT-518.
