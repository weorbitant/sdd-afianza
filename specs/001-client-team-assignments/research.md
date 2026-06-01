# Research — Asignaciones múltiples (DEVPT-518)

**Fase**: 0 (Outline & Research) — todas las `NEEDS CLARIFICATION` del plan resueltas aquí.

## R1 · Estrategia de migración legacy 1:1 → multi-equipo

**Decisión**: una sola migración SQL aditiva ejecutada en `pgi-service-pgi-api` que (a) añade columnas `is_primary_advisor`, `causes_baja` a `client_assignment`, (b) añade columnas `is_primary` a `client_team`, (c) añade el partial unique `(client_id, employee_id) WHERE date_to IS NULL`. **Sin backfill destructivo**: las filas existentes ya tienen `team_id` (la columna se creó en una iteración previa) y `percentage` (con default 100). El bool `is_primary_advisor` se calcula post-deploy con un script idempotente que marca el primer asesor de cada (cliente, departamento) si no hay ninguno marcado.

**Rationale**: la migración aditiva no rompe filas existentes ni el flujo `applyFromClientOnboarding`. El backfill por separado permite rollback sin perder datos. La cláusula `WHERE date_to IS NULL` del partial unique solo cubre filas activas, así que filas históricas no chocan.

**Alternativas consideradas**: migración con backfill atómico (rechazada — riesgo si falla a mitad), reescritura del modelo (rechazada — destructive y rompe el onboarding subscriber existente).

## R2 · Estructura del payload AMQP `client-assignment.v1.updated`

**Decisión**: extender el payload existente añadiendo campos opcionales (nullable) para preservar backward-compat con consumers desplegados antes del nuevo deploy. Schema final:

```typescript
{
  // Existentes (mantenidos)
  clientId: string;
  employeeId: string;
  role: 'responsable' | 'coordinador' | 'asesor' | 'tecnico';
  department: 'fiscal' | 'laboral';
  dateFrom: string; // ISO date (primer día del mes)
  dateTo: string | null; // ISO date (último día del mes) o null si activo
  updatedAt: string; // ISO timestamp
  updatedBy: string; // email
  // Nuevos (opcionales hasta que todos los consumers estén alineados)
  teamId?: string;
  percentage?: number; // 1-100
  isPrimaryAdvisor?: boolean;
  causesBaja?: boolean;
}
```

**Rationale**: los nuevos campos son opcionales en JSON, así que `pd-service-data-factory` y `pd-service-jira-adapter` con la versión vieja del consumer ignoran los campos extra (Postel's law — tolerante). Cuando ambos consumers se actualicen, la información estará disponible para informes y sync Jira Assets.

**Alternativas consideradas**: bump de routing key a `v2.client-assignment.updated` (rechazado — duplica complejidad de routing y migración de queues sin ganancia: los campos son aditivos), versionado en payload con discriminator (rechazado — over-engineering).

## R3 · Alineación de consumers cross-service (deploy plan)

**Decisión**: deploy en este orden para evitar perder eventos durante la ventana de transición:

1. **`pd-service-data-factory`** primero — desplegar la versión que añade `team_id` y `percentage` al modelo + subscriber que lee los nuevos campos cuando vienen. Sigue funcionando con eventos legacy.
2. **`pd-service-jira-adapter`** segundo — desplegar la versión que filtra a `isPrimaryAdvisor=true` antes de sincronizar a Jira Assets. Sigue tratando eventos legacy como "ese es el único, es el principal".
3. **`pgi-service-pgi-api`** último — desplegar el publisher con los nuevos campos. A partir de ahora los eventos llevan datos completos.

**Rationale**: este orden garantiza que cuando pgi-api empieza a emitir los nuevos campos, los consumers ya están preparados para procesarlos. Si se invirtiera el orden, los consumers nuevos esperarían campos que aún no llegan y procesarían los legacy con valores por defecto incorrectos.

**Alternativas consideradas**: feature flag en el publisher (rechazado — añade complejidad de configuración para algo que se resuelve con orden de deploy).

## R4 · Validación del 100% por departamento — implementación

**Decisión**: query agregada SQL ejecutada dentro de la transacción del save, con `SELECT ... FOR UPDATE` sobre `client_assignment` filtrado por `(client_id, department)` y `dateTo IS NULL`. La query suma `percentage` agrupando por `role` (filtrado a asesor / técnico). Si suma ≠ 100% en alguno de los buckets, el team queda en estado `incomplete` (no rechaza, advisory). Si la composición mínima no se cumple (no hay responsable o 0 asesores en el team siendo modificado), rechaza con HTTP 400.

**Rationale**: usar `FOR UPDATE` evita race entre dos peticiones simultáneas. También evita race con el AMQP subscriber del onboarding: si el onboarding está creando filas mientras el responsable edita desde UI, ambos lockean la misma fila y serializan.

**Alternativas consideradas**: cálculo en memoria post-flush (rechazado — no detecta race entre transacciones), trigger BD (rechazado — Constitution V simplicity: la lógica vive en el servicio, no en la BD).

## R5 · Onboarding bridge (D10 sigue parcial)

**Decisión MVP**: `applyFromClientOnboarding` sigue creando filas en `client_assignment` con los valores actuales **con `team_id = NULL`** hasta que PO resuelva D10. Si se decide después que el onboarding debe crear un `ClientTeam` por defecto, se implementa como cambio aditivo en una segunda iteración sin afectar al modelo principal del MVP.

**Acción inmediata**: añadir test de regresión `applyFromClientOnboarding.regression.spec.ts` que verifica que el consumer sigue creando filas legacy correctamente.

**Rationale**: no bloquear el MVP por D10. El usuario verá filas huérfanas (sin team) en la vista del cliente — los onboardings nuevos requerirán que un responsable las agrupe manualmente. Se documenta como limitación conocida en `quickstart.md`.

**Alternativas consideradas**: implementar D10-C como assumption antes de PO confirmation (rechazado — riesgo de retrabajo si PO elige otra opción).

## R6 · State management frontend

**Decisión**: **TanStack Query** para queries y mutations de equipos y miembros, con `optimisticUpdate` para el slider de porcentaje. **Sin Zustand** — la composición del equipo es state servidor cacheado. El bucket-status (suma % por departamento) se calcula client-side a partir del query cache para mostrar la barra advisory en vivo, pero la validación dura es server-side.

**Rationale**: TanStack Query ya es convención en `pgi-app-pgi-web`. Optimistic update aplica bien al slider. Sin necesidad de store cliente para state que es inherentemente servidor.

**Alternativas consideradas**: Zustand para borrador de team antes de commit (rechazado — la decisión PO 2026-05-29 dice persistencia inmediata, no hay borrador), Redux (rechazado — over-engineering).

---

## Resumen de decisiones

| ID | Tema | Decisión |
|---|---|---|
| R1 | Migración | Aditiva, idempotente, backfill por script separado |
| R2 | AMQP payload | Campos nuevos opcionales, sin bump de versión |
| R3 | Deploy order | data-factory → jira-adapter → pgi-api |
| R4 | Validación 100% | Query agregada con `FOR UPDATE` en transacción |
| R5 | Onboarding | MVP mantiene legacy (sin team_id); D10 se resolverá después |
| R6 | Frontend state | TanStack Query + optimistic update para slider |

Todas las `NEEDS CLARIFICATION` técnicas resueltas. Las que dependen de PO (D5 routing por rol, D10 onboarding) tienen assumption MVP documentada y no bloquean.
