#!/usr/bin/env python3
"""Render a compact Markdown cooking reference as HTML and a checked one-page PDF."""
import argparse
import base64
from datetime import date, datetime
import hashlib
import html
from io import BytesIO
import json
import os
from pathlib import Path
import re
import tempfile
from zoneinfo import ZoneInfo

# Only affects native-library lookup on macOS. No accounts or network at runtime.
os.environ.setdefault('DYLD_FALLBACK_LIBRARY_PATH', '/opt/homebrew/lib:/usr/local/lib')
ROOT = Path(__file__).resolve().parent.parent
MONTHS = ('January February March April May June July August September October November December').split()


def parse(source):
    """Deliberately small Markdown dialect; reject rather than silently discard."""
    if source.count('<!-- recipes:start -->') != 1 or source.count('<!-- recipes:end -->') != 1:
        raise ValueError('Use exactly one recipes:start/end marker pair.')
    before, rest = source.split('<!-- recipes:start -->')
    body, _ = rest.split('<!-- recipes:end -->')
    title = next((line[2:].strip() for line in before.splitlines() if line.startswith('# ')), None)
    if not title:
        raise ValueError('Add a # Sheet title before recipes:start.')
    groups, recipe = [], None
    for line in body.splitlines():
        if not line.strip():
            continue
        if line.startswith('## ') and not line.startswith('### '):
            groups.append({'title': line[3:].strip(), 'recipes': []})
            recipe = None
        elif line.startswith('### '):
            if not groups:
                raise ValueError('A recipe needs a ## Column group first.')
            recipe = {'title': line[4:].strip(), 'rows': []}
            groups[-1]['recipes'].append(recipe)
        elif line.startswith('- ') and recipe is not None:
            recipe['rows'].append(line[2:].strip())
        else:
            raise ValueError(f'Unsupported printable Markdown: {line!r}')
    if not 1 <= len(groups) <= 4:
        raise ValueError('Use one to four ## column groups.')
    titles = []
    for group in groups:
        if not group['title'] or not group['recipes']:
            raise ValueError('Empty column group.')
        for recipe in group['recipes']:
            if not recipe['title'] or not recipe['rows'] or any(not x for x in recipe['rows']):
                raise ValueError('Each recipe needs a title and nonempty bullet list.')
            titles.append(recipe['title'])
    if len(titles) != len(set(titles)):
        raise ValueError('Recipe titles must be unique.')
    return title, groups


def inline(value):
    value = re.sub(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]', lambda m: m[2] or m[1], value)
    value = re.sub(r'(\d+(?:\.\d+)?(?:/\d+)?|[¼½¾⅓⅔⅛⅜⅝⅞]) ([A-Za-z]+)', lambda m: m[1] + '\u00a0' + m[2], value)
    return html.escape(value)


def heading(value):
    """Use licensed images with explicit dimensions instead of OS emoji metrics."""
    if not value or ord(value[0]) < 0x2600:
        return inline(value)
    token, sep, label = value.partition(' ')
    key = '-'.join(f'{ord(c):x}' for c in token if c != '\ufe0f')
    asset = ROOT / 'assets/emoji' / (key + '.png')
    if not sep or not asset.is_file():
        raise ValueError(f'No bundled icon for {token!r}; choose a supported emoji or a plain title. See assets/emoji/README.md.')
    from PIL import Image
    rgba = Image.open(asset).convert('RGBA')
    white = Image.new('RGBA', rgba.size, 'white')
    white.alpha_composite(rgba)
    buff = BytesIO()
    white.convert('L').save(buff, format='PNG')
    encoded = base64.b64encode(buff.getvalue()).decode()
    return f'<img class="emoji" alt="{html.escape(token)}" src="data:image/png;base64,{encoded}"> ' + inline(label)


def render(source, stamp, paper='letter', widths=None):
    title, groups = parse(source)
    weights = widths or [1] * len(groups)
    if len(weights) != len(groups) or any(x <= 0 for x in weights):
        raise ValueError('--widths must contain one positive number per column.')
    style = (ROOT / 'assets/print.css').read_text()
    wide, tall = (8.5 * 96, 11 * 96) if paper == 'letter' else (210 / 25.4 * 96, 297 / 25.4 * 96)
    style += f'\n@page {{ size:{paper}; margin:.35in; }}\n#crib-sheet {{ width:{wide - 67.2}px; }}\n'
    style += '#crib-sheet main { grid-template-columns:' + ' '.join(f'minmax(0,{w}fr)' for w in weights) + '; }\n'
    style += '@media screen and (max-width:600px) { #crib-sheet { width:100%; } #crib-sheet main { grid-template-columns:repeat(2,minmax(0,1fr)); } }\n'
    style += '@media screen and (max-width:360px) { #crib-sheet main { grid-template-columns:1fr; } }\n'
    columns = []
    for group in groups:
        cards = []
        for recipe in group['recipes']:
            rows = []
            for row in recipe['rows']:
                cls = ' class="method"' if re.match(r'^(?:\d+°|Sous Vide|Simmer|\d+’|Whisk)', row, re.I) else ''
                rows.append('<li' + cls + '>' + inline(row) + '</li>')
            cards.append('<section><h2>' + heading(recipe['title']) + '</h2><ul>' + ''.join(rows) + '</ul></section>')
        columns.append('<div class="column"><div class="category">' + inline(group['title']) + '</div><div class="stack">' + ''.join(cards) + '</div></div>')
    label = f'{MONTHS[stamp.month-1]} {stamp.day}, {stamp.year}'
    # Required attribution follows the licensed icons into the generated document.
    attribution = '<span>Icons: <a href="https://github.com/jdecked/twemoji">Twemoji</a> · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> (grayscale)</span>' if any(ord(r['title'][0]) >= 0x2600 for g in groups for r in g['recipes']) else ''
    fragment = '<style>' + style + '</style><div id="crib-sheet"><header><h1>' + inline(title) + '</h1></header><main>' + ''.join(columns) + '</main><footer><span>' + label + '</span>' + attribution + '</footer></div>'
    return fragment, groups, (wide, tall)


def normalize(value):
    return re.sub(r'\s+', '', value)


def validate(document, groups, dimensions):
    if len(document.pages) != 1:
        raise ValueError(f'Layout uses {len(document.pages)} pages. Shorten wording or rebalance groups; keep the current type size.')
    page = document.pages[0]
    w, h = dimensions
    if abs(page.width - w) > 1 or abs(page.height - h) > 1:
        raise ValueError('Unexpected PDF page size.')
    # These measurements come from the actual paginated layout, not CSS intent.
    for box in page._page_box.descendants():
        if getattr(box, 'text', '').strip() or getattr(box, 'element_tag', '') == 'img':
            if box.position_x < 32 or box.position_y < 32 or box.position_x + box.width > w-32 or box.position_y + box.height > h-32:
                raise ValueError('Content crosses the printable area; shorten or rebalance it.')
    from pypdf import PdfReader
    pdf = document.write_pdf()
    page_text = PdfReader(BytesIO(pdf)).pages[0].extract_text()
    missing = []
    for group in groups:
        for recipe in group['recipes']:
            label = recipe['title'].split(' ', 1)[1] if ord(recipe['title'][0]) >= 0x2600 else recipe['title']
            for value in [label, *recipe['rows']]:
                if normalize(html.unescape(inline(value))) not in normalize(page_text):
                    missing.append(value)
    if missing:
        raise ValueError('PDF text verification failed: ' + repr(missing[:3]))
    return pdf


def build(args):
    source = args.source.read_text(encoding='utf-8')
    stamp = date.fromisoformat(args.date) if args.date else datetime.now(ZoneInfo(args.timezone)).date()
    fragment, groups, dimensions = render(source, stamp, args.paper, args.widths)
    content = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Kitchen Crib Sheet</title>' + fragment + '</html>'
    out = args.out.resolve()
    if out in (args.source.resolve(), args.source.resolve().parent):
        raise ValueError('Choose a separate output directory.')
    if not args.preview_only:
        from weasyprint import HTML
        def local_data_only(url, **kwargs):
            from weasyprint import default_url_fetcher
            if not url.startswith('data:'):
                raise ValueError('External resources are disabled during rendering.')
            return default_url_fetcher(url, **kwargs)
        document = HTML(string=content, url_fetcher=local_data_only).render()
        pdf = validate(document, groups, dimensions)
    out.mkdir(parents=True, exist_ok=True)
    # Build/validate everything before changing any previous output.
    payloads = {'crib-sheet.html': content.encode(), 'preview.html': fragment.encode()}
    if not args.preview_only:
        payloads['crib-sheet.pdf'] = pdf
    receipt = {'mode': 'preview' if args.preview_only else 'pdf', 'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'date': stamp.isoformat(), 'paper': args.paper, 'recipe_count': sum(len(g['recipes']) for g in groups), 'pdf_validated': not args.preview_only, 'visual_review': 'pending', 'outputs': {k: hashlib.sha256(v).hexdigest() for k,v in payloads.items()}}
    payloads['build.json'] = (json.dumps(receipt,indent=2)+'\n').encode()
    with tempfile.TemporaryDirectory(prefix='.crib-', dir=out) as stage:
        for name, data in payloads.items():
            Path(stage,name).write_bytes(data)
        for name in payloads:
            os.replace(Path(stage,name),out/name)
    print(json.dumps({'output': str(out), **receipt}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, default=Path('output'))
    parser.add_argument('--preview-only', action='store_true', help='Do not build or update PDF')
    parser.add_argument('--date', help='ISO date, useful for reproducible editions')
    parser.add_argument('--timezone', default='UTC', help='IANA zone for today, default UTC')
    parser.add_argument('--paper', choices=['letter','a4'], default='letter')
    parser.add_argument('--widths', type=lambda s:[float(x) for x in s.split(',')])
    args = parser.parse_args()
    try:
        build(args)
    except (ValueError, OSError, ImportError) as exc:
        parser.exit(1, f'Build stopped: {exc}\n')

if __name__ == '__main__':
    main()
