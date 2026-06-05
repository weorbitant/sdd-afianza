---
paths:
  - "specs/**"
---

# User Stories — Afianza

Reglas para redactar User Stories en `specs/<feature>/spec.md` y subirlas a Jira con `/speckit-atlassian-sync-push`. Destiladas de la sesión de refinamiento de DEVPT-518 (2026-06-04).

## 1. Una US = un paquete funcional testeable end-to-end

- **No partir por capa**: nada de "US-BE alta de miembro" + "US-FE alta de miembro". Una sola US "Alta inicial del equipo desde la UI" que incluye BE + FE + tests E2E.
- El criterio para juzgar si vale como US: ¿un revisor no técnico puede aceptarla siguiendo los criterios? Si la respuesta exige mirar el código → no es una US, es una tarea técnica.
- Las tareas BE/FE viven dentro como `T-XX-A` (BE) / `T-XX-B` (FE) en `tasks.md`, no como Stories distintas.

## 2. Formato vinculante: Contexto / Objetivo / Criterios

```markdown
#### US-XX — Título corto

**Contexto**
(2-4 frases) Por qué surge esta US, qué problema operativo cubre.

**Objetivo**
(1 frase, formato "Como X, quiero Y, para Z")

**Criterios de aceptación**
1. (frase numerada testeable, lenguaje funcional, **sin nombres propios** — usar roles genéricos: "un asesor", "el responsable", "el cliente")
2. ...

**Ejemplo**
(opcional pero recomendado cuando el criterio es difícil de visualizar) Un caso concreto con nombres y fechas reales que ilustre uno o varios de los criterios. Va al final, separado de los criterios.

<!-- internal-only -->
**Notas técnicas internas**
- ...
- **FRs cubiertos**: FR-001, FR-002, ...
- **Fuera de scope**: ...

<!-- jira-links -->
- is-blocked-by: US-XX
- relates-to: cross-service ...
<!-- /jira-links -->
<!-- /internal-only -->
```

- Todo lo que viene tras `<!-- internal-only -->` se **excluye** al subir a Jira (`/speckit-atlassian-sync-push` respeta el marcador).
- Criterios de aceptación: numerados, en lenguaje funcional. Nada de "el endpoint devuelve 422" — eso es nota técnica. Sí "veo un error claro y no se persiste nada".

## 3. Antes de crear Stories en Jira, listar las existentes

- Antes de `createJiraIssue`, **siempre** `searchJiraIssuesUsingJql` con `parent = <EPIC> AND status != "Desestimada"` para ver qué hay.
- Si el contenido de una US v2 puede absorber a una existente v1, **actualizar** (`editJiraIssue`) en vez de crear una nueva — preserva comentarios del PO y enlaces.
- Cuando una US v1 queda fusionada en otra v2 (caso US-07 → US-05 en DEVPT-518), añadir en la descripción una nota explicando la fusión.

Memoria de referencia: `feedback_check_existing_jira_stories.md`.

## 4. Antes de cerrar contract API, auditar el servicio destino

- Antes de redactar contract en `specs/<feature>/contracts/rest/`, hacer `ls <servicio>/src/application/rest/` y leer 2-3 controllers existentes.
- Si el servicio existente usa `{ data, total }`, no inventar `{ items, aggregate }`. Si usa NestJS exceptions, no proponer RFC 7807.
- Reglas escritas en `.claude/rules/rest-api-design.md` pueden estar **desactualizadas** vs. código real — verificar empíricamente.

Memoria de referencia: `feedback_audit_service_conventions.md`.

## 5. URLs como recursos, nunca como acciones

- ❌ `POST /clients/{id}/team-assignments/transitions`
- ❌ `POST /clients/{id}/team-assignments/operations`
- ❌ `GET /clients/{id}/team-assignments/history`
- ✅ Operación atómica multi-miembro: `PUT` sobre la colección filtrada (`PUT /clients/{id}/team-assignments?department=fiscal&dateFrom=2026-06-01` con `{ members: [...] }`).
- ✅ "Histórico" = misma colección con filtros distintos. Si tiene shape distinto, es **otro recurso** (`team-assignment-changes`, no `team-assignments/history`).
- Ver `.claude/rules/rest-api-design.md`.

## 6. Nombres de campos: semánticos, no técnicos

- ❌ `tenureSince`, `effectiveDate`, `at`, `causesBaja`, `hasAssociatedCompany`
- ✅ `inClientSince`, `dateFrom`/`dateTo` directos, `date`, `dueToTermination`
- Para query params de fecha: `date` para punto en el tiempo, `from`/`to` para rango. Evitar `at` (críptico).
- Si un campo es **input del cliente** distinto al campo **persistido**, normalmente significa que sobra: o expones el campo real (`dateFrom`) o el modelo está mal.

## 7. Single source of truth para audit

- Si hay tabla de log/cambios (`*_change`), el "quién" (`created_by`/`updated_by`) vive **solo** ahí.
- La tabla principal mantiene `created_at`/`updated_at` (cuándo) porque son útiles para queries rápidas, pero **no** duplica el "quién".
- Razón: si una fila se modifica N veces, `updated_by` solo guarda al último. La trazabilidad se pierde. El log captura cada autor.

## 8. Soft delete / void cuando hay auditoría

- ❌ `DELETE FROM client_team_assignment WHERE id = ?`
- ✅ `UPDATE client_team_assignment SET date_to = date_from - 1 día WHERE id = ?` (tramo queda invisible a queries `WHERE date_from <= :date AND date_to >= :date` pero auditable).
- El log registra `action='voided'` con snapshot completo en los `_before`.
- Si la entidad no tiene semántica temporal, alternativa: columna `deleted_at` (soft delete clásico).

## 9. Audit log: columnas explícitas, no JSON

- Cuando una tabla de log tiene un set acotado de campos (`role`, `percentage`, `is_main`, fechas…), usar columnas explícitas `field_before` / `field_after`.
- `jsonb before/after` solo si el shape de la entidad es genuinamente abierto (raro en dominio).
- `action` enum es ortogonal a las columnas: identifica el tipo de cambio para queries rápidas; los `_before`/`_after` NULLs según `action` son aceptables.

## 10. Resolver fechas relativas a absolutas al escribir

- Si el PO dice "freeze el jueves", traducir a fecha absoluta antes de guardar en spec/Jira (`2026-03-05`). Los Stories sobreviven al "jueves" pero no a "el jueves" sin contexto.
- Aplica también a memorias y notas de plan: ver memoria `project_*` en el índice.

## 11. Dependencias entre Stories como links de Jira

- En la sección `<!-- jira-links -->` listar:
  - `is-blocked-by: US-XX` (otra US que debe estar mergeada antes)
  - `relates-to: <descripción>` (cross-service, ticket espejo)
- `/speckit-atlassian-sync-push` traduce estos a issue links de Jira (`Blocks` / `Relates to`).
- Cuando una US se actualiza por re-orientación (ej. US-05 v1 "histórico" → US-05 v2 "log"), revisar también las dependencias salientes y entrantes.

## 12. Cuando una US se reorienta, propagar el cambio

Si cambias una US ya creada en Jira, revisa en orden:

1. `spec.md` — contexto, objetivo, criterios, notas internas, FRs cubiertos.
2. `data-model.md` / `er-diagram.md` — si la US tocaba tablas, actualizar shape.
3. `decisions.md` — cerrar OQs resueltas, marcar ADRs Superseded.
4. `contracts/` — OpenAPI/AMQP schemas.
5. `tasks.md` — tareas BE/FE de la US.
6. Jira: Story principal + Sub-tasks que ya existan + comentarios del PO conservados.
7. HTML export (`/speckit-md-html-export`).

Si solo tocas uno (típico: solo Jira sin spec), queda drift entre Jira y repo. Siempre la cadena completa.

## 13. Sub-tasks: el tamaño lo dicta lo que es revisable en un PR

- La US es la unidad funcional del PO. El sub-task es la unidad de revisión de código (un sub-task ≈ un PR).
- Si un sub-task tiene > ~400 líneas de diff esperadas o toca > 4 zonas distintas del código, partir.
- Estructura de cada sub-task: **Qué hace** (una frase) — **Cómo funciona** (1 párrafo) — **Qué NO entra aquí** (lista) — **Cómo verificar** (tests/escenarios) — **DoD**. La sección "Qué NO entra" es obligatoria; sin ella el revisor confunde el alcance.
- **Sin estimaciones** en sub-tasks. Si hace falta orientación gruesa, va a nivel de US, no de sub-task.

## 14. Format de mensajes de error visibles al usuario

- Español si el usuario final los va a leer (UI muestra `message` del NestJS exception en toast).
- Inglés solo para errores técnicos que solo ven devs (logs internos).
- No usar códigos `SCREAMING_SNAKE_CASE` separados — el FE discrimina con HTTP status + matching del `message` cuando hace falta. Convención actual de pgi-api.
