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
- **FR-003**: El sistema DEBE validar la suma de porcentajes de **todos los miembros del equipo
  (asesores y técnicos)** y el estado resultante del equipo **tras cada operación de miembro**
  (`POST/PATCH/DELETE /members`). El responsable y el coordinador NO entran en la suma — son roles de
  gestión con 100% implícito. Cada operación persiste de inmediato (ver Clarifications 2026-05-29).
  El equipo está en estado `active` si y solo si: (a) la suma de asesores+técnicos = 100% **y**
  (b) existe exactamente un `TeamMember` con `role: asesor` e `isPrimary: true`. En caso contrario el
  equipo está en estado `incomplete`. Las transiciones entre estados se calculan automáticamente tras
  cada operación. El sistema NO rechaza operaciones que dejen el equipo en `incomplete` — solo lo
  refleja en la UI con banner advisory y suprime la publicación a Plataforma del Dato.
- **FR-004**: Solo los perfiles **responsable** y **coordinador** DEBEN poder crear, modificar o cerrar
  asignaciones. Los asesores y técnicos tienen acceso de solo lectura.
- **FR-005**: Un **cliente** PUEDE tener varios equipos activos por departamento (modelo multi-equipo confirmado por los diseños `08-multi-equipo/*` — ver Clarifications 2026-05-29). Cada equipo se identifica con un **nombre obligatorio y único** dentro del par cliente+departamento; la unicidad efectiva pasa a ser `(client_id, department, name)` cuando `endDate IS NULL`. La validación del 100% se aplica **por equipo**, no por cliente+departamento. La restricción es sobre el cliente, no sobre el empleado que ejerce de responsable.
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
- **FR-016**: Un empleado MUST ocupar como máximo **un único rol** dentro de un mismo `ClientTeam`. No
  se permite que el mismo empleado figure simultáneamente como Coordinador y Asesor del mismo equipo.
  Si una persona ejerce funciones de coordinación y de asesoría en la práctica, el responsable elige
  el rol formal del equipo (típicamente Coordinador).
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
- **FR-021**: El unique constraint actual de `pgi-service-pgi-api/client_assignment`
  `(client, employee, role, department, dateFrom)` MUST modificarse para incluir `team_id` — sin
  este cambio, el caso multi-equipo (mismo empleado como Asesor del Equipo 1 y del Equipo 2 del mismo
  cliente/departamento/fecha) queda bloqueado por BD.
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

## Open Questions — Pending PO Decision

> Estas preguntas quedaron abiertas durante el refinamiento de DEVPT-518 (2026-05-26).
> Deben responderse antes de iniciar la fase de planificación técnica.
> Se documentan también en la Epic de Jira para visibilidad del equipo.

| # | Área | Pregunta para el PO | Impacto |
|---|------|---------------------|---------|
| OQ-001 | Baja de asesor | Si un asesor deja la empresa y ese cliente no tiene todavía un sucesor designado, ¿qué pasa con las tareas pendientes que tenía ese asesor? ¿Se quedan bloqueadas hasta designar un sucesor, el responsable las asume temporalmente, o quedan en una bandeja de sin asignar? | Alto — define el comportamiento de US4 en el escenario de baja |
| OQ-002 | Asesor de referencia | Cuando un cliente tiene varios asesores repartidos por porcentaje, ¿quién es el "asesor de referencia" (el que recibe las tareas automáticas y aparece como interlocutor principal)? ¿Lo elige el responsable explícitamente, o es siempre el primero que se añadió? | Alto — afecta cómo se reparten las tareas automáticas y quién aparece en los informes |
| OQ-003 | Edición simultánea | Si dos responsables editan el equipo del mismo cliente al mismo tiempo y los dos guardan, ¿qué debería ocurrir? ¿Se guardan los cambios del último en guardar (el primero los pierde sin aviso), o el sistema avisa al segundo de que alguien ya ha modificado el equipo? | Medio — afecta la experiencia de usuario en equipos con varios responsables |
| OQ-004 | Informes no disponibles | Si en el momento de guardar un cambio de equipo el sistema de informes no está disponible, ¿qué prefiere negocio? ¿Que el cambio se guarde en el portal y los informes se actualicen en cuanto el sistema vuelva (puede haber minutos de desfase), o que no se permita guardar hasta que los informes también puedan actualizarse? | Medio — afecta la experiencia al guardar y la fiabilidad de los informes en tiempo real |
| ~~OQ-002~~ | ~~Asesor de referencia~~ | ~~Cuando un cliente tiene varios asesores repartidos por porcentaje, ¿quién es el "asesor de referencia"?~~ | ✅ **RESUELTO 2026-05-29** — Ver Clarifications (asesor principal `isPrimary`, obligatorio uno por equipo). |
| ~~OQ-005~~ | ~~Modelo de equipo~~ | ~~Cuando se configura un equipo para un cliente, ¿ese equipo es siempre exclusivo de ese cliente (se crea desde cero para cada cliente), o puede el mismo equipo atender a varios clientes a la vez?~~ | ✅ **RESUELTO 2026-05-28** — Ver Clarifications. |
| OQ-006 | Nombre del equipo | El campo `name` (FR-005) es obligatorio. ¿Es texto libre que rellena el responsable, viene de un catálogo predefinido (administrado por empresa), o se deriva del `ProvidedService.category` que el equipo cubre (los nombres `Libros`/`Cuota` de los frames `08-multi-equipo/*` coinciden con valores reales de `ServiceCategory` — el equipo podría estar vinculado a uno o varios servicios contratados del cliente y heredar el nombre)? | Alto — afecta UX del modal, modelo de datos (¿FK `ClientTeam → ProvidedService`?), y justificación semántica del multi-equipo |
| OQ-007 | UX del cierre/baja de miembro | El frame `01-crear-equipo/08-tras-anadir-responsable.png` muestra un icono **papelera** junto a cada miembro ya añadido del equipo. Las reglas de cierre/causa baja están en FR-010, pero falta decidir la superficie UX: ¿(a) diálogo inline dentro del mismo modal lateral que pregunta "¿Causa baja?", (b) pantalla / modal aparte dedicada al cierre con campos extensos, validaciones y aviso de consecuencias, o (c) híbrido — inline para cierre simple, pantalla aparte cuando entra causa baja + sucesor? | Medio — define número de pantallas a diseñar y construir |
| OQ-008 | Equipos huérfanos por baja de servicios | FR-017 bloquea la **creación** de equipos en departamentos sin servicios contratados activos, pero NO invalida equipos existentes si después se dan de baja todos los servicios de ese departamento. ¿Es correcto, o el sistema debería cerrar automáticamente los equipos huérfanos cuando se da de baja el último servicio del departamento? | Medio — afecta lifecycle y tareas automáticas en clientes que cancelan servicios |

### Nuevas — Challenge funcional 2026-05-28

> Detectadas por `/speckit-challenge functional`. Ver `challenge-report.md` para evidencia y categorización.

#### business-B1 — real-world-event

**Origen**: `challenge-report.md` (2026-05-28)

**Contexto**: Un asesor causa baja en Azure AD (vía `pd-service-azuread-adapter`) sin que el responsable haya cerrado previamente el equipo. El spec solo cubre la baja como parte de un cierre voluntario con `causesBaja: true`. Distinto escenario que OQ-001 (baja planificada sin sucesor).

Cuando llega un evento de baja de empleado desde Azure AD y ese empleado está activo en uno o más equipos como asesor/técnico/coordinador/responsable, ¿qué debe hacer el sistema?

(a) Marcar automáticamente todas sus asignaciones como cerradas con la fecha de baja y dejar los equipos en estado inconsistente (sin asesor / sin 100%) hasta que un responsable intervenga, generando alerta.
(b) Bloquear la propagación de la baja hasta que un responsable confirme sucesores para cada equipo afectado.
(c) Cerrar sus asignaciones y reasignar automáticamente sus tareas abiertas a un asesor por defecto del departamento (configurable), con notificación al responsable.
(d) Mantener su asignación abierta pero marcarla como 'pendiente reasignación' y bloquear nuevas tareas hasta resolver.

Recomendación técnica: (a) con bandeja de alertas — la baja en Azure AD es source of truth y no debe bloquearse; el equipo en estado inconsistente fuerza acción inmediata del responsable.

_Estado_: pending

---

#### business-B2 — real-world-event

**Origen**: `challenge-report.md` (2026-05-28)

**Contexto**: Cuando un empleado cambia de departamento internamente (FISCAL → LABORAL) o de rol, no se especifica qué ocurre con sus asignaciones activas en el departamento de origen ni con equipos donde figura como responsable/coordinador. FR-006 documenta la restricción pero no la transición.

Cuando un empleado cambia de departamento internamente (evento desde Azure AD o RR.HH.), ¿qué debe hacer el sistema con sus asignaciones activas en el departamento del que sale?

(a) Cerrar automáticamente todas sus asignaciones en el departamento origen con fecha del cambio y exigir designación de sucesor por cada cliente afectado antes de aplicar el cambio.
(b) Permitir el cambio y dejar sus asignaciones del departamento origen abiertas hasta que un responsable las cierre manualmente (período de transición).
(c) Bloquear el cambio de departamento si tiene asignaciones activas como asesor/técnico/coordinador/responsable.

Recomendación técnica: (b) con alerta y límite temporal (p.ej. fin de mes en curso). Bloquear cambios de RR.HH. desde un sistema downstream es frágil; cerrar automáticamente puede dejar clientes sin cobertura.

_Estado_: pending

---

#### business-B3 — real-world-event

**Origen**: `challenge-report.md` (2026-05-28)

**Contexto**: Si un cliente cancela contrato o se baja, sus equipos activos en FISCAL y/o LABORAL siguen abiertos. El spec no aborda este escenario y deja equipos huérfanos que distorsionan métricas en `pd-service-data-factory`.

Cuando un cliente cambia de estado a cancelado/baja en el sistema, ¿qué debe ocurrir con sus equipos activos en FISCAL y LABORAL?

(a) Cerrar automáticamente los equipos con fecha = fecha de baja del cliente, sin requerir `causesBaja` (no hay sucesores, el cliente desaparece).
(b) Mantener los equipos abiertos y exigir al responsable que los cierre manualmente; no permitir crear nuevos.
(c) Marcar equipos como 'inactivos por baja de cliente' (estado nuevo) sin requerir flujo de cierre estándar.

Recomendación técnica: (a) — el cierre automático evita equipos huérfanos. La baja del cliente es un evento de negocio, no requiere sucesor.

_Estado_: pending

---

#### business-B4 — work-reassignment

**Origen**: `challenge-report.md` (2026-05-28)

**Contexto**: FR-010 asume un único 'asesor sucesor' al que reasignar tareas, pero el nuevo modelo permite varios asesores con porcentajes. No queda definido a cuál de los nuevos asesores se reasignan las tareas del que causa baja. Conecta con OQ-002.

Cuando un asesor causa baja y el equipo sucesor tiene varios asesores con distintos porcentajes (p.ej. asesor A 60% y asesor B 40%), ¿a quién se reasignan las tareas abiertas del que se va?

(a) Al asesor con mayor porcentaje en el nuevo equipo. En caso de empate, al primero añadido.
(b) Repartir las tareas proporcionalmente entre los nuevos asesores según su porcentaje.
(c) Al 'asesor de referencia' del nuevo equipo (relacionado con OQ-002).
(d) Responsable/coordinador debe seleccionar manualmente el destinatario por cada tarea o por bloque.

Recomendación técnica: (c) ligado a la resolución de OQ-002 — un único asesor de referencia simplifica la lógica de `obligations-api` y mantiene continuidad para el cliente.

_Estado_: pending

---

#### business-B6 — implied-rule

**Origen**: `challenge-report.md` (2026-05-28)

**Contexto**: FR-009 declara el cierre permanente e irreversible. Si se cierra un equipo por error humano (responsable equivocado, `causesBaja` marcado por error), no existe mecanismo de corrección y la reasignación automática de tareas ya se ejecutó.

Si se cierra un equipo por error humano (fecha mal puesta, `causesBaja` marcado por error, miembro equivocado), ¿qué mecanismo de corrección debe existir?

(a) Ninguno — el cierre es irreversible por diseño; cualquier corrección se hace creando un nuevo equipo. El error queda en histórico como evidencia.
(b) Un rol admin (no responsable) puede revertir un cierre en una ventana corta (p.ej. 24h) si no se han generado eventos downstream.
(c) Permitir 'anular cierre' solo si no hay tareas reasignadas ni eventos publicados aún.

Recomendación técnica: (a) — mantener la inmutabilidad simplifica el modelo y obliga a procesos de QA en la UI (confirmación doble).

_Estado_: ✅ **RESUELTA 2026-05-29** — Opción (a). El cierre sigue siendo irreversible (FR-009); el control suficiente es el modal de doble confirmación obligatorio al guardar (ver Clarifications 2026-05-29 sobre UX del cierre). No se construye mecanismo de reversión.

---

#### business-B7 — forgotten-actor

**Origen**: `challenge-report.md` (2026-05-28)

**Contexto**: El spec no menciona ningún tipo de notificación a los empleados implicados cuando entran o salen de un equipo. Asesores y técnicos solo se enteran si abren la ficha del cliente — ruido operativo y riesgo de tareas no atendidas.

Cuando un asesor o técnico es añadido a un equipo o sale de un equipo, ¿debe notificársele?

(a) Sí, notificación in-app y/o email inmediata a cada miembro afectado al ejecutar commit.
(b) Sí, pero diferida: resumen diario de cambios en sus asignaciones.
(c) No notificar individualmente — el empleado se entera al consultar 'Mis Clientes' (cuando esté actualizado tras esta entrega).
(d) Solo notificar a responsable/coordinador del equipo, no a los miembros entrantes/salientes.

Recomendación técnica: (c) para esta entrega (FR-015 ya excluye 'Mis Clientes'); la notificación al empleado encaja mejor cuando 'Mis Clientes' refleje el nuevo modelo.

_Estado_: pending

---

#### business-B8 — visibility

**Origen**: `challenge-report.md` (2026-05-28)

**Contexto**: El portal del cliente (`pc-app-portalcliente-web`) hoy no muestra composición de equipo. Con porcentajes y múltiples asesores no queda claro qué ve el cliente. Conecta con OQ-002 (asesor de referencia).

Durante esta entrega, ¿qué ve el cliente final en su portal (`pc-app-portalcliente-web`) respecto a su equipo?

(a) Nada cambia — el portal sigue mostrando el asesor 'principal' (de referencia, ligado a OQ-002) como hasta ahora.
(b) Lista completa de miembros del equipo con sus nombres (sin porcentajes).
(c) Lista completa con porcentajes (transparencia total).
(d) Solo se muestra el responsable/coordinador como contacto único.

Recomendación técnica: (a) — mantener el portal del cliente intacto evita ampliar el alcance. La transparencia interna (porcentajes) es para uso interno de gestión, no para el cliente.

_Estado_: pending

---

#### business-B10 — quantitative-edge

**Origen**: `challenge-report.md` (2026-05-28)

**Contexto**: Cuando un equipo se cierra el último día del mes M y otro arranca el primer día del mes M+1 (edge case ya aceptado), no está definido a qué equipo se atribuye la rentabilidad del mes en los informes mensuales de `pd-service-data-factory`.

Cuando un equipo se cierra con `endDate` = último día del mes M y otro equipo nuevo arranca el día 1 del mes M+1 (períodos contiguos válidos), ¿a qué equipo se atribuye la rentabilidad mensual?

(a) Cada mes pertenece íntegramente al equipo activo el día 1 (regla simple, alineada con `pd-service-data-factory`).
(b) Reparto proporcional por días activos en cada mes (más preciso, más complejo).
(c) El usuario decide manualmente al cerrar el equipo.

Recomendación técnica: (a) — el día 1 manda. Regla simple, predecible y alineada con la práctica habitual en informes mensuales.

_Estado_: pending

---

### Nuevas — Challenge funcional 2026-06-01

> Detectadas por `/speckit-challenge functional`. Ver `challenge-report.md` para evidencia y categorización.

### D1 — El indicador del equipo solo mide a los asesores

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US1 (Crear y gestionar el equipo de un cliente)  ·  **Bloquea empezar**: US1

**Escenario**: En la vista del equipo aparece una sola barra que dice literalmente *"Dedicación asesores 20%"* y un contador *"Faltan 80% por asignar"*. Sin embargo, la regla escrita dice que asesores y técnicos suman juntos hasta 100%. Hoy podrían convivir lecturas distintas según quién mire la pantalla.

**Por qué te preguntamos**: Si el indicador real es "solo asesores" y técnicos van por separado, cambia la regla central de la feature y los informes de rentabilidad. Si el copy está mal y de verdad es un único cubo, hay que reescribir la etiqueta antes de salir.

**Recomendación del equipo**: A — La decisión de un solo cubo está ratificada en ADR-0008 y simplifica todo (validación, evento, informes). Lo único que sobra es el copy *"Dedicación asesores"* del diseño: cambiarlo cierra la inconsistencia sin reabrir nada.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Mantener un único cubo (asesores+técnicos = 100%) y corregir el copy de la barra a *"Dedicación del equipo"*. | Hay que reabrir el diseño para retocar etiquetas; el resto de la lógica no cambia. |
| B | Volver a dos cubos independientes: asesores 100% y técnicos 100%, cada uno con su propia barra. | Invalida la decisión madura del 28/05 y el ADR-0008; rehace validaciones backend y modelo de evento. |
| C | Mantener un único cubo pero mostrar dos barras informativas (asesores / técnicos) que solo suman para el badge global. | Más complejo de leer; multiplica la lógica de UI sin cambiar la regla de negocio. |

_Estado_: pending

---

### ✅ D2 — RESUELTA · Dos puntos de entrada distintos para crear el equipo

> **Decisión PO 2026-06-01**: solo desde ficha de cliente. El CTA de *Mis tareas* era resto de diseño y se elimina.

[bloque original abajo conservado para trazabilidad]

### D2 (original) — Dos puntos de entrada distintos para crear el equipo

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US1  ·  **Bloquea empezar**: US1

**Escenario**: El responsable abre la ficha de un cliente y, según desde dónde haya llegado, ve dos pantallas diferentes para empezar: una pone *"Añadir persona"* bajo *"Mis clientes"* y otra *"Crear equipo"* bajo *"Mis tareas"*. Ambas parecen iniciar el mismo flujo pero el botón se llama distinto.

**Por qué te preguntamos**: Sin aclarar, los responsables se confunden (*"¿desde dónde se crea?"*) y soporte recibe consultas duplicadas. Además, si solo una entrada está implementada, gente que entra por la otra cree que la feature no está activa.

**Recomendación del equipo**: A — Tener dos entradas suma flexibilidad para los responsables, pero llamarlas distinto induce dudas. Un solo nombre (*"Crear equipo"*) alinea ambos puntos sin cerrar accesos.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Unificar el CTA a *"Crear equipo"* en ambas vistas, manteniendo los dos puntos de entrada al mismo modal. | Hay que retocar diseño y copy de *"Mis clientes"* para alinear. |
| B | Dejar el empty state solo en *"Datos de cliente"* / *"Mis clientes"* y quitarlo de *"Mis tareas"*. | Quien vive en *"Mis tareas"* tiene que cambiar de sección para crear el equipo. |
| C | Permitir ambos puntos de entrada con su copy actual, asumiendo que conviven. | Mantiene la inconsistencia textual; soporte tendrá que explicar la equivalencia. |

_Estado_: pending

---

### ✅ D3 — RESUELTA · Qué hace la papelera junto a cada miembro del equipo

> **Decisión PO 2026-06-01**: NO borra — pone `dateTo` para preservar histórico. Diálogo inline para `causesBaja` y sucesor según FR-010.

[bloque original abajo conservado para trazabilidad]

### D3 (original) — Qué hace la papelera junto a cada miembro del equipo

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US1  ·  **Relacionada con**: OQ-007

**Escenario**: Una vez que el responsable añade gente al equipo, junto a cada miembro aparece un icono de papelera. Hoy no está claro si pulsarla borra al miembro como si nunca hubiera estado o cierra su asignación con la fecha de hoy y deja huella en el histórico.

**Por qué te preguntamos**: Si la papelera borra sin dejar rastro, el histórico (US3) deja de ser fiable y se pueden perder porcentajes pagados a un asesor. Si cierra con fecha fin, hace falta decidir cuándo se pregunta por `causesBaja` y por el sucesor de las tareas (FR-010).

**Recomendación del equipo**: A — Cerrar siempre con `endDate` preserva el histórico de US3 sin excepciones. El diálogo inline mantiene la operación dentro del mismo modal y evita una pantalla nueva.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | La papelera cierra la asignación con `endDate` = hoy y abre un diálogo inline preguntando *"¿Causa baja?"* y sucesor si procede. | Más pasos por miembro, pero conserva trazabilidad y respeta FR-010. |
| B | La papelera solo borra miembros añadidos en la misma sesión que aún no se han propagado; los ya activos se cierran desde otra acción. | Lógica condicional poco descubrible: el mismo icono hace cosas distintas según el estado del miembro. |
| C | La papelera abre una pantalla / modal dedicado de cierre con campos extensos (fecha, motivo, sucesor, `causesBaja`). | Más superficie a diseñar y construir; rompe la fluidez del modal lateral. |

_Estado_: pending

---

### D4 — Equipos a medias que se quedan así para siempre

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US1, US4

**Escenario**: Un responsable empieza a montar el equipo de un cliente, añade un par de miembros, suma 60% y se va a otra cosa. El equipo queda en estado *"incompleto"* con un banner amarillo. Nadie le recuerda nada y la rentabilidad de ese cliente deja de propagarse a los informes.

**Por qué te preguntamos**: La empresa pierde datos de rentabilidad mientras el equipo siga incompleto. Si el responsable se olvida (vacaciones, baja, salida), nadie reclama y el cliente queda fuera de los cuadros de mando hasta que alguien lo descubre.

**Recomendación del equipo**: A — Mantener la decisión actual evita ampliar el alcance. Si en producción aparecen olvidos reales, lo medimos y añadimos visibilidad en una iteración siguiente. La opción B sería ideal pero requiere construir un widget que hoy no está en el plan.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | No imponer límite: el banner advisory es suficiente y el responsable es quien decide cuándo cerrar el 100%. | Riesgo real de equipos olvidados durante semanas; informes infrarrepresentados. |
| B 🏗 | Mostrar un listado/contador de equipos incompletos en la home de cada responsable para visibilidad operativa. | Requiere un widget nuevo en la home — fuera del alcance del FR-015 (solo ficha de cliente). |
| C | Bloquear la creación de un nuevo equipo en el mismo cliente+departamento mientras haya otro en estado `incomplete`. | Evita olvidos pero puede frustrar a equipos grandes que necesiten varios borradores en paralelo. |

_Estado_: pending

---

### D5 — Bajas temporales prolongadas (enfermedad, maternidad)

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US1, US4

**Escenario**: Un asesor del equipo entra en baja médica de larga duración. Sigue figurando como miembro activo del equipo al 40%, las tareas le siguen llegando, y nadie las atiende durante semanas. Cuando vuelve, encuentra una cola enorme o el cliente ya se ha quejado.

**Por qué te preguntamos**: El cliente queda mal atendido durante la baja y no hay registro de quién está realmente cubriendo el hueco. En facturación, el porcentaje que cobra ese asesor durante la baja queda en zona gris.

**Recomendación del equipo**: A — La opción B es la correcta a futuro pero requiere construir entidad y UI nuevas (suplencias) que no están en el plan. Lo pragmático es operar con cierres manuales y aceptar la fricción hasta que tengamos datos reales de cuántas bajas largas hay al año.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Sustituir manualmente: el responsable cierra la asignación del asesor de baja y añade otro al equipo durante la ausencia, sin un flujo específico. | Cuando el asesor vuelve, hay que volver a montar el equipo a mano; depende de que el responsable se acuerde. |
| B 🏗 | Añadir el concepto de *"suplencia temporal"* a `TeamMember` (fecha inicio/fin suplencia, sustituto), sin alterar el porcentaje del titular. | Requiere construir un modelo de suplencias nuevo — entidad y UI propias; fuera del alcance actual. |
| C | No tratar el caso en esta entrega y documentarlo como gap conocido para una iteración posterior. | Las bajas largas seguirán ocurriendo y se gestionan a mano sin trazabilidad estructurada. |

_Estado_: pending

---

### D6 — De dónde sale el nombre del equipo (Libros, Cuota, Larsa…)

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US1  ·  **Bloquea empezar**: US1  ·  **Relacionada con**: OQ-006

**Escenario**: En el rediseño multi-equipo aparecen equipos llamados *"Libros"*, *"Cuota"*, *"Larsa"* y *"Costa"*. *"Libros"* y *"Cuota"* coinciden con categorías reales de servicio contratado. *"Larsa"* y *"Costa"* parecen apellidos o marcas. Hoy no está claro si el responsable escribe el nombre a mano o lo elige de una lista cerrada.

**Por qué te preguntamos**: Si es texto libre, dos responsables pueden llamar *"Cuota"* y *"cuota mensual"* al mismo equipo, los informes no agruparán. Si es lista cerrada de `ServiceCategory`, hay que crear vínculo `ClientTeam → ProvidedService` y limita qué equipos puede crear el responsable.

**Recomendación del equipo**: C — Los frames muestran ambos tipos de nombre (categoría y apellido), así que la realidad es híbrida. Sugerir desde categoría limpia el caso común; permitir texto libre cubre los casos especiales como Larsa/Costa.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A | Texto libre con validación de unicidad por cliente+departamento, sin vínculo a `ProvidedService`. | Máxima flexibilidad pero datos sucios; no se puede agrupar *"equipos de Libros"* entre clientes. |
| B | Lista cerrada derivada de `ServiceCategory` del cliente: el responsable elige entre los servicios contratados activos. | Modelo limpio y consistente, pero no encaja con nombres tipo *"Larsa"*/*"Costa"* que no son categorías. |
| C ⭐ | Híbrido: sugerencia desde `ServiceCategory` con opción a texto libre cuando ninguna categoría aplica. | Más complejo de construir; la sugerencia puede confundir si el responsable la ignora siempre. |

_Estado_: pending

---

### D7 — Qué porcentajes ve cada perfil en el histórico

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US3 (Histórico de cambios de asignación)

**Escenario**: Un asesor entra a la ficha de un cliente que comparte con otros dos asesores y abre el histórico. Hoy la spec dice que cualquier perfil con acceso a la ficha ve el histórico completo — eso incluye que vea qué porcentaje tienen sus compañeros, lo cual se traduce indirectamente en cuánto cobra cada uno por ese cliente.

**Por qué te preguntamos**: Hay sensibilidad alrededor de la rentabilidad y reparto de carga entre asesores. Si se expone sin filtrar, se generan conversaciones internas incómodas. Por otro lado, ocultar porcentajes al asesor le impide entender su propia carga.

**Recomendación del equipo**: A — Es la opción ya descrita en US3 y la más simple de construir. Si en producción surge fricción por exposición de porcentajes, se reduce visibilidad en una iteración siguiente sin romper datos.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Histórico completo y porcentajes visibles para todos los perfiles con acceso a la ficha. | Transparencia total dentro del equipo, asumiendo conversaciones internas posibles. |
| B | El asesor solo ve sus propias entradas y porcentajes; responsable/coordinador ven todo el equipo. | Más complejo de filtrar; el asesor pierde contexto del reparto global del cliente. |
| C | Todos ven la composición y miembros, pero los porcentajes solo se muestran a responsable/coordinador. | Histórico parcial; el asesor sabe quién está pero no cómo se reparte. |

_Estado_: pending

---

### D8 — Equipo activo en un departamento que el cliente ya no contrata

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US1, US4  ·  **Relacionada con**: OQ-008

**Escenario**: Un cliente cancela el servicio Laboral pero sigue con Fiscal. El equipo de Laboral, con sus dos asesores y técnico, sigue marcado como *"activo"* en la ficha. Aparece en informes y los asesores siguen contando ese cliente en su carga, aunque ya no haya trabajo real que hacer.

**Por qué te preguntamos**: Los porcentajes del equipo huérfano siguen alimentando rentabilidad e informes en Plataforma del Dato, distorsionando métricas. Además, los asesores ven al cliente en su *"Mis Clientes"* (cuando se actualice) sin entender por qué.

**Recomendación del equipo**: B — El cierre automático evita huérfanos pero quita control al responsable y depende de un consumer reactivo a eventos de baja de servicio que hoy no está construido. El banner es feasible con lo que hay y deja la decisión en quien conoce al cliente.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A | El sistema cierra automáticamente el equipo cuando se da de baja el último `ProvidedService` activo de ese departamento, fecha = fecha de baja del servicio. | Automatismo que el responsable no controla; si la baja del servicio se hizo por error hay que crear equipo nuevo. |
| B ⭐ | El sistema no cierra el equipo pero muestra banner persistente en la ficha *"Cliente sin servicios activos en este departamento — considera cerrar el equipo"*. | El cierre depende de que un humano vea el banner; durante el delay los informes están sesgados. |
| C | No tratar el caso en esta entrega: el equipo queda activo y se confía en el responsable. | Acumula deuda; sabemos que pasará y elegimos ignorarlo. |

_Estado_: pending

---

### D11 — Política de asignación de tareas: ¿qué rol del equipo hace cada tipo de tarea?

**Origen**: `challenge-report.md` (2026-06-01, detectado tras challenge por inspección de código)  ·  **Afecta a**: US4, cross-cutting (todas las historias que tocan generación/reparto de tareas)  ·  **Bloquea empezar**: US4

**Tipo**: pregunta abierta — pedimos la regla de negocio antes de proponer opciones técnicas.

**Escenario**: Hoy el modelo `Task` en `pd-service-obligations-api` tiene un único campo de asignación: `advisor: Employee`. Es decir, **todas las tareas que el sistema genera (IVA, IS, libros, cuentas, presentaciones, etc.) van a un asesor — sin distinción de rol**. La `Obligation` tampoco tiene un campo que diga *"esta obligación la hace el técnico, no el asesor"*.

La spec actual responde solo el caso fácil: nuevas tareas auto → asesor principal del equipo. Pero no responde a las preguntas reales que aparecen cuando el equipo tiene varios roles:

- Si una obligación históricamente la hacía el **técnico** (ej. contabilización de libros, cierres mensuales), ¿en el nuevo modelo se sigue asignando al asesor principal o pasa al técnico del equipo?
- ¿El **coordinador** recibe tareas o sólo gestiona?
- ¿El **responsable** recibe tareas o sólo supervisa?
- Si hay 2 asesores y 1 técnico, ¿qué obligaciones van a cada uno?
- Si hay 2 técnicos en el equipo, ¿concepto de *"técnico principal"* análogo al *"asesor principal"*? Hoy no existe.

**Por qué te preguntamos**: Sin esta política definida, el plan técnico no puede saber: (1) si `Task` necesita más de un campo de asignación, (2) si `Obligation` necesita `roleResponsible` para disparar el routing al miembro adecuado, (3) si extendemos *"principal"* a técnico/coordinador/responsable (con más booleans `isPrimary` en `TeamMember`), (4) cómo se reparten obligaciones automáticas cuando hay multi-asesor y multi-técnico simultáneamente.

**Lo que pedimos**: no te damos opciones cerradas porque cualquiera que propongamos llevará nuestro sesgo técnico. Necesitamos primero la regla de negocio:

> *Para cada tipo de obligación que el sistema genera automáticamente (lista en `Obligation.category` / `Obligation.type`): ¿qué rol del equipo es responsable de ejecutarla por defecto?*

Si hay categorías donde la respuesta es *"depende"* (a veces asesor, a veces técnico, según el cliente), dilo — eso ya nos define que necesitamos override por cliente. Con tu respuesta el equipo redacta opciones técnicas concretas en una segunda iteración.

**Datos de contexto**:
- Hoy el sistema genera tareas con campo único `advisor`. El cambio que propongas tiene impacto en `pd-service-data-factory` + `pd-service-obligations-api` + `pgi-service-pgi-api`.
- En el código existen los enums cerrados `ObligationCategory` y `ObligationType`. Si los necesitas para responder, te paso la lista exacta.
- El concepto *"asesor principal"* del equipo ya existe (`TeamMember.isPrimary` cuando `role: asesor`). Análogos para técnico/coordinador/responsable NO existen y habría que crearlos si la respuesta los requiere.

_Estado_: pending

---

### D10 — Cómo encajan las asignaciones que llegan por onboarding desde Jira en el nuevo modelo multi-equipo

**Origen**: `challenge-report.md` (2026-06-01, detectado tras challenge por flag manual)  ·  **Afecta a**: US1, cross-cutting (todas las historias)  ·  **Bloquea empezar**: US1

**Escenario**: Hoy hay un flujo automático que crea asignaciones sin que el responsable haga nada: cuando un cliente se da de alta en Jira y se procesa el onboarding, `pgi-service-pgi-api` recibe el evento `client_onboarding_persisted` y crea filas de `client_assignment` automáticamente (responsable, coordinador, asesor, técnico) con `actor = "system:onboarding"`. Esto lleva meses en producción y la spec actual no lo mencionaba. Cuando esta feature añada `team_id` y multi-equipo, hay que decidir cómo se comportan las asignaciones que entran por onboarding sin saber nada de equipos.

**Por qué te preguntamos**: Si no se decide, el onboarding seguirá creando filas con `team_id = NULL` y aparecerán asignaciones huérfanas en la ficha del cliente. El responsable verá *"hay un asesor asignado pero no está en ningún equipo"* y tendrá que reagruparlas a mano cada vez que se da de alta un cliente nuevo. Tampoco está claro si el onboarding debe respetar la pre-condición de `ProvidedService` (FR-017) o si tiene barra libre por ser un sistema interno.

**Recomendación del equipo**: C — Crear automáticamente un *"Equipo inicial"* por cliente+departamento dentro del propio `applyFromClientOnboarding` y meter ahí las asignaciones del onboarding. Sin tocar el contrato del evento ni al productor (data-factory). El responsable luego renombra el equipo si quiere usar nombre real (D6).

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A | Dejar el onboarding como está: crea filas con `team_id = NULL`. El responsable abre la ficha y agrupa manualmente las asignaciones en un equipo. | Cero cambios en código consumer, pero cada alta de cliente nuevo genera trabajo manual para el responsable y rompe la regla de "todo miembro pertenece a un team". |
| B 🏗 | Ampliar el contrato del evento `client_onboarding_persisted` para que el productor (data-factory / Jira flow) envíe ya `teamName`/`teamId` y el consumer cree el team explícitamente con esos datos. | Requiere coordinar con plataforma del dato + el flujo Jira que origina el onboarding. Cambio cross-team que no está en el alcance de esta épica. |
| C ⭐ | El consumer `applyFromClientOnboarding` crea automáticamente un `ClientTeam` con nombre por defecto (*"Equipo inicial"* o el `ServiceCategory` del servicio si está disponible en el mensaje) por cada cliente+departamento, y mete dentro las asignaciones del onboarding. El responsable puede renombrar después. | Aísla el cambio dentro de pgi-api; no toca contratos. Si llega un cliente con dos servicios del mismo departamento (Libros+Cuota), se crea un único *"Equipo inicial"* que mezcla ambos — el responsable lo separa después si quiere. |

_Estado_: pending

---

### ✅ D9 — RESUELTA · Cambio de rol del empleado (técnico pasa a asesor)

> **Decisión PO 2026-06-01**: Cerrar el rol anterior con `dateTo` + abrir uno nuevo con `dateFrom`. Sin coexistencia inválida en el mismo periodo.

[bloque original abajo conservado para trazabilidad]

### D9 (original) — Cambio de rol del empleado (técnico pasa a asesor)

**Origen**: `challenge-report.md` (2026-06-01)  ·  **Afecta a**: US1, US4

**Escenario**: Pablo Ríos es técnico en el equipo Fiscal de un cliente al 100%. Se le promociona a asesor. El responsable necesita reflejarlo. Hoy no sabemos si Pablo se queda en el mismo equipo cambiando su etiqueta (con su porcentaje intacto), o si se cierra su asignación de técnico y se crea una nueva como asesor desde cero.

**Por qué te preguntamos**: Si se *"edita"* el rol in situ, el histórico pierde el momento del cambio y la rentabilidad de los meses anteriores queda atribuida erróneamente al rol nuevo. Si se cierra y se vuelve a crear, hay un día sin cobertura técnica formal — viola FR-011 si no se sustituye.

**Recomendación del equipo**: A — Mantiene la trazabilidad del cambio en el histórico (cumple US3) y respeta la granularidad mensual de FR-012, que es la base del cálculo de rentabilidad.

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Cerrar la asignación actual con `endDate` = último día del mes anterior y crear una nueva con el nuevo rol al día 1 del mes siguiente. | Hay un mes de transición que requiere coordinación; respeta granularidad mensual. |
| B | Editar el rol en el mismo `TeamMember` manteniendo `id`, `startDate` y `percentage`. | El histórico no refleja el cambio; reporting atribuye mal los meses anteriores. |
| C | Cerrar y crear el mismo día sin gap: dos filas en histórico con la transición clara. | Rompe la convención de granularidad mensual (FR-012). |

_Estado_: pending

---

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
- Q: ¿Persona en más de un rol/equipo simultáneo? → A: **No permitido**. ⚠️ Ambigüedad: ¿se refiere a no más de un rol por equipo (= FR-016) o a no en más de un equipo punto? Ver `po-followup-conflicts.md` punto 1.

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
