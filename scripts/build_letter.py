"""Typeset PTAC's letter to the City Council (research/ordinance-proposals.md) as print-ready HTML.

npm run letter runs this, then scripts/print-letter.mjs prints the HTML to PDF.
Usage: python3 scripts/build_letter.py [input.md] [output.html]
Defaults: research/ordinance-proposals.md -> .cache/letter.html
The markdown is the repo copy of the Claude Doc; this script only styles it (letterhead,
chart, the shaded proposed text, Today/Proposed/Why blocks, roster in columns).
"""
import html
import os
import re
import sys

src = sys.argv[1] if len(sys.argv) > 1 else 'research/ordinance-proposals.md'
out = sys.argv[2] if len(sys.argv) > 2 else '.cache/letter.html'
lines = open(src, encoding='utf-8').read().split('\n')

NAVY, RUST, MUTE, SNOW, ICE = '#10243A', '#B93D06', '#47607C', '#EEF3F7', '#A9C4E4'
INK, GREY, RULE, PANEL = '#1F1F1F', '#5F5F5F', '#DDDDDD', '#F4F4F2'


def slug(h):
    return re.sub(r'\s', '-', re.sub(r"[^\w\s-]", '', h.lower()))


def inline(t):
    t = t.replace('&#91;', '[').replace('\\[', '[').replace('\\]', ']').replace('\\$', '$')
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    return t


def table_rows(block):
    """Cells of a markdown table, row by row, without the --- line."""
    rows = [[c.strip() for c in re.split(r'(?<!\\)\|', r.strip())[1:-1]] for r in block if r.strip().startswith('|')]
    return [r for r in rows if not all(set(c) <= set('-: ') for c in r)]


def chart_svg(rows):
    W, H, left, base, h = 680, 212, 20, 170, 108
    band = (W - 2 * left) / len(rows)
    bw = band * 0.56
    peak = max(v for _, v in rows)
    parts = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Sidewalk complaints peak 2 to 3 days after the snow" '
             f'font-family="Barlow, sans-serif" font-size="13">']
    dl = left + band  # deadline: end of the snow day
    parts.append(f'<line x1="{dl:.1f}" x2="{dl:.1f}" y1="22" y2="{base}" stroke="{INK}" stroke-width="1.1" stroke-dasharray="4 4"/>')
    parts.append(f'<text x="{dl + 6:.1f}" y="34" fill="{GREY}" font-size="12.5">Today\'s deadline: the same day, or the next day by about 1 p.m.</text>')
    hot_vals = sorted((v for _, v in rows), reverse=True)[:2]  # the two peak days in rust
    for i, (lab, v) in enumerate(rows):
        x = left + i * band + (band - bw) / 2
        y = base - v / peak * h
        hot = v in hot_vals
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{base - y:.1f}" fill="{RUST if hot else "#CFCFCC"}"/>')
        parts.append(f'<text x="{x + bw / 2:.1f}" y="{y - 7:.1f}" text-anchor="middle" fill="{INK}" font-weight="{600 if hot else 500}">{v:,}</text>')
        parts.append(f'<text x="{x + bw / 2:.1f}" y="{base + 20}" text-anchor="middle" fill="{GREY}">{lab}</text>')
    parts.append(f'<line x1="{left}" x2="{W - left}" y1="{base}" y2="{base}" stroke="{INK}" stroke-width="1"/>')
    parts.append('</svg>')
    return ''.join(parts)


body = []
i = 0
title = date = None
in_text = False      # inside "The proposed text"
open_div = []        # stack of open wrappers


def close_divs():
    while open_div:
        body.append('</div>')
        open_div.pop()


while i < len(lines):
    ln = lines[i]
    s = ln.strip()
    if not s:
        i += 1
        continue
    if s.startswith('Copy of the PTAC Claude Doc'):
        i += 1
        continue
    if s.startswith('# '):
        title = s[2:]
        i += 1
        continue
    if s.startswith('Somerville Pedestrian & Transit Advisory Committee (PTAC) ·'):
        date = s.split('·', 1)[1].strip()
        body.append('<header class="lh"><div class="org">Somerville Pedestrian &amp; Transit Advisory Committee</div>'
                    f'<div class="meta"><span>To: Somerville City Council</span><span>{html.escape(date)}</span></div></header>'
                    f'<h1>{inline(title)}</h1>')
        i += 1
        continue
    # chart block: bold title line + table + source line -> SVG figure
    if s.startswith('**Complaints peak 2 to 3 days after the snow'):
        j = i + 1
        while j < len(lines) and not lines[j].startswith('Source:'):
            j += 1
        source = lines[j][len('Source:'):].strip().replace('; method in research/data-sources.md', '')
        head, vals = table_rows(lines[i + 1:j])[:2]
        rows = list(zip(head, (int(v.replace(',', '')) for v in vals)))
        body.append('<figure class="chart"><figcaption class="ct">Sidewalk complaints peak 2 to 3 days after the snow, long after the deadline</figcaption>'
                    f'<div class="cs">Complaints to 311 after the 16 days with 6+ inches of snow since 2015, each counted once ({sum(v for _, v in rows):,} in all)</div>'
                    f'{chart_svg(rows)}<div class="src">Source: {inline(source)}</div></figure>')
        i = j + 1
        continue
    if s.startswith('## '):
        h = s[3:]
        close_divs()
        in_text = False
        cls = ' class="att"' if h.startswith('Attachment') else ''
        body.append(f'<h2 id="{slug(h)}"{cls}>{inline(h)}</h2>')
        if h == 'The proposed text':
            in_text = True
            # intro paragraph first, then the boxed text
            i += 1
            while not lines[i].strip():
                i += 1
            body.append(f'<p>{inline(lines[i].strip())}</p>')
            body.append('<div class="ord">')
            open_div.append('ord')
        i += 1
        continue
    if s.startswith('### '):
        h = s[4:]
        body.append(f'<h3 id="{slug(h)}">{inline(h)}</h3>')
        i += 1
        continue
    if s.startswith('We would welcome'):
        close_divs()
        in_text = False
        body.append('<div class="closing">')
        open_div.append('closing')
    if s.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            rows.append([c.strip() for c in re.split(r'(?<!\\)\|', lines[i].strip())[1:-1]])
            i += 1
        head, rest = rows[0], [r for r in rows[2:] if any(r)]
        body.append('<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>'
                    + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rest) + '</tbody></table>')
        continue
    if re.match(r'^[-*] ', s):
        items = []
        while i < len(lines) and re.match(r'^[-*] ', lines[i].strip()):
            items.append(lines[i].strip()[2:])
            i += 1
        if all(re.match(r'^\*(Today|Proposed|Why):\*', it) for it in items):
            body.append('<dl class="chg">' + ''.join(
                f'<dt>{m.group(1)}</dt><dd>{inline(m.group(2))}</dd>'
                for m in (re.match(r'^\*(Today|Proposed|Why):\*\s*(.*)$', it) for it in items)) + '</dl></div>')
        else:
            body.append('<ul>' + ''.join(f'<li>{inline(it)}</li>' for it in items) + '</ul>')
            if body[-2:-1] == ['<div class="who">'] or (len(body) > 1 and body[-2].startswith('<div class="who">')):
                body.append('</div>')
        continue
    # paragraphs
    if s == '**Who is affected**':
        body.append('<div class="who"><div class="wh">Who is affected</div>')
        i += 1
        continue
    if re.match(r'^\*\*[^*]+\*\*$', s) and not in_text and i + 2 < len(lines) and lines[i + 2].strip().startswith('- *Today:*'):
        body.append(f'<div class="change"><div class="topic">{inline(s[2:-2])}</div>')
        i += 1
        continue
    if s.startswith('&#91;Roster') or s.startswith('[Roster'):
        body.append(f'<p class="draft">{inline(s)}</p>')
        i += 1
        continue
    if ' · ' in s and s.count(' · ') > 5:
        names = [n.strip() for n in s.split('·')]
        body.append('<ul class="roster">' + ''.join(f'<li>{inline(n)}</li>' for n in names) + '</ul>')
        i += 1
        continue
    if s.startswith('CC:'):
        body.append(f'<p class="cc">{inline(s)}</p>')
        i += 1
        continue
    cls = ''
    m = re.match(r'^(\*\*Sec\. [^*]+\*\*)\s+(.+)$', s)
    if in_text and m:
        body.append(f'<p class="sec">{inline(m.group(1))}</p><p class="note">{inline(m.group(2))}</p>')
        i += 1
        continue
    if in_text and re.match(r'^\*\*Sec\. ', s):
        cls = ' class="sec"'
    elif s in ('Respectfully,',) or s.startswith('The Somerville Pedestrian and Transit Advisory Committee (PTAC)'):
        cls = ' class="sign"'
    body.append(f'<p{cls}>{inline(s)}</p>')
    i += 1
close_divs()

css = f"""
@page {{ size: letter; margin: 0.85in 0.9in 0.8in; }}
* {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ font-family: 'Barlow', 'Helvetica Neue', Arial, sans-serif; font-size: 10.6pt; line-height: 1.5; color: {INK}; margin: 0; }}
a {{ color: {RUST}; text-decoration: none; }}
.lh {{ border-bottom: 2px solid {RUST}; padding-bottom: 8px; margin-bottom: 20px; }}
.lh .org {{ font: 700 13pt/1.1 'Barlow Condensed', sans-serif; text-transform: uppercase; letter-spacing: .8px; color: {NAVY}; }}
.lh .meta {{ display: flex; justify-content: space-between; font-size: 9.5pt; color: {GREY}; margin-top: 4px; }}
h1 {{ font: 600 19pt/1.2 'Barlow', sans-serif; margin: 0 0 16px; color: {INK}; }}
h2 {{ font: 600 14pt/1.25 'Barlow', sans-serif; margin: 22px 0 8px; color: {INK}; break-after: avoid; }}
h2.att {{ break-before: page; margin-top: 0; font-size: 16pt; border-bottom: 1.5px solid {RUST}; padding-bottom: 4px; }}
h3 {{ font: 600 11.5pt/1.3 'Barlow', sans-serif; margin: 18px 0 6px; color: {INK}; break-after: avoid; }}
p {{ margin: 0 0 8px; orphans: 3; widows: 3; }}
strong {{ font-weight: 600; }}
ul {{ margin: 0 0 10px; padding-left: 18px; }}
li {{ margin-bottom: 4px; }}
table {{ width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-size: 9.4pt; line-height: 1.4; break-inside: auto; }}
th {{ text-align: left; font: 600 8.6pt 'Barlow', sans-serif; text-transform: uppercase; letter-spacing: .5px; color: {GREY}; border-bottom: 1px solid {INK}; padding: 4px 6px; }}
td {{ border-bottom: 1px solid {RULE}; padding: 5px 6px; vertical-align: top; }}
tr {{ break-inside: avoid; }}
figure.chart {{ margin: 6px 0 14px; break-inside: avoid; }}
figure.chart svg {{ width: 100%; height: auto; display: block; }}
.ct {{ font: 600 11pt 'Barlow', sans-serif; }}
.cs, .src {{ font-size: 8.8pt; color: {GREY}; }}
.src {{ margin-top: 2px; }}
.ord {{ background: {PANEL}; border-left: 3px solid {INK}; padding: 12px 16px 6px; margin: 8px 0 16px; font-size: 10pt; }}
.ord p {{ margin-bottom: 6px; }}
.ord p.sec {{ font: 600 11pt 'Barlow', sans-serif; margin: 14px 0 6px; padding-top: 8px; border-top: 1px solid {RULE}; break-after: avoid; }}
p.note {{ font-style: italic; color: {GREY}; }}
.closing {{ break-inside: avoid; margin-top: 14px; }}
.ord p.sec:first-child {{ border-top: 0; padding-top: 0; margin-top: 0; }}
p.sign {{ margin-bottom: 4px; }}
p.draft {{ background: #FFF3CD; border: 1px dashed #C9A227; padding: 4px 8px; font-size: 9pt; margin-top: 10px; }}
ul.roster {{ list-style: none; padding: 0; columns: 3; column-gap: 16px; font-size: 9.3pt; margin: 6px 0 12px; }}
ul.roster li {{ margin: 0 0 2px; break-inside: avoid; }}
p.cc {{ font-size: 9.3pt; color: {GREY}; }}
.change {{ margin: 10px 0 12px; break-inside: avoid; }}
.change .topic {{ font: 600 10.8pt 'Barlow', sans-serif; margin-bottom: 3px; }}
dl.chg {{ display: grid; grid-template-columns: 70px 1fr; gap: 3px 10px; margin: 0; }}
dl.chg dt {{ font: 600 8.4pt 'Barlow', sans-serif; text-transform: uppercase; letter-spacing: .5px; color: {GREY}; padding-top: 2px; }}
dl.chg dd {{ margin: 0; }}
dl.chg dt:nth-of-type(2) {{ color: {RUST}; }}
.who {{ background: {PANEL}; border-radius: 3px; padding: 8px 12px 2px; margin: 6px 0 14px; font-size: 9.6pt; break-inside: avoid; }}
.who .wh {{ font: 600 8.4pt 'Barlow', sans-serif; text-transform: uppercase; letter-spacing: .5px; color: {GREY}; margin-bottom: 4px; }}
.who ul {{ margin-bottom: 6px; }}
"""

doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{html.escape(title or 'PTAC letter')}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=Barlow:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap">
<style>{css}</style></head><body>{''.join(body)}</body></html>"""
os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
open(out, 'w', encoding='utf-8').write(doc)
print('wrote', out)
