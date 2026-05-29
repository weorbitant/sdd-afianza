---
description: "Evaluate the active feature's spec.md against the project quality rubric and emit readiness-report.md. Read-only — does not modify spec.md."
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
---

# Speckit Ready

Evaluate whether the active feature's `spec.md` is ready for `/speckit-plan`.

`/speckit-ready` scores the spec against `.specify/quality-rubric.md` (8 criteria) and produces `readiness-report.md` with:

- A **global verdict**: ✅ READY, ⚠️ READY-WITH-RISKS, or ❌ NOT-READY.
- **Per-criterion findings** with concrete evidence (quotes or file pointers).
- A **prioritized action plan** listing the exact commands to run to reach READY.

**Read-only.** The only file written is `readiness-report.md`. `spec.md` is never modified.

**Advisory.** This command does not block `/speckit-plan`. It is the human's responsibility to act on the report. If the verdict is NOT-READY and you run `/speckit-plan` anyway, the resulting plan is likely to have gaps.

## Usage

```
/speckit-ready                      # evaluate the active feature
```

No arguments. The rubric version applied is whatever is in `.specify/quality-rubric.md` at the time of execution.

## Where it fits in the refinement flow

```
/speckit-specify
  ↓
/speckit-clarify
  ↓
/speckit-challenge functional
  ↓
/speckit-atlassian-sync-push      (optional, if PO input needed)
  ↓
/speckit-ready                    ← GATE: are we ready to plan?
  ↓
/speckit-plan
```

If the report comes back NOT-READY, run the suggested remediation commands and re-run `/speckit-ready` until it returns READY or READY-WITH-RISKS (the latter is an accepted-risk decision by the user).

## Execution Steps

### 1. Resolve paths and load context

Run `{SCRIPT}` from repo root. Parse JSON for `FEATURE_DIR` and `AVAILABLE_DOCS`. Derive:

- `SPEC = FEATURE_DIR/spec.md` — required.
- `DECISIONS = FEATURE_DIR/decisions.md` — optional context.
- `RUBRIC = <repo root>/.specify/quality-rubric.md` — required.
- `PROJECT_CLAUDE = <repo root>/CLAUDE.md` — project context (helps disambiguate cross-service / NFR signals).
- `REPORT = FEATURE_DIR/readiness-report.md` — output (created or overwritten).

**Abort with a clear message** if `spec.md` or `.specify/quality-rubric.md` is missing.

Announce to the user:

```
Running /speckit-ready on <FEATURE_DIR>
  Rubric: .specify/quality-rubric.md (version <rubric_version from frontmatter>)
  Output: <FEATURE_DIR>/readiness-report.md
```

### 2. Evaluate the spec against each criterion

Load the rubric in full. For each of the 8 criteria (C1..C8), perform a structured evaluation against `spec.md`:

For every criterion, determine:

1. **Status**: ✅ pass, ⚠️ risk, or ❌ fail, applying the exact thresholds defined in the rubric.
2. **Evidence**: cite the source. Use one of:
   - A direct quote of ≤2 lines from `spec.md` followed by `(spec.md:L<line>)`.
   - A pointer to the missing section ("No section matching 'Out of scope' or equivalent").
   - For cross-service (C4): the list of services detected and what is missing.
3. **Remediation**: copy from the rubric's `Remediación` block for that criterion. If multiple options apply, pick the one most aligned with the failure mode and explain the choice in one short sentence.

**Important constraints**:

- Do NOT invent evidence. If the spec does not contain a section or claim, say so explicitly.
- Do NOT make assumptions about intent. Score what is written, not what you guess the author meant.
- For C4 (cross-service): use the polyrepo service list from `CLAUDE.md` to detect cross-service mentions. The afianza polyrepo services share the prefixes `pc-`, `pgi-`, `pd-`, `af-`.
- For C5 (NFRs): the rubric requires NFRs **proportional to the scope** — a single-service read-only endpoint needs less than a multi-service write with personal data. Use judgment but explain it in the evidence.

### 3. Compute the global verdict

Apply the rule from the rubric:

```
reds   = count(criteria where status == ❌)
ambers = count(criteria where status == ⚠️)

if reds > 0:           verdict = NOT-READY
elif ambers >= 3:      verdict = NOT-READY
elif ambers >= 1:      verdict = READY-WITH-RISKS
else:                  verdict = READY
```

### 4. Build the prioritized action plan

If verdict is READY, skip this step (no action plan needed).

Otherwise, group the failing criteria (❌ first, then ⚠️) by remediation command. Order commands by where they fit in the refinement flow:

1. `/speckit-discover` (if any criterion suggests upstream gaps in problem/users/metrics).
2. `/speckit-clarify` (for AC concretion, NFR gaps, scope boundaries).
3. `/speckit-challenge functional` (for cross-service, edge cases, business-logic gaps).
4. `/speckit-atlassian-sync-push` (only if there are open QUESTION-PO needing external input).

For each command in the action plan, list which criteria it addresses, e.g.:

```
1. /speckit-challenge functional   → resolves C4-cross-service, C8-edge-cases
2. /speckit-clarify                → resolves C2-testable-ac (AC of US-3), C5-nfrs
3. /speckit-ready                  → re-evaluate
```

Always use the full ID (`C<N>-<slug>`) in findings, action plan, and references — never just `C<N>`.

### 5. Write the report

Write `readiness-report.md` using this exact structure (replace placeholders, keep emoji, keep section headings):

```markdown
# Readiness Report — <feature-name>

**Verdict**: <✅ READY | ⚠️ READY-WITH-RISKS | ❌ NOT-READY>
**Generated**: <ISO 8601 timestamp>
**Rubric version**: <rubric_version from frontmatter>
**Spec evaluated**: spec.md (last modified <ISO 8601 mtime>)

## Summary

| ID                  | Criterion                          | Status |
|---------------------|------------------------------------|--------|
| C1-problem-scope    | Problem & scope boundaries         | <✅/⚠️/❌> |
| C2-testable-ac      | User stories con AC testables      | <✅/⚠️/❌> |
| C3-domain-model     | Domain model esbozado              | <✅/⚠️/❌> |
| C4-cross-service    | Cross-service touchpoints          | <✅/⚠️/❌> |
| C5-nfrs             | NFRs explícitos                    | <✅/⚠️/❌> |
| C6-open-questions   | Open questions resueltas/diferidas | <✅/⚠️/❌> |
| C7-success-metrics  | Métricas de éxito                  | <✅/⚠️/❌> |
| C8-edge-cases       | Edge cases catalogados             | <✅/⚠️/❌> |

**Totals**: <N> ✅ · <N> ⚠️ · <N> ❌

## Findings

<For each criterion where status != ✅, emit a block. Skip ✅ criteria entirely.>

### <✅/⚠️/❌> <full-id e.g. C4-cross-service> — <criterion name>

**Evidence**: <quote or pointer>

**Remediation**: <command from rubric> — <one-sentence rationale>

---

<If verdict == READY, skip "Action Plan" section. Otherwise:>

## Action Plan

To reach READY, run in this order:

1. `<command>` — addresses <criteria list>
2. `<command>` — addresses <criteria list>
3. `/speckit-ready` — re-evaluate

## Notes

<Optional. Include here any judgment calls made during scoring (especially around C4 cross-service detection and C5 NFR proportionality) that the human should validate.>
```

### 6. Print summary to the user

After writing the report, print to stdout (do not include in the report file):

```
/speckit-ready completed.

Verdict: <verdict>
Score:   <N> ✅ · <N> ⚠️ · <N> ❌

<If READY:>
The spec is ready for /speckit-plan.

<If READY-WITH-RISKS:>
The spec has accepted risks (see <FEATURE_DIR>/readiness-report.md). You may proceed
to /speckit-plan, but review the ⚠️ findings first.

<If NOT-READY:>
The spec is not ready. Next action:
  → <first command from action plan>

Full report: <FEATURE_DIR>/readiness-report.md
```

## Design notes (for maintainers)

- **No sub-agents.** `/speckit-ready` is a single-pass evaluation. If we ever want to parallelize (e.g., one agent per criterion), we can split — but for now the rubric is short enough to evaluate inline.
- **Rubric versioning.** The report records the `rubric_version` so that older reports can be diffed against newer rubric versions if criteria change.
- **No history.** Every run overwrites `readiness-report.md`. Use git if you want to compare runs.
- **Not a hard gate.** This is intentional. If we later want `/speckit-plan` to abort on NOT-READY, that's a change in `/speckit-plan`, not here.
