# Conventions

## Architecture (all NestJS services)
Strict 3-layer: `application → domain → infrastructure`. Never skip layers. DTOs never cross into domain.

```
src/
  application/rest/[resource]/     # Controllers + dto/ (class-validator + Swagger)
  application/amqp/[topic]-subscriber/  # AMQP subscribers + dto/
  domain/models/                   # MikroORM entities
  domain/interfaces/[name]/        # One interface per file
  domain/services/[name]/          # Business logic
  infrastructure/[name]/           # External API adapters (no MikroORM, no DTOs)
  config/                          # Per-env configs
  migrations/                      # Auto-generated MikroORM migrations
```

- **No NestJS modules per feature** — monolithic AppModule. Exception: `BackofficeUsersModule` is `@Global()` with its own DB connection (users DB owned by IDP).
- **Path alias**: `@/*` → `src/*` (tsconfig + jest).
- **Lib classes** for source-specific transformations (e.g. `SrcErpClientLib` in domain/services).

## MikroORM patterns
- Transactional: `em.fork()` + `em.transactional()` + `finally { txEm.clear() }`.
- Run `npx mikro-orm migration:check` before editing any entity — exit 0 required to proceed.

## AMQP (RabbitMQ)
- vhost: `data_platform`, exchange: `internal` (topic).
- Publish routing key pattern: `<service-name>.v1.<entity>.<event>`.
  - `pgi-service-pgi-api` publishes: `backoffice-api.v1.<entity>.<event>`.
  - `pd-*` publishes: `pd-<service>.v1.<entity>.<event>`.
- Subscribers live in `src/application/amqp/<topic>-subscriber/`.
- `ClientAssignment` entity exists independently in `pgi-service-pgi-api`, `pd-service-data-factory`, and `pd-service-jira-adapter` — desacoplado, each has its own model. Check all three before speculating on cross-service flows.

## Naming & code style
- Code, variables, and comments in **English**.
- Conventional Commits: `<type>(<scope>): <description>` (lowercase).
- REST routes: kebab-case.
- Never commit directly to `main`.
- All written artifacts (docs, PR descriptions) in English.

## Internal library usage
- `brokerConfig()` helper for RabbitMQ setup.
- `@afianza-ac/nest-module-config` — config loader pattern.
- Auth via passport + JWKS guards from `@afianza-ac/nest-module-auth`.

## Cross-service flow rule
Before writing specs or questions about cross-service data flows, grep the actual services. Do not speculate. See `.claude/rules/polyrepo-cross-service.md`.
