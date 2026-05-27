# API Contract: Client Teams

**Service**: `pgi-service-pgi-api` | **Base path**: `/v1/client-teams` | **Date**: 2026-05-25

All endpoints require JWT auth (Azure AD). Permission guards use `BackofficePermissions`.

---

## GET /v1/client-teams/:clientId/department/:department

List all teams (active + historical) for a client+department.

**Auth**: `CLIENT_ASSIGNMENT_VIEW`

**Path params**:
- `clientId` — uuid
- `department` — `FISCAL | LABORAL`

**Response 200**:
```json
[
  {
    "id": "uuid",
    "clientId": "uuid",
    "department": "FISCAL",
    "startDate": "2026-01-01",
    "endDate": null,
    "isActive": true,
    "createdBy": "user@email.com",
    "createdAt": "2026-01-01T10:00:00Z"
  }
]
```

---

## POST /v1/client-teams/:clientId/department/:department

Create a new team for a client+department. Fails if an active team already exists.

**Auth**: `CLIENT_ASSIGNMENT_EDIT` + `CLIENT_ASSIGNMENTS_{DEPARTMENT}_EDIT`

**Path params**: `clientId`, `department`

**Body**:
```json
{
  "startDate": "2026-06-01"   // must be first-of-month
}
```

**Response 201**: Created team object (same shape as GET item)

**Errors**:
- `409 ACTIVE_TEAM_EXISTS` — an active team already exists for this client+department
- `400 DATE_NOT_MONTH_BOUNDARY` — startDate is not the first of a month

---

## PUT /v1/client-teams/:clientId/:teamId/close

Close an active team. Sets `endDate` to the last day of the specified month. Also sets `dateTo` on all active members of that team.

**Auth**: `CLIENT_ASSIGNMENT_EDIT` + `CLIENT_ASSIGNMENTS_{DEPARTMENT}_EDIT`

**Body**:
```json
{
  "endDate": "2026-06-30"    // must be last-of-month
}
```

**Response 200**: Updated team object with `endDate` set and `isActive: false`

**Errors**:
- `400 DATE_NOT_MONTH_BOUNDARY` — endDate is not the last day of a month
- `400 DATE_BEFORE_START` — endDate is before the team's startDate
- `404` — team not found
- `409 TEAM_ALREADY_CLOSED` — team is already closed

---

## GET /v1/client-teams/:clientId/:teamId/members

Get all members (active + historical) of a team.

**Auth**: `CLIENT_ASSIGNMENT_VIEW`

**Response 200**:
```json
[
  {
    "id": "uuid",
    "employee": { "id": "uuid", "name": "Ana", "surname": "García" },
    "role": "asesor",
    "percentage": 60,
    "dateFrom": "2026-01-01",
    "dateTo": null,
    "isActive": true
  }
]
```

---

## POST /v1/client-teams/:clientId/:teamId/members

Add a member to an active team.

**Auth**: `CLIENT_ASSIGNMENT_EDIT` + `CLIENT_ASSIGNMENTS_{DEPARTMENT}_EDIT`

**Body**:
```json
{
  "employeeId": "uuid",
  "role": "asesor",
  "percentage": 60,
  "dateFrom": "2026-06-01"
}
```

**Response 201**: Created assignment object

**Errors**:
- `409 TEAM_CLOSED` — team is already closed
- `409 ROLE_ALREADY_FILLED` — RESPONSABLE or COORDINADOR slot is already taken
- `409 ROLE_CONFLICT` — employee already has a different role in this team
- `400 DATE_NOT_MONTH_BOUNDARY`
- `400 PERCENTAGE_OUT_OF_RANGE` — percentage not in 1–100

> Note: Adding a member does NOT validate 100% sum — the sum is validated only on explicit "save team" or on `PATCH /percentage`. This allows building a team incrementally.

---

## PATCH /v1/client-teams/:clientId/:teamId/members/:assignmentId

Update the percentage of a member (closes current assignment and opens a new one with updated % from `effectiveFrom`).

**Auth**: `CLIENT_ASSIGNMENT_EDIT` + `CLIENT_ASSIGNMENTS_{DEPARTMENT}_EDIT`

**Body**:
```json
{
  "percentage": 40,
  "effectiveFrom": "2026-07-01"   // must be first-of-month; defaults to next month
}
```

**Response 200**: New assignment object (old assignment receives `dateTo = effectiveFrom - 1 day`)

**Errors**:
- `400 PERCENTAGE_VALIDATION_FAILED` — after update, asesor or técnico group no longer sums to 100%
- `400 DATE_NOT_MONTH_BOUNDARY`
- `404` — assignment not found
- `409 TEAM_CLOSED`

---

## DELETE /v1/client-teams/:clientId/:teamId/members/:assignmentId

Remove a member from the team (sets `dateTo` = today's last-of-month).

**Auth**: `CLIENT_ASSIGNMENT_EDIT` + `CLIENT_ASSIGNMENTS_{DEPARTMENT}_EDIT`

**Query params**:
- `effectiveTo` (optional) — last-of-month date; defaults to current month's last day

**Response 204**

**Errors**:
- `400 MIN_ASESOR_REQUIRED` — removing this member would leave 0 asesores
- `400 PERCENTAGE_VALIDATION_FAILED` — remaining asesores/técnicos no longer sum to 100%
- `404` — assignment not found
- `409 TEAM_CLOSED`

---

## POST /v1/client-teams/:clientId/:teamId/validate

Validate a team's current state (100% sums, minimum members). Use before saving.

**Auth**: `CLIENT_ASSIGNMENT_VIEW`

**Response 200**:
```json
{
  "valid": false,
  "violations": [
    { "role": "ASESOR", "sum": 140, "required": 100, "error": "PERCENTAGE_VALIDATION_FAILED" }
  ]
}
```

---

## POST /v1/client-teams/:clientId/:teamId/reassign-tasks

Manually reassign PENDING tasks from one employee to another within a team.

**Auth**: `CLIENT_ASSIGNMENT_EDIT` + `CLIENT_ASSIGNMENTS_{DEPARTMENT}_EDIT`

**Body**:
```json
{
  "fromEmployeeId": "uuid",
  "toEmployeeId": "uuid",
  "taskIds": ["uuid", "uuid"]   // optional; null = all PENDING tasks for fromEmployee in this client+dept
}
```

**Response 202** (async — triggers RabbitMQ event):
```json
{ "status": "accepted", "message": "Task reassignment queued" }
```

---

## GET /v1/client-teams/:clientId/department/:department/active-summary

Quick summary of the active team for a client+department. Used by the client ficha header.

**Auth**: `CLIENT_ASSIGNMENT_VIEW`

**Response 200**:
```json
{
  "teamId": "uuid",
  "startDate": "2026-01-01",
  "memberCount": 4,
  "percentageSummary": {
    "ASESOR": { "sum": 100, "valid": true },
    "TECNICO": { "sum": 100, "valid": true }
  }
}
```

**Response 204**: No active team exists for this client+department.
