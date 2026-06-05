# Archive — superseded artifacts (2026-06-04)

Estos archivos describen la versión anterior de la feature **client team assignments** (DEVPT-518). Se archivan porque el alcance funcional cambia significativamente; se reescribe la spec desde cero con `/speckit-specify`.

## Qué se conserva fuera del archivo

- `../decisions.md` — ADRs históricos. Siguen siendo aprendizajes válidos sobre el dominio, cross-service, optimistic concurrency, etc. Revisar al redactar la nueva spec; los que ya no apliquen se marcan `Superseded`.
- `../er-diagram.md` — modelo ER consolidado el 2026-06-04. Punto de partida **revisable** para el nuevo data-model; no es inmutable.
- `../designs/` — assets de diseño y catálogo (`INDEX.md`). Los frames pueden seguir siendo válidos parcialmente; revisar cuando llegue la nueva spec.

## Qué hay aquí

| Archivo | Para qué servía |
|---------|------------------|
| `spec.md` | Spec funcional anterior (US1..US4, FR-001..FR-035) |
| `plan.md` | Plan técnico por US1 |
| `tasks.md` | Desglose en tareas T001..T045 |
| `data-model.md` | Data model recién alineado al ER |
| `research.md` | Research técnico (R1..R8) |
| `quickstart.md` | Guía de arranque local |
| `contracts/` | OpenAPI contracts (client-teams, client-team-assignments) |
| `checklists/` | Checklists de validación de spec |

## Por qué se archiva en vez de borrar

Trazabilidad: cuando alguien pregunte "¿por qué la nueva spec hace X distinto de lo que vimos en refinement?", esta carpeta es la respuesta. También permite reactivar piezas concretas (un contrato, un FR) si encajan en el nuevo alcance.

## Jira

DEVPT-518 queda sin tocar por ahora. Decisión de comentar / reabrir / clonar Epic se toma cuando la nueva spec esté redactada.
