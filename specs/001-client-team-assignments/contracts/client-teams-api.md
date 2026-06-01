# API Contract — Client Teams

**Servicio**: `pgi-service-pgi-api`  ·  **Base path**: `/api/v1/clients/{clientId}/teams`

## Endpoints

### `POST /api/v1/clients/{clientId}/teams`

Crea un nuevo `ClientTeam` para un cliente en un departamento. Pre-condición: el cliente debe tener al menos un `ProvidedService` activo cuya `family` mapee al departamento (FR-017).

**Permisos**: `responsable` o `coordinador` del cliente.

**Request body**:
```json
{
  "department": "fiscal" | "laboral",
  "startDate": "2026-06-01",  // primer día del mes
  "isPrimary": false           // opcional, default false; max 1 true por (client, dept)
}
```

**Responses**:
- `201 Created` — body: `ClientTeamDto` (con `id`, `updatedAt`)
- `400 Bad Request` — validación falla (fecha no es día 1, dept inválido, etc.)
- `403 Forbidden` — sin permiso de rol
- `412 Precondition Failed` — cliente no tiene `ProvidedService` activo en ese dept (FR-017)
- `409 Conflict` — ya existe un team con `isPrimary=true` activo en ese (client, dept)

### `PATCH /api/v1/clients/{clientId}/teams/{teamId}`

Modifica un team activo. Soporta cambiar `isPrimary`. Requiere `If-Match` header con el `updatedAt` que tenía al cargar (optimistic concurrency, FR-022).

**Permisos**: `responsable` o `coordinador`.

**Headers**: `If-Match: "2026-06-01T10:23:45.000Z"`

**Request body** (todos opcionales):
```json
{
  "isPrimary": true
}
```

**Responses**:
- `200 OK` — body actualizado
- `409 Conflict` — `If-Match` no coincide con `updatedAt` actual (otro editor lo cambió)
- `403 Forbidden`
- `404 Not Found`

### `POST /api/v1/clients/{clientId}/teams/{teamId}/close`

Cierra un team setting `endDate`. Acción irreversible (FR-009). Requiere doble confirmación (UI), pero a nivel API es un POST.

**Permisos**: `responsable`.

**Request body**:
```json
{
  "endDate": "2027-05-31"  // último día del mes
}
```

**Behavior** (resolución T4):
- Toda la mutación (team.endDate + N assignments.dateTo) corre dentro de **un único `em.transactional`**. Si cualquier paso falla, rollback completo — el team no queda parcialmente cerrado.
- Para cada asignación cerrada por esta acción, NO se dispara `causesBaja` automáticamente — eso es decisión per-member al cerrar individualmente vía `DELETE /members/{id}`.
- **AMQP publish post-commit**: los eventos `pgi-api.v1.client-assignment.updated` (uno por miembro cerrado) se emiten DESPUÉS del commit exitoso de la transacción. Si el commit falla, no se emite ningún evento. Pendiente D-005 (outbox pattern) para garantizar at-least-once delivery sin ack manual.

**Responses**:
- `200 OK`
- `400` — endDate no es último día de mes
- `403`
- `409` — team ya cerrado

### `GET /api/v1/clients/{clientId}/teams?status=active|closed|all`

Lista teams del cliente. Default `status=active`. Acceso de lectura para todos los perfiles con acceso a la ficha.

**Response**:
```json
{
  "items": [
    {
      "id": "uuid",
      "clientId": "uuid",
      "department": "fiscal",
      "startDate": "2026-01-01",
      "endDate": null,
      "isPrimary": true,
      "createdBy": "alfonso@afianza-ac.es",
      "createdAt": "2026-01-01T...",
      "updatedAt": "2026-06-01T..."
    }
  ]
}
```

### `GET /api/v1/clients/{clientId}/department/{department}/bucket-status`

Devuelve el estado del 100% por departamento (asesores + técnicos por separado, agregado entre todos los teams del dept). Endpoint que la UI consulta para mostrar barras advisory.

**Response**:
```json
{
  "department": "fiscal",
  "asesores": {
    "sum": 100,
    "status": "complete",
    "members": [{ "employeeId": "...", "teamId": "...", "percentage": 60 }, ...]
  },
  "tecnicos": {
    "sum": 80,
    "status": "incomplete",
    "members": [...]
  },
  "hasPrimaryAdvisor": true,
  "globalStatus": "incomplete"  // active sólo si asesores=100 + tecnicos in {100, not-applicable} + hasPrimary
}
```

## Errors

Errores comunes (formato `application/problem+json`):

| Status | Code | Cuándo |
|---|---|---|
| 400 | `INVALID_DATE_GRANULARITY` | dateFrom/endDate no es primer/último día de mes |
| 400 | `MISSING_COMPOSITION` | Composición mínima no cumplida al guardar |
| 403 | `INSUFFICIENT_ROLE` | Usuario no es responsable/coordinador del cliente |
| 409 | `CONCURRENT_MODIFICATION` | `If-Match` no coincide con `updatedAt` actual |
| 409 | `PRIMARY_ALREADY_EXISTS` | Intentar setear `isPrimary=true` cuando ya existe otro |
| 412 | `NO_PROVIDED_SERVICE` | Cliente sin `ProvidedService` activo en ese dept |
