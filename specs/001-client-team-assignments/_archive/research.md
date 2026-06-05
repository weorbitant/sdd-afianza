# Phase 0 — Research (US1)

**Feature**: 001-client-team-assignments
**Date**: 2026-06-03
**Scope**: US1 only — el resto de decisiones técnicas para US2..US4 viven en `decisions.md` o en `OPEN-001`.

La mayor parte de los "unknowns" ya están resueltos en `decisions.md` (ADRs 0001..0017) y en las sesiones de clarify (`spec.md ## Clarifications`). Este documento consolida solo los que afectan a US1 y traza el origen.

---

## R-001 · Granularidad de fechas

**Decisión**: híbrida — columna `date`, servicio valida `dateFrom = primer día del mes` y `dateTo = último día del mes`. UI permite solo seleccionar mes.

**Rationale**: alinea con el ciclo mensual de rentabilidad de `pd-service-obligations-api` y evita migración de esquema (las filas legacy con fechas no-boundary se grandfather-ean).

**Alternatives considered**: daily (rechazado por complejidad), monthly puro vía varchar (rechazado — requiere migración invasiva).

**Source**: `decisions.md` → ADR-0001 · spec.md FR-012 · Clarifications 2026-05-29.

---

## R-002 · Modelo de validación 100%

**Decisión**: **dos coberturas independientes por (cliente, departamento)** — asesores 100% + técnicos 100%, agregando entre todos los equipos de un mismo cliente+depto. Responsable y coordinador NO suman. Si un departamento no tiene técnicos en ningún equipo del cliente, ese cobertura se considera "no aplicable" (no bloquea).

**Rationale**: confirmado por PO 2026-06-01 con el frame `08-multi-equipo/01-multi-equipo-fiscal-larsa-costa.png`. Refleja la realidad operativa: el cliente se distribuye entre asesores y entre técnicos por separado.

**Alternatives considered**: cobertura único por equipo (ADR-0008 — invalidado), cobertura único por cliente+depto sin distinguir rol (rechazado — no refleja rentabilidad correcta).

**Source**: spec.md FR-003 · Clarifications 2026-06-01 (sesión PO) · supersede ADR-0008.

---

## R-003 · Persistencia inmediata vs. borrador+commit

**Decisión**: persistencia inmediata por miembro (POST/PATCH/DELETE individuales). El estado del equipo es derivado: `incomplete` mientras coberturas ≠ 100% o falte responsable / asesor / `isPrimaryAdvisor` único; transiciona a `active` automáticamente cuando todo se cumple. Banner amarillo advisory en UI mientras `incomplete`, **sin bloquear el guardado de miembros**. El único bloqueo del botón Guardar es la **composición mínima** (1 responsable + 1+ asesor).

**Rationale**: alinea con los frames `05-vista-equipo-incompleto/*` y permite construir el equipo de forma fluida sin un endpoint extra de commit.

**Alternatives considered**: `POST /commit` con validación atómica (descartado — Clarifications 2026-05-29, invalidaba ADR-0007).

**Source**: spec.md FR-003 · Clarifications 2026-05-29 · PO 2026-06-01.

---

## R-004 · Concurrencia optimista

**Decisión**: columna `version smallint` en `ClientTeam` y `ClientAssignment`. El cliente envía `If-Match: <version>` en endpoints de escritura. 409 si la BD ya tiene una versión mayor. UI muestra *"El equipo ha cambiado, recarga para ver el estado más reciente"*.

**Rationale**: `updatedAt` tiene granularidad timestamp y permite colisiones en escrituras dentro del mismo milisegundo. `version` integer monotónico es exacto y barato.

**Alternatives considered**: `updatedAt` (descartado por la razón anterior), pessimistic locking (descartado — sobreingeniería).

**Source**: spec.md FR-022 · decisions.md ADR-0010 · PO ratification 2026-06-01.

---

## R-005 · Partial unique FR-021

**Decisión**: añadir `UNIQUE(client_id, employee_id) WHERE date_to IS NULL` además del unique existente `(client, employee, role, department, dateFrom)`. Refuerza FR-016 a nivel BD: un empleado, una sola asignación activa por cliente, incluso entre departamentos.

**Rationale**: defensa en profundidad — si la lógica de servicio falla, la BD rechaza el duplicado. Postgres soporta partial unique nativamente sin trigger.

**Alternatives considered**: trigger de exclusión (más caro, mismo resultado), solo validación en servicio (rechazada — Constitution security defense-in-depth).

**Source**: spec.md FR-016 + FR-021 · PO 2026-06-01 (opción B).

---

## R-006 · FR-017 — equipo requiere ProvidedService activo

**Decisión**: backend rechaza POST si no existe `ProvidedService` activo del cliente cuya `family` mapee al departamento del equipo (`fiscal` → Fiscal, `laboral` → Laboral). Frontend oculta el CTA en deptos sin servicios. Los equipos **existentes** sobreviven si todos los servicios del dept se dan de baja (la regla aplica a creación, no a invalidación).

**Rationale**: previene crear equipos para departamentos sin contrato activo — fuente de informes inconsistentes en Plataforma del Dato.

**Source**: spec.md FR-017 · Clarifications 2026-06-01 · OQ-008 (huérfanos) pendiente — no bloquea US1.

---

## R-007 · Migración legacy FR-013

**Decisión**: migración MikroORM en `pgi-service-pgi-api/src/migrations/Migration20260603xxxy-backfill-legacy-team-id.ts`. Recorre todos los `ClientAssignment` activos (date_to IS NULL) agrupados por `(client_id, department)`. Para cada grupo:
1. Crea un `ClientTeam` con `start_date = MIN(date_from)`, `end_date = NULL`, `created_by = 'system:migration'`, `version = 1`.
2. Actualiza las filas del grupo con `team_id = <id del nuevo team>`.
3. Marca al primer asesor (orden por `date_from` ASC, luego `id` ASC) con `is_primary_advisor = true`. Si no hay asesor, deja el grupo sin primary — quedará `incomplete` post-migración hasta que un responsable designe uno.

**Idempotencia**: la migración chequea `team_id IS NULL` antes de procesar — re-ejecutar es noop.

**No destructiva**: no toca filas con `team_id` ya asignado ni filas con `date_to IS NOT NULL` (histórico).

**Rationale**: cumple FR-013 + permite que el responsable vea su equipo activo al abrir cualquier ficha post-deploy sin intervención manual.

**Alternatives considered**: migración perezosa (al abrir cada ficha — rechazado por complejidad de race conditions), script Node fuera de migration framework (rechazado — perdemos rollback nativo).

**Source**: spec.md FR-013 · Clarifications 2026-05-28.

---

## R-008 · Cuándo publicar el evento AMQP

**Decisión**: el domain service publica `clientAssignmentUpdated` solo cuando el equipo está en estado `active` tras la operación. Casos:
- Transición `incomplete → active`: publica todos los miembros activos del equipo (snapshot completo).
- Cambio en equipo ya `active` que lo mantiene `active`: publica solo el miembro modificado.
- Transición `active → incomplete`: **no** publica nada (los consumers downstream conservan el último snapshot válido).

**Rationale**: evita ruido en consumers durante construcción incremental del equipo. La transición `→ active` envía snapshot completo para garantizar consistencia.

**Source**: spec.md FR-014 · Clarifications 2026-05-29.

---

## R-009 · `isPrimaryAdvisor` — unicidad

**Decisión**: exactamente un `ClientAssignment` con `role='asesor'` y `is_primary_advisor=true` por (cliente, departamento) activo. Validación a nivel servicio (no BD por simplicidad — el conjunto activo es pequeño).

**Cómo se marca**:
- Si no hay ningún primary y se crea/promueve uno → directo.
- Si ya hay primary y se intenta promover otro → endpoint dedicado `PATCH /client-team-assignments/{id}/promote-primary` que **demote** atómicamente al actual y promueve al nuevo en la misma transacción.
- Eliminar un primary (cerrar con `date_to`) sin sucesor → la operación deja al equipo `incomplete` hasta que se designe otro. Permitido (no bloquea).

**Rationale**: simplifica la API y evita estados intermedios con dos primarys o cero. La validación BD-level (partial unique sobre `is_primary_advisor=true AND date_to IS NULL`) se considera para iteración futura.

**Source**: spec.md FR-005 · Clarifications 2026-05-29 (decisión OQ-002).

---

## R-010 · OPEN — diferidos para iteraciones siguientes

Decisiones que **no** se resuelven en US1 y se han registrado como diferidas:

- **OPEN-001 (change log shape)**: forma de `ClientTeamAssignmentChange` (jsonb vs columnas explícitas, denormalización, correlation_id, etc.). Ver `decisions.md` → OPEN-001.
- **FR-018** ampliación del payload AMQP con `teamId`/`percentage`: se difiere a la iteración que toque también el subscriber de data-factory.
- **OQ-008** equipos huérfanos al cerrar todos los servicios contratados de un departamento.
- **OQ-014..OQ-019** decisiones pendientes de PO (sucesor obligatorio, fallback de Plataforma del Dato, visibilidad de % en histórico, baja Azure AD, cambio de departamento del empleado).

---

## Resumen — NEEDS CLARIFICATION pendientes

**Ninguna** para US1. Todos los unknowns están resueltos por decisiones previas. El plan puede pasar a Phase 1 (data-model + contracts) sin más input de PO.
