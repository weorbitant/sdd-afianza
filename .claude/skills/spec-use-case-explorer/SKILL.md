---
name: spec-use-case-explorer
description: Stress-test a feature spec by generating use cases from normal to extreme,
  one at a time interactively. Use when reviewing a spec for gaps, undefined behavior,
  or missing edge cases — even if the user just says "review this spec", "find holes 
  in this", or "check my ACs".
argument-hint: "<spec content or path to spec file>"
allowed-tools: AskUserQuestion, mcp__atlassian__createJiraIssue
---

# Spec Use Case Explorer

Stress-test a feature spec interactively — one use case at a time, ordered from most 
normal to most extreme, exposing undefined behavior, ambiguous logic, and functional gaps.

## Usage

```
/spec-use-case-explorer $ARGUMENTS
```

## Process

### Step 1 — Assess the spec

Read the spec provided in $ARGUMENTS. Silently extract:
- Primary actor(s) and trigger(s)
- Main action and expected outcome
- Explicit constraints or edge cases already covered
- Number of distinct flows or features described

### Step 2 — Calibrate case volume

Calculate a **Spec Density Score**:

- Count distinct user-facing flows (each user story, AC block, or numbered requirement = 1)
- Count edge/error cases already explicitly covered

| Flows detected | Cases already covered | Total cases to generate |
|---|---|---|
| 1–3 | Any | 8–10 |
| 4–7 | 0–2 | 12–15 |
| 4–7 | 3+ | 10–12 |
| 8+ | 0–3 | 16–20 |
| 8+ | 4+ | 12–15 |

Output a one-line diagnostic before starting:

> 🔍 **Spec scan:** X flows detected, Y edge cases already covered → generating Z use cases.

Then immediately present **Case 1** (do not wait for the user to ask).

### Step 3 — Present cases one at a time

For each case, follow this exact structure:

---

**Caso N / Z** · `<Categoría>` · Gravedad: `<Baja/Media/Alta>`

Write the case as a **narrated example** with real data:

1. **Contexto** — Set up the scenario with concrete actors, names, dates, and numbers
   drawn from the domain of the spec. Never use generic placeholders like "User A" or
   "Entity X" — invent plausible names (e.g. "Construcciones Martínez S.L.", "María Sánchez").

2. **Visual aid** — Include a table or diagram whenever it clarifies the scenario:
   - Use **before/after tables** when the case involves a state change (e.g. task reassignment,
     status transitions). Show the relevant rows with a "change" column or highlight in bold.
   - Use **Mermaid sequence diagrams** when the case involves a process flow, error path,
     rollback, concurrency, or notification chain.
   - Use **both** when a flow produces a state change that needs to be visible.
   - Omit visual aids only for trivially simple cases where prose alone is unambiguous.

3. **Resultado esperado** — State what the system must do, referencing the specific rows or
   steps shown in the visual aid.

**Estado:** ✅ Cubierto / ⚠️ Parcial / ❌ Laguna

For ❌ Laguna and ⚠️ Parcial: add a `> ❌ Laguna:` or `> ⚠️ Parcial:` blockquote explaining
exactly what the spec fails to define, referencing the example.

---

After each case, call `AskUserQuestion` with exactly this structure:

```
AskUserQuestion(
  question: "¿Continuamos con el siguiente caso?",
  options: [
    "Sí, siguiente →",
    "Marcar como gap y continuar",
    "Marcar como cubierto y continuar",
    "Añadir nota a este caso"
  ]
)
```

**Handle responses:**
- **"Sí, siguiente →"** — Present the next case immediately.
- **"Marcar como gap / cubierto"** — Override the status, acknowledge in one line
  (`> ✏️ Actualizado a ❌ Gap`), then present next case.
- **"Añadir nota"** — Ask a free-text follow-up: `"¿Qué nota quieres añadir?"`,
  append it to the case record, then present next case.

Distribute cases across categories proportionally:

- **Normal** (~20%) — Happy path. Validates the spec covers the standard flow.
- **Variations** (~25%) — Different profiles, timing, valid alternative inputs.
- **Boundary conditions** (~20%) — Min/max, empty states, first-time vs. returning, volume.
- **Error & exceptions** (~20%) — Bad input, missing permissions, timeouts, deps down.
- **Adversarial** (~10%) — Double-submit, back button mid-flow, race conditions, stale links.
- **Extreme edge** (~5%, min 1) — Assumption violations: user who is also admin,
  automated actor instead of human, entity with 0 members.

Always at least 1 case per category. Round percentages to whole cases.

### Step 4 — Final summary (after last case)

After the user confirms past the last case, output automatically:

#### Summary table

| # | Use case summary | Category | Severity | Status |
|---|---|---|---|---|
| 1 | ... | ... | Low/Medium/High | ✅/⚠️/❌ |

Reflect any overrides the user made during the session.

#### Top 3 actions

Exactly 3 concrete actions, prioritized, one sentence each, specific to this spec.
Derived from the ❌ Gap and ⚠️ Partial cases with highest severity.

Then call `AskUserQuestion` one last time:

```
AskUserQuestion(
  question: "¿Qué quieres hacer con este resultado?",
  options: [
    "Exportar resumen como markdown",
    "Crear tickets en Jira con los gaps",
    "Nada, ya terminé"
  ]
)
```

**Handle responses:**
- **"Exportar resumen"** — Write a markdown file to `docs/superpowers/specs/<date>-<spec-name>-stress-test-report.md`.
  Structure:
  1. Summary table (all cases with final statuses, reflecting any user overrides).
  2. Full case descriptions in the narrated example format (context + visual aids + expected result + gap note).
  3. Top 3 actions in full detail (not one-liners — one paragraph each explaining what must change,
     why it matters, and what the correct behavior should be).
  Then confirm the file path to the user.
- **"Crear tickets en Jira"** — For each ❌ Gap with severity Medium or High, create
  a Jira issue in the same project as the spec using `mcp__atlassian__createJiraIssue`.
  Title: `[Gap] <use case summary>`. Description: the narrated example + gap explanation.
- **"Nada"** — Acknowledge and close: `> ✅ Sesión finalizada. X gaps identificados.`

## Output format

- Markdown with Mermaid diagrams and tables where applicable.
- Cases presented as narrated examples with real data — never abstract placeholders.
- Language: match the spec's language (Spanish if the spec is in Spanish).
- Tone: direct, no praise — finding holes before dev picks it up.
- If the spec is tight and well-covered, say so in the diagnostic.
