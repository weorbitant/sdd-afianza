# DEVPT-518 · Reunión PO · 14 preguntas

> Una línea por pregunta + nuestra propuesta. Si te paras → `challenge-report.md` para contexto.

## 🔴 Bloqueantes (sin estas no empezamos)

| # | Pregunta | Propuesta |
|---|---|---|
| **1** | El indicador del diseño dice *"Dedicación asesores 20%"* pero la regla actual es que asesores + técnicos suman 100% **juntos** | Cambiar el copy del diseño a *"Dedicación del equipo"*. No reabrir la regla |
| **2** | Empty state tiene dos CTAs distintos: *"Añadir persona"* (en *Mis clientes*) y *"Crear equipo"* (en *Mis tareas*) | Unificar ambos a *"Crear equipo"*, manteniendo los dos puntos de entrada |
| **3** | Cómo se llama un equipo (en frames hay *Libros*, *Cuota*, *Larsa*, *Costa*) — ¿texto libre, catálogo, o derivado del servicio contratado? | Híbrido: sugerir desde `ServiceCategory` del cliente, permitir texto libre |
| **4** | Onboarding desde Jira YA crea asignaciones automáticamente. ¿Cómo encaja con el nuevo modelo de equipo? | El sistema crea automáticamente *"Equipo inicial"* por departamento y mete dentro las asignaciones del onboarding. Responsable renombra después |
| **5** | ¿Qué rol del equipo hace cada tipo de tarea? Hoy todas van al asesor. ¿Y el técnico, coordinador, responsable? | **Sin recomendación — necesitamos tu regla de negocio**: por cada tipo de obligación, ¿qué rol la ejecuta por defecto? |

## 🟡 No bloqueantes (cerrar en la misma reunión si da tiempo)

| # | Pregunta | Propuesta |
|---|---|---|
| **6** | Icono papelera del modal: ¿borra o cierra asignación? | Cierra con fecha = hoy + diálogo inline *"¿Causa baja?"* |
| **7** | Equipos que se quedan "a medias" para siempre | Aceptar, banner amarillo, confiar en responsable |
| **8** | Bajas largas (médica, maternidad) | Sustitución manual. No construimos "suplencia temporal" ahora |
| **9** | ¿Qué porcentajes ve cada perfil en el histórico? | Todos lo ven todo (como dice US3). Reducir más tarde si hay fricción |
| **10** | Cliente cancela el servicio del departamento pero el equipo sigue activo | No cerrar auto. Banner persistente *"considera cerrar el equipo"* |
| **11** | Técnico promociona a asesor: ¿se edita el rol o se cierra y crea? | Cerrar con `endDate` = último día del mes + crear nuevo al día 1 del siguiente |

## 🟢 Heredadas (siguen vivas — revisar si han evolucionado)

| # | Pregunta | Estado |
|---|---|---|
| **12** | Baja de asesor sin sucesor designado: ¿bloquear cierre o bandeja sin asignar? | Provisional dev: bloquear hasta designar sucesor |
| **13** | Edición simultánea — ¿last-write-wins silencioso o aviso al segundo? | Ya aplicado como FR-022: aviso al segundo. Confirmar |
| **14** | Plataforma del Dato no disponible al guardar — ¿persistir y sync diferido o bloquear? | Pendiente |

---

## Cómo conducir la reunión

1. **Empieza por las 5 bloqueantes**. Si la PO va corta, prioriza **#3 (naming)**, **#4 (onboarding)** y **#5 (asignación de tareas)** — son las que más impactan al modelo de datos.
2. Para cada pregunta: si la PO dice *"vale a la propuesta"* → cierras. Si dice *"no me encaja"* → anotas la alternativa.
3. La **#5 no lleva recomendación**: pídele que enumere para cada `ObligationCategory` qué rol del equipo lo ejecuta (asesor/técnico/coordinador/responsable). Si responde *"depende del cliente"*, también vale como respuesta.
4. **#1, #2, #6** son cambios pequeños de UX — pueden ir rápidas.
5. **#13** ya está implementada en spec (FR-022) — solo confirma encaje, no abras debate.

## Después de la reunión

Por cada decisión cerrada, anota la letra/respuesta. Volvemos al spec y:
- Las que sean "vale a la propuesta" → marcamos `_Estado_: resuelto` en `## Open Questions for PO` y movemos a `## Clarifications` con la decisión.
- Las que abran nueva opción → la añadimos como FR o nueva Clarification.
- Las bloqueantes resueltas desbloquean US1 y US4 → ya se puede empezar `/speckit-plan`.
