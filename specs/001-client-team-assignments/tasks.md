---
description: "Tasks for US1 — Crear y gestionar el equipo de un cliente"
---

# Tasks: US1 · Crear y gestionar el equipo de un cliente

**Feature**: [001-client-team-assignments](./spec.md) | **Jira**: [DEVPT-573](https://afianza-ac.atlassian.net/browse/DEVPT-573)

**Scope**: Solo US1 (P1). US2/US3/US4 fuera de scope — se generarán en iteraciones posteriores.

**Prerequisites**: plan.md, spec.md (US1 + clarifications 2026-05-28), data-model.md, contracts/client-teams.md, contracts/client-assignments-history.md, research.md

**Tests**: Obligatorios (Principio II de la constitución — integration tests con `@testcontainers/postgresql`, sin mocking del EntityManager).

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: Paralelizable (ficheros distintos, sin dependencias pendientes)
- **[US1]**: Tarea perteneciente a User Story 1

## Path Conventions (web app polyrepo)

- Backend: `asesores/pgi-service-pgi-api/`
- Frontend: `asesores/pgi-app-pgi-web/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Preparar el repo y el entorno antes de tocar código.

- [ ] T001 Crear rama `feat/001-client-team-assignments` desde `main` (workspace root)
- [ ] T002 [P] Verificar snapshot limpio de MikroORM antes de tocar entidades: `cd asesores/pgi-service-pgi-api && npx mikro-orm migration:check` (debe mostrar "No changes required")
- [ ] T003 [P] Arrancar infra local: `cd asesores/pgi-service-pgi-api && npm run infra:up` (PostgreSQL + RabbitMQ)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Esquema de datos y migración legacy. Bloquea toda la implementación.

**⚠️ CRITICAL**: Ningún trabajo de US1 puede comenzar hasta que esta fase termine.

- [ ] T004 [US1] Crear entity `ClientTeam` en `asesores/pgi-service-pgi-api/src/domain/entities/client-team.entity.ts` (campos: id uuid, client FK, department enum, startDate date, endDate date nullable, createdBy varchar, createdAt/updatedAt timestamptz, índice parcial único `(client_id, department) WHERE end_date IS NULL`)
- [ ] T005 [US1] Extender entity `ClientAssignment` en `asesores/pgi-service-pgi-api/src/domain/entities/client-assignment.entity.ts` (añadir `percentage: number` smallint NOT NULL DEFAULT 100 CHECK 1–100; `team?: ClientTeam` FK nullable)
- [ ] T006 [US1] Generar migración con `cd asesores/pgi-service-pgi-api && npx mikro-orm migration:create` y verificar que cubre T004+T005. Editar la migración para añadir manualmente: (a) índice parcial único `idx_client_team_active`, (b) bloque de migración de datos legacy (ver plan.md → "Migración de datos legacy") en `asesores/pgi-service-pgi-api/src/migrations/Migration<timestamp>_add_client_team.ts`
- [ ] T007 [US1] Verificar que `npx mikro-orm migration:create --dump` devuelve "No changes required" tras T006 (idempotencia del snapshot)
- [ ] T008 [US1] Aplicar migración en local: `cd asesores/pgi-service-pgi-api && npm run migrations:up`

**Checkpoint**: Esquema en BD + datos legacy migrados a equipos implícitos. La capa de dominio puede arrancar.

---

## Phase 3: User Story 1 — Crear y gestionar el equipo de un cliente (Priority: P1) 🎯 MVP

**Goal**: Un responsable puede abrir la ficha de un cliente, crear/gestionar el equipo (asignar coordinador opcional, ≥1 asesor, técnicos), asignar porcentajes (default 100%) y confirmar el equipo con validación del 100% por rol. Asesores y técnicos ven el equipo en solo lectura.

**Independent Test**: Abrir la ficha de un cliente sin equipo → crear equipo con 1 asesor al 100% → commit → equipo activo visible. Cubre AC-1 a AC-4 del spec.

### DTOs y errores compartidos

- [ ] T009 [P] [US1] Crear DTOs de creación/listado/cierre de equipo en `asesores/pgi-service-pgi-api/src/application/dto/client-teams/team.dto.ts` (CreateTeamDto, TeamResponseDto, ActiveTeamSummaryDto)
- [ ] T010 [P] [US1] Crear DTOs de miembros en `asesores/pgi-service-pgi-api/src/application/dto/client-teams/member.dto.ts` (AddMemberDto, UpdatePercentageDto, MemberResponseDto, ValidationResultDto)
- [ ] T011 [P] [US1] Crear códigos de error de dominio en `asesores/pgi-service-pgi-api/src/domain/errors/client-team.errors.ts` (ACTIVE_TEAM_EXISTS, DATE_NOT_MONTH_BOUNDARY, PERCENTAGE_VALIDATION_FAILED, PERCENTAGE_OUT_OF_RANGE, ROLE_ALREADY_FILLED, ROLE_CONFLICT, MIN_ASESOR_REQUIRED, TEAM_CLOSED)

### Domain service — `ClientTeamsService`

- [ ] T012 [US1] Crear `ClientTeamsService` con métodos `createTeam`, `listByClient`, `getActiveSummary`, `findById` en `asesores/pgi-service-pgi-api/src/domain/services/client-teams.service.ts` (usa `em.fork()` para writes; lanza `ACTIVE_TEAM_EXISTS` si ya hay equipo activo para `client+dept`). Depende de T004
- [ ] T013 [US1] Añadir helper `validateMonthBoundary(date, mode: 'start' | 'end')` en `asesores/pgi-service-pgi-api/src/domain/services/client-teams.service.ts` para enforzar primer/último día de mes (lanza `DATE_NOT_MONTH_BOUNDARY`)
- [ ] T014 [US1] Añadir método `addMember(teamId, dto)` en `ClientTeamsService` que crea un `ClientAssignment` con `team_id`, sin validar la suma del 100% (modelo borrador). Valida rol único responsable/coordinador (lanza `ROLE_ALREADY_FILLED` / `ROLE_CONFLICT`) y rango 1–100 (`PERCENTAGE_OUT_OF_RANGE`). Depende de T005
- [ ] T015 [US1] Añadir método `updateMemberPercentage(assignmentId, dto)` en `ClientTeamsService` (sin validar suma, solo rango y boundary de `effectiveFrom`)
- [ ] T016 [US1] Añadir método `removeMember(assignmentId, dto)` en `ClientTeamsService` (sin validar suma — la validación es responsabilidad de `commit`)
- [ ] T017 [US1] Añadir método `validateTeam(teamId): ValidationResultDto` en `ClientTeamsService` (suma de % de **todos los miembros activos con rol ASESOR o TECNICO** — responsable y coordinador excluidos — debe ser exactamente 100; comprueba ≥1 asesor activo). Informativo: no lanza ni publica.
- [ ] T018 [US1] Añadir método `commitTeam(teamId)` en `ClientTeamsService` que invoca `validateTeam`, lanza `PERCENTAGE_VALIDATION_FAILED` / `MIN_ASESOR_REQUIRED` si falla, marca el equipo como confirmado y publica `backoffice-api.v1.client-assignment.updated` (un evento por miembro activo, incluyendo `percentage`)
- [ ] T019 [US1] Extender `ClientAssignmentsService` en `asesores/pgi-service-pgi-api/src/domain/services/client-assignments.service.ts` para incluir `percentage` y `teamId` en las respuestas existentes

### Controllers + permisos

- [ ] T020 [US1] Crear `ClientTeamsController` con los endpoints del contrato en `asesores/pgi-service-pgi-api/src/application/controllers/client-teams.controller.ts`: `GET/POST /v1/client-teams/:clientId/department/:dept`, `GET/POST /v1/client-teams/:clientId/:teamId/members`, `PATCH/DELETE /v1/client-teams/:clientId/:teamId/members/:id`, `POST /v1/client-teams/:clientId/:teamId/validate`, `POST /v1/client-teams/:clientId/:teamId/commit`, `GET /v1/client-teams/:clientId/department/:dept/active-summary`. Guards: `CLIENT_ASSIGNMENT_VIEW` (lectura) y `CLIENT_ASSIGNMENT_EDIT + CLIENT_ASSIGNMENTS_{DEPT}_EDIT` (escritura). Depende de T012–T018
- [ ] T021 [US1] Registrar `ClientTeamsController` y `ClientTeamsService` como providers en `asesores/pgi-service-pgi-api/src/app.module.ts` (sin nuevo módulo — todo en `AppModule` por constitución I)
- [ ] T022 [US1] Extender `ClientAssignmentsController` en `asesores/pgi-service-pgi-api/src/application/controllers/client-assignments.controller.ts` para devolver `percentage` y `teamId` en `GET /v1/client-assignments/:clientId/department/:dept`. Depende de T019

### Integration tests (testcontainers — obligatorios)

- [ ] T023 [P] [US1] Tests de creación de equipo en `asesores/pgi-service-pgi-api/test/integration/client-teams.create.spec.ts` (cubre AC-1: 1 asesor 100% → activo; AC-4: segundo equipo activo mismo cliente+dept → 409 ACTIVE_TEAM_EXISTS; `DATE_NOT_MONTH_BOUNDARY` cuando startDate no es primer día de mes)
- [ ] T024 [P] [US1] Tests de gestión de miembros en `asesores/pgi-service-pgi-api/test/integration/client-teams.members.spec.ts` (añadir/editar/eliminar miembros sin validación de suma — modelo borrador; rol único responsable/coordinador; rango % 1–100)
- [ ] T025 [P] [US1] Tests de validación y commit en `asesores/pgi-service-pgi-api/test/integration/client-teams.commit.spec.ts` (cubre AC-2: suma total (asesores + técnicos) ≠ 100 → 400 PERCENTAGE_VALIDATION_FAILED al commit; commit ok con 60% asesor + 40% técnico → publica `backoffice-api.v1.client-assignment.updated` con `percentage`; ≥1 asesor obligatorio en commit; responsable/coordinador NO entran en la suma)
- [ ] T026 [P] [US1] Tests de permisos en `asesores/pgi-service-pgi-api/test/integration/client-teams.permissions.spec.ts` (cubre AC-3: asesor/técnico → GET ok, POST/PATCH/DELETE → 403)
- [ ] T027 [P] [US1] Tests de migración legacy en `asesores/pgi-service-pgi-api/test/integration/migration.client-team-legacy.spec.ts` (semilla con asignaciones legacy 1-a-1 → aplicar migración → verifica que cada client+dept tiene un `ClientTeam` activo y que `client_assignment.team_id` apunta a él; idempotencia: ejecutar 2 veces produce el mismo estado)
- [ ] T028 [P] [US1] Tests del endpoint de history extendido en `asesores/pgi-service-pgi-api/test/integration/client-assignments.percentage.spec.ts` (GET devuelve `percentage` y `teamId`)

### Frontend — Tab Asignaciones en la ficha

- [ ] T029 [P] [US1] Crear tipos de dominio en `asesores/pgi-app-pgi-web/src/features/client-teams/types/client-team.types.ts` (ClientTeam, TeamMember, Role enum, Department enum)
- [ ] T030 [P] [US1] Crear hooks TanStack Query en `asesores/pgi-app-pgi-web/src/features/client-teams/api/client-teams.api.ts` (useActiveTeamSummary, useTeamMembers, useCreateTeam, useAddMember, useUpdatePercentage, useRemoveMember, useValidateTeam, useCommitTeam)
- [ ] T031 [P] [US1] Crear schema Zod de validación cross-field en `asesores/pgi-app-pgi-web/src/features/client-teams/schemas/team.schema.ts` (suma total de ASESOR + TECNICO = 100; rango % 1–100; ≥1 asesor; responsable/coordinador excluidos de la suma)
- [ ] T032 [P] [US1] Crear componente `PercentageSumIndicator` en `asesores/pgi-app-pgi-web/src/features/client-teams/components/PercentageSumIndicator.tsx` (recibe `sum` total del equipo; verde si 100, rojo si ≠100, texto explicativo "Equipo: X/100%")
- [ ] T033 [US1] Crear componente `TeamMemberForm` en `asesores/pgi-app-pgi-web/src/features/client-teams/components/TeamMemberForm.tsx` (TanStack Form field array; selector empleado + rol + percentage + dateFrom; submit añade miembro al borrador). Depende de T029, T030, T031
- [ ] T034 [US1] Crear componente `TeamMemberList` en `asesores/pgi-app-pgi-web/src/features/client-teams/components/TeamMemberList.tsx` (tabla con miembros activos, acciones eliminar/editar % en modo edición). Depende de T029, T030
- [ ] T035 [US1] Crear componente `TeamSection` en `asesores/pgi-app-pgi-web/src/features/client-teams/components/TeamSection.tsx` (contenedor del tab Asignaciones: muestra resumen, lista de miembros, formulario de añadir, botones "Guardar borrador" y "Confirmar equipo" → llama a `commit`; modo readonly para asesor/técnico). Depende de T032, T033, T034
- [ ] T036 [US1] Localizar el componente de la ficha de cliente en `asesores/pgi-app-pgi-web/` (path probable: `src/features/client-detail/pages/ClientDetailPage.tsx`, pero verificar primero el path real grepeando por la ruta `/general/ficha-cliente`). Añadir la tab `Asignaciones` apuntando a `TeamSection` con gating de permisos: visible siempre, edición según `CLIENT_ASSIGNMENT_EDIT`.

### Frontend tests (Vitest)

- [ ] T037 [P] [US1] Tests del `PercentageSumIndicator` en `asesores/pgi-app-pgi-web/src/features/client-teams/components/PercentageSumIndicator.test.tsx` (verde/rojo según suma)
- [ ] T038 [P] [US1] Tests del `TeamMemberForm` en `asesores/pgi-app-pgi-web/src/features/client-teams/components/TeamMemberForm.test.tsx` (validación Zod, submit deshabilitado fuera de rango, suma calculada correctamente)
- [ ] T039 [P] [US1] Tests del `TeamSection` en `asesores/pgi-app-pgi-web/src/features/client-teams/components/TeamSection.test.tsx` (AC-3: asesor/técnico → no ve botones de edición; AC-1: flujo completo crear → añadir asesor → commit)

**Checkpoint**: US1 funcional end-to-end. Tests pasando. Listo para PR.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [ ] T040 [P] Ejecutar `quickstart.md` contra entorno local y verificar los smoke tests del paso 3
- [ ] T041 [P] Pre-push gate backend: `cd asesores/pgi-service-pgi-api && npm run lint && npm run build && npm test`
- [ ] T042 [P] Pre-push gate frontend: `cd asesores/pgi-app-pgi-web && npm run build && npx vitest run src/features/client-teams`
- [ ] T043 Verificar el evento `backoffice-api.v1.client-assignment.updated` en RabbitMQ Management (localhost:15672) tras un commit: payload debe incluir `percentage`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sin dependencias.
- **Phase 2 (Foundational)**: Depende de Phase 1. **Bloquea US1 hasta T008.**
- **Phase 3 (US1)**: Depende de Phase 2.
- **Phase 4 (Polish)**: Depende de Phase 3.

### Within US1 (Phase 3)

- DTOs y errores (T009–T011) [P entre sí] → `ClientTeamsService` métodos (T012–T018) → Controllers (T020–T022)
- Tests de integración (T023–T028) pueden escribirse en paralelo a la implementación del controller y servicio que cubren, pero deben pasar antes del PR
- Frontend (T029–T039) depende solo del contrato — puede empezar en paralelo a backend (mock de respuestas con MSW si quieres avanzar)

### Parallel Opportunities

- **Setup** (T002, T003) — paralelo
- **Foundational entities**: T004 y T005 NO son paralelos porque comparten la migración (T006 los necesita ambos)
- **DTOs/errors** (T009, T010, T011) — paralelos
- **Service methods individuales** (T012–T018) — comparten fichero, serializar
- **Integration tests** (T023–T028) — ficheros distintos, paralelos
- **Frontend types/api/schema/indicator** (T029–T032) — ficheros distintos, paralelos
- **Frontend tests** (T037–T039) — paralelos

---

## Parallel Example: US1 — primer wave de DTOs + tipos + tests

```bash
# Backend wave A (paralelo)
Task: "T009 DTOs de team"
Task: "T010 DTOs de miembros"
Task: "T011 Códigos de error"
Task: "T023 Test creación de equipo"
Task: "T024 Test gestión de miembros"

# Frontend wave A (paralelo)
Task: "T029 Tipos de dominio"
Task: "T030 Hooks TanStack Query"
Task: "T031 Schema Zod"
Task: "T032 PercentageSumIndicator"
```

---

## Implementation Strategy

### MVP (US1 únicamente)

1. **Phase 1 + 2** → esquema + migración legacy listos
2. **Phase 3 backend** → entidades, service, controllers, tests → API funcional
3. **Phase 3 frontend** → tab Asignaciones contra backend real
4. **Phase 4** → quickstart + gates → PR

### Despliegue progresivo

1. Merge a `main` (incluye migración → aplica a clientes existentes auto-equipo)
2. Verificación post-deploy en staging
3. Demo a PO

---

## Notes

- Constitución II: los tests de integración usan `@testcontainers/postgresql` con `postgres:17-alpine`. Primer arranque ~10s.
- Constitución III: writes con `em.fork()`, reads con `disableIdentityMap: true`. Nunca `@EnsureRequestContext()`.
- Constitución IV: el commit publica vía `this.rabbitMQService.publish(...)` — sin HTTP entre servicios.
- Constitución V: sin nuevos módulos NestJS; providers en `AppModule`.
- El responsable se representa como `ClientAssignment` con `role: responsable` (clarificación 2026-05-28). Su % es 100% implícito y no entra en la validación de suma.
- Modelo borrador + commit (clarificación 2026-05-28): solo `POST /commit` valida y publica eventos.
- Migración masiva legacy (FR-013) dentro de US1 — los datos 1-a-1 son válidos por construcción y se convierten en equipos implícitos al desplegar.
