---
description: Extract structural decisions from spec.md / plan.md / research.md into per-feature ADR files (Nygard format). Selective filter — not every clarification becomes an ADR. Idempotent and append-only.
---

# Speckit — Decisions Extract (ADR generator)

Generate Architecture Decision Records (ADRs) for the active feature from
the design artifacts that already capture decisions implicitly.

## Inputs

Active feature dir resolved via `.specify/scripts/bash/check-prerequisites.sh --json --paths-only`. Reads:

- `spec.md` → sections `## Clarifications`, `## Open Questions`
- `plan.md` → sections `## Constitution Check`, `## Complexity Tracking`
- `research.md` → every `## R-XXX` block

## Output

Per-feature ADR folder: `<FEATURE_DIR>/decisions/`

```
decisions/
├── README.md                              ← auto-generated index
├── 0001-<kebab-title>.md
├── 0002-<kebab-title>.md
└── ...
```

## Selection filter

A decision becomes an ADR **only if** it satisfies AT LEAST ONE:

1. Appears in `research.md` as a numbered `R-XXX` block.
2. Resolves an `Open Question` marked **Critical** or **High** impact.
3. Appears in `plan.md` → `## Complexity Tracking` as a justified violation.
4. The decision touches one of:
   - Public API surface (new endpoint, breaking change)
   - AMQP contract (new event, schema change)
   - Data model (new table, FK, constraint, or index)
   - Migration strategy (data migrations, backfills)
   - A Constitution principle (gate pass/fail justification)
   - Cross-service interaction pattern

**Skip** (stays in `## Clarifications` only):
- Wording fixes, AC rewrites without behavioral change
- UX micro-decisions (button placement, copy)
- Documentation-only changes
- Scope clarifications that don't change architecture

## ADR template (Nygard-light)

```markdown
# ADR-NNNN: <Title in imperative>

**Status**: Accepted | Superseded by ADR-XXXX | Deprecated
**Date**: YYYY-MM-DD
**Story**: US1 | US2 | All
**Sources**: spec.md#clarifications-YYYY-MM-DD, research.md#R-XXX, etc.

## Context

[Why this decision came up. Constraints and forces at play. Existing state.]

## Decision

[The decision, imperative form, one or two sentences.]

## Consequences

- ✅ [Positive outcome]
- ⚠️ [Tradeoff or risk]
- ❌ [Cost incurred]

## Alternatives Considered

- **<Name>**: [Why rejected]
- **<Name>**: [Why rejected]
```

## Index (`decisions/README.md`)

Auto-generated. Format:

```markdown
# Decision Log — <Feature name>

| ADR | Title | Status | Story | Date |
|-----|-------|--------|-------|------|
| [0001](0001-...md) | Title in plain language | Accepted | All | 2026-05-25 |
| [0002](0002-...md) | Title | Superseded by [0008](0008-...md) | All | 2026-05-25 |
```

## Idempotence rules

1. **Existing ADR files are never overwritten.** If `0008-single-bucket-validation.md` already exists, skip — even if its content differs from what the extractor would produce now. The user may have enriched `Consequences` or `Context` manually.
2. **Only assign new ADR numbers to genuinely new decisions.** Numbering is sequential per feature; never reused.
3. **Supersedes detection**: when a new clarification contradicts an earlier ADR's `Decision` (heuristic: same scope, opposite outcome — e.g. "two-bucket" → "single-bucket"), mark the older ADR's status as `Superseded by ADR-NNNN` and add a `Supersedes: ADR-MMMM` line on the new one. If the heuristic is uncertain, surface to the user before modifying any file.
4. **README.md is always regenerated** from the files on disk; no manual edits to it are preserved.

## Numbering

Per feature, starting at `0001`. Independent of other features. Filenames `NNNN-kebab-case-title.md` where NNNN is 4-digit zero-padded.

## Execution steps

1. **Setup**: Run `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` and parse FEATURE_DIR.
2. **Read sources**: `spec.md`, `plan.md`, `research.md` from FEATURE_DIR.
3. **List existing ADRs**: scan `<FEATURE_DIR>/decisions/*.md` (excluding README.md) and parse their YAML frontmatter to know what's already recorded.
4. **Extract candidates**: apply the selection filter. For each candidate, build an ADR draft (title, context, decision, consequences, alternatives) using the source content. The extractor MAY rephrase to imperative; it MUST cite sources verbatim in the `Sources` line.
5. **Detect supersedes**: for each candidate, check if it contradicts an existing ADR. If yes, queue the older ADR for status update.
6. **Write new ADR files**. Skip if filename collision.
7. **Apply supersedes updates** to existing ADRs (this is the only allowed in-place edit — and only on the `**Status**:` line).
8. **Regenerate `decisions/README.md`** from the current state on disk.
9. **Report**: list ADRs created, ADRs marked superseded, candidates skipped (and why), and the path to the index.

## Behavior rules

- If `<FEATURE_DIR>/decisions/` doesn't exist, create it.
- Never silently overwrite ADR files. If an ADR file with the target name already exists but has different content from the new extraction, skip and note in the report (the user can `rm` and re-run if they want regeneration).
- If filtering excludes ALL candidates, exit with a friendly message and don't create an empty `decisions/` folder.
- ADR titles must be < 80 characters and in imperative form.
- Use English in ADR content. (Spec/research may be Spanish; the ADR translates the decision to English for portability — Anglo conventions.)
- Always set `Status: Accepted` for new ADRs unless the source artifact explicitly marks the decision as provisional / pending PO confirmation, in which case use `Status: Proposed`.
