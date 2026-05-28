# Quickstart: Asignaciones Múltiples en Ficha de Cliente

**Feature**: 001-client-team-assignments | **Date**: 2026-05-25

---

## Prerequisites

- Docker running (PostgreSQL + RabbitMQ via `npm run infra:up`)
- Node.js ≥ 20
- Access to `asesores/pgi-service-pgi-api/` and `asesores/pgi-app-pgi-web/`

---

## 1. Backend setup

```bash
cd asesores/pgi-service-pgi-api

# Check migration snapshot is clean before touching entities
npx mikro-orm migration:check

# Apply new migration (ClientTeam table + percentage column)
npm run migrations:up

# Verify: no pending changes after migration
npx mikro-orm migration:create --dump
# Expected: "No changes required"

npm run start:dev
# Runs on http://localhost:3000
```

---

## 2. Frontend setup

```bash
cd asesores/pgi-app-pgi-web

npm install
npm run dev
# Runs on http://localhost:5173
```

---

## 3. Smoke test — create a team via API

```bash
# Replace :clientId with a real client UUID from your dev DB
CLIENT_ID="<uuid>"
DEPT="FISCAL"

# 1. Create a team
curl -X POST http://localhost:3000/v1/client-teams/$CLIENT_ID/department/$DEPT \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"startDate": "2026-06-01"}'
# → 201 Created, returns team with id

TEAM_ID="<team-id-from-response>"
EMPLOYEE_A="<employee-uuid-A>"
EMPLOYEE_B="<employee-uuid-B>"

# 2. Add first asesor at 60%
curl -X POST http://localhost:3000/v1/client-teams/$CLIENT_ID/$TEAM_ID/members \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"employeeId\": \"$EMPLOYEE_A\", \"role\": \"asesor\", \"percentage\": 60, \"dateFrom\": \"2026-06-01\"}"
# → 201 Created

# 3. Add second asesor at 40%
curl -X POST http://localhost:3000/v1/client-teams/$CLIENT_ID/$TEAM_ID/members \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"employeeId\": \"$EMPLOYEE_B\", \"role\": \"asesor\", \"percentage\": 40, \"dateFrom\": \"2026-06-01\"}"
# → 201 Created

# 4. Validate team (informational only — sum should be 100%)
curl http://localhost:3000/v1/client-teams/$CLIENT_ID/$TEAM_ID/validate \
  -H "Authorization: Bearer <token>"
# → { "valid": true, "violations": [] }

# 4b. Commit the team — runs full validation, marks team as confirmed,
# and publishes one `backoffice-api.v1.client-assignment.updated` event
# per active member (with the new `percentage` field).
curl -X POST http://localhost:3000/v1/client-teams/$CLIENT_ID/$TEAM_ID/commit \
  -H "Authorization: Bearer <token>"
# → 200 { "teamId": "...", "committedAt": "...", "membersPublished": 2 }
# If validation fails:
# → 400 PERCENTAGE_VALIDATION_FAILED or MIN_ASESOR_REQUIRED

# 5. Try invalid: bump first asesor to 80% → should fail 400
curl -X PATCH http://localhost:3000/v1/client-teams/$CLIENT_ID/$TEAM_ID/members/<assignment-a-id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"percentage": 80, "effectiveFrom": "2026-07-01"}'
# → 400 PERCENTAGE_VALIDATION_FAILED (asesores would sum to 120%)

# 6. View history
curl http://localhost:3000/v1/client-assignments/$CLIENT_ID/department/$DEPT/history \
  -H "Authorization: Bearer <token>"
# → Shows all assignment periods

# 7. Close the team
curl -X PUT http://localhost:3000/v1/client-teams/$CLIENT_ID/$TEAM_ID/close \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"endDate": "2026-06-30"}'
# → 200 OK, team is now closed; all members get dateTo = 2026-06-30
```

---

## 4. Smoke test — try to create duplicate active team

```bash
# Attempt to create a second active team for the same client+dept (should fail)
curl -X POST http://localhost:3000/v1/client-teams/$CLIENT_ID/department/$DEPT \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"startDate": "2026-07-01"}'
# → 409 ACTIVE_TEAM_EXISTS  (if first team not yet closed)
# → 201 Created             (if first team was closed in step 7)
```

---

## 5. Frontend verification

1. Navigate to `/general/ficha-cliente/:clientId`
2. Open the **Asignaciones** tab
3. Verify the new **Team** section shows:
   - Active team header with start date and createdBy
   - Per-member percentage fields (editable for responsable/coordinador)
   - Live % sum indicator (green = 100%, red = other)
   - **Histórico** accordion showing all past periods
4. Try editing a percentage so the sum goes above 100% → Save button is disabled and indicator turns red
5. Click **Cerrar equipo** → confirm → team shows as inactive

---

## 6. Run tests

```bash
# Backend — integration tests (starts testcontainers automatically)
cd asesores/pgi-service-pgi-api
npm test -- --testPathPattern=client-team

# Frontend — component tests
cd asesores/pgi-app-pgi-web
npx vitest run src/features/client-teams
```

---

## 7. RabbitMQ — manual task reassignment

```bash
# Via API (triggers event)
curl -X POST http://localhost:3000/v1/client-teams/$CLIENT_ID/$TEAM_ID/reassign-tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"fromEmployeeId\": \"$EMPLOYEE_A\", \"toEmployeeId\": \"$EMPLOYEE_B\", \"taskIds\": null}"
# → 202 Accepted

# Verify in RabbitMQ management UI (localhost:15672):
# Exchange: internal, routing key: backoffice-api.v1.task-reassignment.requested
# Check obligations-api queue: obligations-api:task-reassignment:process consumed the message
```
