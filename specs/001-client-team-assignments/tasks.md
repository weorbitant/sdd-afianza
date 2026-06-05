# Tasks — Client Team Assignments v2

**Feature**: 001-client-team-assignments
**Date**: 2026-06-04
**Source**: `spec.md` v2 (US-01..US-07) + `plan.md` + `research.md`

## Convenciones

- **Una tarea = un paquete coherente de trabajo** que un dev entrega a QA cuando termina. No hay micro-tasks atómicas (DTO X, repo Y) — esos quedan dentro de cada tarea como check-list interno del implementador.
- **Naming**: `T-{USXX}-{LETRA}` (ej. `T-01-A`). Las tareas comunes a varias USs van como `T-SETUP-N`.
- **Branch convention**: `feat/dev-518-{ref-task}` (ej. `feat/dev-518-t-01-a-be-endpoints`).
- **`[P]` paralelizable** con sus hermanas — no depende de la otra para arrancar.
- **DoD** = Definition of Done. Cuando el dev marca DoD ✓, el ticket pasa a QA.
- **Servicio**: `pgi-api` = `asesores/pgi-service-pgi-api`. `pgi-web` = `asesores/pgi-app-pgi-web`. `obligations` = `plataforma-del-dato/pd-service-obligations-api`.

---

## Setup compartido — base para todas las US

### T-SETUP-1 — Migraciones + entities base

**Servicio**: pgi-api
**Branch**: `feat/dev-518-setup-migrations`
**Depende de**: ninguna (cabeza del grafo de BE)

**Qué hace**
Sienta la base de schema para toda la feature: añade campos de audit a `client_team`, crea `client_team_assignment` y `client_team_assignment_change` con sus CHECKs e índices, y declara las entities TypeScript correspondientes. Define también las constantes de error.

**Cómo funciona**
Tres migraciones consecutivas en `src/migrations/` (numeración correlativa del repo):
1. `add-client-team-audit-fields`: `ALTER client_team` añadiendo `created_by`, `updated_by`, `version`. **No** se tocan `start_date`/`end_date` (DROP COLUMN se difiere a deploy posterior — R-03).
2. `create-client-team-assignment`: tabla con CHECKs (`cta_role_enum`, `cta_percentage_range`, `cta_main_only_asesor`) e índices (`cta_team_active`, `cta_employee_active`). **Sin** `created_by`/`updated_by` (el "quién" vive en `client_team_assignment_change`).
3. `create-client-team-assignment-change`: tabla con columnas before/after por campo, audit propio (`created_at`/`updated_at`/`created_by`/`updated_by`), CHECK del enum `action` (incluye `voided`), índices (`cta_change_by_assignment`, `cta_change_recent`).

Entities `ClientTeam`, `ClientTeamAssignment`, `ClientTeamAssignmentChange` en `src/domain/models/`. Constantes de error en `src/domain/constants/client-team-errors.ts`.

**Qué NO entra aquí**
- Helpers de dominio (`compute-team-status`, etc.) → T-01-A.
- Service / controller → T-01-A.
- DROP COLUMN `start_date`/`end_date` de `client_team` → deploy B (R-03).

**Cómo verificar**
- `npx mikro-orm migration:check` tras crear las 3 migraciones → "No changes required".
- `npm test` ✓ en pgi-api (los tests existentes no rompen).
- Smoke en BD local: `\d client_team_assignment`, `\d client_team_assignment_change` muestran las CHECKs y los índices esperados.

**DoD**
- Migraciones aplicadas en local + tests integration siguen verdes.
- Entities exportadas y referenciables desde domain services.
- PR mergeada a main.

---

### T-SETUP-2 [P] — Contracts cerrados y publicados

**Servicio**: documentación (no toca código de servicios)
**Branch**: `feat/dev-518-setup-contracts`
**Depende de**: ninguna (paralelo a T-SETUP-1)

**Qué hace**
Deja los contracts OpenAPI/AMQP en estado revisable y publicado, de forma que el equipo FE pueda arrancar con Prism mock antes de que el BE esté mergeado.

**Cómo funciona**
- Pasar `npx @redocly/cli lint` sobre `contracts/rest/client-assignments.openapi.yaml` y arreglar lo que reporte.
- Pasar `npx ajv-cli validate` sobre cada `contracts/amqp/*.schema.json`.
- Verificar nombres de routing keys (`pgi-api.v1.client-team-assignment.opened`/`closed`, `client-onboarding-assignment`) contra constitution P-IV.
- Levantar Prism (`prism mock contracts/rest/client-assignments.openapi.yaml`) en una URL accesible al equipo FE.

**Qué NO entra aquí**
- Implementación BE de los endpoints (T-01-A, T-02-A.*).
- Generación del cliente API tipado en pgi-web (T-02-B.1).

**Cómo verificar**
- `npx @redocly/cli lint` ✓ (0 errores).
- `npx ajv-cli` ✓ en los 3 schemas AMQP.
- FE confirma que su `npm run dev` arranca con Prism y los endpoints responden con ejemplos válidos.

**DoD**
- Linters verdes.
- FE confirma mock funcional.

---

## US-01 — Alta inicial del equipo desde la UI · MVP P1

### T-01-A — BE: controller + service + helpers + publisher AMQP para alta y lectura

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-01-a-be`
**Depende de**: T-SETUP-1, T-SETUP-2

> **Nota**: si en revisión esta tarea queda > ~400 líneas de diff, valorar partirla en T-01-A.1 (helpers de dominio puros) + T-01-A.2 (controller + service + AMQP). De momento se mantiene como una sola para no inflar el plan; el dev decide al implementar.

**Qué hace**
Implementa los 3 endpoints REST de US-01 (POST crear, GET listar vigente, GET por id) con su lógica de servicio, helpers de dominio y publisher AMQP. Inserta filas en `client_team_assignment_change` con `action='opened'` en la misma transacción que el INSERT del tramo.

**Cómo funciona**
- Controller `client-team-assignments.controller.ts` con base path nested bajo cliente (`@Controller({ path: 'clients', version: '1' })`). Endpoints expuestos:
  - `POST /api/v1/clients/{clientId}/team-assignments` (auto-crea `ClientTeam` si no existe). Response 201 `{ id }`. Permission `CLIENT_ASSIGNMENT_EDIT`.
  - `GET /api/v1/clients/{clientId}/team-assignments?department={dept}&date={date?}` (default hoy; acepta pasado y futuro). Response `{ data, total, coverage, mainAsesorPresent, status }` con `inClientSince` por miembro. Permission `CLIENT_ASSIGNMENT_VIEW`.
  - `GET /api/v1/clients/{clientId}/team-assignments/{id}` recupera asignación concreta.
- Service `client-team-assignments.service.ts` con `em.fork()` + `em.transactional()` y `SELECT … FOR UPDATE` sobre `client` (FR-024). En la misma transacción del POST inserta también la fila en `client_team_assignment_change` con `action='opened'`.
- Helpers de dominio en `src/domain/helpers/`: `compute-team-status`, `sum-coverage-percentage`, `assert-single-main-asesor`, `assert-provided-service-active`, `publish-assignment-events`, `compute-in-client-since`.
- Publisher AMQP `pgi-api.v1.client-team-assignment.opened` (payload según `contracts/amqp/client-team-assignment.opened.schema.json`).
- Errores con NestJS exceptions built-in (`NotFoundException`, `ConflictException`, `UnprocessableEntityException`, `BadRequestException`). Shape `{ statusCode, message, error }`. Mensajes en español.
- DTOs con `class-validator` + `@ApiProperty` en `dto/`. Response DTO incluye `inClientSince`.

**Qué NO entra aquí**
- Pantalla, hooks de React → T-01-B.
- Edición de miembros existentes → T-02-A.*.
- Endpoint del log de cambios → T-05-A.
- Subscriber AMQP de onboarding → T-04-A.

**Cómo verificar**

Tests integration con testcontainers cubriendo los 6 criterios de US-01:

| # | Criterio | Verifica |
|---|---|---|
| 1 | Equipo vacío → botón "Crear equipo" disponible | GET vacío devuelve `data: []`, `status: incomplete`. |
| 2 | Alta de responsable + coordinador + asesor main | 3 POST devuelven 201; GET muestra los 3. 3 filas en change. |
| 3 | Tras alta del main, `status: complete` | Cobertura 100% en el GET. |
| 4 | POST sin `ProvidedService` activo | 422 con mensaje en español. Nada persistido. |
| 5 | Cobertura técnica N/A sin técnicos | `coverage.tecnicos: null` en el GET. |
| 6 | GET con `date` pasada con histórico no trivial | Devuelve estado vigente a esa fecha; `inClientSince` correcto. |

Verificación adicional: tras el POST, evento AMQP visible en RabbitMQ Management UI; fila en `client_team_assignment_change` con `created_by` = email del request user.

**DoD**
- `npm run lint && npm run build && npm test` ✓ en pgi-api.
- Los 6 tests de la tabla en CI.
- Smoke manual: `curl POST` × 3 + `curl GET?date=hoy` devuelve `status: complete`.

---

### T-01-B [P] — FE: pantalla del equipo + modal alta miembro + E2E

**Servicio**: pgi-web
**Branch**: `feat/dev-518-t-01-b-fe`
**Depende de**: T-SETUP-2. Puede arrancar con Prism mock antes de que T-01-A esté mergeado.

**Qué hace**
Implementa la pantalla de equipo en la ficha del cliente con el modal de alta de miembros, el selector de fecha (para US-01 criterio 6 "ver equipo a fecha pasada") y los E2E que cubren los 6 criterios.

**Cómo funciona**
- Cliente API tipado generado del OpenAPI (`contracts/rest/client-assignments.openapi.yaml`).
- Componentes con MUI v6: `ClientTeamPage` (contenedor con tabs fiscal/laboral), `ClientTeamView` (lista vigente + banner amarillo "equipo incompleto" + selector "ver equipo a fecha…"), `MemberRow` (empleado, rol, %, `inClientSince`, badge "main"), `AddMemberModal` (selector empleado/rol/%, `isMain` solo activable si `role='asesor'`).
- Hooks TanStack Query: `useTeamAssignments({ clientId, department, date? })`, `useAddAssignment()` con invalidación automática del listado tras éxito.
- Manejo de errores del shape NestJS: 422 → toast con `message` del backend; 409 → refetch + reintento; otros → toast genérico.

**Qué NO entra aquí**
- Edición de miembros existentes → T-02-B.*.
- Log de cambios → T-05-B.
- E2E del flujo onboarding AMQP → no aplica (US-04 no toca UI directamente).

**Cómo verificar**

Tests Vitest + Testing Library en `components/__tests__/` y `hooks/__tests__/`:

| # | Caso | Verifica |
|---|---|---|
| 1 | Abrir cliente vacío | Botón "Crear equipo fiscal" visible; banner "equipo incompleto" amarillo. |
| 2 | Alta de miembro con `isMain` | Modal envía body correcto; tras éxito el listado se refresca. |
| 3 | `isMain` deshabilitado si rol ≠ asesor | El checkbox no se puede marcar. |
| 4 | Toast con 422 | Mensaje del backend visible. |
| 5 | Cambio de selector "ver equipo a fecha" | Nueva query con `date=` y la UI muestra el equipo de ese día. |

**E2E Playwright** (`e2e/team-assignments/initial-setup.spec.ts`): siguiendo el §7.1 de la spec (alta Perico + Alberto + Alfonso con fecha 20/05/2026), verifica que tras 3 altas la cobertura llega al 100%, el banner desaparece y el listado muestra los 3 con `inClientSince`.

**DoD**
- `npm run build && npx vitest run` ✓ en pgi-web.
- E2E Playwright verde contra instancia local de pgi-api con BD limpia.
- Demo manual al PO siguiendo §7.1.

---

## US-02 — Editar el equipo en el mes en curso · MVP P1

> US-02 se entrega en **7 sub-tasks** (4 BE + 3 FE) para que cada PR sea revisable de forma independiente. La Story Jira sigue siendo única (DEVPT-574); estos sub-tasks cuelgan de ella.

### T-02-A.1 — Helper `normalize-month-boundary` + tests unit

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-02-a-1-normalize-helper`
**Depende de**: T-SETUP-1

**Qué hace**
Helper puro `normalize-month-boundary.helper.ts` que valida y redondea fechas para todo el flujo temporal: comprueba que una fecha sea primer día de mes (mes en curso o futuro) y rechaza meses pasados.

**Cómo funciona**
Exporta dos funciones: `assertFirstDayOfMonth(date)` lanza `UnprocessableEntityException` con mensaje en español si la fecha no cumple; `lastDayOfPreviousMonth(date)` devuelve la fecha de cierre que corresponde para un `dateFrom` dado (`date - 1 día`, garantizando que cae en el último día del mes anterior). Sin estado, sin dependencias de NestJS más allá del exception type.

**Qué NO entra aquí**
- Uso del helper en los endpoints — eso ocurre en T-02-A.2/A.3/A.4.
- Lógica de void FR-007 — T-02-A.4.
- Soporte de "mes futuro con preservación de tramos previos" (FR-006-bis) — US-03.

**Cómo verificar**
Tests unit en `helpers/__tests__/normalize-month-boundary.spec.ts`:

| # | Input | Salida esperada |
|---|---|---|
| 1 | `assertFirstDayOfMonth(2026-06-01)` con hoy 15/06 | ok |
| 2 | `assertFirstDayOfMonth(2026-06-15)` | throw 422 "debe ser primer día de mes" |
| 3 | `assertFirstDayOfMonth(2026-05-01)` con hoy 15/06 | throw 422 "no se pueden modificar asignaciones del pasado" |
| 4 | `assertFirstDayOfMonth(2026-09-01)` con hoy 15/06 | ok (mes futuro permitido) |
| 5 | `lastDayOfPreviousMonth(2026-06-01)` | `2026-05-31` |
| 6 | `lastDayOfPreviousMonth(2026-03-01)` | `2026-02-28` (no bisiesto) |

**DoD**
- `npx jest --testPathPattern=normalize-month-boundary` ✓.
- Mensajes de error en español.
- Sin dependencias del EM / servicios.

---

### T-02-A.2 — Endpoint `PUT colección` con diff atómico y log de cambios

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-02-a-2-put-colection`
**Depende de**: T-SETUP-1, T-01-A, T-02-A.1

**Qué hace**
Implementa `PUT /api/v1/clients/{clientId}/team-assignments?department={dept}&dateFrom={YYYY-MM-DD}` con body `{ members: [{ employeeId, role, percentage, isMain }, ...] }`. Aplica el estado deseado del equipo a partir de `dateFrom`, resolviendo close+open de los tramos afectados en una sola transacción. Response 204.

**Cómo funciona**
1. Validar `dateFrom` con el helper de T-02-A.1.
2. `SELECT … FOR UPDATE` sobre la fila `client` (FR-024).
3. Leer estado vigente del equipo en `dateFrom - 1 día`.
4. Diff contra `members[]` del body:
   - Match exacto `(employeeId, role, percentage, isMain)` → sin cambios.
   - Aparece pero no existía o difiere → INSERT con `dateFrom`.
   - Existía pero no aparece → UPDATE cerrando con `dateTo = dateFrom - 1 día`.
5. Por cada mutación, insertar fila en `client_team_assignment_change` (`action='opened'` o `'closed'`) con `created_by` = email del request user.
6. Validaciones de servicio: cobertura, unicidad de `isMain`, `ProvidedService` activo → 422 con mensaje en español si fallan.
7. Tras commit, publicar AMQP `client-team-assignment.opened`/`.closed` por cada mutación.

**Qué NO entra aquí**
- Helper `normalize-month-boundary` → T-02-A.1.
- PUT `/:id` para `isMain` o cerrar tramo individual → T-02-A.3.
- DELETE void de FR-007 → T-02-A.4. (El diff de este PR cierra normalmente los tramos del mes en curso; el void específico se acopla en T-02-A.4.)
- Preservación de tramos futuros (FR-006-bis) → US-03.
- FE → T-02-B.x.

**Cómo verificar**

| # | Escenario | Verifica |
|---|---|---|
| 1 | Estado: 1 asesor 100%. Body: distinto asesor 100%. | 1 closed + 1 opened. 2 filas en change. Cobertura 100%. |
| 2 | Estado: 1 asesor 100%. Body: 2 asesores 50/50. | 1 closed + 2 opened. Solo 1 con `isMain=true`. |
| 3 | Estado: A 50% + B 50%. Body: A 100% (B sale). | Closed B + closed A_50 + opened A_100. |
| 4 | Idempotencia: enviar el mismo body 2 veces. | Segunda llamada no muta nada. 0 filas nuevas en change. |
| 5 | `dateFrom` en mes pasado. | 422 en español. Nada persistido. |
| 6 | Sin `ProvidedService` activo en el departamento. | 422. Rollback. |
| 7 | Dos `isMain=true` en el body. | 422 con mensaje sobre unicidad. |

Smoke manual: verificar en RabbitMQ Management UI los 2 eventos AMQP (closed + opened).

**DoD**
- `npm run lint && npm run build && npm test` ✓ en pgi-api.
- 7 tests de la tabla en CI.
- `created_by` en `client_team_assignment_change` verificado.

---

### T-02-A.3 — Endpoint `PUT /:id` para `isMain` o cierre individual

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-02-a-3-put-by-id`
**Depende de**: T-SETUP-1, T-01-A

**Qué hace**
Implementa `PUT /api/v1/clients/{clientId}/team-assignments/{id}` con body `{ isMain?, dateTo?, version }`. Modifica un tramo vivo: cambia `isMain` (para promover/demover asesor main) o cierra el tramo (salida sin sustituto). Response 204.

**Cómo funciona**
1. Cargar la asignación; si no existe → 404 `NotFoundException`.
2. Comparar `version` del body con el actual; si difiere → 409 `ConflictException` con mensaje "modificada por otro usuario".
3. Si `isMain` cambia:
   - Validar que `role='asesor'`; si no → 422.
   - Validar unicidad de `isMain` en `(client, department)` dentro de la transacción con `SELECT … FOR UPDATE` sobre `client`.
   - UPDATE de la fila + insert en change con `action='main_changed'`.
4. Si `dateTo` viene en el body:
   - Validar que sea ≥ primer día del mes en curso; si no → 422.
   - UPDATE de la fila + insert en change con `action='closed'`.
5. Si ambos vienen, ambas mutaciones en la misma transacción (raro pero permitido).
6. Tras commit, publicar AMQP correspondiente (`opened` no aplica aquí; `closed` sí cuando `dateTo` se setea).

**Qué NO entra aquí**
- PUT colección multi-miembro → T-02-A.2.
- DELETE void → T-02-A.4.
- Cambios de `percentage` o `role` — el modelo los trata como nuevo tramo, no como mutación in-place, así que entran por el PUT colección (T-02-A.2).
- FE → T-02-B.x.

**Cómo verificar**

| # | Escenario | Verifica |
|---|---|---|
| 1 | PUT con `isMain=true` sobre asesor que no era main; no había otro main. | UPDATE in-place. 1 fila en change con `action='main_changed'`. |
| 2 | PUT con `isMain=true` sobre asesor; ya hay otro main activo. | 422 con mensaje de unicidad. Nada persistido. |
| 3 | PUT con `isMain=true` sobre técnico. | 422 con mensaje sobre rol. |
| 4 | PUT con `dateTo=último día del mes en curso` sobre tramo activo. | UPDATE + 1 fila en change con `action='closed'`. AMQP `closed` publicado. |
| 5 | PUT con `dateTo` en mes pasado. | 422. |
| 6 | PUT con `version` obsoleta. | 409. |
| 7 | PUT sin `isMain` ni `dateTo`. | 400 (validación: al menos uno requerido). |

**DoD**
- `npm test` ✓.
- 7 tests de la tabla en CI.

---

### T-02-A.4 — Endpoint `DELETE /:id` (void FR-007)

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-02-a-4-delete-void`
**Depende de**: T-SETUP-1, T-01-A, T-02-A.2 (reutiliza la lógica del PUT colección para detectar caso "creado este mes")

**Qué hace**
Implementa `DELETE /api/v1/clients/{clientId}/team-assignments/{id}` que **no borra físicamente** sino que voida el tramo (`UPDATE date_to = date_from - 1 día`). Solo permitido si `date_from` cae en el mes en curso. Response 204.

**Cómo funciona**
1. Cargar la asignación; si no existe → 404.
2. Verificar `date_from = primer día del mes en curso`. Si no → 422 con mensaje "solo se pueden anular tramos creados en el mes en curso".
3. UPDATE: `date_to = date_from - 1 día`, `updated_at = now()`.
4. INSERT en `client_team_assignment_change` con `action='voided'`, `_before` con snapshot completo del tramo antes del void, `date_to_after = date_from - 1 día`.
5. Tras commit, publicar AMQP `client-team-assignment.closed` con `closureKind='voided'` (cambio menor de payload — coordinar con T-06-A si ya está mergeado, o adelantar el campo en el schema de T-SETUP-2).

**Qué NO entra aquí**
- Modificar el schema AMQP para añadir `closureKind` — debería estar ya en `contracts/amqp/client-team-assignment.closed.schema.json` desde T-SETUP-2. Si no está, añadirlo allí, no aquí.
- Void automático cuando el PUT colección expulsa un tramo del mes en curso — esa lógica vive en T-02-A.2; este PR solo expone el endpoint explícito.
- FE → T-02-B.x.

**Cómo verificar**

| # | Escenario | Verifica |
|---|---|---|
| 1 | DELETE sobre tramo con `date_from = primer día del mes en curso`. | `date_to` queda en `date_from - 1 día`. Tramo invisible a `GET …?date=hoy`. 1 fila en change con `action='voided'`. |
| 2 | DELETE sobre tramo con `date_from` en mes anterior. | 422. Nada persistido. |
| 3 | DELETE sobre tramo ya cerrado (`date_to IS NOT NULL`). | 422 (no se voida algo ya cerrado). |
| 4 | Tras DELETE, recuperar el log: aparece `_before` con snapshot completo del tramo previo al void. | |
| 5 | Recálculo de cobertura post-void: el tramo voided **no** suma. | |

**DoD**
- `npm test` ✓.
- 5 tests de la tabla en CI.
- AMQP `closed` con `closureKind='voided'` verificado en RabbitMQ Management UI.

---

### T-02-B.1 — FE: cliente API tipado + hooks TanStack Query

**Servicio**: pgi-web
**Branch**: `feat/dev-518-t-02-b-1-hooks`
**Depende de**: T-SETUP-2 (contract OpenAPI publicado)

**Qué hace**
Genera el cliente TypeScript del OpenAPI extendido (US-02 endpoints) y crea los hooks de TanStack Query que la UI consumirá: `useReplaceTeam`, `useUpdateAssignment`, `useVoidAssignment`.

**Cómo funciona**
- Regenerar el cliente API con la herramienta de generación ya configurada (`openapi-typescript-codegen` o equivalente — usar la que ya esté en el repo).
- Hooks devuelven mutaciones tipadas con invalidación automática de la query `team-assignments[clientId, department]`:
  - `useReplaceTeam({ clientId, department, dateFrom })` → mutación que envía `{ members: [...] }`.
  - `useUpdateAssignment({ clientId, assignmentId })` → mutación que envía `{ isMain?, dateTo?, version }`.
  - `useVoidAssignment({ clientId, assignmentId })` → mutación DELETE.
- Manejador común de errores `{ statusCode, message, error }` extraído a un helper `parseNestError(error)` que devuelve `{ status, userMessage }` listo para toast.

**Qué NO entra aquí**
- Componentes UI (modales, formularios) → T-02-B.2.
- E2E Playwright → T-02-B.3.
- Cambios en el cliente API de US-01 (ya existe desde T-01-B); este PR solo añade los nuevos endpoints.

**Cómo verificar**

Tests Vitest + Testing Library en `hooks/__tests__/`:

| # | Hook | Caso | Verifica |
|---|---|---|---|
| 1 | `useReplaceTeam` | Mutación OK | Llama a `PUT` con el body correcto. Invalida la query del listado. |
| 2 | `useReplaceTeam` | Response 422 | `parseNestError` extrae `userMessage` listo para toast. |
| 3 | `useUpdateAssignment` | 409 version conflict | El hook expone el conflicto para que el componente refresque. |
| 4 | `useVoidAssignment` | DELETE OK | Invalida la query. |
| 5 | `parseNestError` | 400 con `message` como array (validation pipe) | Devuelve string con joined message. |

**DoD**
- `npx vitest run hooks` ✓.
- Tipos del cliente API regenerados sin errores TS.
- Sin dependencias de componentes (los hooks deben poder usarse desde tests sin renderizar UI).

---

### T-02-B.2 — FE: `EditMemberModal` y flujos de reemplazo / cambio % / redistribución

**Servicio**: pgi-web
**Branch**: `feat/dev-518-t-02-b-2-modal`
**Depende de**: T-02-B.1 (hooks), T-01-B (vista del equipo)

**Qué hace**
Implementa el componente `EditMemberModal` y lo cablea al `ClientTeamView` existente (de US-01) para permitir editar la composición del equipo en el mes en curso desde la UI.

**Cómo funciona**
- Modal con tabs/secciones para los flujos del usuario:
  - **Reemplazar**: selector empleado entrante + datepicker → llama `useReplaceTeam` con el nuevo estado calculado.
  - **Cambiar %**: slider sobre uno o varios miembros + datepicker → `useReplaceTeam`.
  - **Redistribuir**: misma UI que cambio de % pero permitiendo dar de baja a un miembro y entrar varios.
  - **Cerrar tramo sin sustituto / cambiar isMain**: `useUpdateAssignment`.
  - **Anular tramo del mes** (botón en una fila marcada como "creada este mes"): `useVoidAssignment` con confirmación.
- Datepicker restringido a primer día del mes en curso por defecto; permite mes futuro (US-03 lo aprovechará, hoy solo si el feature flag está on — fuera de scope de este PR).
- Toasts:
  - 422 → `userMessage` del backend.
  - 409 → "El equipo ha cambiado, recargando…" + refetch automático.
- Aviso visual en filas que fueron creadas/modificadas en el mes en curso (badge "este mes") para que el usuario sepa cuáles puede voidear.

**Qué NO entra aquí**
- Hooks de TanStack Query → T-02-B.1.
- Selector de fecha futura (US-03).
- E2E Playwright → T-02-B.3.
- Cambios en el listado de US-01 (`ClientTeamView`) más allá de añadir los puntos de entrada al modal y el badge "este mes".

**Cómo verificar**

Tests Vitest + Testing Library:

| # | Caso | Verifica |
|---|---|---|
| 1 | Abrir modal "Reemplazar", seleccionar empleado, guardar. | Llama `useReplaceTeam` con `{ members: [...] }` correcto. |
| 2 | Cambiar slider de % en 2 miembros que suman 100%. | Llama `useReplaceTeam` con ambos. |
| 3 | Click en "Anular" sobre fila con badge "este mes". | Confirmación + llamada `useVoidAssignment`. |
| 4 | Toast cuando backend responde 422. | `userMessage` visible en el toast. |
| 5 | 409 conflict. | Toast + refetch automático. |
| 6 | Botón "Anular" deshabilitado en filas SIN badge "este mes". | |

**DoD**
- `npx vitest run components` ✓.
- Modal accesible vía teclado (esc cierra, enter en form principal envía).
- Sin warnings de React en consola en los tests.

---

### T-02-B.3 — FE: E2E Playwright cubriendo los 5 criterios de US-02

**Servicio**: pgi-web
**Branch**: `feat/dev-518-t-02-b-3-e2e`
**Depende de**: T-02-A.* (BE mergeado), T-02-B.1, T-02-B.2

**Qué hace**
Suite E2E Playwright que recorre los 5 criterios de aceptación de US-02 contra una instancia local de pgi-api con BD limpia y datos seed.

**Cómo funciona**
Cada test sigue el patrón "abrir cliente fixture → ejecutar flujo en UI → verificar estado en la UI **y** consultar BD/log directamente para confirmar la mutación correcta". Datos seed: cliente con `ProvidedService` activo en fiscal y un equipo inicial mediante el endpoint de US-01 antes del test.

**Qué NO entra aquí**
- Tests unit de componentes/hooks (ya en T-02-B.1/B.2).
- Tests integration de BE (ya en T-02-A.*).
- Setup de Playwright (debe existir desde T-01-B; este PR solo añade specs).

**Cómo verificar**

5 specs (uno por criterio):

| # | Criterio | Spec |
|---|---|---|
| 1 | Reemplazo simple | `e2e/team-assignments/replace-simple.spec.ts` — sustituyo asesor por otro al 100% el 15/06; verifico tabla y log. |
| 2 | Cambio de % | `e2e/team-assignments/change-percentage.spec.ts` — bajo asesor a 50%, añado otro al 50%; verifico cobertura 100%, antigüedad preservada. |
| 3 | Redistribución | `e2e/team-assignments/redistribute.spec.ts` — un asesor sale, dos entran al 50% cada uno; verifico cobertura y `isMain` único. |
| 4 | Segundo cambio en mismo mes | `e2e/team-assignments/double-edit-same-month.spec.ts` — dos cambios sucesivos; el primero queda voided invisible; consulta del log lo muestra. |
| 5 | Mes pasado rechazado | `e2e/team-assignments/reject-past-month.spec.ts` — intento cambio con fecha en mayo; toast con mensaje. |

**DoD**
- `npx playwright test` ✓ con los 5 specs en local con BD limpia.
- Suite estable en CI tras 3 corridas seguidas (sin flakiness).
- Demo manual al PO siguiendo los 5 criterios.

**Fuera**: cambios programados a futuro → US-03 (E2E propio).

---

## US-04 — Alta inicial desde Onboarding (AMQP) · MVP P1

### T-04-A — BE: subscriber del evento `client-onboarding-assignment`

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-04-a-be`
**Depende de**: T-SETUP-1, T-SETUP-2 (schema AMQP cerrado)

**Qué hace**
Implementa el subscriber AMQP `ClientOnboardingAssignmentSubscriber` que materializa el alta inicial del equipo de un cliente con las fechas tal cual las recibe del producer (única excepción a la normalización de FR-002).

**Cómo funciona**
- Subscriber en `src/application/amqp/client-onboarding-assignment-subscriber/`. Queue `pgi-api:client-onboarding-assignment:process`. Binding al routing key `client-onboarding-assignment` (nombre hipotetizado — se confirma en T-04-B).
- Idempotencia por `eventId`: si llega un mensaje con `eventId` ya procesado, ACK y log info.
- Defensivo: si el cliente ya tiene equipo activo en ese departamento → DLQ con mensaje de error claro.
- Materialización: dentro de una transacción crear `client_team` (si no existe) + N `client_team_assignment` con fechas tal cual recibidas (sin normalización, sin rechazo de mes pasado — excepción FR-004 v2). Insertar fila en `client_team_assignment_change` con `action='opened'` y `created_by='system:onboarding'`.
- Tras commit, publish de eventos `pgi-api.v1.client-team-assignment.opened` por cada asignación creada (mismo path que el POST de US-01).

**Qué NO entra aquí**
- Confirmación de la routing key con el producer → T-04-B.
- Actualizaciones de equipo vía onboarding (solo alta inicial — actualizaciones van por UI o por otra story futura).
- Tracking del producer del evento — eso es responsabilidad de T-04-B.

**Cómo verificar**

Tests integration con `@golevelup/nestjs-rabbitmq` test utility + testcontainers:

| # | Escenario | Verifica |
|---|---|---|
| 1 | Evento válido con 3 miembros y `dateFrom=20/05/2026` | `client_team` creado; 3 filas en `client_team_assignment` con fechas exactas; 3 filas en change con `created_by='system:onboarding'`. |
| 2 | Mismo `eventId` enviado 2 veces | Segunda llegada ACK silencioso; sin filas duplicadas. |
| 3 | Cliente ya tiene equipo activo en ese departamento | DLQ con mensaje "equipo ya existe"; nada persistido. |
| 4 | Payload malformado (department inválido, employeeId no UUID) | DLQ con mensaje de validación. |
| 5 | Tras materialización, 3 eventos `opened` publicados downstream | Visible en RabbitMQ Management UI. |

**DoD**
- `npm test` ✓ con los 5 casos.
- Smoke manual: publicar mensaje conforme al schema vía RabbitMQ UI → abrir cliente en UI y ver equipo con fechas exactas (no normalizadas).
- DLQ inspeccionable: cada mensaje malformado lleva un campo `error` legible.

---

### T-04-B — Coordinación con producer + ajustar routing key

**Servicio**: ninguno (coordinación cross-team)
**Branch**: solo si hay ajuste → `fix/dev-518-onboarding-binding`
**Depende de**: T-04-A (subscriber existe con routing key hipotetizada)

**Qué hace**
Cierra la duda OQ-005 sobre el nombre exacto de la routing key del evento de onboarding y el shape del payload, coordinando con el equipo dueño del producer.

**Cómo funciona**
1. Identificar producer (portal del cliente, proceso comercial, sistema externo). Punto de partida: Mario o Sofía — confirmar por Slack/Jira.
2. Confirmar con el producer: nombre exacto de routing key, shape del payload, política de versiones.
3. Documentar el acuerdo en `decisions.md` cerrando OQ-005.
4. Si la routing key difiere de la hipotetizada (`client-onboarding-assignment`), ajustar el binding en `client-onboarding-assignment.subscriber.ts`.

**Qué NO entra aquí**
- Implementación del producer (no es nuestro repo).
- Cambios de payload — si el producer envía un shape distinto, OQ-005 se reabre con propuesta de adaptador, no se reescribe aquí.

**Cómo verificar**
- OQ-005 cerrada en `decisions.md` con la decisión final (nombre real de routing key + shape verificado).
- Si hubo ajuste de binding, PR mergeada y deployed a staging; smoke test envía mensaje real desde el producer y llega al subscriber.

**DoD**
- OQ-005 cerrada con la decisión documentada.
- Si hubo ajuste, PR mergeada.

---

## US-05 — Log de cambios sobre el equipo · MVP P1

### T-05-A — BE: `GET /team-assignment-changes` + auditoría de producers del log

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-05-a-be`
**Depende de**: T-01-A, T-02-A.2 (las inserciones en el log se acoplan a esas mutaciones)

**Qué hace**
Expone el endpoint REST de consulta del log y audita que cada mutación de US-01/US-02/US-03/US-04 inserte sus filas correspondientes en `client_team_assignment_change`. Si alguna mutación se olvidó de insertar (esperable si T-05-A llega después de las otras), este PR lo corrige.

**Cómo funciona**
- Endpoint `GET /api/v1/clients/{clientId}/team-assignment-changes?department={dept}&from={date?}&to={date?}` — log paginado por rango (default últimos 90 días). Response `{ data, total }`. Permission `CLIENT_ASSIGNMENT_VIEW`.
- DTO `AssignmentChangeDto` con todas las columnas before/after y audit (ver §1.3 de `data-model.md`).
- Query con JOIN a `client_team_assignment` → `client_team` para filtrar por `department` y `client_id`.
- Auditoría: revisar cada producer del log existente (T-01-A POST, T-02-A.2 PUT colección, T-02-A.3 PUT /:id, T-02-A.4 DELETE void, T-04-A onboarding) y verificar que su transacción incluye la inserción del change. Si falta alguna, añadirla aquí.

**Qué NO entra aquí**
- Vista FE → T-05-B.
- Correcciones manuales del log (script de mantenimiento fuera de scope total).
- Helper `compute-in-client-since` (ya en T-01-A).

**Cómo verificar**

Tests integration:

| # | Escenario | Verifica |
|---|---|---|
| 1 | Tras POST de US-01 | 1 fila con `action='opened'` y `_after` completo. |
| 2 | Tras PUT colección de US-02 (reemplazo) | 2 filas (closed + opened) con autor correcto. |
| 3 | Tras DELETE void de FR-007 | 1 fila con `action='voided'` y `_before` snapshot completo. |
| 4 | GET con rango de fechas | Orden cronológico descendente; filtra correctamente. |
| 5 | GET con `department` | JOIN funciona; solo se devuelven cambios del depto pedido. |
| 6 | Múltiples cambios sobre la misma asignación | Cada cambio conserva su `created_by` (autor preservado). |

Smoke de performance: dataset seed con ~500 cambios → GET p95 < 300 ms.

**DoD**
- `npm test` ✓ con los 6 casos.
- Performance check pasada.
- Auditoría de producers documentada en el PR (si algún producer no insertaba el change, queda corregido).

---

### T-05-B [P] — FE: pestaña "Log de cambios" + filtros + E2E

**Servicio**: pgi-web
**Branch**: `feat/dev-518-t-05-b-fe`
**Depende de**: T-SETUP-2

**Qué hace**
Añade la pestaña "Log de cambios" en la ficha del cliente con tabla cronológica + filtros (rango fechas, departamento) y los E2E que cubren los 5 criterios de US-05.

**Cómo funciona**
- Componente `ClientTeamChangeLog` con tabla MUI: columnas fecha, autor, acción, antes, después.
- Renderizado adaptativo por `action`: cada acción muestra solo las columnas before/after relevantes (ej. `percentage_changed` muestra "% antes → después"; `voided` muestra snapshot del tramo).
- Filtros UI: rango de fechas (datepicker desde/hasta), departamento (toggle fiscal/laboral).
- Hook `useTeamAssignmentChanges({ clientId, department, from?, to? })` → GET del endpoint de T-05-A con `keepPreviousData: true` para evitar flicker al cambiar filtros.

**Qué NO entra aquí**
- Endpoint REST → T-05-A.
- Edición de filas del log (es read-only en la API).

**Cómo verificar**

Tests Vitest + Testing Library:

| # | Caso | Verifica |
|---|---|---|
| 1 | Render con cambios mixtos | Cada fila muestra solo los campos relevantes según `action`. |
| 2 | Filtro por departamento | Llama a la query con `department=` correcto. |
| 3 | Filtro por rango | Llama con `from`/`to`. |
| 4 | Autor `system:onboarding` | Visible como tal (no como email anónimo). |
| 5 | Acción `voided` | Render claro indicando que el tramo fue anulado. |

**E2E Playwright** (`e2e/team-assignments/change-log.spec.ts`): tras correr seed de cambios variados (alta + edit + void), abrir el log, aplicar filtros, verificar orden cronológico descendente y que el autor se mantiene tras múltiples cambios sobre la misma asignación.

**DoD**
- `npx vitest run` ✓ en pgi-web.
- E2E verde.
- Demo al PO con cliente que tenga histórico real (post US-01 + US-02).

---

## US-03 — Cambios futuros con preservación · P2

### T-03-A — BE: preservación de tramos futuros pre-existentes (FR-006-bis)

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-03-a-be`
**Depende de**: T-02-A.2 (la lógica de preservación se inserta en el diff del PUT colección)

**Qué hace**
Extiende el PUT colección para que, cuando `dateFrom` cae en un mes futuro y ya hay tramos futuros pre-existentes para alguna persona+rol, los respete encajando el nuevo tramo entre el corte actual y el futuro previo (FR-006-bis).

**Cómo funciona**
- Helper `insert-with-future-preservation.helper.ts`: dado un nuevo tramo (clientTeamId, employeeId, role, dateFrom), busca el tramo pre-existente con `date_from > dateFrom` más cercano para esa terna y devuelve `dateTo = ese date_from - 1 día`. Si no hay tramo futuro pre-existente, devuelve `null` (tramo abierto).
- Modificar el service de T-02-A.2 para invocar este helper cuando `dateFrom > primer día del mes en curso`. Para tramos en mes en curso, comportamiento sin cambios (no aplica preservación).
- Validación crítica: un cambio con `dateFrom` futuro **no** machaca/voida tramos futuros pre-existentes (a diferencia de FR-007 que solo aplica al mes en curso).

**Qué NO entra aquí**
- FE para programar cambios futuros → T-03-B.
- Lógica del mes en curso (FR-007) → ya en T-02-A.2/A.4.
- Cambios sobre tramos futuros ya planificados (sobrescribir uno con otro futuro): aplica la misma regla, no requiere lógica especial.

**Cómo verificar**

Tests integration cubriendo el §7.5 de la spec:

| # | Escenario | Verifica |
|---|---|---|
| 1 | Estado actual: David 100% activo. PUT con `dateFrom=01/09` → Juan/Paloma 50/50. | David cerrado el 31/08; Juan/Paloma abiertos desde 01/09. |
| 2 | Tras el anterior, PUT con `dateFrom=01/08` → David 75% + Juan 25%. | David tiene 3 tramos consecutivos (100 → 75 → 50); Juan tiene 2 (25 → 50); ningún tramo futuro pre-existente se pierde. |
| 3 | PUT con `dateFrom=01/08` cuando ya hay tramo de Juan en 01/09 al 50%. | El nuevo tramo de Juan se cierra el 31/08 (`date_to = date_from_pre_existente - 1`). |
| 4 | Sin tramos futuros pre-existentes | El nuevo tramo queda abierto (`date_to = NULL`). |
| 5 | Cobertura `at=2026-08-15` y `at=2026-09-15` | 100% en ambas fechas. |

**DoD**
- `npm test` ✓ incluyendo los 5 escenarios.
- Escenario completo §7.5 verificado end-to-end.

---

### T-03-B [P] — FE: selector de fecha futura + indicadores de cambio programado + E2E

**Servicio**: pgi-web
**Branch**: `feat/dev-518-t-03-b-fe`
**Depende de**: T-SETUP-2, T-02-B.2 (reusa `EditMemberModal`)

**Qué hace**
Habilita en la UI la programación de cambios con `dateFrom` futuro (1er día de mes posterior al actual) y añade indicadores visuales sobre miembros con cambios programados.

**Cómo funciona**
- En `EditMemberModal`: ampliar el datepicker para permitir fechas futuras (mes posterior al actual). Si la fecha elegida es futura, mostrar aviso amarillo "cambio programado para 01/MM/YYYY — no afecta a la vista actual".
- En `ClientTeamView`: si un miembro tiene `hasFutureChange=true` (campo nuevo que el GET debería exponer — coordinar con T-01-A para añadirlo), mostrar indicador "⏰ cambio programado".
- Reutilizar el selector "ver equipo a fecha…" de T-01-B con un atajo "ver futuro" que abre datepicker en el mes siguiente.

**Qué NO entra aquí**
- Lógica BE de preservación → T-03-A.
- Modificación del selector base de fecha (ya está en T-01-B).

**Cómo verificar**

Tests Vitest + Testing Library + **E2E Playwright** (5 specs):

| # | Criterio | Spec E2E |
|---|---|---|
| 1 | Programar cambio efectivo 01/09 con hoy 20/06 | Vista "hoy" no cambia; vista "15/09" sí. |
| 2 | Tras anterior, programar 01/08 | Cambio de septiembre intacto; David tiene 3 tramos. |
| 3 | Indicador "cambio programado" visible | Badge "⏰ 01/09" en filas afectadas. |
| 4 | Backend normaliza día mid-month → primer día | UI muestra confirmación "se aplicará desde 01/09". |
| 5 | Rechazo retroactivo | Toast con mensaje del backend. |

**DoD**
- `npx vitest run` ✓ en pgi-web.
- 5 specs E2E verdes.
- Demo al PO siguiendo §7.5 de la spec.

---

## US-06 — Reasignación automática de tareas · P2 cross-service

### T-06-A — pgi-api: verificación de payload completo + contract test AMQP

**Servicio**: pgi-api
**Branch**: `feat/dev-518-t-06-a-pgi`
**Depende de**: T-01-A, T-02-A.2, T-02-A.4 (publishers ya implementados — aquí solo se verifica)

**Qué hace**
Verifica que los eventos AMQP `client-team-assignment.opened` y `.closed` publicados por pgi-api contengan toda la información que obligations-api necesita para reasignar tareas, y deja un contract test que falle si el shape cambia.

**Cómo funciona**
- Auditar los publishers existentes (T-01-A POST, T-02-A.2 PUT, T-02-A.4 DELETE void): payload mínimo debe incluir `assignmentId`, `clientId`, `department`, `role`, `employeeId`, `percentage`, `dateFrom`, `dateTo`, `isMain`, `version`, `closureKind` (solo en `.closed`).
- Añadir contract test usando uno de los enfoques:
  - (a) Validación contra `contracts/amqp/*.schema.json` con `ajv` ejecutada en tests integration tras cada publish.
  - (b) Pact provider verification si obligations-api tiene Pact ya configurado (consultar con su tech lead).
- Documentar el formato exacto en `quickstart.md` con un ejemplo curl/JSON de cada evento.

**Qué NO entra aquí**
- Implementación del subscriber en obligations-api → T-06-B.
- Cambios en el shape del payload — si falta algo se añade al schema en T-SETUP-2, no aquí.

**Cómo verificar**
- Tests integration en pgi-api que validan el JSON publicado contra el schema tras cada operación de US-01/US-02.
- `quickstart.md` actualizado con sección "Eventos AMQP cross-service" + ejemplos.

**DoD**
- Tests verdes con validación de schema.
- `quickstart.md` actualizado.

---

### T-06-B — obligations-api: subscriber + reasignación automática de tareas

**Servicio**: pd-service-obligations-api
**Branch**: `feat/dev-518-t-06-b-obligations` (en el repo de obligations)
**Depende de**: T-06-A. Coordinación con team lead de obligations.

**Qué hace**
Implementa en `pd-service-obligations-api` el subscriber a los eventos AMQP de pgi-api y la lógica de reasignación de tareas abiertas: cuando un asesor sale del equipo, sus tareas con `dueDate >= dateFrom` del nuevo tramo pasan al asesor entrante.

**Cómo funciona**
- Subscriber a `pgi-api.v1.client-team-assignment.opened` y `.closed` con binding en exchange `internal` (vhost `data_platform`).
- Por cada evento `closed`, identificar las tareas abiertas del `clientId` + `department` con `dueDate >= dateFrom` y actualizar su `assignedTo` al asesor que abrió tramo en la misma fecha (lookup correlacionado).
- Idempotencia por `eventId`: ignora duplicados.
- Si el empleado nuevo no existe en obligations → log error + DLQ; la tarea queda como estaba (sin perder dato).

**Qué NO entra aquí**
- Cambio de prioridad o `dueDate` de las tareas (solo `assignedTo`).
- Reasignación de tareas cerradas (solo abiertas).
- Cambios en el publisher de pgi-api (eso es T-06-A).
- UI de obligations — el cambio se ve en la UI existente.

**Cómo verificar**

Tests integration cross-service simulando eventos publicados desde pgi-api:

| # | Escenario | Verifica |
|---|---|---|
| 1 | Cliente con 5 tareas asignadas a David. Llega `closed` David + `opened` Juan con `dateFrom=01/06`. | Tareas con `dueDate >= 01/06` pasan a Juan; tareas con `dueDate < 01/06` siguen con David. |
| 2 | Mismo `eventId` enviado 2 veces | Segunda vez no muta. |
| 3 | Empleado nuevo no existe en obligations | Log error + DLQ; tareas no cambian. |
| 4 | Llega `closed` con `closureKind='voided'` (FR-007) | Tareas se reasignan correctamente al sucesor (si lo hay) o quedan con el saliente si no hay sucesor. |

E2E manual: cambiar asesor en pgi-api vía UI → abrir panel de tareas del cliente en obligations UI → ver el nuevo asesor.

**DoD**
- Tests verdes en obligations-api.
- E2E manual ✓.
- DLQ inspeccionable con mensaje claro en los casos de error.

---

## Resumen

US-07 ha sido **fusionada en US-05** (log de cambios) y ya no aparece como tarea aparte.

| Bloque | Tareas | Notas |
|---|---|---|
| Setup | 2 | T-SETUP-1 (3 migraciones), T-SETUP-2 (contracts) |
| US-01 P1 | 2 | BE, FE+E2E |
| US-02 P1 | 7 | 4 BE (helper + PUT colección + PUT /:id + DELETE void), 3 FE (hooks + modal + E2E) |
| US-04 P1 | 2 | BE subscriber, coordinación producer |
| US-05 P1 | 2 | BE (log endpoint + producer), FE+E2E |
| US-03 P2 | 2 | BE preservación, FE selector futuro |
| US-06 P2 | 2 | pgi-api verificación, obligations subscriber |
| **Total** | **19** | |

## Mapa de dependencias

```
T-SETUP-1 ─┬─→ T-01-A ─┬─→ T-02-A.1 ─┬─→ T-02-A.2 ─┬─→ T-02-A.3
           │           │             │             ├─→ T-02-A.4
           │           │             │             │
           │           │             │             └─→ T-03-A ─→ T-03-B
           │           │             │
           │           │             └─→ T-05-A ─→ T-05-B
           │           │             │
           │           │             └─→ T-06-A ─→ T-06-B (obligations)
           │           │
           │           └─→ T-01-B
           │
           └─→ T-04-A ─→ T-04-B (coordinación)

T-SETUP-2 ─→ desbloquea todos los FE:
              T-01-B
              T-02-B.1 ─→ T-02-B.2 ─→ T-02-B.3
              T-03-B
              T-05-B
```

## Plan de paralelización sugerido (con 3 personas)

| Sprint | Dev A (BE pgi-api) | Dev B (FE pgi-web) | Dev C (variado) |
|---|---|---|---|
| 1 | T-SETUP-1 + T-01-A | T-SETUP-2 (revisar contracts) | T-04-B (coordinación) |
| 2 | T-02-A.1 + T-02-A.2 + T-04-A | T-01-B + T-02-B.1 | T-05-A |
| 3 | T-02-A.3 + T-02-A.4 + T-06-A | T-02-B.2 + T-05-B | T-06-B (obligations) |
| 4 | T-03-A + tests cross | T-02-B.3 + T-03-B | bugfix + e2e cross |

(Indicativo — ajustar según disponibilidad real.)
