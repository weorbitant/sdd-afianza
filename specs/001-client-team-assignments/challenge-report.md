# Anexo técnico — DEVPT-518 (post-PO)

> Las decisiones de negocio (D1-D11, G1-G2) que generaba este report han sido aplicadas
> al spec.md (sección `## Decisiones de la sesión PO`). Aquí queda solo el anexo técnico
> con los findings de `feasibility-reviewer` (T1-T10) y la trazabilidad de IDs para
> auditoría futura.

## Anexo técnico — para el equipo

Esta sección no es para el PO.

### Resumen por severidad

| Severidad     | Cuántos |
|---------------|---------|
| BLOCKER       | 6       |
| ADR           | 2       |
| QUESTION-PO   | 12      |
| BUSINESS-GAP  | 2       |
| NIT           | 0       |

### Hallazgos técnicos

Generados por `/speckit-challenge technical` (2026-06-01). 10 findings de `feasibility-reviewer`. 5 BLOCKERs **bloquean `/speckit-tasks`** hasta resolverse.

#### T1 — BLOCKER — constraint-enforcement

**Afecta a**: cross-cutting
**Location**: `data-model.md#clientassignment`
**Reviewer ID**: `feasibility-F1`

**Evidence**:
> "NUEVO partial unique: (client_id, employee_id) WHERE date_to IS NULL ... una persona puede tener máximo UNA asignación activa al mismo cliente"

**Gap**: El nuevo partial unique colisiona con `applyFromClientOnboarding`, que usa `em.upsert(ClientAssignment, ...)` con la business key existente `(client, employee, role, department, dateFrom)`. El onboarding puede emitir legítimamente una segunda fila activa para el mismo `(client, employee)` cuando cambia el rol — el partial unique lanzará excepción y FR-017 empezará a fallar en el momento que aterrice la migración M1, antes de que D10 se resuelva.

**Suggestion**: O bloquear el partial unique detrás de la resolución de D10, o cambiar el onboarding para que cierre la fila activa existente (poner `date_to`) antes de insertar la nueva, dentro de la misma transacción. Documentar el camino elegido en un ADR + añadir test de regresión en `client-subscriber.spec.ts`.

---

#### T2 — BLOCKER — constraint-enforcement

**Afecta a**: US1, US2
**Location**: `data-model.md#clientassignment`
**Reviewer ID**: `feasibility-F2`

**Evidence**:
> "isPrimaryAdvisor = true solo permitido si role = asesor (CHECK BD ayuda pero validación servicio da mensaje claro)"

**Gap**: El texto dice que un CHECK de BD "ayuda" pero NO está declarado en la migración M1. Igual para `causes_baja` solo significativo cuando `date_to IS NOT NULL`. Un bug en el servicio o una migración futura puede poner `is_primary_advisor=true` en una fila coordinador/técnico, y el partial unique `(client_id, department) WHERE is_primary_advisor=true AND date_to IS NULL` tratará silenciosamente esa fila incorrecta como la principal, rompiendo el sync de jira-adapter (FR-020).

**Suggestion**: Añadir `CHECK (is_primary_advisor = false OR role = 'asesor')` y `CHECK (causes_baja = false OR date_to IS NOT NULL)` en la migración M1 + decoradores MikroORM.

---

#### T3 — BLOCKER — entity-granularity

**Afecta a**: US4
**Location**: `spec.md:L199-L203`
**Reviewer ID**: `feasibility-F3`

**Evidence**:
> "Si un asesor causa baja en la empresa ... el sistema reasigna automáticamente sus tareas abiertas al asesor sucesor definido para ese cliente. Si no hay sucesor definido, el sistema bloquea el cierre"

**Gap**: FR-010 promete bloquear el cierre cuando no hay "sucesor definido para ese cliente", pero NO hay entidad, columna ni relación en data-model.md que almacene qué empleado es el sucesor designado para un cliente. El contrato PATCH/DELETE acepta `successorId` en el body pero no dice dónde vive el sucesor "por defecto" — implicando que debe inferirse de filas existentes, pero D9 (inferencia temporal) no está formalizada en el esquema.

**Suggestion**: O añadir columna `successor_employee_id` en `ClientAssignment` (o tabla `client_succession` separada) + definir cómo se popula, o reescribir FR-010 para que SIEMPRE requiera `successorId` en el payload de cierre. El esquema actual no puede aplicar el bloqueo prometido.

---

#### T4 — BLOCKER — constraint-enforcement

**Afecta a**: US1, cross-cutting
**Location**: `contracts/client-teams-api.md#POST-close`
**Reviewer ID**: `feasibility-F4`

**Evidence**:
> "Setea endDate en el team y en todos sus ClientAssignment activos ... Publica evento AMQP ... para cada miembro cerrado"

**Gap**: Cerrar un team muta la fila del team + N filas de asignaciones + emite N eventos AMQP. El plan y el contrato no especifican los límites transaccionales. Per Constitution III (MikroORM UoW), esto DEBE ser un `em.transactional`, y la semántica de AMQP publish-after-commit DEBE definirse — si no, D-005 (PENDING outbox/retry) se filtra a esta historia y el team puede quedar cerrado en BD mientras los consumers nunca ven el cascade.

**Suggestion**: Declarar explícitamente en plan.md (o sección lifecycle de data-model.md) que el cierre de team corre dentro de un `em.transactional`, con AMQP publish post-commit. Linkear el gap a D-005 — la historia no es implementable hasta resolver ese PENDING.

---

#### T5 — ADR — concurrency

**Afecta a**: cross-cutting
**Location**: `plan.md:L33`
**Reviewer ID**: `feasibility-F5`

**Evidence**:
> "Optimistic concurrency vía updatedAt en ClientTeam y ClientAssignment (FR-022) — HTTP 409 al conflicto"

**Gap**: `updatedAt` es un `timestamp` con granularidad sub-segundo, auto-actualizado por `onUpdate: () => new Date()` en MikroORM. Dos writes en el mismo milisegundo producen el mismo `updatedAt` y bypassan el check optimista. No hay columna `@Version` ni rationale documentado para elegir timestamp en lugar de version integer monotónico.

**Suggestion**: Promover a ADR — o cambiar a columna `version` integer (`@Property({ version: true })` en MikroORM 6) o documentar por qué `updatedAt` con `clock_timestamp()` es aceptable para este workload, y alinear el contrato `If-Match` con la representación elegida.

---

#### T6 — BLOCKER — lifecycle

**Afecta a**: US1, cross-cutting
**Location**: `data-model.md#clientteam`
**Reviewer ID**: `feasibility-F6`

**Evidence**:
> "Partial unique opcional: (client_id, department, is_primary) WHERE is_primary = true AND end_date IS NULL — máximo un team principal activo por (cliente, departamento)"

**Gap**: FR-020 manda jira-adapter sincronizar "solo la asignación del equipo principal del cliente y del asesor principal". El esquema enforced at-most-one primary team pero NO at-least-one. Un cliente con 2+ teams Fiscal activos e `is_primary=false` en todos es un estado válido donde jira-adapter no tiene fila que escribir, rompiendo FR-020 silenciosamente.

**Suggestion**: O (a) requerir `isPrimary=true` en creación cuando no hay otro primary (auto-promote primer team), o (b) documentar el contrato de que jira-adapter cae al team más antiguo activo cuando no hay `is_primary=true`. Capturar como invariante del servicio + test de regresión.

---

#### T7 — ADR — implicit-decision

**Afecta a**: cross-cutting
**Location**: `data-model.md#migrations`
**Reviewer ID**: `feasibility-F7`

**Evidence**:
> "Migration M2 — pd-service-data-factory ... ADD COLUMN team_id uuid NULL ... No FK constraint: cross-service team_id is logical only"

**Gap**: Elegir "FK lógica solo" para `team_id` en data-factory merece un ADR. La alternativa (no `team_id`, derivar primary solo via jira-adapter) no está descartada en `decisions.md` ni `research.md`. Sin ADR, futuros developers no sabrán si tratar `team_id` huérfano (team borrado/cerrado en pgi-api) como corrupción o como esperado.

**Suggestion**: Añadir ADR (e.g., ADR-0011) documentando la decisión cross-service `team_id`: nullable, sin FK, tratado como opaque correlation id, + cómo data-factory maneja team ids desconocidos (ignore vs warn).

---

#### T8 — BLOCKER — concurrency

**Afecta a**: US2, cross-cutting
**Location**: `data-model.md#departmentbucketstatus`
**Reviewer ID**: `feasibility-F8`

**Evidence**:
> "globalStatus: 'active' | 'incomplete'; // active iff asesores=100 + tecnicos in {100, not-applicable} + hasPrimary"

**Gap**: FR-014 publica el evento AMQP SOLO cuando el bucket transiciona a `active`. El bucket se calcula agregando TODAS las asignaciones activas across teams del (client, department). Dos PATCH /members concurrentes en distintos teams del mismo client+department, ambos leyendo status=incomplete y ambos sumando 100, harán race: ambos pueden creer que dispararon la transición y publicar eventos duplicados, o ninguno publicar (read-modify-write hazard). El plan no especifica isolation ni row-level locking.

**Suggestion**: Especificar en plan.md la estrategia de locking (e.g., `SELECT ... FOR UPDATE` en el row padre `client`, o transacción serializable wrapping recompute + publish). Sin esto FR-014 no puede garantizar "exactly one transition event" semantics.

---

#### T9 — QUESTION-PO — lifecycle

**Afecta a**: US1
**Location**: `spec.md:L235-L242`
**Reviewer ID**: `feasibility-F9`

**Evidence**:
> "Los equipos existentes en un departamento permanecen activos aunque luego se den de baja todos los servicios contratados de ese departamento — la regla bloquea creación, no invalida existentes (a confirmar con PO — ver OQ-008)"

**Gap**: OQ-008 sigue marcada 'a confirmar con PO' dentro de FR-017. El data-model no tiene campo para marcar team como 'huérfano por terminación de servicio' ni hook al desactivar el último `ProvidedService` del departamento. El comportamiento divergirá silenciosamente de cualquier respuesta PO futura.

**Suggestion**: O cerrar OQ-008 con PO antes de implementar (default recomendado: teams existentes permanecen activos, sin cambio de esquema) o añadir columna `orphaned_at` + listener en deactivación de `ProvidedService`. Documentar el default elegido en `decisions.md` para no bloquear implementación.

---

#### T10 — BLOCKER — constraint-enforcement

**Afecta a**: cross-cutting
**Location**: `data-model.md#migrations`
**Reviewer ID**: `feasibility-F10`

**Evidence**:
> "Backfill script (separate, idempotent — ejecutado post-deploy) ... UPDATE client_assignment ca SET is_primary_advisor = true"

**Gap**: Migration M1 crea el partial unique `client_assignment_primary_advisor_unique` ANTES de que el backfill corra. Durante el gap entre la migración y la ejecución del backfill, el índice existe pero ninguna fila tiene `is_primary_advisor=true` — significando que el invariante de FR-020 ('exactamente un asesor principal activo por client+department') se viola para TODO cliente+department legacy. Cualquier evento AMQP disparado en esa ventana (o cualquier lectura por jira-adapter) no ve principal.

**Suggestion**: O (a) correr el backfill dentro de la misma transacción de la migración MikroORM (per D-003, la migración legacy ya es una MikroORM migration — aplicar esta regla consistentemente) o (b) diferir creación del partial unique a una segunda migración después del backfill. El orden actual es unsafe.

### Trazabilidad de IDs

| ID PO | Reviewer ID | Severity | Location |
|-------|-------------|----------|----------|
| D1    | business-B1 | QUESTION-PO | spec.md#FR-003 |
| D2    | business-B2 | QUESTION-PO | spec.md#FR-001 |
| D3    | business-B3 | QUESTION-PO | spec.md (ABSENCE) |
| D4    | business-B4 | QUESTION-PO | spec.md#FR-003 |
| D5    | business-B5 | QUESTION-PO | spec.md (ABSENCE) |
| D6    | business-B6 | QUESTION-PO | spec.md#FR-005 |
| D7    | business-B7 | QUESTION-PO | spec.md#user-story-3 |
| D8    | business-B8 | QUESTION-PO | spec.md#FR-017 |
| D9    | business-B11 | QUESTION-PO | spec.md (ABSENCE) |
| D10   | human-flag-2026-06-01 | QUESTION-PO | spec.md#clarifications-2026-06-01 (ABSENCE — flujo onboarding no documentado) |
| D11   | human-flag-2026-06-01 | QUESTION-PO | obligations-api/task.ts (campo único `advisor`); spec.md#FR-010 (no cubre por-rol) |
| G1    | business-B9 | BUSINESS-GAP | spec.md#FR-002 |
| G2    | business-B10 | BUSINESS-GAP | spec.md#FR-009 |
| T1    | feasibility-F1 | BLOCKER | data-model.md#clientassignment |
| T2    | feasibility-F2 | BLOCKER | data-model.md#clientassignment |
| T3    | feasibility-F3 | BLOCKER | spec.md:L199-L203 |
| T4    | feasibility-F4 | BLOCKER | contracts/client-teams-api.md#POST-close |
| T5    | feasibility-F5 | ADR | plan.md:L33 |
| T6    | feasibility-F6 | BLOCKER | data-model.md#clientteam |
| T7    | feasibility-F7 | ADR | data-model.md#migrations |
| T8    | feasibility-F8 | BLOCKER | data-model.md#departmentbucketstatus |
| T9    | feasibility-F9 | QUESTION-PO | spec.md:L235-L242 |
| T10   | feasibility-F10 | BLOCKER | data-model.md#migrations |

### Reviewers fallidos

- **`business-logic-reviewer` (bucket 9 — delivery sequence)** en la pasada técnica 2026-06-01: el reviewer devolvió 9 findings en formato incorrecto (estructura `{title, evidence, impact, recommendation, severity, bucket}` en vez del JSON V2 esperado con `id, category, affectedStories, location, evidence, gap, suggestion`). Todos descartados por el orchestrator per regla de validación. **Contenido valioso perdido** que conviene recuperar manualmente o re-ejecutar el reviewer con prompt más estricto:
  - US4 depende de event extensions que aterrizan con US1 (split migration risk en data-factory)
  - Tasks.md solo cubre US1 pero la migración M1 + AMQP afecta cross-service — riesgo de drift
  - T018 publisher envía nuevos campos sin task que verifique que consumers los toleran
  - Backfill SQL post-deploy no está en runbook → todos los clientes existentes saldrían con banner "incompleto" día 1
  - T006 mezcla DDL + DML en una migración → rollback parcial imposible
  - Frontend (T029-T039) basado en contracts ya desactualizados (commit-team.use-case quitado por decisión PO 2026-05-29)
  - Onboarding regression test no está en tasks.md a pesar de ser constraint declarada
  - lib-core-definitions enum bump no coordinado entre los 4 servicios

### Próximos pasos (para el equipo)

- **Decisiones (D1..D9)**: el orchestrator ofrecerá publicarlas como Open Questions en `spec.md`. Después, `/speckit-atlassian-sync-push` las sube como comments individuales a la Epic.
- **Aclaraciones (G1, G2)**: editar `spec.md` para añadir el FR/AC usando `suggestion` como punto de partida. No requieren input del PO.
- Bloqueantes para empezar US1: D1, D2, D6. Resolverlas antes de iniciar implementación.
