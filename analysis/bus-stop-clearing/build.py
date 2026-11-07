#!/usr/bin/env python3
"""Bus stop clearing: a page where a DPW operator designs each crew's route and sees how good
it is.

This script builds the street network the crews drive on, from the MBTA bus routes, and writes
it with the stops and their riders into one self-contained page (output/map.html, copied to
docs/bus-stops.html). The page does the rest in the browser: the operator picks each crew's
stops in order, sets the assumptions (minutes a stop, bobcat speed, time to cross the road,
...), and the page plays the day and scores it. Routes and settings are saved in the browser.

The street network:
  * each direction of a bus route is its own one-way leg; a stop belongs to the leg it stands on
    the right of (buses stop on the right), and to every leg that passes it;
  * each stop links to the next stop on its leg, in the bus's direction, at the route's length
    (not when they're more than 900 m apart: stops must be missing in between);
  * a crew may also drive back along a leg (against the bus) to get somewhere;
  * stops within 60 m of each other are across the street: crossing costs extra minutes, set
    on the page; so does turning where a leg leaves the city, like the bus;
  * pieces that still can't reach each other are joined at their closest stops.

Inputs (the first two copied into data/ by this script so the folder is self-contained):
  ../../docs/data/bus-stops.json  MBTA stops in Somerville, Fall weekday boardings and alightings, routes
  ../../docs/data/wards.json      ward outlines, for the map
  data/computed-plan.json         the plan an earlier version of this script computed (riders first, one
                                  street at a time, commit 3cc3f4d): the page's starting plan

Run from the repo root:  python3 analysis/bus-stop-clearing/build.py
"""
import json, math, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
DATA, OUT = os.path.join(HERE, 'data'), os.path.join(HERE, 'output')

# ---------- how the street network is built (the page's own settings are set on the page) ----------
A = {
    'cross_m': 60,              # stops this close are across the street from each other
    'max_link_m': 900,          # longer gaps between stops on a route mean stops are missing in between: no link
    'on_route_m': 25,           # a stop this close to a leg is on it (branches share streets)
    'mbta_routes': ['109'],     # the MBTA clears every stop on these routes itself (mbta.com winter page)
}

# defaults for the page's settings (the operator changes them there; they're saved in the browser)
SETTINGS = {
    'crews': 4,                 # the City's snow page lists "4 Routes"
    'service_min': 20,          # minutes to clear one stop: boarding area, shelter, bench
    'mph': 5,                   # bobcat driving speed
    'cross_min': 1,             # crossing the road to the stop on the other side (or turning at the city line)
    'jump_m': 800,              # a drive longer than this to the next stop is a jump to a different place
    'count_off': True,          # count people getting off as well as people getting on
    'include_mbta': False,      # also clear the stops the MBTA clears (route 109)
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
    street is a 'turn' (the page adds its crossing minutes), and so is the end of a leg, where the
    bus leaves the city: the crew turns to the nearest stop of the same route's other direction.
    A crew may drive back along a leg ('back'). Where the network can't get from one part to
    another, the closest stops are joined both ways ('join'). G[a][b] = (meters, kind)."""
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
    for a in list(G):                             # a crew may drive back along a street to get somewhere
        for b, (m, kind) in list(G[a].items()):
            if kind == 'drive' and a not in G[b]:
                G[b][a] = (m, 'back')
                if (a, b) in GEO:
                    GEO[(b, a)] = GEO[(a, b)][::-1]
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
    """Minutes for one link at the default settings (only to keep the quicker of two links)."""
    return m / (SETTINGS['mph'] * 1609 / 60) + (SETTINGS['cross_min'] if kind == 'turn' else 0)


def turn_cost_links(G):
    """Every link as [from, to, meters, kind]: drive (the bus's direction), back (against it),
    turn (across the street, or turning at the city line) and join."""
    return [[a, b, round(m), kind] for a in sorted(G) for b, (m, kind) in sorted(G[a].items())]


if __name__ == '__main__':
    os.makedirs(DATA, exist_ok=True); os.makedirs(OUT, exist_ok=True)
    for f in ('bus-stops.json', 'wards.json'):
        shutil.copyfile(os.path.join(ROOT, 'docs', 'data', f), os.path.join(DATA, f))
    bs = json.load(open(os.path.join(DATA, 'bus-stops.json')))
    wards = json.load(open(os.path.join(DATA, 'wards.json')))['wards']
    allstops = bs['stops']
    P = {s['id']: (s['lon'], s['lat']) for s in allstops}
    G, joins = street_network(allstops, bs['routes'])
    # the plan the earlier version of this script computed (riders first, one street at a time): the starting plan
    base = json.load(open(os.path.join(DATA, 'computed-plan.json')))
    payload = {
        'season': bs['season'], 'A': A, 'settings': SETTINGS, 'base': {'name': base['name'], 'routes': base['routes']},
        'wards': [w['rings'] for w in wards],
        'routes': {k: v['paths'] for k, v in bs['routes'].items() if v['paths']},
        'stops': [{'id': s['id'], 'n': s['name'], 'x': s['lon'], 'y': s['lat'], 'on': s['riders'], 'off': s['off'],
                   'rt': s['routes'], 'mbta': bool(set(s['routes']) & set(A['mbta_routes']))} for s in allstops],
        'links': turn_cost_links(G),
        'geo': {f'{a}|{b}': g for (a, b), g in GEO.items()},
        'away': sorted(f'{a}|{b}' for a, b in AWAY if b in G[a] and G[a][b][1] != 'drive'),
    }
    tpl = open(os.path.join(HERE, 'map_template.html')).read()
    open(os.path.join(OUT, 'map.html'), 'w').write(tpl.replace('/*DATA*/null', json.dumps(payload, separators=(',', ':'))))
    # the same page on the public site (docs/ is served by GitHub Pages)
    shutil.copyfile(os.path.join(OUT, 'map.html'), os.path.join(ROOT, 'docs', 'bus-stops.html'))
    print(f'{len(allstops)} stops; street network: {sum(len(v) for v in G.values())} one-way links, '
          f'{joins} pairs added to join separate pieces; wrote output/map.html and docs/bus-stops.html')
