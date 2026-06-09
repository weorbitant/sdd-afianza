# Task Completion Checklist

Run from inside the service directory after making changes:

```bash
npm run lint:fix    # Auto-fix lint issues
npm run format      # Prettier formatting
npm run build       # Verify TypeScript compiles (pre-push hook also runs this)
npm test            # Run unit tests
```

For entity/migration changes, also:
```bash
npx mikro-orm migration:check   # Verify snapshot is in sync
npm run migrations:create        # If new migration needed
npm run migrations:up            # Apply locally
```

For frontend (pgi-app-pgi-web):
```bash
npm run build       # TypeScript + Vite build
npx vitest run      # Tests
```

## Pre-push hooks (automated)
- `npm run build && npm test` run automatically by Husky on `git push`.
- `npm run lint` runs on `git commit`.

## Branch & PR
1. Verify on correct feature branch (`git branch --show-current`).
2. Create PR via `gh pr create` — title in English, Conventional Commits format.
3. Link Jira ticket in PR description.
