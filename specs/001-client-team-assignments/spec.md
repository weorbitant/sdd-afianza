# Spec — Client Team Assignments (DEVPT-518, v2)

**Feature**: 001-client-team-assignments
**Created**: 2026-06-04 (reescritura completa — versión anterior en `_archive/`)
**Status**: Draft
**Owner**: Alfonso Domenech
**Jira**: DEVPT-518 (sin tocar comentarios hasta validar esta versión)

> **Filosofía**: composición del equipo de un cliente como **historial de asignaciones temporales**. El "equipo" que ve el usuario es una **vista proyectada a una fecha**. No hay edición destructiva: todo cambio (alta, baja, reemplazo, cambio de %, redistribución) se materializa como cierre + apertura de tramos.

---

## 1. Resumen ejecutivo

Los responsables y coordinadores del backoffice de Afianza componen, para cada cliente y departamento (fiscal/laboral), el equipo de personas que lo gestiona: responsable, coordinador opcional, asesores, técnicos. Hoy ese equipo se edita "en caliente" en una tabla 1-a-1; no hay tramos temporales reales, los cambios de % o de persona machacan filas vivas y no se puede reconstruir quién operaba el cliente en una fecha concreta.

Esta feature reemplaza ese modelo por uno **temporal**: cada asignación es un tramo con `dateFrom` y `dateTo` opcional. Cambiar % o persona implica cerrar el tramo actual y abrir uno nuevo en la fecha efectiva del cambio. La UI muestra el equipo vigente hoy (o a una fecha pedida) calculado a partir de los tramos activos en ese momento. Los cambios futuros se pueden registrar con `dateFrom` posterior a hoy sin alterar el estado vigente. El histórico es consultable.

La reasignación de tareas abiertas a obligations (cuando un asesor sale del equipo de un cliente) ocurre **automáticamente** vía evento AMQP: pgi-api notifica close/open de asignaciones, obligations recalcula a quién corresponden las tareas según la fecha de vencimiento y el asesor vigente. Sin flags ni endpoints especiales para "baja".

---

## 2. Decisiones que conservamos de la v1 (ya cerradas)

| Decisión | Origen | Sigue aplicando |
|---|---|---|
| Departamentos fiscal/laboral como dimensión obligatoria de toda asignación | v1 spec | Sí |
| Dos coberturas independientes por rol: asesores 100% + técnicos 100%, sumando cross-team dentro de `(client, department)` | ADR-0012 | Sí |
| Responsable y Coordinador 100% implícito (no entran en la suma de coberturas) | ADR-0012 | Sí |
| Asesor main — exactamente 1 `is_main=true` activo por `(client, department)` | v1 spec | Sí |
| Validación FR-017: no se puede asignar dept X si el cliente no tiene `ProvidedService` activo en `family=X` | v1 spec | Sí |
| Multi-equipo permitido por `(client, department)`: varios `ClientTeam` activos en paralelo | PO 2026-06-01 | Sí |
| Optimistic concurrency con `version` en `ClientTeam` y `ClientTeamAssignment` | ADR-0010 | Sí |
| `client_assignment` legacy queda **congelada** post-deploy (no se migra, no se escribe) | ADR-0009 (reformulada) | Sí, simplificada — sin script de migración |
| Routing key AMQP nuevo: `pgi-api.v1.client-team-assignment.*` (distinto del legacy) | er-diagram.md | Sí |
| Tres tablas: `client_team` (agrupador), `client_team_assignment` (tramos), `client_team_assignment_change` (audit, diferida a US2) | er-diagram.md | Sí |

## 3. Lo que cambia respecto a la v1

| Tema | v1 | v2 (esta spec) |
|---|---|---|
| Granularidad de fechas | Primer/último día del mes obligado por validación | **Normalización a primer/último día del mes en el backend**, transparente al usuario. UI puede ofrecer un día concreto, el backend lo redondea al inicio del mes pedido (y cierra el anterior el último día del mes anterior). Onboarding es excepción: conserva fecha tal cual |
| Edición de un miembro existente | PATCH del % en la misma fila | **Cierre del tramo + apertura de uno nuevo** en la fecha efectiva |
| Reemplazo | DELETE + POST como operaciones separadas | **Operación atómica de "reemplazo"** con una sola fecha de corte |
| Baja del asesor (`causesBaja` + `successorId`) | Flujo dedicado con ADR-0017 | **Eliminado**. La reasignación de tareas la infiere obligations a partir de los eventos AMQP de close/open |
| Unicidad de empleado por cliente | Partial unique `(client, employee) WHERE date_to IS NULL` (FR-021 v1) | **Sin constraint**. Misma persona puede tener Responsable + Coordinador + Asesor activos simultáneamente. Sin protección contra duplicados accidentales (decisión PO 2026-06-04 — minimizar restricciones defensivas) |
| Antigüedad del empleado en el cliente | No existía | **Campo derivado nuevo** `inClientSince` calculado server-side (renombrado desde `tenureSince` en una iteración intermedia) |
| Cambios futuros | No soportado explícitamente | **Soportado** — `dateFrom > today` permitido. Si ya hay un tramo futuro pre-existente para la misma persona+rol, el nuevo tramo se "encaja" entre el corte actual y ese futuro (FR-006-bis); el tramo futuro se respeta |
| Nombre del flag de asesor principal | `is_primary_advisor` | **Renombrado a `is_main`** |
| `clientTeam`: `startDate`/`endDate` propios | Sí (FR-022 v1) | **Eliminados** — la vida del team se infiere de sus asignaciones |
| `client_team_assignment`: `clientId`/`department` denormalizados | Sí (para partial uniques) | **Eliminados** — se accede vía JOIN con `clientTeam`. Los partial uniques que dependían de ellos pasan a validación de servicio |

---

## 4. Modelo conceptual

### Schema simplificado (decidido 2026-06-04)

```
client_team
- id              uuid PK
- client_id       uuid FK → client
- department      enum (fiscal | laboral)
- created_at, updated_at
- created_by, updated_by    string (email | "system:onboarding")
- version         smallint  (optimistic concurrency)

client_team_assignment
- id              uuid PK
- client_team_id  uuid FK → client_team
- employee_id     uuid FK → employee
- role            enum (responsable | coordinador | asesor | tecnico)
- percentage      smallint (1..100, default 100)
- date_from       date
- date_to         date NULL    (NULL = tramo activo)
- is_main         boolean      (renombrado desde is_primary_advisor; solo válido si role='asesor')
- created_at, updated_at      (auto-managed; sin created_by/updated_by — el "quién" vive en client_team_assignment_change)
- version         smallint

client_team_assignment_change
- id                            uuid PK
- client_team_assignment_id     uuid FK → client_team_assignment
- action                        enum (opened | closed | percentage_changed |
                                       role_changed | main_changed | voided)
- employee_id_before            uuid NULL
- employee_id_after             uuid NULL
- role_before                   enum NULL
- role_after                    enum NULL
- percentage_before             smallint NULL
- percentage_after              smallint NULL
- is_main_before                boolean NULL
- is_main_after                 boolean NULL
- date_from_before              date NULL
- date_from_after               date NULL
- date_to_before                date NULL
- date_to_after                 date NULL
- created_at                    timestamp   (auto on insert — = momento del cambio)
- updated_at                    timestamp   (auto on update — normalmente = created_at salvo corrección posterior)
- created_by                    string      (email | "system:onboarding" — quién hizo el cambio)
- updated_by                    string NULL (quién corrigió el registro de audit, si aplica)
```

Cambios respecto al modelo de la v1:
- `clientTeam` ya **no** tiene `startDate`/`endDate` propios. La vida del team se infiere de sus asignaciones.
- `client_team_assignments` ya **no** tiene `clientId` ni `department` denormalizados. Se acceden vía JOIN con `clientTeam`. Implica que los partial uniques que usaban esos campos (FR-021 v1, asesor main unique) no se enforce a nivel BD — pasan a validación de servicio.
- `is_primary_advisor` se renombra a `is_main` (nombre más neutro).

### Asignación (`client_team_assignments`)
Tramo temporal: una persona, en un rol, dentro de un `clientTeam`, durante un intervalo.

### Equipo (`clientTeam`)
Agrupador `(clientId, department)`. Multi-equipo permitido (varios `clientTeam` para el mismo `(clientId, department)`). Las validaciones de cobertura son **cross-team** dentro del par `(clientId, department)`, no por equipo individual.

### Vista vigente
Función `getActiveTeamAt(clientId, department, date)` devuelve todas las asignaciones donde `dateFrom <= date AND (dateTo IS NULL OR dateTo > date)` (half-open: `dateTo` del tramo saliente = `dateFrom` del tramo entrante — sin `±1 día`). Por defecto `date = today`.

### Modelo de fotos de departamento (governing model)

El historial temporal de un `(client, department)` es una **secuencia ordenada de fotos completas**. Cada snapshot (onboarding o UI) es una foto de todos los equipos y roles del departamento, estampada con una fecha efectiva `D`. Cada foto gobierna el intervalo `[D, N)`:

- `N` = `dateFrom` del siguiente snapshot del mismo `(client, department)` — **a nivel de departamento, sin distinción de equipo ni de rol**.
- Si no hay snapshot posterior, `N = ∞` (tramo abierto, `dateTo = NULL`).

Al insertar un nuevo snapshot con fecha `D`:
1. El engine calcula `N` department-wide.
2. Solo el intervalo `[D, N)` se reescribe: diff contra el estado en efecto en `D`.
3. El snapshot en `N` se **preserva byte-for-byte** — incluye a las personas que lista para ese momento. Si ese snapshot sigue listando a alguien que el nuevo elimina, esa persona "reaparece" en `N`. Para extender el cambio más allá de `N`, el usuario debe editar el snapshot de `N` explícitamente.
4. Tramos activos en `[D, N)` que la nueva foto no incluye: **cerrados** (`dateTo = D`) si `dateFrom < F`; **borrados físicamente** si `dateFrom ≥ F` (eran provisionales — planes, no hechos).
5. Tramos de personas nuevas en la foto: abiertos desde `D` hasta `N` (o sin `dateTo` si `N = ∞`).
6. **Coalescing**: si una persona aparece sin cambio de atributos en fotos consecutivas, los tramos contiguos se fusionan en uno solo.

> **UX**: la UI debe mostrar los snapshots futuros ya planificados. Una persona reemplazada en `D` puede "reaparecer" en un snapshot posterior que la sigue listando — este comportamiento debe ser visible para el usuario.

### Reemplazo / cambio de % / redistribución
Vía API normal (UI backoffice):
1. **Normalizar la fecha efectiva** a `D = primer día del mes pedido` (mes en curso o futuro). Rechazar si cae en mes pasado.
2. **Si ya existe un tramo previo en el mismo mes** (creado por otra operación dentro del mismo mes en curso), borrarlo o convertirlo según corresponda (FR-007 — solo el último estado del mes sobrevive).
3. Para cada miembro saliente o que cambia: `UPDATE` cerrando con `dateTo = D` (half-open — mismo valor que `dateFrom` del tramo entrante, ver FR-002).
4. Para cada miembro entrante o que cambia: `INSERT` con `dateFrom = D` y `dateTo = N` donde `N` = siguiente fecha de foto del departamento (governing model, ver FR-006-bis) o `NULL` si no hay foto posterior.

Todas las operaciones de un cambio ocurren en la misma transacción con `SELECT … FOR UPDATE` sobre la fila `client` para serializar transiciones (FR-024).

### Onboarding
El subscriber AMQP del routing key `client-onboarding-assignment` materializa el alta inicial del equipo de un cliente con las fechas **tal cual las recibe**. No aplica normalización, no rechaza fechas en mes pasado. Es el único camino para tener tramos cuyo `dateFrom` no sea primer día de mes.

### Antigüedad (`inClientSince`)
Campo derivado calculado al leer. Para una pareja `(clientId, employeeId)`:
- Buscar las asignaciones de ese empleado en ese cliente ordenadas por `dateFrom` descendente.
- Recorrer hacia atrás mientras los tramos encadenen sin hueco (half-open: `dateTo` del tramo anterior = `dateFrom` del siguiente).
- `inClientSince` = `dateFrom` del tramo más antiguo de esa cadena continua.
- Si el empleado salió y volvió (hay un hueco entre tramos), la cadena se rompe — `inClientSince` arranca del último re-ingreso.

Implementado en `compute-in-client-since.helper.ts` con tests unitarios.

---

## 5. User Stories

Cada story es un **paquete funcional testeable por un revisor no técnico**. Backend y frontend van dentro como tareas internas (ver "Notas técnicas internas" debajo de cada US — sección no se sube a Jira). El **contract OpenAPI/AMQP se cierra primero** para que el FE pueda arrancar con mocks mientras el BE implementa.

Formato listo para `/speckit-atlassian-sync-push`: **Título → Contexto → Objetivo → Criterios de aceptación**. Todo lo demás (FRs cubiertos, contract, dependencias, fuera de scope, tareas internas) vive bajo un marcador HTML `<!-- internal-only -->` que el sync ignora.

### MVP P1

#### US-01 — Alta inicial del equipo desde la UI

**Contexto**
Hoy un cliente nuevo o un cliente migrado desde el modelo legacy no tiene equipo en el modelo nuevo. Hasta que un responsable lo dé de alta no se pueden asignar tareas correctamente ni propagar el equipo a downstream. Esta story habilita la primera carga manual desde el backoffice.

**Objetivo**
Como responsable o coordinador, quiero dar de alta el primer equipo de un cliente (responsable, coordinador opcional, asesores, técnicos) desde la ficha del cliente, para que pgi-api conozca quién opera el cliente y los flujos posteriores (tareas, integraciones) se asignen correctamente.

**Criterios de aceptación**
1. Abro un cliente cuyo equipo fiscal está vacío y veo el botón "Crear equipo fiscal".
2. Añado responsable + coordinador + asesor (marcando este último como main). Cada miembro se persiste tras Guardar y aparece inmediatamente en la pantalla.
3. Tras añadir el asesor main, la cobertura llega a 100% y el banner amarillo "equipo incompleto" desaparece.
4. Si intento añadir miembros en un departamento donde el cliente no tiene `ProvidedService` activo, veo un error claro y no se persiste nada.
5. La cobertura técnica se considera "no aplicable" mientras no añada ningún técnico — no bloquea el estado del equipo.
6. Puedo consultar la vista vigente a una fecha pasada (selector "ver equipo a fecha…") y veo el equipo tal y como estaba ese día. Por cada miembro veo el campo `inClientSince` (fecha desde la que entró al cliente sin interrupción).

<!-- internal-only -->
**Notas técnicas internas**
- **API contract** (ver `contracts/rest/client-assignments.openapi.yaml`). URLs como recursos puros, NestJS exception shapes, `@PermissionsRequired`:
  - `PUT /api/v1/clients/{clientId}/team-assignments` — aplica un snapshot completo del `(client, department)`. Body `TeamSnapshotRequest`: `{ department, dateFrom, teams: [{ clientTeamId?, responsable, coordinador?, asesores: [{ employeeId, percentage, isMain }], tecnicos: [{ employeeId, percentage }] }] }`. `dateFrom` es cualquier día del mes; el engine normaliza a día 1. RESP/COORD no llevan `percentage` (siempre 100, sistema — D4). El engine auto-crea `ClientTeam` si `clientTeamId` es ausente. Response 204. Requiere `BackofficePermissions.CLIENT_ASSIGNMENT_EDIT`.
  - `GET /api/v1/clients/{clientId}/team-assignments?department={dept}&date={date?}` — listado vigente a fecha (default hoy; acepta fechas pasadas y futuras). Response `{ data: [...], total, coverage, mainAsesorPresent, status }`. Cada miembro lleva `inClientSince` (derivado server-side, ver §4). Requiere `BackofficePermissions.CLIENT_ASSIGNMENT_VIEW`.
  - `GET /api/v1/clients/{clientId}/team-assignments/{id}` — detalle de una asignación.
  - Errores: `NestJS exception filters` → `{ statusCode, message, error }`. 409 en conflicto de versión. 422 en reglas de negocio (mes pasado, % ≠ 100, main incorrecto, equipo omitido…).
- **Convenciones REST aplicadas**: ver `.claude/rules/rest-api-design.md` (sección "Convenciones reales en uso"). El servicio pgi-api tiene patrones establecidos y este endpoint los respeta.
- **FRs cubiertos**: FR-001, FR-002, FR-009, FR-010, FR-011, FR-012, FR-013, FR-015, FR-016, FR-021, FR-022, FR-024, FR-025.
- **Fuera de scope**: editar miembros existentes (US-02), cambios futuros (US-03), log de cambios (US-05), verificar efecto en obligations (US-06).

<!-- jira-links -->
(US-01 es la base — no tiene dependencias entrantes. Otras stories enlazarán a esta como `is-blocked-by`.)
<!-- /jira-links -->
<!-- /internal-only -->

---

#### US-02 — Editar el equipo en el mes en curso

**Contexto**
Las composiciones reales de equipos cambian con frecuencia dentro del mes (alguien deja la empresa, se reasigna carga, entra un nuevo asesor para apoyar). Hoy esto se hace machacando filas vivas y perdiendo histórico. Esta story habilita la edición temporal correcta dentro del mes en curso, manteniendo el histórico intacto y normalizando las fechas para evitar cortes en mitad de mes.

**Objetivo**
Como responsable o coordinador, quiero modificar la composición del equipo dentro del mes en curso (sustituir una persona, cambiar el porcentaje de carga, redistribuir cobertura entre varios), para mantener el equipo alineado con la realidad operativa sin esperar al cambio de mes.

**Criterios de aceptación**
1. **Reemplazo simple**: en un equipo activo, sustituyo un asesor por otro al mismo porcentaje a partir de una fecha del mes en curso. El saliente cierra con `dateTo` = primer día del mes en curso (half-open — mismo valor que `dateFrom` del entrante); el entrante queda activo desde ese primer día. La cobertura no se altera.
2. **Cambio de porcentaje**: reduzco el porcentaje de un asesor y reparto el restante a otro que entra. El asesor que se queda tiene dos tramos consecutivos sin hueco; la cobertura suma 100% y su antigüedad se preserva.
3. **Redistribución**: un asesor sale y dos nuevos entran repartiendo su porcentaje. La cobertura sigue al 100% y queda exactamente un asesor main.
4. **Segundo cambio en el mismo mes**: tras un cambio, hago otro distinto unos días después. El tramo del primer cambio se sobrescribe — solo el resultado final del mes queda visible en la UI; el primero se voida (queda en BD pero invisible).
5. **Mes pasado rechazado**: si intento meter un cambio con fecha en un mes anterior al actual, me lo rechaza con mensaje "no se pueden modificar asignaciones del pasado".

**Ejemplo**
Hoy es 15 de junio. Tengo el equipo fiscal con Alfonso al 100% como asesor main. Sustituyo a Alfonso por David al 100% indicando fecha 15/06. Tras guardar veo:

| Empleado | Rol | Desde | Hasta | % |
|---|---|---|---|---|
| Alfonso | asesor (main) | 20/05/2026 | **01/06/2026** | 100 |
| David | asesor (main) | **01/06/2026** | — | 100 |

Cobertura asesores 100%, equipo `complete`. El log de cambios (US-05) registra dos filas: `action='closed'` sobre Alfonso y `action='opened'` sobre David.

<!-- internal-only -->
**Notas técnicas internas**
- **API contract**. URLs como recursos puros (sin verbos).
  - **Snapshot del equipo** (reemplazo, redistribución, cambio de %): `PUT /api/v1/clients/{clientId}/team-assignments` con body `TeamSnapshotRequest`: `{ department, dateFrom, teams: [{ clientTeamId, responsable, coordinador?, asesores: [{ employeeId, percentage, isMain }], tecnicos: [...] }] }`. `dateFrom` es cualquier día del mes en curso; el engine normaliza a `F`. RESP/COORD sin `percentage`. Idempotente. Response 204.
  - **Modificar metadato de un tramo** (cambiar `isMain` o cerrar): `PUT /api/v1/clients/{clientId}/team-assignments/{id}` con body `{ isMain?, dateTo?, version }`. `dateTo` es el half-open upper bound (primer día del mes en que deja de estar activo). Response 204.
  - **Borrar tramo provisional (FR-007)**: `DELETE /api/v1/clients/{clientId}/team-assignments/{id}`. Solo tramos con `dateFrom ≥ F`. DELETE físico; log registra `action='voided'`. Response 204.
  - Permission común: `BackofficePermissions.CLIENT_ASSIGNMENT_EDIT`. 409 si `version` no coincide. 422 si `dateFrom` en mes pasado, snapshot inválido (% ≠ 100, main incorrecto, equipo omitido, `clientTeamId` desconocido…).
- **FRs cubiertos**: FR-002, FR-003, FR-005, FR-007, FR-008, FR-009, FR-013, FR-014, FR-017, FR-024.
- **Fuera de scope**: cambios con `dateFrom` futuro (US-03), reasignación de tareas en obligations (US-06).

<!-- jira-links -->
- is-blocked-by: US-01
<!-- /jira-links -->
<!-- /internal-only -->

---

#### US-04 — Alta inicial del equipo desde Onboarding (AMQP)

**Contexto**
Otros sistemas (portal del cliente, proceso comercial, integraciones externas) dan de alta clientes con su equipo inicial ya definido. Sin un canal automático, los responsables tendrían que volver a meter manualmente los datos en pgi-api, duplicando trabajo y arriesgándose a inconsistencias. Esta story habilita la materialización automática vía AMQP.

**Objetivo**
Como sistema externo (producer del evento `client-onboarding-assignment`), quiero notificar a pgi-api el equipo inicial de un cliente con las fechas que envío, para que el equipo quede materializado sin necesidad de carga manual.

**Criterios de aceptación**
1. Se publica un evento con 3 miembros y `dateFrom=20/05/2026`. El subscriber crea `clientTeam` + 3 asignaciones con esas fechas exactas. El responsable abre la ficha y ve el equipo materializado.
2. Las fechas en BD son exactamente las recibidas en el evento (no normalizadas) — confirma la excepción al modelo de mes-en-curso.
3. Si el evento llega malformado (campos obligatorios ausentes, department inválido), va a DLQ con error claro en logs.
4. Si el evento llega para un cliente que ya tiene equipo activo en ese departamento, el subscriber lo rechaza y lo manda a DLQ con error claro (no machaca el equipo existente).

<!-- internal-only -->
**Notas técnicas internas**
- **API contract**:
  - Subscriber AMQP: routing key `client-onboarding-assignment` (nombre exacto pendiente con producer — ver OQ-005)
  - Schema del payload documentado en `contracts/amqp/client-onboarding-assignment.schema.json`
- **FRs cubiertos**: FR-004, FR-020.
- **Fuera de scope**: actualizaciones de equipo vía onboarding (solo alta inicial — actualizaciones van por UI o por otra story futura).

<!-- jira-links -->
- is-blocked-by: US-01
- relates-to: ticket del producer del evento `client-onboarding-assignment` (cross-team — pendiente identificar)
<!-- /jira-links -->
<!-- /internal-only -->

---

#### US-05 — Log de cambios sobre el equipo

**Contexto**
A medida que el modelo temporal acumula cambios, surgen consultas regulatorias o de incidentes que requieren saber **quién** hizo **qué** cambio y **cuándo** sobre el equipo de un cliente. La vista vigente y la vista a fecha pasada (cubiertas por US-01) responden "qué tramos existían" pero no "quién los cambió y en qué momento". Esta story añade el log de auditoría detallado con before/after.

**Objetivo**
Como responsable o admin, quiero consultar quién hizo qué cambio sobre las asignaciones de un cliente y cuándo (con before/after de cada cambio), para auditoría regulatoria, resolución de incidencias y revisión operativa del equipo.

**Criterios de aceptación**
1. Navego a la pestaña "Log de cambios" de un cliente. Veo todos los cambios realizados sobre el equipo en orden cronológico descendente: fecha del cambio, autor, tipo de acción (alta, cierre, cambio de %, cambio de rol, cambio de main, void) y los valores antes/después.
2. Filtro por rango de fechas y por departamento y la lista se actualiza.
3. Cuando un cambio fue ejecutado por el subscriber de onboarding, el autor aparece como `system:onboarding` y queda claro que no fue una acción manual.
4. Cuando un tramo se "void" por FR-007, aparece en el log con `action='voided'` y los valores antes del void.
5. Cada cambio tiene su propio `createdAt` y `createdBy` inmutables: si reviso un log de hace 2 meses sigo viendo quién lo hizo, aunque la persona ya no esté en la empresa.

<!-- internal-only -->
**Notas técnicas internas**
- **Recurso aparte** (no comparte tabla con `client_team_assignment`): tabla `client_team_assignment_change` con columnas before/after y audit propio (`created_at`, `created_by`, `updated_at`, `updated_by`). Ver §4.
- **API contract**: `GET /api/v1/clients/{clientId}/team-assignment-changes?department={dept}&from={date?}&to={date?}` — log paginado por rango (default últimos 90 días). Response `{ data, total }` donde cada item es una fila de change. Requiere `BackofficePermissions.CLIENT_ASSIGNMENT_VIEW`.
- **Producer del log**: cada operación de US-01/US-02/US-03/US-04 inserta filas en `client_team_assignment_change` dentro de la misma transacción que mutó `client_team_assignment` (atomicidad — no se puede perder un cambio del log).
- **Esta US sustituye a la anterior "Vista histórica y antigüedad"**: la vista del equipo a fecha pasada y el campo `inClientSince` (antes `tenureSince`) se sirven desde el endpoint de US-01 (`GET .../team-assignments?date=`); aquí lo nuevo es el log de cambios.
- **FRs cubiertos**: FR-019, FR-022.
- **Fuera de scope**: edición de filas del log (es read-only — no hay endpoints de mutación).

<!-- jira-links -->
- is-blocked-by: US-01
- is-blocked-by: US-02
<!-- /jira-links -->
<!-- /internal-only -->

### P2

#### US-03 — Programar cambios futuros con preservación de tramos

**Contexto**
Algunos cambios de equipo se conocen con antelación (un asesor sale en septiembre, una redistribución entra en enero). Sin soporte de cambios futuros, los responsables tienen que esperar al día y aplicarlos manualmente — con riesgo de olvido. Además, si ya hay cambios futuros planificados, un nuevo cambio intermedio no debe invalidarlos.

**Objetivo**
Como responsable, quiero registrar con antelación cambios de equipo que entran en vigor en un mes posterior, para planificar reemplazos, redistribuciones o cambios de % sin alterar la vista vigente hasta que llegue la fecha — y sin perder cambios futuros ya planificados.

**Criterios de aceptación**
1. Hoy es 20/06. Programo un cambio efectivo 01/09 (David sale, Juan y Paloma entran al 50%). La vista vigente "a hoy" sigue mostrando David al 100%. La vista "a 15/09" muestra Juan y Paloma.
2. Tras el anterior, programo un cambio efectivo 01/08 (David al 75%, Juan al 25%). El cambio de septiembre queda intacto. David tiene 3 tramos consecutivos (100% → 75% → 50%), Juan tiene 2 (25% → 50%).
3. La UI muestra un indicador "cambio programado para 01/09" sobre las asignaciones afectadas mientras estoy antes de esa fecha.
4. Si registro un cambio efectivo 15/09 (mid-month), el backend lo normaliza a 01/09 sin que el usuario tenga que pensar en mes/día.
5. Si intento un cambio retroactivo (fecha en mes pasado), me lo rechaza con mensaje claro.

<!-- internal-only -->
**Notas técnicas internas**
- **API contract**: misma operación que US-02 — `PUT /api/v1/clients/{clientId}/team-assignments` con `TeamSnapshotRequest`. El `dateFrom` puede ser un mes futuro; el engine lo acota hasta el siguiente snapshot del departamento (`N` — governing model, FR-006-bis). Para previsualizar: `GET …/team-assignments?department={dept}&date={future-date}`.
- **FRs cubiertos**: FR-002, FR-006, FR-006-bis.
- **Fuera de scope**: edición destructiva de cambios futuros ya programados (se sobrescribe programando otro encima en el mismo mes — FR-007).

<!-- jira-links -->
- is-blocked-by: US-02
<!-- /jira-links -->
<!-- /internal-only -->

---

#### US-06 — Reasignación automática de tareas tras cambio de asesor (cross-service)

**Contexto**
Cuando un asesor sale del equipo de un cliente, las tareas abiertas asignadas a él en `pd-service-obligations-api` deberían pasar automáticamente al asesor entrante a partir de la fecha del cambio — sin intervención manual. Hoy esto no ocurre: el responsable tendría que reasignar manualmente cada tarea desde obligations. Esta story cierra el bucle cross-service.

**Objetivo**
Como responsable que cambia un asesor en el equipo, quiero que las tareas abiertas en obligations del cliente pasen automáticamente al nuevo asesor, para no perder trabajo en tránsito durante un reemplazo y no tener que tocar nada manualmente.

**Criterios de aceptación**
1. Cliente X tiene 5 tareas abiertas en obligations asignadas a David. En pgi-api cambio David por Juan en el equipo (efectivo 01/06). Abro el panel de tareas del cliente en la UI de obligations y veo las 5 tareas asignadas a Juan.
2. Las tareas con `dueDate < 01/06` siguen asignadas a David (era trabajo suyo que tenía pendiente).
3. Las tareas con `dueDate >= 01/06` pasan a Juan.
4. Si Juan no existe en obligations (el empleado no está dado de alta en el otro servicio), el subscriber falla y la tarea queda como estaba — sin perder dato — y se registra el error.

<!-- internal-only -->
**Notas técnicas internas**
- **API contract**:
  - Publisher en pgi-api: `pgi-api.v1.client-team-assignment.opened` y `.closed` (los eventos se emiten en cualquier mutación de US-01/02/03/04 — aquí solo se confirma el payload completo).
  - Subscriber en obligations-api: consume y aplica la regla de reasignación.
- **FRs cubiertos**: FR-017, FR-018.
- **Fuera de scope**: reasignación manual (no aplica), reasignación de tareas cerradas (solo abiertas), cambio de prioridad/dueDate (solo cambia el asignado).

<!-- jira-links -->
- is-blocked-by: US-02
- relates-to: cross-service obligations-api (pendiente ticket espejo en proyecto de obligations)
<!-- /jira-links -->
<!-- /internal-only -->

> US-07 (auditoría completa) ha sido **fusionada en US-05** (log de cambios) en la v2 del 2026-06-04. El log temporal y el log de auditoría son la misma vista; no hay dos endpoints distintos.

---

#### US-07 — Propagación del nuevo equipo a plataforma del dato

**Contexto**
Cuando pgi-api crea o cierra una asignación de `ClientTeamAssignment`, `pd-service-data-factory` y `pd-service-jira-adapter` no se enteran: solo escuchan los eventos del modelo antiguo (`client_assignment_persisted`). El flujo del dato queda roto — los nuevos campos (`percentage`, `isMain`) nunca llegan a la plataforma del dato ni a Jira Assets. El modelo antiguo (`ClientAssignment`) se mantiene en paralelo; no se migra.

**Objetivo**
Como plataforma del dato, quiero recibir los eventos del nuevo modelo de equipo para persistir las asignaciones con los atributos nuevos y mantener Jira Assets sincronizado, sin romper el flujo existente del modelo antiguo.

**Criterios de aceptación**
1. Cuando se crea una asignación de equipo en pgi-api, data-factory la persiste con `percentage` e `isMain` y la propaga a los consumidores downstream.
2. Cuando se cierra una asignación (se establece `dateTo` o se anula), data-factory actualiza su copia y propaga el cierre.
3. El flujo existente del modelo antiguo (`ClientAssignment`) no sufre ningún cambio ni interrupción.
4. Jira Assets refleja el cambio de equipo dentro de la ventana de sync habitual del adapter.
5. Si el evento llega para un `clientTeamAssignmentId` desconocido, data-factory lo crea (upsert idempotente — los mensajes AMQP pueden reentregarse).

<!-- internal-only -->
**Notas técnicas internas**
- Subscriber en `pd-service-data-factory`: routing keys `pgi-api.v1.client-team-assignment.opened` y `pgi-api.v1.client-team-assignment.closed`.
- Nueva entidad `ClientTeamAssignment` en data-factory (paralela a `ClientAssignment` existente — **no migrar** datos del modelo antiguo).
- Re-publica `data-factory.v1.client-team-assignment.persisted` tras cada upsert, siguiendo el patrón del modelo antiguo.
- Subscriber en `pd-service-jira-adapter`: consume `data-factory.v1.client-team-assignment.persisted` y sincroniza a Jira Assets siguiendo el patrón del subscriber de `ClientAssignment` existente.
- **FRs cubiertos**: FR-019.
- **Fuera de scope**: migración de datos legacy, cambios en `pd-service-obligations-api` (cubierto en US-06), cambios en `pc-service-portalcliente-api`.

<!-- jira-links -->
- is-blocked-by: US-01
- relates-to: cross-service pd-service-data-factory (requiere ticket espejo)
- relates-to: cross-service pd-service-jira-adapter (requiere ticket espejo)
<!-- /jira-links -->
<!-- /internal-only -->

---

## 6. Requisitos funcionales

### Composición y persistencia

- **FR-001** — Toda asignación persiste como tramo con `dateFrom` obligatorio. `dateTo` NULL indica tramo activo a partir de `dateFrom`.
- **FR-002** — Las operaciones vía API normal (UI backoffice) **normalizan la fecha efectiva del cambio al primer día del mes pedido** usando **intervalos half-open `[dateFrom, dateTo)`** (activo en `t` ssi `dateFrom <= t AND (dateTo IS NULL OR dateTo > t)`):
  - Si `effectiveDate` cae en el mes en curso, se ajusta a `F` (primer día del mes en curso). El tramo saliente cierra con `dateTo = F` (= `dateFrom` del tramo entrante). Sin `±1 día`.
  - Si `effectiveDate` cae en un mes futuro, se ajusta al primer día de ese mes (`D`). El tramo saliente cierra con `dateTo = D`.
  - El frontend puede dejar al usuario indicar un día concreto; el backend lo redondea de forma transparente. Se acepta perder la trazabilidad fina del día real del cambio dentro del mes, a cambio de evitar tramos sucios en mitad de mes.
  - **`F` (rewrite frontier)** = primer día del mes en curso. Tramos con `dateFrom ≥ F` son **provisionales** (borrables cuando son superseded). Tramos con `dateFrom < F` son **inmutables** (solo se cierran, nunca se borran físicamente).
- **FR-003** — Cambios con `effectiveDate` en un mes anterior al mes en curso **se rechazan** con HTTP 422 `CLIENT_TEAM_ASSIGNMENT_PAST_DATE_NOT_ALLOWED`. El sistema no permite manipular el histórico vía la API normal.
- **FR-004** — **Excepción onboarding**: las asignaciones que entran por el subscriber AMQP de onboarding (routing key `client-onboarding-assignment` o equivalente — exacto pendiente de confirmar con el producer) **conservan las fechas tal cual las recibe**, sin normalización a inicio de mes y sin restricción de mes pasado/futuro. Es el único camino para introducir tramos con fechas no-normalizadas.
- **FR-005** — Una operación de **reemplazo** (cambio de persona, cambio de %, redistribución, o salida sin sustituto) se ejecuta como una transacción atómica que cierra los tramos salientes con `dateTo = D` y abre los entrantes con `dateFrom = D`, donde `D` = primer día del mes normalizado (half-open — no `±1 día`). La fecha normalizada actúa como punto de corte único.
- **FR-006** — Se permite registrar asignaciones con `effectiveDate` futuro (mes posterior al actual). La vista vigente del equipo a `today` no las incluye hasta que llegue la fecha normalizada.
- **FR-006-bis** — **Governing model: el bound de inserción es department-wide.** Al insertar un snapshot con fecha efectiva `D`, el engine calcula `N = dateFrom` del siguiente snapshot ya registrado del mismo `(client, department)`, **sin distinción de equipo ni de rol** — cualquier cambio en cualquier equipo o rol del departamento crea un breakpoint que acota a todos los demás. Los nuevos tramos abren desde `D` hasta `N`; si no hay snapshot posterior, `dateTo = NULL`. El snapshot en `N` se preserva byte-for-byte: si sigue listando a alguien que el snapshot `D` elimina, esa persona reaparece en `N`. Para extender el cambio de `D` más allá de `N`, el usuario edita el snapshot de `N` explícitamente. Ver §4 "Modelo de fotos de departamento".
- **FR-007** — Cuando, dentro del mes en curso, llegan **múltiples cambios sucesivos** sobre el mismo `(client, department)`, los tramos previamente creados en este mismo mes (cualquier fila con `dateFrom = primer día del mes en curso` que no exista de antes) son **machacados** por el cambio más reciente:
  - Si el miembro sigue presente con otros atributos: `UPDATE` in-place de su fila (cambia `percentage`, `role`, `isMain`).
  - Si el miembro ya no debe estar tras el nuevo cambio: como estos tramos tienen `dateFrom = F` (son provisionales, ver FR-002), se **borran físicamente** (`DELETE`). El log (`client_team_assignment_change`) registra el borrado con `action='voided'` antes del `DELETE`, preservando la trazabilidad. El mismo criterio aplica a tramos futuros provisionales (`dateFrom > F`) que son superseded por un nuevo snapshot.
  - Los tramos creados en meses **anteriores** al actual NO se machacan; se cierran con `dateTo` como en una operación normal.
  Razón: el modelo no admite dos cortes en el mismo mes; solo la última intención del usuario sobrevive como tramo "vivo" en BD. El log de cambios (US-05) registra cada operación.
- **FR-008** — La edición destructiva (UPDATE/DELETE de tramos históricos con `dateFrom` en mes anterior al actual o `dateTo` no nulo) está **prohibida** vía API normal. Solo se permite mutar tramos cuyo `dateFrom` esté en el mes en curso o tramos activos (`dateTo IS NULL`) para: (a) cerrarlos, (b) ajustar `isMain`, (c) machacar conforme a FR-007.

### Validaciones

- **FR-009** — Por cada `(client, department)`, la suma de `percentage` de los asesores activos a fecha `today` debe ser exactamente **100%**. Si no se cumple, el equipo está en estado `incomplete` (banner advisory en UI, no bloquea persistencia individual). Los porcentajes son **enteros** (1–100, sin decimales); valores no enteros, negativos o superiores a 100 se rechazan con HTTP 422.
- **FR-010** — Por cada `(client, department)`, la suma de `percentage` de los técnicos activos a fecha `today` debe ser exactamente **100%** **si existe al menos un técnico**. Si no hay ningún técnico, la cobertura técnica es "no aplicable" y no bloquea.
- **FR-011** — `is_main=true` solo es válido cuando `role='asesor'`. Hay **exactamente uno** activo por `(client, department)` — validado a nivel de servicio (no a nivel BD, porque `client` y `department` no están denormalizados en `client_team_assignments`). CHECK constraint `is_main = false OR role = 'asesor'` sí se aplica a nivel BD.
- **FR-012** — Antes de crear una asignación en departamento `X`, el cliente debe tener al menos un `ProvidedService` activo con `family=X`. Si no, rechazar con HTTP 422 `CLIENT_TEAM_ASSIGNMENT_NO_PROVIDED_SERVICE`.
- **FR-013** — No se valida ninguna unicidad de tipo `(client, employee)` ni `(client, employee, role)`. La misma persona puede tener varias asignaciones activas simultáneamente con roles distintos (responsable + coordinador + asesor) o, accidentalmente, dos del mismo rol. El sistema confía en el usuario; no añade restricciones defensivas. La cobertura sumaría como corresponda en caso de duplicado.
- **FR-014** — La transición del estado de cobertura a "completo y consistente" tras una operación de escritura dispara la publicación de eventos AMQP descritos en FR-017.

### Composición mínima

- **FR-015** — Un equipo se considera **completo** cuando, por `(client, department)`: (a) hay exactamente 1 responsable activo, (b) hay al menos 1 asesor activo, (c) la cobertura de asesores suma 100%, (d) si hay técnicos, su cobertura suma 100%, (e) hay 1 asesor main activo.
- **FR-016** — Mientras un equipo esté incompleto, el sistema persiste las escrituras individuales pero **suprime** la publicación AMQP a downstream y muestra un banner advisory en UI.

### Publicación AMQP y reasignación de tareas

- **FR-017** — En cada `INSERT` y `UPDATE` (cierre o machaque por FR-007) de una `ClientTeamAssignment`, el servicio publica un evento AMQP con routing key `pgi-api.v1.client-team-assignment.opened` o `.closed`, payload mínimo: `assignmentId`, `clientId`, `department`, `role`, `employeeId`, `percentage`, `effectiveDate` (dateFrom o dateTo), `isMain`, `version`. Solo se publica si el equipo destino está completo (FR-015) o, si no, se difiere hasta la operación que lo complete (entonces se emite un lote con los cambios diferidos en orden cronológico).
- **FR-018** — `pd-service-obligations-api` consume estos eventos y reasigna automáticamente las tareas abiertas según el asesor vigente en su `dueDate`. No hace falta marcar nada en pgi-api: la reasignación se infiere de las fechas.
- **FR-019** — `pd-service-data-factory` y `pd-service-jira-adapter` consumen los mismos eventos para mantener sus copias propias del estado del equipo. Política de sync de jira-adapter pendiente con team lead (no bloquea US1).
- **FR-020** — pgi-api consume un evento de **onboarding** con routing key `client-onboarding-assignment` (nombre exacto pendiente de confirmar con el producer). El subscriber materializa las asignaciones recibidas en `client_team_assignment` **sin aplicar la normalización de FR-002 ni la restricción de FR-003** — las fechas se conservan exactamente como llegan. Cada inserción del onboarding también dispara los eventos AMQP de FR-017 (opened) hacia downstream, igual que cualquier escritura.

### Lectura

- **FR-021** — Endpoint `GET /api/v1/clients/{clientId}/team-assignments?department={dept}&date={date?}` devuelve la composición vigente a la fecha indicada (default `today`; acepta fechas pasadas y futuras). Por miembro: `assignmentId`, `employee`, `role`, `percentage`, `dateFrom`, `dateTo`, `isMain`, `inClientSince`, `version`. `inClientSince` se calcula server-side recorriendo los tramos del `(clientId, employeeId)` y devolviendo el `dateFrom` de la cadena continua más reciente (huecos rompen la cadena).
- **FR-022** — Endpoint `GET /api/v1/clients/{clientId}/team-assignment-changes?department={dept}&from={date?}&to={date?}` devuelve el log de cambios sobre el equipo en orden cronológico descendente. Cada item lleva: `id`, `action`, valores `*_before` y `*_after`, `createdAt`, `createdBy`. Paginable; default últimos 90 días si no se pasa rango.
- **FR-023** — La cobertura agregada `{ asesores, tecnicos, status }` viaja como parte del response de `FR-021` (siblings de `data`/`total`). No hay endpoint separado.

### Concurrencia

- **FR-024** — Toda operación de escritura sobre asignaciones de un `(client, department)` adquiere `SELECT ... FOR UPDATE` sobre la fila `client` correspondiente antes de leer cobertura y persistir cambios. Esto serializa transiciones de completo/incompleto y garantiza "exactamente un evento AMQP por transición" (mantiene la lógica de ADR-0015).
- **FR-025** — Las mutaciones de `ClientTeam` y `ClientTeamAssignment` usan optimistic concurrency con `version`. Cliente envía `version` actual; servidor incrementa o devuelve `409 VERSION_CONFLICT`.
- **FR-026** — Un `clientTeamId` presente en el snapshot debe pertenecer al `(client, department)` indicado. Un `clientTeamId` inexistente o perteneciente a otro cliente/departamento → rechazo HTTP 422.

---

## 7. Ejemplos canónicos

Estos ejemplos sirven como acceptance scenarios y como base para tests e2e. Asumen que la operación llega vía API normal (UI backoffice) salvo el §7.1 que es onboarding. Las fechas reflejan la **regla de normalización** de FR-002 y la conservación de fechas de FR-004.

### 7.1. Alta inicial del equipo vía onboarding (fecha original 20/05/2026)

El evento de onboarding (`client-onboarding-assignment`) llega con tres asignaciones para el cliente, todas con `effectiveDate=20/05/2026`. Como es onboarding, la fecha se conserva tal cual:

| empleado | rol | dateFrom | dateTo | % |
|---|---|---|---|---|
| Perico | coordinador | 20/05/2026 | NULL | 100 |
| Alberto | responsable | 20/05/2026 | NULL | 100 |
| Alfonso | asesor (primary) | 20/05/2026 | NULL | 100 |

Cobertura asesores = 100% ✓. Sin técnicos → cobertura técnica N/A. Equipo `complete` → se publican tres eventos `client-team-assignment.opened`.

### 7.2. Snapshot en mes en curso — foto única, sin fotos posteriores (registrado 15/06/2026, D = F = 01/06/2026)

Estado antes (de §7.1):
- Perico — coordinador — 20/05/2026 → NULL — 100
- Alberto — responsable — 20/05/2026 → NULL — 100
- Alfonso — asesor (main) — 20/05/2026 → NULL — 100

Operación: reemplazar Alfonso por David al 100%. La fecha efectiva del cambio cae en el mes en curso (junio) → `D = 01/06/2026`. Cierre de Alfonso: `dateTo = 01/06/2026` (half-open — mismo valor que `dateFrom` de David).

| empleado | rol | dateFrom | dateTo | % |
|---|---|---|---|---|
| Perico | coordinador | 20/05/2026 | NULL | 100 |
| Alberto | responsable | 20/05/2026 | NULL | 100 |
| Alfonso | asesor (main) | 20/05/2026 | **01/06/2026** | 100 |
| David | asesor (main) | **01/06/2026** | NULL | 100 |

Cobertura asesores `at=today` = 100% (solo David). Se publica `client-team-assignment.closed` para Alfonso y `.opened` para David en la misma transacción.

### 7.3. Cambio futuro sin tramos futuros previos — reemplazo (registrado 20/06/2026 con efectividad 01/09/2026 — David sale, Juan y Paloma entran al 50%)

Estado antes:
- Perico — coordinador — 20/05/2026 → NULL — 100
- Alberto — responsable — 20/05/2026 → NULL — 100
- David — asesor (main) — 01/06/2026 → NULL — 100

Operación: a partir de septiembre, David ya no está; Juan y Paloma asesores al 50% cada uno. Septiembre es futuro → `D = 01/09/2026`. Cierre de David: `dateTo = 01/09/2026` (half-open).

| empleado | rol | dateFrom | dateTo | % |
|---|---|---|---|---|
| Perico | coordinador | 20/05/2026 | NULL | 100 |
| Alberto | responsable | 20/05/2026 | NULL | 100 |
| David | asesor (main) | 01/06/2026 | **01/09/2026** | 100 |
| Juan | asesor (main) | **01/09/2026** | NULL | 50 |
| Paloma | asesor | **01/09/2026** | NULL | 50 |

Hasta el 31/08 sigue David al 100 (activo en `[01/06, 01/09)`). Desde el 01/09 entran Juan (main) + Paloma. El responsable elige main vía UI; el sistema no infiere. No hay tramos futuros pre-existentes que respetar — los nuevos abren sin `dateTo`.

### 7.4. Cambio futuro sin tramos futuros previos — reasignación (registrado 20/06/2026 con efectividad 01/09/2026 — David sigue al 50%, Juan entra al 50%)

Estado antes: igual que §7.3 (David al 100, sin tramos futuros).

Operación: desde septiembre, David baja a 50% y entra Juan al 50%. `D = 01/09/2026`. David cierra el tramo de 100 con `dateTo = 01/09/2026` (half-open) y abre nuevo tramo de 50 desde `01/09/2026`.

| empleado | rol | dateFrom | dateTo | % |
|---|---|---|---|---|
| Perico | coordinador | 20/05/2026 | NULL | 100 |
| Alberto | responsable | 20/05/2026 | NULL | 100 |
| David | asesor (main) | 01/06/2026 | **01/09/2026** | 100 |
| David | asesor (main) | **01/09/2026** | NULL | 50 |
| Juan | asesor | **01/09/2026** | NULL | 50 |

Tramos consecutivos para David (`dateTo` del primero = `dateFrom` del segundo = `01/09/2026`): su antigüedad **no se reinicia** — `inClientSince = 01/06/2026`.

### 7.5. Insert entre dos fotos — governing model en acción (registrado 23/06/2026 con efectividad 01/08/2026, foto previa en 01/09/2026)

Estado antes (resultante de §7.4):
- Perico — coordinador — 20/05/2026 → NULL — 100
- Alberto — responsable — 20/05/2026 → NULL — 100
- David — asesor (main) — 01/06/2026 → 01/09/2026 — 100
- David — asesor (main) — 01/09/2026 → NULL — 50
- Juan — asesor — 01/09/2026 → NULL — 50

Operación: desde agosto, David al 75% y Juan al 25%. `D = 01/08/2026`. Aplicando el governing model (FR-006-bis): el siguiente snapshot del departamento está en `N = 01/09/2026` (department-wide — el snapshot de septiembre ya existe). Los nuevos tramos van desde `01/08/2026` hasta `01/09/2026` (half-open).

| empleado | rol | dateFrom | dateTo | % |
|---|---|---|---|---|
| Perico | coordinador | 20/05/2026 | NULL | 100 |
| Alberto | responsable | 20/05/2026 | NULL | 100 |
| David | asesor (main) | 01/06/2026 | **01/08/2026** | 100 |
| David | asesor (main) | **01/08/2026** | **01/09/2026** | 75 |
| David | asesor (main) | 01/09/2026 | NULL | 50 |
| Juan | asesor | **01/08/2026** | **01/09/2026** | 25 |
| Juan | asesor | 01/09/2026 | NULL | 50 |

David tiene tres tramos consecutivos sin hueco (`[01/06, 01/08)` al 100%, `[01/08, 01/09)` al 75%, `[01/09, ∞)` al 50%). Juan tiene dos: `[01/08, 01/09)` al 25%, `[01/09, ∞)` al 50%. Cobertura `at=2026-08-15` = 75 + 25 = 100 ✓. Cobertura `at=2026-09-15` = 50 + 50 = 100 ✓.

### 7.6. Múltiples cambios en el mes en curso (FR-007 — el último gana)

Hoy es 15/06/2026. El responsable hace **dos cambios** consecutivos durante junio:

1. **05/06/2026**: reemplaza Alfonso por David (igual que §7.2). Se crea David con `dateFrom=01/06/2026`.
2. **20/06/2026**: vuelve a meter a Alfonso al 50% + Sara al 50%. El backend detecta que el tramo de David tiene `dateFrom = F = 01/06/2026` (tramo provisional, ver FR-002) y lo **borra físicamente** (`DELETE`) — David desaparece como si nunca hubiera entrado. El log registra `action='voided'` antes del borrado.

Estado final tras los dos cambios, leyendo `at=today (15/06/2026)`:

| empleado | rol | dateFrom | dateTo | % |
|---|---|---|---|---|
| Perico | coordinador | 20/05/2026 | NULL | 100 |
| Alberto | responsable | 20/05/2026 | NULL | 100 |
| Alfonso | asesor (main) | 20/05/2026 | **01/06/2026** | 100 |
| Alfonso | asesor (main) | **01/06/2026** | NULL | 50 |
| Sara | asesor | **01/06/2026** | NULL | 50 |

Alfonso queda con dos tramos: el viejo cierre con `dateTo=01/06/2026` (half-open, creado por la primera operación, preservado porque cerró un tramo de mes anterior) y un nuevo tramo de junio al 50%. La auditoría de US-05 capturaría las dos operaciones; la BD solo refleja la última intención.

---

## 8. Fuera de scope

- Reasignación manual de tareas desde la UI de equipo. Las tareas las gestiona `obligations-api` automáticamente vía AMQP (FR-016).
- Validación de continuidad (impedir huecos entre tramos consecutivos del mismo `(client, department, role)`). El sistema no exige que el % "cuadre" entre cambios sucesivos en distintas fechas — la cobertura se valida solo a la fecha actual.
- Soft-delete o restauración de equipos completos (`ClientTeam.endDate IS NOT NULL`). Cierre de equipo enteros se trata en US posterior.
- Migración de datos legacy de `client_assignment` a `client_team_assignment`. No hay migración: las asignaciones de los clientes ya existentes se vuelven a meter manualmente desde la UI nueva cuando un responsable abra la ficha por primera vez.
- Sincronización con Jira Assets más allá del consumo AMQP por `jira-adapter`. Política de sync pendiente con team lead.
- Edición de filas del log de cambios (`client_team_assignment_change`). El log es estrictamente read-only en la API; las correcciones manuales (si surgieran) se harían vía script de mantenimiento con justificación documentada.

---

## 9. Open Questions

- **OQ-001** — Granularidad temporal de obligations: ¿obligations consume el evento y reasigna tareas por `dueDate >= effectiveDate` o por algún otro criterio? Confirmar con team lead de obligations antes de cerrar contrato AMQP.
- **OQ-002** — Cuando la cobertura de asesores se queda en 100% pero el asesor main sale sin sustituto (queda 0 primary activos), ¿el equipo pasa a `incomplete` aunque la cobertura siga al 100%? *(propuesta: sí — FR-011 lo exige; reflejar en FR-015.)*
- **OQ-003** — ~~Shape final de `ClientTeamAssignmentChange`~~. **Cerrada 2026-06-04**: columnas explícitas before/after por campo (`employee_id_*`, `role_*`, `percentage_*`, `is_main_*`, `date_from_*`, `date_to_*`), audit propio (`created_at`, `created_by`, `updated_at`, `updated_by`), action enum con `voided` para FR-007. Sin JSON, sin denormalización de `department`/`client_id`. Ver §4.
- **OQ-004** — Si dos asignaciones del mismo empleado+rol+cliente entran activas a la vez (caso accidental que FR-013 no protege), ¿el cálculo de antigüedad las trata como continuas o como cadena rota? *(propuesta: las trata como continuas; los `dateFrom` se ordenan y la cadena no se rompe.)*
- **OQ-005** — Routing key exacta del evento de onboarding (FR-020). Hoy hipotetizamos `client-onboarding-assignment`. Confirmar con el producer (cliente / portal / sistema externo) antes de cerrar contrato del subscriber.
- **OQ-006** — Comportamiento del DELETE de FR-007 cuando el tramo machacado ya tenía un evento AMQP `opened` publicado y consumido aguas abajo. Opciones: (a) publicar un evento de "revocación" inverso, (b) confiar en que el evento `opened` posterior con el nuevo estado prevalezca aunque haya inconsistencia temporal, (c) consolidar en una transacción AMQP. Decidir antes de implementar US1.

---

## 10. Glosario

- **Asignación** (`ClientTeamAssignment`): tramo temporal de una persona en un rol dentro de un cliente+departamento.
- **Cobertura** (antes "bucket"): suma de `percentage` de las asignaciones activas de un rol dentro de `(client, department)`. Hay dos coberturas independientes: asesores y técnicos.
- **Equipo vigente a fecha**: proyección de las asignaciones cuyos `dateFrom <= fecha AND (dateTo IS NULL OR dateTo > fecha)` (half-open — un tramo cierra exactamente en su `dateTo`, no incluye ese día).
- **Reemplazo**: operación atómica close-old + open-new con el mismo punto de corte `D` (half-open: `dateTo` del saliente = `dateFrom` del entrante = `D`).
- **Normalización de fecha**: redondeo automático de `effectiveDate` a `D = primer día del mes pedido`. El tramo saliente cierra con `dateTo = D` (half-open — no "último día del mes anterior"). Aplica a todo el flujo de API normal; **no** aplica al subscriber de onboarding.
- **Rewrite frontier `F`**: primer día del mes en curso. Tramos con `dateFrom < F` son inmutables (solo se cierran con `dateTo = D`). Tramos con `dateFrom ≥ F` son provisionales (se borran físicamente cuando son superseded).
- **Onboarding**: subscriber AMQP (routing key `client-onboarding-assignment`) que materializa el alta inicial del equipo con fechas tal cual. Único camino para tramos con `dateFrom` no normalizado.
- **`inClientSince`**: campo derivado server-side. Fecha de entrada continua más antigua del empleado en el cliente. Renombrado desde `tenureSince` en la v2.
- **Equipo completo**: cumple las cinco condiciones de FR-015. En cualquier otro caso, `incomplete`.
- **Machacar** (FR-007): un tramo provisional (`dateFrom ≥ F`) que es reemplazado por otra operación dentro del mismo mes. Si el miembro sigue con otros atributos, se actualiza in-place; si ya no debe estar, se **borra físicamente** (`DELETE`) — el log registra `action='voided'` antes del borrado.
- **Log de cambios** (US-05): tabla `client_team_assignment_change` que registra cada mutación sobre `client_team_assignment` con before/after, autor y momento. Inmutable salvo corrección documentada.

---

## 11. Artefactos relacionados

- `er-diagram.md` — modelo ER autoritativo (consolidado 2026-06-04). Refleja las 3 tablas: `client_team`, `client_team_assignment`, `client_team_assignment_change`.
- `decisions.md` — ADRs heredados. ADR-0017 (successor required on causes_baja close) queda **superseded** por esta spec. ADR-0012, ADR-0010, ADR-0009, ADR-0015 siguen vigentes. OQ-003 cerrada en esta v2.
- `_archive/` — versión anterior de la spec y derivados, congelada para trazabilidad.
- `designs/` — frames de UI; revisar contra esta spec para detectar gaps (la lista de gaps de `designs/INDEX.md` puede tener entradas obsoletas).
