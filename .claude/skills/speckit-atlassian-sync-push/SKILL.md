---
name: speckit-atlassian-sync-push
description: Push User Stories + tasks from spec.md / tasks.md to Jira as Stories and Sub-tasks under an existing Epic
argument-hint: "[epic-key]  e.g. /speckit-atlassian-sync-push DEVPT-518"
compatibility: Requires spec-kit project structure with .specify/ directory and Atlassian MCP connected
metadata:
  author: afianza-local
  source: atlassian-sync:commands/speckit.atlassian-sync.push.md
user-invocable: true
---

# Atlassian Sync — Push to Jira

## User Input

```text
{{ARGS}}
```

You **MUST** consider the user input before proceeding (if not empty). If a Jira key is provided (e.g. `DEVPT-518`), treat it as the Epic key and skip asking for it.

---

## Execution Steps

### 1. Setup

Run `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` from repo root. Parse JSON for:
- `FEATURE_DIR` (absolute path to the active feature directory)
- `FEATURE_SPEC` (absolute path to spec.md)
- `TASKS` (absolute path to tasks.md)

If JSON parsing fails, abort and ask the user to run `/speckit-specify` first.

### 2. Load configuration

Read `.specify/extensions/atlassian-sync/config/atlassian.yml` for defaults:
- `cloudId`
- `projectKey`
- `issueTypes.story` / `issueTypes.subtask`
- `epicLinkField`

Check if a per-feature override file exists at `{FEATURE_DIR}/atlassian.yml`. If it does, merge it on top (feature values win).

### 3. Determine Epic key

- If an Epic key was passed as argument (e.g. `DEVPT-518`), use it directly.
- Otherwise ask: "¿Cuál es la clave de la Epic en Jira bajo la que deben crearse las historias? (e.g. DEVPT-518)"

### 4. Parse spec.md — extract User Stories

Read `FEATURE_SPEC`. Parse every `### User Story N` section. For each story extract:

- **title**: the heading text after `—` (e.g. `Crear y gestionar el equipo de un cliente`)
- **priority**: the `(Priority: P?)` annotation
- **narrative**: the paragraph immediately after the heading (until the first `**Why` or `**¿Por qué`)
- **why**: the `**Why this priority**` / `**¿Por qué P?**` paragraph
- **independent_test**: the `**Independent Test**` / `**Test independiente**` paragraph
- **scenarios**: all `**Given** … **When** … **Then** …` blocks

Build the full Jira description from these parts using this template:

```
{narrative}

**¿Por qué {priority}?**
{why}

**Test independiente**
{independent_test}

---

**Escenarios de aceptación**

1. **Given** ...
   **When** ...
   **Then** ...
[repeat for each scenario]
```

Also extract **PO questions**: look for lines or sections containing `NEEDS CLARIFICATION`, `TODO`, open questions (lines ending with `?` that are not inside acceptance scenarios). Collect them per story.

### 5. Parse tasks.md — map tasks to stories

Read `TASKS`. For each task line matching the checklist format:

```
- [ ] T### [P] [US?] Description with file path
```

Extract:
- **id**: `T###`
- **parallelizable**: presence of `[P]`
- **story**: `[US?]` tag (e.g. `[US1]`, `[US2]`) — maps to story index
- **description**: the rest of the line

Group tasks by story (`[US1]` → Story 1, `[US2]` → Story 2, etc.).
Tasks without a `[US?]` tag (setup, foundational, polish) go into a special `_unassigned` bucket — do NOT create them as sub-tasks under a story; ask the user which story (or skip).

### 6. Confirm before creating

Show a dry-run summary:

```
📋 Ready to push to Jira

Epic: {epicKey}
Project: {projectKey}
Cloud: {cloudId}

Stories to create: N
  • US1 · {title} — {task_count} sub-tasks
  • US2 · {title} — {task_count} sub-tasks
  ...

Unassigned tasks (no [US?] label): M
  → Skipping unless you specify a story

Proceed? (yes / no)
```

Wait for confirmation before making any API calls.

### 7. Create Stories — one per User Story

For each User Story, call `mcp__atlassian__createJiraIssue` with:
- `cloudId`: from config
- `projectKey`: from config
- `issueTypeName`: `Story`
- `summary`: `US{N} · {title}`
- `description`: full description built in Step 4
- `contentFormat`: `markdown`
- `additional_fields`: `{ "{epicLinkField}": "{epicKey}" }`

Create all stories **in parallel** (single message, multiple tool calls).

Store the mapping: `US1 → DEVPT-XXX`, `US2 → DEVPT-YYY`, etc.

### 8. Create Sub-tasks — one per task per story

For each story, create its sub-tasks under the Story key obtained in Step 7.
Call `mcp__atlassian__createJiraIssue` with:
- `cloudId`: from config
- `projectKey`: from config
- `issueTypeName`: `Sub-task`
- `parent`: the Story key for this story
- `summary`: `{id} · {description}` (include `[P]` marker if parallelizable)
- `description`: file path and brief context extracted from the task line
- `contentFormat`: `markdown`

Batch sub-task creation in parallel groups of up to 6 calls per message to avoid rate limits.

### 9. Report

Output a table of all created issues:

| Story / Sub-task | Jira Key | Link |
|---|---|---|
| US1 · {title} | DEVPT-XXX | https://... |
| └ T001 · ... | DEVPT-YYY | https://... |
| └ T002 · ... | DEVPT-YYZ | https://... |
| US2 · {title} | DEVPT-XXZ | https://... |
| ... | | |

**Total**: N Stories + M Sub-tasks created.

### 10. Optional — Add PO questions as comments

If PO questions were found in Step 4, ask:

"Se encontraron preguntas pendientes para la PO en {N} historias. ¿Quieres añadirlas como comentarios en Jira? (yes / no)"

If yes:
- For each story with questions, call `mcp__atlassian__addCommentToJiraIssue`
- Comment body: list the questions clearly addressed to the PO
- Do NOT add a signature — the comment author is whoever is logged in via MCP

---

## Behavior rules

- Never create duplicate issues: if a story or task already exists (identifiable by `US{N} ·` prefix in summary), skip it and warn.
- If `mcp__atlassian__createJiraIssue` returns an error for a single item, log the error and continue with the rest.
- If the Atlassian MCP is not loaded (tools not available), abort immediately: "Atlassian MCP no está conectado. Conéctalo con `/mcp` y vuelve a ejecutar."
- All Jira text (summaries, descriptions) is written in the same language as the spec (detect from spec.md content).
- Tasks without `[US?]` label are silently skipped unless the user explicitly asks to include them.
