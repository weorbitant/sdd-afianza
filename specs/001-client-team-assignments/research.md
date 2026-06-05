# Research — Client Team Assignments v2

**Phase**: 0 (/speckit-plan)
**Date**: 2026-06-04
**Context**: spec.md v2, decisions.md (ADRs heredados + avisos v2), er-diagram.md v2, data-model.md v2.

> La mayoría de decisiones técnicas ya están consolidadas en `decisions.md` (ADRs heredados de v1, marcados Vigente/Superseded para v2). Esta sección cubre **lo que falta resolver para arrancar implementación** y las decisiones específicas de Phase 0 de v2 que no tenían ADR propio.

## Open Questions de spec.md v2 — estado

| OQ | Tema | Estado para implementación |
|---|---|---|
| OQ-001 | Criterio de obligations para reasignar tareas (`dueDate >= effectiveDate` u otro) | **Pendiente** con team lead de obligations. Bloquea US-06 — no bloquea P1. Para los contratos AMQP de P1 publicamos un payload completo (`role`, `employeeId`, `effectiveDate`, `clientId`, `department`) que cubrirá cualquier criterio razonable. |
| OQ-002 | ¿`incomplete` si hay 0 main aunque la cobertura sea 100%? | **Resuelto**: sí (FR-013 v2 lo exige). Reflejar en helper `compute-team-status`. |
| OQ-003 | Shape de `client_team_assignment_change` | Diferido a US-07. No bloquea. |
| OQ-004 | Antigüedad con dos tramos accidentales simultáneos | **Resuelto provisional**: cadena continua (no rompe). Documentar en helper `compute-employee-tenure`. |
| OQ-005 | Nombre exacto del routing key de onboarding | **Pendiente** con producer. Para implementar US-04 hipotetizamos `client-onboarding-assignment`. El binding se ajusta cuando se confirme — cambio de una línea en el subscriber. |
| OQ-006 | Cómo publicar revocación cuando FR-007 borra un tramo ya publicado | **Resuelto provisional**: opción (b) — el evento `opened` posterior con el nuevo estado prevalece. Downstream debe ser idempotente y considerar el último evento como verdad. Documentar en payload AMQP (incluir `effectiveDate` y `version` para que el consumer pueda ordenar). |

## Decisiones Phase 0 nuevas (no cubiertas por ADRs heredados)

### R-01 — Endpoint composite vs. múltiples llamadas para reemplazos

**Context**: Un reemplazo en US-02 (Alfonso sale, David entra al 100%) implica cerrar un tramo y abrir otro en transacción atómica. Dos opciones:
- (a) FE llama `DELETE /members/{id}` con `effectiveDate` y luego `POST /members` con la nueva persona — 2 llamadas, cada una su transacción.
- (b) FE llama un endpoint composite `POST /teams/{teamId}/operations` con un body `{ closes: [...], opens: [...] }` — 1 llamada, 1 transacción.

**Decision**: Opción (b) — endpoint composite.

**Rationale**:
- Atomicidad real: si una falla, no quedan estados intermedios "Alfonso cerrado sin David abierto" que rompan cobertura temporalmente.
- Menor latencia perceptible para el usuario (1 request en vez de 2).
- El payload del request modela bien la intención "esto es un reemplazo", no "dos operaciones aisladas".
- Encaja con la atomicidad del recompute de cobertura (un solo `SELECT … FOR UPDATE`).

**Alternatives considered**: (a) rechazada por riesgo de estado intermedio incoherente entre las dos llamadas y por duplicar el lock del client.

**Implication**: El OpenAPI tendrá `POST /clients/{id}/teams/{teamId}/operations` con un schema que soporta `creates`/`updates`/`closes`. Los PATCH/DELETE simples siguen existiendo para casos atómicos (cambiar solo `isMain`, por ejemplo) pero la UI usa preferentemente el composite.

### R-02 — Cálculo de `tenureSince` server-side por cada miembro de la vista

**Context**: `tenureSince` es campo derivado (data-model §4.1). Hay que decidir si se calcula on-demand al servir GET `/teams?at` (N+1 query potencial) o si se precalcula vía vista materializada / cache.

**Decision**: On-demand con una sola query agregada por request (no N+1).

**Rationale**:
- Volúmenes pequeños: una ficha de cliente carga ≤ 10 miembros activos. Una sola query `SELECT employee_id, MIN(...) ...` con `WINDOW` o `GROUP BY` resuelve todos en un viaje a BD.
- Sin necesidad de vista materializada en volúmenes actuales (~10k clientes × 5 miembros = 50k filas activas máx).
- Si el perfil de carga cambia (p.ej. dashboards con 1000 clientes en paralelo), se evalúa cache o vista materializada en una iteración posterior.

**Alternatives considered**:
- Vista materializada `employee_tenure_per_client`: refresh asíncrono — añade complejidad operativa innecesaria hoy.
- Cache Redis: lo mismo, prematuro.

### R-03 — Manejo de la migración de schema en `client_team` (DROP COLUMN start_date/end_date)

**Context**: data-model §2.1 indica `DROP COLUMN start_date, end_date` en `client_team`. Riesgo: si algún consumer (otro servicio, frontend, query manual) lee esas columnas, romperá.

**Decision**: Migración en dos pasos cronológicos:
1. **Deploy A**: añadir las nuevas columnas (`created_by`, `updated_by`, `version`), **no tocar las viejas** todavía. Marcar `start_date`/`end_date` como deprecated en comentarios SQL y notificar a consumers (data-factory, jira-adapter) por canal interno.
2. **Deploy B** (1-2 semanas después): `DROP COLUMN start_date, end_date`. Solo si la auditoría de consumers confirma que nadie las lee.

**Rationale**: Constitución P-V (simplicity). Hacerlo de golpe es más rápido pero deja una ventana de incidencia si alguien las usaba sin saberlo. Dos deploys es coste bajo y elimina el riesgo.

**Alternatives considered**: Un solo deploy con DROP directo — rechazado por riesgo de breakage no detectado.

### R-04 — Patrón de publicación AMQP en el mismo flush vs. outbox

**Context**: FR-014 v2 (publicación tras transición complete) requiere que el evento se publique fiablemente tras un commit DB exitoso. RabbitMQ publish dentro de la transacción tiene el problema clásico "dual write" (commit DB ok, publish falla → evento perdido).

**Decision**: Por ahora, publicar **después** del `flush` exitoso, sin outbox. Aceptamos la ventana de riesgo pequeña porque:
- pgi-api ya usa este patrón en otras features (consistencia con el resto del servicio).
- La duración de la ventana entre commit y publish es muy pequeña (<10 ms típico).
- En caso de fallo, hay reconciliation cross-service por el snapshot diario que data-factory hace contra pgi-api.

**Rationale**: Outbox pattern es coste de ingeniería alto para una ventana de riesgo pequeña. Si el dolor aparece, se introduce en una iteración posterior.

**Alternatives considered**:
- Transactional outbox con relay process: más fiable, más complejo. Diferido hasta tener evidencia de eventos perdidos en prod.

### R-05 — Estrategia de tests E2E por user story

**Context**: Constitución P-II exige `@testcontainers/postgresql` para tests con EM. Decidir qué granularidad de E2E por US.

**Decision**: Un archivo E2E por US (`*.usXX-*.e2e-spec.ts`), con un test por acceptance scenario de §5 spec. Cada archivo arranca su contenedor Postgres y un test RabbitMQ embebido o mock (según necesidad de la US).

**Rationale**:
- Trazabilidad 1:1 spec → test. Si el revisor funcional aprueba un scenario, el test correspondiente está identificado.
- Aísla fallos: un archivo flaky no contamina los demás.

**Alternatives considered**: Un único archivo gigante por feature — peor mantenibilidad.

## Stack-specific best practices

### NestJS + MikroORM (P-I, P-III)

- Reads: `findOne(..., { disableIdentityMap: true })` — el patrón estándar del servicio.
- Writes complejos: `em.fork()` + `em.transactional(async txEm => { ... })` envuelve el cálculo de cobertura + close/open + publish.
- AMQP subscriber: cada handler hace `em.fork()` propio. No `@EnsureRequestContext()` (P-III).
- Migraciones: `npx mikro-orm migration:check` antes de aplicar; `npx mikro-orm migration:create --dump` debe devolver "No changes required" tras crearla.

### Tests con testcontainers

- Reutilizar el helper de `test/utils/test-postgres.helper.ts` (existe en pgi-api).
- Container shared entre tests del mismo archivo (constructor del describe), nunca entre archivos.
- ~10 s de cold start por archivo de E2E es aceptable (constitución P-II lo asume).

### RabbitMQ con `@afianza-ac/nest-module-rabbitmq`

- Publish: `this.rabbitMQService.publish('client-team-assignment-opened', payload)` desde dominio.
- Subscribe: clase con `@AmqpSubscribe({ ... })` en `application/amqp/`.
- Idempotencia en consumer de onboarding: `em.upsert()` por `(clientTeamId, employeeId, role, dateFrom)`.

### TanStack Query (frontend)

- Una query key por endpoint (`['client-team', clientId, at]`, `['client-team-history', clientId]`).
- Mutations con `onSuccess: invalidate queries relevantes` — la vista vigente se refresca automáticamente tras cualquier mutación.
- Optimistic updates **no** se usan en esta feature — la complejidad de cobertura/preservación es server-side, no merece optimismo en cliente.

## Riesgos identificados (para Complexity Tracking en caso de violación)

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Consumer no identificado de `client_team.start_date` rompe en producción | Baja-media | Alto | R-03: migración en dos deploys. Auditoría previa de consumers. |
| Routing key de onboarding cambia tras coordinar con producer | Media | Bajo | Binding configurable; cambio de una línea + redeploy. |
| Cobertura cross-team con cliente que tiene 5+ teams concurrentes genera lock contention | Baja | Medio | `SELECT FOR UPDATE` sobre `client` único (no sobre `client_team`) ya serializa. Si aparece contention, considerar locks finos por `(client, department)`. |
| Reasignación automática de tareas (US-06) requiere lógica espejo en obligations que aún no existe | Alta | Bajo (US-06 es P2) | OQ-001 abierta. Si se difiere obligations, los eventos siguen publicándose y obligations los aplica retroactivamente cuando esté listo. |

## Output

✅ research.md generado.
✅ Todas las NEEDS CLARIFICATION del template resueltas (ninguna real — el contexto técnico estaba completo por las iteraciones previas).
✅ Decisiones R-01..R-05 documentadas con rationale.
✅ Open Questions de spec.md con estado actualizado.
