# Phase 1 — Data Model (US1)

**Feature**: 001-client-team-assignments
**Date**: 2026-06-03 · **Aligned to authoritative ER**: 2026-06-04
**Scope**: solo entidades necesarias para US1. La tabla de auditoría `ClientTeamAssignmentChange` queda fuera de US1 (OPEN-001).

Diagrama ER completo y autoritativo en [`er-diagram.md`](./er-diagram.md). Este documento detalla **deltas vs. esquema actual** y reglas de validación por entidad. Ante cualquier discrepancia, manda el ER.

> **Modelo**: 3 tablas nuevas/ampliadas (`ClientTeam` ampliada, `ClientTeamAssignment` nueva, `ClientTeamAssignmentChange` diferida). `ClientAssignment` legacy se **congela** post-deploy — no se le añaden columnas nuevas en este modelo (su columna `percentage` ya existe de M0). Los datos activos se migran a `ClientTeamAssignment` vía script explícito por cliente.

---

## Entidades

### `ClientTeam` (existe — ampliar)

Tabla: `client_team`

| Columna | Tipo | Estado | Notas |
|---------|------|--------|-------|
| `id` | uuid PK | existe | generado en app (uuidv4) |
| `client_id` | uuid FK → client | existe | NOT NULL, `updateRule: cascade`, `deleteRule: restrict` |
| `department` | enum (`fiscal` \| `laboral`) | existe | NOT NULL |
| `start_date` | date | existe | NOT NULL, primer día del mes (validado en servicio) |
| `end_date` | date | existe | NULL = equipo activo; cuando NOT NULL = último día del mes |
| `created_by` | varchar | **NEW** | email backoffice user o `system:onboarding` / `system:migration` |
| `created_at` | timestamp | existe | `onCreate` |
| `updated_at` | timestamp | existe | `onUpdate` |
| `version` | smallint | **NEW** | default `1`, incrementa en cada UPDATE (ADR-0010) |

**Constraints**:
- Índice no único `(client_id, department, end_date)` — soporta query "equipos activos del cliente en el departamento X".
- **No** se añade unique sobre `(client_id, department) WHERE end_date IS NULL` — multi-equipo por dept está permitido (FR-005, PO 2026-06-01).

**Reglas de servicio**:
- `start_date` debe ser primer día del mes (FR-012).
- `end_date`, si no es null, debe ser último día del mes (FR-012).
- `end_date` no puede ser anterior a `start_date`.
- No se permite editar `client_id`, `department`, ni `created_by` una vez creado.

**Estado derivado** (no persiste — calculado on-the-fly por `compute-team-status.helper.ts`):
- `incomplete` si **alguna** de:
  - No hay `ClientTeamAssignment` activa con `role='responsable'` en el equipo.
  - No hay al menos una `ClientTeamAssignment` activa con `role='asesor'` en el equipo.
  - Cobertura de asesores ≠ 100% por (client, department) (sumando entre **todos** los equipos activos del cliente+dept).
  - Cobertura de técnicos ≠ 100% por (client, department) **si existe al menos un técnico** en ese cliente+dept. Si no hay ninguno → cobertura "no aplicable", no bloquea.
  - No existe exactamente un `ClientTeamAssignment` activo con `role='asesor'` e `is_primary_advisor=true` por (client, department).
- `active` si ninguna de las anteriores se cumple.
- `closed` si `end_date IS NOT NULL`.

---

### `ClientTeamAssignment` (NUEVA)

Tabla: `client_team_assignment`

Reemplaza el rol que tenía `ClientAssignment` en el modelo anterior. Todas las asignaciones nuevas viven aquí; las filas activas de `ClientAssignment` se migran a esta tabla por el script de la opción 1 (banner+migrate) o la opción 6 (safety net) — ver ADR-0009.

| Columna | Tipo | Notas |
|---------|------|-------|
| `id` | uuid PK | generado en app (uuidv4) |
| `team_id` | uuid FK → client_team | NOT NULL, `updateRule: cascade`, `deleteRule: restrict` |
| `client_id` | uuid | NOT NULL, denormalizado — debe coincidir con `team.client_id` |
| `employee_id` | uuid FK → employee | NOT NULL |
| `department` | enum (`fiscal` \| `laboral`) | NOT NULL, denormalizado — debe coincidir con `team.department` |
| `role` | enum (`responsable` \| `coordinador` \| `asesor` \| `tecnico`) | NOT NULL |
| `date_from` | date | NOT NULL, primer día del mes |
| `date_to` | date | NULL = activa; NOT NULL = último día del mes |
| `percentage` | smallint | NOT NULL, default 100, CHECK `1..100` |
| `is_primary_advisor` | boolean | NOT NULL, default `false`. Solo puede ser `true` cuando `role='asesor'` (CHECK constraint) |
| `created_by` | varchar | NOT NULL, email o `system:onboarding` / `system:migration:via:<email>` |
| `created_at` | timestamp | `onCreate` |
| `updated_by` | varchar | NULL hasta primer UPDATE |
| `updated_at` | timestamp | `onUpdate` |
| `version` | smallint | NOT NULL, default `1`, incrementa en cada UPDATE (ADR-0010) |

**Constraints**:
- `UNIQUE(client_id, employee_id, role, department, date_from)` — equivalente al existente en `ClientAssignment`; previene duplicados exactos.
- `UNIQUE(client_id, employee_id) WHERE date_to IS NULL` — partial unique (FR-021). Un empleado solo puede estar activo en un único equipo por cliente.
- `UNIQUE(client_id, department) WHERE is_primary_advisor = true AND date_to IS NULL` — partial unique. Máximo un primary advisor activo por (cliente, dept).
- `CHECK (is_primary_advisor = false OR role = 'asesor')` — solo asesores pueden ser primary.
- `CHECK (percentage >= 1 AND percentage <= 100)`.
- Índice `(team_id, date_to)` — soporta listado de miembros activos de un equipo.
- Índice `(client_id, department, date_to)` — soporta cálculo de coberturas cross-team.

**Reglas de servicio**:
- `client_id` y `department` deben coincidir con los del `ClientTeam` referenciado (validado en `assert-team-consistency.helper.ts`).
- `date_from` ≥ `team.start_date` y, si `team.end_date IS NOT NULL`, `date_to ≤ team.end_date`.
- `date_from` debe ser primer día del mes; `date_to` (si presente) último día.
- Recomputo de coberturas tras cada operación de escritura — si la operación dejaría coberturas en estado violador *de composición mínima* (responsable + asesor), persistir pero marcar el equipo `incomplete` y suprimir publish AMQP. Si la operación viola FR-021 (partial unique) o FR-017 (provided service), **rechazar** con 422.
- Roles excluyentes dentro del mismo cliente: cubierto por el partial unique sobre `(client_id, employee_id)`.
- `is_primary_advisor=true` requiere `role='asesor'`. Promoción/demotion vía endpoint dedicado (R-009).
- Cierre con baja del asesor (ADR-0017): el `DELETE /members/:id` lleva en el body `causesBaja: true` + `successorId`. Esos campos NO se persisten en `ClientTeamAssignment` — solo viajan al evento AMQP que `pd-service-obligations-api` consume para reasignar tareas. La asignación cerrada se distingue por `date_to IS NOT NULL` sin más; el "porqué" del cierre vive en el change log (US2) o en el lado consumidor.

---

### `ClientAssignment` (legacy — congelada)

Tabla: `client_assignment`

**No se modifica el schema en US1**. Post-deploy:
- Se mantiene tal cual (con su `team_id` nullable heredado de M0 y su `percentage` siempre = 100).
- No se le añaden `is_primary_advisor`, `version`, `created_by` ni `created_at` — esas columnas viven únicamente en `ClientTeamAssignment`.
- Las filas activas se **copian** (no se mueven) a `client_team_assignment` por el script de migración por cliente; queda como historial inmutable.
- El servicio deja de escribir en esta tabla a partir del cutover (ADR-0009).
- Eventualmente se renombrará a `client_assignment_legacy` o se archivará — fuera de scope de US1.

---

### `ProvidedService` (existe — solo lectura en US1)

Tabla: `provided_service`

Solo se consulta — no se modifica. La validación FR-017 se hace con:

```sql
SELECT COUNT(*) FROM provided_service
WHERE client_id = $1
  AND active = true
  AND family = $2  -- 'fiscal' o 'laboral', mapeo 1:1 con Department
```

Si count = 0 → rechazar con `CLIENT_TEAM_NO_PROVIDED_SERVICE_FOR_DEPARTMENT` (HTTP 422).

---

### `ClientTeamAssignmentChange` — **diferida**

Tabla de auditoría descrita en `er-diagram.md`. **No se crea en US1**. Las decisiones de shape (jsonb vs columnas, denormalización, `correlation_id`, `actor_type`, `occurred_at` vs `recorded_at`) están en `decisions.md` → OPEN-001. La auditoría histórica entra con US2/US3.

Para US1 se mantiene trazabilidad mínima vía:
- `created_by` + `created_at` en `ClientTeamAssignment` y `ClientTeam` (quién creó, cuándo).
- `updated_by` + `updated_at` + `version` (último editor y revisión).
- Las filas "cerradas" (`date_to IS NOT NULL`) actúan como histórico inmutable simple.
- El campo `created_by = 'system:migration:via:<email>'` permite trazar qué responsable disparó el script de promote desde la opción 1.

---

## Migraciones

### `Migration20260603xxxx-add-client-team-fields.ts`

DDL idempotente (no toca `client_assignment`):

```sql
ALTER TABLE client_team
  ADD COLUMN version smallint NOT NULL DEFAULT 1,
  ADD COLUMN created_by varchar NOT NULL DEFAULT 'system:migration';
```

### `Migration20260603xxxy-create-client-team-assignment.ts`

```sql
CREATE TABLE client_team_assignment (
  id uuid PRIMARY KEY,
  team_id uuid NOT NULL REFERENCES client_team(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  client_id uuid NOT NULL REFERENCES client(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  employee_id uuid NOT NULL REFERENCES employee(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  department varchar NOT NULL,  -- enum check below
  role varchar NOT NULL,        -- enum check below
  date_from date NOT NULL,
  date_to date,
  percentage smallint NOT NULL DEFAULT 100,
  is_primary_advisor boolean NOT NULL DEFAULT false,
  created_by varchar NOT NULL,
  created_at timestamp NOT NULL DEFAULT NOW(),
  updated_by varchar,
  updated_at timestamp NOT NULL DEFAULT NOW(),
  version smallint NOT NULL DEFAULT 1,
  CONSTRAINT cta_dept_enum CHECK (department IN ('fiscal','laboral')),
  CONSTRAINT cta_role_enum CHECK (role IN ('responsable','coordinador','asesor','tecnico')),
  CONSTRAINT cta_percentage_range CHECK (percentage BETWEEN 1 AND 100),
  CONSTRAINT cta_primary_only_asesor CHECK (is_primary_advisor = false OR role = 'asesor')
);

CREATE UNIQUE INDEX cta_unique_natural
  ON client_team_assignment (client_id, employee_id, role, department, date_from);

CREATE UNIQUE INDEX cta_one_active_per_client_employee
  ON client_team_assignment (client_id, employee_id) WHERE date_to IS NULL;

CREATE UNIQUE INDEX cta_one_primary_per_client_dept
  ON client_team_assignment (client_id, department) WHERE is_primary_advisor = true AND date_to IS NULL;

CREATE INDEX cta_team_active ON client_team_assignment (team_id, date_to);
CREATE INDEX cta_client_dept_active ON client_team_assignment (client_id, department, date_to);
```

`down()`: `DROP TABLE client_team_assignment`. Sin efecto sobre `client_assignment` legacy.

### `Migration20260603xxxz-backfill-from-legacy.ts`

Lógica imperativa (MikroORM `up()`), idempotente:

Para cada `(client_id, department)` con asignaciones activas en `client_assignment` (es decir, `date_to IS NULL`) que **no tengan ya** equivalente en `client_team_assignment`:

1. Si no existe `ClientTeam` activo para `(client_id, department)`, crearlo con `start_date = MIN(date_from de las filas legacy)`, `end_date = NULL`, `created_by = 'system:migration'`, `version = 1`.
2. Insertar en `client_team_assignment` una fila por cada `client_assignment` activa, copiando `client_id`, `employee_id`, `department`, `role`, `date_from`, `date_to=NULL`, `percentage` (siempre 100 en legacy), `team_id = <team_creado_o_existente>`, `created_by = 'system:migration'`.
3. Marcar el primer asesor activo (`ORDER BY date_from, id`) con `is_primary_advisor = true`. Si no hay asesor → dejar sin primary (equipo queda `incomplete` post-migración, visible en UI con banner).

`down()`: noop (los datos legacy en `client_assignment` siguen intactos; las filas creadas en `client_team_assignment` se pueden borrar manualmente si hace falta).

**Nota**: esta migración cubre el "safety net" (opción 6 — ADR-0009). El flujo principal sigue siendo el script de promote por cliente disparado desde el banner (opción 1), que escribe `created_by = 'system:migration:via:<email>'` para trazar al responsable que lo activó.

---

## Errores y códigos

Se amplían en `src/domain/constants/client-team-errors.ts`:

| Código | HTTP | Descripción |
|--------|------|-------------|
| `CLIENT_TEAM_NOT_FOUND` | 404 | Equipo no existe |
| `CLIENT_TEAM_NO_PROVIDED_SERVICE_FOR_DEPARTMENT` | 422 | FR-017 — no hay servicio activo en ese dept |
| `CLIENT_TEAM_DATE_NOT_MONTH_BOUNDARY` | 422 | FR-012 |
| `CLIENT_TEAM_VERSION_CONFLICT` | 409 | Optimistic concurrency (ADR-0010) |
| `CLIENT_TEAM_ASSIGNMENT_NOT_FOUND` | 404 | Asignación no existe |
| `CLIENT_TEAM_ASSIGNMENT_DUPLICATE_ACTIVE` | 422 | FR-021 — partial unique `(client_id, employee_id) WHERE date_to IS NULL` |
| `CLIENT_TEAM_ASSIGNMENT_PRIMARY_REQUIRES_ASESOR` | 422 | `is_primary_advisor=true` con `role≠asesor` |
| `CLIENT_TEAM_ASSIGNMENT_PRIMARY_CONFLICT` | 422 | Ya existe primary advisor activo para `(client, department)` |
| `CLIENT_TEAM_ASSIGNMENT_TEAM_MISMATCH` | 422 | `client_id`/`department` no coinciden con el team |
| `CLIENT_TEAM_ASSIGNMENT_DATE_OUTSIDE_TEAM_RANGE` | 422 | `date_from < team.start_date` o `date_to > team.end_date` |
| `CLIENT_TEAM_ASSIGNMENT_SUCCESSOR_REQUIRED` | 400 | DELETE con `causesBaja=true` sin `successorId` (ADR-0017) |
| `CLIENT_TEAM_ASSIGNMENT_VERSION_CONFLICT` | 409 | Optimistic concurrency en `ClientTeamAssignment` |
