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
6. **Preserves user-journey hierarchy** — frames inside a Figma `SECTION` land in a subfolder named after the section (slugified). Loose page-level frames go to the `designs/` root. Example: a `SECTION` named `User Journey: Crear equipo` containing a frame `Estado inicial` produces `designs/user-journey-crear-equipo/estado-inicial.png`.
7. Names files after the frame name (slugified). Collisions inside the same section get `-01`, `-02`, … suffixes.
8. Writes `designs/INDEX.md` — auto-generated table (`journey | frame name | file | node id | Figma deep-link`). Overwritten on every run.
9. Appends or replaces `## Designs` in `spec.md`, grouped by `### <Section name>` per journey.

## Output

```
✅ Downloaded 5 frame(s) to specs/001-client-team-assignments/designs/
  - designs/crear-equipo/estado-inicial.png            [Crear equipo]
  - designs/crear-equipo/modal-anadir-asignacion.png   [Crear equipo]
  - designs/anadir-miembro/seleccion-rol.png           [Añadir miembro]
  - designs/anadir-miembro/seleccion-empleado.png      [Añadir miembro]
  - designs/equipo-completo.png                        [loose — no section]
Wrote specs/001-client-team-assignments/designs/INDEX.md
```

## Error Handling

- Missing `FIGMA_TOKEN`: error with instructions to set it
- Invalid URL: clear error message
- Frame not found: list available frames in the file
- API rate limit: wait and retry once