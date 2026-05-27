---
name: speckit-git-pr-create
description: Create a GitHub Pull Request for the active feature branch using spec.md as source for title and body
argument-hint: "[base-branch]  e.g. /speckit-git-pr-create main"
compatibility: Requires spec-kit project structure, gh CLI authenticated, and an active feature branch
metadata:
  author: afianza-local
  source: git-pr:commands/speckit.git-pr.create.md
user-invocable: true
---

# Git PR Creator

## User Input

```text
{{ARGS}}
```

If a base branch is provided (e.g. `main`, `develop`), use it as the PR target. Default: `main`.

---

## Execution Steps

### 1. Setup

Run `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` from repo root. Parse JSON for:
- `FEATURE_DIR` (absolute path to the active feature directory)
- `FEATURE_SPEC` (absolute path to spec.md)
- `BRANCH` (current git branch)

If `BRANCH` is `main` or `master`, abort: "Estás en la rama principal. Cambia a tu rama de feature antes de crear el PR."

### 2. Check for existing PR

Run:
```bash
gh pr view --json url,state 2>/dev/null
```

If a PR already exists for this branch:
- Print: "Ya existe un PR para esta rama: {url}"
- Ask: "¿Quieres continuar de todos modos y crear uno nuevo? (yes / no)"
- If no: abort.

### 3. Load feature context

Read `FEATURE_SPEC` (spec.md). Extract:

- **feature_id**: branch name prefix (e.g. `001-client-team-assignments` → `001`)
- **feature_name**: the main title from `# Feature Specification: {name}` or the `**Input**:` line
- **summary**: the `**Input**:` value, or first paragraph of the spec if no Input field
- **user_stories**: list of `### User Story N — {title} (Priority: P?)` headings
- **acceptance_scenarios**: all `**Given** … **When** … **Then**` blocks per story (first scenario only per story for brevity)

Check for `.specify/extensions/atlassian-sync/config/atlassian.yml` and `{FEATURE_DIR}/atlassian.yml`.
If found, extract `projectKey`. Also check if any Jira keys appear in the spec/tasks (pattern `[A-Z]+-\d+`).
Collect the Epic key if found (first match with the most references).

### 4. Build PR title

```
feat({feature_id}): {feature_name}
```

Example: `feat(001): Asignaciones múltiples en ficha de cliente`

### 5. Build PR body

Use this template (fill with extracted data):

```markdown
## ¿Qué hace este PR?

{summary}

---

## User Stories

| Historia | Prioridad |
|----------|-----------|
{for each user story: | USN · {title} | PN |}

---

## Criterios de aceptación clave

{for each story, first Given/When/Then scenario as a bullet}
- **{story title}**: dado {given}, cuando {when}, entonces {then}.

---

## Testing

- [ ] `npm run infra:up` en cada servicio afectado
- [ ] `npm test` verde en `pgi-service-pgi-api`
- [ ] `npm test` verde en `pd-service-obligations-api`
- [ ] `npm run build` sin errores en `pgi-app-pgi-web`
- [ ] Smoke tests del `quickstart.md`

---

## Jira

{if epic_key found: Epic: [{epic_key}](https://afianza-ac.atlassian.net/browse/{epic_key})}
{if no epic_key: _No se encontró Epic de Jira vinculada._}

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### 6. Confirm

Show the PR title and a preview of the body. Ask:
"¿Crear el PR con este título y descripción? (yes / edit / no)"

- **yes**: proceed to Step 7.
- **edit**: ask what to change (title / body / base branch), apply the change, show preview again, repeat.
- **no**: abort.

### 7. Create the PR

Run:
```bash
gh pr create \
  --title "{title}" \
  --body "{body}" \
  --base {base_branch} \
  --draft
```

Always create as **draft** first. The user can mark it ready for review manually.

### 8. Report

Print:
```
✅ PR creado (draft): {url}

Cuando la implementación esté lista, márcalo como listo para revisión:
  gh pr ready {url}
```

---

## Behavior rules

- Always create as **draft** — never open a ready-for-review PR automatically.
- If `gh` is not installed or not authenticated, abort with: "Instala gh CLI (`brew install gh`) y autentícate con `gh auth login`."
- The PR body is always in the same language as spec.md.
- Never include secrets, tokens, or file paths from local machine in the PR body.
- If spec.md is missing, create a minimal PR with just the branch name as title.
