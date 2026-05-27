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

2. **Given** un equipo con dos asesores al 60% y 40%,
   **When** el responsable intenta cambiar el segundo al 50%,
   **Then** el sistema rechaza el guardado con el mensaje "Los asesores deben sumar 100%".

3. **Given** un equipo ya existente,
   **When** un asesor o técnico accede a la ficha,
   **Then** puede ver el equipo pero no puede editar ningún miembro.

4. **Given** que un responsable ya tiene un equipo en el Departamento A,
   **When** intenta crear un segundo equipo en ese mismo departamento,
   **Then** el sistema rechaza la operación con el mensaje correspondiente.

---

### User Story 2 — Distribución de carga por porcentaje (Priority: P2)

El responsable o coordinador puede ajustar el porcentaje de carga de cada asesor y técnico dentro del
equipo. El sistema valida en tiempo real que la suma por rol (asesores / técnicos) dentro del departamento
sea exactamente 100% antes de permitir guardar.

**Why this priority**: La distribución de carga es la razón de negocio principal de la feature:
rentabilidad y visibilidad de quién absorbe qué parte del cliente.

**Independent Test**: Puede verificarse únicamente modificando porcentajes en un equipo existente y
comprobando que el sistema acepta o rechaza según la regla del 100%.

**Acceptance Scenarios**:

1. **Given** un equipo con un solo asesor al 100%,
   **When** el responsable añade un segundo asesor al 40% sin ajustar el primero,
   **Then** el sistema muestra advertencia "La suma de asesores es 140%: ajusta antes de guardar".

2. **Given** un equipo con dos asesores al 60% y 40%,
   **When** el responsable cambia ambos a 50% y guarda,
   **Then** el cambio se persiste correctamente.

3. **Given** un equipo sin técnicos,
   **When** se añade un técnico con porcentaje 80%,
   **Then** el sistema rechaza el guardado porque el único técnico no llega al 100%.

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
- **FR-003**: El sistema DEBE validar que la suma de porcentajes de los asesores sea exactamente 100%
  y que la suma de los técnicos sea exactamente 100% (si hay alguno), ambas validaciones por
  departamento dentro del cliente, antes de permitir guardar cualquier cambio.
- **FR-004**: Solo los perfiles **responsable** y **coordinador** DEBEN poder crear, modificar o cerrar
  asignaciones. Los asesores y técnicos tienen acceso de solo lectura.
- **FR-005**: Un **cliente** NO PUEDE tener más de un equipo activo por departamento (unicidad: `cliente + departamento` cuando el equipo no tiene fecha de fin). La restricción es sobre el cliente, no sobre el empleado que ejerce de responsable.
- **FR-006**: Un responsable NO PUEDE pertenecer a más de un departamento.
- **FR-007**: El sistema DEBE mostrar el estado actual de las asignaciones en la ficha del cliente
  (quién está activo, con qué porcentaje y desde cuándo).
- **FR-008**: El sistema DEBE mantener un histórico inmutable de todos los cambios de asignación
  (altas, bajas, cambios de porcentaje), con fecha de inicio y fin de cada período.
- **FR-009**: El sistema DEBE permitir cerrar un equipo fijando una fecha de fin que se propaga a
  todos sus miembros activos. El cierre es **permanente e irreversible**: no se puede reabrir ni
  modificar la fecha de fin una vez confirmada. Para reanudar la atención al cliente en el mismo
  departamento se DEBE crear un nuevo equipo con una nueva fecha de inicio.
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
- **FR-013**: El sistema DEBE migrar automáticamente todas las asignaciones 1-a-1 existentes al modelo
  de porcentajes, asignando un 100% a cada miembro único en su rol y departamento. La migración DEBE
  ser idempotente, no destructiva y ejecutarse en una única pasada sin afectar a los registros de
  histórico existentes.
- **FR-014**: El sistema DEBE sincronizar los datos de asignación (empleado, rol, porcentaje, período)
  con la **Plataforma del Dato** publicando un **evento en el bus de mensajería interno** (RabbitMQ,
  exchange `internal`) al confirmar cada cambio. La Plataforma del Dato consume el evento y actualiza
  sus informes de rentabilidad y cuadros de mando. La propagación DEBE completarse en menos de 5
  minutos desde el guardado confirmado.
- **FR-015**: En el **MVP**, únicamente la **ficha de cliente** DEBE actualizarse para reflejar la lista
  completa de miembros del equipo activo con sus porcentajes. Las pantallas "Mis Clientes", buscador
  global del PGI y los informes internos quedan fuera del alcance de esta iteración y se abordarán
  en una fase posterior. El seguimiento por asesor/técnico en Plataforma del Dato (informes externos)
  queda cubierto por FR-014 vía sincronización.

### Key Entities

> ⚠️ Ver **OQ-005** en la sección Open Questions — la estructura interna de `Team` depende de una
> decisión pendiente de PO. El resto de entidades están definidas independientemente del modelo elegido.

- **Equipo** (`Team`): Agrupación de personas con un responsable, una fecha de inicio y opcionalmente
  una fecha de cierre. *(Scope: ver decisión pendiente arriba.)*
- **Miembro del Equipo** (`TeamMember`): Persona que pertenece al equipo, con rol (responsable,
  coordinador, asesor, técnico), porcentaje de carga, fecha de inicio y fecha de fin opcional.
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
| OQ-005 | Modelo de equipo | Cuando se configura un equipo para un cliente, ¿ese equipo es siempre exclusivo de ese cliente (se crea desde cero para cada cliente), o puede el mismo equipo atender a varios clientes a la vez? Por ejemplo, ¿el "Equipo Fiscal Madrid Norte" puede gestionar una cartera de clientes, o cada cliente tiene su propia composición de equipo sin relación con los demás? | **Crítico — determina cómo se estructura toda la asignación en base de datos e informes. Resolver antes de iniciar la planificación técnica.** |

---

## Clarifications

### Session 2026-05-26

- Q: FR-015 — ¿Qué pantallas/módulos reflejan el equipo múltiple en el MVP? → A: **Solo la ficha de cliente.** "Mis Clientes", buscador PGI e informes internos quedan para una iteración posterior. Informes externos vía Plataforma del Dato cubiertos por FR-014.
- Q: FR-014 — ¿Mecanismo de sincronización con Plataforma del Dato? → A: **Evento RabbitMQ (exchange `internal`)** publicado al confirmar cada cambio. Propagación garantizada en <5 minutos.
- Q: FR-010 / CHK025 — ¿Qué ocurre al cerrar asignación con `causesBaja: true` sin sucesor? → A: **Bloquear el cierre** hasta designar sucesor *(provisional — pendiente de confirmar con PO)*.
- Q: Modelo de equipos — ¿Los equipos se crean por cliente (Modelo A) o existen como entidades independientes que se asignan a clientes (Modelo B)? → **[PENDIENTE DE DECISIÓN]** Ver sección Assumptions para detalle de implicaciones.

### Session 2026-05-25

- Q: FR-005 — ¿La unicidad del equipo activo aplica al cliente o al empleado responsable? → A: Al **cliente** — un cliente no puede tener más de un equipo activo por departamento; la unicidad es `client_id + department WHERE end_date IS NULL`.
- Q: FR-012 — ¿Qué granularidad de fechas se usa para los períodos de asignación? → A: **Híbrida** — fecha exacta en base de datos, convención de primer/último día de mes aplicada en el servicio; cálculo de porcentajes y rentabilidad a granularidad mensual.
- Q: FR-009 — ¿El cierre de un equipo es reversible? → A: **No — permanente**. No se puede reabrir ni modificar `endDate` una vez confirmado. Para continuar se crea un nuevo equipo.
- Q: FR-010 / CHK025 — ¿Qué ocurre si no hay sucesor al dar de baja a un asesor? → A: **Diferido — pendiente de decisión con PO**.
- Q: CHK012 — ¿Se puede crear un nuevo equipo el mismo día del cierre del anterior? → A: **Sí** — períodos contiguos son válidos (`endDate` = último día del mes M, `startDate` = primer día del mes M+1). No hay restricción mínima de tiempo entre cierre y nueva apertura.
- Q: CHK024 — ¿Cómo detecta el sistema que un asesor "causa baja en la empresa"? → A: **Campo explícito** — el endpoint de cierre de asignación incluye un parámetro `causesBaja: boolean`. Cuando `true`, el sistema activa la reasignación automática de tareas al sucesor; cuando `false` (asesor que sigue en la empresa), el asesor conserva sus tareas. Sin un `causesBaja` explícito el sistema no puede distinguir ambos casos de forma fiable.
