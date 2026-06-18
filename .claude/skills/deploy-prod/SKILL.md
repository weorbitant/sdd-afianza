---
name: deploy-prod
description: Use when the user wants to deploy to production, "subir a prod", "desplegar en producción", "lanzar a prod", "manual deploy", "deploy prod", or promote a specific version/tag to the production environment. Use for any Afianza service. SKIP if the user only wants to release/tag (use the `release` skill instead).
allowed-tools: Bash AskUserQuestion
metadata:
  argument-hint: "[image_tag]"
---

# Afianza — Deploy to Production

Triggers the `manual-deploy-on-prod.yml` GitHub Actions workflow for the current service with a specific image tag.

## Step 1 — Identify the service

```bash
git rev-parse --show-toplevel
cat package.json | grep '"name"'
```

Confirm with the user which repo/service is being deployed.

## Step 2 — Choose the image tag

If `$ARGUMENTS` contains a tag (e.g., `v0.11.4`), use it directly and skip to Step 3.

Otherwise, show the last 5 tags:
```bash
git tag --sort=-version:refname | grep '^v' | head -5
```

Ask:
> "¿Qué versión quieres desplegar en prod? (últimas versiones arriba)"

The `image_tag` input to the workflow is **just the version tag** (e.g., `v0.11.4`), not the full image URL — the workflow constructs the full registry path internally.

## Step 3 — Confirm before deploying

Always confirm before triggering prod:
> "Vas a desplegar `<tag>` en **producción** para `<service-name>`. ¿Confirmas?"

Do not proceed without an explicit yes.

## Step 4 — Trigger the workflow

```bash
gh workflow run manual-deploy-on-prod.yml \
  --field image_tag=<tag>
```

If the command fails because the workflow isn't found, check the exact filename:
```bash
ls .github/workflows/
```

## Step 5 — Show the run link

```bash
# Wait a moment for the run to register, then get its URL
sleep 3
gh run list --workflow=manual-deploy-on-prod.yml --limit=1
```

Show the direct link to the run:
```
Desplegando <tag> en producción. Sigue el progreso:
https://github.com/<owner>/<repo>/actions/workflows/manual-deploy-on-prod.yml
```

Remind the user: "Recibirás una notificación de Slack cuando el deploy termine (éxito o fallo)."
