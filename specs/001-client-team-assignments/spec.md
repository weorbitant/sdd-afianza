# Feature Specification: Asignaciones Múltiples en Ficha de Cliente

**Feature Branch**: `001-client-team-assignments`

**Epic**: [DEVPT-518](https://afianza.atlassian.net/browse/DEVPT-518) — PGI - Asignaciones con porcentajes en Fiscal y Laboral

**Created**: 2026-05-25

**Updated**: 2026-05-26

**Status**: Draft

**Input**: Asignaciones múltiples — equipos por cliente con distribución de carga porcentual, histórico, y reasignación de tareas.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Crear y gestionar el equipo de un cliente (Priority: P1)

Un responsable accede a la ficha de un cliente y constituye su equipo: asigna un coordinador (opcional),
uno o más asesores y cero o más técnicos. Cada miembro entra con una fecha de inicio y un porcentaje de
carga (por defecto 100%). El sistema valida que los asesores sumen 100% y los técnicos sumen 100% dentro
del departamento antes de guardar.

**Why this priority**: Es el bloque fundacional. Sin poder crear equipos no hay ninguna otra funcionalidad
posible. Además, el día a día de los responsables depende directamente de poder ver y editar quién está
asignado a cada cliente.

**Independent Test**: Un responsable puede abrir la ficha de un cliente sin equipo, crear el equipo
añadiendo al menos un asesor, guardar y ver el equipo activo reflejado en la UI — todo ello sin tocar
ninguna otra funcionalidad.

**Acceptance Scenarios**:

1. **Given** un cliente sin equipo asignado,
   **When** el responsable añade un asesor con porcentaje 100% y guarda,
   **Then** el equipo queda activo y visible en la ficha del cliente.

2. **Given** un equipo con un asesor al 60% y un técnico al 40% (total = 100%),
   **When** el responsable intenta cambiar el técnico al 50% (total quedaría 110%),
   **Then** al confirmar el equipo el sistema rechaza el commit con el mensaje "Los miembros del equipo deben sumar 100%".

3. **Given** un equipo ya existente,
   **When** un usuario sin permiso `CLIENT_ASSIGNMENT_EDIT` (asesor, técnico u otro perfil de solo lectura) accede a la ficha,
   **Then** puede ver el equipo pero no puede editar ningún miembro (botones de edición y commit ocultos en frontend; endpoints de escritura devuelven 403 en backend).

4. **Given** que un cliente ya tiene un equipo activo en el Departamento A,
   **When** un responsable intenta crear un segundo equipo activo para ese mismo cliente en el Departamento A,
   **Then** el sistema rechaza la operación con el mensaje "Ya existe un equipo activo para este cliente en este departamento".

---

### User Story 2 — Distribución de carga por porcentaje (Priority: P2)

El responsable o coordinador puede ajustar el porcentaje de carga de cada miembro del equipo
(asesores y técnicos). El sistema valida en tiempo real que la suma de **todos los miembros**
(excluyendo responsable y coordinador) dentro del cliente+departamento sea exactamente 100%
antes de permitir confirmar el equipo.

**Why this priority**: La distribución de carga es la razón de negocio principal de la feature:
rentabilidad y visibilidad de quién absorbe qué parte del cliente.

**Independent Test**: Puede verificarse únicamente modificando porcentajes en un equipo existente y
comprobando que el sistema acepta o rechaza según la regla del 100%.

**Acceptance Scenarios**:

1. **Given** un equipo con un solo asesor al 100%,
   **When** el responsable añade un segundo asesor al 40% sin ajustar el primero,
   **Then** el sistema muestra advertencia "La suma del equipo es 140%: ajusta antes de confirmar".

2. **Given** un equipo con un asesor al 60% y un técnico al 40% (total = 100%),
   **When** el responsable cambia los porcentajes a 50% y 50% y confirma,
   **Then** el cambio se persiste correctamente.

3. **Given** un equipo con un asesor al 80%,
   **When** se añade un técnico al 10% (total = 90%),
   **Then** el sistema rechaza el commit porque el equipo no llega al 100%.

---

### User Story 3 — Histórico de cambios de asignación (Priority: P3)

Existe una vista de histórico en la ficha de cliente que muestra todos los cambios de asignación:
quién entró, quién salió, qué porcentaje tenía y en qué período estuvo activo. La vista es de solo
lectura y accesible para todos los perfiles con acceso a la ficha.

**Why this priority**: Imprescindible para auditoría, trazabilidad y resolución de disputas sobre
rentabilidad histórica. No bloquea la operativa diaria, pero es requisito de negocio no negociable.

**Independent Test**: Puede verificarse creando un equipo, modificando un porcentaje y comprobando
que el histórico registra ambos estados con sus fechas.

**Acceptance Scenarios**:

1. **Given** un equipo en el que se cambió el porcentaje de un asesor el día 10,
   **When** cualquier usuario accede al histórico,
   **Then** ve dos entradas: la original (con fecha inicio y fecha fin = día 9) y la nueva (con fecha
   inicio = día 10 y sin fecha fin).

2. **Given** un miembro que fue eliminado del equipo,
   **When** se consulta el histórico,
   **Then** aparece con fecha inicio y fecha fin y no aparece en la vista activa.

---

### User Story 4 — Cierre de equipo (Priority: P4)

El responsable puede cerrar el equipo de un cliente fijando una fecha de fin global que aplica a todos
sus miembros activos. El cierre no borra datos: queda registrado en el histórico. Las tareas y
obligaciones activas pendientes del equipo siguen la lógica definida en FR-010: el asesor que continúa
en la empresa conserva y cierra sus propias tareas; el asesor que causa baja tiene sus tareas reasignadas
automáticamente al sucesor. El responsable o coordinador puede además reasignar tareas concretas de
forma manual en cualquier momento.

**Why this priority**: Necesario para ciclos de vida completos (altas y bajas de clientes, cambios
organizativos), pero no bloquea el uso cotidiano de la feature.

**Independent Test**: Un responsable puede cerrar un equipo sin miembros con tareas pendientes y
comprobar que el equipo queda inactivo y registrado en el histórico.

**Acceptance Scenarios**:

1. **Given** un equipo activo sin tareas pendientes,
   **When** el responsable fija la fecha de cierre y confirma,
   **Then** todos los miembros reciben esa fecha como fecha fin y el equipo pasa a inactivo.

2. **Given** un asesor activo que sigue en la empresa y tiene tareas abiertas,
   **When** se define un nuevo asesor para el siguiente período,
   **Then** el asesor original conserva sus tareas abiertas y las cierra él mismo; las nuevas
   tareas/obligaciones del nuevo período se asignan al nuevo asesor.

3. **Given** un asesor que causa baja en la empresa y tiene tareas abiertas pendientes,
   **When** el responsable cierra su asignación con `causesBaja: true`,
   **Then** sus tareas abiertas se reasignan automáticamente al asesor sucesor definido para ese
   cliente en el siguiente período.

4. **Given** un responsable o coordinador que necesita anticipar o controlar una reasignación
   puntual de tareas (sin que el asesor haya causado baja),
   **When** utiliza la opción de reasignación manual,
   **Then** puede seleccionar tareas concretas y reasignarlas a otro miembro del equipo,
   quedando trazabilidad del cambio (quién tenía la tarea, a quién se transfirió y en qué fecha).

---

### Edge Cases

- ¿Qué ocurre si se intenta asignar a una persona que ya forma parte de un equipo activo en otro
  cliente del mismo departamento? → El sistema DEBE permitirlo (un asesor puede trabajar en varios
  clientes); la validación del 100% es por cliente+departamento, no por persona.
- ¿Qué ocurre si el responsable intenta dejar el equipo sin ningún asesor? → El sistema DEBE rechazarlo
  (requisito mínimo: 1..n asesores).
- ¿Puede un coordinador añadirse a sí mismo como asesor? → No: los roles son excluyentes dentro del
  mismo equipo.
- ¿Qué ocurre si se intenta crear un equipo con fecha de inicio en el pasado? → Se permite, pero se
  registra la fecha real de creación en el histórico (audit trail).
- ¿Puede el responsable crear un nuevo equipo el mismo día en que se cierra el anterior? → **Sí** — los períodos contiguos son válidos. El patrón estándar es: equipo anterior con `endDate` = último día del mes M, nuevo equipo con `startDate` = primer día del mes M+1. No existe restricción mínima de tiempo entre el cierre y la apertura de un nuevo equipo en el mismo cliente+departamento.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE permitir a un responsable crear un equipo para un cliente, designando
  opcionalmente un coordinador, al menos un asesor y cero o más técnicos. *(El flujo exacto de
  creación — desde la ficha del cliente o desde una pantalla de equipos — depende de la decisión
  Modelo A vs Modelo B; ver Key Entities.)*
- **FR-002**: Cada miembro del equipo DEBE tener una fecha de inicio, un porcentaje de carga
  (por defecto 100%) y opcionalmente una fecha de fin.
- **FR-003**: El sistema DEBE validar la suma de porcentajes **por bucket de rol** y **por departamento del cliente** (no por equipo individual). Hay **dos buckets independientes**: (i) **asesores** del departamento (suma de % de TODOS los asesores activos en TODOS los equipos del cliente en ese departamento = 100%), y (ii) **técnicos** del departamento (suma de % de TODOS los técnicos activos en TODOS los equipos del cliente en ese departamento = 100%). El responsable y el coordinador NO entran en la suma — son roles de gestión con 100% implícito. **Ejemplo**: 2 equipos Fiscal para un cliente, con 4 asesores totales (2 en Eq1, 2 en Eq2) cada uno al 25% → suma asesores Fiscal = 100% ✓. Lo mismo con técnicos por separado.

  La validación se evalúa tras cada operación de miembro (`POST/PATCH/DELETE /members`). El cliente+departamento está en estado `active` si y solo si: (a) la suma de asesores del departamento = 100% **y** (b) la suma de técnicos del departamento = 100% (con la salvedad: si NO hay técnicos en ningún equipo del departamento, el bucket de técnicos se considera "no aplicable" y no bloquea) **y** (c) existe exactamente un `TeamMember` con `role: asesor` e `isPrimary: true` por departamento. En caso contrario está en estado `incomplete`. El sistema persiste cada operación inmediatamente; muestra banner advisory cuando alguno de los dos buckets ≠ 100% (no bloquea el guardado del miembro). La publicación a Plataforma del Dato se suprime mientras esté en `incomplete`. La validación bloqueante de **composición mínima** (1 responsable + 1+ asesor por equipo) es independiente y SÍ deshabilita el botón Guardar (decisión PO 2026-06-01).
- **FR-004**: Solo los perfiles **responsable** y **coordinador** DEBEN poder crear, modificar o cerrar
  asignaciones. Los asesores y técnicos tienen acceso de solo lectura.
- **FR-005**: Un **cliente** PUEDE tener varios equipos activos por departamento (modelo multi-equipo confirmado por los diseños `08-multi-equipo/*` — ver Clarifications 2026-05-29). Los equipos NO tienen `name` persistido en BD (decisión PO 2026-06-01 — los nombres tipo `Libros`/`Cuota`/`Larsa`/`Costa` de los frames no representan regla de negocio). Para identificar visualmente en UI cuando hay varios equipos del mismo departamento se usa orden de creación (`Equipo 1`, `Equipo 2`) calculado en frontend, sin persistir. La unicidad activa se mantiene a nivel `(client_id, department, id)` — un cliente puede tener N equipos activos en el mismo departamento. La **validación del 100% se aplica por cliente+departamento** (suma de % asesores y técnicos por separado, agregada entre todos los equipos del departamento — ver FR-003 actualizado). La restricción es sobre el cliente, no sobre el empleado que ejerce de responsable.
- **FR-006**: Un responsable NO PUEDE pertenecer a más de un departamento.
  *(Restricción organizativa preexistente del modelo de empleados — gestionada en la creación
  del empleado, no validada en esta feature. Documentada aquí para que el equipo de asignaciones
  pueda asumirla con confianza al consultar el departamento del responsable.)*
- **FR-007**: El sistema DEBE mostrar el estado actual de las asignaciones en la ficha del cliente
  (quién está activo, con qué porcentaje y desde cuándo).
- **FR-008**: El sistema DEBE mantener un histórico inmutable de todos los cambios de asignación
  (altas, bajas, cambios de porcentaje), con fecha de inicio y fin de cada período.
- **FR-009**: El sistema DEBE permitir cerrar un equipo fijando una fecha de fin que se propaga a
  todos sus miembros activos. **UX del cierre** (alineada con el diseño `03-fecha-fin-equipo/*`):
  el responsable activa un checkbox **"Marcar fecha fin de equipo"** dentro del modal de añadir
  asignación e introduce la fecha. Al pulsar "Guardar" con el checkbox activo, el sistema DEBE
  mostrar un diálogo de confirmación obligatorio (*"Estás a punto de cerrar este equipo el
  DD/MM/YYYY. Esta acción no se puede deshacer. ¿Confirmas?"*) — solo al confirmar se aplica el
  cierre. El cierre es **permanente e irreversible**: no se puede reabrir ni modificar la fecha de
  fin una vez confirmada. Para reanudar la atención al cliente en el mismo departamento se DEBE
  crear un nuevo equipo (con un nombre distinto — ver FR-005) y una nueva fecha de inicio.
- **FR-010**: Las tareas existentes NUNCA se cancelan. La asignación de tareas sigue esta lógica:
  - Las **nuevas tareas y obligaciones** se asignan al miembro activo en el período correspondiente.
  - Si un asesor **sigue en la empresa** tras un cambio de asignación, conserva y cierra sus tareas
    abiertas; las nuevas tareas del siguiente período van al nuevo asignado.
  - Si un asesor **causa baja en la empresa**, el responsable o coordinador indica `causesBaja: true`
    al cerrar su asignación; el sistema reasigna **automáticamente** sus tareas abiertas al asesor
    sucesor definido para ese cliente. Si no hay sucesor definido, el sistema **bloquea el cierre**
    y exige designar un sucesor antes de confirmar (comportamiento provisional — pendiente de
    validación con PO).
  - El sistema DEBE ofrecer una **opción manual de reasignación** para que responsable o coordinador
    puedan transferir tareas concretas en cualquier momento (p. ej., anticipar una sustitución o
    gestionar casos especiales).
  - Toda reasignación DEBE quedar registrada con trazabilidad: quién tenía la tarea, a quién se
    transfirió y en qué fecha.
- **FR-011**: No puede existir ningún período sin cobertura (gap) para un cliente con equipo activo:
  el sistema DEBE rechazar cualquier cambio que deje al cliente sin al menos un asesor activo.
- **FR-012**: La granularidad de las fechas de asignación es **híbrida**: se almacena la fecha exacta
  (tipo `date`), pero el servicio valida que `dateFrom` sea siempre el primer día del mes y `dateTo`
  el último. Los porcentajes y la rentabilidad se calculan a granularidad mensual. Esta decisión no
  requiere cambio de esquema y permite mayor precisión en el histórico de auditoría.
  **UX**: la UI solo permite al responsable seleccionar **mes** (no día concreto); el servicio
  asume día 1 al alta y último día del mes al cierre (ver Clarifications 2026-05-29).
- **FR-013**: El sistema DEBE migrar automáticamente todas las asignaciones 1-a-1 existentes al modelo
  de porcentajes, asignando un 100% a cada miembro único en su rol y departamento. La migración DEBE
  ser idempotente, no destructiva y ejecutarse en una única pasada sin afectar a los registros de
  histórico existentes.
- **FR-014**: El sistema DEBE sincronizar los datos de asignación (empleado, rol, porcentaje, período)
  con la **Plataforma del Dato** publicando un **evento en el bus de mensajería interno** (RabbitMQ,
  exchange `internal`) **únicamente cuando el equipo esté en estado `active`** (FR-003). Se publica
  evento en: (a) la transición `incomplete → active`, (b) cualquier cambio de miembro que mantenga
  el equipo en `active`, y (c) la transición `active → closed` (FR-009). Cambios en equipos
  `incomplete` NO disparan evento. La Plataforma del Dato consume el evento y actualiza sus informes
  de rentabilidad y cuadros de mando. La propagación DEBE completarse en menos de 5 minutos desde el
  cambio que produjo el evento.
- **FR-015**: En el **MVP**, únicamente la **ficha de cliente** DEBE actualizarse para reflejar la lista
  completa de miembros del equipo activo con sus porcentajes. Las pantallas "Mis Clientes", buscador
  global del PGI y los informes internos quedan fuera del alcance de esta iteración y se abordarán
  en una fase posterior. El seguimiento por asesor/técnico en Plataforma del Dato (informes externos)
  queda cubierto por FR-014 vía sincronización.
- **FR-016**: Un empleado MUST pertenecer como máximo a **un único equipo activo por cliente** (decisión PO 2026-06-01: opción B). Esto significa: (a) no más de un rol dentro del mismo equipo, y (b) **tampoco en dos equipos distintos del mismo cliente, ni siquiera en departamentos distintos**. Ej: Pedro no puede ser Asesor del equipo Fiscal y Asesor del equipo Laboral del mismo cliente X simultáneamente. Si una persona necesita cambiar de equipo o rol → cerrar la asignación actual con `dateTo` y abrir una nueva con `dateFrom`, sin solape activo. Esta regla aplica **por cliente**, no en absoluto: un asesor sí puede estar activo en equipos de varios clientes (eso es operativa normal).
- **FR-017**: El sistema MUST permitir crear o activar un `ClientTeam` para un cliente en un
  departamento **solo si** el cliente tiene al menos un `ProvidedService` activo cuya `family` mapee a
  ese departamento (mapping: `family=fiscal` → Fiscal, `family=laboral` → Laboral). La UI MUST ocultar
  el CTA `+ Añadir equipo` en los departamentos sin servicios contratados activos; el backend MUST
  rechazar la creación con error de validación (defensa en profundidad). Los equipos existentes en un
  departamento permanecen activos aunque luego se den de baja todos los servicios contratados de ese
  departamento — la regla bloquea **creación**, no invalida **existentes** (a confirmar con PO — ver
  OQ-008).
- **FR-018**: El mensaje AMQP `client-assignment` publicado por `pgi-service-pgi-api` (consumido por
  `pd-service-jira-adapter` y `pd-service-data-factory` — verificado en código) MUST ampliarse para
  incluir `teamId`, `teamName` y `percentage` además de los campos actuales (`clientId`, `employeeId`,
  `role`, `department`, `dateFrom`, `dateTo`). Los consumers deben actualizarse para deserializar y
  persistir los nuevos campos.
- **FR-019**: El modelo `ClientAssignment` en `pd-service-data-factory` (actualmente sin `team_id` ni
  `percentage`) MUST alinearse con el modelo de `pgi-service-pgi-api`: añadir columnas `team_id`
  (nullable FK lógica) y `percentage` (1–100). Migración inicial: `percentage=100` para todas las filas
  existentes y `team_id=NULL` hasta que se re-publiquen desde pgi-api.
- **FR-020**: El sync hacia Jira Assets ("Clientes" object type) realizado por `pd-service-jira-adapter`
  MUST mantener su contrato actual de "una asignación por rol y cliente" cuando hay multi-equipo,
  escribiendo solo la asignación del **equipo principal** del cliente y del **asesor principal**
  (`isPrimary=true`). Las asignaciones de otros equipos NO se reflejan en Jira Assets en esta
  iteración. *(Decisión de scope para no romper contrato existente; ampliable en futura épica.)*
- **FR-021**: El unique constraint actual de `pgi-service-pgi-api/client_assignment` `(client, employee, role, department, dateFrom)` se MANTIENE, pero **se añade adicionalmente** un partial unique sobre `(client_id, employee_id) WHERE dateTo IS NULL` para reforzar FR-016 a nivel BD: un mismo empleado no puede tener más de una asignación activa al mismo cliente (decisión PO 2026-06-01: una persona = un equipo por cliente, incluso entre departamentos). Cualquier intento de doble asignación activa por la misma persona en el mismo cliente queda bloqueado por la BD aunque la lógica del servicio falle.
- **FR-022**: Las operaciones de escritura sobre `ClientTeam` y `ClientAssignment` MUST aplicar control
  de concurrencia optimista basado en `updatedAt`. El cliente envía el `updatedAt` que tenía al cargar
  el equipo; si la BD tiene un `updatedAt` posterior, el backend rechaza con HTTP 409 y la UI muestra
  un aviso *"El equipo ha cambiado, recarga para ver el estado más reciente"* sin perder los datos
  introducidos.

### Key Entities

> ⚠️ Ver **OQ-005** en la sección Open Questions — la estructura interna de `Team` depende de una
> decisión pendiente de PO. El resto de entidades están definidas independientemente del modelo elegido.

- **Equipo** (`Team`): Agrupación de personas con un responsable, una fecha de inicio y opcionalmente
  una fecha de cierre. Lleva un **nombre obligatorio y único** dentro del par cliente+departamento
  (ver FR-005). Estado calculado: `incomplete` | `active` | `closed` (ver FR-003 y FR-009).
  *(Scope: ver decisión pendiente arriba.)*
- **Miembro del Equipo** (`TeamMember`): Persona que pertenece al equipo, con rol (responsable,
  coordinador, asesor, técnico), porcentaje de carga, fecha de inicio y fecha de fin opcional.
  Cuando `role = asesor`, el atributo booleano `isPrimary` indica si es el **asesor principal**
  del equipo (exactamente uno por equipo activo — ver FR-005 y Clarifications 2026-05-29).
- **Rol** (`Role`): Enum — responsable | coordinador | asesor | técnico. Excluyentes dentro del
  mismo equipo.
- **Período de Asignación** (`AssignmentPeriod`): Registro histórico de un miembro en un equipo para
  un intervalo de tiempo determinado. Inmutable una vez cerrado.
- **Departamento** (`Department`): Contexto organizativo dentro del cual se valida la regla del 100%.
  Un cliente puede tener equipos en más de un departamento.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un responsable puede constituir el equipo completo de un cliente nuevo (añadir miembros,
  asignar porcentajes y guardar) en menos de 3 minutos.
  *(Métrica de UX observable post-deploy — se mide con analytics/Hotjar sobre la sesión real, no
  requiere instrumentación específica en esta feature.)*
- **SC-002**: El sistema rechaza el 100% de los intentos de guardar con suma de porcentajes diferente
  a 100% (por rol y departamento), sin excepción.
- **SC-003**: Cualquier cambio de asignación queda registrado en el histórico en menos de 1 segundo
  desde el guardado, visible inmediatamente para todos los usuarios con acceso.
- **SC-004**: No existe ningún cliente con equipo activo que pueda quedarse sin cobertura de asesor
  como resultado de una operación permitida por el sistema.
- **SC-005**: Los responsables y coordinadores pueden consultar el histórico completo de asignaciones
  de cualquier cliente al que tengan acceso, sin limitación temporal.
- **SC-006**: El 0% de las tareas existentes se pierde o cancela como resultado de un cambio de
  asignación o cierre de equipo.

---

## Assumptions

- Existe ya un concepto de **Departamento** en el sistema que se reutiliza (no es un nuevo concepto
  a crear desde cero).
- Existe ya un sistema de **Tareas** y un sistema de **Obligaciones** al que esta feature debe
  conectarse; los detalles de esa integración se detallarán en la fase de planificación técnica.
- Los perfiles de usuario (responsable, coordinador, asesor, técnico) ya están definidos en el
  sistema de autenticación / control de acceso existente.
- Un mismo empleado puede ser asesor en varios clientes simultáneamente (la restricción del 100%
  es por cliente+departamento, no por persona).
- La UI de la ficha de cliente ya existe y esta feature añade una nueva sección/tab; no implica
  rediseño de la ficha completa.
- La rentabilidad se calcula a partir de los porcentajes de asignación; el motor de cálculo de
  rentabilidad se actualiza como parte de esta feature o en una fase posterior (a definir en planning).
- El histórico es de solo lectura y no requiere exportación en esta fase (MVP).

## Designs

Frames exportados desde Figma — Portal Asesor / Ficha de cliente:

![Ficha de cliente 01](designs/ficha-cliente-01.png)
![Ficha de cliente 02](designs/ficha-cliente-02.png)
![Ficha de cliente 03](designs/ficha-cliente-03.png)
![Ficha de cliente 04](designs/ficha-cliente-04.png)
![Ficha de cliente 05](designs/ficha-cliente-05.png)
![Ficha de cliente 06](designs/ficha-cliente-06.png)
![Ficha de cliente 07](designs/ficha-cliente-07.png)
![Ficha de cliente 08](designs/ficha-cliente-08.png)
![Ficha de cliente 09](designs/ficha-cliente-09.png)
![Ficha de cliente 10](designs/ficha-cliente-10.png)
![Ficha de cliente 11](designs/ficha-cliente-11.png)
![Ficha de cliente 12](designs/ficha-cliente-12.png)
![Ficha de cliente 13](designs/ficha-cliente-13.png)
![Ficha de cliente 14](designs/ficha-cliente-14.png)
![Ficha de cliente 15](designs/ficha-cliente-15.png)
![Ficha de cliente 16](designs/ficha-cliente-16.png)
![Ficha de cliente 17](designs/ficha-cliente-17.png)
![Ficha de cliente 18](designs/ficha-cliente-18.png)
![Ficha de cliente 19](designs/ficha-cliente-19.png)

> Fuente: [Portal Asesor - Mis clientes](https://www.figma.com/design/ra1egztv3K3yBTrWbHVacy) · Página: Mis clientes · 2026-05-25

---

## Decisiones de la sesión PO

Tabla única de preguntas para la PO y decisiones tomadas. Reemplaza los antiguos bloques "Open Questions" + "Nuevas — Challenge funcional" + ficheros `po-*.md` (eliminados).

Para evidencia detallada de cada decisión y discusión histórica ver `## Clarifications` más abajo, y `challenge-report.md` para los hallazgos del challenge funcional + técnico.

### ✅ Resueltas (13)

| # | Tema | Decisión PO |
|---|---|---|
| 1 | Suma 100% del equipo | **Dos buckets** (asesores 100% + técnicos 100% por separado), agregando entre todos los equipos del **departamento** del cliente (no por equipo individual). PO 2026-06-01. |
| 2 | Persistencia de miembros | Persistencia inmediata por miembro (sin borrador+commit). Toast tras cada `POST /members`. PO 2026-05-29. |
| 3 | Asesor principal del equipo | Obligatorio, único por (cliente, departamento). Atributo `isPrimaryAdvisor` en `ClientAssignment`. PO 2026-05-29. |
| 4 | Modelo de equipo | Modelo A — el equipo es exclusivo del cliente, no se comparte. PO 2026-05-28. |
| 5 | Nombre del equipo | **Descartado de scope** — sin campo `name` en BD. UI muestra `Equipo 1/2` por orden de creación. PO 2026-06-01. |
| 6 | Papelera del modal de miembros | **No borra** — pone `dateTo`. Diálogo inline pregunta `causesBaja` y sucesor (si aplica). PO 2026-06-01. |
| 7 | Punto de entrada para crear equipo | **Solo desde ficha de cliente**. El CTA de *Mis tareas* era resto de diseño y se elimina. PO 2026-06-01. |
| 8 | Equipos en estado `incomplete` | Banner amarillo advisory, **sin bloqueo del guardado de miembros**. El bloqueo solo aplica a composición mínima (ver #12) y a "marcar como principal" / disparar tareas auto. PO 2026-06-01. |
| 9 | Bajas largas (médica, maternidad) | Sustitución estándar — cerrar la asignación del que se va + alta del sustituto. **NO se construye entidad "suplencia temporal"**. PO 2026-06-01. |
| 10 | Cambio de rol del empleado (técnico → asesor) | Cerrar el rol anterior con `dateTo` + abrir uno nuevo con `dateFrom`. Sin coexistencia. PO 2026-06-01. |
| 11 | Persona en multi-equipo | **No permitido** — una persona, un equipo por cliente, **ni siquiera entre departamentos** (opción B). Partial unique `(client_id, employee_id) WHERE date_to IS NULL`. PO 2026-06-01. |
| 12 | Validación bloqueante de composición mínima | Botón Guardar **deshabilitado** mientras falten roles obligatorios (1 responsable + 1+ asesor). PO 2026-06-01. |
| 13 | Edición simultánea (último editor pisa) | **Optimistic concurrency con columna `version` integer** (no `updatedAt`). Header `If-Match`, HTTP 409 al conflicto. Ver ADR-0010. Dev + ratificación PO 2026-06-01. |

### ⏳ Pendientes PO (6)

| # | Tema | Recomendación dev | Por qué pregunta |
|---|---|---|---|
| 14 | Baja de asesor sin sucesor designado | Bloquear el cierre hasta que se designe sucesor | Si lanzamos sin sucesor, las tareas pendientes quedan sin asignar y nadie las atiende |
| 15 | Plataforma del Dato no disponible al guardar | (sin propuesta dev — decisión negocio) | ¿Persistir y sync diferido, o bloquear el guardado hasta que vuelva el sistema? |
| 16 | Equipos huérfanos por baja del último servicio contratado del dept | Dejar activos + banner persistente *"sin servicios activos en este departamento"* | Si cierras auto, retiras control al responsable. Si dejas activo, distorsiona informes. |
| 17 | Visibilidad de porcentajes en histórico por perfil | Todos ven todo (asesores ven los % de los compañeros del cliente) | Hay sensibilidad — los % se traducen indirectamente en retribución |
| 18 | Baja repentina de empleado en Azure AD | Cerrar asignaciones automáticamente + alertar al responsable | Hoy el sistema solo cubre bajas voluntarias con `causesBaja:true`, no la propagación desde RR.HH. |
| 19 | Cambio de departamento del empleado (fiscal ↔ laboral) | Cerrar asignaciones del dept origen + designar sucesor antes de aplicar | Si se permite el cambio sin transición, asignaciones del dept origen quedan en estado inválido |

### ⏳ Pendiente Producto (1)

| # | Tema | Estado | Assumption MVP |
|---|---|---|---|
| 20 | Política de routing de tareas por rol (qué `ObligationCategory` ejecuta cada rol del equipo) | Producto no lo tiene definido aún | Todo al asesor principal del departamento. Cuando Producto defina mapping, se extiende `Obligation` con `roleResponsible` |

### ⏳ Decisión parcial — pendiente confirmación PO (1)

| # | Tema | Estado actual | Pendiente |
|---|---|---|---|
| 21 | Onboarding desde Jira en el nuevo modelo | MVP: `applyFromClientOnboarding` sigue creando filas con `team_id=NULL`. Test de regresión obligatorio | ¿Crear *"Equipo inicial"* auto por dept en el consumer (recomendado), o que la PO confirme dejarlo así indefinidamente? |


## Clarifications

### Session 2026-06-01 (tarde — sesión con PO, resultados)

> Decisiones tomadas en la sesión de refinamiento con PO el 2026-06-01.
> Pendientes 4 conflictos a confirmar — ver `po-followup-conflicts.md`.

- Q: ¿Crear equipo desde *Mis tareas* o solo desde *ficha de cliente*? → A: **Solo desde ficha de cliente**. El CTA *"Crear equipo"* de *Mis tareas* era resto de diseño y se elimina. Cierra D2.
- Q: ¿Qué hace la papelera junto a cada miembro? → A: **NO borra**. Pone `dateTo` para preservar histórico siempre. El detalle de UX (diálogo inline para `causesBaja` y sucesor) se aplica como FR-010 ya describía. Cierra D3 y OQ-007.
- Q: ¿Nombres de equipo (Libros, Cuota, Larsa…)? → A: **Ignorar** — no representan regla de negocio para esta feature. Pendiente confirmación: ¿campo `name` existe o no? Ver `po-followup-conflicts.md` punto 3. Cierra parcialmente D6 y OQ-006.
- Q: ¿Cambio de rol de un empleado (técnico → asesor)? → A: **Cerrar el rol anterior con `dateTo`** + **abrir uno nuevo con `dateFrom`**. Sin coexistencia inválida en el mismo periodo. Cierra D9.
- Q: ¿Onboarding desde Jira crea equipos automáticamente? → A: **Sí, mantener comportamiento actual** del onboarding. **Pendiente**: confirmar si las asignaciones del onboarding ahora deben crear un *Equipo inicial* con `team_id` o seguir creando con `team_id = NULL`. Ver `po-followup-conflicts.md`. Cierra parcialmente D10.
- Q: ¿Composición mínima del equipo? → A: **1 responsable obligatorio + 1+ asesores + 0-1 coordinador + 0-N técnicos**. Confirma FR-003 (ya estaba). UI muestra asterisco + validación visible + **botón guardar bloqueado** mientras no se cumpla la composición mínima.
- Q: ¿Se pueden crear equipos con fecha inicio futura? → A: **Sí**. Sin restricción de rango temporal.
- Q: ¿Una tarea puede quedar sin asignar si no hay miembro válido? → A: **No**. La tarea SIEMPRE se genera. Si no se puede asignar automáticamente, se escala. Documentar como nuevo AC en US4 / FR-010.
- Q: ¿Los porcentajes de dedicación se usan para repartir tareas? → A: **No**. Son solo para informes de rentabilidad / atribución de ingresos. Las tareas las recibe el asesor principal independientemente del %. Esto refuerza FR-029 (ya estaba alineado).
- Q: ¿La validación en la UI del PGI debe ser idéntica a la de Jira? → A: **Sí**. Una sola lógica de validación, aplicada en ambos lados.
- Q: ¿Asignaciones múltiples = mover carteras entre asesores masivamente? → A: Aclarada como funcionalidad de **reasignación masiva** (varios clientes a la vez, manteniendo porcentajes y con fecha efectiva). **Confirmar si está en scope de DEVPT-518 o es feature separada**.
- Q: ¿Persona en más de un rol/equipo simultáneo? → A: **No permitido** (confirmación PO 2026-06-01 post-meeting): opción B — una persona puede pertenecer como máximo a UN equipo de UN cliente en un momento dado, **incluso si los equipos son de departamentos distintos**. Ej: Pedro no puede ser Asesor de Fiscal del cliente X y a la vez Técnico de Laboral del mismo cliente X. Para cambiar de equipo/rol → cerrar el actual con `dateTo` y abrir uno nuevo con `dateFrom`. Esto refuerza FR-016 y **cambia FR-021** (el unique constraint que íbamos a relajar para multi-equipo ya no aplica — al contrario, hay que añadir una restricción nueva por `(client_id, employee_id) WHERE dateTo IS NULL`).
- Q (post-sesión) · Modelo de suma 100% → A: **Dos buckets independientes (asesores 100% + técnicos 100%) y suma POR DEPARTAMENTO del cliente, NO por equipo individual**. Confirmado por la PO con el frame `08-multi-equipo/01-multi-equipo-fiscal-larsa-costa.png`: 2 equipos Fiscal con 3 asesores totales distribuidos entre ambos, todos sumando 100% en conjunto. Si hay 4 asesores en 2 equipos Fiscal, cada uno al 25% → 100%. Lo mismo con técnicos por separado. **Esto invalida ADR-0008 (single bucket por equipo)** — la decisión debe registrarse como nuevo ADR que supersede al anterior. **Cambia FR-003** (aplicado en esta misma iteración).
- Q (post-sesión) · Bajas largas → A: **Se gestionan como cualquier baja**: fecha fin a la asignación. Si el equipo está al 100%, hay que SUSTITUIR (cerrar la asignación del que se va + abrir nueva para el sustituto, manteniendo la suma 100% por departamento). No hay flujo especial de "suplencia temporal" en esta iteración. Cierra D5.
- Q (post-sesión) · Nombre del equipo → A: **Descartado de scope**. La PO confirmó que los nombres `Libros`/`Cuota`/`Larsa`/`Costa` de los frames no representan regla de negocio. **Acción**: documentar como assumption que el equipo NO tiene campo `name` obligatorio en MVP. Si en algún momento se necesita identificar visualmente equipos del mismo departamento, se hará por orden de creación (`Equipo 1`, `Equipo 2`) sin persistirlo en BD. Cierra D6 y OQ-006.

**Pendientes después de la sesión** (no bloquean diseño técnico del MVP si asumimos defaults):
- D5 (qué rol del equipo hace cada tarea) — Producto no lo tiene definido. Assumption MVP: todo va al asesor principal.
- TaxDown / subcontratados — más adelante.
- Vista de anomalías clientes con servicio sin equipo — backlog futuro.
- Visibilidad de % en histórico por perfil (D7) — pendiente para próxima sesión PO.
- Edición simultánea (D13 / FR-022) — confirmar con PO la propuesta dev.
- Plataforma del Dato no disponible al guardar — pendiente sesión técnica con Paula.

---

### Session 2026-06-01 (cross-service discovery + nuevas restricciones)

- Q: Verificación en código del polyrepo — ¿qué rutas de creación/propagación de asignaciones existen además de la UI del PGI? → A (parcial — corregida 2026-06-01 tarde, ver D10): **UI del PGI es UNA de las rutas de escritura, pero NO la única**. Existen también: (i) ruta de **entrada AMQP `client_onboarding_persisted`** consumida por `pgi-service-pgi-api/client-subscriber` que llama a `ClientAssignmentsService.applyFromClientOnboarding(...)` y crea filas en `client_assignment` automáticamente cuando se da de alta un cliente desde Jira (actor = `system:onboarding`) — flujo en producción desde mayo 2026, fix de duplicados ya implementado (DEVPT-539); (ii) pipelines AMQP de **SALIDA** que deben actualizarse — `pd-service-jira-adapter` (sync a Jira Assets) y `pd-service-data-factory` (informes). Modelos `ClientAssignment` desalineados en data-factory (sin `team_id`/`percentage`). **Nuevos FR-018..FR-021** documentan los cambios de salida; **la integración con la ruta de onboarding queda como D10 pendiente PO**.
- Q: Restricción por servicios contratados — ¿se permite crear un equipo en un departamento donde el cliente no tiene `ProvidedService` activo? → A: **No** — la creación se bloquea en frontend (CTA oculto) y backend (validación). Apunte introducido en clarify 2026-06-01. Verificado en código: existen `ProvidedService` con `family: ServiceFamily` y `category: ServiceCategory`. **Nuevo FR-017**. Pregunta abierta sobre equipos huérpanos al darse de baja servicios → **OQ-008**.
- Q: Un mismo empleado puede ocupar varios roles en un mismo equipo (ej. Coordinador y Asesor a la vez)? → A: **No** — un empleado, un único rol por equipo. **Nuevo FR-016**. (El mismo empleado SÍ puede estar en equipos de departamentos distintos del mismo cliente — eso está permitido por el unique constraint actual.)
- Q: Política de concurrencia cuando dos editores tocan el mismo equipo a la vez? → A: **Optimistic concurrency con `updatedAt`**. HTTP 409 al conflicto + aviso UI. **Nuevo FR-022**.
- Q: Nombre del equipo (`name` de FR-005) — ¿texto libre, catálogo, o derivado de `ProvidedService.category` que el equipo cubre? → A: **Pendiente de PO** — los nombres `Libros`/`Cuota` de los frames coinciden literalmente con valores reales de `ServiceCategory`, sugiriendo enlace `ClientTeam ↔ ProvidedService`. **Nuevo OQ-006** para llevar a PO.
- Q: Comportamiento del icono papelera del modal — ¿diálogo inline o pantalla aparte para causa baja? → A: **Pendiente de PO** — las reglas de negocio ya están en FR-010, falta sólo la superficie UX. **Nuevo OQ-007** para llevar a PO.
- Conflict flag pendiente: la decisión "dos cubos separados (asesores 100% + técnicos 100%)" tomada en una iteración paralela del 2026-06-01 mañana **queda invalidada** — la decisión madura del 2026-05-28 (un solo cubo, ratificada en ADR-0008) prevalece. Spec actual mantiene **single bucket**.

### Session 2026-05-29 (US1 — Design Conformance)

- Q: ¿Permite la spec varios equipos activos por cliente+departamento (los frames `08-multi-equipo/*` muestran 'Equipo Larsa' y 'Equipo Costa' coexistiendo en Fiscal)? → A: **Sí — multi-equipo permitido**. Los diseños son fuente de verdad: FR-005 cambia de "1 equipo activo por cliente+departamento" a "N equipos activos por cliente+departamento, identificados por nombre". La validación del 100% pasa a aplicarse **por equipo**. La unicidad pasa a ser `(client, department, name)` cuando `endDate IS NULL`. Implica que el campo `name` del equipo es obligatorio (resuelto en la pregunta siguiente).
- Q: ¿Existe el concepto de "asesor principal" del equipo (frame `02-anadir-asesor/01-modal-checkbox-asesor-principal.png` muestra checkbox 'Marcar como asesor principal' + badge `Principal`)? → A: **Sí — obligatorio, exactamente uno por equipo**. `TeamMember` incorpora el atributo booleano `isPrimary` (solo aplicable cuando `role = asesor`). En cada equipo activo debe existir **exactamente un** `TeamMember` con `role: asesor` y `isPrimary: true`. El sistema valida esta regla en la transición del equipo a estado `active` (ver pregunta siguiente). El asesor principal es el **destinatario por defecto de tareas automáticas** y el **sucesor por defecto** cuando otros asesores del equipo causan baja. **Resuelve OQ-002.**
- Q: ¿Persistencia inmediata por miembro (toast tras cada add) o borrador+commit explícito? (frames `05-vista-equipo-incompleto/*` muestran toast inmediato y banner advisory; no hay botón "Confirmar equipo") → A: **Persistencia inmediata con estado del equipo `incomplete` / `active`**. Cada `POST/PATCH/DELETE /members` persiste al instante y devuelve toast. El equipo permanece en estado `incomplete` mientras la suma de asesores + técnicos sea distinta de 100% **o** mientras no exista un asesor con `isPrimary: true`. Transiciona automáticamente a `active` cuando ambas condiciones se cumplen, y a `incomplete` si vuelven a romperse por una edición posterior. **Solo se publican eventos a Plataforma del Dato (FR-014) cuando el equipo está en estado `active`**, incluyendo la propia transición `incomplete → active`. El endpoint `POST /commit` y el modelo borrador+commit declarados en Clarifications 2026-05-28 **quedan invalidados** — ADR-0007 debe revisarse en consecuencia.
- Q: ¿Cómo se cierra un equipo — acción separada en la ficha o checkbox dentro del modal de añadir asignación? (frame `03-fecha-fin-equipo/01-modal-checkbox-fecha-fin-equipo.png` muestra checkbox "Marcar fecha fin de equipo" incrustado en el modal) → A: **Checkbox en el modal (como el diseño) + modal de confirmación obligatorio al guardar si está marcado**. Al pulsar "Guardar" con el checkbox activo, el sistema DEBE mostrar un diálogo: *"Estás a punto de cerrar este equipo el DD/MM/YYYY. Esta acción no se puede deshacer. ¿Confirmas?"* con opciones [Cancelar] [Sí, cerrar el equipo]. Solo al confirmar se aplica el cierre. Mantiene la irreversibilidad declarada en FR-009. **Resuelve B6** (corrección de cierre por error): no se construye mecanismo de reversión, la doble confirmación es el control suficiente.
- Q: ¿Granularidad del selector de fecha en la UI — mes o día? (frame `01-crear-equipo/06-modal-fecha-inicio-calendario.png` muestra calendario que solo permite seleccionar mes) → A: **UI solo permite seleccionar mes**. El servicio fija `startDate` al día 1 del mes seleccionado y `endDate` al último día del mes seleccionado. Alineado con FR-012 (granularidad híbrida ya existente) y con la lógica mensual de rentabilidad. Si en el futuro algún caso exige el día exacto, se amplía el modal de forma aditiva sin cambio de esquema.

### Session 2026-05-28 (US1)

- Q: Rol `responsable` en el equipo — ¿cómo se materializa al crear un equipo? → A: **`ClientAssignment` con `role: responsable`** (1 fila por equipo, % implícito 100%, no entra en la validación de suma). Aparece en la lista de miembros y deja huella histórica de los cambios de responsable.
- Q: ¿Cuándo se valida la suma del 100% por rol? → A: **Modelo borrador + commit**. Los endpoints `POST/PATCH/DELETE /members` no validan la suma — permiten construir el equipo incrementalmente. Existe un endpoint explícito `POST /commit` que valida y confirma el equipo (publica el evento RabbitMQ y marca los miembros como activos). `POST /validate` queda como herramienta informativa para el frontend.
- Q: ¿Cómo se gestionan las asignaciones legacy con `team_id = NULL`? → A: **Migración masiva al desplegar (FR-013 dentro de US1)**. La migración recorre todos los `client + department` con asignaciones activas, crea un `ClientTeam` por cada uno con `startDate` = mínimo `dateFrom` de sus miembros y `endDate = NULL`, y asocia las asignaciones existentes (`team_id` = id del equipo creado, `percentage = 100`). La migración es idempotente y no destructiva. Cuando un responsable abra cualquier ficha post-deploy ya verá su equipo activo sin intervención manual.
- Q: Modelo de validación del 100% — ¿dos cubos (asesores 100% + técnicos 100%) o un solo cubo del equipo? → A: **Un solo cubo**. La suma del equipo (todos los asesores + todos los técnicos) debe ser exactamente 100%. El **responsable** y el **coordinador** NO entran en la suma (son roles de gestión con 100% implícito). Ejemplo válido: 1 asesor 60% + 1 asesor 20% + 1 técnico 20% = 100%. Esto simplifica FR-003, los AC de US1/US2 y el indicador del frontend (un solo total, no uno por rol).

### Session 2026-05-26

- Q: FR-015 — ¿Qué pantallas/módulos reflejan el equipo múltiple en el MVP? → A: **Solo la ficha de cliente.** "Mis Clientes", buscador PGI e informes internos quedan para una iteración posterior. Informes externos vía Plataforma del Dato cubiertos por FR-014.
- Q: FR-014 — ¿Mecanismo de sincronización con Plataforma del Dato? → A: **Evento RabbitMQ (exchange `internal`)** publicado al confirmar cada cambio. Propagación garantizada en <5 minutos.
- Q: FR-010 / CHK025 — ¿Qué ocurre al cerrar asignación con `causesBaja: true` sin sucesor? → A: **Bloquear el cierre** hasta designar sucesor *(provisional — pendiente de confirmar con PO)*.
- Q: OQ-005 — Modelo de equipos (Modelo A vs B) → **Modelo A para MVP**: los equipos se crean directamente desde la ficha de cada cliente y son exclusivos de ese cliente. Si se necesita la misma composición en otro cliente, se crea un equipo nuevo desde su ficha. **Futuro posible (Modelo B)**: tanto la **creación del equipo** como la **asignación del equipo a uno o varios clientes** se gestionarían en una pantalla propia fuera de la ficha del cliente; la ficha del cliente quedaría como vista de consulta del equipo asignado, no como punto de gestión. El modelo de datos actual (Modelo A) no bloquea esta evolución: `ClientTeam` ya es una entidad de primera clase con FK a `client`; en el futuro bastaría con introducir una tabla pivote `team_assignment` (team_id ↔ client_id) sin alterar las columnas existentes — migración aditiva.

### Session 2026-05-25

- Q: FR-005 — ¿La unicidad del equipo activo aplica al cliente o al empleado responsable? → A: Al **cliente** — un cliente no puede tener más de un equipo activo por departamento; la unicidad es `client_id + department WHERE end_date IS NULL`.
- Q: FR-012 — ¿Qué granularidad de fechas se usa para los períodos de asignación? → A: **Híbrida** — fecha exacta en base de datos, convención de primer/último día de mes aplicada en el servicio; cálculo de porcentajes y rentabilidad a granularidad mensual.
- Q: FR-009 — ¿El cierre de un equipo es reversible? → A: **No — permanente**. No se puede reabrir ni modificar `endDate` una vez confirmado. Para continuar se crea un nuevo equipo.
- Q: FR-010 / CHK025 — ¿Qué ocurre si no hay sucesor al dar de baja a un asesor? → A: **Diferido — pendiente de decisión con PO**.
- Q: CHK012 — ¿Se puede crear un nuevo equipo el mismo día del cierre del anterior? → A: **Sí** — períodos contiguos son válidos (`endDate` = último día del mes M, `startDate` = primer día del mes M+1). No hay restricción mínima de tiempo entre cierre y nueva apertura.
- Q: CHK024 — ¿Cómo detecta el sistema que un asesor "causa baja en la empresa"? → A: **Campo explícito** — el endpoint de cierre de asignación incluye un parámetro `causesBaja: boolean`. Cuando `true`, el sistema activa la reasignación automática de tareas al sucesor; cuando `false` (asesor que sigue en la empresa), el asesor conserva sus tareas. Sin un `causesBaja` explícito el sistema no puede distinguir ambos casos de forma fiable.
