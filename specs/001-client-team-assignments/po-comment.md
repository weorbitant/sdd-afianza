# Refinamiento DEVPT-518 — preguntas para PO

Spec restaurada al estado maduro de 2026-05-29 (con 4 rondas previas de clarify + challenge) más los hallazgos del 2026-06-01 sobre flujos cross-service y restricciones.

## Preguntas abiertas para PO

Las preguntas viven en el spec en `## Open Questions — Pending PO Decision`. Resumen rápido:

### Heredadas de iteraciones anteriores (ya en spec)

- **OQ-001** · Si un asesor causa baja sin sucesor designado, ¿qué pasa con sus tareas pendientes? *(provisional FR-010: bloquear cierre hasta designar sucesor)*
- **OQ-003** · Edición simultánea — ¿last-write-wins silencioso o aviso al segundo editor? *(propuesta dev: optimistic con `updatedAt` — ya recogida en FR-022 nuevo, pero validar con PO si encaja)*
- **OQ-004** · Si Plataforma del Dato no está disponible al guardar, ¿se persiste el cambio igualmente con sync diferido o se bloquea el guardado?

### Bloque del challenge funcional 2026-05-28 (ya en spec)

- **business-B1** · Asesor causa baja en Azure AD sin que el responsable haya cerrado el equipo antes — comportamiento del sistema. *(propuesta dev: marcar asignaciones cerradas + alerta a responsable)*
- **business-B2** · Empleado cambia de departamento internamente — qué pasa con sus asignaciones del departamento de origen.
- (resto en `challenge-report.md`)

### Nuevas del 2026-06-01 (apuntes de hoy)

- **OQ-006** · **Nombre del equipo** (FR-005): ¿es texto libre, catálogo administrado, o **derivado de `ProvidedService.category`**? Los nombres `Libros` y `Cuota` que aparecen en los frames coinciden con valores reales de `ServiceCategory` — sugiere que `ClientTeam` podría enlazarse a uno o varios `ProvidedService` del cliente y heredar el nombre. Si se confirma esto, el modelo de datos cambia (FK `ClientTeam → ProvidedService`).
- **OQ-007** · **UX papelera del modal**: junto a cada miembro ya añadido hay un icono papelera. Las reglas de cierre y causa baja están en FR-010, pero falta decidir la superficie UX — ¿diálogo inline en el mismo modal, pantalla aparte dedicada al cierre, o híbrido?
- **OQ-008** · **Equipos huérfanos por baja de servicios**: FR-017 bloquea la **creación** de equipos en departamentos sin servicios contratados activos. ¿Y los equipos existentes cuando se da de baja el último servicio del departamento? ¿Se cierran auto o permanecen vivos hasta su fecha fin natural?

## Decisiones nuevas que NO necesitan PO (dev las cierra)

Aplicadas como FR nuevos sobre la spec restaurada:

- **FR-016**: un empleado = un único rol por equipo.
- **FR-017**: pre-condición `ProvidedService` activo del cliente para crear equipo (UI + backend).
- **FR-018..FR-021**: alineación cross-service (mensaje AMQP `client-assignment` ampliado con `teamId`+`teamName`+`percentage`; modelo de `data-factory` alineado; unique constraint con `team_id`; sync de `jira-adapter` solo del equipo principal).
- **FR-022**: optimistic concurrency con `updatedAt` (recomendación para OQ-003).

## Cómo usar este documento

1. Lleva las 8 OQ pendientes (3 viejas + 5 nuevas/del challenge) a la sesión con la PO.
2. Las **3 nuevas (OQ-006/007/008)** son las que descubrimos hoy y son las únicas que el PO no ha visto antes.
3. Las decisiones se aplican al spec actualizando `## Clarifications` con una nueva Session.
