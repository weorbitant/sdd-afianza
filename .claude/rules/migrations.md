---
paths:
  - "**/migrations/**"
  - "**/src/domain/**/*.entity.ts"
  - "**/src/domain/**/*.entities.ts"
---

# Migrations — critical rules

- After creating a migration, always verify: `npx mikro-orm migration:create --dump` must return "No changes required".
- **Never modify already-applied migrations** — checksum mismatches break tracking.
- When touching entities, run `npx mikro-orm migration:check` **before** editing any entity to confirm the snapshot on `main` is in sync.
