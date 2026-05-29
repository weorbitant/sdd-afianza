# Common commands

## Backend services (NestJS)

Run from inside the service directory:

```bash
npm run infra:up                    # Start PostgreSQL + RabbitMQ via Docker
npm run start:dev                   # Dev server with watch
npm run build                       # Compile (nest build)
npm test                            # Jest
npx jest --testPathPattern=<path>   # Single test file
npm run lint:fix                    # ESLint with auto-fix
npm run format                      # Prettier
npm run migrations:create           # New MikroORM migration
npm run migrations:up               # Apply migrations
```

## Frontend (`pgi-app-pgi-web`)

```bash
npm run dev          # Vite dev server
npm run build        # TypeScript check + Vite build
npx vitest run src/path/to/file.test.tsx  # Single test file
```

## Package manager

All services use **npm** (`package-lock.json`).
