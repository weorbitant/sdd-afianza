---
name: "prism-gate"
description: "Check whether the current feature meets the entry/exit criteria for its phase and what's needed to advance. Use before switching phases."
argument-hint: "Optional: target phase to check (e.g. 'DESIGN', 'TASKS', 'IMPLEMENT')"
user-invocable: true
disable-model-invocation: false
---

## Active PRISM state

```json
!`cat .prism/state.json 2>/dev/null || echo '{"active_feature":null,"phase":"NONE"}'`
```

## Feature directory contents

```
!`FEAT=$(cat .prism/state.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('active_feature',''))" 2>/dev/null); [ -n "$FEAT" ] && find "$FEAT" -maxdepth 2 -type f | sort || echo "No active feature"`
```

## Outline

### 1. Determine current phase and target phase

- Read `active_feature` and `phase` from state.
- If ARGUMENTS specifies a target phase (e.g., "DESIGN"), check what's needed to reach it.
- Otherwise, check exit criteria for the current phase and entry criteria for the next.

### 2. Run gate checks

For each phase, the criteria are:

#### DISCOVER → SPECIFY
- [ ] `discovery.md` exists in feature dir
- [ ] `discovery.md` has at least one section filled (not all placeholders)

#### SPECIFY → REFINE
- [ ] `spec.md` exists
- [ ] `spec.md` has Executive Summary (non-empty)
- [ ] `spec.md` has at least 1 User Story with acceptance criteria
- [ ] `spec.md` has at least 3 FRs
- [ ] Section 9 (Compliance & Data) filled
- [ ] ≤ 3 NEEDS CLARIFICATION markers remaining

#### REFINE → DECIDE (ADRs)
- [ ] All NEEDS CLARIFICATION resolved (grep spec.md for the marker)
- [ ] No ⛔ BLOCKING items outstanding in clarifications log
- [ ] User stories have tracker keys assigned (or explicitly skipped)

#### DECIDE → DESIGN (plan)
- [ ] All non-trivial architectural decisions have a corresponding ADR in `adrs/`
- [ ] All ADRs have `status: accepted` or `status: rejected` (none in `proposed` state)

#### DESIGN → POC (if required)
- [ ] `plan.md` exists
- [ ] `plan.md` has Technical Context filled
- [ ] `plan.md` has Risk Assessment section
- [ ] If PoC marked required in plan.md: `poc.md` exists

#### POC → TASKS
- [ ] If PoC exists: `poc.md` has `status: go` or `status: go-with-constraints`
- [ ] `plan.md` has Source Structure section filled

#### TASKS → IMPLEMENT
- [ ] `tasks.md` exists
- [ ] `tasks.md` has at least one unchecked task
- [ ] All Phase 1 (Setup) tasks are listed

#### IMPLEMENT → REVIEW
- [ ] All tasks in `tasks.md` marked `[x]`
- [ ] Test suite passes (check with `npm test` if possible)

#### REVIEW → DONE
- [ ] Code review completed (prism-review ran)
- [ ] No blocking findings outstanding

### 3. Output gate report

For each criterion in the current → next phase transition:

```
GATE: [CURRENT_PHASE] → [NEXT_PHASE]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ spec.md exists
✅ At least 1 US with AC
❌ Section 9 (Compliance) — empty, must be filled
❌ 2 NEEDS CLARIFICATION remain → run /prism-clarify

STATUS: BLOCKED (2 items)
Next action: [exact command to run]
```

### 4. If all criteria met

Output:
```
GATE PASSED ✅
You can advance to [NEXT_PHASE].
Run: /prism-[next-skill]
```

And update `.prism/state.json` phase to the next phase.

## Key rules

- Never advance phase if any ❌ BLOCKING criterion fails. Warn but don't modify state.
- Items that are optional (e.g., PoC when not required) show as `(optional — skipped)` not ❌.
- If no active feature in state, output: "No active feature. Run /prism-specify first."
