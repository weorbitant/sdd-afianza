# Implementation Plan: PGI · Asignaciones múltiples por porcentajes (DEVPT-518)

**Branch**: `feat/001-client-team-assignments`  ·  **Date**: 2026-06-01  ·  **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-client-team-assignments/spec.md` (848 líneas, 39 FRs, 12 entradas de Clarifications, 11 Open Questions PO con 7 resueltas).

## Summary

Evolucionar las asignaciones cliente↔empleado desde el modelo legacy 1:1 (un empleado por rol y departamento) a un modelo **multi-equipo con porcentajes**: cada cliente puede tener N `ClientTeam` activos por departamento, cada team agrupa miembros con `role` (responsable / coordinador / asesor / técnico), porcentaje de dedicación y un asesor principal. La validación del 100% se calcula **por bucket de rol** (asesores / técnicos) **y por departamento del cliente** (agregando entre todos los teams del mismo departamento), no por equipo individual.

Stack confirmado en el polyrepo: NestJS 10 + MikroORM 6 + PostgreSQL 17 (backend), React 19 + Vite (frontend), RabbitMQ para coordinación cross-service. Tres servicios backend y un frontend tocados: `pgi-service-pgi-api` (owner), `pgi-app-pgi-web` (UI), `pd-service-data-factory` (consumer del evento `client-assignment` para informes), `pd-service-jira-adapter` (consumer + sync a Jira Assets).

## Technical Context

**Language/Version**: TypeScript 5.7 (todos los servicios).

**Primary Dependencies**: NestJS 10, MikroORM 6 (PostgreSQL), `@afianza-ac/nest-module-rabbitmq` (AMQP wrapper), `@afianza-ac/lib-core-definitions` (enums + shared types: `Department`, `ClientAssignmentRole`, `ServiceFamily`, `ServiceCategory`), React 19 + Vite + TanStack Query (frontend).

**Storage**: PostgreSQL 17 (esquema compartido por servicio).

**Testing**: Jest + `@testcontainers/postgresql` con `postgres:17-alpine` (integration), Jest mocks para servicios sin EntityManager, Supertest para controllers, Vitest para frontend.

**Target Platform**: Linux (AKS) para backend; web browser moderno (Chrome/Edge corporativo) para frontend.

**Project Type**: Multi-service web — backend NestJS + frontend React, comunicación entre servicios vía AMQP.

**Performance Goals**:
- Sincronización a Plataforma del Dato vía AMQP en <5 min desde el cambio (FR-014, ya existente).
- Carga de "Asignaciones actuales" en la ficha de cliente <500 ms incluso con 4+ teams activos (degradación aceptable hasta 800 ms en p95).
- Validación de suma 100% por departamento sincrónica al guardar miembro (<200 ms).

**Constraints**:
- Optimistic concurrency vía `updatedAt` en `ClientTeam` y `ClientAssignment` (FR-022) — HTTP 409 al conflicto.
- Backward-compat con pipeline `client_onboarding_persisted` existente (FR-017 onboarding sigue creando filas legacy hasta resolver D10).
- Validación cross-service: cualquier nueva regla aplicada en UI MUST replicarse en backend (decisión PO 2026-06-01).
- Migración no destructiva, idempotente, sin afectar registros históricos.
- ⚠️ D10 (onboarding ↔ ClientTeam) y D11 (asignación tareas por rol) siguen abiertas — assumption MVP: onboarding sigue creando legacy + reagrupación manual / todas las tareas van al asesor principal.

**Scale/Scope**: ~3-4k clientes activos · ~150 empleados · ~2 departamentos (Fiscal + Laboral, enum cerrado) · 4 user stories (P1-P4) · 4 servicios tocados.

## Compliance & Security Surface *(mandatory — Afianza preset)*

- **Datos sensibles tocados**: porcentajes de dedicación (≈ retribución implícita por cliente), histórico de cambios de asignación con autoría (`updatedBy`). Acceso restringido por rol (responsable/coordinador = edición; asesor/técnico = lectura).
- **Auth**: Azure AD via `@afianza-ac/nest-module-auth` en todos los endpoints. JWT con claims de rol.
- **Authorization**: validación de rol en cada endpoint de escritura (composición mínima + permiso de edición). Defense in depth: UI oculta CTA + backend rechaza 403 si el rol no encaja.
- **OWASP**:
  - Input validation via `class-validator` en DTOs (límites de porcentaje 1-100, enums cerrados, fechas válidas).
  - SQL injection: ORM (MikroORM) — no se usan queries raw.
  - Authorization bypass: tests específicos en controllers verificando 403 para roles sin permiso.
- **Histórico**: las filas de `ClientAssignment` con `dateTo` no se borran (preserva auditoría — decisión PO).
- **Logs**: cambios de asignación generan eventos AMQP que data-factory ingiere para auditoría.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Notas |
|---|---|---|
| I · 3-layer arch | ✅ Pass | Endpoints en `application/rest/`, lógica en `domain/services/`, persistencia via MikroORM `domain/models/`. AMQP subscribers en `application/amqp/` sin lógica de negocio. |
| II · Real-container testing | ✅ Pass | Integration tests con `@testcontainers/postgresql` para `ClientAssignmentsService`, `ClientTeamsService`, AMQP subscribers. Sin mocks del EntityManager. |
| III · MikroORM UoW | ✅ Pass | AMQP subscribers usan `em.fork()` + `em.transactional` para inserciones masivas. `em.upsert()` en `applyFromClientOnboarding`. `disableIdentityMap: true` en queries de validación. |
| IV · Event-driven | ✅ Pass | Cross-service vía AMQP (`client-assignment` ampliado con `teamId`+`percentage`, `client_onboarding_persisted` sin cambios). Sin llamadas HTTP entre servicios. |
| V · Simplicity | ✅ Pass | No se introduce ningún patrón nuevo (Repository, Factory, etc.). Reuso de `RabbitMQService`, `BackofficeUser` actor pattern, `MikroOrmModule`. Sin abstracciones especulativas. |

## Project Structure

### Documentation (this feature)

```text
specs/001-client-team-assignments/
├── plan.md                   # Este fichero
├── research.md               # Phase 0: decisiones técnicas resueltas (NEEDS CLARIFICATION → answers)
├── data-model.md             # Phase 1: entidades + migraciones
├── quickstart.md             # Phase 1: cómo arrancar este feature en local
├── contracts/                # Phase 1: contratos API + AMQP events
│   ├── client-teams-api.md
│   ├── client-assignments-api.md
│   └── client-assignment-event.md
├── decisions/                # ADRs existentes — se añadirá ADR-0010
├── spec.md                   # Spec (input)
└── tasks.md                  # Phase 2 output (/speckit-tasks)
```

### Source Code (polyrepo — afecta a 4 servicios)

```text
afianza/                                  # workspace root
├── asesores/
│   ├── pgi-service-pgi-api/              # OWNER · backend principal
│   │   ├── src/
│   │   │   ├── application/
│   │   │   │   ├── rest/
│   │   │   │   │   ├── client-teams/            # NEW · controller + DTOs equipos
│   │   │   │   │   └── client-assignments/      # MODIFY · añadir endpoints de % + isPrimary
│   │   │   │   └── amqp/
│   │   │   │       ├── client-subscriber/       # MODIFY · onboarding consumer (D10 partial)
│   │   │   │       └── client-assignment-publisher/  # NEW · publica `client-assignment` ampliado
│   │   │   └── domain/
│   │   │       ├── models/
│   │   │       │   ├── client-team.ts           # MODIFY · añadir `isPrimary`, validation por dept
│   │   │       │   └── client-assignment.ts     # MODIFY · añadir `isPrimary` (asesor), `causesBaja`, unique constraint nuevo
│   │   │       └── services/
│   │   │           ├── client-teams/            # NEW · CRUD + validation 100% por dept
│   │   │           └── client-assignments/      # MODIFY · routing tareas + reasignación al sucesor
│   │   └── migrations/                    # NEW · migración aditiva FR-013 + nuevos constraints
│   └── pgi-app-pgi-web/                   # FRONTEND
│       └── src/features/client-assignments/
│           ├── presentation/components/   # MODIFY · modal lateral con multi-rol + slider %
│           ├── application/use-cases/     # MODIFY · validate composition + 100% por dept
│           └── infrastructure/            # MODIFY · DTOs alineados con nuevos contratos
├── plataforma-del-dato/
│   ├── pd-service-data-factory/           # MODIFY · alineación modelo + consumer client-assignment
│   │   ├── src/domain/models/
│   │   │   └── client-assignment.ts       # MODIFY · añadir `team_id` + `percentage`
│   │   └── src/application/amqp/          # MODIFY · subscriber consume nuevos campos
│   │   └── migrations/                    # NEW · añadir columnas
│   └── pd-service-jira-adapter/           # MODIFY · sync solo principal a Jira Assets
│       └── src/domain/services/client-assignment/  # MODIFY · seleccionar `isPrimary=true` + team principal
└── specs/001-client-team-assignments/     # docs
```

**Structure Decision**: Polirepo existente — no se crea ningún servicio nuevo. La feature se reparte entre 4 repos siguiendo el patrón cross-service via AMQP existente (`internal` exchange, `data_platform` vhost). Cada servicio mantiene su 3-layer arch y migraciones locales. No hay nuevo módulo NestJS (Constitution I: monolithic AppModule).

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (ninguna) | — | — |

Ningún principio constitucional se rompe. No se introduce abstracción nueva (`ClientTeamsService` y `ClientAssignmentsService` ya existen — se amplían). Migración aditiva, sin destructive changes. Reuso de patterns existentes para AMQP + onboarding subscriber.

## Phase Plan

### Phase 0 — Research (genera `research.md`)

Resolver dudas técnicas surgidas del spec + open questions parcialmente respondidas:

1. **Migración 1:1 → multi-equipo**: ¿cómo asignar `team_id` a las filas existentes sin team? Crear un `ClientTeam` por (cliente, departamento) con miembros existentes al 100% — idempotente.
2. **AMQP message ampliado**: estructura exacta del payload `client-assignment.v1.updated` con los nuevos campos `teamId`, `percentage`, `isPrimary`.
3. **Consumer alignment**: pasos para que `pd-service-data-factory` y `pd-service-jira-adapter` deserialicen los nuevos campos sin romper compat con productores legacy (rolling deploy).
4. **Validación 100% por departamento — implementación**: query agregada vs cálculo en memoria; ¿forzar transacción para evitar race con AMQP subscriber paralelo?
5. **Onboarding bridge (D10 partial)**: documentar la assumption de que `applyFromClientOnboarding` sigue creando filas con `team_id = NULL` hasta resolución PO; añadir test de regresión para asegurar que no rompe.
6. **Frontend state model**: TanStack Query vs Zustand para el modal de composición de equipo con validación reactiva del 100% por departamento.

### Phase 1 — Design & Contracts

**Artefactos a generar**:

1. **`data-model.md`** — entidades y migraciones:
   - `ClientTeam` (modificar): añadir `isPrimary: boolean = false` por departamento del cliente (max 1 con `true`).
   - `ClientAssignment` (modificar): añadir `isPrimaryAdvisor: boolean = false` (solo aplica si `role: asesor`, max 1 por team), `causesBaja: boolean = false`. Constraints nuevos:
     - Mantener actual: `(client, employee, role, department, dateFrom) UNIQUE`.
     - Añadir: `(client_id, employee_id) WHERE dateTo IS NULL` partial unique (FR-021 — opción B PO: una persona, un equipo por cliente).
     - Mantener CHECK `percentage >= 1 AND percentage <= 100`.
   - Nuevo concepto: validación derivada (no entidad) `DepartmentBucketState` calculada en `ClientTeamsService.getDepartmentBucketStatus(clientId, department)`.

2. **`contracts/client-teams-api.md`** — endpoints REST para gestión de equipos:
   - `POST /clients/{clientId}/teams` (crear team)
   - `PATCH /clients/{clientId}/teams/{teamId}` (modificar nombre / `isPrimary`)
   - `POST /clients/{clientId}/teams/{teamId}/close` (cerrar con fecha fin)
   - Headers: `If-Match: <updatedAt>` para optimistic concurrency.

3. **`contracts/client-assignments-api.md`** — endpoints de miembros:
   - `POST /clients/{clientId}/teams/{teamId}/members` (añadir miembro)
   - `PATCH /clients/{clientId}/teams/{teamId}/members/{memberId}` (ajustar % / `isPrimary`)
   - `DELETE /clients/{clientId}/teams/{teamId}/members/{memberId}` (alias semántico de "cerrar" — pone `dateTo = hoy` y abre diálogo causa baja).
   - `GET /clients/{clientId}/department/{dept}/bucket-status` (devuelve estado del 100% por dept).

4. **`contracts/client-assignment-event.md`** — schema del evento AMQP ampliado:
   - Topic: `internal`, routing key `pgi-api.v1.client-assignment.updated`.
   - Payload: `{ clientId, teamId, teamId, employeeId, role, department, dateFrom, dateTo?, percentage, isPrimaryAdvisor, updatedAt, updatedBy }`.
   - Backward compat: campos nuevos como nullable, consumers actuales no rompen.

5. **`quickstart.md`** — cómo arrancar el dev local:
   - Migración inicial pgi-api.
   - Migración aditiva data-factory.
   - Verificación AMQP local (RabbitMQ in docker-compose).
   - Comando de regresión onboarding (consumer de `client_onboarding_persisted` sigue funcionando).

6. **ADR-0010 — Supersede ADR-0008** (single-bucket → two-bucket-por-departamento), documentando la decisión PO 2026-06-01.

7. **Agent context update**: actualizar el bloque `<!-- SPECKIT START --> ... <!-- SPECKIT END -->` en CLAUDE.md root para apuntar a este plan.

### Phase 2 — Tasks (manejado por `/speckit-tasks`)

Plan generará una `tasks.md` ordenada por user story con secciones por servicio:

```text
- US1 (Crear equipo)
  - pgi-api: model, service, controller, tests, migration
  - frontend: modal lateral, validation, mutation TanStack
- US2 (Distribución %)
  - backend: bucket status endpoint, validation logic
  - frontend: slider, live stats
- US3 (Histórico)
  - backend: query histórico
  - frontend: panel lateral timeline
- US4 (Cierre + reasignación)
  - backend: closure logic, successor inference, AMQP reassignment publish
  - frontend: dialog cierre, alert sucesor
- Cross-cutting
  - data-factory: model alignment, migration, subscriber update
  - jira-adapter: select primary, sync filtered
- Regression
  - onboarding pipeline preserved
```

## Re-check Constitution post-design

| Principio | Post-Phase 1 |
|---|---|
| I · 3-layer | ✅ Ningún cambio en arquitectura. |
| II · Real-container | ✅ Tests previstos con testcontainers. |
| III · MikroORM UoW | ✅ Forks + transactional en consumers AMQP. |
| IV · Event-driven | ✅ Sin HTTP cross-service nuevo. |
| V · Simplicity | ✅ Sin nuevas abstracciones. |

## Technical Challenge resolutions (2026-06-01)

`/speckit-challenge technical` detectó 6 BLOCKERs + 2 ADRs. Todos abordados antes de `/speckit-tasks`:

| ID | Finding | Resolución |
|----|---------|------------|
| T1 | Onboarding `upsert` vs nuevo partial unique | `applyFromClientOnboarding` cierra fila activa existente antes de insertar (pseudo-código + test de regresión en `data-model.md > Onboarding bridge`) |
| T2 | Faltaban CHECK constraints | Añadidos `chk_primary_advisor_only_asesor` y `chk_causes_baja_only_when_closed` en migración M1a |
| T3 | Sucesor no modelado | `successorId` REQUIRED en DELETE/close con `causesBaja=true`. Backend devuelve 400 SUCCESSOR_REQUIRED con `suggestedSuccessorId` calculado por temporalidad. Sin nuevo schema |
| T4 | Cierre de team sin transactionality | Contrato POST close ahora dice `em.transactional` + AMQP publish post-commit. Referencia a D-005 PENDING (outbox) |
| T5 | `updatedAt` para optimistic concurrency | **ADR-0010** — cambio a columna `version: integer` (`@Property({version: true})`) |
| T6 | At-least-one primary team no garantizado | Service auto-promotes el primer team de `(client, dept)` a `isPrimary=true`. Documentado en data-model lifecycle |
| T7 | `team_id` en data-factory sin FK justificado | **ADR-0011** — logical FK only, política de huérfanos documentada |
| T8 | Race en cómputo bucket status + publish | `SELECT ... FOR UPDATE` sobre fila padre `client` en la transacción que puede emitir transición |
| T10 | Backfill ordenado después del partial unique | Migración partida en **M1a (DDL + CHECKs + backfill + audit)** → **M1b (partial uniques)**. Si los datos legacy violan FR-021, M1a aborta con mensaje claro antes de crear el unique |

T9 (QUESTION-PO sobre OQ-008) sigue abierta pero **no bloquea el MVP** — ver assumption documentada en `quickstart.md > Limitaciones`.

Sub-findings del reviewer bucket-9 (que devolvió formato incorrecto y fue descartado) parcialmente cubiertos:
- M2 ahora añade también `is_primary_advisor` y `causes_baja` para evitar split migration cuando US4 ship later.
- Recordatorio explícito de test de regresión `apply-from-client-onboarding` en `data-model.md`.
- Coordinación de `@afianza-ac/lib-core-definitions` bump pendiente — se aborda en `tasks.md` cuando se genere.
