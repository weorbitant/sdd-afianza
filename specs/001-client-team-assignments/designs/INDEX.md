# Designs Index — 001-client-team-assignments

Frames exportados manualmente desde Figma "Portal Asesor - Mis clientes" (file key `ra1egztv3K3yBTrWbHVacy`, página `Mis clientes`) el 2026-05-29 vía Claude-in-Chrome + Cmd+A + Exportar 47 capas.

23 frames de US1 organizados por **user journey** según el contenido observado. 6 frames off-topic (Servicios contratados, Mis clientes listing) bajo `_off-topic/`.

## 01-crear-equipo

El flow de crear el equipo desde cero. Empty state → modal lateral → primer responsable.

| Archivo | Qué muestra |
|---|---|
| `01-empty-state-mis-clientes-anadir-persona.png` | Empty state en pestaña "Datos de cliente" con header "Mis clientes". CTA `+ Añadir persona`. Copy: *"Empieza añadiendo un responsable, después un coordinador, asesores y técnicos. La suma de % de carga entre asesores y técnicos debe alcanzar el 100%."* |
| `02-empty-state-mis-tareas-crear-equipo.png` | Variante con header "Mis tareas" y CTA `+ Crear equipo`. |
| `03-modal-anadir-asignacion-vacio.png` | Modal lateral "Añadir nueva asignación" con campos vacíos: Tipo de rol / Buscar asesor / Fecha inicio / Fecha fin. Botón `+ Añadir rol`. |
| `04-modal-dropdown-tipo-rol.png` | Dropdown "Tipo de rol" abierto. Opciones: **Responsable, Coordinador, Asesor, Técnico** (en ese orden). |
| `05-modal-autocompletar-asesor.png` | Búsqueda de asesor con autocompletar: input "Alejan" muestra resultados (Alejandra Sánchez, Alejandra Sáiz, Alejandro Jiménez) cada uno con su departamento. |
| `06-modal-fecha-inicio-calendario.png` | Calendario mensual abierto sobre el campo "Fecha inicio". Año 2025 navegable. **Granularidad MES** (selección por mes, no por día). |
| `07-modal-responsable-listo.png` | Modal listo para crear: Tipo=Responsable, Asesor=Alejandro Jiménez, Fecha inicio=05/2026. |
| `08-tras-anadir-responsable.png` | Estado tras añadir: arriba del modal aparece *"Alejandro Jiménez · Responsable desde 13/5/2026"*. Modal vuelve a estado limpio para añadir siguiente miembro. Toast verde implícito (ver frame 12). |

## 02-anadir-asesor

Modal añadir asesor con el **slider de porcentaje** y la decisión clave de **asesor principal**.

| Archivo | Qué muestra |
|---|---|
| `01-modal-checkbox-asesor-principal.png` | 🔑 **Hallazgo crítico**: Modal con Tipo=Asesor, Empleado=Miriam Díaz. Checkbox visible: **`✓ Marcar como asesor principal`**. Slider "Porcentaje de **dedicación**" 0%-100%. Stats: `Ya asignado: 0%` · `Disponible: 100%` · `Total tras añadir: 100%`. |
| `02-modal-slider-porcentaje-20pct.png` | Slider movido a 20%. Stats: `Disponible 100%` · `Total tras añadir 20%`. |

## 03-fecha-fin-equipo

Mecanismo de fecha fin del equipo **incrustado dentro del modal de añadir asignación** (UX no documentada en spec).

| Archivo | Qué muestra |
|---|---|
| `01-modal-checkbox-fecha-fin-equipo.png` | 🔑 **Hallazgo crítico**: Con 2 miembros ya en el equipo (Responsable + Asesor [P]) aparece un checkbox **`☐ Marcar fecha fin de equipo`** *antes* del bloque "Tipo de rol". Sin marcar. |
| `02-modal-fecha-fin-marcada-05-2027.png` | Checkbox marcado, fecha 05/2027 introducida. Continúa permitiendo añadir más roles. |

## 04-anadir-coordinador-tecnico

| Archivo | Qué muestra |
|---|---|
| `01-modal-anadir-coordinador.png` | Modal con Tipo=Coordinador, Buscar empleado=Alba Romero. **Coordinador no muestra slider de porcentaje** (los management roles van sin %). Fecha fin equipo ya marcada 05/2027. |
| `02-modal-anadir-tecnico-slider-0pct.png` | Tipo=Técnico, Buscar empleado=Pablo Ríos. Slider de porcentaje SÍ aparece para técnico. Stats: `Disponible 100%` / `Total tras añadir 100%`. |
| `03-modal-cuarto-miembro.png` | Modal limpio para añadir 5º miembro con los 4 ya guardados arriba (Responsable, Asesor [P], Coordinador, Técnico). |

## 05-vista-equipo-incompleto

Estados donde el equipo aún no suma 100%. Banner amarillo informativo, **no bloqueante**.

| Archivo | Qué muestra |
|---|---|
| `01-equipo-incompleto-banner-warning-20pct.png` | Vista compacta con barra "Dedicación asesores 20% · Faltan 80% por asignar · 1 responsable · 0 coord. · 1 ases. · 0 téc.". Banner ⚠️ *"No hay establecido un 100% de carga en las asignaciones."* Toast verde en esquina inferior derecha: *"Asignaciones creadas correctamente."* 🔑 Confirma persistencia inmediata + banner advisory. |
| `02-equipo-4-miembros-incompleto.png` | Misma vista con 4 miembros pero ahora SIN barras de dedicación visibles arriba (¿bug del diseño?). Lista: Responsable + Coordinador + Asesor [P] 20% + Técnico 100%. |

## 06-vista-equipo-completo

Equipo válido al 100%. **No hay barras de Asesores 100% / Técnicos 100% en estos frames del rediseño** — diferencia respecto al legacy.

| Archivo | Qué muestra |
|---|---|
| `01-equipo-completo-2-asesores-1-tecnico.png` | Equipo Fiscal: Responsable Alejandro · Coordinador Alba · Asesor Miriam 40% [P] + Asesor Nuria 60% · Técnico Pablo 100%. CTA `+ Añadir equipo` arriba derecha. Sin banner, sin barras. |
| `02-equipo-completo-fechas-historicas.png` | Mismo equipo con fechas de antigüedad variadas (Responsable desde 02/2025, Coordinador desde 05/2024, Técnico desde 06/2024). 🔑 Sugiere que el equipo **se compone de asignaciones con diferentes fechas de inicio individuales**. |

## 07-historico

| Archivo | Qué muestra |
|---|---|
| `01-panel-historico-cambios-timeline.png` | 🔑 **Hallazgo nuevo**: Panel lateral derecho "Histórico de cambios - Asignaciones" con timeline cronológico. Cada entrada muestra: fecha + composición del equipo en ese momento (Responsable, Coordinador, Asesor, Técnico). Útil para US3. |

## 08-multi-equipo

🔑 **Hallazgo gordo del rediseño**: equipos con NOMBRES (Libros, Cuota, Larsa, Costa) y **varios equipos activos por departamento**.

| Archivo | Qué muestra |
|---|---|
| `01-multi-equipo-fiscal-larsa-costa.png` | Fiscal con dos equipos: `Equipo 1` (Larsa) y `Equipo 2` (Costa) listados expandidos. Cada uno con su Responsable, Coordinador, Asesor, Técnico. Departamento Laboral aparece colapsado abajo. |
| `02-vista-compacta-libros-cuota.png` | Vista compacta una línea por equipo: `Equipo Libros - Responsable X | Coordinador Y | Asesor Z | Técnico W` + `Equipo Cuota - ...`. Etiqueta `Activo` y *"hasta 05/2027"* a la derecha. |
| `03-multi-equipo-multi-departamento.png` | Vista expandida completa: Fiscal con Equipo 1 (Larsa) + Equipo 2 (Costa) + Laboral con su equipo único. |

## Hallazgos consolidados (vs spec / ADRs)

| # | Evidencia visual | Spec / ADR afectado |
|---|---|---|
| 1 | Sin botón "Confirmar equipo" en ningún frame. Toast *"Asignaciones creadas correctamente"* tras cada add (frame `05/01`). | ADR-0007 (draft + commit) ⚠️ inválido |
| 2 | Barras separadas `Asesores 100%` + `Técnicos 100%` en legacy frames 16-17. En rediseño actual desaparecen pero el copy del empty state sigue diciendo *"la suma de % de carga entre asesores y técnicos debe alcanzar el 100%"* — single bucket. | ADR-0008 / dos cubos no resuelto definitivamente — confirmar con PO |
| 3 | Checkbox **"Marcar como asesor principal"** en modal + badge `P` / `Principal` en lista. | Falta campo `is_primary` en data-model + FR nueva |
| 4 | Frames `08/01`, `08/03`: Equipo 1 + Equipo 2 ambos activos en Fiscal con `hasta 05/2027 Activo`. | ADR-0003 (one active team per client+dept) ⚠️ inválido |
| 5 | Slider `Porcentaje de dedicación` 0-100 + stats `Ya asignado` / `Disponible` / `Total tras añadir`. | UI spec ausente — añadir FR |
| 6 | Checkbox **"Marcar fecha fin de equipo"** dentro del modal de añadir asignación (no en endpoint separado). | UX no documentada — afecta a US4 (cierre de equipo) |
| 7 | Equipos con NOMBRES propios (Libros, Cuota, Larsa, Costa). | Falta campo `name` en `ClientTeam` |
| 8 | Calendario `Fecha inicio` solo permite seleccionar MES (no día). | Confirma granularidad mes (ya en spec) ✓ |
| 9 | "Coordinador" no muestra slider de porcentaje en modal — solo Asesor y Técnico. | Confirma single-bucket excluye management roles ✓ ADR-0008 parcial |
| 10 | Tab activa es "Datos de cliente" en algunos frames y "Mis tareas" en otros. La sección "Asignaciones actuales" aparece en ambas. | Posible inconsistencia — ¿es una nueva tab "Asignaciones" o se integra en "Datos de cliente"? |

## Off-topic (`_off-topic/`)

6 frames de páginas no-US1: "PortalAsesor - Mis clientes" (listing externo) y 5 "PortalAsesor - Servicios contratados". Conservados por contexto pero no entran en el alcance de US1.
