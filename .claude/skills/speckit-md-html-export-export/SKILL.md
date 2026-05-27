---
name: speckit-md-html-export-export
description: Convert all Markdown files in the current feature directory to self-contained
  HTML
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: md-html-export:commands/md-html-export.export.md
---

# Markdown to HTML Export

Convert every `.md` file in the current feature directory to a self-contained HTML file
that can be opened directly in a browser, with no external dependencies.

## Execution

Run the Python conversion script:

```bash
python3 .specify/extensions/md-html-export/scripts/bash/md_to_html.py
```

The script reads `.specify/feature.json` to find the feature directory automatically.

## Output

- One `.html` file per `.md` file, placed alongside the source Markdown file.
- Example: `specs/001-client-team-assignments/spec.md` → `specs/001-client-team-assignments/spec.html`
- Report a summary: `Converted N file(s) to HTML in <feature_directory>`

## Error Handling

- If `.specify/feature.json` is missing: warn and skip.
- If `python3` is not available: warn and skip.
- If a file fails to convert: log the error but continue with remaining files.