---
description: "Generate a single index.html from all Markdown files in the current feature directory"
---

# Markdown to HTML Export

Generate a single `index.html` that consolidates all Markdown artifacts for the active feature
(spec, plan, data-model, research, tasks, contracts, checklists) into one browsable document
with a sticky navigation bar and one card per section.

## Execution

```bash
python3 .specify/extensions/md-html-export/scripts/bash/md_to_html.py
```

The script reads `.specify/feature.json` to locate the feature directory automatically.

## Output

- A single `index.html` in the feature directory root.
- Example: `specs/001-client-team-assignments/index.html`
- Sections appear in this order: Specification → Technical Plan → Data Model → Research → Tasks → subdirectory files (contracts, checklists, …)
- Report a summary: `Generated specs/…/index.html (N section(s))`

## Error Handling

- If `.specify/feature.json` is missing: warn and skip.
- If `python3` is not available: warn and skip.
- If a file fails to convert: log the error but continue with remaining files.
