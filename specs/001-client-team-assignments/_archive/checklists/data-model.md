# Data Model Quality Checklist — DEVPT-518

**Purpose**: Validate that the data model (entities, constraints, migrations, cross-service alignment) is complete, clear and safe BEFORE `/speckit-tasks`. Requirements-quality check, not implementation test.

**Created**: 2026-06-02
**Reviewed (batch)**: 2026-06-03 — auto-verdict por Claude contra `data-model.md`, `research.md`, `decisions.md` (ADRs 0010-0017) y `er-diagram.md`. Items con `→ GAP:` requieren acción antes de `/speckit-implement`.
**Feature**: [spec.md](../spec.md) · [data-model.md](../data-model.md) · [decisions.md](../decisions.md)
**Audience**: author (pre-tasks gate)
**Depth**: focused (data model only — API y funcional cubiertos en otros checklists)

> Marca [x] cuando la pregunta tenga respuesta clara en `data-model.md` + ADRs. "No" = gap que conviene cerrar antes de generar tareas o migraciones.

## ⚠️ Unresolved decisions afectando el modelo

- [ ] CHK001 — ¿Está resuelta la decisión sobre **onboarding ↔ ClientTeam** (#21 parcial)? [Pendiente, Spec §Decisiones-PO]
                → Pendiente: assumption MVP = `applyFromClientOnboarding` crea `team_id = NULL` (ADR-0014). Si PO opta por crear "Equipo inicial" automático, hay que modificar `applyFromClientOnboarding` y posiblemente añadir un valor enum a `createdBy`.
                → Verdict: assumption MVP confirmada vía ADR-0014; R-007 backfill-ea. Sigue pendiente PO sólo si cambia el criterio.
- [ ] CHK002 — ¿Está resuelta la decisión sobre **routing de tareas por rol** (#20 Producto)? [Pendiente, Spec §Decisiones-PO]
                → Pendiente: si Producto define mapping `ObligationCategory → role`, hay que extender `Obligation` con `roleResponsible` — nuevo campo + migración aparte. Assumption MVP: todo al asesor principal, sin nuevo campo.
                → Verdict: **N/A US1** — el routing por rol es responsabilidad de `pd-service-obligations-api`. Sin acción en US1.

## Entity field completeness

- [x] CHK003 — ¿Está documentado para CADA campo de `ClientTeam` y `ClientAssignment`: tipo SQL, nullable, default, regla de validación? [Completeness, data-model.md]
                → Tablas en `data-model.md:17-29` y `:53-71` cubren tipo, nullable, default, reglas de servicio aparte.
- [x] CHK004 — ¿Está cada campo nuevo (`is_primary`, `is_primary_advisor`, `causes_baja`, `version`) presente tanto en la entity TypeScript como en la migración? [Consistency, data-model.md §M1a]
                → Para **US1**: `is_primary_advisor`, `version`, `created_by`, `created_at` están en M1a (`data-model.md:122-126`). `is_primary` y `causes_baja` son US4 — explícitamente fuera de scope US1.
- [x] CHK005 — ¿Está especificada la columna `version` como `smallint` con default 1 y MikroORM decorator `@Property({ version: true })` en ambas entities? [Clarity, ADR-0010]
                → SQL: smallint default 1 (data-model.md:122-123). Decorator MikroORM se aplicará en T011/T012 de tasks.md per ADR-0010.
- [x] CHK006 — ¿Está documentada la regla "team puede tener `endDate` null o un día específico, pero NO valores intermedios" (inmutable post-cierre)? [Clarity, Spec §FR-009]
                → data-model.md `:35-38` "end_date... último día del mes" + "No se permite editar... una vez creado". Refuerzo BD-level no incluido (ver CHK014).

## Relationships & FKs

- [ ] CHK007 — ¿Tiene cada FK declarada su política `ON UPDATE` y `ON DELETE` (CASCADE / RESTRICT / SET NULL)? [Completeness, data-model.md]
                → **GAP parcial**: `client_id` en `ClientTeam` tiene `updateRule: cascade, deleteRule: restrict`. **Falta declararlo explícitamente para `team_id`, `employee_id` y `client_id` en `ClientAssignment`**. Acción: añadir tabla "FK policies" en data-model.md.
- [x] CHK008 — ¿Está justificado por qué `team_id` es nullable en `ClientAssignment` (compatibilidad con onboarding legacy)? [Clarity, ADR-0014]
                → data-model.md:60 "era nullable; la migración FR-013 lo rellena, luego se añade NOT NULL en una segunda migración una vez verificado backfill".
- [x] CHK009 — ¿Está documentada la decisión de "logical FK, sin constraint BD" para `team_id` en `pd-service-data-factory`? [Clarity, ADR-0011]
                → ADR-0011 cubierto. N/A US1 (no se toca data-factory en US1).

## Constraints (uniques + CHECKs)

- [x] CHK010 — ¿Está la lista COMPLETA de partial uniques nuevos enumerada en data-model.md (FR-021 + primary advisor + primary team)? [Completeness, data-model.md §M1b]
                → `UNIQUE(client_id, employee_id) WHERE date_to IS NULL` en M1a (data-model.md:125). El partial unique sobre `is_primary_advisor` se deja como service-level por R-009 (decisión explícita). "Primary team" no existe en US1.
- [ ] CHK011 — ¿Está documentado el DROP de `idx_client_team_active` y por qué (bloqueaba multi-team — ADR-0012)? [Clarity, data-model.md §M1a, ADR-0012]
                → **GAP**: data-model.md no menciona DROP de índices existentes. data-model.md:31 niega añadir unique pero no menciona drop. Acción: verificar en migraciones previas si existe `idx_client_team_active` y si bloquea multi-team; si existe, añadir DROP a M1a; si no, anotar "no existe — multi-team ya soportado".
- [x] CHK012 — ¿Están los CHECK constraints (`chk_primary_advisor_only_asesor`, `chk_causes_baja_only_when_closed`) documentados con expresión SQL exacta? [Completeness, ADR-0016]
                → `chk_primary_advisor_only_asesor`: `CHECK (is_primary_advisor = false OR role = 'asesor')` (data-model.md:124). `chk_causes_baja_only_when_closed` es US4.
- [x] CHK013 — ¿Está documentado el comportamiento esperado cuando un INSERT viola un partial unique (qué código de error responde el backend al cliente)? [Coverage, contracts/client-assignments-api.md]
                → `data-model.md §Errores` tabla → `CLIENT_ASSIGNMENT_DUPLICATE_ACTIVE` HTTP 422.

## State transitions

- [ ] CHK014 — ¿Está documentada la regla "transición `active → closed` es irreversible" a nivel BD (no solo a nivel servicio)? [Clarity, Spec §FR-009]
                → **GAP**: la irreversibilidad sólo se enforce a nivel servicio. No hay trigger / check. Acción: aceptar como deuda y documentarlo explícitamente, o añadir `CHECK (end_date IS NULL OR end_date >= start_date) NOT VALID + UPDATE trigger`. Recomendación: aceptar deuda (servicio basta; auditoría con `updated_by`).
- [x] CHK015 — ¿Está especificado qué transiciones disparan publish AMQP y cuáles se suprimen (incomplete → no emite)? [Consistency, ADR-0013, FR-014]
                → research.md R-008.
- [x] CHK016 — ¿Está documentada la lógica del auto-promote del primer team a `is_primary=true` (cuándo se ejecuta exactamente, antes/después del flush)? [Clarity, ADR-0016]
                → N/A US1 — no hay `is_primary` en ClientTeam (multi-team sin primary; sólo `isPrimaryAdvisor` en assignment). El auto-mark del primer asesor en la migración legacy está en R-007.

## Migration safety

- [x] CHK017 — ¿Está documentado por qué M1a y M1b son migraciones separadas (split en lugar de monolítica)? [Clarity, ADR-0016]
                → data-model.md tiene 3 migraciones: M1 (add columns + CHECK + partial unique), M2 (backfill), M3 (NOT NULL). Separación justificada en data-model.md:138-142 ("segundo deploy una vez verificado").
- [x] CHK018 — ¿Es idempotente cada paso de backfill de M1a (ejecutar 2 veces produce el mismo estado)? [Coverage, data-model.md §M1a]
                → R-007: "la migración chequea `team_id IS NULL` antes de procesar — re-ejecutar es noop."
- [ ] CHK019 — ¿Está definido el comportamiento cuando la audit query de M1a detecta `(client_id, employee_id)` con >1 fila activa (RAISE EXCEPTION + mensaje claro)? [Coverage, data-model.md §M1a]
                → **GAP**: no hay paso de audit pre-flight. El partial unique en M1a fallaría con error genérico de Postgres si hay duplicados activos legacy. Acción: añadir a M1a un `SELECT` de validación que `RAISE EXCEPTION 'Legacy duplicate active assignment...'` con detalle del par afectado **antes** de crear el índice.
- [ ] CHK020 — ¿Hay rollback strategy documentada (qué pasa si M1a o M1b fallan a mitad)? [Coverage, research.md §R8]
                → **GAP parcial**: M2 backfill tiene `down(): noop` (data-model.md:135). M1 (add columns) y M3 (NOT NULL) no documentan `down()`. Acción: declarar explícitamente `down()` para M1 (DROP de columnas/índices) y M3 (DROP NOT NULL), o marcar como forward-only.
- [ ] CHK021 — ¿Está documentado que la M0 ya aplicada NO se modifica retroactivamente (Constitution III)? [Compliance, data-model.md]
                → **GAP**: no hay nota explícita. Implícito por convención de MikroORM (migraciones aplicadas son inmutables). Acción: añadir frase en `data-model.md §Migraciones` recordando que las migraciones existentes no se tocan — sólo se añaden nuevas.
- [ ] CHK022 — ¿Tiene cada migración nueva su método `down()` documentado o explícitamente declarado como forward-only? [Coverage, data-model.md]
                → **GAP**: ver CHK020. Sólo M2 lo declara. M1 y M3 no.

## Cross-service alignment

- [x] CHK023 — ¿Refleja `pd-service-data-factory/client_assignment` los MISMOS 4 campos nuevos (`team_id`, `percentage`, `is_primary_advisor`, `causes_baja`) que `pgi-service-pgi-api`? [Consistency, data-model.md §M2]
                → N/A US1 — US1 NO cambia el payload AMQP (FR-018 diferido). data-factory no necesita columnas nuevas hasta US2. Marcado como `[x]` en sentido "decisión consciente de no propagar todavía".
- [x] CHK024 — ¿Está documentado por qué M2 añade `is_primary_advisor` y `causes_baja` AHORA aunque US4 los implemente después (evita segunda migración cross-service)? [Clarity, ADR-0016]
                → ADR-0016 razona el split a US1 sin tocar data-factory. La segunda migración cross-service se hará con US2.
- [x] CHK025 — ¿Está documentada la política de huérfanos en data-factory (qué pasa si llega `team_id` no conocido)? [Coverage, ADR-0011]
                → ADR-0011 cubre. N/A para US1.
- [ ] CHK026 — ¿Está actualizado `@afianza-ac/lib-core-definitions` con los enums/types necesarios (o queda como tarea explícita)? [Gap, plan.md]
                → **GAP**: `Department` y `Role` ya existen en lib-core. `isPrimaryAdvisor`/`version` son campos nuevos — hay que confirmar si lib-core tipa `ClientAssignment` (en cuyo caso requiere bump) o no. Acción: comprobar en `lib-core-definitions` antes de implementar y añadir tarea si procede.

## Onboarding bridge

- [ ] CHK027 — ¿Está documentado el pseudo-code completo de `applyFromClientOnboarding` post-fix (cierra fila activa antes del upsert)? [Completeness, ADR-0014, data-model.md §Onboarding bridge]
                → **GAP**: `data-model.md` menciona el `created_by = 'system:onboarding'` (línea 24) pero no incluye el pseudo-code. Está parcialmente en ADR-0014. Acción: añadir sección "Onboarding bridge — pseudo-code" en data-model.md (cerrar fila activa con `date_to = today.lastOfMonth()` antes del nuevo INSERT).
- [ ] CHK028 — ¿Está identificado el test de regresión obligatorio (`apply-from-client-onboarding.regression.spec.ts`)? [Coverage, quickstart.md]
                → **GAP**: tasks.md no lista una tarea T-XXX para este test. quickstart.md no lo menciona. Acción: añadir tarea en tasks.md Phase 2 foundational (test que verifique que aplicar onboarding sobre cliente con asignación activa cierra la previa y crea nueva sin violar partial unique).
- [x] CHK029 — ¿Está documentado el comportamiento cuando el onboarding intenta crear una fila para un empleado que ya tiene asignación activa en OTRO cliente (no debería disparar nada — FR-021 es por cliente)? [Coverage, Edge Case, Spec §FR-021]
                → FR-021 partial unique es `(client_id, employee_id)` — empleados pueden estar activos en N clientes simultáneamente. Implícito por la forma del índice.

## Audit & PII

- [ ] CHK030 — ¿Están `updatedBy` y `updatedAt` poblados consistentemente en TODAS las mutaciones (incluido el publisher AMQP)? [Consistency, data-model.md]
                → **GAP parcial**: `ClientTeam` tabla (data-model.md:17-29) lista `updated_at` pero **falta `updated_by`** explícito. `ClientAssignment` lo tiene. Acción: añadir `updated_by varchar` a ClientTeam (alineado con assignment) o documentar explícitamente que ClientTeam no requiere updated_by porque no se modifica post-creación (la única mutación esperada es `end_date` en US4).
- [x] CHK031 — ¿Está identificada la PII en columnas (`employee_id` → email/nombre, `updated_by` → email) y su tratamiento en logs? [Compliance, plan.md §Compliance]
                → plan.md Compliance: "(none new)" para US1. Auth via AzureAdJwtGuard.
- [ ] CHK032 — ¿Está documentado que filas históricas cerradas (`date_to IS NOT NULL`) son inmutables y no se borran? [Consistency, Spec §FR-008]
                → **GAP**: implícito por convención. No hay constraint BD que lo enforce, ni nota explícita en data-model.md. Acción: añadir frase en data-model.md y posiblemente un `BEFORE UPDATE` trigger que rechace cambios cuando `OLD.date_to IS NOT NULL` (recomendación: aceptar deuda y enforce en servicio).

## Edge cases / lifecycle

- [ ] CHK033 — ¿Está documentado qué pasa con asignaciones cuando se borra un `Employee` (la FK tiene RESTRICT — orphan-safe)? [Coverage, Edge Case]
                → **GAP**: la política FK de `employee_id` no se declara en data-model.md (ligado a CHK007). Comportamiento esperado: RESTRICT. Acción: añadir a la tabla de FK policies.
- [x] CHK034 — ¿Está documentado el estado "team con 0 miembros activos pero `endDate=null`" (es válido o transitorio)? [Coverage, Edge Case, Spec §FR-011]
                → data-model.md `:42-46` lo trata como `incomplete` (sin responsable / sin asesor → incomplete). Válido transitoriamente; no se publica AMQP mientras incomplete.
- [ ] CHK035 — ¿Está documentado el comportamiento cuando un cliente pierde todos sus `ProvidedService` activos (equipos huérfanos — OQ #16)? [Pendiente, Edge Case]
                → R-006: "Los equipos existentes sobreviven si todos los servicios del dept se dan de baja" — pero OQ-008 sigue pendiente. Marcado [ ] hasta que PO confirme política de cleanup.

---

## Resumen post-revisión (2026-06-03)

- **Total**: 35 items (2 unresolved + 33 quality checks).
- **PASS**: 19 (`[x]`).
- **GAP / pendiente**: 16 (`[ ]`).

### Críticos a resolver antes de `/speckit-implement`

1. **CHK019** → añadir audit pre-flight en M1a (RAISE EXCEPTION si hay duplicados activos legacy). Riesgo de migración rota en prod.
2. **CHK007 + CHK033** → declarar FK policies (`team_id`, `employee_id`, `client_id` ON UPDATE / ON DELETE) en data-model.md.
3. **CHK020 + CHK022** → declarar `down()` (o forward-only explícito) en M1 y M3.
4. **CHK027 + CHK028** → pseudo-code del bridge `applyFromClientOnboarding` + test de regresión como tarea en tasks.md.
5. **CHK030** → resolver `updated_by` en `ClientTeam` (añadir columna o justificar ausencia).

### Aceptables como deuda

- CHK011 (DROP `idx_client_team_active`) — verificar en migrations existentes; si no existe, marcar resuelto.
- CHK014, CHK032 (enforce BD-level de inmutabilidad) — servicio + auditoría con `updated_by` es suficiente.
- CHK021 (M0 inmutable) — convención implícita.
- CHK026 (`lib-core-definitions`) — verificar antes de implementar; añadir tarea si procede.
- CHK035 (OQ-008 huérfanos) — pendiente PO; no bloquea US1.
- CHK001-002 (PO pending) — assumptions MVP cubren US1.
