# API Contract — Client Assignments (members of teams)

**Servicio**: `pgi-service-pgi-api`  ·  **Base path**: `/api/v1/clients/{clientId}/teams/{teamId}/members`

## Endpoints

### `POST /api/v1/clients/{clientId}/teams/{teamId}/members`

Añade un miembro al team. Persistencia inmediata (decisión 2026-05-29: no hay borrador+commit).

**Permisos**: `responsable` o `coordinador`.

**Request body**:
```json
{
  "employeeId": "uuid",
  "role": "responsable" | "coordinador" | "asesor" | "tecnico",
  "dateFrom": "2026-06-01",
  "percentage": 60,              // solo si role es asesor o tecnico; 1..100
  "isPrimaryAdvisor": false       // solo si role=asesor; max 1 true por (client, dept) activo
}
```

**Validation (orden de aplicación)**:
1. `role` válido + `department` derivado del team.
2. `percentage`: required y 1..100 si rol es asesor/tecnico; ignorado si responsable/coordinador.
3. `isPrimaryAdvisor`: rechazado si rol no es asesor.
4. Unique constraints BD (FR-021): la persona no puede tener otra asignación activa al mismo cliente, en ningún dept.
5. Cálculo derivado: tras añadir, si el `globalStatus` del dept queda en `incomplete`, devolver el body con flag advisory pero NO rechazar (FR-016 — banner amarillo, no bloqueo).

**Responses**:
- `201 Created` — body: `ClientAssignmentDto` con flag `departmentStatus`
- `400` — validación falla
- `403`
- `409 Conflict` — `(client, employee)` ya tiene asignación activa (FR-021) — error `PERSON_ALREADY_ACTIVE_IN_CLIENT`
- `412 Precondition Failed` — composición mínima no cumplida tras añadir (ej. team sin responsable)

### `PATCH /api/v1/clients/{clientId}/teams/{teamId}/members/{memberId}`

Modifica `percentage` o `isPrimaryAdvisor` de un miembro activo. Requiere `If-Match`.

**Permisos**: `responsable` o `coordinador`.

**Headers**: `If-Match: "<updatedAt>"`

**Request body** (todos opcionales):
```json
{
  "percentage": 40,
  "isPrimaryAdvisor": true
}
```

**Responses**:
- `200 OK`
- `409` — concurrencia o ya hay otro `isPrimaryAdvisor=true`

### `DELETE /api/v1/clients/{clientId}/teams/{teamId}/members/{memberId}`

Alias semántico de "cerrar miembro". **NO borra físicamente** (decisión PO 2026-06-01): pone `date_to` y opcionalmente marca `causesBaja`. El frontend abre un diálogo inline para preguntar la causa antes de mandar la petición.

**Permisos**: `responsable` o `coordinador`.

**Request body**:
```json
{
  "causesBaja": true,         // si el empleado deja la empresa, dispara reasignación al sucesor
  "successorId": "uuid"       // REQUIRED si causesBaja=true (resolución T3 — no inferencia silenciosa).
                              //          Si se omite, el endpoint devuelve 400 SUCCESSOR_REQUIRED con
                              //          un campo `suggestedSuccessorId` calculado por temporalidad
                              //          (asesor activo más antiguo con dateFrom > current.dateTo en el
                              //          mismo client+department). El frontend puede pre-rellenar el
                              //          diálogo con esa sugerencia.
}
```

**Behavior**:
- Setea `dateTo = today` y `causesBaja` según body.
- Publica evento AMQP `pgi-api.v1.client-assignment.updated` con campos completos.
- Si `causesBaja = true`: dispara `reassignOpenTasksToSuccessor(...)` en background.

**Responses**:
- `200 OK` — body con `ClientAssignmentDto` cerrado
- `400` — successorId no es empleado activo, etc.
- `403`

### `GET /api/v1/clients/{clientId}/assignments?status=active|closed|all`

Lista asignaciones del cliente, opcional filtrar por status. Lectura para todos los perfiles con acceso a la ficha.

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "clientId": "uuid",
      "teamId": "uuid",
      "employeeId": "uuid",
      "employeeName": "Alejandro Jiménez",
      "role": "asesor",
      "department": "fiscal",
      "dateFrom": "2026-01-01",
      "dateTo": null,
      "percentage": 60,
      "isPrimaryAdvisor": true,
      "causesBaja": false,
      "updatedAt": "2026-06-01T..."
    }
  ]
}
```

## Errors

| Status | Code | Cuándo |
|---|---|---|
| 400 | `INVALID_PERCENTAGE` | percentage fuera de 1..100 o ausente para asesor/tecnico |
| 400 | `PRIMARY_NOT_ASESOR` | isPrimaryAdvisor=true para rol no-asesor |
| 403 | `INSUFFICIENT_ROLE` | Usuario sin permiso |
| 409 | `PERSON_ALREADY_ACTIVE_IN_CLIENT` | FR-021 partial unique falla |
| 409 | `CONCURRENT_MODIFICATION` | If-Match falla |
| 412 | `MISSING_COMPOSITION` | Tras la operación, team queda sin responsable o sin asesor — composición mínima incumplida |
| 400 | `SUCCESSOR_REQUIRED` | DELETE con `causesBaja=true` sin `successorId`. Respuesta incluye `suggestedSuccessorId` (puede ser null si no hay candidato — el responsable debe designar uno manualmente o reabrir el equipo). |
