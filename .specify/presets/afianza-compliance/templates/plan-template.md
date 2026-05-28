# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Compliance & Security Surface *(mandatory — Afianza preset)*

<!--
  ACTION REQUIRED. Concreta a nivel técnico lo que la spec declaró en "Compliance & Data Considerations".
  Si una sección no aplica, escribe "N/A — <razón>". No la borres.
-->

### PII storage & encryption

- **Tablas/columnas que almacenan PII**: [schema.tabla.columna — N/A si no persiste PII]
- **Encriptación en reposo**: [sí/no — mecanismo: pgcrypto, columna cifrada app-side, KMS]
- **Encriptación en tránsito**: [TLS asumido / mTLS / otro]
- **Logs**: [confirma explícitamente que PII NO se loguea, o documenta qué se redacta]

### Auth & authorization

- **Guard/middleware aplicado a los endpoints nuevos**: [e.g. `AzureAdJwtGuard` de `@afianza-ac/nest-module-auth`]
- **Scopes/claims requeridos**: [listar — N/A si público]
- **Roles RBAC tocados**: [listar]
- **Si se añade un endpoint público o sin auth**: justificar aquí

### RabbitMQ contracts

- **Publicaciones nuevas**:
  - Routing key: `<service>.v1.<entity>.<event>`
  - Payload schema: [link a `contracts/` o describir]
  - PII en payload: [sí/no — si sí, justificar]
- **Suscripciones nuevas**:
  - Queue: `<service>:<event>:process`
  - Idempotencia: [estrategia — `em.upsert`, idempotency key, dedupe table]
- **N/A si la feature no toca el bus**

### External integrations

- **Adapter usado**: [`pd-service-azuread-adapter` / `pd-service-jira-adapter` / `pd-service-data-factory` / nuevo cliente]
- **Credenciales/secretos**: [dónde viven — key vault, env, config por entorno]
- **Rate limits / cuotas conocidas**: [documentar o "no aplica"]
- **Manejo de fallos del tercero**: [reintentos, circuit breaker, DLQ]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

[Gates determined based on constitution file]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
