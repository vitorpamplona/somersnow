#!/usr/bin/env python3
"""Which order should the City clear its bus stops in after a storm?

Compares two ways of sending bobcat crews to Somerville's bus stops:

  * route by route: each crew works through whole bus routes, stop by stop in the
    order the bus runs (a stand-in for today's practice; the City's own 4 clearing
    routes are not published);
  * ridership first: each crew, when it finishes a stretch, takes the stretch of
    street that clears the most riders' stops per minute, counting the time to get
    there: a short drive if the stretch starts close by, or 30 minutes to load the
    bobcat on a trailer and move it if it doesn't.

Inputs (copied into data/ by this script so the folder is self-contained):
  ../../docs/data/bus-stops.json  MBTA stops in Somerville, Fall weekday boardings, routes
  ../../docs/data/wards.json      ward outlines, for the map

Outputs (output/):
  plan.csv     every stop, in the order each plan clears it, with times
  summary.md   the headline numbers
  map.html     the illustrated explainer (open it in a browser); also copied to
               docs/bus-stops.html, the public page

Python standard library only:  python3 analysis/bus-stop-clearing/build.py
"""
import csv, json, math, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
DATA, OUT = os.path.join(HERE, 'data'), os.path.join(HERE, 'output')

# ---------- assumptions (change them here; every output is rebuilt from them) ----------
A = {
    'crews': 4,                 # bobcat crews on bus stops at once (the City's snow page lists "4 Routes")
    'service_min': 20,          # minutes to clear one stop: boarding area, shelter, bench
    'drive_m_per_min': 134,     # bobcat driving speed on the street: about 5 mph
    'detour': 1.3,              # street distance / straight-line distance
    'drive_max_m': 800,         # farther than this, the bobcat goes on a trailer
    'trailer_min': 30,          # load, haul and unload the bobcat
    'mbta_routes': ['109'],     # the MBTA clears every stop on these routes itself (mbta.com winter page)
    'max_stretch': 12,          # longest stretch a crew commits to before choosing again
    'sweep_after': 0.6,         # once stops with this share of riders are taken, sweep the nearest stretches
}


def meters(a, b):
    """Straight-line distance in meters between two (lon, lat) points."""
    kx = 111320 * math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * 110540)


def move_min(a, b):
    """Minutes to get a crew from point a to point b, and how: 'drive' or 'trailer'."""
    if a is None:
        return A['trailer_min'], 'trailer'          # every crew starts at the yard
    d = meters(a, b) * A['detour']
    if d <= A['drive_max_m']:
        return d / A['drive_m_per_min'], 'drive'
    return A['trailer_min'], 'trailer'


def project(pt, path):
    """Distance along a polyline to the point on it nearest pt, and how far pt is from it (m)."""
    best, along = (1e18, 0), 0
    for p, q in zip(path, path[1:]):
        seg = meters(p, q)
        if seg == 0:
            continue
        kx = 111320 * math.cos(math.radians(p[1]))
        vx, vy = (q[0] - p[0]) * kx, (q[1] - p[1]) * 110540
        wx, wy = (pt[0] - p[0]) * kx, (pt[1] - p[1]) * 110540
        t = max(0, min(1, (wx * vx + wy * vy) / (seg * seg)))
        off = math.hypot(wx - t * vx, wy - t * vy)
        if off < best[0]:
            best = (off, along + t * seg)
        along += seg
    return best[1], best[0]


def stretches(stops, routes):
    """Each route's stops in the order the bus passes them, cut where the gap is too long to drive."""
    out = []
    for rid, r in sorted(routes.items(), key=lambda kv: (len(kv[0]), kv[0])):
        mine = [s for s in stops if rid in s['routes']]
        if not mine or not r['paths']:
            continue
        # put each stop on the path of this route it sits on (both directions are separate paths)
        on = {}
        for s in mine:
            pos = min(((project((s['lon'], s['lat']), p), i) for i, p in enumerate(r['paths'])), key=lambda x: x[0][1])
            (along, off), i = pos
            if off < 120:
                on.setdefault(i, []).append((along, s['id']))
        for i in sorted(on):
            seq = [sid for _, sid in sorted(on[i])]
            cur = [seq[0]]
            for a, b in zip(seq, seq[1:]):
                if meters(P[a], P[b]) * A['detour'] > A['drive_max_m']:
                    out.append((rid, cur)); cur = []
                cur.append(b)
            out.append((rid, cur))
    return out


def run(plan, stops_by_id, choose):
    """Event loop: the crew that frees up first chooses its next stretch with `choose`."""
    crews = [{'t': 0.0, 'at': None, 'n': k + 1} for k in range(A['crews'])]
    done, log = {}, []
    while len(done) < len(stops_by_id):
        c = min(crews, key=lambda c: c['t'])
        pick = choose(c, done)
        if not pick:
            c['t'] = float('inf'); continue
        t, at = c['t'], c['at']
        for sid in pick:
            s = stops_by_id[sid]
            mv, how = move_min(at, P[sid])
            t += mv
            if sid not in done:
                t += A['service_min']
                done[sid] = t
                log.append({'crew': c['n'], 'stop': sid, 'move': how, 'move_min': round(mv, 1), 'done_h': round(t / 60, 2)})
            at = P[sid]
        c['t'], c['at'] = t, at
    return done, log


def route_by_route(stops_by_id, strs):
    """Today's way, as best we can model it: whole routes, in route-number order, split among
    the crews so each has about the same number of stops; each stop counted on its first route."""
    seen, routes = set(), {}
    for rid, seq in strs:
        for sid in seq:
            if sid not in seen:
                seen.add(sid); routes.setdefault(rid, []).append(sid)
    queues = [[] for _ in range(A['crews'])]
    for rid in sorted(routes, key=lambda r: -len(routes[r])):          # balance the crews' loads
        min(queues, key=lambda q: sum(len(routes[x]) for x in q)).append(rid)
    for q in queues:
        q.sort(key=lambda r: (len(r), r))
    todo = {k + 1: [sid for rid in q for sid in routes[rid]] for k, q in enumerate(queues)}

    def choose(c, done):
        q = [sid for sid in todo[c['n']] if sid not in done]
        return q[:1] if q else None
    return run('route', stops_by_id, choose)


def ridership_first(stops_by_id, strs):
    """Each free crew takes the stretch with the most riders cleared per minute, travel included."""
    windows = []
    for rid, seq in strs:
        for d in (seq, seq[::-1]):
            for i in range(len(d)):
                for n in range(1, min(A['max_stretch'], len(d) - i) + 1):
                    windows.append(d[i:i + n])
    claimed = set()
    total = sum(s['riders'] for s in stops_by_id.values())

    def sweep(c):
        """Late phase: the nearest stretch with stops left, whole, so crews stop crossing town."""
        best, key = None, None
        for rid, seq in strs:
            for d in (seq, seq[::-1]):
                w = [sid for sid in d if sid not in claimed]
                if not w:
                    continue
                k = (move_min(c['at'], P[w[0]])[0], -sum(stops_by_id[s]['riders'] for s in w))
                if key is None or k < key:
                    best, key = w, k
        return best

    def choose(c, done):
        if sum(stops_by_id[s]['riders'] for s in claimed) >= A['sweep_after'] * total:
            best = sweep(c)
            if best:
                claimed.update(best)
            return best
        best, best_score = None, 0
        for w in windows:
            new = [sid for sid in w if sid not in claimed]
            if not new or w[0] in claimed:
                continue
            gain = sum(stops_by_id[sid]['riders'] for sid in new) + 1e-3 * len(new)
            t, at = 0.0, c['at']
            for sid in w:
                t += move_min(at, P[sid])[0]
                if sid not in claimed:
                    t += A['service_min']
                at = P[sid]
            score = gain / t
            if score > best_score:
                best, best_score = w, score
        if best:
            claimed.update(best)
        return best
    return run('ridership', stops_by_id, choose)


def curve(done, stops_by_id, total):
    """Share of riders whose stop is clear, hour by hour."""
    end = max(done.values()) / 60
    pts = []
    for h10 in range(0, int(math.ceil(end * 10)) + 1):
        h = h10 / 10
        pts.append([h, round(sum(stops_by_id[s]['riders'] for s, t in done.items() if t / 60 <= h) / total, 4)])
    return pts


def stats(done, log, stops_by_id, total):
    rid = lambda h: sum(stops_by_id[s]['riders'] for s, t in done.items() if t / 60 <= h) / total
    wait = sum(stops_by_id[s]['riders'] * t / 60 for s, t in done.items()) / total
    return {'avg_wait_h': round(wait, 1), 'finish_h': round(max(done.values()) / 60, 1),
            'share_by': {h: round(rid(h) * 100) for h in (2, 4, 6, 8, 12, 24)},
            'trailer_moves': sum(1 for e in log if e['move'] == 'trailer'),
            'move_h': round(sum(e['move_min'] for e in log) / 60, 1)}


if __name__ == '__main__':
    os.makedirs(DATA, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    for f in ('bus-stops.json', 'wards.json'):
        shutil.copyfile(os.path.join(ROOT, 'docs', 'data', f), os.path.join(DATA, f))
    bs = json.load(open(os.path.join(DATA, 'bus-stops.json')))
    wards = json.load(open(os.path.join(DATA, 'wards.json')))['wards']
    allstops = bs['stops']
    mbta = [s for s in allstops if set(s['routes']) & set(A['mbta_routes'])]
    stops = [s for s in allstops if s not in mbta]
    P = {s['id']: (s['lon'], s['lat']) for s in allstops}
    by_id = {s['id']: s for s in stops}
    total = sum(s['riders'] for s in stops)
    def simulate():
        strs = [(r, [x for x in seq if x in by_id]) for r, seq in stretches(stops, bs['routes'])]
        strs = [(r, seq) for r, seq in strs if seq]
        covered = {sid for _, seq in strs for sid in seq}
        for s in stops:                               # a stop no route path passes near: its own stretch
            if s['id'] not in covered:
                strs.append((s['routes'][0] if s['routes'] else '', [s['id']]))
        plans = {'route': route_by_route(by_id, strs), 'ridership': ridership_first(by_id, strs)}
        return plans, {k: stats(d, l, by_id, total) for k, (d, l) in plans.items()}

    # does the answer hold if the assumptions are off? change one at a time
    base, sens = dict(A), []
    for key, val, label in [('crews', 2, '2 crews'), ('crews', 6, '6 crews'), ('service_min', 10, '10 min a stop'),
                            ('service_min', 30, '30 min a stop'), ('trailer_min', 15, '15 min to trailer'),
                            ('trailer_min', 45, '45 min to trailer'), ('drive_max_m', 500, 'drive at most 500 m'),
                            ('drive_max_m', 1500, 'drive up to 1.5 km'), ('drive_m_per_min', 80, 'bobcat at 3 mph')]:
        A.update(base); A[key] = val
        _, s2 = simulate()
        sens.append({'label': label, **{k: {'wait': v['avg_wait_h'], 'h4': v['share_by'][4], 'finish': v['finish_h'],
                                            'trailers': v['trailer_moves']} for k, v in s2.items()}})
    A.update(base)
    plans, S = simulate()

    # ---- plan.csv ----
    with open(os.path.join(OUT, 'plan.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['plan', 'order', 'crew', 'stop_id', 'stop', 'routes', 'weekday_boardings', 'arrive_by', 'move_minutes', 'clear_by_hour'])
        for k, (d, log) in plans.items():
            for i, e in enumerate(sorted(log, key=lambda e: e['done_h']), 1):
                s = by_id[e['stop']]
                w.writerow([k, i, e['crew'], s['id'], s['name'], ' '.join(s['routes']), s['riders'], e['move'], e['move_min'], e['done_h']])

    # ---- summary.md ----
    top = sorted(stops, key=lambda s: -s['riders'])
    acc, half = 0, None
    for i, s in enumerate(top, 1):
        acc += s['riders']
        if half is None and acc >= total / 2:
            half = i
    r, f = S['route'], S['ridership']
    lines = [
        '# Bus stop clearing order: results', '',
        f"Built by build.py from MBTA {bs['season']} weekday boardings. {len(stops)} stops the City clears "
        f"({len(mbta)} more are on route {', '.join(A['mbta_routes'])}, which the MBTA clears), {total:,} weekday boardings.", '',
        f'Half of those boardings happen at {half} stops.', '',
        '| | Route by route | Ridership first |', '| --- | --- | --- |',
        f"| Average wait for a rider's stop | {r['avg_wait_h']} h | {f['avg_wait_h']} h |",
        *[f"| Riders' stops clear after {h} h | {r['share_by'][h]}% | {f['share_by'][h]}% |" for h in (2, 4, 6, 8, 12)],
        f"| All stops clear | {r['finish_h']} h | {f['finish_h']} h |",
        f"| Trailer moves | {r['trailer_moves']} | {f['trailer_moves']} |",
        f"| Time spent moving | {r['move_h']} h | {f['move_h']} h |", '',
        'Hours are working hours for the crews, from the time they start on bus stops.', '',
        'Assumptions: ' + '; '.join(f'{k} = {v}' for k, v in A.items()) + '.', '',
        '## If an assumption is off', '',
        '| Change | Average wait (route by route → ridership first) | Riders\' stops clear after 4 h | All stops clear | Trailer moves |',
        '| --- | --- | --- | --- | --- |',
        *[f"| {x['label']} | {x['route']['wait']} h → {x['ridership']['wait']} h | {x['route']['h4']}% → {x['ridership']['h4']}% "
          f"| {x['route']['finish']} h → {x['ridership']['finish']} h | {x['route']['trailers']} → {x['ridership']['trailers']} |" for x in sens], '']
    open(os.path.join(OUT, 'summary.md'), 'w').write('\n'.join(lines))

    # ---- map.html ----
    payload = {
        'season': bs['season'], 'A': A, 'stats': S, 'total': total, 'half': half, 'sens': sens,
        'nstops': len(stops), 'nmbta': len(mbta),
        # the 3 busiest stops vs. how many of the quietest stops add up to fewer riders
        'top3': {'names': [s['name'] for s in top[:3]], 'riders': sum(s['riders'] for s in top[:3]),
                 'quiet': max(k for k in range(len(top) + 1) if sum(s['riders'] for s in top[len(top) - k:]) < sum(s['riders'] for s in top[:3]))},
        'wards': [w['rings'] for w in wards],
        'routes': {k: v['paths'] for k, v in bs['routes'].items() if v['paths']},
        'stops': [{'id': s['id'], 'n': s['name'], 'x': s['lon'], 'y': s['lat'], 'r': s['riders'], 'rt': s['routes'],
                   **{k: {'h': round(plans[k][0][s['id']] / 60, 2),
                          'c': next(e['crew'] for e in plans[k][1] if e['stop'] == s['id'])} for k in plans}} for s in stops],
        'mbta': [{'n': s['name'], 'x': s['lon'], 'y': s['lat'], 'r': s['riders']} for s in mbta],
        'seq': {k: [[e['crew'], e['stop'], e['move']] for e in sorted(plans[k][1], key=lambda e: (e['crew'], e['done_h']))] for k in plans},
        'curve': {k: curve(plans[k][0], by_id, total) for k in plans},
    }
    tpl = open(os.path.join(HERE, 'map_template.html')).read()
    open(os.path.join(OUT, 'map.html'), 'w').write(tpl.replace('/*DATA*/null', json.dumps(payload, separators=(',', ':'))))
    # the same page on the public site (docs/ is served by GitHub Pages)
    shutil.copyfile(os.path.join(OUT, 'map.html'), os.path.join(ROOT, 'docs', 'bus-stops.html'))
    print('\n'.join(lines))
