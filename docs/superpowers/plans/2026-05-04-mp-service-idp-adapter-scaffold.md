# mp-service-idp-adapter Scaffold — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a fully buildable NestJS scaffold for `mp-service-idp-adapter` — the internal IDP adapter that exchanges Entra ID Authorization Codes for signed internal JWTs.

**Architecture:** 3-layer NestJS monolith (application → domain → infrastructure), no NestJS sub-modules, all providers in AppModule. Copies the structure of `mp-service-portalcliente-api`, strips business-specific code, and adds the IDP-specific entity, config, and `jose` dependency.

**Tech Stack:** NestJS 10, MikroORM 6 (PostgreSQL), TypeScript 5.7, `jose` (JWT/JWKS), npm

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `package.json` | Create | Service name + deps (jose added, rabbitmq removed) |
| `tsconfig.json` | Create | TypeScript compiler settings |
| `tsconfig.build.json` | Create | Exclude test/spec from build |
| `nest-cli.json` | Create | NestJS CLI config |
| `jest.config.js` | Create | Jest test runner config |
| `.eslintrc.js` | Create | ESLint + prettier rules |
| `.prettierrc` | Create | Prettier formatting |
| `commitlint.config.mjs` | Create | Conventional commits |
| `.npmrc` | Create | GitHub packages registry for @afianza-ac |
| `.nvmrc` | Create | Node version pin (24) |
| `.gitignore` | Create | Standard NestJS ignores |
| `.env.example` | Create | Required env vars documented |
| `mikro-orm.config.ts` | Create | MikroORM CLI config (points to UserAppAccess entity) |
| `src/main.ts` | Create | App bootstrap (LokiLogger, Swagger, ValidationPipe) |
| `src/app.module.ts` | Create | AppModule: ConfigModule + MikroOrmModule + TerminusModule only (no RabbitMQ) |
| `src/config/default.config.ts` | Create | Default config shape (postgresql + IDP env vars) |
| `src/config/local.config.ts` | Create | Local dev overrides |
| `src/config/development.config.ts` | Create | Dev cluster overrides |
| `src/config/production.config.ts` | Create | Prod overrides |
| `src/config/test.config.ts` | Create | Test DB overrides |
| `src/config/entra.config.ts` | Create | All Entra/Internal JWT env vars typed |
| `src/domain/models/user-app-access.ts` | Create | `UserAppAccess` MikroORM entity |
| `src/application/rest/healthcheck/healthcheck.controller.ts` | Create | GET /healthcheck — DB ping |
| `src/migrations/.gitkeep` | Create | Placeholder — humans add real migrations |
| `infra/docker-compose.local.yml` | Create | Local PostgreSQL only (no RabbitMQ) |
| `afianza-ac.yml` | Create | Service manifest |
| `CLAUDE.md` | Create | Service-level guidance |

---

## Task 1: Bootstrap the directory and config files

**Files:**
- Create: `mp-service-idp-adapter/package.json`
- Create: `mp-service-idp-adapter/tsconfig.json`
- Create: `mp-service-idp-adapter/tsconfig.build.json`
- Create: `mp-service-idp-adapter/nest-cli.json`
- Create: `mp-service-idp-adapter/jest.config.js`
- Create: `mp-service-idp-adapter/.eslintrc.js`
- Create: `mp-service-idp-adapter/.prettierrc`
- Create: `mp-service-idp-adapter/commitlint.config.mjs`
- Create: `mp-service-idp-adapter/.npmrc`
- Create: `mp-service-idp-adapter/.nvmrc`
- Create: `mp-service-idp-adapter/.gitignore`
- Create: `mp-service-idp-adapter/.env.example`
- Create: `mp-service-idp-adapter/mikro-orm.config.ts`
- Create: `mp-service-idp-adapter/afianza-ac.yml`
- Create: `mp-service-idp-adapter/infra/docker-compose.local.yml`
- Create: `mp-service-idp-adapter/src/migrations/.gitkeep`

- [ ] **Step 1: Create the root directory**

```bash
mkdir -p /Users/sito/Documents/afianza/mp-service-idp-adapter/src/migrations
mkdir -p /Users/sito/Documents/afianza/mp-service-idp-adapter/infra
```

- [ ] **Step 2: Create `package.json`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/package.json`:

```json
{
  "name": "mp-service-idp-adapter",
  "version": "0.0.1",
  "description": "IDP adapter — exchanges Entra ID Authorization Code for internal JWT",
  "author": "",
  "private": true,
  "license": "UNLICENSED",
  "scripts": {
    "build": "nest build",
    "format": "prettier --write \"src/**/*.ts\" \"test/**/*.ts\"",
    "start": "nest start",
    "start:dev": "nest start --watch",
    "start:debug": "nest start --debug --watch",
    "start:prod": "node dist/src/main",
    "lint": "eslint \"{src,apps,libs,test}/**/*.ts\" --fix",
    "lint:fix": "eslint \"{src,apps,libs,test}/**/*.ts\" --fix",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:cov": "jest --coverage",
    "test:debug": "node --inspect-brk -r tsconfig-paths/register -r ts-node/register node_modules/.bin/jest --runInBand",
    "test:e2e": "jest --config ./test/jest-e2e.json",
    "manifest": "npx make-manifest",
    "migrations:create-initial": "mikro-orm migration:create --initial",
    "migrations:create": "mikro-orm migration:create",
    "migrations:up": "mikro-orm migration:up",
    "migrations:down": "mikro-orm migration:down",
    "infra:up": "docker compose -f infra/docker-compose.local.yml up -d",
    "infra:down": "docker compose -f infra/docker-compose.local.yml down",
    "prepare": "husky"
  },
  "dependencies": {
    "@afianza-ac/nest-module-config": "^1.0.0",
    "@afianza-ac/nest-module-logger": "^1.3.0",
    "@mikro-orm/core": "^6.4.3",
    "@mikro-orm/nestjs": "^6.0.2",
    "@mikro-orm/postgresql": "^6.4.3",
    "@nestjs/common": "^10.0.0",
    "@nestjs/config": "^4.0.0",
    "@nestjs/core": "^10.0.0",
    "@nestjs/platform-express": "^10.0.0",
    "@nestjs/swagger": "^8.1.1",
    "@nestjs/terminus": "^11.0.0",
    "class-transformer": "^0.5.1",
    "class-validator": "^0.14.1",
    "jose": "^5.9.6",
    "pg": "^8.13.3",
    "reflect-metadata": "^0.2.2",
    "rxjs": "^7.8.1"
  },
  "devDependencies": {
    "@commitlint/cli": "^19.7.1",
    "@commitlint/config-conventional": "^19.7.1",
    "@mikro-orm/cli": "^6.4.3",
    "@mikro-orm/migrations": "^6.4.3",
    "@nestjs/cli": "^10.0.0",
    "@nestjs/schematics": "^10.0.0",
    "@nestjs/testing": "^10.0.0",
    "@types/express": "^5.0.0",
    "@types/jest": "^29.5.14",
    "@types/node": "^22.10.7",
    "@types/supertest": "^6.0.2",
    "@typescript-eslint/eslint-plugin": "^8.0.0",
    "@typescript-eslint/parser": "^8.0.0",
    "dotenv": "^16.4.7",
    "eslint": "^8.0.0",
    "eslint-config-prettier": "^9.0.0",
    "eslint-plugin-prettier": "^5.0.0",
    "globals": "^15.15.0",
    "husky": "^9.1.7",
    "jest": "^29.7.0",
    "prettier": "^3.4.2",
    "source-map-support": "^0.5.21",
    "supertest": "^7.0.0",
    "ts-jest": "^29.2.5",
    "ts-loader": "^9.5.2",
    "ts-node": "^10.9.2",
    "tsconfig-paths": "^4.2.0",
    "typescript": "^5.7.3"
  },
  "mikro-orm": {
    "useTsNode": true,
    "configPaths": [
      "./mikro-orm.config.ts"
    ]
  }
}
```

- [ ] **Step 3: Create `tsconfig.json`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/tsconfig.json`:

```json
{
  "compilerOptions": {
    "module": "commonjs",
    "esModuleInterop": true,
    "declaration": true,
    "removeComments": true,
    "emitDecoratorMetadata": true,
    "experimentalDecorators": true,
    "allowSyntheticDefaultImports": true,
    "target": "ES2021",
    "sourceMap": true,
    "outDir": "./dist",
    "baseUrl": "./",
    "paths": {
      "@/*": ["src/*"]
    },
    "incremental": true,
    "skipLibCheck": true,
    "strictNullChecks": false,
    "noImplicitAny": false,
    "strictBindCallApply": false,
    "forceConsistentCasingInFileNames": false,
    "noFallthroughCasesInSwitch": false
  }
}
```

- [ ] **Step 4: Create `tsconfig.build.json`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/tsconfig.build.json`:

```json
{
  "extends": "./tsconfig.json",
  "exclude": ["node_modules", "test", "dist", "**/*spec.ts"]
}
```

- [ ] **Step 5: Create `nest-cli.json`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/nest-cli.json`:

```json
{
  "$schema": "https://json.schemastore.org/nest-cli",
  "collection": "@nestjs/schematics",
  "sourceRoot": "src",
  "compilerOptions": {
    "deleteOutDir": true
  }
}
```

- [ ] **Step 6: Create `jest.config.js`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/jest.config.js`:

```js
module.exports = {
  moduleFileExtensions: ['js', 'json', 'ts'],
  rootDir: 'src',
  testRegex: '.*\\.spec\\.ts$',
  transform: {
    '^.+\\.(t|j)s$': 'ts-jest',
  },
  collectCoverageFrom: ['**/*.(t|j)s'],
  coverageDirectory: '../coverage',
  testEnvironment: 'node',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  testTimeout: 60000,
  maxWorkers: 2,
};
```

- [ ] **Step 7: Create `.eslintrc.js`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/.eslintrc.js`:

```js
module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    project: 'tsconfig.json',
    tsconfigRootDir: __dirname,
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint/eslint-plugin'],
  extends: ['plugin:@typescript-eslint/recommended', 'plugin:prettier/recommended'],
  root: true,
  env: {
    node: true,
    jest: true,
  },
  ignorePatterns: ['.eslintrc.js'],
  rules: {
    '@typescript-eslint/interface-name-prefix': 'off',
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    'prettier/prettier': ['error', { printWidth: 140 }],
  },
};
```

- [ ] **Step 8: Create `.prettierrc`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/.prettierrc`:

```json
{
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 140
}
```

- [ ] **Step 9: Create `commitlint.config.mjs`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/commitlint.config.mjs`:

```js
export default { extends: ['@commitlint/config-conventional'] };
```

- [ ] **Step 10: Create `.npmrc`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/.npmrc`:

```
@afianza-ac:registry=https://npm.pkg.github.com
```

- [ ] **Step 11: Create `.nvmrc`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/.nvmrc`:

```
24
```

- [ ] **Step 12: Create `.gitignore`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/.gitignore`:

```
# compiled output
/dist
/node_modules
/build

# Logs
logs
*.log
npm-debug.log*
pnpm-debug.log*
yarn-debug.log*
yarn-error.log*
lerna-debug.log*

# OS
.DS_Store

# Tests
/coverage
/.nyc_output

# IDEs and editors
/.idea
.project
.classpath
.c9/
*.launch
.settings/
*.sublime-workspace

# IDE - VSCode
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json

# dotenv environment variable files
.env
.env.development.local
.env.test.local
.env.production.local
.env.local

# temp directory
.temp
.tmp

# Runtime data
pids
*.pid
*.seed
*.pid.lock

# Diagnostic reports
report.[0-9]*.[0-9]*.[0-9]*.[0-9]*.json

# CLAUDE local config
.claude

*.http
workflows/
```

- [ ] **Step 13: Create `.env.example`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/.env.example`:

```
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mp-service-idp-adapter-local
POSTGRES_USER=postgresql
POSTGRES_PASSWORD=Password123

# Logging
LOG_LEVEL=info
LOKI_URL=
SERVICE_ENV=local

# App
PORT=3000

# Entra ID — External ID (B2C/CIAM)
ENTRA_B2C_TENANT_ID=
ENTRA_B2C_CLIENT_ID=
ENTRA_B2C_CLIENT_SECRET=
ENTRA_B2C_JWKS_URI=https://clientesafianza.ciamlogin.com/<tenant>/v2.0/discovery/keys

# Entra ID — Workforce
ENTRA_WF_TENANT_ID=40369211-...
ENTRA_WF_CLIENT_ID=
ENTRA_WF_CLIENT_SECRET=
ENTRA_WF_JWKS_URI=https://login.microsoftonline.com/<tenant>/discovery/v2.0/keys

# Microsoft Graph API (invitations)
GRAPH_CLIENT_ID=
GRAPH_CLIENT_SECRET=
GRAPH_TENANT_ID=
GRAPH_INVITE_REDIRECT_URL=

# Internal JWT
INTERNAL_JWT_SECRET=
INTERNAL_JWT_TTL=

# backoffice-api
BACKOFFICE_API_URL=http://localhost:4000
```

- [ ] **Step 14: Create `mikro-orm.config.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/mikro-orm.config.ts`:

```ts
import { MikroOrmModuleOptions } from '@mikro-orm/nestjs';
import { PostgreSqlDriver } from '@mikro-orm/postgresql';
import * as dotenv from 'dotenv';

dotenv.config();

export default {
  entities: ['./dist/src/domain/models/*.js'],
  entitiesTs: ['./src/domain/models/*.ts'],
  driver: PostgreSqlDriver,
  dbName: process.env.POSTGRES_DB,
  user: process.env.POSTGRES_USER,
  password: process.env.POSTGRES_PASSWORD,
  host: process.env.POSTGRES_HOST,
  port: Number(process.env.POSTGRES_PORT),
  debug: true,
  migrations: {
    path: './migrations',
    pathTs: './src/migrations',
  },
} as MikroOrmModuleOptions;
```

- [ ] **Step 15: Create `infra/docker-compose.local.yml`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/infra/docker-compose.local.yml`:

```yaml
services:
  pd_postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: mp-service-idp-adapter-local
      POSTGRES_USER: postgresql
      POSTGRES_PASSWORD: Password123
    ports:
      - '5433:5432'
```

Note: port 5433 (host) to avoid collision with other local services on 5432.

- [ ] **Step 16: Create `afianza-ac.yml`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/afianza-ac.yml`:

```yaml
basename: mp-service-idp-adapter
description: IDP adapter — Entra ID Authorization Code to internal JWT
displayName: mp-service-idp-adapter
environments:
  - name: local
    infrastructure:
      compose: infra/docker-compose.local.yml
    env:
      LOG_LEVEL: trace
      NODE_ENV: development
      PORT: 3000
  - name: development
    env:
      LOG_LEVEL: debug
      NODE_ENV: development
  - name: staging
    env:
      LOG_LEVEL: info
      NODE_ENV: production
  - name: production
    env:
      LOG_LEVEL: warn
      NODE_ENV: production
projectName: Mis Portales
projectShortName: misportales
repository:
  enable_tags: true
  repo: afianza-ac/mp-service-idp-adapter
  source: git+ssh://git@github.com/afianza-ac/mp-service-idp-adapter.git
resourcesShortName: mpserviceidpad
secrets: []
tags:
  - ProjectType: InternalTooling
  - Team: Engineering
  - ServiceType: Backend
  - TechStack: Node.js
type: service
```

- [ ] **Step 17: Create `src/migrations/.gitkeep`**

```bash
touch /Users/sito/Documents/afianza/mp-service-idp-adapter/src/migrations/.gitkeep
```

- [ ] **Step 18: Commit**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
git init
git checkout -b feat/idp-adapter-scaffold
git add package.json tsconfig.json tsconfig.build.json nest-cli.json jest.config.js .eslintrc.js .prettierrc commitlint.config.mjs .npmrc .nvmrc .gitignore .env.example mikro-orm.config.ts afianza-ac.yml infra/docker-compose.local.yml src/migrations/.gitkeep
git commit -m "chore: initialize mp-service-idp-adapter project scaffold"
```

---

## Task 2: Config layer

**Files:**
- Create: `src/config/default.config.ts`
- Create: `src/config/local.config.ts`
- Create: `src/config/development.config.ts`
- Create: `src/config/production.config.ts`
- Create: `src/config/test.config.ts`
- Create: `src/config/entra.config.ts`

- [ ] **Step 1: Create directory**

```bash
mkdir -p /Users/sito/Documents/afianza/mp-service-idp-adapter/src/config
```

- [ ] **Step 2: Create `src/config/default.config.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/config/default.config.ts`:

```ts
export const config = () => ({
  postgresql: {
    host: '<env-specific>',
    port: 5432,
    database: '<env-specific>',
    user: '<env-specific>',
    password: '<env-secret>',
  },
});
```

- [ ] **Step 3: Create `src/config/local.config.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/config/local.config.ts`:

```ts
export const config = () => ({
  postgresql: {
    host: 'localhost',
    database: 'mp-service-idp-adapter-local',
    user: 'postgresql',
    password: 'Password123',
  },
});
```

- [ ] **Step 4: Create `src/config/development.config.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/config/development.config.ts`:

```ts
export const config = () => ({
  postgresql: {
    host: 'pd-infra-pgbouncer.plataformadato.svc.cluster.local',
    port: 6432,
    database: 'mp-service-idp-adapter-dev',
    user: 'postgres',
    password: process.env.POSTGRES_PASSWORD,
    applicationName: 'mp-service-idp-adapter-pgbouncer',
  },
});
```

- [ ] **Step 5: Create `src/config/production.config.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/config/production.config.ts`:

```ts
export const config = () => ({
  postgresql: {
    host: 'af-psql-pro.afianza-ac.es',
    database: 'mp-service-idp-adapter-prod',
    user: 'postgres',
    password: process.env.POSTGRES_PASSWORD,
  },
});
```

- [ ] **Step 6: Create `src/config/test.config.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/config/test.config.ts`:

```ts
export const config = () => ({
  postgresql: {
    host: 'localhost',
    database: 'mp-service-idp-adapter-test',
    user: 'postgresql',
    password: 'Password123',
  },
});
```

- [ ] **Step 7: Create `src/config/entra.config.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/config/entra.config.ts`:

```ts
/**
 * Entra ID configuration — loaded directly from env vars at runtime.
 * Not loaded via nest-module-config because these values are IDP-specific
 * and do not vary by cluster environment (they are always the same tenant).
 */
export interface EntraConfig {
  // External ID (B2C / CIAM) — customer-facing portal
  b2c: {
    tenantId: string;
    clientId: string;
    clientSecret: string;
    jwksUri: string; // https://clientesafianza.ciamlogin.com/<tenant>/v2.0/discovery/keys
  };

  // Workforce — employee-facing tools
  workforce: {
    tenantId: string;
    clientId: string;
    clientSecret: string;
    jwksUri: string; // https://login.microsoftonline.com/<tenant>/discovery/v2.0/keys
  };

  // Microsoft Graph API — used for B2B invitations
  graph: {
    clientId: string;
    clientSecret: string;
    tenantId: string;
    inviteRedirectUrl: string;
  };

  // Internal JWT issued by this service to BFFs
  internalJwt: {
    secret: string;
    ttl: string; // e.g. "1h", "15m" — leave blank if decision pending
  };

  // Downstream services
  backofficeApiUrl: string;
}

export function loadEntraConfig(): EntraConfig {
  return {
    b2c: {
      tenantId: process.env.ENTRA_B2C_TENANT_ID ?? '',
      clientId: process.env.ENTRA_B2C_CLIENT_ID ?? '',
      clientSecret: process.env.ENTRA_B2C_CLIENT_SECRET ?? '',
      jwksUri: process.env.ENTRA_B2C_JWKS_URI ?? '',
    },
    workforce: {
      tenantId: process.env.ENTRA_WF_TENANT_ID ?? '',
      clientId: process.env.ENTRA_WF_CLIENT_ID ?? '',
      clientSecret: process.env.ENTRA_WF_CLIENT_SECRET ?? '',
      jwksUri: process.env.ENTRA_WF_JWKS_URI ?? '',
    },
    graph: {
      clientId: process.env.GRAPH_CLIENT_ID ?? '',
      clientSecret: process.env.GRAPH_CLIENT_SECRET ?? '',
      tenantId: process.env.GRAPH_TENANT_ID ?? '',
      inviteRedirectUrl: process.env.GRAPH_INVITE_REDIRECT_URL ?? '',
    },
    internalJwt: {
      secret: process.env.INTERNAL_JWT_SECRET ?? '',
      ttl: process.env.INTERNAL_JWT_TTL ?? '',
    },
    backofficeApiUrl: process.env.BACKOFFICE_API_URL ?? '',
  };
}
```

- [ ] **Step 8: Commit**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
git add src/config/
git commit -m "feat(config): add environment configs and entra.config.ts"
```

---

## Task 3: Domain entity — UserAppAccess

**Files:**
- Create: `src/domain/models/user-app-access.ts`

- [ ] **Step 1: Create directory**

```bash
mkdir -p /Users/sito/Documents/afianza/mp-service-idp-adapter/src/domain/models
```

- [ ] **Step 2: Create `src/domain/models/user-app-access.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/domain/models/user-app-access.ts`:

```ts
import { Entity, Index, PrimaryKey, Property } from '@mikro-orm/postgresql';

/**
 * Records which applications a user is allowed to access.
 *
 * `userExternalId` uses a prefixed format ("entra:oid:<oid>") so the value
 * remains portable if the IDP is ever changed — the prefix makes the source
 * explicit without requiring a schema migration.
 */
@Entity()
export class UserAppAccess {
  @PrimaryKey({ type: 'uuid', defaultRaw: 'gen_random_uuid()' })
  id: string;

  /**
   * Prefixed external user identifier.
   * Format: "entra:oid:<oid>" for Entra ID users.
   */
  @Property()
  @Index()
  userExternalId: string;

  /**
   * The application this record grants access to.
   * Known values: "portalcliente" | "sherpa" | "misfacturas"
   * Open-ended string — add values as new apps are onboarded.
   */
  @Property()
  app: string;

  /**
   * Logical FK to Client in backoffice-api.
   * Nullable — not all users are linked to a client (e.g. employees).
   */
  @Property({ nullable: true })
  clientId?: string;

  /**
   * Logical FK to Employee in backoffice-api.
   * Nullable — not all users are employees.
   */
  @Property({ nullable: true })
  employeeId?: string;

  @Property({ onCreate: () => new Date() })
  createdAt: Date;
}
```

- [ ] **Step 3: Commit**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
git add src/domain/models/user-app-access.ts
git commit -m "feat(domain): add UserAppAccess entity"
```

---

## Task 4: Application layer — HealthcheckController

**Files:**
- Create: `src/application/rest/healthcheck/healthcheck.controller.ts`

- [ ] **Step 1: Create directories**

```bash
mkdir -p /Users/sito/Documents/afianza/mp-service-idp-adapter/src/application/rest/healthcheck
```

- [ ] **Step 2: Create `healthcheck.controller.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/application/rest/healthcheck/healthcheck.controller.ts`:

```ts
import { Controller, Get } from '@nestjs/common';
import { HealthCheck, HealthCheckService, MikroOrmHealthIndicator } from '@nestjs/terminus';

@Controller('healthcheck')
export class HealthcheckController {
  constructor(
    private readonly health: HealthCheckService,
    private readonly db: MikroOrmHealthIndicator,
  ) {}

  @Get()
  @HealthCheck()
  check() {
    return this.health.check([() => this.db.pingCheck('database')]);
  }
}
```

- [ ] **Step 3: Commit**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
git add src/application/rest/healthcheck/healthcheck.controller.ts
git commit -m "feat(application): add healthcheck controller"
```

---

## Task 5: AppModule and main.ts

**Files:**
- Create: `src/app.module.ts`
- Create: `src/main.ts`

- [ ] **Step 1: Create `src/app.module.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/app.module.ts`:

```ts
import { MiddlewareConsumer, Module, NestModule, RequestMethod } from '@nestjs/common';
import { asyncLocalStorage, HttpLoggerMiddleware } from '@afianza-ac/nest-module-logger';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { MikroOrmModule } from '@mikro-orm/nestjs';
import { getEnvironmentConfig } from '@afianza-ac/nest-module-config';
import { PostgreSqlDriver } from '@mikro-orm/postgresql';
import { HealthcheckController } from './application/rest/healthcheck/healthcheck.controller';
import { TerminusModule } from '@nestjs/terminus';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      load: [getEnvironmentConfig],
    }),
    MikroOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (configService: ConfigService) => ({
        entities: ['./dist/src/domain/models/*.js'],
        entitiesTs: ['./src/domain/models/*.ts'],
        driver: PostgreSqlDriver,
        dbName: configService.get('postgresql.database'),
        user: configService.get('postgresql.user'),
        password: configService.get('postgresql.password'),
        host: configService.get('postgresql.host'),
        port: Number(configService.get('postgresql.port')),
      }),
      inject: [ConfigService],
    }),
    TerminusModule.forRoot(),
  ],
  controllers: [HealthcheckController],
  providers: [],
})
export class AppModule implements NestModule {
  configure(consumer: MiddlewareConsumer) {
    consumer.apply(HttpLoggerMiddleware).exclude({ path: 'healthcheck', method: RequestMethod.GET }).forRoutes('*');
  }
}
```

- [ ] **Step 2: Create `src/main.ts`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/src/main.ts`:

```ts
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { ValidationPipe, VersioningType } from '@nestjs/common';
import { CorrelationIdInterceptor, LokiLoggerService, asyncLocalStorage } from '@afianza-ac/nest-module-logger';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    logger: new LokiLoggerService({
      logLevel: process.env.LOG_LEVEL || 'info',
      loggerStorage: asyncLocalStorage,
      lokiUrl: process.env.LOKI_URL,
      serviceName: 'mp-service-idp-adapter',
      environment: process.env.SERVICE_ENV || 'local',
    }),
    bufferLogs: true,
  });

  app.useGlobalPipes(new ValidationPipe({ transform: true }));

  app.useGlobalInterceptors(new CorrelationIdInterceptor(asyncLocalStorage));

  app.enableVersioning({
    type: VersioningType.URI,
  });

  const config = new DocumentBuilder()
    .setTitle('mp-service-idp-adapter')
    .setDescription('IDP adapter — exchanges Entra ID Authorization Code for internal JWT')
    .setVersion('1.0')
    .addServer('/', 'local')
    .build();
  const documentFactory = () => SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('docs', app, documentFactory);

  await app.listen(process.env.PORT ?? 3000);
}
void bootstrap();
```

- [ ] **Step 3: Commit**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
git add src/app.module.ts src/main.ts
git commit -m "feat: add AppModule and main.ts bootstrap"
```

---

## Task 6: Install dependencies and verify build

- [ ] **Step 1: Install npm dependencies**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
npm install
```

Expected: npm resolves all packages and creates `package-lock.json`. The `@afianza-ac/*` packages will be fetched from GitHub Packages — this requires a valid `NODE_AUTH_TOKEN` or `NPM_TOKEN` set in the environment (same token used in `mp-service-portalcliente-api`).

If `@afianza-ac` packages are not accessible, copy `node_modules/@afianza-ac/` from `mp-service-portalcliente-api` as a workaround:

```bash
mkdir -p /Users/sito/Documents/afianza/mp-service-idp-adapter/node_modules/@afianza-ac
cp -r /Users/sito/Documents/afianza/mp-service-portalcliente-api/node_modules/@afianza-ac/* \
      /Users/sito/Documents/afianza/mp-service-idp-adapter/node_modules/@afianza-ac/
```

- [ ] **Step 2: Run build**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
npm run build
```

Expected output: NestJS compiles to `dist/` with no TypeScript errors. The last line should be something like `webpack compiled successfully` or `Successfully compiled`.

If there are import errors for `@afianza-ac/*`, see the workaround in Step 1.

- [ ] **Step 3: Run tests (should pass — no spec files yet, so suite is empty)**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
npm test
```

Expected: `Test Suites: 0 passed` or Jest exits 0 (no test files found is not a failure with current jest.config).

- [ ] **Step 4: Commit**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
git add package-lock.json
git commit -m "chore: add package-lock.json after npm install"
```

---

## Task 7: Initial MikroORM migration for UserAppAccess

> Note: Migrations require a running PostgreSQL instance. Run `npm run infra:up` first. After the migration is created, it must be verified clean.

- [ ] **Step 1: Start local PostgreSQL**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
npm run infra:up
```

Expected: Docker starts `pd_postgres` on port 5433.

- [ ] **Step 2: Create a `.env` from the example**

```bash
cp /Users/sito/Documents/afianza/mp-service-idp-adapter/.env.example \
   /Users/sito/Documents/afianza/mp-service-idp-adapter/.env
```

- [ ] **Step 3: Create the initial migration**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
npm run migrations:create-initial
```

Expected: A new file `src/migrations/Migration<timestamp>.ts` is created with a `CREATE TABLE user_app_access` statement.

- [ ] **Step 4: Verify no pending schema changes**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
npx mikro-orm migration:create --dump
```

Expected output: `No changes required` (confirms the migration fully captures the entity schema).

- [ ] **Step 5: Commit**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
git add src/migrations/
git commit -m "feat(migrations): add initial migration for UserAppAccess"
```

---

## Task 8: CLAUDE.md for the new service

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create `CLAUDE.md`**

Create `/Users/sito/Documents/afianza/mp-service-idp-adapter/CLAUDE.md`:

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Serena MCP — CRITICAL: Mandatory for Code Operations

> **CRITICAL**: When the Serena MCP server is available, you **MUST** use Serena's semantic tools as the **primary method** for reading, exploring, and editing code. This applies to the **main session, ALL agents, and ALL subagents** — no exceptions.

**Why**: Serena's semantic tools consume significantly less context than native tools. They allow reading only symbols, signatures, or specific function bodies instead of entire files.

**Strategy**: Always read code progressively — start with `get_symbols_overview` or `find_symbol` with `include_body=false`, then read only the specific symbol bodies you need with `include_body=true`. Avoid reading full files unless strictly necessary.

**Fallback**: Use native tools when Serena is unavailable or doesn't support the file format.

## Superpowers Workflow — CRITICAL: Context Management

Each superpowers workflow phase (brainstorm → plan → execution → review) should run in a separate session. When completing a phase:

1. Provide the path to the generated file
2. Tell the user which skill to invoke next and with what arguments (so they can copy-paste after clearing context)
3. Suggest the user to clean context

## Project Overview

NestJS microservice — IDP Adapter for the Afianza platform.

**Responsibilities**:
1. Receives the Authorization Code callback from Entra ID (Workforce + External ID)
2. Validates the Entra JWT using `jose` + JWKS endpoint
3. Queries `UserAppAccess` to determine which apps the user can access
4. Emits a signed internal JWT with app permission claims
5. Exposes a JWKS endpoint so BFFs can validate the internal JWT

**Stack**: NestJS 10, MikroORM 6 (PostgreSQL), `jose` 5, TypeScript 5.7

## Scope & Rules

### What AI CAN touch:
- `src/application/` - controllers, DTOs
- `src/domain/` - services, models
- `src/infrastructure/` - external API clients (Entra token exchange, Graph API)
- `src/config/` - environment configs

### What AI CANNOT touch:
- Anything outside the `src` folder except `package.json`
- `src/migrations/` - humans only, never generate or modify
- `app.module.ts` - only with explicit approval

### Development Approach
- **TDD**: Write/update tests for any code you modify
- **Incremental**: Small, focused changes
- **Ask first**: When in doubt about scope, ask before proceeding

## Essential Commands

```bash
# Development
npm run start:dev              # Start with watch mode
npm run infra:up               # Start PostgreSQL via Docker

# Testing
npm run test                   # Run all tests
npm run test -- --testNamePattern="pattern"
npm run test -- src/path/to/file.spec.ts

# Database
npm run migrations:up          # Apply pending migrations

# Code quality
npm run lint                   # ESLint with auto-fix
npm run format                 # Prettier formatting
```

## Architecture

Monolithic NestJS service with strict layering (no NestJS sub-modules):

```
src/
├── application/           # REST controllers (DTOs here)
│   └── rest/[feature]/dto/
├── domain/
│   ├── models/            # MikroORM entities (UserAppAccess)
│   └── services/          # Business logic (token validation, JWT emission)
├── infrastructure/        # External API clients (Entra token exchange, Graph)
└── config/                # Per-environment + entra.config.ts
```

### Layer Rules

1. **Application -> Domain -> Infrastructure** (never skip layers)
2. DTOs never cross into domain layer — map to domain objects first
3. Controllers/subscribers contain NO business logic
4. Only domain services can call infrastructure
5. All services registered directly in `app.module.ts` (no NestJS sub-modules)

### MikroORM Patterns

- **Reads**: `findOne(..., { disableIdentityMap: true })` — no fork needed
- **Writes**: `const em = this.em.fork()` before any upsert/create/assign/flush

## Key Domain Concepts

| Concept | Description |
|---------|-------------|
| `userExternalId` | Prefixed format `entra:oid:<oid>` — portable across IDP changes |
| `app` | App identifier string: `"portalcliente"`, `"sherpa"`, `"misfacturas"` |
| Internal JWT | Signed by `INTERNAL_JWT_SECRET`, validated by BFFs via `/jwks` endpoint |
| JWKS endpoint | `GET /.well-known/jwks.json` — public keys for BFF validation |

## Local Development

Default ports: App 3000, PostgreSQL **5433** (to avoid conflict with other services)
Local DB: `mp-service-idp-adapter-local` / user: `postgresql` / pass: `Password123`

Swagger docs: `http://localhost:3000/docs`
```

- [ ] **Step 2: Commit**

```bash
cd /Users/sito/Documents/afianza/mp-service-idp-adapter
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md for mp-service-idp-adapter"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Copy structure from `mp-service-portalcliente-api` → Tasks 1–5 copy all tooling/config files and strip RabbitMQ
- [x] Clean what doesn't apply (Sample entity/controller/service/subscriber) → Not created; only healthcheck and UserAppAccess
- [x] Install `jose` → Added to `package.json` dependencies in Task 1
- [x] `UserAppAccess` entity with all required fields → Task 3
- [x] Initial MikroORM migration → Task 7
- [x] `entra.config.ts` with all required env vars → Task 2, Step 7
- [x] `package.json` name = `mp-service-idp-adapter`, no RabbitMQ deps → Task 1
- [x] `npm run build` passes → Task 6
- [x] CLAUDE.md → Task 8

**Type consistency:** `UserAppAccess` entity defined once in Task 3, referenced by `mikro-orm.config.ts` glob `./src/domain/models/*.ts` — no manual import needed.

**No placeholders:** All steps contain exact file contents and commands.
