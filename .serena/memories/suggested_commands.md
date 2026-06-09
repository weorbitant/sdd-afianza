# Suggested Commands

## Per-service (run from inside service directory)

```bash
# Infrastructure
npm run infra:up              # Start PostgreSQL + RabbitMQ (Docker Compose)
npm run infra:down            # Stop containers

# Development
npm run start:dev             # Dev server with watch
npm run build                 # nest build (TypeScript compile)

# Testing
npm test                      # Jest all unit tests
npx jest --testPathPattern=<path>  # Single test file
npm run test:e2e              # E2E tests (testcontainers, ~10s first run)
npm run test:cov              # Coverage report

# Code quality
npm run lint                  # ESLint
npm run lint:fix              # ESLint with auto-fix
npm run format                # Prettier

# MikroORM migrations
npx mikro-orm migration:check # Check snapshot drift (exit 0=ok, 1=drift) — run BEFORE editing entities
npm run migrations:create     # Generate new migration
npm run migrations:up         # Apply pending migrations
npm run migrations:down       # Rollback last
```

## Frontend (pgi-app-pgi-web only)
```bash
npm run dev                   # Vite dev server
npm run build                 # TypeScript check + Vite build
npx vitest run src/path/to/file.test.tsx  # Single test
```

## GitHub / Jira
```bash
gh pr create ...              # All GitHub operations via gh CLI
```

## Darwin-specific notes
- No significant divergence from standard Unix shell for these commands.
- RTK proxy active: all bash commands auto-proxied through `rtk` for token savings.
