# Decisiones pendientes — Asignaciones Múltiples en Ficha de Cliente

**Para**: PO  ·  **Generado**: 2026-06-01  ·  **Modo**: functional

## En una frase

Tenemos **11 decisiones de negocio** que necesitamos resolver contigo antes de construir, más 2 aclaraciones que el equipo cerrará por su cuenta.

## Riesgo por historia

| Historia | Decisiones | Aclaraciones | ¿Se puede empezar? |
|----------|-----------|--------------|---------------------|
| US1 — Crear y gestionar el equipo de un cliente | D1, D2, D3, D4, D5, D6, D9, D10 | G1, G2 | **No — bloqueada hasta resolver D1, D2, D6, D10** |
| US2 — Distribución de carga por porcentaje | — | G1 | Sí |
| US3 — Histórico de cambios de asignación | D7 | — | Sí, con matices |
| US4 — Cierre de equipo | D3, D4, D5, D8, D9, D11 | — | **No — bloqueada hasta resolver D11** |
| cross-cutting | D10, D11 | — | — |

## Qué necesitamos de ti

- **11 decisiones** marcadas como `D1..D11` abajo. Cada una incluye escenario, opciones (cuando aplica), trade-offs y nuestra recomendación.
- Cada decisión se publicará como un comentario individual en la Epic de Jira al ejecutar `/speckit-atlassian-sync-push`. Puedes responder ahí mismo con la letra elegida.
- **2 aclaraciones** (`G1, G2`) que cerraremos sin tu intervención salvo que veas algo raro — sección *Aclaraciones* más abajo.

---

## Decisiones

### D1 — El indicador del equipo solo mide a los asesores

**Afecta a**: US1 (Crear y gestionar el equipo de un cliente)
**¿Bloquea empezar?**: Sí — US1

#### Escenario
En la vista del equipo aparece una sola barra que dice literalmente *"Dedicación asesores 20%"* y un contador *"Faltan 80% por asignar"*. Sin embargo, la regla escrita dice que asesores y técnicos suman juntos hasta 100%. Hoy podrían convivir lecturas distintas según quién mire la pantalla.

#### Por qué te preguntamos
Si el indicador real es "solo asesores" y técnicos van por separado, cambia la regla central de la feature y los informes de rentabilidad. Si el copy está mal y de verdad es un único cubo, hay que reescribir la etiqueta antes de salir.

#### Recomendación del equipo: A
La decisión de un solo cubo está ratificada en ADR-0008 y simplifica todo (validación, evento, informes). Lo único que sobra es el copy *"Dedicación asesores"* del diseño: cambiarlo cierra la inconsistencia sin reabrir nada.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Mantener un único cubo (asesores+técnicos = 100%) y corregir el copy de la barra a *"Dedicación del equipo"*. | Hay que reabrir el diseño para retocar etiquetas; el resto de la lógica no cambia. |
| B | Volver a dos cubos independientes: asesores 100% y técnicos 100%, cada uno con su propia barra. | Invalida la decisión madura del 28/05 y el ADR-0008; rehace validaciones backend y modelo de evento. |
| C | Mantener un único cubo pero mostrar dos barras informativas (asesores / técnicos) que solo suman para el badge global. | Más complejo de leer; multiplica la lógica de UI sin cambiar la regla de negocio. |

---

### D2 — Dos puntos de entrada distintos para crear el equipo

**Afecta a**: US1
**¿Bloquea empezar?**: Sí — US1

#### Escenario
El responsable abre la ficha de un cliente y, según desde dónde haya llegado, ve dos pantallas diferentes para empezar: una pone *"Añadir persona"* bajo *"Mis clientes"* y otra *"Crear equipo"* bajo *"Mis tareas"*. Ambas parecen iniciar el mismo flujo pero el botón se llama distinto.

#### Por qué te preguntamos
Sin aclarar, los responsables se confunden (*"¿desde dónde se crea?"*) y soporte recibe consultas duplicadas. Además, si solo una entrada está implementada, gente que entra por la otra cree que la feature no está activa.

#### Recomendación del equipo: A
Tener dos entradas suma flexibilidad para los responsables, pero llamarlas distinto induce dudas. Un solo nombre (*"Crear equipo"*) alinea ambos puntos sin cerrar accesos.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Unificar el CTA a *"Crear equipo"* en ambas vistas, manteniendo los dos puntos de entrada al mismo modal. | Hay que retocar diseño y copy de *"Mis clientes"* para alinear. |
| B | Dejar el empty state solo en *"Datos de cliente"* / *"Mis clientes"* y quitarlo de *"Mis tareas"*. | Quien vive en *"Mis tareas"* tiene que cambiar de sección para crear el equipo. |
| C | Permitir ambos puntos de entrada con su copy actual, asumiendo que conviven. | Mantiene la inconsistencia textual; soporte tendrá que explicar la equivalencia. |

---

### D3 — Qué hace la papelera junto a cada miembro del equipo

**Afecta a**: US1
**Relacionada con**: OQ-007

#### Escenario
Una vez que el responsable añade gente al equipo, junto a cada miembro aparece un icono de papelera. Hoy no está claro si pulsarla borra al miembro como si nunca hubiera estado o cierra su asignación con la fecha de hoy y deja huella en el histórico.

#### Por qué te preguntamos
Si la papelera borra sin dejar rastro, el histórico (US3) deja de ser fiable y se pueden perder porcentajes pagados a un asesor. Si cierra con fecha fin, hace falta decidir cuándo se pregunta por `causesBaja` y por el sucesor de las tareas (FR-010).

#### Recomendación del equipo: A
Cerrar siempre con `endDate` preserva el histórico de US3 sin excepciones. El diálogo inline mantiene la operación dentro del mismo modal y evita una pantalla nueva.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | La papelera cierra la asignación con `endDate` = hoy y abre un diálogo inline preguntando *"¿Causa baja?"* y sucesor si procede. | Más pasos por miembro, pero conserva trazabilidad y respeta FR-010. |
| B | La papelera solo borra miembros añadidos en la misma sesión que aún no se han propagado; los ya activos se cierran desde otra acción. | Lógica condicional poco descubrible: el mismo icono hace cosas distintas según el estado del miembro. |
| C | La papelera abre una pantalla / modal dedicado de cierre con campos extensos (fecha, motivo, sucesor, `causesBaja`). | Más superficie a diseñar y construir; rompe la fluidez del modal lateral. |

---

### D4 — Equipos a medias que se quedan así para siempre

**Afecta a**: US1, US4

#### Escenario
Un responsable empieza a montar el equipo de un cliente, añade un par de miembros, suma 60% y se va a otra cosa. El equipo queda en estado *"incompleto"* con un banner amarillo. Nadie le recuerda nada y la rentabilidad de ese cliente deja de propagarse a los informes.

#### Por qué te preguntamos
La empresa pierde datos de rentabilidad mientras el equipo siga incompleto. Si el responsable se olvida (vacaciones, baja, salida), nadie reclama y el cliente queda fuera de los cuadros de mando hasta que alguien lo descubre.

#### Recomendación del equipo: A
Mantener la decisión actual evita ampliar el alcance. Si en producción aparecen olvidos reales, lo medimos y añadimos visibilidad en una iteración siguiente. La opción B sería ideal pero requiere construir un widget que hoy no está en el plan.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | No imponer límite: el banner advisory es suficiente y el responsable es quien decide cuándo cerrar el 100%. | Riesgo real de equipos olvidados durante semanas; informes infrarrepresentados. |
| B 🏗 | Mostrar un listado/contador de equipos incompletos en la home de cada responsable para visibilidad operativa. | Requiere un widget nuevo en la home — fuera del alcance del FR-015 (solo ficha de cliente). |
| C | Bloquear la creación de un nuevo equipo en el mismo cliente+departamento mientras haya otro en estado `incomplete`. | Evita olvidos pero puede frustrar a equipos grandes que necesiten varios borradores en paralelo. |

> Leyenda: ⭐ recomendada por el equipo · 🏗 requiere construir infraestructura que no existe hoy.

---

### D5 — Bajas temporales prolongadas (enfermedad, maternidad)

**Afecta a**: US1, US4

#### Escenario
Un asesor del equipo entra en baja médica de larga duración. Sigue figurando como miembro activo del equipo al 40%, las tareas le siguen llegando, y nadie las atiende durante semanas. Cuando vuelve, encuentra una cola enorme o el cliente ya se ha quejado.

#### Por qué te preguntamos
El cliente queda mal atendido durante la baja y no hay registro de quién está realmente cubriendo el hueco. En facturación, el porcentaje que cobra ese asesor durante la baja queda en zona gris.

#### Recomendación del equipo: A
La opción B es la correcta a futuro pero requiere construir entidad y UI nuevas (suplencias) que no están en el plan. Lo pragmático es operar con cierres manuales y aceptar la fricción hasta que tengamos datos reales de cuántas bajas largas hay al año.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Sustituir manualmente: el responsable cierra la asignación del asesor de baja y añade otro al equipo durante la ausencia, sin un flujo específico. | Cuando el asesor vuelve, hay que volver a montar el equipo a mano; depende de que el responsable se acuerde. |
| B 🏗 | Añadir el concepto de *"suplencia temporal"* a `TeamMember` (fecha inicio/fin suplencia, sustituto), sin alterar el porcentaje del titular. | Requiere construir un modelo de suplencias nuevo — entidad y UI propias; fuera del alcance actual. |
| C | No tratar el caso en esta entrega y documentarlo como gap conocido para una iteración posterior. | Las bajas largas seguirán ocurriendo y se gestionan a mano sin trazabilidad estructurada. |

> Leyenda: ⭐ recomendada por el equipo · 🏗 requiere construir infraestructura que no existe hoy.

---

### D6 — De dónde sale el nombre del equipo (Libros, Cuota, Larsa…)

**Afecta a**: US1
**¿Bloquea empezar?**: Sí — US1
**Relacionada con**: OQ-006

#### Escenario
En el rediseño multi-equipo aparecen equipos llamados *"Libros"*, *"Cuota"*, *"Larsa"* y *"Costa"*. *"Libros"* y *"Cuota"* coinciden con categorías reales de servicio contratado. *"Larsa"* y *"Costa"* parecen apellidos o marcas. Hoy no está claro si el responsable escribe el nombre a mano o lo elige de una lista cerrada.

#### Por qué te preguntamos
Si es texto libre, dos responsables pueden llamar *"Cuota"* y *"cuota mensual"* al mismo equipo, los informes no agruparán. Si es lista cerrada de `ServiceCategory`, hay que crear vínculo `ClientTeam → ProvidedService` y limita qué equipos puede crear el responsable.

#### Recomendación del equipo: C
Los frames muestran ambos tipos de nombre (categoría y apellido), así que la realidad es híbrida. Sugerir desde categoría limpia el caso común; permitir texto libre cubre los casos especiales como Larsa/Costa.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A | Texto libre con validación de unicidad por cliente+departamento, sin vínculo a `ProvidedService`. | Máxima flexibilidad pero datos sucios; no se puede agrupar *"equipos de Libros"* entre clientes. |
| B | Lista cerrada derivada de `ServiceCategory` del cliente: el responsable elige entre los servicios contratados activos. | Modelo limpio y consistente, pero no encaja con nombres tipo *"Larsa"*/*"Costa"* que no son categorías. |
| C ⭐ | Híbrido: sugerencia desde `ServiceCategory` con opción a texto libre cuando ninguna categoría aplica. | Más complejo de construir; la sugerencia puede confundir si el responsable la ignora siempre. |

---

### D7 — Qué porcentajes ve cada perfil en el histórico

**Afecta a**: US3 (Histórico de cambios de asignación)

#### Escenario
Un asesor entra a la ficha de un cliente que comparte con otros dos asesores y abre el histórico. Hoy la spec dice que cualquier perfil con acceso a la ficha ve el histórico completo — eso incluye que vea qué porcentaje tienen sus compañeros, lo cual se traduce indirectamente en cuánto cobra cada uno por ese cliente.

#### Por qué te preguntamos
Hay sensibilidad alrededor de la rentabilidad y reparto de carga entre asesores. Si se expone sin filtrar, se generan conversaciones internas incómodas. Por otro lado, ocultar porcentajes al asesor le impide entender su propia carga.

#### Recomendación del equipo: A
Es la opción ya descrita en US3 y la más simple de construir. Si en producción surge fricción por exposición de porcentajes, se reduce visibilidad en una iteración siguiente sin romper datos.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Histórico completo y porcentajes visibles para todos los perfiles con acceso a la ficha. | Transparencia total dentro del equipo, asumiendo conversaciones internas posibles. |
| B | El asesor solo ve sus propias entradas y porcentajes; responsable/coordinador ven todo el equipo. | Más complejo de filtrar; el asesor pierde contexto del reparto global del cliente. |
| C | Todos ven la composición y miembros, pero los porcentajes solo se muestran a responsable/coordinador. | Histórico parcial; el asesor sabe quién está pero no cómo se reparte. |

---

### D8 — Equipo activo en un departamento que el cliente ya no contrata

**Afecta a**: US1, US4
**Relacionada con**: OQ-008

#### Escenario
Un cliente cancela el servicio Laboral pero sigue con Fiscal. El equipo de Laboral, con sus dos asesores y técnico, sigue marcado como *"activo"* en la ficha. Aparece en informes y los asesores siguen contando ese cliente en su carga, aunque ya no haya trabajo real que hacer.

#### Por qué te preguntamos
Los porcentajes del equipo huérfano siguen alimentando rentabilidad e informes en Plataforma del Dato, distorsionando métricas. Además, los asesores ven al cliente en su *"Mis Clientes"* (cuando se actualice) sin entender por qué.

#### Recomendación del equipo: B
El cierre automático evita huérfanos pero quita control al responsable y depende de un consumer reactivo a eventos de baja de servicio que hoy no está construido. El banner es feasible con lo que hay y deja la decisión en quien conoce al cliente.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A | El sistema cierra automáticamente el equipo cuando se da de baja el último `ProvidedService` activo de ese departamento, fecha = fecha de baja del servicio. | Automatismo que el responsable no controla; si la baja del servicio se hizo por error hay que crear equipo nuevo. |
| B ⭐ | El sistema no cierra el equipo pero muestra banner persistente en la ficha *"Cliente sin servicios activos en este departamento — considera cerrar el equipo"*. | El cierre depende de que un humano vea el banner; durante el delay los informes están sesgados. |
| C | No tratar el caso en esta entrega: el equipo queda activo y se confía en el responsable. | Acumula deuda; sabemos que pasará y elegimos ignorarlo. |

---

### D9 — Cambio de rol del empleado (técnico pasa a asesor)

**Afecta a**: US1, US4

#### Escenario
Pablo Ríos es técnico en el equipo Fiscal de un cliente al 100%. Se le promociona a asesor. El responsable necesita reflejarlo. Hoy no sabemos si Pablo se queda en el mismo equipo cambiando su etiqueta (con su porcentaje intacto), o si se cierra su asignación de técnico y se crea una nueva como asesor desde cero.

#### Por qué te preguntamos
Si se *"edita"* el rol in situ, el histórico pierde el momento del cambio y la rentabilidad de los meses anteriores queda atribuida erróneamente al rol nuevo. Si se cierra y se vuelve a crear, hay un día sin cobertura técnica formal — viola FR-011 si no se sustituye.

#### Recomendación del equipo: A
Mantiene la trazabilidad del cambio en el histórico (cumple US3) y respeta la granularidad mensual de FR-012, que es la base del cálculo de rentabilidad.

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A ⭐ | Cerrar la asignación actual con `endDate` = último día del mes anterior y crear una nueva con el nuevo rol al día 1 del mes siguiente. | Hay un mes de transición que requiere coordinación; respeta granularidad mensual. |
| B | Editar el rol en el mismo `TeamMember` manteniendo `id`, `startDate` y `percentage`. | El histórico no refleja el cambio; reporting atribuye mal los meses anteriores. |
| C | Cerrar y crear el mismo día sin gap: dos filas en histórico con la transición clara. | Rompe la convención de granularidad mensual (FR-012). |

---

### D10 — Cómo encajan las asignaciones que llegan por onboarding desde Jira en el nuevo modelo multi-equipo

**Afecta a**: US1, cross-cutting (todas las historias)
**¿Bloquea empezar?**: Sí — US1

#### Escenario
Hoy hay un flujo automático que crea asignaciones sin que el responsable haga nada: cuando un cliente se da de alta en Jira y se procesa el onboarding, `pgi-service-pgi-api` recibe el evento `client_onboarding_persisted` y crea filas de `client_assignment` automáticamente (responsable, coordinador, asesor, técnico) con `actor = "system:onboarding"`. Esto lleva meses en producción y la spec actual no lo menciona — incluso decía "UI es la única ruta de escritura", que era incorrecto. Cuando esta feature añada `team_id` y multi-equipo, hay que decidir cómo se comportan las asignaciones que entran por onboarding sin saber nada de equipos.

#### Por qué te preguntamos
Si no se decide, el onboarding seguirá creando filas con `team_id = NULL` y aparecerán asignaciones huérfanas en la ficha del cliente. El responsable verá *"hay un asesor asignado pero no está en ningún equipo"* y tendrá que reagruparlas a mano cada vez que se da de alta un cliente nuevo. Tampoco está claro si el onboarding debe respetar la pre-condición de `ProvidedService` (D8 / FR-017) o si tiene barra libre por ser un sistema interno.

#### Recomendación del equipo: C
Crear automáticamente un *"Equipo inicial"* por cliente+departamento dentro del propio `applyFromClientOnboarding` y meter ahí las asignaciones del onboarding. Sin tocar el contrato del evento ni al productor (data-factory). El responsable luego renombra el equipo si quiere usar nombre real (D6).

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| A | Dejar el onboarding como está: crea filas con `team_id = NULL`. El responsable abre la ficha y agrupa manualmente las asignaciones en un equipo. | Cero cambios en código consumer, pero cada alta de cliente nuevo genera trabajo manual para el responsable y rompe la regla de "todo miembro pertenece a un team". |
| B 🏗 | Ampliar el contrato del evento `client_onboarding_persisted` para que el productor (data-factory / Jira flow) envíe ya `teamName`/`teamId` y el consumer cree el team explícitamente con esos datos. | Requiere coordinar con plataforma del dato + el flujo Jira que origina el onboarding. Cambio cross-team que no está en el alcance de esta épica. |
| C ⭐ | El consumer `applyFromClientOnboarding` crea automáticamente un `ClientTeam` con nombre por defecto (*"Equipo inicial"* o el `ServiceCategory` del servicio si está disponible en el mensaje) por cada cliente+departamento, y mete dentro las asignaciones del onboarding. El responsable puede renombrar después. | Aísla el cambio dentro de pgi-api; no toca contratos. Si llega un cliente con dos servicios del mismo departamento (Libros+Cuota), se crea un único *"Equipo inicial"* que mezcla ambos — el responsable lo separa después si quiere. |

> Leyenda: ⭐ recomendada por el equipo · 🏗 requiere construir infraestructura que no existe hoy.

---

### D11 — Política de asignación de tareas: ¿qué rol del equipo hace cada tipo de tarea?

**Afecta a**: US4, cross-cutting (todas las historias que tocan generación/reparto de tareas)
**¿Bloquea empezar?**: Sí — US4
**Tipo**: pregunta abierta — pedimos la regla de negocio antes de proponer opciones técnicas

#### Escenario
Hoy el modelo `Task` en `pd-service-obligations-api` tiene un único campo de asignación: `advisor: Employee`. Es decir, **todas las tareas que el sistema genera (IVA, IS, libros, cuentas, presentaciones, etc.) van a un asesor — sin distinción de rol**. La `Obligation` tampoco tiene un campo que diga "esta obligación la hace el técnico, no el asesor".

La spec actual responde solo el caso fácil: nuevas tareas auto → asesor principal del equipo. Pero no responde a las preguntas reales que aparecen cuando el equipo tiene varios roles:

- Si una obligación históricamente la hacía el **técnico** (ej. contabilización de libros, cierres mensuales), ¿en el nuevo modelo se sigue asignando al asesor principal o pasa al técnico del equipo?
- ¿El **coordinador** recibe tareas o sólo gestiona?
- ¿El **responsable** recibe tareas o sólo supervisa?
- Si hay **2 asesores y 1 técnico**, ¿qué obligaciones van a cada uno?
- Si hay **2 técnicos en el equipo**, ¿concepto de "técnico principal" análogo al "asesor principal"? Hoy no existe.

#### Por qué te preguntamos
Sin esta política definida, el plan técnico no puede saber:
1. Si la entidad `Task` necesita más de un campo de asignación (uno por rol) o sigue con sólo `advisor`.
2. Si `Obligation` necesita un campo `roleResponsible` (asesor / técnico / coordinador / responsable) que dispare el routing al miembro adecuado del equipo.
3. Si necesitamos extender el concepto "asesor principal" a "técnico principal" / "coordinador principal" / "responsable principal" (y por tanto tocar `TeamMember` con más booleans `isPrimary` por rol).
4. Cómo se reparten obligaciones automáticas cuando hay multi-asesor y multi-técnico simultáneamente.

#### Lo que pedimos
**No te damos opciones cerradas porque cualquiera que propongamos llevará nuestro sesgo técnico**. Necesitamos primero entender la regla de negocio real:

> *"Para cada tipo de obligación que el sistema genera automáticamente (lista en `Obligation.category` / `Obligation.type`): ¿qué rol del equipo es responsable de ejecutarla por defecto?"*

Si hay categorías donde la respuesta es *"depende"* (a veces el asesor, a veces el técnico, según el cliente), dilo — eso ya nos define que necesitamos override por cliente.

Con tu respuesta el equipo redacta opciones técnicas concretas en una segunda iteración.

#### Datos de contexto (para que respondas con base, no a ciegas)
- Hoy el sistema genera tareas con campo único `advisor`. El cambio que propongas tiene impacto en data-factory + obligations-api + pgi-api.
- En el código aparecen los conceptos `ObligationCategory` y `ObligationType` como enums cerrados — si quieres, te paso la lista exacta de valores en cuanto los necesites para responder.
- El concepto "asesor principal" del equipo ya existe (`TeamMember.isPrimary` cuando `role: asesor`). Análogos para técnico/coordinador/responsable no existen y habría que crearlos si la respuesta los requiere.

---

## Aclaraciones que cerrará el equipo

Estas son ambigüedades que la spec olvidó formalizar pero que tienen respuesta clara. El equipo las añadirá al spec sin necesitar tu input. **Solo léelas si quieres saber qué decidiremos** — si discrepas con alguna, díselo al tech lead y la elevamos a decisión tuya.

### G1 — Porcentaje mínimo de un miembro del equipo

**Afecta a**: US1, US2

Añadir AC explícita: el porcentaje mínimo aceptado para un miembro del equipo (asesor o técnico) es **1%**. El slider de UI debe bloquear el rango 0% (mostrar mensaje *"El porcentaje mínimo es 1%"*) y el backend rechazar `percentage < 1` con HTTP 400. Documentar también el máximo (100%) y la granularidad (enteros) en el mismo FR-002.

---

### G2 — Cierre de equipo en estado incompleto

**Afecta a**: US1

Añadir AC explícita: la opción *"Marcar fecha fin de equipo"* solo está habilitada cuando el equipo está en estado `active`. En estado `incomplete`, el checkbox aparece deshabilitado con tooltip *"Completa el equipo antes de cerrarlo"*. Alternativa: permitir cerrar en estado `incomplete` pero con confirmación adicional explícita (*"Vas a cerrar un equipo que nunca llegó a estar completo — su rentabilidad no se ha propagado a informes"*). Decidir cuál de las dos antes de implementar.

---

## Anexo técnico — para el equipo

Esta sección no es para el PO.

### Resumen por severidad

| Severidad     | Cuántos |
|---------------|---------|
| BLOCKER       | 6       |
| ADR           | 2       |
| QUESTION-PO   | 12      |
| BUSINESS-GAP  | 2       |
| NIT           | 0       |

### Hallazgos técnicos

Generados por `/speckit-challenge technical` (2026-06-01). 10 findings de `feasibility-reviewer`. 5 BLOCKERs **bloquean `/speckit-tasks`** hasta resolverse.

#### T1 — BLOCKER — constraint-enforcement

**Afecta a**: cross-cutting
**Location**: `data-model.md#clientassignment`
**Reviewer ID**: `feasibility-F1`

**Evidence**:
> "NUEVO partial unique: (client_id, employee_id) WHERE date_to IS NULL ... una persona puede tener máximo UNA asignación activa al mismo cliente"

**Gap**: El nuevo partial unique colisiona con `applyFromClientOnboarding`, que usa `em.upsert(ClientAssignment, ...)` con la business key existente `(client, employee, role, department, dateFrom)`. El onboarding puede emitir legítimamente una segunda fila activa para el mismo `(client, employee)` cuando cambia el rol — el partial unique lanzará excepción y FR-017 empezará a fallar en el momento que aterrice la migración M1, antes de que D10 se resuelva.

**Suggestion**: O bloquear el partial unique detrás de la resolución de D10, o cambiar el onboarding para que cierre la fila activa existente (poner `date_to`) antes de insertar la nueva, dentro de la misma transacción. Documentar el camino elegido en un ADR + añadir test de regresión en `client-subscriber.spec.ts`.

---

#### T2 — BLOCKER — constraint-enforcement

**Afecta a**: US1, US2
**Location**: `data-model.md#clientassignment`
**Reviewer ID**: `feasibility-F2`

**Evidence**:
> "isPrimaryAdvisor = true solo permitido si role = asesor (CHECK BD ayuda pero validación servicio da mensaje claro)"

**Gap**: El texto dice que un CHECK de BD "ayuda" pero NO está declarado en la migración M1. Igual para `causes_baja` solo significativo cuando `date_to IS NOT NULL`. Un bug en el servicio o una migración futura puede poner `is_primary_advisor=true` en una fila coordinador/técnico, y el partial unique `(client_id, department) WHERE is_primary_advisor=true AND date_to IS NULL` tratará silenciosamente esa fila incorrecta como la principal, rompiendo el sync de jira-adapter (FR-020).

**Suggestion**: Añadir `CHECK (is_primary_advisor = false OR role = 'asesor')` y `CHECK (causes_baja = false OR date_to IS NOT NULL)` en la migración M1 + decoradores MikroORM.

---

#### T3 — BLOCKER — entity-granularity

**Afecta a**: US4
**Location**: `spec.md:L199-L203`
**Reviewer ID**: `feasibility-F3`

**Evidence**:
> "Si un asesor causa baja en la empresa ... el sistema reasigna automáticamente sus tareas abiertas al asesor sucesor definido para ese cliente. Si no hay sucesor definido, el sistema bloquea el cierre"

**Gap**: FR-010 promete bloquear el cierre cuando no hay "sucesor definido para ese cliente", pero NO hay entidad, columna ni relación en data-model.md que almacene qué empleado es el sucesor designado para un cliente. El contrato PATCH/DELETE acepta `successorId` en el body pero no dice dónde vive el sucesor "por defecto" — implicando que debe inferirse de filas existentes, pero D9 (inferencia temporal) no está formalizada en el esquema.

**Suggestion**: O añadir columna `successor_employee_id` en `ClientAssignment` (o tabla `client_succession` separada) + definir cómo se popula, o reescribir FR-010 para que SIEMPRE requiera `successorId` en el payload de cierre. El esquema actual no puede aplicar el bloqueo prometido.

---

#### T4 — BLOCKER — constraint-enforcement

**Afecta a**: US1, cross-cutting
**Location**: `contracts/client-teams-api.md#POST-close`
**Reviewer ID**: `feasibility-F4`

**Evidence**:
> "Setea endDate en el team y en todos sus ClientAssignment activos ... Publica evento AMQP ... para cada miembro cerrado"

**Gap**: Cerrar un team muta la fila del team + N filas de asignaciones + emite N eventos AMQP. El plan y el contrato no especifican los límites transaccionales. Per Constitution III (MikroORM UoW), esto DEBE ser un `em.transactional`, y la semántica de AMQP publish-after-commit DEBE definirse — si no, D-005 (PENDING outbox/retry) se filtra a esta historia y el team puede quedar cerrado en BD mientras los consumers nunca ven el cascade.

**Suggestion**: Declarar explícitamente en plan.md (o sección lifecycle de data-model.md) que el cierre de team corre dentro de un `em.transactional`, con AMQP publish post-commit. Linkear el gap a D-005 — la historia no es implementable hasta resolver ese PENDING.

---

#### T5 — ADR — concurrency

**Afecta a**: cross-cutting
**Location**: `plan.md:L33`
**Reviewer ID**: `feasibility-F5`

**Evidence**:
> "Optimistic concurrency vía updatedAt en ClientTeam y ClientAssignment (FR-022) — HTTP 409 al conflicto"

**Gap**: `updatedAt` es un `timestamp` con granularidad sub-segundo, auto-actualizado por `onUpdate: () => new Date()` en MikroORM. Dos writes en el mismo milisegundo producen el mismo `updatedAt` y bypassan el check optimista. No hay columna `@Version` ni rationale documentado para elegir timestamp en lugar de version integer monotónico.

**Suggestion**: Promover a ADR — o cambiar a columna `version` integer (`@Property({ version: true })` en MikroORM 6) o documentar por qué `updatedAt` con `clock_timestamp()` es aceptable para este workload, y alinear el contrato `If-Match` con la representación elegida.

---

#### T6 — BLOCKER — lifecycle

**Afecta a**: US1, cross-cutting
**Location**: `data-model.md#clientteam`
**Reviewer ID**: `feasibility-F6`

**Evidence**:
> "Partial unique opcional: (client_id, department, is_primary) WHERE is_primary = true AND end_date IS NULL — máximo un team principal activo por (cliente, departamento)"

**Gap**: FR-020 manda jira-adapter sincronizar "solo la asignación del equipo principal del cliente y del asesor principal". El esquema enforced at-most-one primary team pero NO at-least-one. Un cliente con 2+ teams Fiscal activos e `is_primary=false` en todos es un estado válido donde jira-adapter no tiene fila que escribir, rompiendo FR-020 silenciosamente.

**Suggestion**: O (a) requerir `isPrimary=true` en creación cuando no hay otro primary (auto-promote primer team), o (b) documentar el contrato de que jira-adapter cae al team más antiguo activo cuando no hay `is_primary=true`. Capturar como invariante del servicio + test de regresión.

---

#### T7 — ADR — implicit-decision

**Afecta a**: cross-cutting
**Location**: `data-model.md#migrations`
**Reviewer ID**: `feasibility-F7`

**Evidence**:
> "Migration M2 — pd-service-data-factory ... ADD COLUMN team_id uuid NULL ... No FK constraint: cross-service team_id is logical only"

**Gap**: Elegir "FK lógica solo" para `team_id` en data-factory merece un ADR. La alternativa (no `team_id`, derivar primary solo via jira-adapter) no está descartada en `decisions.md` ni `research.md`. Sin ADR, futuros developers no sabrán si tratar `team_id` huérfano (team borrado/cerrado en pgi-api) como corrupción o como esperado.

**Suggestion**: Añadir ADR (e.g., ADR-0011) documentando la decisión cross-service `team_id`: nullable, sin FK, tratado como opaque correlation id, + cómo data-factory maneja team ids desconocidos (ignore vs warn).

---

#### T8 — BLOCKER — concurrency

**Afecta a**: US2, cross-cutting
**Location**: `data-model.md#departmentbucketstatus`
**Reviewer ID**: `feasibility-F8`

**Evidence**:
> "globalStatus: 'active' | 'incomplete'; // active iff asesores=100 + tecnicos in {100, not-applicable} + hasPrimary"

**Gap**: FR-014 publica el evento AMQP SOLO cuando el bucket transiciona a `active`. El bucket se calcula agregando TODAS las asignaciones activas across teams del (client, department). Dos PATCH /members concurrentes en distintos teams del mismo client+department, ambos leyendo status=incomplete y ambos sumando 100, harán race: ambos pueden creer que dispararon la transición y publicar eventos duplicados, o ninguno publicar (read-modify-write hazard). El plan no especifica isolation ni row-level locking.

**Suggestion**: Especificar en plan.md la estrategia de locking (e.g., `SELECT ... FOR UPDATE` en el row padre `client`, o transacción serializable wrapping recompute + publish). Sin esto FR-014 no puede garantizar "exactly one transition event" semantics.

---

#### T9 — QUESTION-PO — lifecycle

**Afecta a**: US1
**Location**: `spec.md:L235-L242`
**Reviewer ID**: `feasibility-F9`

**Evidence**:
> "Los equipos existentes en un departamento permanecen activos aunque luego se den de baja todos los servicios contratados de ese departamento — la regla bloquea creación, no invalida existentes (a confirmar con PO — ver OQ-008)"

**Gap**: OQ-008 sigue marcada 'a confirmar con PO' dentro de FR-017. El data-model no tiene campo para marcar team como 'huérfano por terminación de servicio' ni hook al desactivar el último `ProvidedService` del departamento. El comportamiento divergirá silenciosamente de cualquier respuesta PO futura.

**Suggestion**: O cerrar OQ-008 con PO antes de implementar (default recomendado: teams existentes permanecen activos, sin cambio de esquema) o añadir columna `orphaned_at` + listener en deactivación de `ProvidedService`. Documentar el default elegido en `decisions.md` para no bloquear implementación.

---

#### T10 — BLOCKER — constraint-enforcement

**Afecta a**: cross-cutting
**Location**: `data-model.md#migrations`
**Reviewer ID**: `feasibility-F10`

**Evidence**:
> "Backfill script (separate, idempotent — ejecutado post-deploy) ... UPDATE client_assignment ca SET is_primary_advisor = true"

**Gap**: Migration M1 crea el partial unique `client_assignment_primary_advisor_unique` ANTES de que el backfill corra. Durante el gap entre la migración y la ejecución del backfill, el índice existe pero ninguna fila tiene `is_primary_advisor=true` — significando que el invariante de FR-020 ('exactamente un asesor principal activo por client+department') se viola para TODO cliente+department legacy. Cualquier evento AMQP disparado en esa ventana (o cualquier lectura por jira-adapter) no ve principal.

**Suggestion**: O (a) correr el backfill dentro de la misma transacción de la migración MikroORM (per D-003, la migración legacy ya es una MikroORM migration — aplicar esta regla consistentemente) o (b) diferir creación del partial unique a una segunda migración después del backfill. El orden actual es unsafe.

### Trazabilidad de IDs

| ID PO | Reviewer ID | Severity | Location |
|-------|-------------|----------|----------|
| D1    | business-B1 | QUESTION-PO | spec.md#FR-003 |
| D2    | business-B2 | QUESTION-PO | spec.md#FR-001 |
| D3    | business-B3 | QUESTION-PO | spec.md (ABSENCE) |
| D4    | business-B4 | QUESTION-PO | spec.md#FR-003 |
| D5    | business-B5 | QUESTION-PO | spec.md (ABSENCE) |
| D6    | business-B6 | QUESTION-PO | spec.md#FR-005 |
| D7    | business-B7 | QUESTION-PO | spec.md#user-story-3 |
| D8    | business-B8 | QUESTION-PO | spec.md#FR-017 |
| D9    | business-B11 | QUESTION-PO | spec.md (ABSENCE) |
| D10   | human-flag-2026-06-01 | QUESTION-PO | spec.md#clarifications-2026-06-01 (ABSENCE — flujo onboarding no documentado) |
| D11   | human-flag-2026-06-01 | QUESTION-PO | obligations-api/task.ts (campo único `advisor`); spec.md#FR-010 (no cubre por-rol) |
| G1    | business-B9 | BUSINESS-GAP | spec.md#FR-002 |
| G2    | business-B10 | BUSINESS-GAP | spec.md#FR-009 |
| T1    | feasibility-F1 | BLOCKER | data-model.md#clientassignment |
| T2    | feasibility-F2 | BLOCKER | data-model.md#clientassignment |
| T3    | feasibility-F3 | BLOCKER | spec.md:L199-L203 |
| T4    | feasibility-F4 | BLOCKER | contracts/client-teams-api.md#POST-close |
| T5    | feasibility-F5 | ADR | plan.md:L33 |
| T6    | feasibility-F6 | BLOCKER | data-model.md#clientteam |
| T7    | feasibility-F7 | ADR | data-model.md#migrations |
| T8    | feasibility-F8 | BLOCKER | data-model.md#departmentbucketstatus |
| T9    | feasibility-F9 | QUESTION-PO | spec.md:L235-L242 |
| T10   | feasibility-F10 | BLOCKER | data-model.md#migrations |

### Reviewers fallidos

- **`business-logic-reviewer` (bucket 9 — delivery sequence)** en la pasada técnica 2026-06-01: el reviewer devolvió 9 findings en formato incorrecto (estructura `{title, evidence, impact, recommendation, severity, bucket}` en vez del JSON V2 esperado con `id, category, affectedStories, location, evidence, gap, suggestion`). Todos descartados por el orchestrator per regla de validación. **Contenido valioso perdido** que conviene recuperar manualmente o re-ejecutar el reviewer con prompt más estricto:
  - US4 depende de event extensions que aterrizan con US1 (split migration risk en data-factory)
  - Tasks.md solo cubre US1 pero la migración M1 + AMQP afecta cross-service — riesgo de drift
  - T018 publisher envía nuevos campos sin task que verifique que consumers los toleran
  - Backfill SQL post-deploy no está en runbook → todos los clientes existentes saldrían con banner "incompleto" día 1
  - T006 mezcla DDL + DML en una migración → rollback parcial imposible
  - Frontend (T029-T039) basado en contracts ya desactualizados (commit-team.use-case quitado por decisión PO 2026-05-29)
  - Onboarding regression test no está en tasks.md a pesar de ser constraint declarada
  - lib-core-definitions enum bump no coordinado entre los 4 servicios

### Próximos pasos (para el equipo)

- **Decisiones (D1..D9)**: el orchestrator ofrecerá publicarlas como Open Questions en `spec.md`. Después, `/speckit-atlassian-sync-push` las sube como comments individuales a la Epic.
- **Aclaraciones (G1, G2)**: editar `spec.md` para añadir el FR/AC usando `suggestion` como punto de partida. No requieren input del PO.
- Bloqueantes para empezar US1: D1, D2, D6. Resolverlas antes de iniciar implementación.
