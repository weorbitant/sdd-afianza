---
name: speckit-figma-export-browser
description: "Browser-driven bulk export of all Figma frames + semantic rename & organize by user journey. Replaces the REST API path (Figma rate-limits make it unusable). Requires Claude-in-Chrome connected to a browser logged into Figma."
argument-hint: "<figma_file_url>"
compatibility: Requires spec-kit project structure with .specify/ directory AND Claude-in-Chrome browser extension connected
metadata:
  author: afianza-local
  source: figma-export:commands/speckit.figma-export.browser.md
user-invocable: true
---


# Figma Frame Export — Browser-driven

Uses Claude-in-Chrome to drive Figma's own export UI. The Figma REST API path was removed (v2.0.0): rate-limits made it unusable for full file exports, and many real-world Figma files don't use `SECTION` parents to group frames — leaving the API path unable to infer user-journey hierarchy.

This browser-driven path:
- Uses the user's authenticated Figma session (no rate limit).
- Triggers Figma's native bulk export (`Cmd+A` → "Exportar N capas" → ZIP) — gives PNGs at full frame resolution, not viewport screenshots.
- Inspects frames multimodally to recover user-journey hierarchy when Figma doesn't encode it structurally.

## Pre-conditions

- Brave/Chrome with the Claude-in-Chrome extension connected to this session.
- User logged into Figma in that browser with access to the file.
- The feature directory exists with a `specs/<feature>/` folder. `designs/` will be created if needed.

## Usage

```
/speckit-figma-export-browser <figma_file_url>
```

`<figma_file_url>` — any Figma URL that points to the file. The skill navigates to the page given by `?node-id=X-Y` if present, otherwise to the default page.

## Execution

### Step 1 — Navigate and select all

1. Backup any existing `designs/` content to `designs.legacy/`.
2. Use `mcp__claude-in-chrome__tabs_context_mcp` to create a tab if needed.
3. Navigate the tab to the Figma URL.
4. Wait 6-8 seconds for Figma to load the canvas.
5. Click on empty canvas area to deselect.
6. Press `Cmd+A` (or `Ctrl+A` on non-mac) to select all frames in the active page.
7. Verify the right Properties panel shows "**N seleccionados**" — that tells you how many top-level nodes you have.

### Step 2 — Trigger Figma's native export

Two equivalent triggers:

- **Right panel button**: click `Exportar N capas` at the bottom of the Properties panel (coordinate varies by viewport size — read the page or screenshot first).
- **Keyboard**: `Cmd+Shift+E` opens the Export dialog. Click the `Exportar` button at the top right of that dialog.

Figma builds a ZIP server-side and starts a download (~10s for ~50 frames at 1x scale).

### Step 3 — Wait for download and extract

The ZIP lands in `~/Downloads/<file-name>.zip`. Brave/Chrome may store partial downloads in `~/Downloads/.com.brave.Browser.*` until complete.

```bash
mv ~/Downloads/*.zip specs/<feature>/designs/figma-export.zip
cd specs/<feature>/designs && unzip -q figma-export.zip && rm figma-export.zip
```

The ZIP contains one PNG per frame, named after the Figma layer name with `-N` suffixes for collisions. Example:
```
PortalAsesor - Ficha de cliente.png
PortalAsesor - Ficha de cliente-1.png
PortalAsesor - Ficha de cliente-2.png
...
PortalAsesor - Servicios contratados.png
PortalAsesor - Servicios contratados-1.png
```

### Step 4 — Separate off-topic frames

The bulk export captures *every* top-level frame on the page, including ones from other features or earlier versions. Move them aside:

```bash
mkdir -p _off-topic
mv "<known off-topic frame names>"*.png _off-topic/
```

Heuristic to identify off-topic: frame names referencing other features (`Servicios contratados`, `Obligaciones`…) or scaffolding (`Cover`, `layout 1440`, `Moodboard`).

### Step 5 — Read each frame multimodally to identify content

For each remaining PNG, invoke the `Read` tool. Multimodal Read renders the image and lets you describe:

- What screen state it shows (empty state / modal / completed view…).
- Which user journey it belongs to (based on which workflow step it represents).
- Any UI elements not yet covered by the spec (badges, checkboxes, sliders, banners…).

Take notes as you go — these notes feed the renaming step and the design-conformance section that `/speckit-clarify` will surface as design-vs-spec gaps.

### Step 6 — Create journey folders and rename

Group the frames into folders named after the user journey they belong to, prefixing with a sequence number for ordering. Example layout for this repo:

```
designs/
├── INDEX.md
├── 01-crear-equipo/
│   ├── 01-empty-state.png
│   ├── 02-modal-vacio.png
│   └── ...
├── 02-anadir-asesor/
│   ├── 01-modal-checkbox-principal.png
│   └── ...
├── ...
└── _off-topic/
    └── ...
```

Naming convention:
- **Folder**: `NN-<journey-slug>/` — sequenced by logical flow order, kebab-case.
- **File**: `NN-<state-or-action-slug>.png` — sequenced within the journey.

### Step 7 — Generate `INDEX.md`

Write `designs/INDEX.md` with:

1. **Header** — source file URL, page, export date, total frame count.
2. **Per-journey section** — for each folder, a markdown table `Archivo | Qué muestra` with one row per frame. Use 🔑 emoji to mark frames that reveal a **design-conformance finding** (UI element absent from the spec).
3. **Consolidated findings** — a final table listing each finding with: evidence frame path, spec/ADR affected, severity. `/speckit-clarify` reads these as design-conformance gaps when refining the spec.
4. **Off-topic** — short paragraph naming what's in `_off-topic/` and why.

## Output

```
✅ Browser export complete: specs/<feature>/designs/
  - Total frames extracted from ZIP: 30
  - In-scope frames organized in 8 journey folders: 23
  - Off-topic frames moved to _off-topic/: 6
  - INDEX.md generated with N design-conformance findings flagged

Next: invoke /speckit-clarify (or continue with the refinement workflow) — the findings table in INDEX.md will surface as design-conformance gaps for the spec.
```

## Error Handling

- **Brave asks for download confirmation each time**: ask user to grant "Always allow downloads from figma.com" in Brave Settings → Privacy → Sites and shields → Downloads.
- **ZIP empty or partial**: re-trigger the export click — sometimes the first Cmd+Shift+E reaches Figma before selection registers.
- **All frames are off-topic**: the URL pointed to a wrong page. Re-navigate with the right `?node-id=` and retry.
- **Multimodal Read on PNG fails**: the file may be 0 bytes — re-extract the ZIP.

## Pre-conditions that must hold

- Claude-in-Chrome MCP connected to a Chromium-based browser (Chrome / Brave / Edge).
- That browser has the user logged into Figma with access to the file.
- The browser is configured to not prompt on every download (Settings → Downloads → "Ask where to save each file" disabled for figma.com), or the user is willing to confirm each save manually.

If these don't hold, ask the user to set them up before invoking the command — there is no API fallback.
