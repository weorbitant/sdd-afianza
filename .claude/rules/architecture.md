---
paths:
  - "**/src/**/*.ts"
---

# Architecture — backend services

All NestJS services follow the same **strict 3-layer architecture** with no NestJS modules (monolithic by design, all providers in `AppModule`):

```
application/     # Controllers + AMQP subscribers + DTOs. No business logic.
domain/          # Business logic, MikroORM entities, domain services.
infrastructure/  # External API clients. Never called directly from application.
config/          # Per-environment configs (default, local, development, production, test).
migrations/      # MikroORM auto-generated migrations + snapshot JSON.
```

**Call flow**: `application → domain → infrastructure` — never skip layers, never call infrastructure from application, never let DTOs cross into domain.

## Shared internal libraries (`@afianza-ac/`)

| Package | Purpose |
|---------|---------|
| `lib-core-definitions` | Shared domain types/contracts across services |
| `nest-module-auth` | Azure AD JWT middleware (passport + JWKS) |
| `nest-module-config` | Per-environment config loader |
| `nest-module-logger` | Structured logging |
| `nest-module-rabbitmq` | RabbitMQ abstraction (`brokerConfig()` helper) |
| `ui` | Afianza design system component library |
