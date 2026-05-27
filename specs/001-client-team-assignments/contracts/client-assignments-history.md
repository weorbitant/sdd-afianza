# API Contract: Assignment History

**Service**: `pgi-service-pgi-api` | **Base path**: `/v1/client-assignments` | **Date**: 2026-05-25

---

## GET /v1/client-assignments/:clientId/department/:department

Existing endpoint — extended to include `percentage` and `teamId` in response.

**Auth**: `CLIENT_ASSIGNMENT_VIEW`

**Response 200** (extended):
```json
[
  {
    "id": "uuid",
    "client": "uuid",
    "employee": { "id": "uuid", "name": "Ana", "surname": "García" },
    "department": "FISCAL",
    "role": "asesor",
    "dateFrom": "2026-01-01",
    "dateTo": null,
    "percentage": 60,
    "teamId": "uuid",
    "updatedAt": "2026-01-01T10:00:00Z",
    "updatedBy": "responsable@email.com"
  }
]
```

> `percentage` defaults to 100 for legacy rows. `teamId` is null for legacy rows.

---

## GET /v1/client-assignments/:clientId/department/:department/history

Full assignment history — all periods (active + closed) ordered by dateFrom desc.

**Auth**: `CLIENT_ASSIGNMENT_VIEW`

**Query params**:
- `role` (optional) — filter by `asesor | tecnico | coordinador | responsable`
- `employeeId` (optional) — filter by specific employee

**Response 200**: Same shape as the existing endpoint, all rows including those with `dateTo` set. Ordered: `dateFrom DESC, role ASC`.

---

## RabbitMQ Events

### Published: `backoffice-api.v1.client-assignment.updated` (extended)

Existing event — `percentage` field added (backward-compatible; downstream consumers that don't use it will ignore it).

```typescript
{
  id: string;
  employeeId: string;
  clientId: string;
  department: 'FISCAL' | 'LABORAL';
  role: 'responsable' | 'coordinador' | 'asesor' | 'tecnico';
  dateFrom: string;      // ISO date
  dateTo: string | null;
  percentage: number;   // NEW — always present (100 for legacy rows)
  updatedAt: string;
  updatedBy: string;
}
```

### Published: `backoffice-api.v1.task-reassignment.requested` (new)

```typescript
{
  clientId: string;
  department: 'FISCAL' | 'LABORAL';
  fromEmployeeId: string;
  toEmployeeId: string;
  taskIds: string[] | null;   // null = all PENDING tasks
  requestedBy: string;
  requestedAt: string;        // ISO datetime
}
```

**Consumer** (obligations-api):
- Queue: `obligations-api:task-reassignment:process`
- Handler: `TaskReassignmentSubscriber.handleReassignmentRequested()`
- Action: reassign tasks (PENDING only unless taskIds specified) from `fromEmployeeId` to `toEmployeeId`
- Idempotent: reassigning an already-reassigned task is a no-op
