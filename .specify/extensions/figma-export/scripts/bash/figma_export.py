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


def get_top_level_frames(file_key: str, token: str) -> list[dict]:
    """Returns list of {id, name} for top-level frames."""
    data = figma_get(f"/files/{file_key}?depth=2", token)
    frames = []
    pages = data.get('document', {}).get('children', [])
    for page in pages:
        for child in page.get('children', []):
            if child.get('type') in ('FRAME', 'COMPONENT', 'SECTION'):
                frames.append({'id': child['id'], 'name': child['name']})
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
    """Append or update ## Designs section in spec.md"""
    if not spec_path.exists():
        return
    content = spec_path.read_text(encoding='utf-8')
    section = "\n## Designs\n\n"
    for ref in image_refs:
        section += f"![{ref['name']}]({ref['rel_path']})\n\n"
    if '## Designs' in content:
        # Replace existing section
        content = re.sub(r'\n## Designs\n.*?(?=\n## |\Z)', section, content, flags=re.DOTALL)
    else:
        content = content.rstrip() + '\n' + section
    spec_path.write_text(content, encoding='utf-8')


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
            print(f"  - [{f['id']}] {f['name']}")
        node_ids = [f['id'] for f in frames]
        names = {f['id']: f['name'] for f in frames}
    else:
        try:
            names = get_node_names(file_key, node_ids, token)
        except RuntimeError as e:
            print(f"Error fetching node names: {e}")
            names = {nid: nid for nid in node_ids}

    # Export
    print(f"\nExporting {len(node_ids)} frame(s) at 2x...")
    try:
        image_urls = export_frames(file_key, node_ids, token)
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

    downloaded = []
    for nid in node_ids:
        img_url = image_urls.get(nid)
        if not img_url:
            print(f"  SKIP [{nid}] — no image URL returned")
            continue
        name = names.get(nid, nid)
        filename = f"{slugify(name)}.png"
        dest = designs_dir / filename
        try:
            download_file(img_url, dest)
            rel = str(dest.relative_to(feature_dir))
            print(f"  OK  designs/{filename}  (\"{name}\")")
            downloaded.append({'name': name, 'rel_path': rel, 'path': str(dest)})
        except Exception as e:
            print(f"  FAIL [{nid}] {name}: {e}")

    if downloaded:
        spec_path = feature_dir / 'spec.md'
        if spec_path.exists():
            update_spec_designs(spec_path, downloaded)
            print(f"\nUpdated {spec_path} with {len(downloaded)} design reference(s)")

    print(f"\nDone: {len(downloaded)}/{len(node_ids)} frame(s) downloaded to {designs_dir}")


if __name__ == '__main__':
    main()
