# Data Model — DEVPT-518 v2

**Feature**: 001-client-team-assignments
**Date**: 2026-06-04 (reescrito desde cero alineado a `spec.md` v2 y `er-diagram.md` v2)
**Status**: Draft — espera revisión de plan/contracts antes de generar tasks

> **Ámbito**: tablas y migraciones para US1 + lo que afecta a US2/US3 a nivel de schema. La autoridad de modelo es `er-diagram.md`; la autoridad funcional es `spec.md` v2. Este documento detalla los **deltas vs. el schema actual de producción** y las reglas de validación por entidad.

---

## 1. Modelo

### 1.1. `client_team` (existe — recortar)

Tabla: `client_team`

| Columna | Tipo | Estado | Notas |
|---------|------|--------|-------|
| `id` | uuid PK | existe | generado en app (uuidv4) |
| `client_id` | uuid FK → client | existe | NOT NULL, `updateRule: cascade`, `deleteRule: restrict` |
| `department` | enum (`fiscal` \| `laboral`) | existe | NOT NULL |
| `created_by` | varchar | **NEW** | email backoffice o `system:onboarding` |
| `updated_by` | varchar | **NEW** | email backoffice o `system:onboarding` |
| `created_at` | timestamp | existe | `onCreate` |
| `updated_at` | timestamp | existe | `onUpdate` |
| `version` | smallint | **NEW** | default `1`, incrementa en cada UPDATE (ADR-0010) |
| ~~`start_date`~~ | ~~date~~ | **DROP** | La vida del team se infiere de sus asignaciones |
| ~~`end_date`~~ | ~~date~~ | **DROP** | Mismo motivo |

**Constraints**:
- Índice no único `(client_id, department)` — soporta query "teams del cliente en el departamento X" en hot path.
- **Sin** unique sobre `(client_id, department)` — multi-equipo permitido (PO 2026-06-01).

**Reglas de servicio**:
- `client_id`, `department` y `created_by` no editables tras creación.
- `client_team` se crea vacío (sin asignaciones); la primera asignación que entra fija su vida útil de facto.

**Estado derivado** (calculado on-the-fly por `compute-team-status.helper.ts`):
- `complete` si en `(client_id, department)`: hay 1 responsable activo, hay ≥1 asesor activo, cobertura asesores = 100%, cobertura técnicos = 100% (o no hay técnicos), hay exactamente 1 asesor con `is_main=true` activo.
- `incomplete` si alguna condición falla. El servicio suprime publicación AMQP downstream (FR-016 v2) y la UI muestra banner.

---

### 1.2. `client_team_assignment` (NUEVA)

Tabla: `client_team_assignment`

Reemplaza el rol que tenía `client_assignment` en producción. Todas las asignaciones nuevas viven aquí; la tabla legacy queda **congelada** (ver §1.4).

| Columna | Tipo | Notas |
|---------|------|-------|
| `id` | uuid PK | generado en app (uuidv4) |
| `client_team_id` | uuid FK → client_team | NOT NULL, `updateRule: cascade`, `deleteRule: restrict` |
| `employee_id` | uuid FK → employee | NOT NULL |
| `role` | enum (`responsable` \| `coordinador` \| `asesor` \| `tecnico`) | NOT NULL |
| `date_from` | date | NOT NULL. Vía API normal: primer día del mes. Vía onboarding: tal cual recibida. Tramos voided (FR-007 v2): `date_to = date_from - 1 día`. |
| `date_to` | date | NULL = tramo activo. Cuando NOT NULL: último día del mes (API normal), tal cual (onboarding), o `date_from - 1` si el tramo está voided. |
| `percentage` | smallint | NOT NULL, default 100, CHECK `1..100`. |
| `is_main` | boolean | NOT NULL, default `false`. CHECK: solo `true` si `role='asesor'`. Reemplaza al antiguo `is_primary_advisor`. |
| `created_at` | timestamp | `onCreate`. |
| `updated_at` | timestamp | `onUpdate`. |
| `version` | smallint | NOT NULL, default `1`, incrementa en cada UPDATE (ADR-0010). |

> **Decisión 2026-06-04**: el "quién" (created_by/updated_by) **NO** se persiste aquí. Vive exclusivamente en `client_team_assignment_change` (§1.3), una fila por mutación. Esto evita perder el rastro cuando una asignación se modifica varias veces: el log conserva cada autor; la asignación solo retiene el último estado.

**Constraints de BD**:
- `CHECK (percentage BETWEEN 1 AND 100)` — `cta_percentage_range`.
- `CHECK (is_main = false OR role = 'asesor')` — `cta_main_only_asesor`.
- Índice `(client_team_id, date_to)` — listado de miembros activos de un team.
- Índice `(employee_id, date_to)` — histórico del empleado.

**Constraints que NO se imponen en BD** (validación de servicio únicamente — decisión v2):
- "Máximo 1 asesor con `is_main=true` activo por `(client_id, department)`" — requeriría JOIN con `client_team`, no expresable como partial unique. Validado en `assert-single-main-asesor.helper.ts` dentro de la transacción con `SELECT ... FOR UPDATE` sobre `client` (FR-024 v2).
- Cualquier unicidad de tipo `(client_id, employee_id)` o `(client_id, employee_id, role)` — **explícitamente eliminada** en v2 (FR-013 v2). Misma persona puede tener responsable+coordinador+asesor activos a la vez, o accidentalmente dos del mismo rol activos. El sistema confía en el usuario.

**Reglas de servicio**:

- **Normalización de fechas (API normal — FR-002 v2)**:
  - `date_from` se ajusta a primer día del mes del `effectiveDate` solicitado.
  - `date_to` del tramo que se cierra se ajusta a último día del mes anterior.
- **Rechazo de mes pasado (FR-003 v2)**:
  - Si `effectiveDate < primer día del mes en curso`, rechazar con `CLIENT_TEAM_ASSIGNMENT_PAST_DATE_NOT_ALLOWED` (HTTP 422).
- **Preservación de tramos futuros (FR-006-bis v2)**:
  - Al insertar un tramo con `effectiveDate` futuro, si ya existe un tramo posterior para el mismo `(client_team_id, employee_id, role)`, `date_to` del nuevo tramo se ajusta al día anterior al `date_from` del futuro pre-existente.
- **Machacado de tramos del mes en curso (FR-007 v2)**:
  - Si una operación toca un tramo cuyo `date_from = primer día del mes en curso`, el tramo se UPDATE in-place (si el miembro sigue con otros atributos) o se **voida** (si el miembro sale) — `UPDATE date_to = date_from - 1 día`. No hay DELETE físico: la fila persiste para auditoría, pero queda invisible a queries de vista vigente. La acción se registra en `client_team_assignment_change` con `action='voided'`.
- **Onboarding (FR-004 v2)**:
  - Tramos creados vía subscriber AMQP `client-onboarding-assignment` conservan las fechas tal cual recibidas. Sin normalización, sin rechazo de mes pasado, sin preservación (no debería haber tramos futuros pre-existentes en alta inicial — pero si los hubiera, ver decisión OQ-005).
- **Validación de `ProvidedService` (FR-012 v2)**:
  - Antes de crear/promocionar una asignación en `(client_id, department)`, comprobar que existe `provided_service.active = true` con `family = department`. Si no, rechazar con `CLIENT_TEAM_ASSIGNMENT_NO_PROVIDED_SERVICE` (HTTP 422).
- **Concurrencia**:
  - Toda operación de escritura adquiere `SELECT ... FOR UPDATE` sobre la fila `client` antes de leer cobertura. Esto serializa transiciones complete/incomplete y garantiza "exactamente un evento AMQP por transición" (ADR-0015).
  - Optimistic concurrency con `version` para mutaciones individuales (UPDATE de % o `is_main` sobre tramo activo).

---

### 1.3. `client_team_assignment_change` (NUEVA — promovida a US-05)

Tabla de auditoría. **Se crea en US-01** (en T-SETUP-1 junto con `client_team_assignment`) porque cada mutación de US-01/02/03/04 inserta filas aquí dentro de la misma transacción que mutó la asignación. La lectura de este log es lo que sirve US-05.

| Columna | Tipo | Notas |
|---------|------|-------|
| `id` | uuid PK | generado en app (uuidv4) |
| `client_team_assignment_id` | uuid FK → client_team_assignment | NOT NULL, `deleteRule: restrict` (no se borra el tramo nunca — se voida). |
| `action` | enum | `opened` \| `closed` \| `percentage_changed` \| `role_changed` \| `main_changed` \| `voided` |
| `employee_id_before` | uuid | NULL si la acción crea desde cero (`opened`) |
| `employee_id_after` | uuid | NULL si la acción solo cierra/voida |
| `role_before` | enum | NULL si no aplica |
| `role_after` | enum | NULL si no aplica |
| `percentage_before` | smallint | NULL si no aplica |
| `percentage_after` | smallint | NULL si no aplica |
| `is_main_before` | boolean | NULL si no aplica |
| `is_main_after` | boolean | NULL si no aplica |
| `date_from_before` | date | NULL si no aplica |
| `date_from_after` | date | NULL si no aplica |
| `date_to_before` | date | NULL si no aplica |
| `date_to_after` | date | NULL si no aplica |
| `created_at` | timestamp | `onCreate` — momento del cambio. Inmutable. |
| `updated_at` | timestamp | `onUpdate` — normalmente igual a `created_at`. Se actualiza solo si se corrige el registro de audit. |
| `created_by` | varchar | NOT NULL, email del backoffice o `system:onboarding`. Quién hizo el cambio. |
| `updated_by` | varchar | NULL salvo corrección posterior del registro. |

**Filas por acción** (qué columnas se llenan):

| `action` | Columnas con valor |
|---|---|
| `opened` | Solo los `_after` (el tramo nuevo completo). |
| `closed` | `date_to_before = NULL`, `date_to_after = fecha de cierre`. |
| `percentage_changed` | `percentage_before` y `percentage_after`. |
| `role_changed` | `role_before` y `role_after`. |
| `main_changed` | `is_main_before` y `is_main_after`. |
| `voided` | Snapshot completo en los `_before`; `date_to_before = NULL` (o valor original), `date_to_after = date_from - 1 día`. |

**Constraints de BD**:
- CHECK `cta_change_action_enum` sobre los valores válidos del enum `action`.
- Índice `(client_team_assignment_id, created_at DESC)` — para reconstruir el historial de una asignación en orden cronológico.
- Índice `(created_at DESC)` — para listados globales por rango.

**Reglas de servicio**:
- Cada operación de US-01/02/03/04 que muta `client_team_assignment` (INSERT, UPDATE, void) inserta una o más filas en `client_team_assignment_change` **dentro de la misma transacción**. Atomicidad obligatoria: si falla la inserción del change, falla toda la operación.
- El log es **read-only desde la API**. No hay endpoints REST de mutación. Las correcciones se hacen vía script de mantenimiento con `updated_at`/`updated_by` reflejando la corrección.

---

### 1.4. `client_assignment` (legacy — congelada)

Tabla: `client_assignment`

**No se modifica el schema, no se migra, no se sigue escribiendo**. Post-deploy:
- Mantiene su forma actual (incluyendo `team_id` nullable y `percentage` siempre 100 heredados de M0).
- No se le añaden columnas: `is_main`, `version`, ni nada nuevo.
- El servicio deja de escribir en esta tabla a partir del cutover.
- Cuando un responsable abre la ficha de un cliente cuyo equipo activo aún vive en `client_assignment`, la UI nueva muestra el equipo **vacío** — el responsable lo vuelve a meter manualmente (3-5 personas, segundos). Sin script de migración, sin banner, sin `migrated_from_legacy`. La fila legacy queda como historial inmutable.
- Renombrar a `client_assignment_legacy` o archivar — fuera de scope de US1.

---

### 1.5. `provided_service` (existe — solo lectura)

Tabla: `provided_service`

Solo se consulta. Validación FR-012 v2:

```sql
SELECT 1 FROM provided_service
WHERE client_id = $1
  AND active = true
  AND family = $2  -- 'fiscal' o 'laboral', mapeo 1:1 con department
LIMIT 1;
```

Sin coincidencia → rechazar con `CLIENT_TEAM_ASSIGNMENT_NO_PROVIDED_SERVICE` (HTTP 422).

---

## 2. Migraciones

### 2.1. `Migration20260604xxxx-add-client-team-audit-fields.ts`

Añade auditoría + version a `client_team`. Elimina `start_date`/`end_date` que dejan de tener sentido.

```sql
ALTER TABLE client_team
  ADD COLUMN created_by varchar NOT NULL DEFAULT 'system:migration',
  ADD COLUMN updated_by varchar,
  ADD COLUMN version smallint NOT NULL DEFAULT 1;

ALTER TABLE client_team
  DROP COLUMN start_date,
  DROP COLUMN end_date;
```

`down()`: `ADD start_date date`, `ADD end_date date`, `DROP COLUMN created_by, updated_by, version`. No restaura valores históricos de fechas (no críticos).

**Riesgo**: si hay procesos que leen `client_team.start_date`/`end_date`, romperán. Auditar consumers antes de aplicar. Si los hay, separar en dos migraciones (primero quitar lecturas, luego DROP COLUMN).

### 2.2. `Migration20260604xxxy-create-client-team-assignment.ts`

```sql
CREATE TABLE client_team_assignment (
  id uuid PRIMARY KEY,
  client_team_id uuid NOT NULL REFERENCES client_team(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  employee_id uuid NOT NULL REFERENCES employee(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  role varchar NOT NULL,
  date_from date NOT NULL,
  date_to date,
  percentage smallint NOT NULL DEFAULT 100,
  is_main boolean NOT NULL DEFAULT false,
  created_at timestamp NOT NULL DEFAULT NOW(),
  updated_at timestamp NOT NULL DEFAULT NOW(),
  version smallint NOT NULL DEFAULT 1,

  CONSTRAINT cta_role_enum CHECK (role IN ('responsable', 'coordinador', 'asesor', 'tecnico')),
  CONSTRAINT cta_percentage_range CHECK (percentage BETWEEN 1 AND 100),
  CONSTRAINT cta_main_only_asesor CHECK (is_main = false OR role = 'asesor')
);

CREATE INDEX cta_team_active ON client_team_assignment (client_team_id, date_to);
CREATE INDEX cta_employee_active ON client_team_assignment (employee_id, date_to);
```

`down()`: `DROP TABLE client_team_assignment`. Sin efecto sobre legacy.

### 2.3. `Migration20260604xxxA-create-client-team-assignment-change.ts`

```sql
CREATE TABLE client_team_assignment_change (
  id uuid PRIMARY KEY,
  client_team_assignment_id uuid NOT NULL REFERENCES client_team_assignment(id) ON UPDATE CASCADE ON DELETE RESTRICT,
  action varchar NOT NULL,
  employee_id_before uuid,
  employee_id_after uuid,
  role_before varchar,
  role_after varchar,
  percentage_before smallint,
  percentage_after smallint,
  is_main_before boolean,
  is_main_after boolean,
  date_from_before date,
  date_from_after date,
  date_to_before date,
  date_to_after date,
  created_at timestamp NOT NULL DEFAULT NOW(),
  updated_at timestamp NOT NULL DEFAULT NOW(),
  created_by varchar NOT NULL,
  updated_by varchar,

  CONSTRAINT cta_change_action_enum CHECK (action IN (
    'opened', 'closed', 'percentage_changed', 'role_changed', 'main_changed', 'voided'
  ))
);

CREATE INDEX cta_change_by_assignment ON client_team_assignment_change (client_team_assignment_id, created_at DESC);
CREATE INDEX cta_change_recent ON client_team_assignment_change (created_at DESC);
```

`down()`: `DROP TABLE client_team_assignment_change`.

**No hay**:
- Migración de backfill desde `client_assignment` (no se migra — §1.4).
- Partial unique sobre `(client_id, employee_id)` (FR-013 v2 elimina).
- Partial unique sobre asesor main por `(client_id, department)` (no expresable sin JOIN — validación servicio).
- CHECK `chk_causes_baja_only_when_closed` (no hay columna `causes_baja` en v2).

### 2.4. `Migration20260604xxxz-noop-legacy-freeze.ts` — opcional

Solo si se quiere materializar el freeze de `client_assignment` con un trigger que rechace nuevos INSERTs/UPDATEs post-cutover. **Recomendado dejar para una segunda iteración** — primero ver si algún consumer aún escribe.

---

## 3. Errores y códigos

Definidos en `src/domain/constants/client-team-errors.ts`:

| Código | HTTP | Cuándo |
|--------|------|--------|
| `CLIENT_TEAM_NOT_FOUND` | 404 | Team no existe |
| `CLIENT_TEAM_VERSION_CONFLICT` | 409 | Optimistic concurrency en team (ADR-0010) |
| `CLIENT_TEAM_ASSIGNMENT_NOT_FOUND` | 404 | Asignación no existe |
| `CLIENT_TEAM_ASSIGNMENT_VERSION_CONFLICT` | 409 | Optimistic concurrency en asignación |
| `CLIENT_TEAM_ASSIGNMENT_PAST_DATE_NOT_ALLOWED` | 422 | `effectiveDate < primer día del mes en curso` (FR-003 v2) |
| `CLIENT_TEAM_ASSIGNMENT_NO_PROVIDED_SERVICE` | 422 | No hay `provided_service` activo con `family = department` (FR-012 v2) |
| `CLIENT_TEAM_ASSIGNMENT_MAIN_ONLY_ASESOR` | 422 | `is_main=true` con `role ≠ 'asesor'` (CHECK BD) |
| `CLIENT_TEAM_ASSIGNMENT_DUPLICATE_MAIN` | 422 | Intento de marcar `is_main=true` cuando ya hay un asesor main activo en `(client, department)` (validación servicio) |
| `CLIENT_TEAM_ASSIGNMENT_INVALID_ROLE` | 422 | `role` fuera del enum |
| `CLIENT_TEAM_ASSIGNMENT_INVALID_PERCENTAGE` | 422 | `percentage` fuera de 1..100 |

**No existen** (v2):
- `CLIENT_TEAM_ASSIGNMENT_DATE_NOT_MONTH_BOUNDARY` — el backend normaliza, no rechaza.
- `CLIENT_TEAM_ASSIGNMENT_DUPLICATE_ACTIVE` — sin partial unique `(client, employee)`.
- `CLIENT_TEAM_ASSIGNMENT_DATE_OUTSIDE_TEAM_RANGE` — sin `start_date`/`end_date` en team.
- `CLIENT_TEAM_ASSIGNMENT_TEAM_MISMATCH` — sin denormalizados.
- `CLIENT_TEAM_ASSIGNMENT_CAUSES_BAJA_ON_ACTIVE` — sin `causes_baja`.
- `CLIENT_TEAM_ASSIGNMENT_SUCCESSOR_REQUIRED` — flujo ADR-0017 eliminado (reasignación automática vía AMQP).

---

## 4. Campos derivados (no persisten)

### 4.1. `inClientSince` — antigüedad del empleado en el cliente

Calculado server-side en lectura. Helper: `compute-in-client-since.helper.ts` (renombrado desde `compute-employee-tenure.helper.ts` en la v2).

Algoritmo: para `(client_id, employee_id)`, recorrer las asignaciones **no voided** (`date_to IS NULL OR date_to >= date_from`) ordenadas por `date_from` descendente. Avanzar mientras los tramos encadenen sin hueco (`date_to` del tramo previo en el orden cronológico >= `date_from - 1` del siguiente). `inClientSince` = `date_from` del tramo más antiguo de esa cadena continua.

- Si la persona salió y volvió (hueco real entre tramos), `inClientSince` arranca del último reingreso.
- Si la persona tiene varios tramos contiguos por cambios de % o de rol, la cadena es continua y `inClientSince` se preserva.
- Caso accidental (dos tramos activos simultáneos del mismo empleado): se tratan como continuos (no rompen cadena) — propuesta OQ-004 spec v2.
- Tramos voided (`date_to < date_from`, FR-007 v2): se **ignoran completamente** — no rompen ni extienden cadenas.

### 4.2. Cobertura por rol — `CoverageStatus`

Calculado server-side. Helper: `sum-coverage-percentage.helper.ts`.

Para `(client_id, department, role, asOfDate)`:

```sql
SELECT COALESCE(SUM(cta.percentage), 0) AS coverage
FROM client_team_assignment cta
JOIN client_team ct ON ct.id = cta.client_team_id
WHERE ct.client_id = $1
  AND ct.department = $2
  AND cta.role = $3
  AND cta.date_from <= $4
  AND (cta.date_to IS NULL OR cta.date_to >= $4);
```

Resultado por rol:
- `asesor`: debe sumar 100 → si no, `incomplete`.
- `tecnico`: si hay ≥1 técnico activo, debe sumar 100. Si no hay técnicos, "no aplicable" (no bloquea).
- `responsable`/`coordinador`: no entran en la suma — 100% implícito (ADR-0012).

### 4.3. `getActiveTeamAt(clientId, department, date)`

Vista vigente a fecha. Devuelve todas las `client_team_assignment` cuyo `date_from <= date AND (date_to IS NULL OR date_to >= date)` para los teams del `(client_id, department)`. Esta misma fórmula excluye automáticamente los tramos voided (`date_to < date_from`). Cada miembro lleva su `inClientSince` calculado.

---

## 5. Lo que cambia respecto al data-model v1 (archivado)

| v1 (`_archive/data-model.md`) | v2 (este doc) |
|---|---|
| `ClientTeam` con `start_date`/`end_date` | Sin temporalidad — DROP COLUMN |
| `ClientTeamAssignment` con `client_id`/`department` denormalizados | Sin denormalizados — acceso vía JOIN |
| `is_primary_advisor` | `is_main` |
| Columna `causes_baja` + CHECK `chk_causes_baja_only_when_closed` | Eliminadas — flujo ADR-0017 superseded |
| Partial unique `(client_id, employee_id) WHERE date_to IS NULL` | Eliminado — FR-013 v2 (sin unicidad de empleado por cliente) |
| Partial unique `(client_id, department) WHERE is_primary_advisor = true AND date_to IS NULL` | Eliminado de BD — validación servicio (no expresable sin JOIN) |
| Migraciones M1a + M1b + M2 con backfill desde `client_assignment` | Migración única `create-client-team-assignment` + congelar legacy (sin backfill) |
| Validación `date_from = primer día del mes` con error 422 | Backend normaliza automáticamente, no rechaza — excepto si mes pasado |
| Sin soporte explícito de cambios futuros con preservación | FR-006-bis v2 — preservación de tramos futuros pre-existentes |

---

## 6. Pendientes

- Confirmar nombre exacto del routing key de onboarding con el producer (OQ-005 spec v2). El subscriber se llamará `ClientOnboardingAssignmentSubscriber` y vivirá en `src/application/amqp/client-onboarding-assignment-subscriber/`.
- Decidir qué hacer si el evento de onboarding llega con tramos que solapan tramos ya existentes en `client_team_assignment` (no debería ocurrir, pero defensivo). Propuesta inicial: rechazar (`OnboardingPayloadException`) y dejar el mensaje en DLQ.
- Auditar consumers de `client_team.start_date`/`end_date` antes de aplicar la migración 2.1 (riesgo de breakage cross-service).
