# Implementation Plan: Asignaciones Múltiples — US1 (Crear y gestionar el equipo de un cliente)

**Branch**: `001-client-team-assignments` | **Date**: 2026-06-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-client-team-assignments/spec.md`

**Scope of this plan**: solo **US1 (P1)** — crear/editar miembros de equipos de cliente, validación de coberturas 100% asesores/técnicos por (cliente, departamento), permisos `responsable`/`coordinador`, persistencia inmediata por miembro, optimistic concurrency, FR-017 (servicios contratados), partial unique FR-021 y migración legacy FR-013.

US2 (porcentajes avanzados), US3 (histórico) y US4 (cierre + reasignación de tareas) **no** entran en esta iteración. La tabla de auditoría `ClientTeamAssignmentChange` queda diferida (ver `decisions.md` → `OPEN-001-change-log-shape`).

## Summary

US1 permite a un responsable abrir la ficha de un cliente y constituir su equipo añadiendo miembros (responsable + coordinador opcional + 1..n asesores + 0..n técnicos), con `percentage`, `dateFrom`/`dateTo` (granularidad mensual — FR-012), e `isPrimaryAdvisor` para el asesor principal. Cada operación persiste de inmediato; el equipo está en estado derivado `incomplete` mientras (a) los coberturas de % no sumen 100% por (client, department), (b) falte el responsable o al menos un asesor o (c) no haya `isPrimaryAdvisor` único. La publicación AMQP (FR-014) y la transición a `active` ocurren cuando todas las condiciones se cumplen.

Aprovechamos las entidades existentes `ClientTeam` y `ClientAssignment` en `pgi-service-pgi-api` (ya tienen la base — falta añadir `version`, `isPrimaryAdvisor`, `createdBy`, constraints nuevos y la migración FR-013).

## Technical Context

**Language/Version**: TypeScript (Node 22 — `.nvmrc` en pgi-service-pgi-api). Frontend TS estricto.

**Primary Dependencies**:
- Backend: NestJS, MikroORM (postgres driver), `@afianza-ac/nest-module-auth`, `@afianza-ac/nest-module-rabbitmq`, `@afianza-ac/lib-core-definitions` (enums `Department`, `ClientAssignmentRole`).
- Frontend: React 19 + Vite + TanStack Query (patrón ya existente en `pgi-app-pgi-web`).

**Storage**: PostgreSQL 17 (MikroORM). Schema cambios vía migrations auto-generadas.

**Testing**:
- Backend: Jest unit + `@testcontainers/postgresql` para tests de servicios que tocan EM (NON-NEGOTIABLE — Constitution II). Supertest para controllers con DTO validation.
- Frontend: Vitest + Testing Library.

**Target Platform**: pgi-service-pgi-api (NestJS) + pgi-app-pgi-web (SPA backoffice). Sin cambios cross-service en US1 — `pd-service-data-factory` y `pd-service-jira-adapter` quedan para iteración aparte (los FR-018..FR-020 se aplican cuando US2/US3 entren en juego).

**Project Type**: Web (backend NestJS + SPA React).

**Performance Goals**:
- POST/PATCH/DELETE de miembro: p95 < 300 ms (operación + recomputo de coberturas).
- GET de equipo de cliente: p95 < 200 ms.

**Constraints**:
- Optimistic concurrency con columna `version` smallint (ADR-0010 en `decisions.md`). Header `If-Match: <version>` en endpoints de escritura. 409 al conflicto.
- Granularidad mensual (FR-012): el servicio fija `dateFrom = primer día del mes` y `dateTo = último día del mes`.
- Partial unique BD: `UNIQUE(client_id, employee_id) WHERE date_to IS NULL` (FR-021).
- Idempotencia AMQP: subscribers downstream ya usan `em.upsert` (Constitution III). No requiere cambios en US1.

**Scale/Scope**:
- ~10k clientes activos, ~2 deptos cada uno → ~20k `ClientTeam` post-migración.
- ~30k `ClientAssignment` activas estimadas (avg 1.5 miembros por equipo en MVP).
- 0 cambios en `pc-app-*` ni en `pd-service-*` (US1 contenido en `pgi-*`).

## Compliance & Security Surface

### PII storage & encryption

- **Tablas/columnas que almacenan PII**: ninguna nueva. `ClientTeam` y `ClientAssignment` referencian `Employee` (PII en otra tabla, no duplicada). Los `created_by` / `updated_by` guardan el **email** del backoffice user — patrón ya presente en otras tablas, considerado dato operativo.
- **Encriptación en reposo**: cifrado a nivel disco/Postgres gestionado — N/A a nivel app.
- **Encriptación en tránsito**: TLS asumido (mTLS interno N/A — comunicación intra-cluster vía SDN).
- **Logs**: ni `Employee.email` ni nombres de cliente se loguean en este flujo. Solo se loguean IDs (uuid) y `version`.

### Auth & authorization

- **Guard aplicado a los endpoints nuevos**: `AzureAdJwtGuard` (de `@afianza-ac/nest-module-auth`) + guard de rol custom que exige claim `permissions` contiene `CLIENT_ASSIGNMENT_EDIT` para POST/PATCH/DELETE. GET solo requiere `CLIENT_ASSIGNMENT_READ`.
- **Scopes/claims requeridos**:
  - `CLIENT_ASSIGNMENT_READ` para GET.
  - `CLIENT_ASSIGNMENT_EDIT` para POST/PATCH/DELETE.
- **Roles RBAC tocados**: `responsable`, `coordinador` (edit). `asesor`, `tecnico` (read).
- **Endpoints públicos / sin auth**: ninguno.

### RabbitMQ contracts

- **Publicaciones modificadas**: routing key existente `pgi-api.v1.client-assignment.updated`. Payload actual ya incluye `clientId`, `employeeId`, `role`, `department`, `dateFrom`, `dateTo`. Para US1 **no** se amplía el payload (FR-018 — `teamId`/`percentage` — se difiere a iteración con US2). Sí se mantiene la regla de **suprimir publicación cuando el equipo está `incomplete`** (FR-014).
- **Suscripciones nuevas**: ninguna.
- **PII en payload**: solo uuid + email (ya en payload actual).
- **Idempotencia**: subscriber downstream (pd-service-data-factory) ya usa `em.upsert` por `(client, employee, role, department, dateFrom)` — sin cambios en US1.

### External integrations

- **Adapter usado**: ninguno nuevo. No se llama a Microsoft Graph ni a Jira en US1.
- **Credenciales/secretos**: N/A.
- **Manejo de fallos del tercero**: N/A.

## Constitution Check

**Principio I (3 capas)**: ✅ Endpoints REST en `src/application/rest/client-teams/` y `/client-team-assignments/`. Validación de coberturas, transiciones de estado y reglas FR-016/FR-017/FR-021 en `src/domain/services/...`. Sin infrastructure: solo Postgres a través de EM.

**Principio II (Real-container testing)**: ✅ Servicios de dominio testeados con `@testcontainers/postgresql`. Controllers con Supertest + domain mockeado solo para 400/403/409.

**Principio III (UoW MikroORM)**: ✅ Lecturas con `disableIdentityMap: true`. Escrituras con `em.fork()`. POST/PATCH/DELETE de miembro envuelve recomputo de coberturas + flush en `em.transactional()` para evitar carrera con otra request en el mismo (client, department).

**Principio IV (Event-driven)**: ✅ Mantiene `rabbitMQService.publish('clientAssignmentUpdated', ...)`. Supresión cuando `incomplete` en el domain service.

**Principio V (Simplicidad)**: ✅
- No se introduce `ClientTeamAssignmentChange` (diferido — OPEN-001).
- No se crea repository layer — EM directo.
- No `POST /commit` (modelo borrador descartado en Clarifications 2026-05-29).

**Gate result**: ✅ PASS sin violaciones — no se requiere Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-client-team-assignments/
├── plan.md              # This file (US1 scope)
├── spec.md
├── decisions.md         # ADRs consolidados + OPEN-001
├── er-diagram.md
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── client-teams.openapi.yaml
│   └── client-team-assignments.openapi.yaml
└── tasks.md             # /speckit-tasks (siguiente comando)
```

### Source Code (repository root — polyrepo)

```text
asesores/pgi-service-pgi-api/
├── src/
│   ├── application/
│   │   └── rest/
│   │       ├── client-teams/                         # EXISTE — ampliar
│   │       │   ├── client-teams.controller.ts
│   │       │   └── dto/
│   │       │       ├── create-client-team.dto.ts     # NEW
│   │       │       └── client-team-response.dto.ts   # NEW
│   │       └── client-team-assignments/              # NEW
│   │           ├── client-team-assignments.controller.ts
│   │           └── dto/
│   │               ├── create-assignment.dto.ts
│   │               ├── update-assignment.dto.ts
│   │               └── assignment-response.dto.ts
│   ├── domain/
│   │   ├── models/
│   │   │   ├── client-team.ts                        # EXISTE — añadir `version`, `createdBy`
│   │   │   └── client-assignment.ts                  # EXISTE — añadir `isPrimaryAdvisor`, `version`, `createdBy`
│   │   ├── services/
│   │   │   ├── client-teams/
│   │   │   │   ├── client-teams.service.ts
│   │   │   │   └── helpers/
│   │   │   │       ├── assert-month-boundary.helper.ts
│   │   │   │       └── compute-team-status.helper.ts
│   │   │   └── client-team-assignments/
│   │   │       ├── client-team-assignments.service.ts
│   │   │       └── helpers/
│   │   │           ├── sum-coverage-percentage.helper.ts
│   │   │           ├── assert-provided-service-active.helper.ts
│   │   │           └── assert-no-conflicting-active-assignment.helper.ts
│   │   └── constants/
│   │       └── client-team-errors.ts                 # EXISTE — ampliar códigos
│   └── migrations/
│       ├── Migration20260603xxxx-add-version-and-primary-advisor.ts
│       └── Migration20260603xxxy-backfill-legacy-team-id.ts  # FR-013
└── test/
    └── e2e/
        ├── client-team-assignments.create.e2e-spec.ts
        ├── client-team-assignments.coverage-validation.e2e-spec.ts
        └── client-teams.status-transitions.e2e-spec.ts

asesores/pgi-app-pgi-web/
└── src/
    └── features/
        └── client-team/                              # NEW
            ├── ClientTeamSection.tsx
            ├── AddMemberModal.tsx
            ├── MemberRow.tsx
            ├── hooks/
            │   ├── useClientTeam.ts
            │   └── useUpsertAssignment.ts
            └── __tests__/
                └── ClientTeamSection.test.tsx
```

**Structure Decision**: feature contenida en `pgi-service-pgi-api` (backend) + `pgi-app-pgi-web` (frontend). Sin tocar `pd-*` ni `pc-*` en US1. La migración FR-013 vive en `pgi-service-pgi-api/src/migrations/` y se ejecuta vía `npm run migrations:apply` en deploy.

## Complexity Tracking

No aplica — Constitution Check pasa sin violaciones.
