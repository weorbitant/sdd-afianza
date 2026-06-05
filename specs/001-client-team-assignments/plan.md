# Implementation Plan: Client Team Assignments (DEVPT-518, v2)

**Branch**: `main` (work happens on feature branches `feat/dev-518-*` per US) | **Date**: 2026-06-04 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from `specs/001-client-team-assignments/spec.md`

> **Scope of this plan**: las 6 user stories funcionales de §5 spec (US-01..US-06) + US-07 diferida. Foco principal en **MVP P1 (US-01, US-02, US-04, US-05)**. P2 (US-03, US-06) se planifican aquí pero pueden split-shippearse en sprints distintos.

## Summary

Reemplaza el modelo actual de `client_assignment` (filas 1-1 sin tramos temporales) por uno **temporal y consultable a fecha**: dos tablas nuevas (`client_team`, `client_team_assignment`) en `pgi-service-pgi-api`, normalización de fechas a primer día del mes en API normal (excepción AMQP onboarding), cobertura por rol cross-team, antigüedad como campo derivado server-side, y propagación a downstream vía nuevo routing key `pgi-api.v1.client-team-assignment.{opened|closed}`. Frontend en `pgi-app-pgi-web` con pantalla de composición + modales de alta/edición + vista histórica. La tabla legacy `client_assignment` queda congelada — sin migración explícita, los equipos se vuelven a meter manualmente vía UI o vía evento de onboarding cuando aplique.

**Modelo decidido y consolidado** en [`er-diagram.md`](./er-diagram.md) y [`data-model.md`](./data-model.md). Decisiones cerradas en [`decisions.md`](./decisions.md) (con avisos v2). Plan de implementación a partir de aquí.

## Technical Context

**Language/Version**: TypeScript 5.x (BE y FE).

**Primary Dependencies**:
- **Backend (`pgi-service-pgi-api`)**: NestJS 10, MikroORM 6 (Postgres driver), `@afianza-ac/nest-module-auth` (AzureAdJwtGuard), `@afianza-ac/nest-module-rabbitmq`, class-validator/class-transformer, date-fns para cálculo de boundaries de mes y manipulación de fechas.
- **Frontend (`pgi-app-pgi-web`)**: React 19, Vite, TanStack Query 5, react-hook-form, MUI v6 (componentes ya existentes), date-fns.

**Storage**: PostgreSQL 17 (`postgres:17-alpine` en dev/test, RDS en cloud). Schema en `client_team` + `client_team_assignment` (nuevas) + lecturas a `client`, `employee`, `provided_service` (existentes).

**Testing**:
- Backend: Jest + `@testcontainers/postgresql` para integración (constitución Principio II — NO mockear EntityManager). Supertest para controllers. Unit tests para helpers de dominio (`compute-employee-tenure`, `sum-coverage-percentage`, `normalize-month-boundary`).
- Frontend: Vitest + Testing Library. Mocks de TanStack Query para tests de UI.
- E2E: Playwright cubriendo los acceptance scenarios de §5 spec por US.

**Target Platform**: Backend en Linux server (Azure AKS). Frontend en navegadores modernos (Chrome/Edge corporativos).

**Project Type**: Web — backend NestJS + frontend SPA. Cross-service AMQP a `pd-service-obligations-api` y `pd-service-data-factory`.

**Performance Goals**:
- POST/PATCH/DELETE member: p95 < 300 ms (incluye cálculo de cobertura + publish AMQP en transacción).
- GET `/clients/{id}/teams?at={date}`: p95 < 150 ms.
- GET `/clients/{id}/teams/history`: p95 < 300 ms (sin paginación, volúmenes pequeños ~50-200 filas).

**Constraints**:
- `SELECT … FOR UPDATE` sobre fila `client` antes de calcular cobertura para serializar transiciones complete/incomplete (FR-024 spec, ADR-0015).
- Optimistic concurrency con `version` (ADR-0010) — cliente envía `version`, servidor incrementa o devuelve 409.
- Routing key AMQP debe seguir `<service>.v1.<entity>.<event>` (constitution P-IV).

**Scale/Scope**: ~10.000 clientes activos, ~2.000 empleados en backoffice, equipos típicos de 3-8 miembros por cliente+departamento, ~3-5 cambios de equipo al mes por cliente activo. Volumen de eventos AMQP estimado: ~3.000 eventos/mes en régimen estable.

## Compliance & Security Surface *(Afianza preset)*

### PII storage & encryption

- **Tablas/columnas que almacenan PII**: ninguna directamente en las tablas nuevas — solo FKs (`client_id`, `employee_id`) y emails de auditoría (`created_by`, `updated_by`). La PII real vive en `client` y `employee` (ya existentes, fuera de scope de esta feature).
- **Encriptación en reposo**: TLS de la conexión + cifrado de disco a nivel de RDS (estándar Azure). No se añade encriptación adicional a las nuevas columnas.
- **Encriptación en tránsito**: TLS asumido en todas las conexiones (Postgres, RabbitMQ, HTTP).
- **Logs**: PII NO se loguea. Los logs estructurados llevan `clientId` y `employeeId` (UUIDs, no PII directa). Confirmación explícita: ni `created_by` ni `updated_by` (emails) se loguean en logs de aplicación — solo en BD como audit trail.

### Auth & authorization

- **Guard aplicado a los endpoints nuevos**: `AzureAdJwtGuard` de `@afianza-ac/nest-module-auth` en todos los endpoints REST de la feature.
- **Scopes/claims requeridos**: rol `Responsable` o `Coordinador` (claim `role` en el JWT) para escrituras (POST/PATCH/DELETE). Lectura (GET) abierta a cualquier usuario autenticado del backoffice.
- **Roles RBAC tocados**: ninguno nuevo. Se reutilizan `Responsable` y `Coordinador` definidos en `pgi-api` (existentes).
- **Endpoints públicos**: ninguno. Todos requieren autenticación.

### RabbitMQ contracts

**Publicaciones nuevas** (pgi-api → exchange `internal` en vhost `data_platform`):

- Routing key: `pgi-api.v1.client-team-assignment.opened`
  - Disparado en: cada INSERT en `client_team_assignment` (incluyendo onboarding) cuando el equipo destino queda `complete`.
  - Payload (mínimo): `assignmentId`, `clientTeamId`, `clientId`, `department`, `role`, `employeeId`, `percentage`, `isMain`, `dateFrom` (effective), `version`.
- Routing key: `pgi-api.v1.client-team-assignment.closed`
  - Disparado en: cada UPDATE que setea `date_to` o DELETE por FR-007.
  - Payload (mínimo): `assignmentId`, `clientTeamId`, `clientId`, `department`, `role`, `employeeId`, `dateTo` (effective), `version`.
- **PII en payload**: no — solo UUIDs y enums.
- **Schemas detallados**: ver [`contracts/amqp/`](./contracts/amqp/).

**Suscripciones nuevas** (pgi-api consume):

- Queue: `pgi-api:client-onboarding-assignment:process`
  - Routing key bound: `client-onboarding-assignment` (nombre exacto pendiente con producer — OQ-005)
  - Idempotencia: dedupe por `payload.id` (UUID generado por el producer) + idempotency key check en una `inbox_messages` simple, o `em.upsert` por `(clientTeamId, employeeId, role, dateFrom)` natural key. Decisión final en task de implementación de US-04.

### External integrations

- **Adapters usados**: ninguno HTTP. Toda la comunicación cross-service es vía RabbitMQ.
- **Credenciales/secretos**: variables de entorno estándar (Azure Key Vault inyectado vía CSI driver en AKS). No se introducen credenciales nuevas.
- **Rate limits**: no aplica (todo interno).
- **Manejo de fallos del tercero**: `pd-service-obligations-api` y `pd-service-data-factory` consumen los eventos asincrónicamente; si fallan, los mensajes van a DLQ del lado consumer (no del producer). El producer (pgi-api) no reintenta — confía en RabbitMQ persistencia.

## Constitution Check

| Principio | Cumplimiento | Notas |
|---|---|---|
| **I. 3-layer architecture (NON-NEGOTIABLE)** | ✅ | Endpoints REST en `src/application/rest/client-teams/` y `/client-team-assignments/`. Lógica de cobertura, normalización, antigüedad en `src/domain/services/...` y helpers. AMQP subscriber en `src/application/amqp/client-onboarding-assignment-subscriber/`. Sin llamadas infra→app inversas. |
| **II. Real-container testing (NON-NEGOTIABLE)** | ✅ | Todos los tests de integración (controllers + servicios con EM) usan `@testcontainers/postgresql`. EntityManager no se mockea. Tests de helpers puros (sin DB) usan Jest sin contenedor. |
| **III. MikroORM UoW discipline** | ✅ | Lecturas con `disableIdentityMap: true`. Escrituras con `em.fork()`. Operaciones de reemplazo (close + open) envueltas en `em.fork()` + `em.transactional()` para serializar con `SELECT … FOR UPDATE`. `em.upsert()` en el subscriber AMQP de onboarding para idempotencia. Sin `@EnsureRequestContext()` en AMQP. Migraciones pasan `migration:check` antes de aplicar. |
| **IV. Event-driven cross-service** | ✅ | Routing keys siguen `pgi-api.v1.client-team-assignment.{opened\|closed}`. Queue naming `pgi-api:client-onboarding-assignment:process`. No hay HTTP cross-service. Contratos AMQP en `contracts/amqp/`. |
| **V. Simplicity & intentional complexity** | ✅ | Sin abstracciones nuevas no justificadas. No se introduce repository pattern (MikroORM EM directo). Helpers puros donde aplica. Decisión explícita de NO denormalizar `client_id`/`department` en `client_team_assignment` (data-model.md §1.2) — los partial uniques que requerían denormalización pasan a validación de servicio. Sin protección contra duplicados accidentales (FR-013 v2). |

**Status**: ✅ Sin violaciones. Sección "Complexity Tracking" al final queda vacía.

## Project Structure

### Documentation (this feature)

```text
specs/001-client-team-assignments/
├── spec.md              # Funcional autoritativa (v2)
├── plan.md              # Este archivo (/speckit-plan output)
├── research.md          # Phase 0 — decisiones técnicas resueltas
├── data-model.md        # Modelo de datos detallado (v2)
├── er-diagram.md        # Diagrama ER autoritativo
├── decisions.md         # ADRs heredados con marcadores v2
├── quickstart.md        # Phase 1 — guía de arranque local
├── contracts/
│   ├── rest/
│   │   ├── client-teams.openapi.yaml
│   │   └── client-team-assignments.openapi.yaml
│   └── amqp/
│       ├── client-team-assignment.opened.schema.json
│       ├── client-team-assignment.closed.schema.json
│       └── client-onboarding-assignment.schema.json
├── tasks.md             # Phase 2 (a generar con /speckit-tasks — agrupado por US)
├── designs/             # frames de UI (heredados de v1, revisar)
├── checklists/          # heredadas — pueden necesitar refresh
└── _archive/            # v1 congelada
```

### Source Code (backend — `pgi-service-pgi-api`)

```text
asesores/pgi-service-pgi-api/src/
├── application/
│   ├── rest/
│   │   ├── client-teams/
│   │   │   ├── client-teams.controller.ts          # POST /clients/{id}/teams, GET ?at, GET /history
│   │   │   ├── client-teams.controller.spec.ts
│   │   │   └── dto/
│   │   └── client-team-assignments/
│   │       ├── client-team-assignments.controller.ts  # POST/PATCH/DELETE members
│   │       ├── client-team-assignments.controller.spec.ts
│   │       └── dto/
│   └── amqp/
│       └── client-onboarding-assignment-subscriber/
│           ├── client-onboarding-assignment.subscriber.ts
│           └── client-onboarding-assignment.subscriber.spec.ts
├── domain/
│   ├── entities/
│   │   ├── client-team.entity.ts                    # con `version`, sin start/end
│   │   └── client-team-assignment.entity.ts         # con `is_main`, sin denormalizados
│   ├── services/
│   │   ├── client-teams/
│   │   │   ├── client-teams.service.ts
│   │   │   ├── client-teams.service.spec.ts
│   │   │   └── helpers/
│   │   │       ├── compute-team-status.helper.ts
│   │   │       ├── compute-team-status.helper.spec.ts
│   │   │       ├── compute-employee-tenure.helper.ts
│   │   │       └── compute-employee-tenure.helper.spec.ts
│   │   └── client-team-assignments/
│   │       ├── client-team-assignments.service.ts
│   │       ├── client-team-assignments.service.spec.ts
│   │       └── helpers/
│   │           ├── normalize-month-boundary.helper.ts
│   │           ├── normalize-month-boundary.helper.spec.ts
│   │           ├── sum-coverage-percentage.helper.ts
│   │           ├── sum-coverage-percentage.helper.spec.ts
│   │           ├── insert-with-future-preservation.helper.ts
│   │           ├── insert-with-future-preservation.helper.spec.ts
│   │           ├── assert-single-main-asesor.helper.ts
│   │           ├── assert-provided-service-active.helper.ts
│   │           └── publish-assignment-events.helper.ts
│   └── constants/
│       └── client-team-errors.ts                    # códigos de error de §3 data-model
├── infrastructure/                                   # vacío para esta feature
└── migrations/
    ├── 20260604xxxx-add-client-team-audit-fields.ts # ALTER client_team
    └── 20260604xxxy-create-client-team-assignment.ts

test/
└── e2e/
    ├── client-teams.us01-creation.e2e-spec.ts
    ├── client-team-assignments.us02-edit-current-month.e2e-spec.ts
    ├── client-team-assignments.us03-future-changes.e2e-spec.ts
    ├── client-onboarding-assignment.us04-amqp.e2e-spec.ts
    └── client-teams.us05-history-tenure.e2e-spec.ts
```

### Source Code (frontend — `pgi-app-pgi-web`)

```text
asesores/pgi-app-pgi-web/src/
├── features/
│   └── client-team/
│       ├── components/
│       │   ├── ClientTeamView.tsx                   # vista vigente con cobertura + banner
│       │   ├── ClientTeamHistory.tsx                # vista histórica
│       │   ├── AddMemberModal.tsx                   # US-01 + US-02 alta
│       │   ├── EditMemberModal.tsx                  # US-02 reemplazo/cambio % + US-03 selector futuro
│       │   └── MemberRow.tsx
│       ├── hooks/
│       │   ├── useTeam.ts                           # query GET /teams?at
│       │   ├── useTeamHistory.ts                    # query GET /teams/history
│       │   ├── useAddMember.ts                      # mutation POST member
│       │   ├── useUpdateMember.ts                   # mutation PATCH
│       │   └── useRemoveMember.ts                   # mutation DELETE
│       ├── api/
│       │   └── client-team.client.ts                # OpenAPI client tipado
│       └── pages/
│           └── ClientTeamPage.tsx                   # entry point en la ficha del cliente
```

### Source Code (cross-service — `pd-service-obligations-api`, **solo US-06**)

```text
plataforma-del-dato/pd-service-obligations-api/src/
└── application/
    └── amqp/
        └── client-team-assignment-subscriber/       # consume opened/closed para reasignar tareas
```

**Structure Decision**: Multi-paquete polirepo. Backend principal en `asesores/pgi-service-pgi-api/`, frontend en `asesores/pgi-app-pgi-web/`. Cross-service para US-06 (P2) en `plataforma-del-dato/pd-service-obligations-api/`. La feature se ramifica por US — cada US tiene su propia rama `feat/dev-518-usXX-<slug>`; no hay una rama monolítica.

## Complexity Tracking

> Vacío — sin violaciones del Constitution Check. Toda la complejidad introducida está justificada por reglas funcionales explícitas en spec.md (normalización de mes, preservación de tramos futuros, cobertura cross-team) y respeta los 5 principios.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| — | — | — |
