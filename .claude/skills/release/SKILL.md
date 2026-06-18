---
name: release
description: Use when the user wants to release, tag, publish, or deploy a new version to dev. Triggers on "release", "tag", "nueva versión", "bump version", "subir versión", "publicar versión", "deploy dev", "sacar release", or any mention of creating a v* tag. Use this skill whenever the user wants to cut a new version of any Afianza service, even if they don't say "release" explicitly.
allowed-tools: Bash AskUserQuestion
---

# Afianza — Release to Dev

Creates a new version tag in the current service, pushes it, and triggers the CI/CD pipeline that builds and deploys to dev.

## Step 1 — Verify context

```bash
# Must be in a service repo with a package.json
git rev-parse --show-toplevel
cat package.json | grep '"name"\|"version"'
git branch --show-current
```

If not on `main`, warn the user:
> "Estás en la rama `<branch>`. Los releases normalmente se hacen desde `main`. ¿Quieres continuar de todas formas?"

Check the working tree is clean:
```bash
git status --porcelain
```

If there are uncommitted changes, stop and tell the user to commit or stash them first.

## Step 2 — Resolve current version

```bash
# Latest git tag
git tag --sort=-version:refname | grep '^v' | head -1

# Version in package.json
node -p "require('./package.json').version"
```

Compare them. If they differ (e.g., tag is `v0.11.3` but package.json says `0.10.0`):
1. Sync package.json to the latest tag **without creating a new commit yet**:
   ```bash
   npm version <latest-tag-version> --no-git-tag-version
   git add package.json package-lock.json
   git commit -m "chore: sync version to $(git tag --sort=-version:refname | grep '^v' | head -1)"
   git push
   ```
2. Inform the user: "He sincronizado package.json con el último tag (`<tag>`) antes de hacer el bump."

## Step 3 — Choose bump type

Ask the user:
> "¿Qué tipo de bump quieres hacer?
> - **patch** — corrección (0.11.3 → 0.11.4)
> - **minor** — nueva funcionalidad (0.11.3 → 0.12.0)
> - **major** — cambio breaking (0.11.3 → 1.0.0)"

Show the current version and what the resulting tag will be for each option.

## Step 4 — Create the release

```bash
npm version <patch|minor|major> -m "chore(release): %s"
git push --follow-tags
```

`npm version` updates `package.json`, creates a commit, and creates the git tag. `--follow-tags` pushes both the commit and the tag.

## Step 5 — Show CI/CD link

```bash
# Get the repo remote URL to build the Actions link
git remote get-url origin
```

Extract the `owner/repo` from the remote URL and show:
```
Tag <v0.11.4> pushed. CI/CD en marcha:
https://github.com/<owner>/<repo>/actions
```

Tell the user: "El pipeline de GitHub Actions se ha disparado. Cuando la imagen esté lista, se desplegará automáticamente en dev. Usa `/deploy-prod` cuando quieras subir esta versión a producción."
