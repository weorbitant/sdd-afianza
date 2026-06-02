# Refinement Model

How Spec Kit is extended for the Afianza polyrepo. **Minimal by design**.

## Principles

1. **Jira owns governance** (Epic, Stories, status, comments, AC).
2. **Repo owns the technical layer** (plan, tasks, decisions).
3. **Tasks are NEVER pushed to Jira** — they live in `tasks.md`.
4. **Custom layer = exactly one file per feature**: `decisions.md`. Nothing else.

## Source of truth per artifact

| Artifact | Lives in | Source of truth | Edited by |
|----------|----------|-----------------|-----------|
| Epic | Jira | **Jira** | PO |
| User Story (title, description, AC, priority) | Jira + `spec.md` | **Jira** | PO + dev |
| Story status (To Do / In Progress / Done) | Jira | **Jira** | dev |
| Comments with PO | Jira | **Jira** | everyone |
| Bugs | Jira | **Jira** | everyone |
| Open questions for PO | Jira (Epic comment via `jira-push`) | **Jira** | PO + dev |
| Open technical questions (dev-only) | Slack / Jira Story comment | ad-hoc | dev |
| Technical tasks | `tasks.md` | **Repo** | dev |
| Technical plan, data model, contracts | `plan.md`, `data-model.md`, `contracts/` | **Repo** | dev |
| Technical decisions + rejected alternatives | `decisions.md` (one per feature) | **Repo** | dev |
| Risks worth tracking | Promoted to `decisions.md` if they drive a decision; ignored otherwise | — | dev |

**Rule of thumb**: if a PO reads or edits it, Jira. If it answers *how* or *why* technical, repo.

## Folder layout per feature

```
specs/001-feature-name/
├── spec.md                          # Spec Kit
├── plan.md                          # Spec Kit
├── tasks.md                         # Spec Kit (organized by story, NOT pushed to Jira)
├── research.md                      # Spec Kit
├── data-model.md                    # Spec Kit
├── quickstart.md                    # Spec Kit
├── contracts/                       # Spec Kit
├── checklists/                      # Spec Kit (review of spec quality)
├── designs/                         # Figma exports
└── decisions.md                     # Single decision log for the whole feature
```

**One custom file per feature**: `decisions.md`. Nothing else is added on top of Spec Kit.

## Workflow

```
1. PO creates Epic in Jira (e.g. DEVPT-518)
2. /speckit-atlassian-sync-fetch DEVPT-518   → contexto Epic
3. /speckit-figma-export-browser              → exporta diseños a designs/
4. /speckit-specify                           → spec.md (lee diseños como fuente de verdad)
5. /speckit-clarify                           → resuelve dudas
6. /speckit-atlassian-sync-push               → crea Stories + Open Questions en Jira (NO subtasks)
7. /speckit-plan + /speckit-tasks             → plan técnico + tareas (viven en repo)
8. Crear decisions.md la primera vez que haga falta:
   cp .specify/templates/refinement/decisions.template.md specs/<feature>/decisions.md
9. /speckit-implement story by story.
   Cada decisión técnica → decisions.md taggeada con la Jira story key.
```

Per-story refinement notes are NOT a separate file. If a dev has open questions before implementing a story:

- **For the PO** → comment on the Jira Story.
- **For the team** → Slack thread or PR description.
- **Important enough to track long-term** → it's actually a decision, promote it to `decisions.md`.

## Templates

`.specify/templates/refinement/decisions.template.md` — single template.

To instantiate for a feature:

```bash
cp .specify/templates/refinement/decisions.template.md specs/<feature>/decisions.md
```

## Linking convention

Every `### User Story N` block in `spec.md` includes one line under the title:

```markdown
### User Story 1 - Assign client to a team (Priority: P1)

**Jira**: [DEVPT-519](https://...)

[narrative continues]
```

The Jira key replaces `DEVPT-XXX` after `/speckit-atlassian-sync-push` returns the real keys.

## What this model deliberately does NOT do

- **No per-story refinement files.** Dev-internal open questions live in Slack/Jira comments, not in markdown.
- **No `ready-checklist.md`.** Gate is implicit: if blocking questions exist in Jira/Slack, work does not start.
- **No story-level decision-log.** All decisions live in the single feature-level `decisions.md`, tagged with the story key.
- **No "Mirror from Jira" sections.** Functional content stays in Jira; the repo does not mirror Jira fields.
- **No auto-sync between Jira and repo.** Drift is reconciled manually via `fetch-epic` or by editing `spec.md`.
- **No subtasks in Jira.** All technical breakdown lives in `tasks.md`.

## When to revisit this model

Re-introduce per-story markdown (`stories/<KEY>/notes.md`) only when **all** of these hold:

1. Stories are refined weeks/sprints before they are implemented.
2. The dev who refines is not always the dev who implements.
3. Slack/Jira comments are insufficient for the team to keep context across that gap.

If you only meet 1 or 2 of those, stick with Slack + Jira comments.
