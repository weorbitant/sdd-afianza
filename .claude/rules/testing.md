---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/*.spec.ts"
  - "**/*.spec.tsx"
---

# Testing

- **Never mock EntityManager** — use `@testcontainers/postgresql` with a real `postgres:17-alpine` container.
- Services without EntityManager: standard Jest mocks.
- Controller tests: Supertest + mock domain services, test DTO validation + 400 error cases.
- Integration tests: first run per session takes ~10s for container startup.
