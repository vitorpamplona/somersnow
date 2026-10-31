#!/usr/bin/env python3
"""Write one fixed page per storm (docs/storms/<id>.html) and an index (docs/storms/index.html).

Everything a page shows is prepared here and written into the page: title, summary, "at a glance" facts,
links to the previous and next storm, the storm cards, and the data (as JSON in the page). The page's script
(docs/js/storm.js) only draws and animates. Run by `npm run data` after collecting, or alone with `npm run pages`.
Template: scripts/storm_page.html.
"""
import hashlib, html, json, os
from collections import defaultdict
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'docs', 'data')
OUT = os.path.join(ROOT, 'docs', 'storms')
SITE = 'https://vitorpamplona.com/somersnow/'


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def tm(t):
    h = t.hour % 12 or 12
    s = f'{h}' if t.minute == 0 else f'{h}:{t.minute:02d}'
    return s + (' a.m.' if t.hour < 12 else ' p.m.')


def day_tm(t):
    return f'{t:%a} {tm(t)}'


def day(t):
    return f'{t:%a}, {t:%b} {t.day}'


def short(sid):
    d = datetime.fromisoformat(sid)
    return f'{d:%b} {d.day}, {d.year}'


def pct(r):
    return f'{"+" if r > 0 else "−" if r < 0 else ""}{abs(round(r * 100))}%'


def esc(s):
    return html.escape(s, quote=True)


def daily_drop(series, t0, after):
    """The day (from `after` on) where a series fell furthest below its normal: (day, percent change)."""
    if not series:
        return None
    now, base = series['now'], series['base']
    days = defaultdict(lambda: [0.0, 0.0])
    for k, (a, b) in enumerate(zip(now, base)):
        t = t0 + timedelta(hours=k)
        if t.date() < after.date() or b is None:
            continue
        days[t.date()][0] += a or 0
        days[t.date()][1] += b
    best = None
    for d, (a, b) in days.items():
        if b >= 20:  # ignore days with almost no normal activity
            r = a / b - 1
            if best is None or r < best[1]:
                best = (d, r)
    return best


def facts(S):
    """The storm's key facts, from the prepared data, for the page description (link previews).
    Returns (html list items, plain-text summary bits); only the summary is used now."""
    t0 = datetime.fromisoformat(S['from'])
    start, stop = datetime.fromisoformat(S['snowStart']), datetime.fromisoformat(S['snowStop'])
    x = S.get('extra') or {}
    k = S['groups'].index('sidewalk')
    base = int((start - t0).total_seconds() // 3600)
    sidewalk = sum(v[k] for i, v in S['requests'].items() if int(i) >= base)
    items, summary = [], []
    items.append(f'<li><b>{S["snowTotal"]} in</b> of snow at Logan, {esc(day_tm(start))} to {esc(day_tm(stop))}</li>')
    som = x.get('snowSomerville')
    summary.append(f'{S["snowTotal"]} inches of snow at Logan' + (f' ({som["total"]} in Somerville)' if som and not som['partial'] else ''))
    # the most serious NWS product that overlapped the snow (several segments of it are merged)
    RANK = ['BZ.W', 'WS.W', 'IS.W', 'LE.W', 'WC.W', 'WW.Y', 'WS.A', 'BZ.A']
    ws = [w for w in x.get('warnings') or [] if w['code'] in RANK and datetime.fromisoformat(w['to']) > start and datetime.fromisoformat(w['from']) < stop]
    if ws:
        top = min(ws, key=lambda w: RANK.index(w['code']))
        same = [w for w in ws if w['code'] == top['code']]
        a_, b_ = min(datetime.fromisoformat(w['from']) for w in same), max(datetime.fromisoformat(w['to']) for w in same)
        items.append(f'<li><b>{esc(top["name"])}</b> from the National Weather Service, {esc(day_tm(a_))} to {esc(day_tm(b_))}</li>')
        summary.append(top['name'])
    if S.get('emergency', {}).get('start'):
        items.append(f'<li><b>Snow emergency</b> from {esc(day_tm(datetime.fromisoformat(S["emergency"]["start"])))}' +
                     (f' to {esc(day_tm(datetime.fromisoformat(S["emergency"]["end"])))}' if S['emergency'].get('end') else '') + '</li>')
    elif S.get('emergency', {}).get('end'):
        items.append(f'<li><b>Snow emergency</b> until {esc(day_tm(datetime.fromisoformat(S["emergency"]["end"])))}</li>')
    pol = x.get('police')
    if pol is not None:
        tows = sum(n for _, n in pol['tows'])
        items.append(f'<li><b>{tows}</b> snow emergency tows logged by police</li>')
        if tows: summary.append(f'{tows} snow emergency tows')
    for key, label in (('tEntries', 'T entries at Somerville stations'), ('bikes', 'Bluebikes trips from Somerville stations')):
        dd = daily_drop(x.get(key), t0, start)
        if dd and dd[1] <= -0.15:
            items.append(f'<li><b>{pct(dd[1])}</b> {label} on {esc(day(datetime.combine(dd[0], datetime.min.time())))}, compared with a normal week</li>')
            if key == 'tEntries': summary.append(f'T entries {pct(dd[1])} on {dd[0]:%A}')
    al = x.get('alerts')
    if al:
        items.append(f'<li><b>{len(al)}</b> MBTA alerts on Somerville routes and stations</li>')
    items.append(f'<li><b>{sidewalk}</b> sidewalk reports to 311 after the snow started</li>')
    summary.append(f'{sidewalk} sidewalk reports to 311')
    return '\n'.join(items), summary


def lede(S):
    start, stop = datetime.fromisoformat(S['snowStart']), datetime.fromisoformat(S['snowStop'])
    e = S.get('emergency')
    missing = (' The City\'s snow emergency notices for this storm aren\'t online, so parking messages are left out.' if not e
               else ' Only the City\'s notice about the end of the emergency is online.' if not e.get('start')
               else ' The City\'s notice about the end of the emergency isn\'t online.' if not e.get('end') else '')
    som = (S.get('extra') or {}).get('snowSomerville')
    here = f' ({som["total"]} in Somerville, from volunteer observers{", partial report" if som["partial"] else ""})' if som else ''
    return (f'{S["snowTotal"]} inches at Logan{here}. Snow from {day_tm(start)} to {day_tm(stop)}.{missing} Press play, or drag the line.').replace('..', '.')


def cards(storms, current=None, prefix=''):
    out, peaks13 = [], 0
    for st in storms:
        v = [d[2].get('sidewalk', 0) for d in st['days']]
        mx = max(1, *v)
        pk = v.index(mx) - 2
        if 1 <= pk <= 3: peaks13 += 1
        bars = ''.join(f'<rect x="{k * 20 + 2}" y="{60 - n / mx * 56:.1f}" width="16" height="{n / mx * 56:.1f}" rx="2" fill="{"#10243A" if k == 2 else "#FF8A3D"}"/>' for k, n in enumerate(v))
        sel = st['end'] == current
        cur = ' aria-current="page"' if sel else ''
        out.append(f'<a class="mini{" sel" if sel else ""}" href="{prefix}{st["end"]}.html"{cur}>'
                   f'<h4>{short(st["end"])}</h4><small>{st["snow"]} in · peak {mx} on day {"+" if pk >= 0 else ""}{pk}</small>'
                   f'<svg viewBox="0 0 200 74" aria-hidden="true">{bars}<path d="M0 61 H200" stroke="#C9D6E3"/><text x="51" y="73" text-anchor="middle" font-size="10" fill="#47607C">LAST SNOW</text></svg>'
                   f'<span class="go">{"Showing above" if sel else "Replay this storm →"}</span></a>')
    lede_ = f'In {peaks13} of {len(storms)} big storms, sidewalk reports peaked 1 to 3 days after the last day of snow.'
    return '\n'.join(out), lede_


def main():
    storms = load('storms.json')['storms']
    wards = load('wards.json')['wards']
    bus = load('bus-stops.json')
    ids = [st['end'] for st in storms]
    with open(os.path.join(ROOT, 'scripts', 'storm_page.html')) as f:
        tpl = f.read()
    # Cache-busting: browsers may keep old copies of these files for a while; a content hash in the URL
    # makes a changed file load fresh, so a new page never runs with an old script.
    for rel in ('js/storm.js', 'js/deadline.js', 'css/storm.css', 'css/style.css'):
        with open(os.path.join(ROOT, 'docs', rel), 'rb') as f:
            v = hashlib.sha1(f.read()).hexdigest()[:8]
        tpl = tpl.replace(f'../{rel}"', f'../{rel}?v={v}"')
    os.makedirs(OUT, exist_ok=True)
    for k, sid in enumerate(ids):
        S = load(f'storm-{sid}.json')
        _, summary = facts(S)
        nav = ''.join([
            f'<a href="{ids[k - 1]}.html">← {short(ids[k - 1])}</a>' if k > 0 else '<span></span>',
            '<a href="./">All storms</a>',
            f'<a href="{ids[k + 1]}.html">{short(ids[k + 1])} →</a>' if k < len(ids) - 1 else '<span></span>',
        ])
        cards_html, all_lede = cards(storms, sid)
        data = json.dumps({'storm': S, 'wards': wards, 'bus': {'season': bus['season'], 'stops': bus['stops'][:19]}, 'ids': ids},
                          separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
        desc = f'Replay the {S["title"]} storm in Somerville hour by hour: ' + ', '.join(summary) + '. By the Somerville PTAC.'
        page = (tpl.replace('%%TITLE%%', esc(S['title'])).replace('%%DESC%%', esc(desc)).replace('%%URL%%', f'{SITE}storms/{sid}.html')
                .replace('%%LEDE%%', esc(lede(S))).replace('%%NAV%%', nav)
                .replace('%%CARDS%%', cards_html).replace('%%ALL_LEDE%%', esc(all_lede)).replace('%%DATA%%', data))
        with open(os.path.join(OUT, f'{sid}.html'), 'w') as f:
            f.write(page)
    # index: every storm, newest first in the lede link
    cards_html, all_lede = cards(storms)
    latest = ids[-1]
    idx = INDEX
    for rel in ('css/storm.css', 'css/style.css'):
        with open(os.path.join(ROOT, 'docs', rel), 'rb') as f:
            idx = idx.replace(f'../{rel}"', f'../{rel}?v={hashlib.sha1(f.read()).hexdigest()[:8]}"')
    idx = idx.replace('%%CARDS%%', cards_html).replace('%%ALL_LEDE%%', esc(all_lede)).replace('%%LATEST%%', latest).replace('%%LATEST_NAME%%', esc(load(f'storm-{latest}.json')['title']))
    with open(os.path.join(OUT, 'index.html'), 'w') as f:
        f.write(idx)
    print(f'  wrote docs/storms/ ({len(ids)} storm pages and index.html)')


INDEX = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Every big storm since 2016 · Somerville Snow Guide</title>
<meta name="description" content="Replay every big Somerville snowstorm since 2016, hour by hour: the snow, the City's snow emergency, the shoveling deadline, 311 reports, the T and Bluebikes. By the Somerville PTAC.">
<meta property="og:title" content="Every big storm since 2016 · Somerville Snow Guide">
<meta property="og:description" content="Replay every big Somerville snowstorm since 2016, hour by hour.">
<meta name="theme-color" content="#10243A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../css/style.css">
<link rel="stylesheet" href="../css/storm.css">
</head>
<body>
<header class="bar"><div class="wrap"><a class="brand" href="../">Somerville <span>Snow</span></a><nav class="nav"><a href="../">Back to the guide</a></nav></div></header>
<section class="replay-all" style="background:var(--paper)">
<div class="wrap">
<div class="eyebrow">Storm replays</div>
<h2 style="margin-top:14px">Every big storm<br>since 2016</h2>
<p class="lede" style="margin-top:18px">%%ALL_LEDE%% Pick a storm to replay it hour by hour: the snow, the City's snow emergency, the shoveling deadline, 311, the T and Bluebikes.</p>
<p style="margin-top:20px"><a class="btn" href="%%LATEST%%.html">Replay the latest: %%LATEST_NAME%%</a></p>
<div class="multiples">
%%CARDS%%
</div>
<p class="cite" style="margin-top:20px">Sidewalk reports to 311 per day, from 2 days before to 7 days after the last day of snow (marked). Storms with 6 inches or more in a day at Logan.</p>
</div>
</section>
<footer><div class="wrap"><p>By the Somerville PTAC. Not an official City page. The City's rules apply: <a href="https://www.somervillema.gov/snow">somervillema.gov/snow</a>.</p></div></footer>
</body>
</html>
'''

if __name__ == '__main__':
    main()
