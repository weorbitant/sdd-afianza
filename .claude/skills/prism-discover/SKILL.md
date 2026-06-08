---
name: "prism-discover"
description: "Phase 0 — Explore the codebase before writing a spec. Finds existing code, AMQP events, REST endpoints, data models, and cross-service drift related to the feature. Produces discovery.md in the feature directory."
argument-hint: "Feature description or keywords to search for (e.g. 'client team assignments')"
user-invocable: true
disable-model-invocation: false
---

## Input

```
$ARGUMENTS
```

## Active PRISM state

```json
!`cat .prism/state.json 2>/dev/null || echo '{"active_feature":null,"phase":"NONE"}'`
```

## Existing specs

```
!`ls specs/ 2>/dev/null | sort`
```

## Outline

### 1. Locate or create the feature directory

- If `active_feature` in state is non-null, use that directory.
- Otherwise, determine the next sequential number from `specs/` and create `specs/NNN-[short-name]/`.
  - Short name: 2-4 words from ARGUMENTS, kebab-case.
- Update `.prism/state.json`: set `active_feature` to the chosen path, `phase` to `"DISCOVER"`, `last_updated` to today.

### 2. Determine search keywords

Extract 3-6 search terms from ARGUMENTS. Examples: entity names, service names, event names, domain verbs.

### 3. Explore the codebase

Run these probes in parallel. For each result, note the service, file path, and a one-line description.

**a. Domain entities** — find matching model/entity files:
```
grep -rli "[keyword]" */src --include="*.entity.ts" --include="*.model.ts" 2>/dev/null | head -20
```

**b. Use cases / services**:
```
grep -rli "[keyword]" */src --include="*.service.ts" --include="*.use-case.ts" 2>/dev/null | head -20
```

**c. REST endpoints** — find controllers with matching routes:
```
grep -rli "[keyword]" */src --include="*.controller.ts" 2>/dev/null | head -10
```

**d. AMQP — publishers**:
```
grep -rli "[keyword]" */src/application/amqp --include="*.ts" 2>/dev/null | head -10
```

**e. AMQP — subscribers**:
```
find . -path "*/application/amqp/*subscriber*" -name "*.ts" 2>/dev/null | xargs grep -li "[keyword]" 2>/dev/null | head -10
```

**f. Existing specs** — check if there's a related spec already:
```
grep -rli "[keyword]" specs/ --include="*.md" 2>/dev/null | head -10
```

For each found file: skim it (read top 40 lines) to extract relevant entity fields, routing keys, method signatures, or invariants.

### 4. Cross-service drift check

For each entity name found (e.g., `ClientAssignment`), run:
```
grep -rli "[EntityName]" */src --include="*.ts" 2>/dev/null
```

List which services have their own version and note obvious field differences. This is the drift section.

### 5. Synthesize

Based on everything found, write `FEATURE_DIR/discovery.md` using the template at `.claude/templates/prism/discovery.md`.

Fill each section:
- **Related code found**: table of service + file + notes
- **AMQP events (existing)**: routing keys, publishers, consumers, payload summary
- **REST endpoints (existing)**: method + path + service
- **Data models (existing)**: entity + service + key fields
- **Drift detected**: inconsistencies across services
- **Missing coverage**: what doesn't exist yet
- **Key constraints**: things spec must respect
- **Open questions for spec**: 3-5 questions discovered during exploration

### 6. Report

Output:
- Path to `discovery.md`
- Summary table: N entities found, N AMQP events, N REST endpoints, N drift items, N open questions
- Suggested next command: `/prism-specify`

## Key rules

- Never write spec.md in this phase — discovery only.
- Probe by grepping, not by reading entire files. Skim selectively.
- If no code found: output "No existing code found for [keywords]" and create an empty discovery.md noting the clean-slate context.
- Use `grep -rli` (case-insensitive, filenames only) for broad scan, then targeted `grep -n` to find exact lines.
