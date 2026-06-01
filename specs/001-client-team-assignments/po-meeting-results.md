# DEVPT-518 · Resultados sesión PO

**Fecha**: 2026-06-01  ·  **Modelo**: 4 categorías — ✅ Respondida · 🟡 Parcial · ⏳ Pendiente · ⚠️ Conflicto con spec actual

---

## ✅ Respondidas (cerradas en la sesión)

| # | Pregunta | Decisión PO | Acción siguiente | Owner |
|---|---|---|---|---|
| 2 | ¿Crear equipo desde *Mis tareas* o solo desde *ficha de cliente*? | Solo desde ficha de cliente. El CTA de *Mis tareas* era resto de diseño. | Quitar empty state de *Mis tareas* en spec + frames | Dev |
| 3 | Nombres del equipo (*Libros*, *Cuota*, *Larsa*…) | **Ignorar**. No representan regla de negocio para esta feature. | Cerrar D6 / OQ-006 + reescribir FR-005 sin obligatoriedad de naming derivado | Dev |
| 4 | Onboarding desde Jira crea asignaciones | Sí, mantener el comportamiento actual del onboarding | Cerrar D10 con opción de seguir creando como hoy (ver 🟡 abajo — falta `team_id`) | Dev |
| 6 | Papelera del modal | **No borra** — pone `dateTo`. Mantiene histórico siempre. | Aplicar a FR-009 + spec frames. Cerrar D3 / OQ-007 | Dev |
| 11 | Cambio de rol (técnico → asesor) | Cerrar el rol anterior con `dateTo` + abrir uno nuevo con `dateFrom`. Sin coexistencia inválida. | Cerrar D9. Documentar en US1 + FR-010 | Dev |
| — | **Composición mínima del equipo** | 1 responsable obligatorio · 1+ asesores · 0-1 coordinador · 0-N técnicos | Refuerza FR-003 (ya estaba). Confirmar visualmente: asterisco + validación + botón guardar **bloqueado** si no se cumple | Dev |
| — | **Equipos futuros permitidos** | Sí | Cerrar parte de la duda original sobre fechas. Documentar como AC | Dev |
| — | **Persona en más de un rol/equipo en mismo periodo** | No permitido | Refuerza FR-016. Pero ⚠️ ver punto en sección Conflicto | Dev |
| — | **Tareas nunca se pierden** | Siempre se generan aunque falle la asignación. Se escala. | Añadir nueva AC a US4 / FR-010 | Dev |
| — | **Porcentajes son solo para informes de rentabilidad** | No afectan a quién recibe la tarea | ⚠️ Conflicto parcial con spec — ver sección abajo | Dev |
| — | **Validación UI = validación Jira** | Misma lógica en ambos lados | Documentar como invariante en spec | Dev |
| — | **Asignaciones múltiples = mover carteras** | Es una operación masiva de reasignación (varios clientes a la vez, con porcentajes y fecha efectiva) | Confirmar si está en scope de DEVPT-518 o es feature aparte | PO + Tech Lead |
| — | **Grupo de empresas en ficha cliente** | Localizado en frames, no era duda conceptual | Verificar que está reflejado en spec | Dev |

---

## 🟡 Parcialmente respondidas (orientación pero sin cerrar)

| # | Pregunta | Lo que se aclaró | Lo que falta | Owner |
|---|---|---|---|---|
| 4 | Onboarding con `team_id` | OK seguir creando como hoy | Decidir si el onboarding crea ahora un *Equipo inicial* con `team_id` o sigue dejando `team_id = NULL` | PO o Dev (necesita confirmación) |
| 7 | Equipos a medias indefinidamente | Validación bloqueante si falta composición mínima | ¿También se bloquea si suma % ≠ 100% (no solo composición)? La spec actual dice advisory | PO |
| 8 | Bajas largas (médica, maternidad) | Reasignar a otro asesor + backup a coord/responsable | Definir el backup exacto: ¿automático o manual? ¿coord o responsable? | PO |
| 12 | Baja asesor sin sucesor | Principio: tarea no se pierde, se escala | Persona/rol concreto de destino final cuando no hay sucesor | PO |
| 16 | UI vigente vs futuro (cómo mostrarlo) | Se discutió, hubo varias posturas | Decisión final de diseño — pendiente con Elena | Diseño + PO |
| 18 | Cambio de responsable en UI | No dejar equipo sin responsable, botón bloqueado | Detalle de modal/lateral pendiente con Elena | Diseño + PO |
| 19 | Consolidar reasignación si el destino ya tenía % | La idea: consolidar para no duplicar a la misma persona | Spec técnica del comportamiento exacto | Dev |
| 20 | Histórico — qué se guarda | Propuesta: snapshots por fecha + deducir cambios | Validar con Paula desde plataforma | Dev + Plataforma |

---

## ⏳ Pendientes (no se entraron)

| # | Pregunta | Razón | Próxima acción | Owner |
|---|---|---|---|---|
| 5 | Qué rol hace cada tarea (asesor / técnico / coord / responsable) | PO no lo tiene definido aún | Esperar a definición de producto antes de modelar `Obligation.roleResponsible` | PO (Producto) |
| 9 | Visibilidad de porcentajes en histórico por perfil | No se entró | Llevar como pregunta concreta en próxima sesión | PO |
| 10 | Cliente cancela servicio del dept con equipo activo | Solo se reconoció como anomalía futura | Diseño de vista de anomalías / supervisión | Dev + PO en futuro |
| 13 | Edición simultánea | No se entró | Confirmar la propuesta dev (FR-022: optimistic + aviso al segundo) | PO |
| 14 | Plataforma del Dato no disponible al guardar | No se entró | Llevar a próxima sesión técnica con Paula | Dev + Plataforma |
| 22 | TaxDown / subcontratados | Más adelante, depende de definición de obligaciones/servicios | Re-agendar cuando se aborde obligaciones | PO + Producto |
| 23 | Eliminar fecha fin explícita y calcularla desde la siguiente asignación | Idea aceptada pero no decidida | Revisar coste UX / dev antes de proponer cambio formal | Dev |
| 24 | Vista de anomalías (cliente con servicio sin equipo válido) | Reconocida como necesidad futura | Backlog | PO + Dev en iteración futura |

---

## ⚠️ Conflictos detectados con la spec actual

Decisiones del PO que **contradicen** lo que ya hay escrito en `spec.md` — hay que reconciliar:

| # | Conflicto | Decisión PO | Spec actual | Acción |
|---|---|---|---|---|
| C1 | **% solo para informes, no para asignación** | Los porcentajes NO se usan para repartir tareas | Clarification 2026-05-29 dice *"el asesor principal es el destinatario por defecto de tareas automáticas"* — esto sigue válido. Pero FR-029 dice *"aplicar % en dashboards para no contabilizar varias veces"* — esto es informes, así que OK. | Revisar redacciones que sugieran routing por % y aclarar que solo el `isPrimary` decide |
| C2 | **Validación bloqueante de composición mínima** | Botón guardar **deshabilitado** mientras falten roles obligatorios | FR-003 dice advisory: persistencia inmediata + estado `incomplete`. PO ahora dice bloqueo duro para composición mínima (responsable + 1+ asesor). | Distinguir 2 niveles: composición mínima = bloqueante (PO confirmado), suma 100% = advisory (no confirmado, decidir) |
| C3 | **Persona en más de un equipo en mismo periodo: prohibido** | La PO dijo *"una persona no puede ocupar simultáneamente más de un equipo/rol en el mismo intervalo temporal"* | Spec actual permite mismo empleado en equipos de departamentos distintos del mismo cliente (FR-016 + clarification 2026-06-01) | ⚠️ Ambigüedad real: ¿la PO se refería a no más de un rol en el mismo equipo (= FR-016) o a no en más de un equipo? Verificar con PO antes de codificar |
| C4 | **Bajas largas: backup coord/responsable** | Reasignación a otro asesor + si no, escala a coord/responsable | Spec no contempla escalado a coord/responsable, solo entre asesores | Añadir FR sobre cadena de fallback en bajas |

---

## Plan de acción inmediato (orden de prioridad)

1. **Aplicar al spec las ✅ Respondidas** — actualizar `## Open Questions for PO` cerrando D2, D3, D6, D9, D10 (parcial). Mover a `## Clarifications` con la decisión PO.
2. **Resolver los ⚠️ Conflictos** — sobre todo C3 (persona en más de un equipo) porque cambia el modelo de datos. Mandar mail/Slack a PO con la pregunta concreta antes de seguir.
3. **Capturar los nuevos hallazgos** (asignaciones múltiples, tareas que nunca se pierden, validación bloqueante composición mínima) como FRs adicionales.
4. Las 🟡 Parciales que dependen de Elena (UI vigente/futuro, cambio de responsable) → bloquear hasta sesión con diseño.
5. Las ⏳ Pendientes que dependen de Producto (#5 qué rol hace cada tarea, #22 TaxDown) → no bloquean el plan técnico del MVP siempre que asumamos default *"asesor principal hace todo"*. Documentar como assumption.

## Métricas de la reunión

- Preguntas llevadas: **14 explícitas + ~10 emergentes**
- Respondidas: **13** (52%)
- Parcial: **8** (32%)
- Pendiente: **8** (32%)
- Conflictos con spec previa: **4**

**Veredicto**: reunión productiva — cerró las decisiones operativas del MVP. Los conflictos son manejables. Lo único que bloquea de verdad el plan técnico es C3 (persona en multi-equipo) y la decisión final sobre composición mínima vs suma 100%.
