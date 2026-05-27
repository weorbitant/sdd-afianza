# Business Rules Checklist: Asignaciones Múltiples en Ficha de Cliente

**Purpose**: Validar que los requisitos de reglas de negocio son completos, inequívocos y testeables — antes de abrir PR y antes de release.
**Created**: 2026-05-25
**Feature**: [spec.md](../spec.md) · [data-model.md](../data-model.md) · [contracts/client-teams.md](../contracts/client-teams.md)
**Audience**: Autor (pre-PR) · QA (pre-release)
**Focus**: Reglas de negocio — validación %, fechas, unicidad, roles, cierre, tareas

---

## 1. Validación de porcentaje (FR-003)

- [ ] CHK001 — ¿Está especificado en qué momento exacto se ejecuta la validación del 100% — en cada cambio de campo, al añadir un miembro o solo al intentar guardar? ¿O en todos? [Claridad, Spec §FR-003]
- [ ] CHK002 — ¿El requisito define qué se considera un miembro "activo" a efectos del cálculo del 100%: solo los que tienen `dateTo = null`, o también los que tienen `dateTo >= hoy`? [Claridad, Spec §FR-003]
- [ ] CHK003 — ¿Está especificado cómo se comporta el sistema durante la construcción incremental del equipo (p. ej., un equipo con un solo asesor al 60% antes de añadir el segundo)? ¿Se bloquea o solo se advierte? [Cobertura, Spec §US2]
- [ ] CHK004 — ¿El spec define si la validación del 100% aplica también al grupo de técnicos cuando hay exactamente un técnico al 80%? ¿El rechazo es explícito? [Completitud, Spec §FR-003]
- [ ] CHK005 — ¿Los mensajes de error para `PERCENTAGE_VALIDATION_FAILED` están especificados con el texto exacto que verá el usuario, o solo se nombra el código de error? [Claridad, Gap]
- [ ] CHK006 — ¿La regla de validación del 100% aplica cuando se elimina un miembro, o solo cuando se añade o modifica? ¿El spec cubre el escenario de eliminación que deja una suma inválida? [Cobertura, Spec §FR-003, Edge Cases]

---

## 2. Convención de fechas first-of-month (FR-012)

- [ ] CHK007 — ¿El spec especifica el comportamiento del sistema cuando un usuario intenta introducir una fecha que no es el primer día del mes — rechazo silencioso, error visible o corrección automática? [Claridad, Spec §FR-012]
- [ ] CHK008 — ¿Está documentado qué ocurre con los registros históricos existentes (con fechas no alineadas a mes) cuando se aplica la nueva convención — se migran, se muestran tal cual, o se normalizan en lectura? [Completitud, Spec §FR-012]
- [ ] CHK009 — ¿El req define si `dateTo = null` representa "activo indefinidamente" o "pendiente de cierre"? ¿Son semánticamente equivalentes en el spec? [Ambigüedad, Spec §FR-002]
- [ ] CHK010 — ¿El spec cubre qué ocurre si `effectiveFrom` de un cambio de porcentaje (PATCH) es el mismo mes que el inicio del equipo — se solapan y cuál prevalece? [Edge Case, contracts §PATCH]

---

## 3. Unicidad del equipo activo por cliente+departamento (FR-005)

- [ ] CHK011 — ¿El spec especifica el mensaje de error (`ACTIVE_TEAM_EXISTS`) que verá el usuario al intentar crear un segundo equipo activo, y no solo el código de error interno? [Claridad, Spec §FR-005]
- [ ] CHK012 — ¿El req define si se puede crear un nuevo equipo el mismo día en que se cierra el anterior (es decir, ¿`endDate` de un equipo = `startDate` del siguiente es válido)? [Edge Case, Gap]
- [ ] CHK013 — ¿El spec cubre qué ocurre si dos operaciones concurrentes intentan crear equipos simultáneamente para el mismo cliente+departamento — el índice parcial lo evita, pero ¿está el comportamiento de error documentado como req? [Cobertura, Concurrencia]

---

## 4. Reglas de exclusividad de roles (FR-001, FR-004, Edge Cases)

- [ ] CHK014 — ¿El spec especifica el comportamiento exacto cuando se intenta añadir un empleado como ASESOR que ya figura como COORDINADOR del mismo equipo — error, advertencia, o rechazo silencioso? [Claridad, Spec §Edge Cases]
- [ ] CHK015 — ¿Está documentado si el RESPONSABLE puede también ser ASESOR o TÉCNICO en el mismo equipo, o si los cuatro roles son mutuamente excluyentes entre sí? [Completitud, Spec §Edge Cases]
- [ ] CHK016 — ¿El req define qué sucede si se elimina el único COORDINADOR del equipo — el equipo sigue siendo válido sin coordinador? ¿El spec confirma que coordinador es opcional? [Claridad, Spec §FR-001]
- [ ] CHK017 — ¿La restricción de "máximo 1 RESPONSABLE y 1 COORDINADOR por equipo" tiene un mensaje de error especificado (`ROLE_ALREADY_FILLED`)? ¿O solo se menciona como regla sin definir el comportamiento de fallo? [Claridad, Gap]

---

## 5. Mínimo 1 asesor activo sin gaps (FR-011)

- [ ] CHK018 — ¿El spec define si la regla de mínimo 1 asesor aplica también durante el cierre del equipo — puede el responsable cerrar un equipo dejando 0 asesores activos si todos reciben `dateTo`? [Ambigüedad, Spec §FR-011]
- [ ] CHK019 — ¿El req especifica qué ocurre si el único asesor activo intenta reducir su porcentaje a 0% — es un escenario de "sin cobertura" o la validación del 100% lo rechaza antes? [Cobertura, Edge Case]
- [ ] CHK020 — ¿El mensaje de error `MIN_ASESOR_REQUIRED` está especificado con texto orientado al usuario, o solo como código interno? [Claridad, Gap]

---

## 6. Cierre de equipo y propagación de fechas (FR-009, US4)

- [ ] CHK021 — ¿El spec define el comportamiento cuando se intenta cerrar un equipo que ya tiene miembros con `dateTo` anterior a la `endDate` propuesta — ¿se sobreescribe, se ignoran, o el sistema lo rechaza? [Completitud, Spec §FR-009]
- [ ] CHK022 — ¿El req especifica qué pasa si el responsable intenta cerrar un equipo cuya `endDate` es anterior a la `dateFrom` de algún miembro activo — ¿es posible ese escenario y cómo se trata? [Edge Case, Gap]
- [ ] CHK023 — ¿Está definido si un equipo cerrado puede reabrirse (cambiar `endDate` a null) o si el cierre es irreversible salvo creando un nuevo equipo? [Completitud, Ambigüedad, Spec §US4]

---

## 7. Reglas de reasignación de tareas (FR-010)

- [ ] CHK024 — ¿El spec define operacionalmente qué significa "asesor que causa baja en la empresa" — quién lo registra, qué campo del sistema lo refleja y cómo lo detecta el flujo automático? [Claridad, Spec §FR-010]
- [ ] CHK025 — ¿El req especifica qué ocurre si se activa la reasignación automática pero no hay sucesor definido para ese cliente+departamento — se bloquea el alta de baja, se notifica, o las tareas quedan sin asignar? [Cobertura, Gap, Spec §FR-010]
- [ ] CHK026 — ¿El spec aclara si la reasignación manual (POST /reassign-tasks) es instantánea o asíncrona desde la perspectiva del usuario, y si debe existir confirmación visual del resultado? [Claridad, Spec §FR-010, contracts §reassign-tasks]

---

## 8. Testabilidad de los criterios de aceptación

- [ ] CHK027 — ¿Cada acceptance scenario de US1–US4 tiene exactamente un resultado esperado ("Then") que pueda verificarse sin interpretación? ¿Hay algún "Then" con lenguaje vago como "queda registrado" sin especificar dónde y cómo? [Testabilidad, Spec §US1–US4]
- [ ] CHK028 — ¿Los Success Criteria SC-002 ("rechaza el 100% de los intentos") y SC-004 ("ningún cliente puede quedarse sin cobertura") tienen un procedimiento de verificación definible — o son afirmaciones no testeables en su forma actual? [Testabilidad, Spec §SC-002, §SC-004]

---

## 9. Designación de asesor/equipo principal (Gap — Epic DEVPT-518)

- [ ] CHK029 — ¿El spec captura como FR explícito el requisito de designar un "asesor principal" cuando el cliente tiene un único equipo? ¿Está especificado quién puede designarlo y cuándo? [Completitud, Gap]
- [ ] CHK030 — ¿El spec define cómo se designa el "equipo principal" cuando un cliente tiene dos equipos activos simultáneos (p. ej., Fiscal + Laboral) — quién lo designa, cuándo y qué implica a nivel operativo (NOA, responsabilidad, asignación de tareas)? [Completitud, Gap]
- [ ] CHK031 — ¿El req define qué ocurre con la asignación de tareas en curso cuando el asesor o equipo principal cambia — ¿las tareas abiertas siguen al asesor original o se reasignan al nuevo principal? [Cobertura, Spec §FR-010]

---

## 10. Integración con Plataforma del Dato (FR-014)

- [ ] CHK032 — ¿El req FR-014 especifica qué ocurre si la sincronización con Plataforma del Dato falla — ¿la operación de guardado falla también (consistencia fuerte) o se reintenta en segundo plano (consistencia eventual)? [Completitud, Gap, Spec §FR-014]
- [ ] CHK033 — ¿El spec define qué campos exactos se sincronizan con Plataforma del Dato (empleado, rol, porcentaje, período) y en qué contrato o formato? ¿Existe un contrato de integración documentado? [Claridad, Gap, Spec §FR-014]
- [ ] CHK034 — ¿El req aclara si la sincronización es push (PGI notifica a PD tras cada cambio) o pull (PD consulta periódicamente a PGI), y cuál es el sistema of record en caso de discrepancia entre ambos? [Claridad, Gap]

---

## 11. Migración 1-a-1 → porcentajes (FR-013)

- [ ] CHK035 — ¿El req FR-013 define el criterio de validación de idempotencia — qué debe ocurrir exactamente si la migración se ejecuta una segunda vez sobre datos ya migrados? [Testabilidad, Spec §FR-013]
- [ ] CHK036 — ¿El spec especifica qué `AssignmentPeriod` se genera para las asignaciones migradas — ¿con `dateFrom` retroactivo (fecha original de la asignación existente) o con la fecha de ejecución de la migración? [Completitud, Spec §FR-013]
- [ ] CHK037 — ¿El req define si la migración se ejecuta en ventana de mantenimiento (downtime) o en caliente (zero-downtime), y qué garantías de consistencia existen para las lecturas durante la transición? [Completitud, Gap]

---

---

## 12. Modelo de propiedad del equipo — Modelo A vs Modelo B (⚠️ Pendiente de decisión)

- [ ] CHK038 — ¿El spec declara explícitamente si los equipos son entidades propiedad del cliente (`Team.client_id`, Modelo A) o entidades independientes asignables a clientes (`ClientTeamAssignment`, Modelo B)? Esta decisión determina el data model completo y el flujo de creación de UI. [Completitud, Gap, Spec §Key Entities]
- [ ] CHK039 — Si se adopta Modelo B (equipos independientes), ¿el spec define el ciclo de vida autónomo del equipo — cuándo se crea, quién lo gestiona, y qué ocurre con el equipo cuando ya no está asignado a ningún cliente? [Completitud, Gap]
- [ ] CHK040 — ¿El spec especifica si un mismo equipo (Modelo B) puede estar asignado a múltiples clientes simultáneamente, y cómo se interpreta entonces la regla del 100% por cliente+departamento? [Claridad, Gap]

---

## 13. Alcance de pantallas en MVP (FR-015)

- [ ] CHK041 — ¿El spec declara explícitamente qué pantallas quedan **fuera del alcance del MVP** (Mis Clientes, buscador PGI, informes internos) para evitar que el equipo de desarrollo los implemente por defecto? [Completitud, Spec §FR-015]
- [ ] CHK042 — ¿El spec define qué campo o columna se muestra en los listados actuales (Mis Clientes, buscador) cuando un cliente tiene múltiples asesores, mientras no se actualicen esas pantallas en el MVP? ¿Se muestra el primero, el principal, o se mantiene el valor anterior? [Claridad, Gap]

---

## 14. Edición concurrente

- [ ] CHK043 — ¿El spec define el comportamiento cuando dos responsables modifican el equipo del mismo cliente simultáneamente — last-write-wins, error de conflicto, o bloqueo optimista? [Cobertura, Gap]
- [ ] CHK044 — ¿El spec especifica qué respuesta recibe el usuario cuya operación llega "tarde" en un conflicto de concurrencia (p. ej., mensaje de error, refresco automático del formulario, o indicación del conflicto)? [Claridad, Gap]

---

## Notes

**Actualizado**: 2026-05-26 — añadidos CHK038–CHK044 tras sesión de clarify (gaps modelo A/B, alcance MVP FR-015, concurrencia).

- Marcar con `[x]` cuando el requisito pasa la validación de calidad
- Anotar inline si se detecta ambigüedad o gap: p. ej. `[x] CHK001 — ✓ OK` o `[ ] CHK001 — ⚠️ El spec no especifica el momento de validación → abrir issue`
- Los ítems con `[Gap]` no tienen respuesta en el spec actual — requieren decisión del PO antes de implementar
- **CHK038–CHK040** son bloqueantes para planning si el equipo no ha decidido Modelo A vs Modelo B
- Referencia rápida: FR = Functional Requirement, SC = Success Criteria, US = User Story (en spec.md)
