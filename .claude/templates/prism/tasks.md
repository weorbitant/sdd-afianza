# Tasks — [FEATURE NAME]

**Feature**: `specs/[###-feature-name]/`
**Generated**: [DATE]
**Spec**: [link] | **Plan**: [link]
**Phase**: `TASKS`

---

## Format

```
- [ ] T-NNN [P?] [US-NN?] Description — `path/to/file.ts`
```

- `[P]` = parallelizable (no dependency on incomplete tasks, different files)
- `[US-NN]` = user story this task belongs to (required for story phases)
- Tasks marked `- [x]` are complete

---

## Phase 1 — Setup

*Project infrastructure, dependencies, migrations. No story label.*

- [ ] T-001 Create MikroORM migration for [entity] — `[service]/src/infrastructure/database/migrations/`
- [ ] T-002 Register new entities in MikroORM config — `[service]/mikro-orm.config.ts`
- [ ] T-003 [Setup task 3] — `path`

**Gate**: All setup tasks done + `npm run migrations:up` passes before Phase 2.

---

## Phase 2 — Domain layer

*Core domain entities and logic. No story label. Blocks all story phases.*

- [ ] T-010 [P] Create `[Entity]` domain entity — `src/domain/[entity]/[entity].entity.ts`
- [ ] T-011 [P] Create `[Entity]` repository interface — `src/domain/[entity]/[entity].repository.ts`
- [ ] T-012 Write unit tests for domain invariants — `src/domain/[entity]/[entity].spec.ts`

**Gate**: Domain tests pass before story phases begin.

---

## Phase 3 — US-01: [Title]

*Goal: [one sentence describing what US-01 delivers]*
*Independent test: [how to verify this US alone works end-to-end]*

- [ ] T-020 [US-01] Implement `[UseCase]` use case — `src/application/[use-case].ts`
- [ ] T-021 [P] [US-01] Create REST endpoint `POST /[resource]` — `src/application/rest/[resource].controller.ts`
- [ ] T-022 [P] [US-01] Create DTO `Create[Resource]Dto` — `src/application/rest/dto/`
- [ ] T-023 [US-01] Write integration test for `POST /[resource]` — `test/[resource].e2e-spec.ts`

---

## Phase 4 — US-02: [Title]

*Goal: [one sentence]*
*Independent test: [how to verify]*

- [ ] T-030 [US-02] [Task] — `path`
- [ ] T-031 [P] [US-02] [Task] — `path`

---

## Phase N — AMQP (cross-service)

*Events published/consumed by this feature.*

- [ ] T-050 [P] Implement `[Event]Publisher` — `src/application/amqp/publishers/`
- [ ] T-051 [P] Implement `[Event]Subscriber` in [service] — `[service]/src/application/amqp/`
- [ ] T-052 Write AMQP integration test — `test/amqp/`

---

## Phase N+1 — Polish

*Cross-cutting concerns, final validation.*

- [ ] T-060 Run `npm run lint:fix` across changed files
- [ ] T-061 Run full test suite — confirm all tests pass
- [ ] T-062 Review spec compliance — no FR left unimplemented
- [ ] T-063 Update CLAUDE.md plan reference if needed

---

## Dependencies

```
Phase 1 (Setup)
  └── Phase 2 (Domain)
        ├── Phase 3 (US-01)
        │     └── Phase N (AMQP)
        ├── Phase 4 (US-02)
        └── Phase N+1 (Polish)
```

---

## Parallel opportunities

- T-020 + T-021 + T-022 can run in parallel (same US, different files)
- T-030 + T-040 can run in parallel (different US, no shared files)

---

## MVP scope

Minimum to demonstrate value: **Phase 1 + Phase 2 + Phase 3 (US-01 only)**.
