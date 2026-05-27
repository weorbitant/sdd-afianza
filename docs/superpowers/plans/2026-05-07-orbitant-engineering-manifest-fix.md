# Fix orbitant-engineering plugin manifest — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the `orbitant-engineering` plugin manifest so `/ground-control` loads cleanly, resolving `weorbitant/orbitant-os#35`.

**Architecture:** Append `.md` to the `commands` entry in `plugin.json`. Bump version to 0.1.1.

**Tech Stack:** Claude Code plugin manifest (JSON), `gh` CLI, git.

---

## Task 1: Sync working tree and create fix branch

- [ ] Stash unrelated `package-lock.json` change
- [ ] Sync `main`, branch off as `fix/plugin-manifest-command-extension`

## Task 2: Apply the manifest fix

- [ ] Edit `plugins/orbitant-engineering/.claude-plugin/plugin.json`:
  - `"version": "0.1.0"` → `"version": "0.1.1"`
  - `"commands": ["./commands/ground-control"]` → `"commands": ["./commands/ground-control.md"]`
- [ ] Validate JSON with `python3 -m json.tool`
- [ ] Confirm `commands/ground-control.md` exists

## Task 3: Verify (already proven earlier in session — skipped)

The same edit was applied to the local cache earlier and confirmed working via `/reload-plugins` + `/doctor` + `/orbitant-engineering:ground-control` execution.

## Task 4: Commit, push, open PR

- [ ] Commit with Conventional Commits message + `Closes #35`
- [ ] Push branch
- [ ] Open PR via `gh pr create` (option B rationale, test plan)
- [ ] Restore stashed `package-lock.json`
