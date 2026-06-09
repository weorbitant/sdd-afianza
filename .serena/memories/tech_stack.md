# Tech Stack

## Backend (all NestJS services)
- **Runtime**: Node.js 22 (`.nvmrc`)
- **Framework**: NestJS (monolithic, no NestJS module-per-feature — single AppModule)
- **ORM**: MikroORM + PostgreSQL
- **Messaging**: RabbitMQ via `@afianza-ac/nest-module-rabbitmq`
- **Auth**: `@afianza-ac/nest-module-auth` (Azure AD JWT, Passport + JWKS)
- **Config**: `@afianza-ac/nest-module-config` (loads `src/config/<NODE_ENV>.config.ts` merged on `default.config.ts`)
- **Logging**: `@afianza-ac/nest-module-logger`
- **Validation**: `class-validator` + `class-transformer` on DTOs
- **API docs**: Swagger via NestJS decorators
- **Testing**: Jest; E2E uses `@testcontainers/postgresql`; global timeout 120s
- **Linting**: ESLint + Prettier
- **Git hooks**: Husky (pre-commit: lint; pre-push: build + test; commit-msg: commitlint)

## Frontend (pgi-app-pgi-web)
- **Framework**: React 19 + Vite
- **Testing**: Vitest
- **Build**: TypeScript check + Vite build

## Internal libraries (`@afianza-ac/`)
- `lib-core-definitions` — shared domain types/contracts
- `nest-module-auth` — Azure AD JWT
- `nest-module-auth-v2` — Entra External ID / CIAM (WIP)
- `nest-module-config` — environment config loader
- `nest-module-logger` — structured logging
- `nest-module-rabbitmq` — RabbitMQ broker abstraction (`brokerConfig()` helper)

## Infrastructure
- **DB**: PostgreSQL (Docker Compose for local dev)
- **Message broker**: RabbitMQ, vhost `data_platform`, exchange `internal` (topic)
- **Cloud**: Azure (AKS: `kubectl --context=dev/prod -n plataformadato` for pd-* services)
- **Jira**: `afianza-ac.atlassian.net`, cloudId `2dca67d5-bd8d-4522-aea4-079ceee40982`
