# ADR-0011 — `team_id` in `pd-service-data-factory` is a logical FK only

**Status**: Accepted
**Date**: 2026-06-01
**Supersedes**: N/A
**Superseded by**: N/A
**Origin**: Challenge technical 2026-06-01, T7 (feasibility-F7)

## Context

La feature DEVPT-518 introduce `ClientTeam` en `pgi-service-pgi-api`. El modelo `ClientAssignment` en `pd-service-data-factory` necesita reflejar el `team_id` para que los informes de rentabilidad puedan agregar por equipo (FR-014 + FR-018, FR-019).

Decisión a documentar: cómo se modela ese `team_id` en data-factory cuando la fuente de verdad (`ClientTeam`) vive en pgi-api, otro servicio.

Constitution IV (event-driven cross-service) prohíbe HTTP calls directos entre servicios. Cualquier consistencia entre tablas cross-service depende del AMQP pipeline.

## Decision

`pd-service-data-factory/client_assignment.team_id` es una **columna `uuid NULL`** sin foreign key constraint. Es un **correlation id lógico** — útil para join en queries de informes pero NO valida integridad referencial entre BDs.

Política de huérfanos:
- Si un evento llega con un `teamId` que data-factory no conoce (porque el team fue creado en pgi-api pero el evento de creación de team aún no llegó / no se emite): **persistir el valor tal cual** y emitir log warn `unknown team_id for client_assignment {id}: {teamId}`.
- Si un team se cierra/elimina en pgi-api y data-factory tiene asignaciones con ese `team_id`: **mantener el valor** — el histórico es válido y los informes que agregan por team siguen funcionando con teams cerrados.
- **NO** se crea entidad `ClientTeam` en data-factory. Si en el futuro hace falta, se añade vía nueva migración + nuevo evento `client-team.updated`.

## Alternatives considered

### A. FK real cross-service (descartado por imposible)

Postgres no soporta FK entre bases de datos. Habría que mover ambos modelos a la misma BD — fuera de scope (rompe boundaries de servicio).

### B. No tener `team_id` en data-factory, derivar via jira-adapter (descartado)

**Pro**: cero acoplamiento entre data-factory y conceptos de equipo.
**Con**: informes de rentabilidad NO pueden agregar por equipo sin pedir a otro servicio. Eficiencia y simplicidad de queries cae.

### C. `team_id` como logical FK + log warn en huérfanos (**elegida**)

**Pro**: informes pueden agregar por team sin coordinación cross-service. Cero coste de validación referencial. Huérfanos observables pero no rompen ingest.
**Con**: posibilidad de drift silencioso si pgi-api borra teams sin notificar (mitigado: pgi-api no borra teams, solo cierra con endDate — los teams cerrados no son huérfanos, son históricos válidos).

## Consequences

- **Migración M2** mantiene `team_id uuid NULL` sin FK constraint.
- `pd-service-data-factory/client-assignment.subscriber` añade log warn cuando recibe payload con teamId no conocido localmente (puede ocurrir en rolling deploy si data-factory está más atrasado).
- Si en una iteración futura se necesita validar integridad, se introduce evento `client-team.created/closed` aparte y data-factory mantiene una proyección local de `ClientTeam`. Por ahora, YAGNI (Constitution V).
- No hay migración para "limpiar" huérfanos — los huérfanos son inputs válidos del sistema.
