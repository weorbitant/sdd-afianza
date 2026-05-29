---
paths:
  - "**/src/domain/**/*.ts"
  - "**/src/application/**/*.ts"
  - "**/src/infrastructure/**/*.ts"
---

# MikroORM EntityManager patterns

MikroORM uses **Unit of Work + Identity Map**. Long-lived processes (AMQP consumers) accumulate references if the EM is never cleared.

- **Reads**: `findOne(..., { disableIdentityMap: true })` — no fork needed.
- **Writes**: `const em = this.em.fork()` before any `upsert/create/assign/flush`.
- **Multi-write transactions**: `em.fork()` + `em.transactional(async txEm => { ... })`.
- **Never use `@EnsureRequestContext()`** in AMQP/cron contexts — it silently reuses the global EM.
- **`em.upsert()`** for concurrent contexts (AMQP); **`em.create()`** only inside serialized transactions.
