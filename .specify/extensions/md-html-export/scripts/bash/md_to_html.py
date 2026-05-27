#!/usr/bin/env python3
"""Spec Kit - Markdown to HTML converter. Generates a single navigable index.html per feature."""
import sys, re, json, html as html_mod
from pathlib import Path
from datetime import date

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------
TPL = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{title}</title>
  <style>
    *{{box-sizing:border-box}}
    body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;font-size:16px;line-height:1.7;color:#1a1a2e;background:#f8f9fc;margin:0;padding:0}}

    /* ── Top nav ── */
    nav{{position:sticky;top:0;z-index:100;background:#0f172a;border-bottom:1px solid #1e293b;padding:.55rem 2rem;display:flex;gap:1.2rem;flex-wrap:wrap;align-items:center}}
    nav a{{color:#94a3b8;text-decoration:none;font-size:.8rem;font-weight:500;white-space:nowrap;padding:.2rem .4rem;border-radius:4px;transition:background .15s,color .15s}}
    nav a:hover{{color:#f1f5f9;background:#1e293b}}
    nav a.active{{color:#60a5fa;background:#1e3a5f}}
    nav .brand{{color:#3b82f6;font-weight:800;font-size:.9rem;margin-right:.5rem;letter-spacing:-.01em}}
    nav .sep{{color:#334155;font-size:.7rem}}

    /* ── Layout ── */
    .page{{max-width:940px;margin:2rem auto 4rem;padding:0 1.5rem}}

    /* ── Cover / index card ── */
    .cover{{background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);border-radius:12px;padding:2.5rem 3rem 2rem;margin-bottom:2rem;color:#f1f5f9;box-shadow:0 4px 24px rgba(0,0,0,.18)}}
    .cover h1{{font-size:1.75rem;font-weight:800;color:#fff;margin:0 0 .5rem;border:none;padding:0}}
    .cover .meta{{display:flex;gap:1.2rem;flex-wrap:wrap;font-size:.82rem;color:#94a3b8;margin-bottom:1.5rem}}
    .cover .meta span{{display:flex;align-items:center;gap:.3rem}}
    .cover .meta a{{color:#60a5fa;text-decoration:none}}
    .cover .meta a:hover{{text-decoration:underline}}
    .cover .badge{{display:inline-block;background:#1e3a5f;color:#60a5fa;font-size:.7rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:.15rem .55rem;border-radius:20px;border:1px solid #2563eb}}
    .index-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:.75rem;margin-top:.25rem}}
    .index-card{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);border-radius:8px;padding:.85rem 1rem;text-decoration:none;color:#cbd5e1;transition:background .15s,border-color .15s,transform .1s;display:flex;flex-direction:column;gap:.25rem}}
    .index-card:hover{{background:rgba(255,255,255,.11);border-color:#3b82f6;transform:translateY(-1px);color:#f1f5f9}}
    .index-card .card-icon{{font-size:1.1rem}}
    .index-card .card-label{{font-size:.82rem;font-weight:600;color:#e2e8f0}}
    .index-card .card-sub{{font-size:.72rem;color:#64748b}}
    .index-group-title{{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#475569;margin:.9rem 0 .35rem}}

    /* ── Content sections ── */
    .section{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:2.5rem 3rem;box-shadow:0 2px 12px rgba(0,0,0,.05);margin-bottom:1.75rem;scroll-margin-top:52px}}
    .section-label{{font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#3b82f6;margin-bottom:.75rem;display:flex;align-items:center;gap:.4rem}}
    .section-label .icon{{font-size:.95rem}}
    h1{{font-size:1.9rem;font-weight:700;color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:.5rem;margin-top:0}}
    h2{{font-size:1.35rem;font-weight:600;color:#1e293b;border-bottom:1px solid #f1f5f9;padding-bottom:.25rem;margin-top:2rem}}
    h3{{font-size:1.1rem;font-weight:600;color:#334155;margin-top:1.6rem}}
    h4{{font-size:1rem;font-weight:600;color:#475569;margin-top:1.3rem}}
    h5,h6{{font-size:.9rem;font-weight:600;color:#64748b;margin-top:1.1rem}}
    p{{margin:.65rem 0}}
    a{{color:#2563eb;text-decoration:none}} a:hover{{text-decoration:underline}}
    strong{{font-weight:600}} em{{font-style:italic}}
    code{{font-family:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;font-size:.855rem;background:#f1f5f9;border:1px solid #e2e8f0;border-radius:4px;padding:.1em .35em}}
    pre{{background:#0f172a;color:#e2e8f0;border-radius:6px;padding:1.1rem 1.4rem;overflow-x:auto;font-size:.82rem;line-height:1.6;margin:1rem 0}}
    pre code{{background:none;border:none;padding:0;color:inherit;font-size:inherit}}
    blockquote{{border-left:4px solid #3b82f6;margin:1rem 0;padding:.5rem 1rem;background:#eff6ff;color:#1e40af;border-radius:0 4px 4px 0}}
    blockquote p{{margin:0}}
    ul,ol{{margin:.65rem 0;padding-left:1.7rem}} li{{margin:.2rem 0}}
    li input[type=checkbox]{{margin-right:.4rem}}
    hr{{border:none;border-top:1px solid #f1f5f9;margin:1.75rem 0}}
    table{{border-collapse:collapse;width:100%;margin:.9rem 0;font-size:.875rem}}
    th{{background:#f8fafc;font-weight:600;text-align:left;padding:.55rem .85rem;border:1px solid #e2e8f0;color:#334155}}
    td{{padding:.5rem .85rem;border:1px solid #e2e8f0;vertical-align:top}}
    tr:nth-child(even) td{{background:#fafafa}}
    .nc{{background:#fef3c7;border:1px solid #f59e0b;border-radius:4px;padding:.1em .4em;font-size:.82em;color:#92400e}}
    .footer{{margin-top:3rem;padding-top:1rem;border-top:1px solid #e2e8f0;font-size:.78rem;color:#94a3b8;text-align:center}}
    .mermaid{{margin:1rem 0;text-align:center}}
    .mermaid svg{{max-width:100%;height:auto}}
    .oq-badge{{display:inline-block;background:#fef9c3;color:#854d0e;font-size:.7rem;font-weight:700;padding:.1rem .45rem;border-radius:20px;border:1px solid #fbbf24;margin-left:.4rem;vertical-align:middle}}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
  <script>mermaid.initialize({{startOnLoad:true,theme:'base',themeVariables:{{primaryColor:'#eff6ff',primaryBorderColor:'#3b82f6',primaryTextColor:'#1e293b',lineColor:'#64748b',fontSize:'14px'}}}});</script>
  <script>
    document.addEventListener('DOMContentLoaded', () => {{
      const links = document.querySelectorAll('nav a[href^="#"]');
      const obs = new IntersectionObserver(entries => {{
        entries.forEach(e => {{
          if (e.isIntersecting) {{
            links.forEach(l => l.classList.toggle('active', l.getAttribute('href') === '#' + e.target.id));
          }}
        }});
      }}, {{rootMargin: '-10% 0px -80% 0px'}});
      document.querySelectorAll('.section[id],.cover[id]').forEach(s => obs.observe(s));
    }});
  </script>
</head>
<body>
<nav>
  <span class="brand">Spec Kit</span>
  <span class="sep">|</span>
  {nav_links}
</nav>
<div class="page">
{cover}
{sections}
<div class="footer">Generated by Spec Kit &middot; Afianza &middot; {today}</div>
</div>
</body></html>"""

# ---------------------------------------------------------------------------
# Section order & metadata
# ---------------------------------------------------------------------------
SECTION_ORDER = ['spec', 'plan', 'data-model', 'research', 'tasks', 'quickstart']

SECTION_META = {
    'spec':        ('📋', 'Specification',   'Requirements & user stories'),
    'plan':        ('🏗️', 'Technical Plan',  'Architecture & design'),
    'data-model':  ('🗄️', 'Data Model',      'Entities & relationships'),
    'research':    ('🔬', 'Research',         'Spikes & findings'),
    'tasks':       ('✅', 'Tasks',            'Implementation plan'),
    'quickstart':  ('⚡', 'Quickstart',       'Getting started guide'),
}

SUBDIR_ICONS = {
    'checklists': '☑️',
    'contracts':  '📑',
    'designs':    '🎨',
}

# ---------------------------------------------------------------------------
# Inline / block renderers
# ---------------------------------------------------------------------------
def esc(s): return html_mod.escape(s, quote=False)

def inl(s):
    s = re.sub(r'\[NEEDS CLARIFICATION:([^\]]+)\]',
               r'<span class="nc">&#x26A0; NEEDS CLARIFICATION:\1</span>', s)
    s = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', s)
    s = re.sub(r'\*\*(.+?)\*\*',     r'<strong>\1</strong>', s)
    s = re.sub(r'__(.+?)__',          r'<strong>\1</strong>', s)
    s = re.sub(r'\*([^*\n]+?)\*',    r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', lambda m: f'<code>{esc(m.group(1))}</code>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'~~(.+?)~~', r'<del>\1</del>', s)
    return s

def tbl(rows):
    out = ['<table>']; hd = False
    for r in rows:
        r = r.strip()
        if not r.startswith('|'): continue
        cells = [c.strip() for c in r.split('|')[1:-1]]
        if all(re.match(r'^:?-+:?$', c.replace(' ', '')) for c in cells if c):
            hd = True; continue
        t = 'th' if not hd else 'td'
        out.append('<tr>' + ''.join(f'<{t}>{inl(esc(c))}</{t}>' for c in cells) + '</tr>')
    out.append('</table>')
    return '\n'.join(out)

def lst(lines):
    ordered = bool(re.match(r'^\d+[.)]\s', lines[0].strip()))
    tag = 'ol' if ordered else 'ul'
    items = []
    for l in lines:
        m = re.match(r'^(\s*)(?:\d+[.)]\s|\*\s|-\s|\+\s)(.*)', l)
        if not m: continue
        c = m.group(2)
        cb = re.match(r'^\[([ xX])\]\s*(.*)', c)
        if cb:
            chk = 'checked' if cb.group(1).lower() == 'x' else ''
            c = f'<input type="checkbox" disabled {chk}/> {inl(esc(cb.group(2)))}'
        else:
            c = inl(esc(c))
        items.append(f'<li>{c}</li>')
    return f'<{tag}>\n' + '\n'.join(items) + f'\n</{tag}>'

def convert_body(md):
    lines = md.split('\n')
    if lines and lines[0].strip() == '---':
        e = next((j for j in range(1, len(lines)) if lines[j].strip() == '---'), None)
        if e: lines = lines[e + 1:]
    text = re.sub(r'<!--.*?-->', '', '\n'.join(lines), flags=re.DOTALL)
    lines = text.split('\n')
    out = []; i = 0
    in_c = False; c_lang = ''; c_buf = []; t_buf = []; l_buf = []

    def fl():
        if l_buf: out.append(lst(list(l_buf))); l_buf.clear()
    def ft():
        if t_buf: out.append(tbl(list(t_buf))); t_buf.clear()

    while i < len(lines):
        r = lines[i].rstrip()
        if r.startswith('```'):
            fl(); ft()
            if not in_c: in_c = True; c_lang = r[3:].strip(); c_buf = []
            else:
                in_c = False
                if c_lang == 'mermaid':
                    out.append(f'<div class="mermaid">{chr(10).join(c_buf)}</div>')
                else:
                    body = '\n'.join(esc(x) for x in c_buf)
                    la = f' class="language-{c_lang}"' if c_lang else ''
                    out.append(f'<pre><code{la}>{body}</code></pre>')
            i += 1; continue
        if in_c: c_buf.append(r); i += 1; continue
        if r.startswith('|'): fl(); t_buf.append(r); i += 1; continue
        else: ft()
        if re.match(r'^(\*\*\*+|---+|___+)\s*$', r): fl(); out.append('<hr/>'); i += 1; continue
        m = re.match(r'^(#{1,6})\s+(.*)', r)
        if m:
            fl(); lv = len(m.group(1))
            out.append(f'<h{lv}>{inl(esc(m.group(2)))}</h{lv}>')
            i += 1; continue
        if r.startswith('>'):
            fl(); c = re.sub(r'^>\s?', '', r)
            out.append(f'<blockquote><p>{inl(esc(c))}</p></blockquote>')
            i += 1; continue
        if re.match(r'^(\s*)(\*|-|\+|\d+[.)]) ', r):
            ft(); l_buf.append(r); i += 1; continue
        else: fl()
        if not r.strip(): i += 1; continue
        para = [r]; i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            if (not nxt.strip() or nxt.startswith('#') or nxt.startswith('>') or
                    nxt.startswith('|') or nxt.startswith('```') or
                    re.match(r'^(\s*)(\*|-|\+|\d+[.)]) ', nxt) or
                    re.match(r'^(\*\*\*+|---+|___+)\s*$', nxt)):
                break
            para.append(nxt); i += 1
        out.append(f'<p>{inl(esc(" ".join(x.strip() for x in para)))}</p>')
    fl(); ft()
    return '\n'.join(out)

# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------
def section_sort_key(path: Path):
    stem = path.stem.lower()
    try: return (0, SECTION_ORDER.index(stem), str(path))
    except ValueError: return (0, len(SECTION_ORDER), str(path))

def find_md_files(feature_dir: Path):
    top = sorted([p for p in feature_dir.glob('*.md') if p.name != 'index.md'], key=section_sort_key)
    sub = sorted([p for p in feature_dir.rglob('*.md')
                  if p.parent != feature_dir and p.name != 'index.md'], key=lambda p: str(p))
    return top + sub

def make_label(path: Path, feature_dir: Path):
    stem = path.stem.lower()
    if stem in SECTION_META: return SECTION_META[stem][1]
    rel = path.relative_to(feature_dir)
    parts = str(rel.with_suffix('')).replace('\\', '/').split('/')
    return ' · '.join(p.replace('-', ' ').replace('_', ' ').title() for p in parts)

def make_icon(path: Path, feature_dir: Path):
    stem = path.stem.lower()
    if stem in SECTION_META: return SECTION_META[stem][0]
    rel = path.relative_to(feature_dir)
    parent = rel.parts[0] if len(rel.parts) > 1 else ''
    return SUBDIR_ICONS.get(parent, '📄')

def make_sub(path: Path, feature_dir: Path):
    stem = path.stem.lower()
    if stem in SECTION_META: return SECTION_META[stem][2]
    rel = path.relative_to(feature_dir)
    if len(rel.parts) > 1: return rel.parts[0].replace('-', ' ').title()
    return ''

# ---------------------------------------------------------------------------
# Extract spec metadata (epic link, status, dates)
# ---------------------------------------------------------------------------
def extract_spec_meta(spec_path: Path):
    meta = {'epic_key': None, 'epic_url': None, 'status': None, 'created': None, 'updated': None, 'open_questions': 0}
    if not spec_path.exists(): return meta
    txt = spec_path.read_text(encoding='utf-8')
    m = re.search(r'\*\*Epic\*\*:\s*\[([^\]]+)\]\(([^)]+)\)', txt)
    if m: meta['epic_key'] = m.group(1); meta['epic_url'] = m.group(2)
    m = re.search(r'\*\*Status\*\*:\s*(.+)', txt)
    if m: meta['status'] = m.group(1).strip()
    m = re.search(r'\*\*Created\*\*:\s*(.+)', txt)
    if m: meta['created'] = m.group(1).strip()
    m = re.search(r'\*\*Updated\*\*:\s*(.+)', txt)
    if m: meta['updated'] = m.group(1).strip()
    meta['open_questions'] = len(re.findall(r'^\|\s*OQ-\d+', txt, re.MULTILINE))
    return meta

# ---------------------------------------------------------------------------
# Cover / index section
# ---------------------------------------------------------------------------
def build_cover(feature_name: str, meta: dict, sections_info: list):
    # Meta bar
    meta_parts = []
    if meta['epic_key'] and meta['epic_url']:
        meta_parts.append(f'<span>🔗 <a href="{esc(meta["epic_url"])}" target="_blank">{esc(meta["epic_key"])}</a></span>')
    if meta['status']:
        meta_parts.append(f'<span>📌 {esc(meta["status"])}</span>')
    if meta['updated']:
        meta_parts.append(f'<span>🗓 Updated {esc(meta["updated"])}</span>')
    elif meta['created']:
        meta_parts.append(f'<span>🗓 Created {esc(meta["created"])}</span>')
    if meta['open_questions']:
        meta_parts.append(f'<span>⚠️ <strong>{meta["open_questions"]} open question{"s" if meta["open_questions"] != 1 else ""}</strong> pending PO</span>')

    meta_html = f'<div class="meta">{"".join(meta_parts)}</div>' if meta_parts else ''

    # Group sections into Core / Quality / Contracts / Other
    groups = {'Core': [], 'Checklists': [], 'Contracts': []}
    for anchor, label, icon, sub, _ in sections_info:
        if 'checklist' in anchor.lower() or sub.lower() == 'checklists':
            groups['Checklists'].append((anchor, label, icon, sub))
        elif 'contract' in anchor.lower() or sub.lower() == 'contracts':
            groups['Contracts'].append((anchor, label, icon, sub))
        else:
            groups['Core'].append((anchor, label, icon, sub))

    grid_html = ''
    for group_name, items in groups.items():
        if not items: continue
        grid_html += f'<div class="index-group-title">{group_name}</div><div class="index-grid">'
        for anchor, label, icon, sub in items:
            oq = ' <span class="oq-badge">⚠️ OQ</span>' if anchor == 'spec' and meta['open_questions'] else ''
            grid_html += (
                f'<a class="index-card" href="#{anchor}">'
                f'<span class="card-icon">{icon}</span>'
                f'<span class="card-label">{esc(label)}{oq}</span>'
                f'<span class="card-sub">{esc(sub)}</span>'
                f'</a>'
            )
        grid_html += '</div>'

    return (
        f'<div class="cover" id="index">'
        f'<h1>{esc(feature_name)}</h1>'
        f'{meta_html}'
        f'{grid_html}'
        f'</div>'
    )

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) >= 2: fd = Path(sys.argv[1])
    else:
        fj = Path('.specify/feature.json')
        if not fj.exists(): print('Warning: .specify/feature.json not found'); sys.exit(1)
        try: fd = Path(json.loads(fj.read_text())['feature_directory'])
        except Exception as e: print(f'Warning: {e}'); sys.exit(1)

    if not fd.exists(): print(f'Warning: {fd} not found'); sys.exit(1)

    md_files = find_md_files(fd)
    if not md_files: print(f'No .md files in {fd}'); sys.exit(0)

    # Feature name
    feature_name = fd.name.replace('-', ' ').replace('_', ' ').title()
    spec_path = fd / 'spec.md'
    if spec_path.exists():
        m = re.search(r'^#\s+(?:Feature Specification:\s*)?(.+)', spec_path.read_text(encoding='utf-8'), re.MULTILINE)
        if m: feature_name = m.group(1).strip()

    meta = extract_spec_meta(spec_path)
    sections_info = []  # (anchor, label, icon, sub, body)
    sections_html = []
    nav_items = [f'<a href="#index">Index</a>']

    for p in md_files:
        try:
            txt = p.read_text(encoding='utf-8')
            rel = p.relative_to(fd)
            anchor = str(rel.with_suffix('')).replace('/', '-').replace('\\', '-').lower()
            label = make_label(p, fd)
            icon = make_icon(p, fd)
            sub = make_sub(p, fd)
            body = convert_body(txt)

            sections_info.append((anchor, label, icon, sub, body))
            sections_html.append(
                f'<div class="section" id="{anchor}">\n'
                f'  <div class="section-label"><span class="icon">{icon}</span> {esc(label)}</div>\n'
                f'  {body}\n'
                f'</div>'
            )
            nav_items.append(f'<a href="#{anchor}">{icon} {esc(label)}</a>')
            print(f'  OK {p}')
        except Exception as e:
            print(f'  FAIL {p}: {e}')

    cover = build_cover(feature_name, meta, sections_info)
    html = TPL.format(
        title=esc(feature_name),
        nav_links='\n  '.join(nav_items),
        cover=cover,
        sections='\n'.join(sections_html),
        today=date.today().isoformat(),
    )

    out_path = fd / 'index.html'
    out_path.write_text(html, encoding='utf-8')
    print(f'\nGenerated {out_path} ({len(md_files)} section(s))')

if __name__ == '__main__':
    main()
