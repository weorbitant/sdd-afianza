---
description: "Adversarial review of the active feature. Two modes: 'functional' (business-logic gaps, PO questions) and 'technical' (feasibility + delivery sequence). Read-only by default."
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
---

# Speckit Challenge

Run adversarial review to surface **what's missing**. Two complementary phases match the natural order of refinement:

- **Functional phase** — runs after `/speckit-clarify`, before `/speckit-plan`. Surfaces missing use cases, real-world scenarios, and PO questions. Decisions land in `spec.md` Open Questions and reach the PO via `/speckit-atlassian-sync-push`. The plan is built on resolved questions, not assumptions.
- **Technical phase** — runs after `/speckit-plan`, before `/speckit-tasks`. Surfaces data-model gaps, missing constraints, implicit decisions worth promoting to ADRs, and cross-service delivery-sequence risks.

Complements `/speckit-analyze`:
- `/speckit-analyze` finds **inconsistency** (what is mis-aligned across artifacts).
- `/speckit-challenge` finds **gaps** (what is missing).

**Read-only by default.** Step 7 (promoting QUESTION-PO to `spec.md` Open Questions) is the only opt-in mutation and requires explicit user consent.

## Usage

```
/speckit-challenge                  # auto: functional if no plan.md yet, all otherwise
/speckit-challenge functional       # only business-logic-reviewer, focus on PO questions
/speckit-challenge technical        # feasibility-reviewer + business-logic restricted to bucket 9 (delivery sequence)
/speckit-challenge all              # both phases combined
```

### Mode resolution

Parse the first positional argument from `$ARGUMENTS`:

- `functional` → MODE = functional
- `technical`  → MODE = technical
- `all`        → MODE = all
- empty or anything else → auto-detect:
  - if `plan.md` does NOT exist in FEATURE_DIR → MODE = functional
  - if `plan.md` exists → MODE = all

Announce the resolved mode to the user before dispatching reviewers.

## Execution Steps

### 1. Resolve feature paths and project context

Run `{SCRIPT}` from repo root. Parse JSON for `FEATURE_DIR` and `AVAILABLE_DOCS`. Derive:

- `SPEC = FEATURE_DIR/spec.md`
- `PLAN = FEATURE_DIR/plan.md`
- `DATA_MODEL = FEATURE_DIR/data-model.md`
- `CONTRACTS_DIR = FEATURE_DIR/contracts/` (if listed in AVAILABLE_DOCS)
- `RESEARCH = FEATURE_DIR/research.md` (if present — passed to agents for context, not reviewed)
- `DECISIONS = FEATURE_DIR/decisions.md` (if present — passed to agents for context)
- `PROJECT_CLAUDE = <repo root>/CLAUDE.md` (always passed to agents as project context)
- `PROJECT_CONTEXT = <repo root>/.specify/project-context.md` (optional; if present, appended to PROJECT_CLAUDE in the `<project-context>` block)

**Abort with a clear message** if `spec.md` is missing. For MODE = `technical` or `all`, also abort if `plan.md` is missing. For MODE = `functional`, `plan.md` and `data-model.md` are not required. `data-model.md` is recommended for technical phases but not strictly required (warn and proceed if absent). If `CLAUDE.md` is missing at repo root, warn and continue without project context.

### 2. Build the reviewer team

Active reviewers (v0.5.0 — PO-first V2 schema):

- `feasibility-reviewer` — `.specify/extensions/challenge/agents/feasibility-reviewer.md` (technical phase)
- `business-logic-reviewer` — `.specify/extensions/challenge/agents/business-logic-reviewer.md` (functional phase, plus bucket 9 in technical phase)

Select reviewers based on resolved MODE:

| MODE | Reviewers dispatched | business-logic focus instruction |
|------|---------------------|----------------------------------|
| `functional` | `business-logic-reviewer` only | "Focus on buckets 1–8. SKIP bucket 9 (delivery sequence) — there is no plan to review yet." |
| `technical`  | `feasibility-reviewer` + `business-logic-reviewer` | "Focus EXCLUSIVELY on bucket 9 (delivery sequence and dependencies). Skip buckets 1–8 — they were covered in the functional phase." |
| `all`        | `feasibility-reviewer` + `business-logic-reviewer` | No restriction — all 9 buckets active. |

Announce to the user using this exact shape (substituting the actual MODE and reviewer list):

```
Running /speckit-challenge (mode: <MODE>) on <FEATURE_DIR>:
- <reviewer name>  →  <one-line focus>
- <reviewer name>  →  <one-line focus>
```

### 3. Dispatch reviewers in parallel

For each reviewer in the team, dispatch a sub-agent via the `Agent` tool with `subagent_type: "general-purpose"`. **All reviewers run in parallel** — issue all `Agent` calls in a single assistant message.

Each agent receives a prompt built from this template:

```
You are operating as the reviewer defined below. Follow its instructions exactly. Output only the JSON array described in its "Output format" section, with no surrounding prose or markdown fences.

<mode-focus>
{the "business-logic focus instruction" string from the table in step 2, or empty for feasibility-reviewer (it does not have buckets)}
</mode-focus>

<reviewer-definition>
{contents of .specify/extensions/challenge/agents/<reviewer>.md}
</reviewer-definition>

<project-context>
{full content of PROJECT_CLAUDE — root CLAUDE.md — if present}

{if PROJECT_CONTEXT exists, append a "---" separator and its full content}
</project-context>

<artifacts>
<spec path="{SPEC}">
{full content of spec.md}
</spec>

<plan path="{PLAN}">
{full content of plan.md, or the string "NOT PRESENT (functional phase — plan not yet written)" when MODE=functional and plan.md is absent}
</plan>

<data-model path="{DATA_MODEL}">
{full content of data-model.md, or "NOT PRESENT"}
</data-model>

<contracts>
{for each file in CONTRACTS_DIR: <file path="..."> ... </file>, or "NONE"}
</contracts>

<context-only-research path="{RESEARCH}">
{full content of research.md if present, else "NOT PRESENT"}
</context-only-research>

<context-only-decisions path="{DECISIONS}">
{full content of decisions.md if present, else "NOT PRESENT"}
</context-only-decisions>
</artifacts>

Return the JSON array of findings now.
```

**Pass the full artifacts**, not summaries. The reviewer must see exact text to cite literal evidence.

### 4. Collect, validate, and renumber findings

For each reviewer that returned:

1. Parse the JSON array. If parsing fails, record the reviewer as failed and continue.
2. For each finding, **discard it** if any of these is true:
   - Missing `evidence`, `location`, `category`, `gap`, or `affectedStories`.
   - `affectedStories` is not a non-empty array of strings, or contains values that are neither `US<N>` matching a user story header in `spec.md` nor one of the literal tokens `outside-scope` / `cross-cutting`. If the reviewer returned an unknown `US<N>` not present in the spec, downgrade to `outside-scope` rather than discarding (record a warning in the report's "Failed reviewers" section).
   - `severity` not in `BLOCKER | ADR | QUESTION-PO | BUSINESS-GAP | NIT`.
   - **V2 PO-fields validation (QUESTION-PO from `business-logic-reviewer` only)** — discard if any of these is missing or empty:
     - `shortTitle` (non-empty, ≤ 80 chars after trimming).
     - `scenarioPlain` (non-empty, ≥ 1 sentence — at least one `.`, `?` or `!` after trimming).
     - `businessImpact` (non-empty).
     - `options` — must be an array of ≥ 2 objects, each with non-empty `letter`, `action`, `tradeoff`. Letters must be unique and drawn from `A`, `B`, `C`, `D`.
     - `recommendedOption` — must match one of the letters present in `options`.
     - `recommendationReason` (non-empty).
   - `severity` is `BUSINESS-GAP` or `NIT` and the finding has no `suggestion`.
   - `evidence` is empty, generic, or — when it does NOT start with the literal token `ABSENCE` — cannot be found as a substring in any artifact. `ABSENCE — ...` evidence is allowed only for missing-scenario findings from `business-logic-reviewer` and must be followed by an explicit description of what is absent.
3. **Feasibility audit (V2)** — for each surviving QUESTION-PO finding from `business-logic-reviewer`:
   - Inspect each `options[].tradeoff`. If it starts with `Requiere construir`, `Requiere integrar`, or `Requiere desplegar`, mark the option as `feasibility: new-infra-needed` internally — this surfaces in the report as a 🏗 icon next to that option in the table.
   - If the `recommendedOption` is one of those marked `new-infra-needed`, append a one-line warning to the finding rendered in the report: `> ⚠️ La opción recomendada exige construir infraestructura nueva — confirma con el equipo que el coste es aceptable antes de elegirla.`
   - If `options[]` contains fewer than 2 entries after the reviewer dropped infeasible ones, this is acceptable (the reviewer was honest); do not discard the finding.
   - The orchestrator does **not** itself second-guess feasibility — it trusts the reviewer's tradeoff text. Its job is only to make the cost visible.
4. **Renumber surviving findings using PO-facing IDs** (V2):
   - QUESTION-PO from `business-logic-reviewer` → `D1, D2, …` (Decisions, in the original order returned by the reviewer).
   - BUSINESS-GAP / NIT from `business-logic-reviewer` → `G1, G2, …` (Gaps).
   - All findings from `feasibility-reviewer` (any severity) → `T1, T2, …` (Technical findings).
   Record the original reviewer ID (e.g. `business-B3`) alongside the new ID — both go in the anexo for traceability.
5. If a reviewer produces zero valid findings, record that explicitly in the report.

### 5. Write challenge-report.md (V2 layout — PO-first)

Write to `{FEATURE_DIR}/challenge-report.md`. The layout puts the PO-facing content at the top and pushes evidence / IDs from the reviewer / failed-reviewer logs to an *Anexo técnico* at the bottom.

Let `K` = number of QUESTION-PO findings, `L` = BUSINESS-GAP, `M` = NIT, `T_total` = technical findings (anything from `feasibility-reviewer`, plus any non-QUESTION-PO from `business-logic-reviewer` that does not classify as BUSINESS-GAP/NIT — e.g. BLOCKER/ADR).

```markdown
# Decisiones pendientes — {feature name}

**Para**: PO  ·  **Generado**: {ISO date}  ·  **Modo**: {MODE}

## En una frase

{Pick the matching template based on counts:}

- K > 0:  "Tenemos **{K} decisiones de negocio** que necesitamos resolver contigo antes de construir{si L>0: `, más {L} aclaraciones que el equipo cerrará por su cuenta`}{si T_total>0: `, más {T_total} temas técnicos para el equipo`}."
- K = 0, L > 0:  "No hay decisiones pendientes para el PO — solo {L} aclaraciones que cerrará el equipo{si T_total>0: ` y {T_total} temas técnicos`}."
- K = 0, L = 0:  "Sin hallazgos pendientes en esta revisión.{si T_total>0: ` Hay {T_total} notas técnicas para el equipo.`}"

## Riesgo por historia

Construye la tabla con TODAS las historias del spec (`US1..USN`) y las pseudo-filas `outside-scope` y `cross-cutting` si tienen findings. Para cada historia, calcula:

- **Decisiones pendientes**: lista de IDs `D*` cuyo `affectedStories` incluye esta historia.
- **Aclaraciones**: lista de IDs `G*` cuyo `affectedStories` incluye esta historia.
- **¿Se puede empezar?**: derivar así:
  - Si existe al menos un `D*` con `blocksStory: true` que afecte a esta historia → `**No — bloqueada hasta resolver {D-ids}**`.
  - Si existen `D*` (ninguno bloqueante) → `Sí, con matices`.
  - Si solo hay aclaraciones / nada → `Sí`.

| Historia | Decisiones | Aclaraciones | ¿Se puede empezar? |
|----------|-----------|--------------|---------------------|
| US1 — {title} | D2, D7 | G1 | Sí, con matices |
| US4 — {title} | D1, D3, D4, D6 | — | **No — bloqueada hasta resolver D1, D3, D4** |
| outside-scope | D8 | — | Decisión de scope |

Omite filas vacías.

## Qué necesitamos de ti

- **{K} decisiones** marcadas como `D1..D{K}` abajo. Cada una incluye escenario, opciones, trade-offs y nuestra recomendación.
- Cada decisión se publicará como un comentario individual en la Epic de Jira al ejecutar `/speckit-atlassian-sync-push`. Puedes responder ahí mismo con la letra elegida.
{si L > 0:}
- **{L} aclaraciones** (`G1..G{L}`) que cerraremos sin tu intervención salvo que veas algo raro — sección *Aclaraciones* más abajo.

---

## Decisiones

(Render uno por cada QUESTION-PO en orden `D1..D{K}`. **No incluir** `evidence`, `gap` técnico, ni IDs internos del reviewer en esta sección — todo eso vive en el Anexo.)

### D{n} — {shortTitle}

**Afecta a**: {comma-separated `affectedStories` translated to story names, e.g. `US4 (Cierre de equipo) — principal, US1 (Crear y gestionar equipo)`}
{si blocksStory == true:}
**¿Bloquea empezar?**: Sí — {primary US in affectedStories}
{si relatedOpenQuestions no vacío:}
**Relacionada con**: {comma-separated, e.g. `OQ-001`}

#### Escenario
{scenarioPlain}

#### Por qué te preguntamos
{businessImpact}

#### Recomendación del equipo: {recommendedOption}
{recommendationReason}

#### Opciones

| Opción | Qué hace | Trade-off |
|--------|----------|-----------|
| {letter}{si letter == recommendedOption: ` ⭐`}{si option marcada `new-infra-needed`: ` 🏗`} | {action} | {tradeoff} |
| ... | ... | ... |

{si recommendedOption está marcada `new-infra-needed`:}
> ⚠️ La opción recomendada exige construir infraestructura nueva — confirma con el equipo que el coste es aceptable antes de elegirla.

{si alguna opción está marcada `new-infra-needed`:}
> Leyenda: ⭐ recomendada por el equipo · 🏗 requiere construir infraestructura que no existe hoy.

---

(repeat for every D)

{si L > 0:}
## Aclaraciones que cerrará el equipo

Estas son ambigüedades que la spec olvidó formalizar pero que tienen respuesta clara. El equipo las añadirá al spec sin necesitar tu input. **Solo léelas si quieres saber qué decidiremos** — si discrepas con alguna, díselo al tech lead y la elevamos a decisión tuya.

### G{n} — {shortTitle or category-derived label}

**Afecta a**: {affectedStories translated to story names}

{suggestion}

---

(repeat for every G)

---

## Anexo técnico — para el equipo

Esta sección no es para el PO. Reúne evidencia literal, IDs internos de los reviewers, hallazgos técnicos puros (sin impacto directo en preguntas al PO) y log de reviewers fallidos.

### Resumen por severidad

| Severidad     | Cuántos |
|---------------|---------|
| BLOCKER       | N       |
| ADR           | N       |
| QUESTION-PO   | K       |
| BUSINESS-GAP  | L       |
| NIT           | M       |

### Hallazgos técnicos

(Render aquí todo lo que viene de `feasibility-reviewer` y cualquier BLOCKER/ADR de `business-logic-reviewer` que no encaje en Decisiones / Aclaraciones. Mantén el formato denso clásico.)

#### T{n} — {severity} — {category}

**Afecta a**: {affectedStories}
**Location**: `{location}`
**Reviewer ID**: {original reviewer id, e.g. `feasibility-F1`}

**Evidence**:
> "{literal quote}"

**Gap**: {gap text}

**Suggestion**: {suggestion text}

---

### Trazabilidad de IDs

Mapeo `Dx`/`Gx`/`Tx` → ID original devuelto por el reviewer. Útil para regenerar el report o auditar cambios entre runs.

| ID PO | Reviewer ID | Severity | Location |
|-------|-------------|----------|----------|
| D1    | business-B1 | QUESTION-PO | spec.md (ABSENCE) |
| D2    | business-B4 | QUESTION-PO | spec.md#FR-010 |
| G1    | business-B5 | BUSINESS-GAP | spec.md#FR-003 |
| T1    | feasibility-F1 | BLOCKER | data-model.md#client-team |
| ...   | ...         | ...      | ... |

### Evidencia literal de las Decisiones

Para cada `Dx`, la cita exacta del spec (o el marcador `ABSENCE`) que motivó el hallazgo. Útil cuando el PO pide ver "dónde lo pone".

- **D1** — `spec.md (ABSENCE)` → "ABSENCE — no FR or AC in spec.md addresses what happens when an employee resigns mid-team"
- **D2** — `spec.md#FR-006` → "FR-006: Responsable NO PUEDE pertenecer a más de un departamento. (Restricción organizativa preexistente.)"
- ...

### Reviewers fallidos

(Lista los reviewers que no devolvieron JSON válido con el error concreto. Si ninguno falló: "ninguno".)

### Próximos pasos (para el equipo)

- **BLOCKER (T*)**: resolver antes de `/speckit-tasks`. Editar `spec.md` / `plan.md` / `data-model.md` según corresponda y re-ejecutar `/speckit-challenge`.
- **ADR (T*)**: promover a `decisions.md` con `/speckit-decisions-extract`.
- **Decisiones (D*)**: el orchestrator ofrecerá publicarlas como Open Questions en `spec.md` en el paso 7. Después, `/speckit-atlassian-sync-push` las sube como comments individuales a la Epic.
- **Aclaraciones (G*)**: editar `spec.md` para añadir el FR/AC usando `suggestion` como punto de partida. No requieren input del PO.
- **NIT**: opportunistic.
```

### 6. Summarize to the user

Print a concise summary in the chat (do NOT dump the full report):

```
Challenge complete — {FEATURE_DIR}/challenge-report.md

  N BLOCKER · M ADR candidate · K QUESTION-PO · L BUSINESS-GAP · J nit

  Top BLOCKERs (if any):
    - feasibility-F1: <one-line gap summary>
    - feasibility-F2: <one-line gap summary>

  Top QUESTION-PO (if any):
    - business-B4: <one-line question summary>
    - business-B1: <one-line question summary>
    - business-B6: <one-line question summary>

If BLOCKERs exist: do NOT proceed to /speckit-tasks. Resolve first.
```

If zero findings: say so plainly and recommend the user proceed to `/speckit-tasks`.

### 7. Offer to promote QUESTION-PO findings to spec.md Open Questions

**Only if at least one valid QUESTION-PO finding exists.** Skip this step otherwise.

Ask the user (single prompt — use `AskUserQuestion` if available, otherwise a numbered list with explicit input expected):

```
Hay K QUESTION-PO en el report. ¿Qué hago con ellas?

  (a) Añadir TODAS al spec.md como Open Questions (append, no modifica nada existente)
  (b) Dejarme elegir una a una (cherry-pick)
  (c) No tocar spec.md — se quedan solo en challenge-report.md
```

#### If user picks (a) — bulk append

1. Open `spec.md` and locate the section heading `## Open Questions` (case-sensitive, exact).
2. If the section does not exist, append it to the end of the file with the heading and an empty body.
3. For each QUESTION-PO finding, append a **V2 block** in this format **at the end of the Open Questions section** (never replace existing content). The block is self-contained so `/speckit-atlassian-sync-push` can publish it verbatim as a Jira comment:

   ```markdown
   ### {finding.id} — {finding.shortTitle}

   **Origen**: `challenge-report.md` ({ISO date})  ·  **Afecta a**: {affectedStories translated to story names, primary first}{si finding.blocksStory == true: `  ·  **Bloquea empezar**: {primary US}`}{si finding.relatedOpenQuestions no vacío: `  ·  **Relacionada con**: {comma-separated IDs}`}

   **Escenario**: {finding.scenarioPlain}

   **Por qué te preguntamos**: {finding.businessImpact}

   **Recomendación del equipo**: {finding.recommendedOption} — {finding.recommendationReason}

   | Opción | Qué hace | Trade-off |
   |--------|----------|-----------|
   | {letter}{si letter == recommendedOption: ` ⭐`}{si option marcada `new-infra-needed`: ` 🏗`} | {action} | {tradeoff} |
   | ... | ... | ... |

   {si recommendedOption está marcada `new-infra-needed`:}
   > ⚠️ La opción recomendada exige construir infraestructura nueva — el equipo necesita confirmar el coste antes de comprometerla.

   _Estado_: pending
   ```

4. After appending, print: `Añadidas K Open Questions al spec.md. Ejecuta /speckit-atlassian-sync-push para publicarlas al PO en el Epic.`

#### If user picks (b) — cherry-pick

For each QUESTION-PO in turn, show:

```
[N/K] business-BX — <category>

  <one-line gap>

  ¿Añadir al spec.md? (s/n/parar)
```

`s` appends in the same format as (a); `n` skips; `parar` aborts the cherry-pick loop. At the end, print how many were appended.

#### If user picks (c) — no spec.md changes

Print: `OK. Las QUESTION-PO se quedan solo en challenge-report.md. Puedes consultarlas allí cuando quieras.`

#### Safety rules

- **Never modify or remove existing content in `spec.md`.** Only append inside the `## Open Questions` section.
- **Never duplicate a question.** Before appending, check if a heading `### {finding.id}` already exists in the Open Questions section. If it does, skip with a note in the console output.
- **Skip if the finding's `evidence` starts with `ABSENCE`** is still allowed — the gap is real, the question text is what matters to the PO. The `ABSENCE` marker stays in `challenge-report.md` and does not leak into `spec.md`.

## Operating Constraints

- **Default to read-only** — reviewer dispatch and report writing never modify `spec.md`, `plan.md`, `data-model.md`, `contracts/`, `decisions.md`, or any other artifact. The only file the read-only phase writes is `challenge-report.md`.
- **Step 7 is the only opt-in mutation** — promoting QUESTION-PO findings to `spec.md` Open Questions happens **only after explicit user consent** in step 7, and only as an append inside the `## Open Questions` section. Never edit existing content, never touch any other section.
- **Never mock** reviewer output — if all reviewers fail, report it honestly. Do not synthesize findings yourself.
- **Determinism is not required** — adversarial review is inherently noisy. Reviewers may legitimately produce different findings between runs. Treat the report as a checklist, not as the final word.

## Context

{ARGS}
