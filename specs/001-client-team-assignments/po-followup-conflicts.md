# Seguimiento sesión PO 2026-06-01 — TODOS los conflictos cerrados ✅

Todos los conflictos detectados tras la sesión han sido resueltos. Este archivo se conserva para trazabilidad.

| Conflicto | Decisión PO | Aplicado en spec |
|---|---|---|
| C1 · Persona en multi-equipo | **B**: una persona, un equipo por cliente, ni siquiera en departamentos distintos | FR-016 reescrito + FR-021 cambia a partial unique `(client_id, employee_id) WHERE dateTo IS NULL` |
| C2 · Validación bloqueante (composición vs 100%) | Solo composición mínima bloquea Guardar. 100% queda advisory | FR-003 reescrito |
| C3 · Nombre del equipo | Descartado del MVP — no hay `name` en BD. UI muestra `Equipo 1/2` por orden | FR-005 reescrito |
| C4 · Bajas largas | Sustitución estándar (fecha fin + alta sucesor) | Documentado en Clarifications 2026-06-01 tarde |

## Estado del refinamiento

- Todas las decisiones blocking de PO resueltas.
- Spec listo para `/speckit-plan`.
- Pendientes solo gaps de producto (qué rol hace cada tarea — D5) que no bloquean el modelo de datos del MVP. Assumption MVP: "todo va al asesor principal".

## Próximo paso

Ejecutar `/speckit-workflow-planning` (o directamente `/speckit-plan`) para generar el plan técnico, data model y contratos de API basados en este spec.
