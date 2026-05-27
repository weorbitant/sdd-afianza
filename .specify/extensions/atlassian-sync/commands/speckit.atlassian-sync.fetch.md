---
description: "Fetch a Jira Epic and format its content as spec input for /speckit-specify."
---

# Atlassian Sync — Fetch Epic from Jira

Reads a Jira Epic via MCP and produces a structured description ready to be consumed by `speckit.specify`.

## Usage

```
/speckit-atlassian-sync-fetch <epic-key>
```

- `epic-key` (required): Jira key of the Epic to fetch (e.g. `DEVPT-518`).

## Execution Steps

### 1. Check prerequisites

Verify the Atlassian MCP connection is active. If not, abort with:
> "Atlassian MCP is not connected. Run `/mcp` and reconnect before retrying."

Load configuration from `.specify/extensions/atlassian-sync/config/atlassian.yml`
(`cloudId`, `projectKey`).

### 2. Fetch the Epic

Call `mcp__atlassian__getJiraIssue` with `{ issueIdOrKey: "<epic-key>" }`.

Confirm the returned issue type is Epic. If not, abort:
> "Issue <epic-key> is not an Epic (type: <actual-type>). Provide a valid Epic key."

Extract the following fields:
- `summary` → feature name
- `description` → problem statement, context, goals
- `acceptanceCriteria` (custom field or inline in description)
- `labels`, `priority`, `assignee`, `reporter`
- Any linked child issues (Stories already created, if any)
- Any attachments listed (images, PDFs, design links)

### 3. Fetch child issues (if any)

If the Epic already has linked Stories, fetch their summaries via
`mcp__atlassian__searchJiraIssuesUsingJql`:
```
project = <projectKey> AND "Epic Link" = <epic-key> AND issuetype = Story
```
Include their titles in the output so `specify` is aware of what's already defined.

### 4. Format spec input

Produce a structured Markdown block as `spec_input` output:

```markdown
# Epic: <summary>

**Jira**: <epic-key> | **Priority**: <priority>

## Context & Problem

<description>

## Acceptance Criteria (from Jira)

<acceptance criteria, if present>

## Existing Stories (if any)

<list of already-created stories>

## Attachments & Links

<list of attachments or design links>
```

### 5. Output

Return:
- `spec_input`: the formatted Markdown block above
- `epic_key`: the validated Epic key
- `epic_summary`: the Epic summary (feature name)

Report to the user:
> "✅ Epic fetched: <epic-key> — <summary>"
> "Ready to pass to /speckit-specify."

## Error Handling

- MCP not connected → abort with reconnect instructions.
- Epic key not found or not an Epic → abort with clear message.
- Description empty → warn and continue with a placeholder; `specify` will ask for more context.
