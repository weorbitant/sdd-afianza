# Challenge Report — 001-client-team-assignments

**Generated**: 2026-05-28T12:45Z
**Mode**: functional (buckets 1–8, skip 9)
**Reviewers**: business-logic-reviewer
**Artifacts reviewed**: spec.md, plan.md, data-model.md, contracts/

## Summary

| Severity      | Count |
|---------------|-------|
| BLOCKER       | 0     |
| ADR           | 0     |
| QUESTION-PO   | 8     |
| BUSINESS-GAP  | 3     |
| NIT           | 0     |

> Nota de filtrado: 12 hallazgos brutos → 11 supervivientes tras descartar 1 que duplicaba `decisions.md D-005 (PENDING — outbox/retry strategy)`.

## Findings by user story

| Story | Findings | Notes |
|-------|----------|-------|
| US1 (P1 — crear y gestionar equipo) | business-B2, business-B5, business-B7, business-B9 | Carga ligera. B5 y B9 son BUSINESS-GAP — editables sin PO. |
| US2 (P2 — distribución %) | business-B5 | Comparte con US1 (granularidad %). |
| US3 (P3 — histórico) | business-B10, business-B11 | B11 es BUSINESS-GAP — definir semántica de `CLIENT_ASSIGNMENT_VIEW`. |
| US4 (P4 — cierre de equipo) | business-B1, business-B2, business-B3, business-B4, business-B6, business-B7 | **Concentra el riesgo** — 6 findings, 5 son QUESTION-PO. No arrancar US4 sin resolver B1, B3, B4 con el PO. |
| outside-scope | business-B8 | Toca `pc-app-portalcliente-web`. Candidata a US nueva o ampliación explícita de FR-015 (hoy queda como "fuera de alcance" tácito). |

## Findings

### business-B1 — QUESTION-PO — real-world-event

**Affects**: US4 (primary), US1

**Location**: `spec.md (ABSENCE)`

**Evidence**:
> ABSENCE — spec menciona `causesBaja` al cerrar equipo pero no qué pasa cuando llega evento de baja de Azure AD para un asesor de un equipo activo no cerrado.

**Gap**: Un asesor causa baja en Azure AD (vía `pd-service-azuread-adapter`) sin que el responsable haya cerrado previamente el equipo. ¿Qué ocurre con sus asignaciones activas y sus tareas? El spec solo cubre la baja como parte de un cierre voluntario con `causesBaja: true`.

**Pregunta para PO**:

> Cuando llega un evento de baja de empleado desde Azure AD y ese empleado está activo en uno o más equipos como asesor/técnico/coordinador/responsable, ¿qué debe hacer el sistema?
>
> (a) Marcar automáticamente todas sus asignaciones como cerradas con la fecha de baja y dejar los equipos en estado inconsistente (sin asesor / sin 100%) hasta que un responsable intervenga, generando alerta.
> (b) Bloquear la propagación de la baja hasta que un responsable confirme sucesores para cada equipo afectado.
> (c) Cerrar sus asignaciones y reasignar automáticamente sus tareas abiertas a un asesor por defecto del departamento (configurable), con notificación al responsable.
> (d) Mantener su asignación abierta pero marcarla como 'pendiente reasignación' y bloquear nuevas tareas hasta resolver.
>
> Recomendación técnica: (a) con bandeja de alertas — la baja en Azure AD es source of truth y no debe bloquearse; el equipo en estado inconsistente fuerza acción inmediata del responsable. Conecta con OQ-001 pero es escenario distinto (baja involuntaria/no planificada).

---

### business-B2 — QUESTION-PO — real-world-event

**Affects**: US1, US4

**Location**: `spec.md#FR-006`

**Evidence**:
> "FR-006: Responsable NO PUEDE pertenecer a más de un departamento. (Restricción organizativa preexistente.)"

**Gap**: Cuando un empleado cambia de departamento (p.ej. FISCAL → LABORAL) o de rol interno, no se especifica qué ocurre con sus asignaciones activas en el departamento de origen ni con los equipos donde figura como responsable/coordinador.

**Pregunta para PO**:

> Cuando un empleado cambia de departamento internamente (evento desde Azure AD o RR.HH.), ¿qué debe hacer el sistema con sus asignaciones activas en el departamento del que sale?
>
> (a) Cerrar automáticamente todas sus asignaciones en el departamento origen con fecha del cambio y exigir designación de sucesor por cada cliente afectado antes de aplicar el cambio.
> (b) Permitir el cambio y dejar sus asignaciones del departamento origen abiertas hasta que un responsable las cierre manualmente (período de transición).
> (c) Bloquear el cambio de departamento si tiene asignaciones activas como asesor/técnico/coordinador/responsable.
>
> Recomendación técnica: (b) con alerta y límite temporal (p.ej. fin de mes en curso). Bloquear cambios de RR.HH. desde un sistema downstream es frágil; cerrar automáticamente puede dejar clientes sin cobertura.

---

### business-B3 — QUESTION-PO — real-world-event

**Affects**: US4

**Location**: `spec.md (ABSENCE)`

**Evidence**:
> ABSENCE — el spec no menciona qué pasa con equipos activos cuando un cliente cancela contrato, se da de baja o cambia de razón social (merger/split).

**Gap**: Si un cliente cancela contrato o se baja, los equipos activos en FISCAL y/o LABORAL siguen abiertos. No queda claro si el sistema debe cerrar los equipos automáticamente, mantenerlos para histórico, o requerir cierre manual.

**Pregunta para PO**:

> Cuando un cliente cambia de estado a cancelado/baja en el sistema, ¿qué debe ocurrir con sus equipos activos en FISCAL y LABORAL?
>
> (a) Cerrar automáticamente los equipos con fecha = fecha de baja del cliente, sin requerir `causesBaja` (no hay sucesores, el cliente desaparece).
> (b) Mantener los equipos abiertos y exigir al responsable que los cierre manualmente; no permitir crear nuevos.
> (c) Marcar equipos como 'inactivos por baja de cliente' (estado nuevo) sin requerir flujo de cierre estándar.
>
> Recomendación técnica: (a) — el cierre automático evita equipos huérfanos que confunden las métricas de rentabilidad en `pd-service-data-factory`. La baja del cliente es un evento de negocio, no requiere sucesor.

---

### business-B4 — QUESTION-PO — work-reassignment

**Affects**: US4

**Location**: `spec.md#FR-010`

**Evidence**:
> "Si asesor causa baja, responsable/coordinador indica `causesBaja: true` al cerrar; sistema reasigna automáticamente sus tareas abiertas al asesor sucesor."

**Gap**: El spec asume un único 'asesor sucesor' al que reasignar las tareas, pero el nuevo modelo permite varios asesores con porcentajes distintos. No queda definido a cuál de los nuevos asesores se reasignan las tareas del que causa baja.

**Pregunta para PO**:

> Cuando un asesor causa baja y el equipo sucesor tiene varios asesores con distintos porcentajes (p.ej. asesor A 60% y asesor B 40%), ¿a quién se reasignan las tareas abiertas del que se va?
>
> (a) Al asesor con mayor porcentaje en el nuevo equipo. En caso de empate, al primero añadido.
> (b) Repartir las tareas proporcionalmente entre los nuevos asesores según su porcentaje.
> (c) Al 'asesor de referencia' del nuevo equipo (relacionado con OQ-002).
> (d) Responsable/coordinador debe seleccionar manualmente el destinatario por cada tarea o por bloque.
>
> Recomendación técnica: (c) ligado a la resolución de OQ-002 — un único asesor de referencia simplifica la lógica de `obligations-api` y mantiene continuidad para el cliente. Repartir tareas (b) genera fricción operativa.

---

### business-B5 — BUSINESS-GAP — quantitative-edge

**Affects**: US1, US2

**Location**: `spec.md#FR-003`

**Evidence**:
> "FR-003: Sistema DEBE validar suma porcentajes de todos los miembros (asesores + técnicos) = 100% exacto por cliente+depto en commit."

**Gap**: No se especifica granularidad mínima del porcentaje (¿enteros 1-100? ¿decimales?). `data-model.md` define `smallint 1-100` pero el spec funcional no lo formaliza. Tres asesores a partes iguales no suman 100 con enteros (33-33-34 vs decimales).

**Suggestion**: Añadir a FR-003: "el porcentaje es un entero entre 1 y 100. La suma exacta = 100 se valida con aritmética entera. Para repartos no exactos (p.ej. 3 miembros), el responsable distribuye discrecionalmente (33-33-34) y la UI puede sugerir un reparto inicial."

> _Nota_: Si el PO prefiere decimales (informes más precisos), entonces hay que cambiar `data-model.md` (`smallint` → `decimal(5,2)`) y el plan de migración FR-013. Llevar a confirmación en sync.

---

### business-B6 — QUESTION-PO — implied-rule

**Affects**: US4

**Location**: `spec.md#FR-009`

**Evidence**:
> "Cierre permanente e irreversible: no se puede reabrir ni modificar endDate una vez confirmada."

**Gap**: Si se cierra un equipo por error humano (responsable equivocado, fecha mal, `causesBaja` marcado por error), no existe ningún mecanismo de corrección. Crear un nuevo equipo no resuelve trazabilidad ni revierte la reasignación automática de tareas al sucesor.

**Pregunta para PO**:

> Si se cierra un equipo por error humano (fecha mal puesta, `causesBaja` marcado por error, miembro equivocado), ¿qué mecanismo de corrección debe existir?
>
> (a) Ninguno — el cierre es irreversible por diseño; cualquier corrección se hace creando un nuevo equipo. El error queda en histórico como evidencia.
> (b) Un rol admin (no responsable) puede revertir un cierre en una ventana corta (p.ej. 24h) si no se han generado eventos downstream.
> (c) Permitir 'anular cierre' solo si no hay tareas reasignadas ni eventos publicados aún (raro en práctica).
>
> Recomendación técnica: (a) — mantener la inmutabilidad simplifica el modelo, garantiza histórico fiable y obliga a procesos de QA en la UI (confirmación doble). Conecta con SC-005 (histórico inmutable).

---

### business-B7 — QUESTION-PO — forgotten-actor

**Affects**: US1, US4

**Location**: `spec.md (ABSENCE)`

**Evidence**:
> ABSENCE — el spec no menciona ningún tipo de notificación a los empleados implicados cuando entran o salen de un equipo.

**Gap**: Asesores y técnicos no se enteran de su entrada/salida de un equipo salvo que abran la ficha del cliente. Para empleados con muchos clientes esto es ruido operativo importante y puede llevar a tareas no atendidas.

**Pregunta para PO**:

> Cuando un asesor o técnico es añadido a un equipo o sale de un equipo, ¿debe notificársele?
>
> (a) Sí, notificación in-app y/o email inmediata a cada miembro afectado al ejecutar commit.
> (b) Sí, pero diferida: resumen diario de cambios en sus asignaciones.
> (c) No notificar individualmente — el empleado se entera al consultar 'Mis Clientes' (cuando esté actualizado tras esta entrega).
> (d) Solo notificar a responsable/coordinador del equipo, no a los miembros entrantes/salientes.
>
> Recomendación técnica: (c) para esta entrega (FR-015 ya excluye 'Mis Clientes'); la notificación al empleado encaja mejor cuando 'Mis Clientes' refleje el nuevo modelo. Documentar como pendiente explícito para la siguiente iteración.

---

### business-B8 — QUESTION-PO — visibility

**Affects**: outside-scope (toca `pc-app-portalcliente-web`)

**Location**: `spec.md#FR-015`

**Evidence**:
> "En MVP, únicamente la ficha de cliente DEBE actualizarse para reflejar miembros del equipo activo. 'Mis Clientes', buscador global PGI e informes internos quedan fuera del alcance."

**Gap**: El portal del cliente (`pc-app-portalcliente-web`) hoy no muestra composición de equipo. Con porcentajes y múltiples asesores no queda claro qué ve el cliente (¿un único asesor de referencia? ¿todos? ¿nada cambia?). El cliente puede llamar y pedir hablar 'con su asesor' y haber varios.

**Pregunta para PO**:

> Durante esta entrega, ¿qué ve el cliente final en su portal (`pc-app-portalcliente-web`) respecto a su equipo?
>
> (a) Nada cambia — el portal sigue mostrando el asesor 'principal' (de referencia, ligado a OQ-002) como hasta ahora. Coherencia con cliente, cero impacto en `pc-app`.
> (b) Lista completa de miembros del equipo con sus nombres (sin porcentajes).
> (c) Lista completa con porcentajes (transparencia total).
> (d) Solo se muestra el responsable/coordinador como contacto único.
>
> Recomendación técnica: (a) — mantener el portal del cliente intacto evita ampliar el alcance y reduce riesgo de confusión externa. La transparencia interna (porcentajes) es para uso interno de gestión, no para mostrar al cliente.

---

### business-B9 — BUSINESS-GAP — implied-rule

**Affects**: US1

**Location**: `spec.md#FR-013`

**Evidence**:
> "FR-013: Sistema DEBE migrar automáticamente todas las asignaciones 1-a-1 existentes al modelo de porcentajes (100% a cada miembro único). Migración idempotente, no destructiva, una pasada."

**Gap**: El spec asume migración limpia sin definir qué hacer con datos malformados en producción (clientes con asignación abierta pero sin asesor activo, empleados ya dados de baja todavía asignados, fechas inválidas).

**Suggestion**: Ampliar FR-013 con: "La migración DEBE generar un informe de inconsistencias detectadas (clientes sin asesor activo, miembros con baja en Azure AD, fechas inválidas) que se entrega a responsables tras despliegue. Las inconsistencias NO bloquean la migración; los equipos resultantes quedan marcados como 'requieren revisión' para que el responsable los corrija desde la UI."

> _Nota_: convertir en QUESTION-PO si producto prefiere bloquear despliegue ante datos sucios.

---

### business-B10 — QUESTION-PO — quantitative-edge

**Affects**: US3

**Location**: `spec.md#FR-012`

**Evidence**:
> "FR-012: Granularidad de fechas híbrida: fecha exacta almacenada, servicio valida primer/último día de mes."

**Gap**: Cuando un equipo se cierra el último día del mes M y otro arranca el primer día del mes M+1 (edge case ya aceptado en `## Edge Cases`), no está definido a qué equipo se atribuye la rentabilidad del mes solapado en los informes mensuales de `pd-service-data-factory`. Tampoco se aborda el caso real de que altas/bajas de Azure AD no caen en día 1 o último.

**Pregunta para PO**:

> Cuando un equipo se cierra con `endDate` = último día del mes M y otro equipo nuevo arranca el día 1 del mes M+1 (períodos contiguos válidos), ¿a qué equipo se atribuye la rentabilidad mensual?
>
> (a) Cada mes pertenece íntegramente al equipo activo el día 1 (regla simple, alineada con `pd-service-data-factory`).
> (b) Reparto proporcional por días activos en cada mes (más preciso, más complejo).
> (c) El usuario decide manualmente al cerrar el equipo.
>
> Recomendación técnica: (a) — el día 1 manda. Es la regla más simple, predecible y alineada con la práctica habitual en informes mensuales. Documentarlo explícitamente en FR-012 o en un AC de US3.

---

### business-B11 — BUSINESS-GAP — visibility

**Affects**: US3, US1

**Location**: `spec.md (ABSENCE)`

**Evidence**:
> ABSENCE — no se especifica si un asesor/técnico ya salido del equipo conserva acceso de lectura al histórico del cliente al que perteneció.

**Gap**: Un asesor que dejó de estar asignado a un cliente hace tiempo, ¿puede seguir consultando la ficha y el histórico de ese cliente (por ejemplo para responder una pregunta sobre algo que él hizo)? El permiso `CLIENT_ASSIGNMENT_VIEW` no aclara si es por cliente actual o por histórico.

**Suggestion**: Añadir AC a US3: "Cualquier usuario con permiso `CLIENT_ASSIGNMENT_VIEW` puede consultar el histórico de cualquier cliente, independientemente de haber sido o no miembro de su equipo. El permiso es por rol global, no por relación activa con el cliente."

> _Nota_: si producto quiere aislamiento por relación activa (compliance/GDPR), elevar a QUESTION-PO.

---

## Failed reviewers

(ninguno)

## Next actions

- **BLOCKER findings**: ninguno — puedes proceder a planificar tareas.
- **QUESTION-PO findings (8)**: candidatos para `spec.md > Open Questions`. El orchestrator ofrecerá promover en el siguiente paso.
- **BUSINESS-GAP findings (3)**: edita `spec.md` para añadir el FR/AC que falta usando la `suggestion` como punto de partida (B5 → FR-003, B9 → FR-013, B11 → AC nuevo en US3). No necesitan input del PO salvo en los matices marcados con "_Nota_".
- **NIT**: ninguno.

## Conexiones con Open Questions ya existentes en spec.md

- **B1** ↔ OQ-001 (baja sin sucesor) — B1 es el caso de baja involuntaria desde Azure AD, OQ-001 es el cierre manual sin sucesor designado. Misma raíz, distintos triggers.
- **B4** ↔ OQ-002 (asesor de referencia) — B4 propone usar la decisión de OQ-002 como mecanismo de routing de tareas legacy.
- **B8** ↔ FR-015 / OQ-002 — el portal del cliente depende del asesor de referencia.
