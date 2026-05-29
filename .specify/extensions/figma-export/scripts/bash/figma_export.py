#!/usr/bin/env python3
"""
Spec Kit - Figma Frame Exporter
Downloads Figma frames as PNG into specs/<feature>/designs/
No external dependencies — uses stdlib urllib only.

Usage:
    python3 figma_export.py "<figma_url>" [node_id1 node_id2 ...]
"""

import sys, os, re, json, time, urllib.request, urllib.parse, urllib.error
from pathlib import Path


API = "https://api.figma.com/v1"


def slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'[àáâãäå]', 'a', name)
    name = re.sub(r'[èéêë]', 'e', name)
    name = re.sub(r'[ìíîï]', 'i', name)
    name = re.sub(r'[òóôõö]', 'o', name)
    name = re.sub(r'[ùúûü]', 'u', name)
    name = re.sub(r'[ñ]', 'n', name)
    name = re.sub(r'[^a-z0-9]+', '-', name)
    return name.strip('-') or 'frame'


def figma_get(path: str, token: str) -> dict:
    url = f"{API}{path}"
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Figma API error {e.code}: {body}")


def download_file(url: str, dest: Path):
    with urllib.request.urlopen(url, timeout=60) as r:
        dest.write_bytes(r.read())


def parse_figma_url(url: str) -> tuple[str, list[str]]:
    """Returns (file_key, [node_ids])"""
    m = re.search(r'/(?:file|design|proto)/([A-Za-z0-9_-]+)', url)
    if not m:
        raise ValueError(f"Could not extract file key from URL: {url}")
    file_key = m.group(1)
    node_ids = []
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    if 'node-id' in qs:
        for nid in qs['node-id']:
            node_ids.extend(n.strip() for n in nid.split(',') if n.strip())
    return file_key, node_ids


def _is_bold_text(node: dict) -> bool:
    """Returns True if node is a TEXT with bold weight (Figma uses fontWeight or fontPostScriptName)."""
    if node.get('type') != 'TEXT':
        return False
    style = node.get('style') or {}
    weight = style.get('fontWeight')
    if isinstance(weight, (int, float)) and weight >= 600:
        return True
    psname = style.get('fontPostScriptName') or ''
    if isinstance(psname, str) and ('Bold' in psname or 'Black' in psname or 'Heavy' in psname):
        return True
    return False


def _infer_journey(frame_bbox: dict, text_labels: list[dict]) -> str | None:
    """Find the bold TEXT label that best describes the journey of the frame.

    Two-pass heuristic:
      (1) closest TEXT directly above (vertical bottom <= frame.y) AND horizontally
          overlapping the frame's column. Strongest signal.
      (2) if no overlap match, fall back to the TEXT whose top y is closest above
          the frame's top y *regardless of horizontal alignment* — captures the case
          where the label is anchored to the leftmost frame of a row but the frame
          sits to its right.

    The vertical-gap budget for the fallback is capped at 1200px to avoid attributing
    a frame on row N to a label many rows above.
    """
    if not frame_bbox:
        return None
    fx, fy, fw = frame_bbox['x'], frame_bbox['y'], frame_bbox['width']

    # Pass 1 — strict horizontal overlap
    best = None
    best_gap = float('inf')
    for label in text_labels:
        lb = label['bbox']
        lbottom = lb['y'] + lb['height']
        if lbottom > fy:
            continue
        if (lb['x'] + lb['width']) < fx or lb['x'] > (fx + fw):
            continue
        gap = fy - lbottom
        if gap < best_gap:
            best_gap = gap
            best = label
    if best:
        return best['characters']

    # Pass 2 — closest above ignoring x, capped vertical distance
    best = None
    best_gap = float('inf')
    for label in text_labels:
        lb = label['bbox']
        lbottom = lb['y'] + lb['height']
        gap = fy - lbottom
        if gap < 0 or gap > 1200:
            continue
        if gap < best_gap:
            best_gap = gap
            best = label
    return best['characters'] if best else None


def get_top_level_frames(file_key: str, token: str) -> list[dict]:
    """Returns list of {id, name, section_id, section_name} for FRAME / COMPONENT nodes.

    Three-tier detection of the "user journey" each frame belongs to:
      1. SECTION parent (Figma native grouping) — strongest signal.
      2. Bold TEXT label positioned above the frame on the canvas — heuristic for files
         that use floating headers instead of SECTIONs.
      3. None — frame stays loose.
    """
    data = figma_get(f"/files/{file_key}?depth=3", token)
    frames = []
    pages = data.get('document', {}).get('children', [])
    for page in pages:
        # Collect bold TEXT labels at page level (heuristic source)
        text_labels = []
        for child in page.get('children', []):
            if _is_bold_text(child):
                bbox = child.get('absoluteBoundingBox')
                if bbox:
                    text_labels.append({
                        'characters': (child.get('characters') or '').strip(),
                        'bbox': bbox,
                    })

        for child in page.get('children', []):
            ctype = child.get('type')
            if ctype == 'SECTION':
                section_id = child['id']
                section_name = child['name']
                for grandchild in child.get('children', []):
                    if grandchild.get('type') in ('FRAME', 'COMPONENT'):
                        frames.append({
                            'id': grandchild['id'],
                            'name': grandchild['name'],
                            'section_id': section_id,
                            'section_name': section_name,
                        })
            elif ctype in ('FRAME', 'COMPONENT'):
                bbox = child.get('absoluteBoundingBox')
                inferred = _infer_journey(bbox, text_labels) if bbox else None
                frames.append({
                    'id': child['id'],
                    'name': child['name'],
                    'section_id': None,
                    'section_name': inferred,
                })
    return frames


def get_node_names(file_key: str, node_ids: list[str], token: str) -> dict[str, str]:
    """Returns {node_id: name} for the given node IDs."""
    ids_param = ','.join(node_ids)
    data = figma_get(f"/files/{file_key}/nodes?ids={urllib.parse.quote(ids_param)}", token)
    result = {}
    for nid, node_data in data.get('nodes', {}).items():
        name = node_data.get('document', {}).get('name', nid)
        result[nid] = name
    return result


def export_frames(file_key: str, node_ids: list[str], token: str, scale: int = 2) -> dict[str, str]:
    """Returns {node_id: image_url}"""
    ids_param = ','.join(node_ids)
    data = figma_get(
        f"/images/{file_key}?ids={urllib.parse.quote(ids_param)}&format=png&scale={scale}",
        token
    )
    if data.get('err'):
        raise RuntimeError(f"Figma export error: {data['err']}")
    return data.get('images', {})


def update_spec_designs(spec_path: Path, image_refs: list[dict]):
    """Append or update ## Designs section in spec.md, grouped by section_name."""
    if not spec_path.exists():
        return
    content = spec_path.read_text(encoding='utf-8')
    section = "\n## Designs\n\n"
    # Group by section_name preserving original order
    groups: dict[str, list[dict]] = {}
    order: list[str] = []
    for ref in image_refs:
        key = ref.get('section_name') or '_loose'
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(ref)
    for key in order:
        if key == '_loose':
            section += "### Sin user journey asociado\n\n"
        else:
            section += f"### {key}\n\n"
        for ref in groups[key]:
            section += f"![{ref['name']}]({ref['rel_path']})\n\n"
    if '## Designs' in content:
        content = re.sub(r'\n## Designs\n.*?(?=\n## |\Z)', section, content, flags=re.DOTALL)
    else:
        content = content.rstrip() + '\n' + section
    spec_path.write_text(content, encoding='utf-8')


def write_designs_index(designs_dir: Path, image_refs: list[dict], file_key: str):
    """Write designs/INDEX.md — auto-generated table of section → frame → file → Figma link."""
    if not image_refs:
        return
    lines = [
        "# Designs Index",
        "",
        "Auto-generado por `figma_export.py`. **No editar a mano** — se regenera en cada ejecución.",
        "",
        "| User journey | Frame (Figma) | Archivo | Node ID | Figma |",
        "|---|---|---|---|---|",
    ]
    for ref in image_refs:
        journey = ref.get('section_name') or '_sin journey_'
        frame_name = ref['name']
        rel = ref['rel_path'].removeprefix('designs/')
        nid = ref['node_id']
        node_url_part = nid.replace(':', '-')
        deep_link = f"https://www.figma.com/design/{file_key}?node-id={node_url_part}"
        lines.append(f"| {journey} | {frame_name} | `{rel}` | `{nid}` | [abrir]({deep_link}) |")
    (designs_dir / 'INDEX.md').write_text("\n".join(lines) + "\n", encoding='utf-8')


def main():
    token = os.environ.get('FIGMA_TOKEN', '').strip()
    if not token:
        print("Error: FIGMA_TOKEN environment variable is not set.")
        print("Set it in .claude/settings.json under 'env' or export it in your shell.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: figma_export.py <figma_url> [node_id ...]")
        sys.exit(1)

    figma_url = sys.argv[1]
    extra_node_ids = sys.argv[2:]

    # Resolve feature directory
    fj = Path('.specify/feature.json')
    if fj.exists():
        try:
            feature_dir = Path(json.loads(fj.read_text())['feature_directory'])
        except Exception:
            feature_dir = Path('specs/designs')
    else:
        feature_dir = Path('specs/designs')

    designs_dir = feature_dir / 'designs'
    designs_dir.mkdir(parents=True, exist_ok=True)

    try:
        file_key, url_node_ids = parse_figma_url(figma_url)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    node_ids = list(dict.fromkeys(url_node_ids + extra_node_ids))

    print(f"File key: {file_key}")

    # node_meta: {node_id: {name, section_name}}
    node_meta: dict[str, dict] = {}

    if not node_ids:
        print("No node IDs provided — fetching all top-level frames...")
        try:
            frames = get_top_level_frames(file_key, token)
        except RuntimeError as e:
            print(f"Error fetching file: {e}")
            sys.exit(1)
        if not frames:
            print("No frames found in file.")
            sys.exit(0)
        print(f"Found {len(frames)} frame(s):")
        for f in frames:
            journey = f"  [journey: {f['section_name']}]" if f.get('section_name') else ""
            print(f"  - [{f['id']}] {f['name']}{journey}")
        node_ids = [f['id'] for f in frames]
        node_meta = {f['id']: {'name': f['name'], 'section_name': f.get('section_name')} for f in frames}
    else:
        try:
            names = get_node_names(file_key, node_ids, token)
        except RuntimeError as e:
            print(f"Error fetching node names: {e}")
            names = {nid: nid for nid in node_ids}
        node_meta = {nid: {'name': names.get(nid, nid), 'section_name': None} for nid in node_ids}

    # Export
    print(f"\nExporting {len(node_ids)} frame(s) at 2x...")
    try:
        image_urls = export_frames(file_key, node_ids, token)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    downloaded = []
    # Track collisions per (section, slug)
    seen: dict[tuple, int] = {}
    for nid in node_ids:
        img_url = image_urls.get(nid)
        if not img_url:
            print(f"  SKIP [{nid}] — no image URL returned")
            continue
        meta = node_meta.get(nid, {'name': nid, 'section_name': None})
        name = meta['name']
        section_name = meta.get('section_name')
        section_slug = slugify(section_name) if section_name else None
        frame_slug = slugify(name)
        key = (section_slug, frame_slug)
        seen[key] = seen.get(key, 0) + 1
        suffix = f"-{seen[key]:02d}" if seen[key] > 1 else ""
        filename = f"{frame_slug}{suffix}.png"
        subdir = designs_dir / section_slug if section_slug else designs_dir
        subdir.mkdir(parents=True, exist_ok=True)
        dest = subdir / filename
        try:
            download_file(img_url, dest)
            rel = str(dest.relative_to(feature_dir))
            label_path = f"{section_slug}/{filename}" if section_slug else filename
            journey_log = f"  [{section_name}]" if section_name else ""
            print(f"  OK  designs/{label_path}{journey_log}  (\"{name}\")")
            downloaded.append({
                'name': name,
                'section_name': section_name,
                'rel_path': rel,
                'path': str(dest),
                'node_id': nid,
            })
        except Exception as e:
            print(f"  FAIL [{nid}] {name}: {e}")

    if downloaded:
        spec_path = feature_dir / 'spec.md'
        if spec_path.exists():
            update_spec_designs(spec_path, downloaded)
            print(f"\nUpdated {spec_path} with {len(downloaded)} design reference(s)")
        write_designs_index(designs_dir, downloaded, file_key)
        print(f"Wrote {designs_dir / 'INDEX.md'}")

    print(f"\nDone: {len(downloaded)}/{len(node_ids)} frame(s) downloaded to {designs_dir}")


if __name__ == '__main__':
    main()
