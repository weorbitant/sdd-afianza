# Tasks: Asignaciones Múltiples — US1 (Crear y gestionar el equipo de un cliente)

**Input**: Design documents from `/specs/001-client-team-assignments/`
**Branch**: `feat/001-client-team-assignments-us1` (a crear desde `main` antes de empezar)
**Scope**: solo **US1 (P1)**. US2/US3/US4 fuera de scope.

## Format

`[ID] [P?] [Story?] Description con ruta absoluta o relativa al repo root`

- **[P]**: paralelizable (archivos distintos, sin dependencia con tareas no completadas)
- **[Story]**: `[US1]` en este plan (otras stories en iteraciones futuras)
- **TDD obligatorio**: en cada bloque de implementación, el test correspondiente se escribe **antes** que el código. El test debe **fallar** primero (red), luego pasar (green), luego refactor.

---

## Phase 1 — Setup

**Purpose**: branch, infra y baseline.

- [ ] T001 Crear branch `feat/001-client-team-assignments-us1` desde `main` (`git checkout -b feat/001-client-team-assignments-us1`).
- [ ] T002 Arrancar infra local del backend (`cd asesores/pgi-service-pgi-api && npm install && npm run infra:up`).
- [ ] T003 Verificar baseline de migraciones (`cd asesores/pgi-service-pgi-api && npx mikro-orm migration:check`) — exit 0 = en sync. Si exit 1 sobre `main` limpio, parar y avisar.
- [ ] T004 [P] Arrancar frontend (`cd asesores/pgi-app-pgi-web && npm install && npm run dev`) y comprobar que ficha de cliente carga.

---

## Phase 2 — Foundational (Blocking)

**Purpose**: cambios de esquema + helpers puros que necesitan TODAS las tareas de US1.

**⚠️ CRITICAL**: ninguna tarea de US1 puede empezar hasta que esta fase esté verde.

### Tests primero (TDD)

- [ ] T005 [P] Escribir `asesores/pgi-service-pgi-api/src/domain/services/client-teams/helpers/assert-month-boundary.helper.spec.ts` — cubre: primer día de mes válido, día 15 inválido, último día de mes válido para modo `end`, edge case Feb 28/29.
- [ ] T006 [P] Escribir `asesores/pgi-service-pgi-api/src/domain/services/client-team-assignments/helpers/sum-coverage-percentage.helper.spec.ts` — cubre: cobertura asesores suma 100% con 2 asesores 60+40, cobertura técnicos suma 100% con 4 técnicos 25%, cobertura vacío devuelve `null` (no aplicable), excluye filas con `dateTo IS NOT NULL`, excluye filas de otros departamentos.
- [ ] T007 [P] Escribir `asesores/pgi-service-pgi-api/src/domain/services/client-teams/helpers/compute-team-status.helper.spec.ts` — cubre: `incomplete` sin responsable, `incomplete` sin asesor, `incomplete` sin primary advisor único, `incomplete` con cobertura asesor ≠ 100%, `active` cuando todo se cumple, `closed` cuando `endDate IS NOT NULL`, cobertura técnico N/A no bloquea.

### Implementación de helpers (después de T005-T007)

- [ ] T008 [P] Implementar `asesores/pgi-service-pgi-api/src/domain/services/client-teams/helpers/assert-month-boundary.helper.ts` hasta que T005 pase verde.
- [ ] T009 [P] Implementar `asesores/pgi-service-pgi-api/src/domain/services/client-team-assignments/helpers/sum-coverage-percentage.helper.ts` hasta que T006 pase verde.
- [ ] T010 [P] Implementar `asesores/pgi-service-pgi-api/src/domain/services/client-teams/helpers/compute-team-status.helper.ts` hasta que T007 pase verde.

### Schema + migraciones

- [ ] T011 Modificar entidad `asesores/pgi-service-pgi-api/src/domain/models/client-team.ts`: añadir `version: number` (smallint, default 1) y `createdBy: string`. NO añadir `name` (PO 2026-06-01 lo descartó).
- [ ] T012 Modificar entidad `asesores/pgi-service-pgi-api/src/domain/models/client-assignment.ts`: añadir `isPrimaryAdvisor: boolean` (default false), `createdBy: string`, `createdAt: Date`, `version: number`. Mantener unique existente.
- [ ] T013 Generar migración DDL (`cd asesores/pgi-service-pgi-api && npm run migrations:create`). Revisar SQL: debe incluir columnas nuevas. **Editar a mano** para añadir `CHECK (is_primary_advisor = false OR role = 'asesor')` y `CREATE UNIQUE INDEX ... ON client_assignment (client_id, employee_id) WHERE date_to IS NULL` (MikroORM no genera partial unique). Nombrar `Migration20260603xxxx-add-version-and-primary-advisor.ts`.
- [ ] T014 Aplicar migración local (`npm run migrations:up`) y verificar `migration:check` exit 0 + `migration:create --dump` devuelve "No changes required".

### Migración legacy (FR-013) — TDD

- [ ] T015 Escribir test E2E `asesores/pgi-service-pgi-api/test/e2e/legacy-backfill.e2e-spec.ts` con testcontainers: seed con N filas `client_assignment` activas + `team_id NULL` agrupadas en 3 combos `(client, department)`, ejecuta la migración, verifica que crea 3 `client_team` con `created_by='system:migration'`, todas las filas tienen `team_id` no nulo, primer asesor por grupo tiene `is_primary_advisor=true`. Re-ejecutar migración debe ser noop (idempotencia).
- [ ] T016 Implementar `asesores/pgi-service-pgi-api/src/migrations/Migration20260603xxxy-backfill-legacy-team-id.ts` hasta que T015 pase verde. `down()` = noop.

**Checkpoint**: foundation lista — implementación de US1 puede empezar.

---

## Phase 3 — User Story 1 (Priority: P1) 🎯 MVP

**Goal**: un responsable abre la ficha de un cliente sin equipo, añade responsable + asesor (con `isPrimaryAdvisor`), guarda y ve el equipo `active`. Endpoints rechazan a usuarios sin permiso. Optimistic concurrency vía `If-Match`. FR-017 (provided service) y FR-021 (partial unique) cumplidos.

**Independent Test**: ver `quickstart.md § 6. Smoke test manual`.

### Backend — Tests primero (TDD)

#### Validators / helpers de dominio adicionales

- [ ] T017 [P] [US1] Escribir `asesores/pgi-service-pgi-api/src/domain/services/client-team-assignments/helpers/assert-provided-service-active.helper.spec.ts` — cubre FR-017: rechaza cuando no hay `ProvidedService` activo con `family` matching, acepta cuando hay al menos uno.
- [ ] T018 [P] [US1] Escribir `asesores/pgi-service-pgi-api/src/domain/services/client-team-assignments/helpers/assert-no-conflicting-active-assignment.helper.spec.ts` — cubre FR-021/FR-016: rechaza si el empleado ya tiene asignación activa al mismo cliente (mismo o distinto dept).
- [ ] T019 [P] [US1] Implementar `assert-provided-service-active.helper.ts` hasta que T017 pase.
- [ ] T020 [P] [US1] Implementar `assert-no-conflicting-active-assignment.helper.ts` hasta que T018 pase.

#### Servicios de dominio (integration tests con testcontainers)

- [ ] T021 [US1] Escribir `asesores/pgi-service-pgi-api/src/domain/services/client-teams/client-teams.service.spec.ts` con testcontainers postgres. Casos: `create` con `startDate` no-boundary → error 422, `create` con dept sin ProvidedService activo → 422, `create` ok → fila persistida con `version=1` y `createdBy`. `findByClientId` filtra closed según flag.
- [ ] T022 [US1] Implementar `asesores/pgi-service-pgi-api/src/domain/services/client-teams/client-teams.service.ts` hasta que T021 pase. Usar `em.fork()` en writes, `disableIdentityMap: true` en reads (Constitution III).
- [ ] T023 [US1] Escribir `asesores/pgi-service-pgi-api/src/domain/services/client-team-assignments/client-team-assignments.service.spec.ts` con testcontainers. Casos:
  - `create` con `role=asesor`, `isPrimaryAdvisor=true`, `percentage=100` → ok.
  - `create` viola partial unique (mismo empleado, mismo cliente, otro dept) → 422 `CLIENT_ASSIGNMENT_DUPLICATE_ACTIVE`.
  - `create` con `client_id` ≠ `team.client_id` → 422 `CLIENT_ASSIGNMENT_TEAM_MISMATCH`.
  - `update` solo permite `percentage` y `dateTo` (intentar cambiar `role` → 422 / ignorado).
  - `update` con `If-Match` stale → 409 `CLIENT_TEAM_VERSION_CONFLICT`.
  - `closeAssignment` setea `dateTo` (no DELETE físico).
  - `promotePrimary` demote del primary actual + promote del nuevo en la misma transacción.
  - Tras crear todos los miembros mínimos, equipo transiciona a `active` y se llama a `rabbitMQService.publish('clientAssignmentUpdated', ...)`.
  - Mientras está `incomplete`, NO se publica (verificar con spy en `rabbitMQService.publish`).
- [ ] T024 [US1] Implementar `asesores/pgi-service-pgi-api/src/domain/services/client-team-assignments/client-team-assignments.service.ts` hasta que T023 pase. Envolver POST/PATCH/DELETE/promote en `em.fork()` + `em.transactional()` para evitar carrera en recomputo de coberturas.
- [ ] T025 [US1] Ampliar `asesores/pgi-service-pgi-api/src/domain/constants/client-team-errors.ts` con los códigos de `data-model.md § Errores y códigos`.

### Backend — REST controllers (Supertest)

- [ ] T026 [P] [US1] Escribir `asesores/pgi-service-pgi-api/src/application/rest/client-teams/client-teams.controller.spec.ts` con Supertest + domain service mockeado. Casos: GET sin auth → 401, GET sin `CLIENT_ASSIGNMENT_READ` → 403, POST sin `CLIENT_ASSIGNMENT_EDIT` → 403, POST con body inválido (DTO falla) → 400, POST ok → 201 y body matches schema.
- [ ] T027 [US1] Implementar DTOs `create-client-team.dto.ts`, `client-team-response.dto.ts` en `asesores/pgi-service-pgi-api/src/application/rest/client-teams/dto/` y `client-teams.controller.ts`. Endpoints según `contracts/client-teams.openapi.yaml`. Aplicar `AzureAdJwtGuard` + role guard custom. Validar que T026 pasa.
- [ ] T028 [P] [US1] Escribir `asesores/pgi-service-pgi-api/src/application/rest/client-team-assignments/client-team-assignments.controller.spec.ts`. Casos: POST/PATCH/DELETE/promote-primary con permisos correctos, 403 sin permiso, 400 con body inválido, 409 cuando service lanza `CLIENT_TEAM_VERSION_CONFLICT`.
- [ ] T029 [US1] Implementar DTOs (`create-assignment.dto.ts`, `update-assignment.dto.ts`, `assignment-response.dto.ts`) y controller `client-team-assignments.controller.ts` según `contracts/client-team-assignments.openapi.yaml`. Validar If-Match header (extraer a integer; ausencia o no-integer → 400 — consistente con la validación DTO del resto del repo). Validar que T028 pasa.

### Backend — E2E golden path

- [ ] T030 [US1] Escribir y ejecutar `asesores/pgi-service-pgi-api/test/e2e/client-team-assignments.create.e2e-spec.ts` reproduciendo el smoke test de `quickstart.md § 6`: crear team, añadir responsable + asesor primary, GET devuelve `status='active'`, verificar publish AMQP con spy.
- [ ] T031 [US1] Escribir `asesores/pgi-service-pgi-api/test/e2e/client-team-assignments.coverage-validation.e2e-spec.ts`: dos equipos Fiscal de un mismo cliente, 4 asesores al 25% en total → equipo `active`. Cambiar un asesor a 30% → equipo `incomplete` (110% en cobertura asesores), publish NO se emite.
- [ ] T032 [US1] Escribir `asesores/pgi-service-pgi-api/test/e2e/client-teams.status-transitions.e2e-spec.ts`: ciclo `incomplete → active → incomplete` por edición posterior. Verificar publish en transición a `active` y supresión en regreso a `incomplete`.

### Frontend — Tests primero (TDD)

- [ ] T033 [P] [US1] Escribir `asesores/pgi-app-pgi-web/src/features/client-team/__tests__/useClientTeam.test.ts` (Vitest + MSW): hook llama a `/clients/:id/teams`, devuelve datos parseados, refresca cuando se invalida la query.
- [ ] T034 [P] [US1] Escribir `asesores/pgi-app-pgi-web/src/features/client-team/__tests__/useUpsertAssignment.test.ts`: mutación POST/PATCH/DELETE, en 409 muestra toast *"El equipo ha cambiado, recarga..."*, invalida `useClientTeam` tras éxito.
- [ ] T035 [P] [US1] Escribir `asesores/pgi-app-pgi-web/src/features/client-team/__tests__/ClientTeamSection.test.tsx` con Testing Library: render con equipo `incomplete` muestra banner amarillo, botón Guardar deshabilitado mientras falte composición mínima (responsable + 1 asesor), botones de edición ocultos para usuario sin `CLIENT_ASSIGNMENT_EDIT`.

### Frontend — Implementación

- [ ] T036 [P] [US1] Implementar `asesores/pgi-app-pgi-web/src/features/client-team/hooks/useClientTeam.ts` hasta que T033 pase.
- [ ] T037 [P] [US1] Implementar `asesores/pgi-app-pgi-web/src/features/client-team/hooks/useUpsertAssignment.ts` hasta que T034 pase. Mandar `If-Match` con la `version` del team o assignment.
- [ ] T038 [US1] Implementar `asesores/pgi-app-pgi-web/src/features/client-team/MemberRow.tsx` y `AddMemberModal.tsx` (modal con selector de mes — FR-012 — para `dateFrom`).
- [ ] T039 [US1] Implementar `asesores/pgi-app-pgi-web/src/features/client-team/ClientTeamSection.tsx` integrando hooks + modal + banner. Validar que T035 pasa.
- [ ] T040 [US1] Integrar `ClientTeamSection` en la página de ficha de cliente existente (`src/pages/clients/ClientDetail.tsx` o equivalente — localizar y enchufar). Verificar a mano con `npm run dev`.

**Checkpoint US1**: golden path completo, todos los tests verdes, smoke test manual de `quickstart.md § 6` reproducible.

---

## Phase 4 — Polish & Cross-Cutting

- [ ] T041 [P] Ejecutar `npm run lint && npm run build && npm test` en `pgi-service-pgi-api` — debe pasar.
- [ ] T042 [P] Ejecutar `npm run build && npx vitest run` en `pgi-app-pgi-web` — debe pasar.
- [ ] T043 Generar segunda migración `Migration20260603xxxz-team-id-not-null.ts` (`ALTER TABLE client_assignment ALTER COLUMN team_id SET NOT NULL`). **NO** aplicarla en el mismo deploy — queda lista para un deploy posterior una vez verificado que no hay filas con `team_id IS NULL` en producción.
- [ ] T044 Documentar en PR description: pasos de deploy (1. apply migrations US1, 2. verificar `SELECT COUNT(*) FROM client_assignment WHERE team_id IS NULL` = 0, 3. apply migración NOT NULL en deploy siguiente).
- [ ] T045 Abrir PR con `gh pr create` enlazando DEVPT-518. Título: `feat(client-team): US1 — create and manage client teams with cobertura validation`.

---

## Dependencies

```
T001 → T002 → T003 → (T004 || resto)

Phase 2 (foundational):
  T005,T006,T007 [P] → T008,T009,T010 [P]
  T011 → T012 → T013 → T014
  T015 → T016
  (helpers + schema independientes entre sí en Phase 2 — pueden ir en paralelo en ramas distintas pero merge antes de Phase 3)

Phase 3 (US1):
  T017,T018 [P] → T019,T020 [P]
  T021 → T022 (depende de T010,T011)
  T023 → T024 (depende de T009,T012,T019,T020)
  T025 puede ir en cualquier momento de Phase 3
  T026 → T027 (depende de T022)
  T028 → T029 (depende de T024)
  T030,T031,T032 después de T027 + T029
  T033,T034,T035 [P]
  T036,T037 [P] (después de sus tests)
  T038 después de T037
  T039 después de T036,T037,T038
  T040 después de T039

Phase 4:
  T041,T042 [P] al final de Phase 3
  T043 → T044 → T045
```

## Parallel execution examples

- **Tras T004**: T005, T006, T007 en paralelo (3 helpers, 3 spec files distintos).
- **Tras T010**: T011 y T015 pueden empezar en paralelo (entity vs E2E test de migración).
- **Tras T016**: T017, T018, T026, T028, T033, T034, T035 todos en paralelo (helpers + controllers + frontend hooks/components, archivos distintos).
- **Tras T024**: T030, T031, T032 en paralelo (3 E2E independientes).

## Independent test criteria (US1)

US1 se considera "done" cuando:

1. ✅ El smoke test manual de `quickstart.md § 6` pasa de extremo a extremo.
2. ✅ Todos los tests unit/integration/E2E del backend verdes.
3. ✅ Todos los tests de frontend verdes.
4. ✅ `npm run lint && npm run build && npm test` pasa en ambos servicios.
5. ✅ Migration `migration:check` exit 0 + `migration:create --dump` devuelve "No changes required".
6. ✅ Un usuario `responsable` puede crear un equipo en un cliente sin equipo previo y verlo `active`.
7. ✅ Un usuario `asesor` (sin `CLIENT_ASSIGNMENT_EDIT`) ve el equipo pero no puede editarlo (botones ocultos + endpoint 403).
8. ✅ Crear segundo `ClientAssignment` activo para el mismo (cliente, empleado) → 422 (FR-021).
9. ✅ Crear team en dept sin `ProvidedService` activo → 422 (FR-017).
10. ✅ Concurrencia: dos requests con mismo `If-Match` — segunda recibe 409.

## Implementation strategy — MVP scope

Esta tasks.md cubre **solo US1** = MVP de la feature. US2/US3/US4 vienen en iteraciones posteriores con su propio `/speckit-plan` y `/speckit-tasks` (o ampliación de este plan, según se prefiera).

Total tasks: **45**. Suggested MVP scope: **T001..T040** + polish (T041..T045) = todo este tasks.md.
