# Git & commit conventions

- **Never commit to `main`** — always create a feature branch (`feat/<name>`, `fix/<name>`, etc.).
- **Conventional Commits** enforced by commitlint + Husky: `<type>(<scope>): <description>` (lowercase subject).
- Pre-commit: `npm run lint`. Pre-push: `npm run build && npm test`.
- One commit per logical concern. Squash review fixes into originals before merging.
- **GitHub CLI**: use `gh` for all GitHub operations (PRs, issues, branches).
- PR titles, descriptions, and all written artifacts in **English**.
