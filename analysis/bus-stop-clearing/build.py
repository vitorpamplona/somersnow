#!/usr/bin/env python3
"""Which order should the City clear its bus stops in after a storm?

Goal: the most riders at a clear stop, as fast as possible. We measure it as the
average wait for a rider's stop: each stop's hour of clearing, weighted by its
weekday boardings. Lower is better.

Each bobcat crew starts at its first stop at hour 0 and then drives from stop to
stop all day. Two orders are compared:

  * route by route: each crew works through whole bus routes, stop by stop in the
    order the bus runs (a stand-in for today's practice; the City's own 4 clearing
    routes are not published);
  * riders first: each crew drives next to the stop that clears the most riders
    per minute of driving and clearing; then a clean-up pass moves single stops to
    another place in a crew's day, or to another crew, and flips stretches of a
    crew's day, whenever that lowers the average wait.

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
    'mbta_routes': ['109'],     # the MBTA clears every stop on these routes itself (mbta.com winter page)
    'passes': 8,                # rounds of the clean-up pass
}


def meters(a, b):
    """Straight-line distance in meters between two (lon, lat) points."""
    kx = 111320 * math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * 110540)


_DIST = {}


def drive(a, b):
    """Minutes to drive the bobcat from stop a to stop b."""
    k = (a, b)
    if k not in _DIST:
        _DIST[k] = _DIST[(b, a)] = meters(P[a], P[b])
    return _DIST[k] * A['detour'] / A['drive_m_per_min']


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


def route_orders(stops, routes):
    """Each route's stops in the order the bus passes them (each direction is its own path)."""
    out = []
    for rid, r in sorted(routes.items(), key=lambda kv: (len(kv[0]), kv[0])):
        mine = [s for s in stops if rid in s['routes']]
        if not mine or not r['paths']:
            continue
        on = {}
        for s in mine:
            (along, off), i = min(((project((s['lon'], s['lat']), p), i) for i, p in enumerate(r['paths'])), key=lambda x: x[0][1])
            if off < 120:
                on.setdefault(i, []).append((along, s['id']))
        for i in sorted(on):
            out.append((rid, [sid for _, sid in sorted(on[i])]))
    return out


# ---------- timing ----------
def times(seq):
    """Hour each stop in one crew's day is clear, and the minutes it drove."""
    t, out, drove = 0.0, [], 0.0
    for i, sid in enumerate(seq):
        if i:
            d = drive(seq[i - 1], sid); t += d; drove += d
        t += A['service_min']
        out.append(t)
    return out, drove


def cost(seq):
    """Rider-hours of waiting for one crew's day (lower is better)."""
    t, w = 0.0, 0.0
    for i, sid in enumerate(seq):
        if i:
            t += drive(seq[i - 1], sid)
        t += A['service_min']
        w += R[sid] * t
    return w


# ---------- the two plans ----------
def route_by_route(stops, orders):
    """Whole routes, in route-number order, split among the crews so each has about the
    same number of stops; each stop counted on its first route."""
    seen, routes = set(), {}
    for rid, seq in orders:
        for sid in seq:
            if sid not in seen:
                seen.add(sid); routes.setdefault(rid, []).append(sid)
    for s in stops:                                   # a stop no route path passes near
        if s['id'] not in seen:
            routes.setdefault(s['routes'][0], []).append(s['id']); seen.add(s['id'])
    queues = [[] for _ in range(A['crews'])]
    for rid in sorted(routes, key=lambda r: -len(routes[r])):
        min(queues, key=lambda q: sum(len(routes[x]) for x in q)).append(rid)
    return [[sid for rid in sorted(q, key=lambda r: (len(r), r)) for sid in routes[rid]] for q in queues]


def riders_first(stops):
    """Greedy start, then a clean-up pass of single-stop moves and flips."""
    left = {s['id'] for s in stops}
    seqs = [[] for _ in range(A['crews'])]
    clock = [0.0] * A['crews']
    while left:
        k = min(range(A['crews']), key=lambda k: clock[k])
        here = seqs[k][-1] if seqs[k] else None

        def score(sid):
            d = drive(here, sid) if here else 0.0
            return (R[sid] + 1e-3) / (d + A['service_min'])
        nxt = max(left, key=score)
        clock[k] += (drive(here, nxt) if here else 0.0) + A['service_min']
        seqs[k].append(nxt); left.discard(nxt)

    costs = [cost(s) for s in seqs]
    for _ in range(A['passes']):
        better = False
        # move one stop to any place in any crew's day
        for a in range(len(seqs)):
            i = 0
            while i < len(seqs[a]):
                sid = seqs[a][i]
                rest = seqs[a][:i] + seqs[a][i + 1:]
                ca = cost(rest)
                best = (0, None)
                for b in range(len(seqs)):
                    base = rest if b == a else seqs[b]
                    cb_old = ca if b == a else costs[b]
                    for j in range(len(base) + 1):
                        cand = base[:j] + [sid] + base[j:]
                        gain = (costs[a] + (0 if b == a else costs[b])) - ((cost(cand)) + (0 if b == a else ca))
                        if gain > best[0] + 1e-6:
                            best = (gain, (b, j))
                if best[1]:
                    b, j = best[1]
                    if b == a:
                        seqs[a] = rest[:j] + [sid] + rest[j:]
                    else:
                        seqs[a] = rest; seqs[b] = seqs[b][:j] + [sid] + seqs[b][j:]
                        costs[b] = cost(seqs[b])
                    costs[a] = cost(seqs[a]); better = True
                    if b != a:
                        continue                      # the next stop slid into place i
                i += 1
        # flip a stretch of one crew's day (fixes paths that cross themselves)
        for a in range(len(seqs)):
            s = seqs[a]
            for i in range(1, len(s) - 1):
                for j in range(i + 1, len(s)):
                    cand = s[:i] + s[i:j + 1][::-1] + s[j + 1:]
                    c = cost(cand)
                    if c < costs[a] - 1e-6:
                        s, costs[a], better = cand, c, True
            seqs[a] = s
        if not better:
            break
    return seqs


def schedule(seqs):
    """Hour each stop is clear, its crew, and the minutes driven to reach it."""
    done = {}
    for k, seq in enumerate(seqs):
        ts, _ = times(seq)
        for i, (sid, t) in enumerate(zip(seq, ts)):
            done[sid] = {'h': t / 60, 'crew': k + 1, 'drive': drive(seq[i - 1], sid) if i else 0.0, 'order': i + 1}
    return done


def stats(seqs, total):
    done = schedule(seqs)
    share = lambda h: sum(R[s] for s, d in done.items() if d['h'] <= h) / total
    km = sum(meters(P[a], P[b]) * A['detour'] for seq in seqs for a, b in zip(seq, seq[1:])) / 1000
    return {'avg_wait_h': round(sum(R[s] * d['h'] for s, d in done.items()) / total, 1),
            'finish_h': round(max(d['h'] for d in done.values()), 1),
            'share_by': {h: round(share(h) * 100) for h in (1, 2, 4, 6, 8, 12)},
            'drive_h': round(sum(d['drive'] for d in done.values()) / 60, 1),
            'km': round(km, 1)}


def curve(seqs, total):
    done = schedule(seqs)
    end = max(d['h'] for d in done.values())
    return [[h10 / 10, round(sum(R[s] for s, d in done.items() if d['h'] <= h10 / 10) / total, 4)]
            for h10 in range(0, int(math.ceil(end * 10)) + 1)]


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
    R = {s['id']: s['riders'] for s in stops}
    by_id = {s['id']: s for s in stops}
    total = sum(R.values())
    orders = [(r, [x for x in seq if x in by_id]) for r, seq in route_orders(stops, bs['routes'])]
    orders = [(r, seq) for r, seq in orders if seq]

    def simulate():
        plans = {'route': route_by_route(stops, orders), 'riders': riders_first(stops)}
        return plans, {k: stats(v, total) for k, v in plans.items()}

    # does the answer hold if the assumptions are off? change one at a time
    base, sens = dict(A), []
    for key, val, label in [('crews', 2, '2 crews'), ('crews', 6, '6 crews'), ('service_min', 10, '10 min a stop'),
                            ('service_min', 30, '30 min a stop'), ('drive_m_per_min', 80, 'bobcat at 3 mph'),
                            ('drive_m_per_min', 215, 'bobcat at 8 mph'), ('detour', 1.6, 'streets 60% longer than a straight line')]:
        A.update(base); A[key] = val; A['passes'] = 3
        _, s2 = simulate()
        sens.append({'label': label, **{k: {'wait': v['avg_wait_h'], 'h4': v['share_by'][4], 'finish': v['finish_h']} for k, v in s2.items()}})
    A.update(base)
    plans, S = simulate()
    sched = {k: schedule(v) for k, v in plans.items()}

    # ---- plan.csv ----
    with open(os.path.join(OUT, 'plan.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['plan', 'crew', 'order', 'stop_id', 'stop', 'routes', 'weekday_boardings', 'drive_minutes', 'clear_by_hour'])
        for k, seqs in plans.items():
            for c, seq in enumerate(seqs, 1):
                for sid in seq:
                    d, s = sched[k][sid], by_id[sid]
                    w.writerow([{'route': 'route by route', 'riders': 'riders first'}[k], c, d['order'], sid, s['name'],
                                ' '.join(s['routes']), s['riders'], round(d['drive'], 1), round(d['h'], 2)])

    # ---- summary.md ----
    top = sorted(stops, key=lambda s: -s['riders'])
    acc, half = 0, None
    for i, s in enumerate(top, 1):
        acc += s['riders']
        if half is None and acc >= total / 2:
            half = i
    r, f = S['route'], S['riders']
    lines = [
        '# Bus stop clearing order: results', '',
        f"Built by build.py from MBTA {bs['season']} weekday boardings. {len(stops)} stops the City clears "
        f"({len(mbta)} more are on route {', '.join(A['mbta_routes'])}, which the MBTA clears), {total:,} weekday boardings.", '',
        f'Half of those boardings happen at {half} stops.', '',
        '| | Route by route | Riders first |', '| --- | --- | --- |',
        f"| Average wait for a rider's stop | {r['avg_wait_h']} h | {f['avg_wait_h']} h |",
        *[f"| Riders' stops clear after {h} h | {r['share_by'][h]}% | {f['share_by'][h]}% |" for h in (1, 2, 4, 8, 12)],
        f"| All stops clear | {r['finish_h']} h | {f['finish_h']} h |",
        f"| Hours driving between stops | {r['drive_h']} h | {f['drive_h']} h |",
        f"| Distance driven | {r['km']} km | {f['km']} km |", '',
        'Hours are working hours, from when the crews start at their first stops. The bobcats drive from stop to stop.', '',
        'Assumptions: ' + '; '.join(f'{k} = {v}' for k, v in A.items()) + '.', '',
        '## If an assumption is off', '',
        '| Change | Average wait (route by route → riders first) | Riders\' stops clear after 4 h | All stops clear |',
        '| --- | --- | --- | --- |',
        *[f"| {x['label']} | {x['route']['wait']} h → {x['riders']['wait']} h | {x['route']['h4']}% → {x['riders']['h4']}% "
          f"| {x['route']['finish']} h → {x['riders']['finish']} h |" for x in sens], '']
    open(os.path.join(OUT, 'summary.md'), 'w').write('\n'.join(lines))

    # ---- map.html ----
    longest = max((sched['riders'][sid]['drive'], sid) for sid in R)
    payload = {
        'season': bs['season'], 'A': A, 'stats': S, 'total': total, 'half': half, 'sens': sens,
        'nstops': len(stops), 'nmbta': len(mbta),
        'top3': {'names': [s['name'] for s in top[:3]], 'riders': sum(s['riders'] for s in top[:3]),
                 'quiet': max(k for k in range(len(top) + 1) if sum(s['riders'] for s in top[len(top) - k:]) < sum(s['riders'] for s in top[:3]))},
        'longest_drive_min': round(longest[0]),
        'wards': [w['rings'] for w in wards],
        'routes': {k: v['paths'] for k, v in bs['routes'].items() if v['paths']},
        'stops': [{'id': s['id'], 'n': s['name'], 'x': s['lon'], 'y': s['lat'], 'r': s['riders'], 'rt': s['routes'],
                   **{k: {'h': round(sched[k][s['id']]['h'], 2), 'c': sched[k][s['id']]['crew']} for k in plans}} for s in stops],
        'mbta': [{'n': s['name'], 'x': s['lon'], 'y': s['lat'], 'r': s['riders']} for s in mbta],
        'seq': plans,
        'curve': {k: curve(v, total) for k, v in plans.items()},
    }
    tpl = open(os.path.join(HERE, 'map_template.html')).read()
    open(os.path.join(OUT, 'map.html'), 'w').write(tpl.replace('/*DATA*/null', json.dumps(payload, separators=(',', ':'))))
    # the same page on the public site (docs/ is served by GitHub Pages)
    shutil.copyfile(os.path.join(OUT, 'map.html'), os.path.join(ROOT, 'docs', 'bus-stops.html'))
    print('\n'.join(lines))
