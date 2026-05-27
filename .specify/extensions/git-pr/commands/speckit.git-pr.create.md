---
description: "Create a GitHub Pull Request for the active feature branch using spec.md as source"
---

# Git PR Creator

Opens a GitHub Pull Request for the current feature branch.
Title and body are generated from `spec.md`. Jira Epic link is included if available.

## Usage

```
/speckit-git-pr-create [base-branch]
```

- `base-branch` (optional): target branch for the PR (default: `main`).

## What it creates

- **Title**: `feat(<feature-id>): <feature name from spec.md>`
- **Body**: Feature summary + User Stories table + Acceptance Criteria + Jira link + testing notes

## Output

Prints the PR URL on success.

## Error Handling

- If `gh` CLI is not authenticated: abort with `gh auth login` hint.
- If already on `main`/`master`: abort with branch hint.
- If PR already exists for this branch: print the existing PR URL and skip creation.
