# Decisiones pendientes — Asignaciones Múltiples en Ficha de Cliente

**Para**: PO  ·  **Generado**: 2026-05-29  ·  **Modo**: functional (design conformance)

## En una frase

Tenemos **6 decisiones de negocio** que necesitamos resolver contigo antes de construir, más 2 aclaraciones que el equipo cerrará por su cuenta. Esta ronda se centra en **conformidad con los diseños** — la ronda anterior (2026-05-28) ya cubrió el resto de huecos funcionales.

## Riesgo por historia

| Historia | Decisiones | Aclaraciones | ¿Se puede empezar? |
|----------|-----------|--------------|---------------------|
| US1 — Crear y gestionar el equipo de un cliente | D1, D2, D3, D4, D6 | G1, G2 | **No — bloqueada hasta resolver D1, D2, D3, D4** |
| US2 — Distribución de carga por porcentaje | D4 | — | **No — bloqueada hasta resolver D4** |
| US3 — Histórico de cambios de asignación | — | — | Sí |
| US4 — Cierre de equipo | D1, D2, D3, D5 | — | **No — bloqueada hasta resolver D1, D2, D3, D5** |

## Qué necesitamos de ti

- **6 decisiones** marcadas como `D1..D6` abajo. Cada una incluye escenario, opciones, trade-offs y nuestra recomendación.
- Cada decisión se publicará como un comentario individual en la Epic de Jira al ejecutar `/speckit-atlassian-sync-push`. Puedes responder ahí mismo con la letra elegida.
- **2 aclaraciones** (`G1..G2`) que cerraremos sin tu intervención salvo que veas algo raro — sección *Aclaraciones* más abajo.

---

## Decisiones

### D1 — ¿Varios equipos activos a la vez por cliente y departamento?

**Afecta a**: US1 (Crear y gestionar equipo) — principal, US4 (Cierre de equipo)
**¿Bloquea empezar?**: Sí — US1

#### Escenario
En la ficha de Creativa Studio S.L. se ven dos equipos del departamento Fiscal funcionando a la vez ('Equipo Larsa' y 'Equipo Costa'), cada uno con su responsable, coordinador, asesor y técnico. Hoy la spec dice expresamente que un cliente solo puede tener un equipo activo por departamento. El diseño contradice esa regla.

#### Por qué te preguntamos
Si admitimos varios equipos por departamento se rompe la regla de unicidad, la validación del 100% pasa a ser por equipo y no por cliente+departamento, y cambia toda la lógica de reasignación de tareas. Si la mantenemos, los diseños no son implementables tal como están y hay que rehacerlos.

#### Recomendación del equipo: A
Los diseños son la fuente de verdad cuando hay conflicto con la spec. Si los frames muestran varios equipos activos por departamento, asumimos ese modelo: reescribimos FR-005 (la unicidad pasa a ser por nombre+departamento, no por departamento), ampliamos `ClientTeam` con el campo `name` (D3 obligatorio), y la validación del 100% pasa a aplicarse por equipo en lugar de por cliente+departamento.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Permitir varios equipos activos por cliente+departamento, cada uno con su propio nombre y su propia validación del 100%. | Cambia FR-005, FR-003 y la sincronización con Plataforma del Dato; impacto grande en modelo y migración. |
| B | Mantener un único equipo activo por departamento y rehacer los frames multi-equipo antes de implementar. | Los diseños actuales no se respetan; los frames de carteras Larsa/Costa/Libros/Cuota se descartan. |
| C | Reinterpretar 'Equipo Larsa' y 'Equipo Costa' como sub-carteras dentro de un mismo equipo, no como equipos independientes. | Requiere introducir el concepto de cartera/sub-equipo, no contemplado hoy en el modelo. |

---

### D2 — Marca de asesor principal en cada equipo

**Afecta a**: US1 (Crear y gestionar equipo) — principal, US4 (Cierre de equipo)
**¿Bloquea empezar?**: Sí — US1
**Relacionada con**: OQ-002

#### Escenario
Cuando se añade un asesor a un equipo, el modal incluye un checkbox 'Marcar como asesor principal' y luego ese asesor aparece con la etiqueta 'Principal' en la lista del equipo. Esto parece responder a la pregunta abierta OQ-002 (quién es el asesor de referencia), pero hoy ni la spec ni el modelo de datos guardan esa marca.

#### Por qué te preguntamos
Sin definir el significado de 'principal', el equipo de desarrollo tendría que inventar las reglas: ¿puede haber dos principales? ¿es obligatorio uno? ¿es el destinatario por defecto de tareas y de la reasignación al causar baja? Estas decisiones impactan a quién llega cada tarea y a quién ve el cliente como interlocutor.

#### Recomendación del equipo: A
Cierra a la vez OQ-002 y un hueco del modelo. El diseño ya empuja en esa dirección y los responsables están acostumbrados a 'un asesor de cabecera' por cliente.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Adoptar 'asesor principal' como la respuesta a OQ-002: exactamente uno por equipo, obligatorio, recibe tareas automáticas y herencia al causar baja. | Obliga al responsable a elegir uno; añade validación nueva al commit. |
| B | Hacer la marca de 'principal' opcional (cero o uno) sin efecto funcional, solo visual para el responsable. | No resuelve OQ-002 ni el routing de tareas — el diseño promete algo que no se cumple. |
| C | Retirar el checkbox y el badge del diseño hasta resolver OQ-002 explícitamente. | Hay que rehacer varios frames antes de implementar. |

---

### D3 — Nombre de equipo en la ficha de cliente

**Afecta a**: US1 (Crear y gestionar equipo) — principal, US4 (Cierre de equipo)
**¿Bloquea empezar?**: Sí — US1

#### Escenario
En clientes con varios equipos activos en el mismo departamento los diseños identifican cada uno con un nombre corto: 'Equipo Libros', 'Equipo Cuota', 'Equipo Larsa', 'Equipo Costa'. En clientes con un único equipo no hay nombre, solo el literal 'Equipo'. La spec no menciona este atributo.

#### Por qué te preguntamos
Sin un nombre, los responsables no pueden distinguir entre los equipos a simple vista ni en filtros o informes. Si lo introducimos, hay que decidir si es obligatorio, único por cliente, editable y si se publica en los eventos a Plataforma del Dato.

#### Recomendación del equipo: A
Un nombre obligatorio da identidad estable al equipo y permite seguirlo a lo largo del tiempo aunque cambien sus miembros. Es coherente con la dirección que marca el diseño.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Hacer el nombre obligatorio y único por cliente+departamento; se introduce al crear el equipo y se publica en los eventos a Plataforma del Dato. | Añade un campo y una validación más al alta del equipo. |
| B | Permitir nombre opcional; los equipos sin nombre se muestran como 'Equipo 1', 'Equipo 2'… por orden de creación. | Los informes pueden mezclar equipos con y sin nombre — peor experiencia. |
| C | No introducir nombre y modificar el diseño para identificar los equipos por sus miembros (p.ej. 'Equipo de Alejandro'). | Cambia el diseño y se pierde estabilidad del identificador cuando el responsable rote. |

> **Nota**: D3 va de la mano con **D1**. Si confirmas D1=A (varios equipos activos por departamento), el nombre pasa a ser obligatorio sí o sí — sin él los responsables no pueden distinguir entre "Equipo Larsa" y "Equipo Costa" en la misma ficha.

---

### D4 — ¿Cuándo se da por confirmado el equipo?

**Afecta a**: US1 (Crear y gestionar equipo) — principal, US2 (Distribución de carga)
**¿Bloquea empezar?**: Sí — US1

#### Escenario
En el diseño, cada vez que el responsable añade un miembro aparece un toast 'Asignaciones creadas correctamente' inmediatamente. Si el equipo no llega al 100% se queda como está, con un aviso amarillo, pero ya guardado. No hay ningún botón 'Confirmar equipo' por ninguna parte. La spec, en cambio, dice que el equipo solo se da por bueno cuando el responsable pulsa un 'Confirmar' y la suma es exactamente 100%.

#### Por qué te preguntamos
Si el equipo se considera 'activo' desde el primer miembro guardado, podemos publicar a Plataforma del Dato equipos a medias (al 20% o al 60%) y generar informes de rentabilidad inconsistentes. Si el equipo solo se considera activo tras alcanzar el 100%, hay que añadir un botón al diseño que hoy no existe.

#### Recomendación del equipo: A
Respeta lo que ven los responsables en el diseño (toasts inmediatos) sin contaminar los informes. El estado 'incompleto' es honesto: el equipo existe pero todavía no cubre al cliente al 100%.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Persistir cada cambio al instante y mostrar el equipo como 'incompleto' hasta sumar 100%; no publicar a Plataforma del Dato hasta entonces. | Hay que distinguir 'incompleto' de 'activo' en todas las pantallas y eventos. |
| B | Añadir un botón 'Confirmar equipo' al diseño y mantener el flujo borrador+commit del spec. | El diseño actual hay que rehacerlo y se pierde la inmediatez del toast. |
| C | Persistir cada cambio al instante y publicar a Plataforma del Dato directamente; el banner amarillo es solo informativo. | Riesgo alto de informes con equipos a medias durante la composición. |

---

### D5 — Cerrar el equipo desde el modal de añadir asignación

**Afecta a**: US4 (Cierre de equipo) — principal
**¿Bloquea empezar?**: Sí — US4

#### Escenario
Para cerrar un equipo, el responsable no encuentra un botón 'Cerrar equipo' en la ficha; tiene que abrir el modal de 'Añadir nueva asignación' y marcar un checkbox llamado 'Marcar fecha fin de equipo'. Una vez marcado, esa fecha se aplica al equipo entero. La spec, en cambio, describe el cierre como una acción independiente, permanente e irreversible.

#### Por qué te preguntamos
Si el cierre se hace desde el flujo de alta, es muy fácil cerrarlo por error al estar añadiendo un miembro. Y al ser irreversible (FR-009), el error es definitivo. Además, no queda claro cómo se conecta con el cierre por baja (causesBaja) y con la designación de sucesor, ni si exige confirmación explícita.

#### Recomendación del equipo: A
El cierre es irreversible y desencadena reasignación de tareas; merece su propia acción separada del alta de miembros. El coste UX es bajo frente al riesgo de cierres accidentales.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Mover el cierre a una acción independiente con doble confirmación, separada del modal de añadir miembro. | Cambia el diseño actual; un paso más para el responsable. |
| B | Mantener el checkbox en el modal pero exigir confirmación adicional al guardar si se ha marcado fecha fin de equipo. | Cierre por error sigue siendo posible aunque más controlado. |
| C | Mantener el flujo del diseño tal cual y aceptar el riesgo de cierre accidental. | Choca con la inmutabilidad de FR-009 — cierres por error sin marcha atrás. |

> **Nota**: conecta con la pregunta nueva **B6** que tenías pendiente subir a Jira sobre corrección de cierre por error. Si elegimos A aquí (acción separada con doble confirmación), B6 puede quedar resuelta como "no hace falta mecanismo de reversión".

---

### D6 — Selector de fecha por mes en el modal

**Afecta a**: US1 (Crear y gestionar equipo)
**¿Bloquea empezar?**: No

#### Escenario
Cuando el responsable elige la fecha de inicio de una asignación, el calendario solo le deja escoger un mes ('May 2025', 'Jun 2025'…), nunca un día. La pantalla luego muestra 'desde 05/2026'. La spec, en cambio, dice que la base de datos guarda fechas exactas con día, mes y año.

#### Por qué te preguntamos
Si la UI no expone el día, las altas a mitad de mes (asesor que entra el 15) no son introducibles por el responsable. Para el histórico de auditoría puede importar saber el día exacto; para la rentabilidad mensual ya hemos dicho que da igual. Conviene confirmar si el día siempre es 1 / último, o si en algún caso necesitamos un día concreto.

#### Recomendación del equipo: A
Encaja con FR-012 y con la lógica mensual de rentabilidad. Si en el futuro necesitamos el día exacto, es una ampliación aditiva del modal.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Aceptar que la UI solo elige mes; el servicio fija día 1 al alta y último día al cierre, alineado con FR-012. | Se pierde el día real del cambio en el histórico. |
| B | Añadir un selector de día opcional en el modal para casos especiales (alta a mitad de mes). | Mayor complejidad en el modal y posibles inconsistencias con el cálculo mensual. |

---

## Aclaraciones que cerrará el equipo

Estas son ambigüedades que la spec olvidó formalizar pero que tienen respuesta clara. El equipo las añadirá al spec sin necesitar tu input. **Solo léelas si quieres saber qué decidiremos** — si discrepas con alguna, dínoslo y la elevamos a decisión tuya.

### G1 — Barra de dedicación y contador por rol en la ficha

**Afecta a**: US1 (Crear y gestionar equipo)

Añadir AC a US1 (y referencia en FR-007): *"En la ficha de cliente, encima de la lista del equipo, el sistema DEBE mostrar (a) una barra de progreso con la dedicación agregada de asesores+técnicos (0–100%), (b) el texto 'Faltan N% por asignar' cuando la suma sea < 100% y (c) un contador con el número de miembros activos por rol (responsable, coordinador, asesor, técnico). El resumen se actualiza en tiempo real al añadir/editar miembros."*

---

### G2 — Filas placeholder cuando faltan coordinador o técnicos

**Afecta a**: US1 (Crear y gestionar equipo)

Añadir AC a US1: *"En la vista de equipo activo, cuando un equipo no tenga coordinador y/o no tenga técnicos, el sistema DEBE mostrar una fila placeholder ('No hay coordinador', 'No hay técnicos') con un CTA inline '+ Añadir asignaciones' visible solo para perfiles con permiso `CLIENT_ASSIGNMENT_EDIT`. La ausencia de responsable o de asesor NO se representa como placeholder porque ambos son obligatorios y bloquean el alta del equipo."*

---

## Anexo técnico — para el equipo

### Resumen por severidad

| Severidad     | Cuántos |
|---------------|---------|
| BLOCKER       | 0       |
| ADR           | 0       |
| QUESTION-PO   | 6       |
| BUSINESS-GAP  | 2       |
| NIT           | 0       |

### Hallazgos técnicos

Ninguno en esta ronda — modo `functional`, sin reviewer de feasibility.

### Trazabilidad de IDs

| ID PO | Reviewer ID | Severity | Location |
|-------|-------------|----------|----------|
| D1    | business-B12 | QUESTION-PO | spec.md#FR-005 |
| D2    | business-B13 | QUESTION-PO | spec.md (ABSENCE) |
| D3    | business-B14 | QUESTION-PO | spec.md (ABSENCE) |
| D4    | business-B15 | QUESTION-PO | spec.md#FR-003 |
| D5    | business-B16 | QUESTION-PO | spec.md#FR-009 |
| D6    | business-B17 | QUESTION-PO | spec.md#FR-012 |
| G1    | business-B18 | BUSINESS-GAP | spec.md#FR-007 |
| G2    | business-B19 | BUSINESS-GAP | spec.md (ABSENCE) |

### Evidencia literal de las Decisiones

- **D1** — `spec.md#FR-005` + `DESIGN — 08-multi-equipo/01-multi-equipo-fiscal-larsa-costa.png`: dos equipos 'Equipo 1' y 'Equipo 2' simultáneamente Activos en Departamento Fiscal del mismo cliente Creativa Studio S.L.
- **D2** — `spec.md (ABSENCE)` + `DESIGN — 02-anadir-asesor/01-modal-checkbox-asesor-principal.png`: checkbox 'Marcar como asesor principal' en el modal y badge 'Principal'/'P' junto al asesor en la lista del equipo.
- **D3** — `spec.md (ABSENCE)` + `DESIGN — 08-multi-equipo/02-vista-compacta-libros-cuota.png`: cada fila de equipo muestra una etiqueta de nombre propio (Libros, Cuota, Larsa, Costa) junto al literal 'Equipo'.
- **D4** — `spec.md#FR-003` + `DESIGN — 05-vista-equipo-incompleto/01-equipo-incompleto-banner-warning-20pct.png`: equipo con Asesor 20% guardado y toast 'Asignaciones creadas correctamente' + banner amarillo 'No hay establecido un 100% de carga'. No hay botón 'Confirmar equipo'.
- **D5** — `spec.md#FR-009` + `DESIGN — 03-fecha-fin-equipo/01-modal-checkbox-fecha-fin-equipo.png`: checkbox 'Marcar fecha fin de equipo' dentro del modal de añadir asignación, no en una acción separada.
- **D6** — `spec.md#FR-012` + `DESIGN — 01-crear-equipo/06-modal-fecha-inicio-calendario.png`: el selector de 'Fecha inicio' solo deja elegir mes (Ene, Feb, Mar…) dentro de un año, no día concreto.

### Reviewers fallidos

Ninguno.

### Próximos pasos (para el equipo)

- **Decisiones (D1..D6)**: el orchestrator ofrecerá publicarlas como Open Questions en `spec.md` (sección Open Questions) si confirmas. Después, `/speckit-atlassian-sync-push` las sube como comments individuales a la Epic DEVPT-518.
- **Aclaraciones (G1..G2)**: editar `spec.md` añadiendo los AC propuestos en `suggestion`. No requieren input del PO.
- **Conexiones con la ronda anterior** (challenge-report.md del 2026-05-28, ya en spec.md > Open Questions):
  - D1 (multi-equipo) puede invalidar varias decisiones previas — resolverla cambia el alcance del modelo.
  - D2 (asesor principal) **resuelve OQ-002** ("asesor de referencia") que llevaba bloqueada desde el 26/5.
  - D5 (cerrar desde modal) **conecta con B6** (corrección de cierre por error) que estaba pendiente de subir a Jira — si elegimos A en D5, B6 puede cerrarse sin necesidad de mecanismo de reversión.
