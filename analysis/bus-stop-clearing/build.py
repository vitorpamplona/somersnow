#!/usr/bin/env python3
"""Which order should the City clear its bus stops in after a storm?

Goal: the most riders at a clear stop, as fast as possible. We measure it as the
average wait for a rider's stop: each stop's hour of clearing, weighted by its
weekday riders: the people who get on there plus the people who get off (someone
stepping off the bus needs a clear stop too). Lower is better.

The bobcats move only along the street, stop to stop. Each side of a street is
driven the way the bus goes; to reach the stop across the street, or where a route
leaves the city, a crew turns around. A crew never drives past a waiting stop; it
clears the next one it reaches. It may drive through stops that are already clear.
Each crew starts at its first stop at hour 0.

Two orders are compared:
  * route by route: each crew works through whole bus routes, stop by stop in the
    order the bus runs (a stand-in for today's practice; the City's own 4 clearing
    routes are not published);
  * riders first: crews start at busy stops spread across the city; a crew keeps
    going along its side of the street while the next stop waits, then crosses the
    road and clears the other side on the way back; after that it heads for the
    waiting stop whose run ahead clears the most riders per minute of driving and
    clearing (leaving other crews the stops just ahead of them, and coming back to
    the far side of its own streets first: both sides of a street are one crew's);
    once stops with 70% of riders are clear, the nearest.

Inputs (copied into data/ by this script so the folder is self-contained):
  ../../docs/data/bus-stops.json  MBTA stops in Somerville, Fall weekday boardings and alightings, routes
  ../../docs/data/wards.json      ward outlines, for the map

Outputs (output/):
  plan.csv     every stop, in the order each plan clears it, with times
  summary.md   the headline numbers
  map.html     the illustrated explainer (open it in a browser); also copied to
               docs/bus-stops.html, the public page

Python standard library only:  python3 analysis/bus-stop-clearing/build.py
"""
import csv, heapq, json, math, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
DATA, OUT = os.path.join(HERE, 'data'), os.path.join(HERE, 'output')

# ---------- assumptions (change them here; every output is rebuilt from them) ----------
A = {
    'crews': 4,                 # bobcat crews on bus stops at once (the City's snow page lists "4 Routes")
    'service_min': 20,          # minutes to clear one stop: boarding area, shelter, bench
    'drive_m_per_min': 134,     # bobcat driving speed on the street: about 5 mph
    'cross_m': 60,              # stops this close are across the street from each other
    'on_route_m': 25,           # a stop this close to a leg is on it (branches share streets)
    'turn_min': 1,              # crossing to clear the other side of the street (or turning at the city line): small roads
    'max_link_m': 900,          # longer gaps between stops on a route mean stops are missing in between: no link
    'lookahead': 8,             # a crew judges a direction by the run of up to this many waiting stops ahead
    'start_apart_m': 1200,      # the crews' first stops are at least this far apart
    'jump_m': 800,              # a drive longer than this to the next stop is a jump to a different place
    'jump_min': 30,             # a jump counts as this many minutes of everyone's average wait when planning (it isn't added to the hours)
    'sweep_after': 0.7,         # once stops with this share of riders are clear, take the nearest waiting stop
    'mbta_routes': ['109'],     # the MBTA clears every stop on these routes itself (mbta.com winter page)
}


def meters(a, b):
    """Straight-line distance in meters between two (lon, lat) points."""
    kx = 111320 * math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((a[0] - b[0]) * kx, (a[1] - b[1]) * 110540)


def project(pt, path):
    """Distance along a polyline to the point on it nearest pt, how far pt is from it (m), and
    whether pt is on the right of the line in the direction it runs (where a bus stops)."""
    best, along = (1e18, 0, True), 0
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
            best = (off, along + t * seg, vx * wy - vy * wx <= 0)
        along += seg
    return best[1], best[0], best[2]


def route_orders(stops, routes):
    """Each route's stops in the order the bus passes them, with the distance along the
    route. Each direction is its own path (a leg), and a stop belongs to the leg it stands on
    the right of: on a two-way street both legs follow the same line, one stop on each side.
    A stop is on every leg that passes it (branches share streets). A stop on the left of
    every leg is served by buses running the other way on a pattern the route data doesn't
    carry, so it goes on that street driven the other way."""
    out = []
    for rid, r in sorted(routes.items(), key=lambda kv: (len(kv[0]), kv[0])):
        mine = [s for s in stops if rid in s['routes']]
        if not mine or not r['paths']:
            continue
        paths = r['paths'] + [p[::-1] for p in r['paths']]
        n, on = len(r['paths']), {}
        for s in mine:
            fits = [(project((s['lon'], s['lat']), p), i) for i, p in enumerate(paths)]
            ok = [f for f in fits if f[0][1] < 120]
            pick = ([f for f in ok if f[1] < n and f[0][2]]
                    or [f for f in ok if f[1] >= n and f[0][2]] or ok)
            if pick:                              # every leg that passes it (branches share streets)
                best = min(f[0][1] for f in pick)
                for (along, off, _), i in pick:
                    if off <= max(best, A['on_route_m']):
                        on.setdefault(i, []).append((along, s['id']))
        for i in sorted(on):
            out.append((rid, paths[i], sorted(on[i])))
    return out


def slice_path(path, x, y):
    """The piece of a polyline between distances x and y along it."""
    def at(p, q, t):
        return [p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t]
    pts, along = [], 0.0
    for p, q in zip(path, path[1:]):
        seg = meters(p, q)
        if seg and along + seg >= x and along <= y:
            if not pts:
                pts.append(at(p, q, max(0.0, (x - along) / seg)))
            if along + seg >= y:
                pts.append(at(p, q, (y - along) / seg)); break
            pts.append(list(q))
        along += seg
    return [[round(a, 5), round(b, 5)] for a, b in pts]


GEO = {}                                          # (a, b) -> the street shape of the link from a to b
AWAY = set()                                      # links that leave the city or the bus routes (no street shape)


def street_network(allstops, routes):
    """A one-way network: each bus route's stops on one side of the street, linked from each stop
    to the next in the direction the bus runs (by the route's own length, unless the gap is so
    long that stops must be missing in between). Crossing to the stop on the other side of the
    street is a turnaround that costs A['turn_min'], and so is the end of a leg, where the bus
    leaves the city: the crew turns to the nearest stop of the same route's other direction. Where the network can't get from one part
    to another, the closest stops are joined both ways. G[a][b] = (meters, kind)."""
    G = {s['id']: {} for s in allstops}
    RT = {s['id']: s['routes'] for s in allstops}
    GEO.clear(); AWAY.clear()

    def link(a, b, m, kind, shape=None):
        if a != b and (b not in G[a] or edge_min(m, kind) < edge_min(*G[a][b])):
            G[a][b] = (m, kind)
            GEO.pop((a, b), None)
            if shape and len(shape) > 2:
                GEO[(a, b)] = shape
    legs = route_orders(allstops, routes)
    for _, path, seq in legs:
        for (x, a), (y, b) in zip(seq, seq[1:]):
            m = max(y - x, meters(P[a], P[b]))
            if m <= A['max_link_m']:
                link(a, b, m, 'drive', slice_path(path, x, y))
    for rid, _, seq in legs:                      # where a leg leaves the city, turn around like the bus
        first, last = seq[0][1], seq[-1][1]
        other = sorted({t for r, _, q in legs if r == rid and q is not seq for _, t in q} - {first, last})
        if other:
            for a, b in ((last, min(other, key=lambda t: meters(P[last], P[t]))),
                         (min(other, key=lambda t: meters(P[first], P[t])), first)):
                link(a, b, meters(P[a], P[b]), 'turn')
                if meters(P[a], P[b]) > A['cross_m']:
                    AWAY.add((a, b))
    ids = list(G)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            d = meters(P[a], P[b])
            if d <= A['cross_m']:
                link(a, b, d, 'turn'); link(b, a, d, 'turn')
    joins = 0
    while True:                                   # every stop must be able to reach every other
        comps = strong_parts(G)
        if len(comps) == 1:
            return G, joins
        small = min(comps, key=len)
        a, b = min(((a, b) for a in sorted(small) for b in ids if b not in small),   # a stop on the same route counts half as far
                   key=lambda ab: meters(P[ab[0]], P[ab[1]]) / (2 if set(RT[ab[0]]) & set(RT[ab[1]]) else 1))
        d = meters(P[a], P[b])
        link(a, b, d, 'join'); link(b, a, d, 'join'); AWAY.update({(a, b), (b, a)}); joins += 1


def strong_parts(G):
    """Groups of stops that can all reach each other (strongly connected components)."""
    order, seen = [], set()
    for s in G:                                   # pass 1: finishing order
        if s in seen:
            continue
        stack = [(s, iter(G[s]))]; seen.add(s)
        while stack:
            u, it = stack[-1]
            v = next(it, None)
            if v is None:
                order.append(u); stack.pop()
            elif v not in seen:
                seen.add(v); stack.append((v, iter(G[v])))
    back = {s: [] for s in G}
    for u in G:
        for v in G[u]:
            back[v].append(u)
    comps, done = [], set()
    for s in reversed(order):                     # pass 2: on the reversed links
        if s in done:
            continue
        part, todo = set(), [s]
        while todo:
            u = todo.pop()
            if u not in done:
                done.add(u); part.add(u); todo.extend(back[u])
        comps.append(part)
    return comps


def edge_min(m, kind):
    """Minutes for one link: driving at the bobcat's speed, plus the turnaround to cross."""
    return m / A['drive_m_per_min'] + (A['turn_min'] if kind == 'turn' else 0)


def dijkstra(G, src, stop_at=None):
    """Quickest drive (minutes) from src. Nodes in stop_at are reached but not driven through."""
    dist, prev, pq = {src: 0.0}, {}, [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        if stop_at and u != src and u in stop_at:
            continue
        for v, (m, kind) in G[u].items():
            nd = d + edge_min(m, kind)
            if nd < dist.get(v, 1e18):
                dist[v], prev[v] = nd, u
                heapq.heappush(pq, (nd, v))
    return dist, prev


def path_meters(G, src, path):
    """Meters driven along a path of stops starting at src."""
    m, at = 0.0, src
    for n in path:
        m += G[at][n][0]; at = n
    return m


def path_to(prev, src, dst):
    p = [dst]
    while p[-1] != src:
        p.append(prev[p[-1]])
    return p[::-1][1:]                            # the stops after src, ending at dst


# ---------- the two plans ----------
def route_by_route(G, stops, orders):
    """Whole routes, in route-number order, split among the crews so each has about the
    same number of stops; each stop counted on its first route."""
    seen, routes = set(), {}
    for rid, _, seq in orders:
        for _, sid in seq:
            if sid in R and sid not in seen:
                seen.add(sid); routes.setdefault(rid, []).append(sid)
    for s in stops:                                   # a stop no route path passes near
        if s['id'] not in seen:
            routes.setdefault(s['routes'][0], []).append(s['id']); seen.add(s['id'])
    queues = [[] for _ in range(A['crews'])]
    for rid in sorted(routes, key=lambda r: -len(routes[r])):
        min(queues, key=lambda q: sum(len(routes[x]) for x in q)).append(rid)
    days = []
    for q in queues:
        seq = [sid for rid in sorted(q, key=lambda r: (len(r), r)) for sid in routes[rid]]
        t, day = 0.0, []
        for i, sid in enumerate(seq):
            path, m, mins = [sid], 0.0, 0.0
            if i:
                dist, prev = dijkstra(G, seq[i - 1])
                path, mins = path_to(prev, seq[i - 1], sid), dist[sid]
                m = path_meters(G, seq[i - 1], path)
            t += mins + A['service_min']
            day.append({'stop': sid, 'path': path, 'm': m, 'mins': mins, 'h': t / 60})
        days.append(day)
    return days


def run_value(G, start_min, v, left):
    """Riders per minute of the run that starts at v and follows the street from waiting stop to
    adjacent waiting stop, up to A['lookahead'] stops: the best of its first 1, 2, ... stops."""
    t, val, cur, seen = start_min + A['service_min'], R[v], v, {v}
    best = (val + 1e-3) / t
    for _ in range(A['lookahead'] - 1):
        nb = [(w, edge_min(*e)) for w, e in sorted(G[cur].items()) if w in left and w not in seen]
        if not nb:
            break
        w, mins = max(nb, key=lambda wm: (R[wm[0]] + 1e-3) / (wm[1] + A['service_min']))
        t += mins + A['service_min']; val += R[w]; seen.add(w); cur = w
        best = max(best, (val + 1e-3) / t)
    return best


def run_ahead(G, here, left):
    """The stops a crew at `here` will clear next by the street rules: along its side while the
    next stop waits, then across the road and back (up to A['lookahead'] stops)."""
    run, cur = [], here
    for _ in range(A['lookahead']):
        nb = [w for w, (m, kind) in sorted(G[cur].items()) if kind == 'drive' and w in left and w not in run]
        nb = nb or [w for w, (m, kind) in sorted(G[cur].items()) if kind == 'turn' and w in left and w not in run]
        if not nb:
            break
        cur = max(nb, key=lambda w: R[w]); run.append(cur)
    return run


def riders_first(G, stops):
    """Crews start at busy stops spread across the city. A crew keeps going along its side of
    the street while the next stop ahead waits; at the end of the run it crosses the road and
    clears the other side on the way back. With neither, it heads for the waiting stop whose run
    ahead clears the most riders per minute, and once stops with most riders are clear, the
    nearest waiting stop. Either way it leaves other crews their runs ahead and the far side of
    every street they cleared, and comes back first to the far side of its own: each street,
    both sides, is one crew's. A crew never drives past a waiting stop."""
    left = {s['id'] for s in stops}
    total = sum(R[s] for s in left)
    days = [[] for _ in range(A['crews'])]
    clock, starts, taken = [0.0] * A['crews'], [], 0
    for k in range(A['crews']):                       # hour 0: busy stops, spread apart
        far = [s for s in sorted(left) if all(meters(P[s], P[x]) > A['start_apart_m'] for x in starts)] or sorted(left)
        sid = max(far, key=lambda s: run_value(G, 0.0, s, left))
        starts.append(sid); left.discard(sid); taken += R[sid]; clock[k] = A['service_min']
        days[k].append({'stop': sid, 'path': [sid], 'm': 0.0, 'h': clock[k] / 60})
    while left:
        k = min(range(A['crews']), key=lambda k: clock[k])
        here = days[k][-1]['stop']
        dist, prev = dijkstra(G, here, stop_at=left)
        reach = [s for s in sorted(left) if s in dist]
        if not reach:
            clock[k] = float('inf'); continue
        ahead = [w for w, (m, kind) in sorted(G[here].items()) if kind == 'drive' and w in left]
        back = [w for w, (m, kind) in sorted(G[here].items()) if kind == 'turn' and w in left]
        if ahead:                                     # keep going along this side while the next stop waits
            nxt = max(ahead, key=lambda s: run_value(G, dist[s], s, left))
        elif back:                                    # then cross the road and clear the other side on the way back
            nxt = max(back, key=lambda s: run_value(G, dist[s], s, left))
        else:
            far = [{w for e in day for w, (m, kind) in G[e['stop']].items() if kind == 'turn' and m <= A['cross_m']} for day in days]
            theirs = {w for j in range(A['crews']) if j != k for w in run_ahead(G, days[j][-1]['stop'], left) + sorted(far[j])}
            reach = [s for s in reach if s not in theirs] or reach    # leave other crews their runs ahead and their streets' far sides
            jump = {s: path_meters(G, here, path_to(prev, here, s)) > A['jump_m'] for s in reach}
            cost = {s: dist[s] + (A['jump_min'] if jump[s] else 0) for s in reach}   # jumps across town are costly
            reach = [s for s in reach if s in far[k] and not jump[s]] or reach   # finish the far side of your own street
            if taken >= A['sweep_after'] * total:
                nxt = min(reach, key=lambda s: (cost[s], -R[s]))
            else:
                nxt = max(reach, key=lambda s: run_value(G, cost[s], s, left))
        clock[k] += dist[nxt] + A['service_min']
        left.discard(nxt); taken += R[nxt]
        path = path_to(prev, here, nxt)
        days[k].append({'stop': nxt, 'path': path, 'm': path_meters(G, here, path), 'mins': dist[nxt], 'h': clock[k] / 60})
    return days


ALL = {}                                          # (speed, crossing) -> {stop: (minutes to every stop, previous)}, for follow()
JOB = []                                          # the what-if runner, set by the main script (for worker processes)


def run_job(i):
    return JOB[0](i)


def follow(G, lists):
    """Crews work through their lists of stops, each by the quickest way; a crew that reaches a
    waiting stop on the way clears it then and there (so no crew ever drives past a waiting
    stop). A crew that finishes its list helps with the nearest waiting stop."""
    key = (A['drive_m_per_min'], A['turn_min'])
    if key not in ALL:
        ALL[key] = {a: dijkstra(G, a) for a in G}
    quick, paths = ALL[key], ALL.setdefault(key + ('paths',), {})

    def sp(a, b):
        if (a, b) not in paths:
            paths[(a, b)] = path_to(quick[a][1], a, b) if a != b else []
        return paths[(a, b)]
    waiting = {s for L in lists for s in L}
    n = len(lists)
    days, clock, pos, ptr = [[] for _ in range(n)], [0.0] * n, [None] * n, [0] * n
    for k, L in enumerate(lists):
        pos[k] = L[0]; waiting.discard(L[0]); clock[k] = A['service_min']
        days[k].append({'stop': L[0], 'path': [L[0]], 'm': 0.0, 'mins': 0.0, 'h': clock[k] / 60})
    while waiting:
        k = min(range(n), key=lambda k: (clock[k], k))
        L = lists[k]
        while ptr[k] < len(L) and L[ptr[k]] not in waiting:
            ptr[k] += 1
        if ptr[k] < len(L):
            tgt = L[ptr[k]]
        else:
            dist = quick[pos[k]][0]
            tgt = min(sorted(waiting), key=lambda t: dist.get(t, 1e18))
        path, m, mins, at = [], 0.0, 0.0, pos[k]
        for nd in sp(pos[k], tgt):
            e = G[at][nd]; m += e[0]; mins += edge_min(*e); path.append(nd); at = nd
            if nd in waiting:
                break
        waiting.discard(at); clock[k] += mins + A['service_min']; pos[k] = at
        days[k].append({'stop': at, 'path': path, 'm': m, 'mins': mins, 'h': clock[k] / 60})
    return days


def fewer_jumps(G, days, total):
    """Look at the whole day: cut each crew's day at its jumps, and try handing each piece to
    the crew that passes closest to it (at its first or last stop, either way round). Keep a
    change when it lowers the average wait plus A['jump_min'] for every jump."""
    def score(d):
        st = stats(d, total)
        return st['avg_wait_h'] * 60 + A['jump_min'] * st['jumps']
    lists = [[e['stop'] for e in day] for day in days]
    days = follow(G, lists)
    best = score(days)
    for _ in range(40):
        lists = [[e['stop'] for e in day] for day in days]
        pieces = []
        for k, day in enumerate(days):
            cur = []
            for i, e in enumerate(day):
                if i and e['m'] > A['jump_m'] and cur:
                    pieces.append((k, cur)); cur = []
                cur.append(e['stop'])
            pieces.append((k, cur))
        better = False
        for k, piece in pieces:
            if piece[0] == lists[k][0]:
                continue                                  # a crew keeps its first stop
            rest = [[s for s in L if s not in piece] for L in lists]
            tries = []
            for j, L in enumerate(rest):
                for end, seg in ((piece[0], piece), (piece[-1], piece[::-1])):
                    tries += [(j, i, seg) for i in sorted(range(len(L)), key=lambda i: (meters(P[L[i]], P[end]), i))[:3]]
            for j, i, seg in tries:
                trial = [L[:] for L in rest]; trial[j] = trial[j][:i + 1] + seg + trial[j][i + 1:]
                d = follow(G, trial); sc = score(d)
                if sc < best - 1e-9:
                    best, days, better = sc, d, True
                    break
        if not better:
            return days
    return days


def stats(days, total):
    done = {e['stop']: e['h'] for day in days for e in day}
    share = lambda h: sum(R[s] for s, t in done.items() if t <= h) / total
    return {'avg_wait_h': round(sum(R[s] * t for s, t in done.items()) / total, 1),
            'finish_h': round(max(done.values()), 1),
            'share_by': {h: round(share(h) * 100) for h in (1, 2, 4, 6, 8, 12)},
            'drive_h': round(sum(e.get('mins', e['m'] / A['drive_m_per_min']) for day in days for e in day) / 60, 1),
            'km': round(sum(e['m'] for day in days for e in day) / 1000, 1),
            'jumps': sum(1 for day in days for e in day if e['m'] > A['jump_m']),
            'jump_km': round(sum(e['m'] for day in days for e in day if e['m'] > A['jump_m']) / 1000, 1)}


def curve(days, total):
    done = {e['stop']: e['h'] for day in days for e in day}
    end = max(done.values())
    return [[h10 / 10, round(sum(R[s] for s, t in done.items() if t <= h10 / 10) / total, 4)]
            for h10 in range(0, int(math.ceil(end * 10)) + 1)]


if __name__ == '__main__':
    os.makedirs(DATA, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    for f in ('bus-stops.json', 'wards.json'):
        shutil.copyfile(os.path.join(ROOT, 'docs', 'data', f), os.path.join(DATA, f))
    bs = json.load(open(os.path.join(DATA, 'bus-stops.json')))
    wards = json.load(open(os.path.join(DATA, 'wards.json')))['wards']
    allstops = bs['stops']
    for s in allstops:                                # riders at a stop: people getting on plus people getting off
        s['on'], s['riders'] = s['riders'], s['riders'] + s['off']
    mbta = [s for s in allstops if set(s['routes']) & set(A['mbta_routes'])]
    stops = [s for s in allstops if s not in mbta]
    P = {s['id']: (s['lon'], s['lat']) for s in allstops}
    R = {s['id']: s['riders'] for s in stops}
    by_id = {s['id']: s for s in stops}
    total = sum(R.values())
    G, joins = street_network(allstops, bs['routes'])
    orders = route_orders(stops, bs['routes'])

    def simulate():
        plans = {'route': route_by_route(G, stops, orders), 'riders': fewer_jumps(G, riders_first(G, stops), total)}
        return plans, {k: stats(v, total) for k, v in plans.items()}

    # does the answer hold if the assumptions are off? change one at a time (and try 1 to 10 crews);
    # each what-if is a whole plan, so they run side by side where the computer allows it
    base = dict(A)
    whatifs = [('crews', 2, '2 crews'), ('crews', 6, '6 crews'), ('service_min', 10, '10 min a stop'),
               ('service_min', 30, '30 min a stop'), ('drive_m_per_min', 80, 'bobcat at 3 mph'),
               ('drive_m_per_min', 215, 'bobcat at 8 mph')] + [('crews', c, c) for c in range(1, 11)]

    def whatif(i):
        A.update(base); A[whatifs[i][0]] = whatifs[i][1]
        return simulate()[1]
    JOB[:] = [whatif]
    try:
        import multiprocessing
        with multiprocessing.get_context('fork').Pool() as pool:
            results = pool.map(run_job, range(len(whatifs)))
    except (ValueError, OSError):                      # no fork (Windows): one at a time
        results = [whatif(i) for i in range(len(whatifs))]
    A.update(base)
    sens = [{'label': label, **{k: {'wait': v['avg_wait_h'], 'h4': v['share_by'][4], 'finish': v['finish_h']} for k, v in s2.items()}}
            for (_, _, label), s2 in zip(whatifs[:6], results[:6])]
    plans, S = simulate()

    # how many crews? same rules, 1 to 10 crews
    crews_curve = [{'crews': c, **{k: {'wait': v['avg_wait_h'], 'finish': v['finish_h']} for k, v in s2.items()}}
                   for (_, c, _), s2 in zip(whatifs[6:], results[6:])]

    # ---- plan.csv ----
    with open(os.path.join(OUT, 'plan.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['plan', 'crew', 'order', 'stop_id', 'stop', 'routes', 'weekday_on', 'weekday_off', 'weekday_riders', 'drive_meters', 'drive_minutes', 'clear_by_hour', 'drives_through'])
        for k, days in plans.items():
            for c, day in enumerate(days, 1):
                for i, e in enumerate(day, 1):
                    s = by_id[e['stop']]
                    through = [P_name for P_name in (by_id[x]['name'] if x in by_id else next(m['name'] for m in mbta if m['id'] == x) for x in e['path'][:-1])]
                    w.writerow([{'route': 'route by route', 'riders': 'riders first'}[k], c, i, s['id'], s['name'], ' '.join(s['routes']),
                                s['on'], s['off'], s['riders'], round(e['m']), round(e.get('mins', 0), 1), round(e['h'], 2), '; '.join(through)])

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
        f"Built by build.py from MBTA {bs['season']} weekday ridership. {len(stops)} stops the City clears "
        f"({len(mbta)} more are on route {', '.join(A['mbta_routes'])}, which the MBTA clears), {total:,} weekday riders: "
        f"{sum(s['on'] for s in stops):,} getting on and {sum(s['off'] for s in stops):,} getting off.", '',
        f'Half of those riders use {half} stops.', '',
        '| | Route by route | Riders first |', '| --- | --- | --- |',
        f"| Average wait for a rider's stop | {r['avg_wait_h']} h | {f['avg_wait_h']} h |",
        *[f"| Riders' stops clear after {h} h | {r['share_by'][h]}% | {f['share_by'][h]}% |" for h in (1, 2, 4, 8, 12)],
        f"| All stops clear | {r['finish_h']} h | {f['finish_h']} h |",
        f"| Hours driving | {r['drive_h']} h | {f['drive_h']} h |",
        f"| Distance driven | {r['km']} km | {f['km']} km |",
        f"| Jumps (drives over {A['jump_m']} m to the next stop) | {r['jumps']} ({r['jump_km']} km) | {f['jumps']} ({f['jump_km']} km) |", '',
        'Hours are working hours, from when the crews start at their first stops. The bobcats drive along the street, '
        'stop to stop, and never drive past a waiting stop.', '',
        'Assumptions: ' + '; '.join(f'{k} = {v}' for k, v in A.items()) + '.', '',
        '## If an assumption is off', '',
        '| Change | Average wait (route by route → riders first) | Riders\' stops clear after 4 h | All stops clear |',
        '| --- | --- | --- | --- |',
        *[f"| {x['label']} | {x['route']['wait']} h → {x['riders']['wait']} h | {x['route']['h4']}% → {x['riders']['h4']}% "
          f"| {x['route']['finish']} h → {x['riders']['finish']} h |" for x in sens], '',
        '## How many crews?', '',
        '| Crews | Average wait (route by route → riders first) | All stops clear |', '| --- | --- | --- |',
        *[f"| {x['crews']} | {x['route']['wait']} h → {x['riders']['wait']} h | {x['route']['finish']} h → {x['riders']['finish']} h |" for x in crews_curve], '']
    open(os.path.join(OUT, 'summary.md'), 'w').write('\n'.join(lines))

    # ---- map.html ----
    payload = {
        'season': bs['season'], 'A': A, 'stats': S, 'total': total, 'half': half, 'sens': sens, 'crewsCurve': crews_curve,
        'nstops': len(stops), 'nmbta': len(mbta),
        'top3': {'names': [s['name'] for s in top[:3]], 'riders': sum(s['riders'] for s in top[:3]),
                 'quiet': max(k for k in range(len(top) + 1) if sum(s['riders'] for s in top[len(top) - k:]) < sum(s['riders'] for s in top[:3]))},
        'wards': [w['rings'] for w in wards],
        'routes': {k: v['paths'] for k, v in bs['routes'].items() if v['paths']},
        'nodes': {s['id']: [s['lon'], s['lat']] for s in allstops},
        'geo': {f'{a}|{b}': g for (a, b), g in GEO.items()},
        'away': sorted(f'{a}|{b}' for a, b in AWAY if b in G[a] and G[a][b][1] != 'drive'),
        'stops': [{'id': s['id'], 'n': s['name'], 'x': s['lon'], 'y': s['lat'], 'r': s['riders'], 'on': s['on'], 'off': s['off'], 'rt': s['routes'],
                   **{k: next({'h': round(e['h'], 2), 'c': c + 1} for c, day in enumerate(plans[k]) for e in day if e['stop'] == s['id']) for k in plans}} for s in stops],
        'mbta': [{'n': s['name'], 'x': s['lon'], 'y': s['lat'], 'r': s['riders']} for s in mbta],
        'days': {k: [[[e['stop'], e['path'], round(e['h'], 3), round(e['m'])] for e in day] for day in days] for k, days in plans.items()},
        'curve': {k: curve(v, total) for k, v in plans.items()},
    }
    tpl = open(os.path.join(HERE, 'map_template.html')).read()
    open(os.path.join(OUT, 'map.html'), 'w').write(tpl.replace('/*DATA*/null', json.dumps(payload, separators=(',', ':'))))
    # the same page on the public site (docs/ is served by GitHub Pages)
    shutil.copyfile(os.path.join(OUT, 'map.html'), os.path.join(ROOT, 'docs', 'bus-stops.html'))
    print('\n'.join(lines))
    print(f'street network: {sum(len(v) for v in G.values())} one-way links, {joins} pairs added to join separate pieces')
