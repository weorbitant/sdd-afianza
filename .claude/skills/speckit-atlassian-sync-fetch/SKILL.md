---
name: speckit-atlassian-sync-fetch
description: Fetch a Jira Epic and format its content as spec input ready for /speckit-specify
argument-hint: "<epic-key>  e.g. /speckit-atlassian-sync-fetch DEVPT-518"
compatibility: Requires Atlassian MCP connected
metadata:
  author: afianza-local
  source: atlassian-sync:commands/speckit.atlassian-sync.fetch.md
user-invocable: true
---

# Atlassian Sync — Fetch Epic from Jira

## User Input

```text
{{ARGS}}
```

If an Epic key is provided (e.g. `DEVPT-518`), use it directly. Otherwise ask:
"¿Cuál es la clave de la Epic en Jira? (e.g. DEVPT-518)"

---

## Execution Steps

### 1. Check MCP connection

If `mcp__atlassian__getJiraIssue` is not available, abort:
> "Atlassian MCP no está conectado. Conéctalo con `/mcp` y vuelve a ejecutar."

Load `.specify/extensions/atlassian-sync/config/atlassian.yml` for `cloudId` and `projectKey`.

### 2. Fetch the Epic

Call `mcp__atlassian__getJiraIssue` with `{ "issueIdOrKey": "<epic-key>" }`.

Verify the issue type is Epic. If not, abort:
> "El issue <epic-key> no es una Epic (tipo: <actual-type>). Proporciona una clave de Epic válida."

Extract:
- `summary` → nombre de la feature
- `description` → contexto, problema, objetivos
- `priority.name`
- `assignee.displayName` (si existe)
- Any acceptance criteria (buscar en description o custom fields)
- Attachment names/URLs (si existen)

### 3. Fetch Stories ya vinculadas (si hay)

Call `mcp__atlassian__searchJiraIssuesUsingJql` with:
```
project = <projectKey> AND "Epic Link" = <epic-key> AND issuetype = Story ORDER BY created ASC
```

Collect their summaries for context.

### 4. Formatear spec_input

Produce el siguiente bloque Markdown:

```markdown
# <summary>

**Epic**: <epic-key> | **Prioridad**: <priority>

## Contexto y Problema

<description>

## Criterios de Aceptación (desde Jira)

<acceptance criteria si existen, si no: "No definidos en Jira — extraer durante specify">

## Stories existentes (si hay)

<lista de stories ya creadas, o "Ninguna">

## Adjuntos y enlaces

<lista de attachments/links, o "Ninguno">
```

### 5. Output

Muestra al usuario:
> "✅ Epic cargada: <epic-key> — <summary>"
> "Contenido listo para /speckit-specify."

Devuelve el bloque formateado como contexto para el siguiente paso.

## Behavior rules

- Si la descripción de la Epic está vacía, continúa con un placeholder y avisa: "La Epic no tiene descripción en Jira. /speckit-specify pedirá más contexto."
- No modifica ningún fichero — solo lee y formatea.
