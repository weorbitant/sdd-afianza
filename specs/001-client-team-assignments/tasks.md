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

- [x] T001 Crear rama `feat/001-client-team-assignments` desde `main` (workspace root)
- [x] T002 [P] Verificar snapshot limpio de MikroORM antes de tocar entidades: `cd asesores/pgi-service-pgi-api && npx mikro-orm migration:check` (debe mostrar "No changes required")
- [x] T003 [P] Arrancar infra local: `cd asesores/pgi-service-pgi-api && npm run infra:up` (PostgreSQL + RabbitMQ)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Esquema de datos y migración legacy. Bloquea toda la implementación.

**⚠️ CRITICAL**: Ningún trabajo de US1 puede comenzar hasta que esta fase termine.

- [x] T004 [US1] Crear entity `ClientTeam` en `asesores/pgi-service-pgi-api/src/domain/models/client-team.ts` (campos: id uuid, client FK, department enum, startDate date, endDate date nullable, createdBy varchar, createdAt/updatedAt timestamptz, índice parcial único `(client_id, department) WHERE end_date IS NULL`)
- [x] T005 [US1] Extender entity `ClientAssignment` en `asesores/pgi-service-pgi-api/src/domain/models/client-assignment.ts` (añadir `percentage: number` smallint NOT NULL DEFAULT 100 CHECK 1–100; `team?: ClientTeam` FK nullable)
- [x] T006 [US1] Generar migración con `cd asesores/pgi-service-pgi-api && npx mikro-orm migration:create` y verificar que cubre T004+T005. Editar la migración para añadir manualmente: (a) índice parcial único `idx_client_team_active`, (b) bloque de migración de datos legacy (ver plan.md → "Migración de datos legacy") en `asesores/pgi-service-pgi-api/src/migrations/Migration<timestamp>_add_client_team.ts`
- [x] T007 [US1] Verificar que `npx mikro-orm migration:create --dump` devuelve "No changes required" tras T006 (idempotencia del snapshot)
- [x] T008 [US1] Aplicar migración en local: `cd asesores/pgi-service-pgi-api && npm run migrations:up`

**Checkpoint**: Esquema en BD + datos legacy migrados a equipos implícitos. La capa de dominio puede arrancar.

---

## Phase 3: User Story 1 — Crear y gestionar el equipo de un cliente (Priority: P1) 🎯 MVP

**Goal**: Un responsable puede abrir la ficha de un cliente, crear/gestionar el equipo (asignar coordinador opcional, ≥1 asesor, técnicos), asignar porcentajes (default 100%) y confirmar el equipo con validación del 100% por rol. Asesores y técnicos ven el equipo en solo lectura.

**Independent Test**: Abrir la ficha de un cliente sin equipo → crear equipo con 1 asesor al 100% → commit → equipo activo visible. Cubre AC-1 a AC-4 del spec.

### DTOs y errores compartidos

- [x] T009 [P] [US1] Crear DTOs de creación/listado/resumen de equipo en `asesores/pgi-service-pgi-api/src/application/rest/client-teams/dto/` (`create-team-dto.ts`, `team-response-dto.ts`, `active-team-summary-dto.ts`)
- [x] T010 [P] [US1] Crear DTOs de miembros en `asesores/pgi-service-pgi-api/src/application/rest/client-teams/dto/` (`add-member-dto.ts`, `update-percentage-dto.ts`, `member-response-dto.ts`, `validation-result-dto.ts`)
- [x] T011 [P] [US1] Crear códigos de error de dominio en `asesores/pgi-service-pgi-api/src/domain/constants/client-team-errors.ts` (ACTIVE_TEAM_EXISTS, DATE_NOT_MONTH_BOUNDARY, PERCENTAGE_VALIDATION_FAILED, PERCENTAGE_OUT_OF_RANGE, ROLE_ALREADY_FILLED, ROLE_CONFLICT, MIN_ASESOR_REQUIRED, TEAM_CLOSED)

### Domain service — `ClientTeamsService`

- [x] T012 [US1] Crear `ClientTeamsService` con métodos `createTeam`, `listByClient`, `getActiveSummary`, `findById` en `asesores/pgi-service-pgi-api/src/domain/services/client-teams/client-teams.service.ts` (usa `em.fork()` para writes; lanza `ACTIVE_TEAM_EXISTS` si ya hay equipo activo para `client+dept`). Depende de T004
- [x] T013 [US1] Helper `validateMonthBoundary(date, mode: 'start' | 'end')` extraído como función pura en `asesores/pgi-service-pgi-api/src/domain/services/client-teams/helpers/validate-month-boundary.helper.ts` (+ `.spec.ts` colocado, 7 tests pasando) y cableado en `createTeam`. Sigue la regla `domain-layer.md` de helpers en `helpers/`.
- [x] T014 [US1] Añadir método `addMember(teamId, dto)` en `ClientTeamsService` que crea un `ClientAssignment` con `team_id`, sin validar la suma del 100% (modelo borrador). Valida rol único responsable/coordinador (lanza `ROLE_ALREADY_FILLED` / `ROLE_CONFLICT`), TEAM_CLOSED si team.endDate, rango 1–100 (`PERCENTAGE_OUT_OF_RANGE`), y month-boundary en dateFrom/dateTo. Depende de T005
- [x] T015 [US1] Añadir método `updateMemberPercentage(assignmentId, dto)` en `ClientTeamsService` (transaccional: cierra fila vieja con `dateTo = effectiveFrom - 1d`, crea fila nueva con nuevo `percentage`; valida rango + boundary; TEAM_CLOSED; 404 si no existe). TDD: 6 tests.
- [x] T016 [US1] Añadir método `removeMember(assignmentId, { effectiveTo? })` en `ClientTeamsService` — soft delete (set `dateTo`); valida boundary 'end'; default último día del mes actual; TEAM_CLOSED + 404; no valida suma ni min-asesor (modelo borrador, ADR-0007). Contrato DELETE actualizado para reflejar esto. TDD: 6 tests.
- [x] T017 [US1] Añadir método `validateTeam(teamId): ValidationResultDto` en `ClientTeamsService` — informativo, no lanza ni publica. Filtra miembros activos (`dateTo` null o > now), suma ASESOR+TECNICO (excluye RESPONSABLE/COORDINADOR), comprueba ≥1 asesor activo. TDD: 7 tests.
- [ ] T018 [US1] Añadir método `commitTeam(teamId)` en `ClientTeamsService` que invoca `validateTeam`, lanza `PERCENTAGE_VALIDATION_FAILED` / `MIN_ASESOR_REQUIRED` si falla, marca el equipo como confirmado y publica `backoffice-api.v1.client-assignment.updated` (un evento por miembro activo, incluyendo `percentage`)
- [ ] T019 [US1] Extender `ClientAssignmentsService` en `asesores/pgi-service-pgi-api/src/domain/services/client-assignments/client-assignments.service.ts` para incluir `percentage` y `teamId` en las respuestas existentes

### Controllers + permisos

- [ ] T020 [US1] Crear `ClientTeamsController` con los endpoints del contrato en `asesores/pgi-service-pgi-api/src/application/rest/client-teams/client-teams.controller.ts`: `GET/POST /v1/client-teams/:clientId/department/:dept`, `GET/POST /v1/client-teams/:clientId/:teamId/members`, `PATCH/DELETE /v1/client-teams/:clientId/:teamId/members/:id`, `POST /v1/client-teams/:clientId/:teamId/validate`, `POST /v1/client-teams/:clientId/:teamId/commit`, `GET /v1/client-teams/:clientId/department/:dept/active-summary`. Guards: `CLIENT_ASSIGNMENT_VIEW` (lectura) y `CLIENT_ASSIGNMENT_EDIT + CLIENT_ASSIGNMENTS_{DEPT}_EDIT` (escritura). Depende de T012–T018
- [ ] T021 [US1] Registrar `ClientTeamsController` y `ClientTeamsService` como providers en `asesores/pgi-service-pgi-api/src/app.module.ts` (sin nuevo módulo — todo en `AppModule` por constitución I)
- [ ] T022 [US1] Extender `ClientAssignmentsController` en `asesores/pgi-service-pgi-api/src/application/rest/client-assignments/client-assignments.controller.ts` para devolver `percentage` y `teamId` en `GET /v1/client-assignments/:clientId/department/:dept`. Depende de T019

### Tests (testcontainers — colocados junto al service/controller)

> Convención del repo: los tests con testcontainers viven junto al fichero que prueban (`*.service.spec.ts` en `domain/services/<feature>/`, `*.controller.spec.ts` en `application/rest/<feature>/`). No hay `test/integration/`.

- [x] T023 [P] [US1] Tests de creación de equipo en `asesores/pgi-service-pgi-api/src/domain/services/client-teams/client-teams.service.spec.ts` — bloque "createTeam" (cubre AC-1: 1 asesor 100% → activo; AC-4: segundo equipo activo mismo cliente+dept → `ACTIVE_TEAM_EXISTS`; `DATE_NOT_MONTH_BOUNDARY` cuando startDate no es primer día de mes). 18 tests verdes incluyendo `addMember`, `findById`, `listByClient`, `getActiveSummary`.
- [ ] T024 [P] [US1] Tests de gestión de miembros en el mismo `client-teams.service.spec.ts` — `addMember` ya cubierto en T023; pendiente `updatePercentage` (T015) y `removeMember` (T016) — añadir cuando se implementen esos métodos.
- [ ] T025 [P] [US1] Tests de validación y commit en el mismo `client-teams.service.spec.ts` — bloques "validateTeam / commitTeam" (cubre AC-2: suma total (asesores + técnicos) ≠ 100 → `PERCENTAGE_VALIDATION_FAILED` al commit; commit ok con 60% asesor + 40% técnico → publica `backoffice-api.v1.client-assignment.updated` con `percentage`; ≥1 asesor obligatorio en commit; responsable/coordinador NO entran en la suma)
- [ ] T026 [P] [US1] Tests de controller + permisos en `asesores/pgi-service-pgi-api/src/application/rest/client-teams/client-teams.controller.spec.ts` con Supertest + mocks de servicio (cubre AC-3: asesor/técnico → GET ok, POST/PATCH/DELETE → 403; DTO validation → 400)
- [ ] T027 [P] [US1] Tests de migración legacy en `asesores/pgi-service-pgi-api/src/migrations/Migration20260528122459.spec.ts` (semilla con asignaciones legacy 1-a-1 → aplicar migración → verifica que cada client+dept tiene un `ClientTeam` activo y que `client_assignment.team_id` apunta a él; idempotencia: ejecutar 2 veces produce el mismo estado)
- [ ] T028 [P] [US1] Tests del endpoint de history extendido en `asesores/pgi-service-pgi-api/src/application/rest/client-assignments/client-assignments.controller.spec.ts` (GET devuelve `percentage` y `teamId`)

### Frontend — Tab Asignaciones en la ficha

> Convención del repo: cada feature usa Clean Architecture en 4 capas (`domain/`, `infrastructure/`, `application/use-cases/`, `presentation/`). Filenames en kebab-case con sufijos `.model.ts`, `.repository.ts`, `-dto.ts`, `.use-case.ts`. Patrón espejado de `features/client-assignments/`.

- [ ] T029 [P] [US1] Crear modelos e interfaces de dominio en `asesores/pgi-app-pgi-web/src/features/client-teams/domain/models/client-team.model.ts`, `domain/models/team-member.model.ts` y `domain/interfaces/client-team-payloads.d.ts` (ClientTeam, TeamMember, payloads de create/add/update/commit)
- [ ] T030 [P] [US1] Crear interface de repositorio + implementación HTTP en `asesores/pgi-app-pgi-web/src/features/client-teams/domain/repositories/client-teams.repository.ts` (interface) y `infrastructure/client-teams.repository-impl.ts` (axios calls a los endpoints del contrato) + DTOs en `infrastructure/dto/client-team-dto.ts`, `member-dto.ts`, `active-team-summary-dto.ts`, `validation-result-dto.ts`
- [ ] T031 [P] [US1] Crear use-cases en `asesores/pgi-app-pgi-web/src/features/client-teams/application/use-cases/` (`create-team.use-case.ts`, `add-member.use-case.ts`, `update-percentage.use-case.ts`, `remove-member.use-case.ts`, `validate-team.use-case.ts`, `commit-team.use-case.ts`, `get-active-team-summary.use-case.ts`, `composition-root.ts`, `index.ts`) + schema Zod cross-field en `presentation/utils/team-validation.schema.ts` (suma total ASESOR+TECNICO = 100; rango 1–100; ≥1 asesor; responsable/coordinador excluidos)
- [ ] T032 [P] [US1] Crear componente en `asesores/pgi-app-pgi-web/src/features/client-teams/presentation/components/percentage-sum-indicator/percentage-sum-indicator.tsx` (recibe `sum`; verde si 100, rojo si ≠100, texto "Equipo: X/100%")
- [ ] T033 [US1] Crear componente en `asesores/pgi-app-pgi-web/src/features/client-teams/presentation/components/team-member-form/team-member-form.tsx` (TanStack Form field array; selector empleado + rol + percentage + dateFrom; submit añade miembro al borrador). Depende de T029, T030, T031
- [ ] T034 [US1] Crear componente en `asesores/pgi-app-pgi-web/src/features/client-teams/presentation/components/team-member-list/team-member-list.tsx` (tabla con miembros activos, acciones eliminar/editar % en modo edición). Depende de T029, T030
- [ ] T035 [US1] Crear componente contenedor en `asesores/pgi-app-pgi-web/src/features/client-teams/presentation/components/team-section/team-section.tsx` (resumen, lista de miembros, formulario, botones "Guardar borrador" y "Confirmar equipo" → llama a `commit-team.use-case`; modo readonly para asesor/técnico). Depende de T032, T033, T034
- [ ] T036 [US1] Añadir tab `Asignaciones` en `asesores/pgi-app-pgi-web/src/features/clients/presentation/components/client-profile-tabs/client-profile-tabs.tsx` apuntando a `TeamSection` con gating de permisos: visible siempre, edición según `CLIENT_ASSIGNMENT_EDIT`.

### Frontend tests (Vitest)

- [ ] T037 [P] [US1] Tests en `asesores/pgi-app-pgi-web/src/features/client-teams/presentation/components/percentage-sum-indicator/percentage-sum-indicator.test.tsx` (verde/rojo según suma)
- [ ] T038 [P] [US1] Tests en `asesores/pgi-app-pgi-web/src/features/client-teams/presentation/components/team-member-form/team-member-form.test.tsx` (validación Zod, submit deshabilitado fuera de rango, suma calculada correctamente)
- [ ] T039 [P] [US1] Tests en `asesores/pgi-app-pgi-web/src/features/client-teams/presentation/components/team-section/team-section.test.tsx` (AC-3: asesor/técnico → no ve botones de edición; AC-1: flujo completo crear → añadir asesor → commit)

**Checkpoint**: US1 funcional end-to-end. Tests pasando. Listo para PR.

---

## Phase 4: Polish & Cross-Cutting Concerns

- [ ] T040 [P] Ejecutar `quickstart.md` contra entorno local y verificar los smoke tests del paso 3
- [ ] T041 [P] Pre-push gate backend: `cd asesores/pgi-service-pgi-api && npm run lint && npm run build && npm test`
- [ ] T042 [P] Pre-push gate frontend: `cd asesores/pgi-app-pgi-web && npm run build && npx vitest run src/features/client-teams/presentation/components`
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
