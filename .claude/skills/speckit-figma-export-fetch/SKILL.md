---
name: speckit-figma-export-fetch
description: Download frames from a Figma file URL into the feature designs/ folder
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: figma-export:commands/speckit.figma-export.fetch.md
---

# Figma Frame Export

Download one or more Figma frames as PNG images and save them into the current feature's `designs/` folder.

## Usage

The user must provide a Figma URL. Accepted formats:
- File URL: `https://www.figma.com/file/FILEID/...`
- Design URL: `https://www.figma.com/design/FILEID/...`
- Frame URL with node: `https://www.figma.com/file/FILEID/...?node-id=123-456`
- Multiple node IDs: comma-separated in node-id param, or passed as arguments

## Execution

```bash
python3 .specify/extensions/figma-export/scripts/bash/figma_export.py "<FIGMA_URL>"
```

The script:
1. Reads `FIGMA_TOKEN` from the environment
2. Parses the file key and optional node IDs from the URL
3. If no node IDs given, lists all top-level frames in the file and downloads all of them
4. Calls `GET /v1/images/{file_key}?ids={node_ids}&format=png&scale=2`
5. Downloads the PNGs to `specs/<feature>/designs/`
6. Names files after the frame name (slugified), e.g. `vista-equipo-activo.png`
7. Appends an `## Designs` section to `spec.md` referencing the downloaded images (if not already present)

## Output

```
✅ Downloaded 3 frame(s) to specs/001-client-team-assignments/designs/
  - designs/equipo-activo.png  (Frame: "Equipo Activo")
  - designs/historico.png      (Frame: "Histórico")
  - designs/cierre-equipo.png  (Frame: "Cierre de Equipo")
```

## Error Handling

- Missing `FIGMA_TOKEN`: error with instructions to set it
- Invalid URL: clear error message
- Frame not found: list available frames in the file
- API rate limit: wait and retry once