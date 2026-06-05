# API & Contracts Quality Checklist — DEVPT-518

**Purpose**: Validate that the REST + AMQP contract definitions are complete, clear, consistent and RFC-aligned BEFORE `/speckit-tasks`. This is a requirements-quality check, not an implementation test.

**Created**: 2026-06-02
**Reviewed (batch)**: 2026-06-03 — auto-verdict por Claude contra `contracts/*.openapi.yaml`, `data-model.md`, `research.md`, `decisions.md` y `.claude/rules/rest-api-design.md`. Items con `→ GAP:` requieren acción antes de `/speckit-implement`.
**Feature**: [spec.md](../spec.md) · [contracts/](../contracts/)
**Audience**: author (pre-tasks gate)
**Depth**: focused (API only — functional spec covered separately)

> Marca cada item con [x] cuando la pregunta tenga respuesta clara en spec/plan/contracts/decisions. Si la respuesta es "no", el item revela un gap que conviene cerrar antes de generar tareas.

## ⚠️ Unresolved Decisions afectando contratos

Decisiones PO pendientes que cambiarían el shape del API si se resuelven en sentido distinto al assumption MVP. No bloquean `/speckit-tasks` (hay assumption documentada) pero el reviewer debería tener visibilidad.

- [ ] CHK001 — ¿Está resuelta la decisión sobre **baja de asesor sin sucesor designado** (#14)? [Pendiente, Spec §Decisiones-PO]
                → Pendiente: assumption MVP = bloquear cierre con `400 SUCCESSOR_REQUIRED` (ADR-0017). Si PO permite cierre sin sucesor, hay que relajar a warn + nullable `successorId`.
                → Verdict: **N/A US1** — el cierre con sucesor es US4. Queda como pending PO para US4.
- [ ] CHK002 — ¿Está resuelta la decisión sobre **visibilidad de porcentajes en histórico por perfil** (#17)? [Pendiente, Spec §Decisiones-PO]
                → Pendiente: assumption MVP = todos ven todo. Si PO restringe, el response shape de `GET /assignments` cambia (campo `percentage` condicional al rol del caller).
                → Verdict: **N/A US1** — histórico es US3. Sigue pendiente.
- [ ] CHK003 — ¿Está resuelta la decisión sobre **comportamiento al fallar Plataforma del Dato al guardar** (#15)? [Pendiente, Spec §Decisiones-PO]
                → Pendiente: sin propuesta dev. Afecta a retry policy del publisher + necesidad de outbox pattern (D-005) en el contrato AMQP.
                → Verdict: **N/A US1** — US1 no cambia el payload AMQP (FR-018 diferido a US2). Volver a evaluar en US2.
- [ ] CHK004 — ¿Está resuelta la decisión sobre **onboarding desde Jira creando equipo inicial** (#21 parcial)? [Pendiente, Spec §Decisiones-PO]
                → Pendiente: assumption MVP = `team_id = NULL` en filas creadas por `applyFromClientOnboarding`. Si PO opta por crear "Equipo inicial" automático, el contrato AMQP del consumer cambia.
                → Verdict: assumption MVP confirmada vía ADR-0014; la migración R-007 ya backfill-ea team_id. Pendiente sólo si PO cambia opinión.

## Endpoint Completeness

- [x] CHK005 — ¿Están documentados los permisos por rol para CADA endpoint de escritura? [Completeness, contracts/]
                → `client-teams.openapi.yaml` POST (`CLIENT_ASSIGNMENT_EDIT`); `client-team-assignments.openapi.yaml` POST/PATCH/DELETE/promote-primary cubren con `Forbidden` response + descripción.
- [ ] CHK006 — ¿Hay requisitos de paginación definidos para `GET /teams` y `GET /assignments`? [Gap, contracts/]
                → **GAP**: `GET /clients/{clientId}/teams` devuelve array plano sin `?page`/`?limit`/`?cursor`. Para US1 (1 cliente → pocos teams) probablemente no es crítico, pero conviene decidir antes (¿asumimos cap < 50 y no paginamos en US1?). Acción sugerida: anotar la asunción en research.md.
- [ ] CHK007 — ¿Está acotado el número máximo de teams activos por (cliente, dept)? [Gap, Spec §FR-005]
                → **GAP**: FR-005 permite multi-team sin cap. No bloquea US1 pero abre la puerta a 100+ teams en un cliente. Acción sugerida: documentar tope blando en research (p.ej. "esperable 1-3 teams; >10 = revisión manual").
- [x] CHK008 — ¿Están definidas las respuestas para cliente sin teams activos y sin assignments activos (empty state)? [Coverage, Edge Case]
                → Schema devuelve array; vacío = `[]`. Implícito pero estándar OpenAPI.
- [x] CHK009 — ¿Están listados los headers requeridos (Auth, If-Match, Content-Type) en CADA endpoint mutador? [Completeness, contracts/]
                → `security: azureAdJwt` aplicado globalmente. `If-Match` definido como `required: true` en `IfMatchTeamVersion`/`IfMatchAssignmentVersion` para PATCH/DELETE/promote. POST creation no lleva If-Match (no hay versión previa) — correcto.

## Endpoint Clarity

- [ ] CHK010 — ¿Es inequívoco el comportamiento de PATCH con múltiples campos opcionales (semántica "patch" vs "replace")? [Clarity, contracts/client-teams-api.md, client-assignments-api.md]
                → **GAP**: `UpdateAssignmentRequest` define `percentage` y `dateTo` como opcionales pero no explicita la semántica (¿ausente = sin cambio? ¿`null` = reset?). RFC 7396 (merge-patch) implícito pero no declarado. Acción: añadir nota "JSON Merge Patch — campo ausente = sin cambio; explícito `null` = reset (solo aplicable a `dateTo`)".
- [x] CHK011 — ¿Está claro qué body fields son requeridos vs opcionales en CADA PATCH variant (% change, primary promote, close)? [Clarity, contracts/client-assignments-api.md]
                → OpenAPI lista `required` por schema (`CreateAssignmentRequest: [employeeId, role, dateFrom]`; `UpdateAssignmentRequest` sin required = todos opt; promote-primary sin body).
- [ ] CHK012 — ¿Es distinguible cada código 409 (`PERSON_ALREADY_ACTIVE_IN_CLIENT` vs `PRIMARY_ALREADY_EXISTS` vs `PRIMARY_ADVISOR_ALREADY_EXISTS` vs `ALREADY_CLOSED` vs `NO_PROVIDED_SERVICE`) por la respuesta? [Clarity, contracts/]
                → **GAP**: Los códigos actuales (`CLIENT_ASSIGNMENT_DUPLICATE_ACTIVE`, `CLIENT_ASSIGNMENT_PRIMARY_REQUIRES_ASESOR`, `CLIENT_TEAM_NO_PROVIDED_SERVICE_FOR_DEPARTMENT`) están en `data-model.md §Errores` pero NO referenciados explícitamente en los OpenAPI specs (sólo prosa). Acción: añadir `enum` de codes en el schema `Error` o listar `examples` por response.

## Consistency

- [x] CHK013 — ¿Requieren `If-Match` TODOS los endpoints mutadores sobre recursos versionados? [Consistency, contracts/]
                → POST team (creación) no requiere If-Match (no hay versión previa, correcto). POST/PATCH/DELETE/promote sobre assignment sí — todos parametrizados con `IfMatchAssignmentVersion`.
- [x] CHK014 — ¿Se llaman igual los filter query params equivalentes (`?department=`, `?status=`, `?teamId=`) en todos los endpoints? [Consistency, contracts/]
                → `department` enum compartido (`fiscal`/`laboral`). `?status=` y `?teamId=` no aparecen aún (no se necesitan en US1: GET único por cliente lista todos los teams).
- [x] CHK015 — ¿Está cada code de error que aparece en una response también en la tabla central "Errors comunes"? [Consistency, contracts/]
                → `data-model.md` tiene tabla central con HTTP code + descripción. Match 1:1 con los códigos citados en OpenAPI.
- [ ] CHK016 — ¿Hay una única forma de "cerrar" una asignación (PATCH con `dateTo`), o conviven dos caminos? [Consistency, contracts/client-assignments-api.md]
                → **GAP (crítico)**: el contrato actual define DOS caminos — `PATCH /client-team-assignments/{id}` con `dateTo` en body Y `DELETE /client-team-assignments/{id}?dateTo=...`. Además `DELETE` con query-param de mutación viola `.claude/rules/rest-api-design.md §6` (DELETE sin body, RFC 9110). Acción: eliminar el DELETE; cerrar siempre vía PATCH con `dateTo`.

## Status codes (RFC alignment)

- [ ] CHK017 — ¿`If-Match` que falla devuelve **412** (RFC 7232) en TODOS los PATCH versionados? [Consistency, contracts/]
                → **GAP (crítico)**: el contrato devuelve **409** `CLIENT_TEAM_VERSION_CONFLICT`. La regla `rest-api-design.md §Status codes` exige **412 Precondition Failed**. Acción: cambiar 409 → 412 en VersionConflict response y renombrar code a `CONCURRENT_MODIFICATION` (alineado con la regla).
- [ ] CHK018 — ¿Los conflictos de estado del recurso usan **409** y los semánticos post-mutación **422** consistentemente? [Consistency, contracts/]
                → **GAP**: ligado a CHK017 — el uso actual de 409 para "version stale" contamina la semántica. Tras corregir CHK017, 409 quedará reservado para conflictos de estado reales (ej. `ALREADY_CLOSED`).
- [x] CHK019 — ¿Se usa **201** para creación y **200** para read/update sin ambigüedad? [Clarity, contracts/]
                → POST team → 201; POST assignment → 201; PATCH/DELETE/GET → 200. Consistente.

## Request/Response shape quality

- [x] CHK020 — ¿Están documentados los rangos/constraints de TODOS los campos numéricos del request (ej. `percentage` 1..100)? [Completeness, contracts/]
                → `percentage`: `minimum: 1, maximum: 100`. `version`: `minimum: 1`. UUIDs con `format: uuid`. Fechas con `format: date`/`date-time`.
- [ ] CHK021 — ¿Aparecen los campos de audit (`updatedBy`, `updatedAt`, `version`) en TODAS las response shapes de recursos versionados? [Consistency, contracts/]
                → **GAP**: `ClientTeam` schema (client-teams.openapi.yaml:139-189) tiene `createdBy`, `createdAt`, `updatedAt`, `version` pero **falta `updatedBy`**. `Assignment` lo incluye correctamente. Acción: añadir `updatedBy: string` opcional al schema `ClientTeam`.
- [x] CHK022 — ¿Está documentado qué campos del request body son required vs optional para POST y PATCH separadamente? [Completeness, contracts/]
                → OpenAPI separa `CreateAssignmentRequest` (required: employeeId, role, dateFrom) y `UpdateAssignmentRequest` (todos opt).
- [x] CHK023 — ¿Está especificado el formato exacto de fechas (`date` ISO YYYY-MM-DD vs timestamp ISO) en cada campo? [Clarity, contracts/]
                → `format: date` para `startDate`/`endDate`/`dateFrom`/`dateTo`; `format: date-time` para `createdAt`/`updatedAt`.

## AMQP contract

- [ ] CHK024 — ¿Está documentada la routing key completa con versión (`pgi-api.v1.client-assignment.updated`)? [Completeness, contracts/client-assignment-event.md]
                → **GAP**: `contracts/client-assignment-event.md` **no existe**. La routing key se menciona en `quickstart.md:84` y en `research.md R-008` pero no hay contrato AMQP formal. Para US1 (que no cambia payload) basta una nota; para US2+ debe crearse el contrato.
- [x] CHK025 — ¿Están listados explícitamente los triggers que disparan publish (create, percentage change, primary change, close, team close)? [Completeness, contracts/client-assignment-event.md]
                → research.md R-008 los lista (incomplete→active, active→active, active→incomplete=no publish).
- [x] CHK026 — ¿Está documentada la regla de SUPPRESSION (no emite si globalStatus=incomplete)? [Clarity, contracts/client-assignment-event.md, Spec §FR-014]
                → research.md R-008 + spec FR-014.
- [x] CHK027 — ¿Está documentado el fallback behavior de los consumers ante payload legacy (campos nuevos ausentes)? [Coverage, contracts/client-assignment-event.md]
                → US1 no cambia payload — fallback no aplica. Para US2 con `teamId`/`percentage` ver `NOTE-001` en decisions.md.
- [ ] CHK028 — ¿Hay garantía de idempotencia documentada (misma payload dos veces → mismo estado en BD)? [Coverage, contracts/client-assignment-event.md]
                → **GAP**: no hay documento de contrato AMQP que lo declare. Implícito por upsert pero conviene escribirlo. Acción: añadir párrafo en research.md R-008 sobre idempotencia (upsert by (client, employee, role, dateFrom)).

## Versioning & backward compat

- [x] CHK029 — ¿Está documentada la estrategia de versionado y cuándo se bumpea de v1 a v2? [Completeness, contracts/]
                → `rest-api-design.md §Versionado`: path `/api/v1/...`, bump sólo en breaking change, aditivos son seguros (Postel). Decisions `NOTE-001-amqp-versioning-when-payload-changes` cubre AMQP.
- [x] CHK030 — ¿Está documentado el orden de deploy cross-service (data-factory → jira-adapter → pgi-api) en sitio accesible? [Completeness, ADR-0014]
                → ADR-0014 cubre el bridge. US1 no requiere deploy coordinado (no toca payload AMQP).
- [x] CHK031 — ¿Está documentado qué pasa si un consumer viejo recibe un payload con campos nuevos? [Coverage, contracts/client-assignment-event.md]
                → `rest-api-design.md` cita Postel's law explícitamente. N/A US1.

## Concurrency & error semantics

- [x] CHK032 — ¿Está especificado qué hacer en frontend cuando se recibe 412 `CONCURRENT_MODIFICATION` (recargar vs merge vs prompt)? [Gap, contracts/]
                → `quickstart.md:73` define toast *"El equipo ha cambiado, recarga..."* + invalidate de TanStack Query. Pendiente sólo de renombrar code/code-status cuando se corrija CHK017.
- [x] CHK033 — ¿Está documentada la respuesta cuando `suggestedSuccessorId` es `null` (no hay candidato) en SUCCESSOR_REQUIRED? [Coverage, ADR-0017]
                → N/A US1 (sucesor es US4 — ADR-0017).
- [ ] CHK034 — ¿Es coherente la semántica de "ya cerrado" entre `team.endDate` y `assignment.dateTo` (mismo código `ALREADY_CLOSED`)? [Consistency, contracts/]
                → **GAP**: no existe código `ALREADY_CLOSED` en `data-model.md §Errores`. Cierre de team es US4. Para US1 no aplica, pero al introducirse hay que reservar el mismo code para ambos.

## Cross-cutting

- [x] CHK035 — ¿Está identificada la PII en payload AMQP + REST (employee email, percentage proxy de retribución) y su tratamiento? [Compliance, plan.md §Compliance]
                → plan.md sección Compliance lo declara ("(none new)" para US1; auth via AzureAdJwtGuard + role guard).
- [x] CHK036 — ¿Está la regla `.claude/rules/rest-api-design.md` referenciada desde los contratos o las decisiones para futuras revisiones? [Traceability, decisions.md]
                → tasks.md y CLAUDE.md la cargan vía frontmatter `paths: specs/**/contracts/**`.

---

## Resumen post-revisión (2026-06-03)

- **Total items**: 36 (4 unresolved + 32 quality checks).
- **PASS**: 22 (`[x]`).
- **GAP / pendiente**: 14 (`[ ]`).

### Críticos a resolver antes de `/speckit-implement`

1. **CHK017 + CHK018** → cambiar 409 a **412** + renombrar code a `CONCURRENT_MODIFICATION` en `client-team-assignments.openapi.yaml` (alineación RFC 7232 y `.claude/rules/rest-api-design.md`).
2. **CHK016** → eliminar `DELETE /client-team-assignments/{id}` con query-param; canonizar cierre vía `PATCH` con `dateTo` en body. Aplica también a `PATCH /promote-primary` (CHK016 ext.).
3. **CHK021** → añadir `updatedBy` al schema `ClientTeam`.
4. **CHK010** → declarar semántica merge-patch en `UpdateAssignmentRequest`.
5. **CHK012** → exponer los códigos de error en el schema `Error` (enum o examples).

### Aceptables como deuda

- CHK006, CHK007 (paginación/cap) — no críticos en US1; documentar en research.
- CHK024, CHK028 (contrato AMQP formal) — US1 no cambia payload; obligatorio en US2.
- CHK034 (ALREADY_CLOSED) — entra con US4.
- CHK001-004 (PO pending) — assumptions MVP cubren US1.
