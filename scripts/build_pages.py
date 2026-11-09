#!/usr/bin/env python3
"""Write one fixed page per storm (docs/snow/storms/<id>.html) and an index (docs/snow/storms/index.html).

Everything a page shows is prepared here and written into the page: title, summary, "at a glance" facts,
links to the previous and next storm, the storm cards, and the data (as JSON in the page). The page's script
(docs/snow/js/storm.js) only draws and animates. Run by `npm run data` after collecting, or alone with `npm run pages`.
Template: scripts/storm_page.html.
"""
import csv, hashlib, html, io, json, os
from collections import defaultdict
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'docs', 'snow', 'data')
OUT = os.path.join(ROOT, 'docs', 'snow', 'storms')
SITE = 'https://somerwalks.org/snow/'


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


def holidays(y):
    """Holidays that empty the T and the streets on their own (Massachusetts), so a dip isn't read as the storm."""
    def nth(month, weekday, n):  # n-th weekday (Mon=0) of a month
        d = date(y, month, 1)
        return d + timedelta(days=(weekday - d.weekday()) % 7 + 7 * (n - 1))
    return {date(y, 1, 1): 'New Year', nth(1, 0, 3): 'MLK Day', nth(2, 0, 3): "Presidents' Day", nth(4, 0, 3): "Patriots' Day",
            nth(11, 3, 4): 'Thanksgiving', date(y, 12, 25): 'Christmas'}


def window_holidays(S):
    a, b = datetime.fromisoformat(S['from']).date(), datetime.fromisoformat(S['to']).date()
    return {d.isoformat(): name for y in {a.year, b.year} for d, name in holidays(y).items() if a <= d <= b}


def daily_drop(series, t0, after, until=None, skip=()):
    """The day (from `after` to `until`, holidays in `skip` left out) where a series fell furthest below its normal:
    (day, percent change)."""
    if not series:
        return None
    now, base = series['now'], series['base']
    days = defaultdict(lambda: [0.0, 0.0])
    for k, (a, b) in enumerate(zip(now, base)):
        t = t0 + timedelta(hours=k)
        if t.date() < after.date() or (until and t.date() > until.date()) or t.date().isoformat() in skip or b is None:
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
        if tows: summary.append(f'{tows:,} snow emergency tow{"s" if tows != 1 else ""}')
    for key, label in (('tEntries', 'T entries at Somerville stations'), ('bikes', 'Bluebikes trips from Somerville stations')):
        # from the first snow to 3 days after it stops: later dips are more likely weekend shutdowns than the storm
        dd = daily_drop(x.get(key), t0, start, stop + timedelta(days=3), window_holidays(S))
        if dd and dd[1] <= -0.15:
            items.append(f'<li><b>{pct(dd[1])}</b> {label} on {esc(day(datetime.combine(dd[0], datetime.min.time())))}, compared with a normal week</li>')
            if key == 'tEntries': summary.append(f'T entries {pct(dd[1])} on {dd[0]:%A}')
    al = x.get('alerts')
    if al:
        items.append(f'<li><b>{len(al)}</b> MBTA alerts on Somerville routes and stations</li>')
    items.append(f'<li><b>{sidewalk}</b> sidewalk reports to 311 after the snow started</li>')
    summary.append(f'{sidewalk:,} sidewalk report{"s" if sidewalk != 1 else ""} to 311')
    return '\n'.join(items), summary


def lede(S):
    start, stop = datetime.fromisoformat(S['snowStart']), datetime.fromisoformat(S['snowStop'])
    e = S.get('emergency')
    missing = (' The City\'s snow emergency notices for this storm aren\'t online, so parking messages are left out.' if not e
               else ' Only the City\'s notice about the end of the emergency is online.' if not e.get('start')
               else ' The City\'s notice about the end of the emergency isn\'t online.' if not e.get('end') else '')
    som = (S.get('extra') or {}).get('snowSomerville')
    here = f' ({som["total"]} in Somerville, from volunteer observers{", partial report" if som["partial"] else ""})' if som else ''
    n = len(S.get('snowfalls') or [1])
    falls = f'{n} snowfalls, ' if n > 1 else ''
    lasted = f' Sidewalk reports kept coming for {S["lasted"]} days after the {"first " if n > 1 else ""}snow stopped.' if S.get('lasted', 0) > 1 else ''
    if (stop - start).days >= 2:  # a period over several days: name the dates
        when = lambda t: f'{t:%a}, {t:%b} {t.day}, ' + day_tm(t).split(' ', 1)[1]
        span_txt = f'Snow from {when(start)} to {when(stop)}.'
    else:
        span_txt = f'Snow from {day_tm(start)} to {day_tm(stop)}.'
    return (f'{falls}{S["snowTotal"]} inches at Logan{here}. {span_txt}{lasted}{missing} Press play, or drag the line.').replace('..', '.')


def winter_of(day):
    return int(day[:4]) - (int(day[5:7]) < 7)


def _peak(st):
    """Day of the most sidewalk reports, counted from the last day of snow (only for a single snowfall)."""
    v = [d[2].get('sidewalk', 0) for d in st['days']]
    off = (date.fromisoformat(st['end']) - date.fromisoformat(st['days'][0][0])).days
    return v.index(max(1, *v)) - off if max(v, default=0) else -99


def span(st):
    """'Mar 3, 2026' for one snowfall, 'Jan 25 – Feb 10, 2026' for a period of several."""
    if len(st.get('snowfalls', [])) <= 1:
        return short(st['end'])
    a, b = date.fromisoformat(st['start']), date.fromisoformat(st['end'])
    left = f'{a:%b} {a.day}' + (f', {a.year}' if a.year != b.year else '')
    return f'{left} – {short(st["end"])}' if a.month != b.month or a.year != b.year else f'{a:%b} {a.day}–{b.day}, {b.year}'


def cards(storms, current=None, prefix=''):
    """Storm cards grouped by winter. On the index: every winter (one without a storm says so, so years never
    silently go missing). On a storm page (current): only that storm's winter."""
    out = []
    W_ = load('winters.json'); totals = dict(W_['snow'])  # winter starting year -> inches at Logan
    first_w, last_w = winter_of(storms[0]['end']), winter_of(storms[-1]['end'])
    if current:
        first_w = last_w = winter_of(current)
    by_w = defaultdict(list)
    for st in storms:
        by_w[winter_of(st['end'])].append(st)
    seq = []
    for w in range(first_w, last_w + 1):
        tot = f' · {totals[w]:g} in all winter' if w in totals else ''
        seq.append(f'<h3 class="winter">Winter {w}–{(w + 1) % 100:02d}<small>{tot}</small></h3>')
        if not by_w[w]:
            seq.append('<div class="mini gap"><small>No storm with 3 inches or more at Logan.</small></div>')
        seq.extend(by_w[w])
    for st in seq:
        if isinstance(st, str):
            out.append(st)
            continue
        # every day of the period's window: sidewalk reports (orange), snow days (navy), until reports died down
        v = [d[2].get('sidewalk', 0) for d in st['days']]
        mx = max(1, *v)
        snow_days = {f0 for f in st.get('snowfalls', [{'start': st['start'], 'end': st['end']}])
                     for f0 in ((date.fromisoformat(f['start']) + timedelta(k)).isoformat() for k in range((date.fromisoformat(f['end']) - date.fromisoformat(f['start'])).days + 1))}
        w = 200 / len(v)
        bars = ''.join(f'<rect x="{k * w + w * 0.1:.1f}" y="{60 - max(n / mx * 56, 1.5 if day in snow_days else 0):.1f}" width="{w * 0.8:.1f}" height="{max(n / mx * 56, 1.5 if day in snow_days else 0):.1f}" rx="1.5" fill="{"#10243A" if day in snow_days else "#FF8A3D"}"/>'
                       for k, ((day, _, _), n) in enumerate(zip(st['days'], v)))
        n_falls = len(st.get('snowfalls', [1]))
        lasted = st.get('lasted')
        txt = (f'{st["snow"]} in' + (f' · {n_falls} snowfalls' if n_falls > 1 else '') + ' · ' +
               (f'reports for {lasted} day{"s" if lasted != 1 else ""}' if max(v) and lasted else 'no sidewalk reports' if not max(v) else 'reports for a day'))
        sel = st['id'] == current
        cur = ' aria-current="page"' if sel else ''
        out.append(f'<a class="mini{" sel" if sel else ""}" href="{prefix}{st["id"]}.html"{cur}>'
                   f'<h4>{span(st)}</h4><small>{txt}</small>'
                   f'<svg viewBox="0 0 200 64" aria-hidden="true">{bars}<path d="M0 61 H200" stroke="#C9D6E3"/></svg>'
                   f'<span class="go">{"Showing above" if sel else "Replay this storm →"}</span></a>')
    # counted on the periods picked by snowfall only: the ones found through 311 were picked by their reports
    snowy = [st for st in storms if st.get('kind', 'snow') == 'snow']
    lasted = sorted(st['lasted'] for st in snowy)
    med = lasted[len(lasted) // 2]
    week, two = sum(1 for x in lasted if x > 7), sum(1 for x in lasted if x > 14)
    single = [st for st in snowy if len(st.get('snowfalls', [1])) == 1]
    peaks13 = sum(1 for st in single if 1 <= _peak(st) <= 3)
    lede_ = (f'After the snow stops, sidewalk reports keep coming for {med} days in a typical storm. They lasted more than a week in '
             f'{week} of {len(snowy)} snow periods, and more than two weeks in {two}, when more snow fell before the sidewalks were clear. '
             f'Where it snowed once, reports peaked 1 to 3 days after the snow in {peaks13} of {len(single)} storms.')
    return '\n'.join(out), lede_


def hourly_csv(S):
    """docs/snow/data/csv/<id>.csv: one row per hour of the storm's window, every hourly number the page draws, so the
    charts can be checked in a spreadsheet. Empty cells: the source doesn't cover this storm (never a zero)."""
    t0 = datetime.fromisoformat(S['from']); n = len(S['hours']); x = S.get('extra') or {}
    pick = lambda *path: (lambda o: o if isinstance(o, list) else None)(_dig(x, path))
    def per_hour(pairs):  # [[hour index, count], ...] -> list
        if pairs is None:
            return None
        v = [0] * n
        for i, c in pairs:
            if 0 <= i < n: v[i] += c
        return v
    def per_hour_at(rows):  # [[hour index, value, ...]] -> the value at its hour, empty elsewhere
        if rows is None:
            return None
        v = [None] * n
        for r in rows:
            if 0 <= r[0] < n: v[r[0]] = r[1]
        return v
    snow_start = datetime.fromisoformat(S['snowStart'])
    temps = [h[1] for h in S['hours']]
    refreeze = []
    for k, tv in enumerate(temps):  # same rule as the page: at or below 32°F within 12 h after 34°F or warmer, from the first snow
        ok = tv is not None and tv <= 32 and t0 + timedelta(hours=k) >= snow_start and any(
            temps[j] is not None and temps[j] >= 34 for j in range(max(0, k - 12), k))
        refreeze.append(int(ok))
    pol = x.get('police')
    cols = [('hour_start', [(t0 + timedelta(hours=k)).isoformat(timespec='minutes') for k in range(n)]),
            ('snow_logan_0to3', [h[0] for h in S['hours']]), ('temp_f', temps), ('visibility_mi', [h[2] for h in S['hours']]),
            ('wind_kn', [h[3] for h in S['hours']]), ('freezing_rain_or_sleet_0to3', [h[4] if len(h) > 4 else None for h in S['hours']])]
    for g_i, g in enumerate(S['groups']):
        cols.append((f'311_{g}', [(S['requests'].get(str(k)) or [0] * len(S['groups']))[g_i] for k in range(n)]))
    cols += [('311_salting', per_hour(S.get('salting'))), ('refreezing', refreeze),
             ('311_parking', per_hour(_dig(x, ('calls311', 'parking')))), ('311_trash', per_hour(_dig(x, ('calls311', 'trash')))),
             ('police_tows_per_shift', per_hour(pol['tows']) if pol else None), ('police_disabled_per_shift', per_hour(pol['disabled']) if pol else None),
             ('t_entries', pick('tEntries', 'now')), ('t_entries_normal', pick('tEntries', 'base')),
             ('bus_trips', pick('buses', 'trips', 'now')), ('bus_trips_normal', pick('buses', 'trips', 'base')),
             ('bus_minutes_late', pick('buses', 'late', 'now')), ('bus_minutes_late_normal', pick('buses', 'late', 'base')),
             ('bus_pct_slower', pick('buses', 'speed', 'slow')),
             ('subway_pct_slower', pick('subway', 'slow')), ('subway_trains', pick('subway', 'trains', 'now')), ('subway_trains_normal', pick('subway', 'trains', 'base')),
             ('bluebikes_trips', pick('bikes', 'now')), ('bluebikes_trips_normal', pick('bikes', 'base')),
             ('fire_medical_calls', pick('fire', 'ems', 'now')), ('fire_medical_calls_normal', pick('fire', 'ems', 'base')),
             ('snow_on_ground_in', per_hour_at(x.get('snowDepth')))]
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow([c for c, _ in cols])
    for k in range(n):
        w.writerow(['' if v is None or v[k] is None else v[k] for _, v in cols])
    return out.getvalue()


def _dig(o, path):
    for p_ in path:
        if not isinstance(o, dict) or o.get(p_) is None:
            return None
        o = o[p_]
    return o


def main():
    storms = load('storms.json')['storms']
    W = load('wards.json'); wards = W['wards']; survey = W.get('survey')
    bus = load('bus-stops.json')
    ids = [st['id'] for st in storms]
    with open(os.path.join(ROOT, 'scripts', 'storm_page.html')) as f:
        tpl = f.read()
    # Cache-busting: browsers may keep old copies of these files for a while; a content hash in the URL
    # makes a changed file load fresh, so a new page never runs with an old script.
    for rel in ('js/storm.js', 'js/deadline.js', 'css/storm.css', 'css/style.css'):
        with open(os.path.join(ROOT, 'docs', 'snow', rel), 'rb') as f:
            v = hashlib.sha1(f.read()).hexdigest()[:8]
        tpl = tpl.replace(f'../{rel}"', f'../{rel}?v={v}"')
    os.makedirs(OUT, exist_ok=True)
    for k, sid in enumerate(ids):
        S = load(f'storm-{sid}.json')
        _, summary = facts(S)
        nav = ''.join([  # neighbors by their date range ("Jan 25 – Feb 10, 2026"), not just their last day
            f'<a href="{ids[k - 1]}.html">← {span(storms[k - 1])}</a>' if k > 0 else '<span></span>',
            '<a href="./">All storms</a>',
            f'<a href="{ids[k + 1]}.html">{span(storms[k + 1])} →</a>' if k < len(ids) - 1 else '<span></span>',
        ])
        cards_html, all_lede = cards(storms, sid)
        data = json.dumps({'storm': S, 'holidays': window_holidays(S), 'wards': wards, 'survey': survey, 'bus': {'season': bus['season'], 'stops': [{k: st[k] for k in ('name', 'lat', 'lon', 'riders', 'routes')} for st in bus['stops']], 'routes': bus.get('routes', {}), 'subway': bus.get('subway', {})}, 'ids': ids},
                          separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
        desc = f'Replay the {S["title"]} storm in Somerville hour by hour: ' + ', '.join(summary) + '. By the Somerville PTAC.'
        page = (tpl.replace('%%TITLE%%', esc(S['title'])).replace('%%DESC%%', esc(desc)).replace('%%URL%%', f'{SITE}storms/{sid}.html')
                .replace('%%LEDE%%', esc(lede(S))).replace('%%NAV%%', nav).replace('%%ID%%', sid)
                .replace('%%CARDS%%', cards_html).replace('%%ALL_LEDE%%', esc(all_lede)).replace('%%DATA%%', data))
        with open(os.path.join(OUT, f'{sid}.html'), 'w') as f:
            f.write(page)
        os.makedirs(os.path.join(ROOT, 'docs', 'snow', 'data', 'csv'), exist_ok=True)
        with open(os.path.join(ROOT, 'docs', 'snow', 'data', 'csv', f'{sid}.csv'), 'w', newline='') as f:
            f.write(hourly_csv(S))
    # a snowfall that is now part of a longer period keeps its address: a small page that forwards to the period
    alias = {a: st['id'] for st in storms for a in st.get('aliases', [])}
    for a, to in alias.items():
        with open(os.path.join(OUT, f'{a}.html'), 'w') as f:
            f.write(f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Storm replay</title>'
                    f'<link rel="canonical" href="{SITE}storms/{to}.html"><meta http-equiv="refresh" content="0; url={to}.html">'
                    f'<script>location.replace("{to}.html" + location.hash)</script></head><body>'
                    f'<p>This snowfall is part of a longer snow period: <a href="{to}.html">see the replay</a>.</p></body></html>\n')
    for f in os.listdir(OUT):  # pages for ids that no longer exist
        if f.endswith('.html') and f != 'index.html' and f[:-5] not in ids and f[:-5] not in alias:
            os.remove(os.path.join(OUT, f))
    # index: every storm, newest first in the lede link
    cards_html, all_lede = cards(storms)
    latest = ids[-1]
    idx = INDEX
    for rel in ('css/storm.css', 'css/style.css'):
        with open(os.path.join(ROOT, 'docs', 'snow', rel), 'rb') as f:
            idx = idx.replace(f'../{rel}"', f'../{rel}?v={hashlib.sha1(f.read()).hexdigest()[:8]}"')
    idx = idx.replace('%%CARDS%%', cards_html).replace('%%ALL_LEDE%%', esc(all_lede)).replace('%%LATEST%%', latest).replace('%%LATEST_NAME%%', esc(load(f'storm-{latest}.json')['title']))
    with open(os.path.join(OUT, 'index.html'), 'w') as f:
        f.write(idx)
    print(f'  wrote docs/snow/storms/ ({len(ids)} storm pages and index.html)')


INDEX = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Every storm since 2016 · SomerWalks</title>
<meta name="description" content="Replay every Somerville snowstorm of 3 inches or more since 2016, hour by hour: the snow, the City's snow emergency, the shoveling deadline, 311 reports, the T and Bluebikes. By the Somerville PTAC.">
<meta property="og:title" content="Every storm since 2016 · SomerWalks">
<meta property="og:description" content="Replay every Somerville snowstorm of 3 inches or more since 2016, hour by hour.">
<meta name="theme-color" content="#10243A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600;700&display=swap">
<link rel="stylesheet" href="../css/style.css">
<link rel="stylesheet" href="../css/storm.css">
</head>
<body>
<header class="bar"><div class="wrap"><a class="brand" href="../../">Somer<span>Walks</span></a><nav class="nav"><a href="../">Snow guide</a></nav></div></header>
<section class="replay-all" style="background:var(--paper)">
<div class="wrap">
<div class="eyebrow">Storm replays</div>
<h2 style="margin-top:14px">Every storm<br>since 2016</h2>
<p class="lede" style="margin-top:18px">%%ALL_LEDE%% Pick a storm to replay it hour by hour: the snow, the City's snow emergency, the shoveling deadline, 311, the T and Bluebikes.</p>
<p style="margin-top:20px"><a class="btn" href="%%LATEST%%.html">Replay the latest: %%LATEST_NAME%%</a></p>
<div class="multiples">
%%CARDS%%
</div>
<p class="cite" style="margin-top:20px">Sidewalk reports per day (orange) and snow days (navy), until reports died down. Snow that falls before then joins the same storm. Every snow of 3 inches or more at Logan, plus smaller ones that drew many reports. <a href="https://github.com/vitorpamplona/somerwalks/blob/main/research/data-sources.md">Method notes</a>.</p>
</div>
</section>
<footer><div class="wrap"><p>By the Somerville PTAC. Not an official City page. The City's rules apply: <a href="https://www.somervillema.gov/snow">somervillema.gov/snow</a>. <a href="https://github.com/vitorpamplona/somerwalks">Source code and data</a>.</p></div></footer>
</body>
</html>
'''

if __name__ == '__main__':
    main()
