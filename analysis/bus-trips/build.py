"""Where Somerville's bus riders get off: an estimate, drawn on a map of the whole routes.

The MBTA publishes, for every scheduled trip, how many people get on and off at each stop
(averages for one season), but not where each rider gets off. This script estimates it, trip by
trip: everyone on the bus is equally likely to get off at the next stop. At each stop, the people
getting off are taken from the people on board in proportion to where they got on; then the people
getting on join. Whoever is still on board at the last stop gets off there. Added up over every
trip of a day, that gives about how many riders go from each stop to each other stop on each route.

Routes: every bus route with a stop in Somerville in the ridership data (docs/snow/data/bus-stops.json),
drawn whole, through every city and town they serve.

Inputs (downloaded once into ../../.cache/, git-ignored; delete a file there to refresh it):
  MBTA Bus Ridership by Trip, Season, Route/Line, and Stop (MBTA open data), latest Fall season
  MBTA schedule (GTFS) from the MBTA's feed archive, the last one of that same season: stops,
    towns, route shapes, rapid transit lines and stations, so the map shows the routes as they ran
    when the riders were counted. A stop in the ridership file that the schedule doesn't have (the
    "Bennett Alley" layover before Harvard's upper busway) is counted at the next stop on its trip.
  MassGIS: Massachusetts municipalities with generalized coast (town outlines)
Output:
  output/trips.html, copied to ../../docs/bus-trips.html (the public page; don't edit the copy)

Run from the repo root: python3 analysis/bus-trips/build.py
Python standard library only.
"""
import csv, io, json, math, os, shutil, sys, time, urllib.parse, urllib.request, zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CACHE, OUT = os.path.join(ROOT, '.cache'), os.path.join(HERE, 'output')
UA = 'somersnow-bus-trips (PTAC; github.com/vitorpamplona/somersnow)'

RIDERSHIP = 'https://www.arcgis.com/sharing/rest/content/items/8daf4a33925a4df59183f860826d29ee/data'
FEEDS = 'https://cdn.mbta.com/archive/archived_feeds.txt'
# rivers, ponds and tidal water (MassDEP 1:25,000 water bodies): town lines run down the middle of the Charles and
# the Mystic, so the town outlines alone leave them out. POLY_CODE 1: reservoirs (Fresh Pond, Spot Pond); 6: rivers and
# ponds (Charles River, Alewife Brook); 8: tidal water (Mystic River, Chelsea River). The unnamed codes (2, 5, 7) look
# like marsh and wetland and are left out; so is the ocean itself (the town outlines already leave it out).
WATER = ('https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/'
         '1_25_000_USGS_MassDEP_Hydrography/FeatureServer/1/query')
# what's at each stop: MBTA Plan for Accessible Transit Infrastructure (PATI): accessibility status as of Jan 2024,
# and amenities (benches, trash cans, bike racks, blocked paths) from the 2017 survey. No shelters or real-time signs.
# what volunteers mapped at each stop: OpenStreetMap bus stops (shelter, bench, bin, lit, tactile paving, departures
# board), matched by MBTA stop number (ref), and each tag's year from the stop's edit history. ODbL, (c) OpenStreetMap
# contributors. Overpass servers come and go, so a few are tried in turn.
OVERPASS = ['https://overpass-api.de/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter']
OSM_API = 'https://api.openstreetmap.org/api/0.6/node/{}/history.json'
OSM_TAGS = ['shelter', 'bench', 'bin', 'lit', 'tactile_paving', 'departures_board']
PATI = 'https://services1.arcgis.com/ceiitspzDAHrdGO1/arcgis/rest/services/PATI_Bus_Stops/FeatureServer/0/query'
TOWNS = ('https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/'
         'Massachusetts_Municipalities_Hosted/FeatureServer/0/query')
DAYS = {'Wkdy': 'Weekday', 'Sat': 'Saturday', 'Sun': 'Sunday'}   # the file also has Friday on its own ('Fri'), left out
# the ridership file's route id -> the schedule's, where they differ: '194' is the schedule's '8993' ("89/93",
# Clarendon Hill - Haymarket via Sullivan, a supplemental early trip: same start times, 4:30 weekdays, 4:33 Sat, 5:16 Sun)
SCHEDULE_ID = {'194': '8993'}
FROM_SCHEDULE = {v: k for k, v in SCHEDULE_ID.items()}
RAPID = {'Red': '#DA291C', 'Orange': '#ED8B00', 'Green-B': '#00843D', 'Green-C': '#00843D',
         'Green-D': '#00843D', 'Green-E': '#00843D', 'Blue': '#003DA5'}
MIN_RIDERS = 0.05                                  # pairs under this many riders a day are left out (rounding)


def get(url, params=None, tries=4):
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=300) as r:
                return r.read()
        except Exception as e:                    # network hiccup: back off and retry
            if i == tries - 1:
                raise
            print(f'  retry {url[:70]}… ({e})', file=sys.stderr)
            time.sleep(2 ** (i + 1))


def cached(name, url, params=None, quiet=False):
    path = os.path.join(CACHE, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        if not quiet:
            print(f'  downloading {name}…', file=sys.stderr)
        blob = get(url, params)
        with open(path + '.part', 'wb') as f:
            f.write(blob)
        os.replace(path + '.part', path)
    return path


def gtfs(season):
    """The MBTA's archived schedule feed: the last one published for the ridership's season."""
    feeds = list(csv.DictReader(io.StringIO(get(FEEDS).decode('utf-8-sig'))))
    pick = [f for f in feeds if f['feed_version'].startswith(season + ',')]
    f = max(pick, key=lambda f: f['feed_start_date'])
    z = zipfile.ZipFile(cached(f"mbta-gtfs-{f['feed_start_date']}.zip", f['archive_url']))
    print(f"  schedule: {f['feed_version'].split(',')[0]}, from {f['feed_start_date']}", file=sys.stderr)
    return z, f['feed_start_date']


def table(z, name):
    return csv.DictReader(io.TextIOWrapper(z.open(name), encoding='utf-8-sig'))


def decode_polyline(s):
    pts, i, lat, lon = [], 0, 0, 0
    while i < len(s):
        vals = []
        for _ in range(2):
            shift = res = 0
            while True:
                b = ord(s[i]) - 63; i += 1
                res |= (b & 0x1f) << shift; shift += 5
                if b < 0x20:
                    break
            vals.append(~(res >> 1) if res & 1 else res >> 1)
        lat += vals[0]; lon += vals[1]
        pts.append((lon / 1e5, lat / 1e5))
    return pts


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    i, dmax = 0, -1
    for k in range(1, len(pts) - 1):
        d = abs(dy * pts[k][0] - dx * pts[k][1] + x2 * y1 - y2 * x1) / L
        if d > dmax:
            i, dmax = k, d
    if dmax <= tol:
        return [pts[0], pts[-1]]
    return simplify(pts[:i + 1], tol)[:-1] + simplify(pts[i:], tol)


def piece(pts, a, b):
    """The stretch of a route shape (lon, lat points) from the point nearest a to the point nearest b after it."""
    kx = 111320 * math.cos(math.radians(pts[0][1]))

    def near(p, start):
        best = (1e18, start, 0.0)
        for i in range(start, len(pts) - 1):
            (x1, y1), (x2, y2) = pts[i], pts[i + 1]
            vx, vy, wx, wy = (x2 - x1) * kx, (y2 - y1) * 110540, (p[0] - x1) * kx, (p[1] - y1) * 110540
            L = vx * vx + vy * vy
            t = max(0.0, min(1.0, (wx * vx + wy * vy) / L)) if L else 0.0
            d = math.hypot(wx - t * vx, wy - t * vy)
            if d < best[0]:
                best = (d, i, t)
        return best
    at = lambda i, t: (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t)
    d0, i0, t0 = near(a, 0)
    d1, i1, t1 = near(b, i0)
    if d0 > 60 or d1 > 60 or (i1, t1) <= (i0, t0):
        return None
    return [at(i0, t0)] + pts[i0 + 1:i1 + 1] + [at(i1, t1)]


def clip(ring, box):
    """A polygon ring cut to a box (Sutherland-Hodgman), so water far off the map isn't carried."""
    x0, y0, x1, y1 = box
    for inside, cut in ((lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
                        (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
                        (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
                        (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))):
        out = []
        for k, p in enumerate(ring):
            q = ring[k - 1]
            if inside(p):
                if not inside(q):
                    out.append(cut(q, p))
                out.append(p)
            elif inside(q):
                out.append(cut(q, p))
        ring = out
        if not ring:
            break
    return ring


def pati(box):
    """{stop id: [PATI records]} for every stop in the box (paged; cached in .cache). A stop with benches has one
    record with the count and one more per bench with its type and condition."""
    out, offset = defaultdict(list), 0
    while True:
        with open(cached(f'bus-trips-pati-{offset}.json', PATI, {
                'where': '1=1', 'geometry': ','.join(f'{v:.4f}' for v in box), 'geometryType': 'esriGeometryEnvelope',
                'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'outFields': '*', 'returnGeometry': 'false',
                'resultOffset': offset, 'f': 'json'})) as f:
            d = json.load(f)
        for ft in d.get('features', []):
            a = ft['attributes']
            out[str(a['Stop_ID'])].append(a)
        if not d.get('exceededTransferLimit') or not d.get('features'):
            return out
        offset += len(d['features'])


def amenities(recs):
    """A stop's PATI records, short: access status (2024) and what was there in 2017."""
    val = lambda k: next(((r.get(k) or '').strip() for r in recs if (r.get(k) or '').strip()), '')
    most = lambda k: max((r.get(k) or 0) for r in recs)
    benches = [f"{r['SeatType17'].strip().lower()} ({r['SeatCond17'].strip().lower()})" if (r.get('SeatCond17') or '').strip()
               else r['SeatType17'].strip().lower() for r in recs if (r.get('SeatType17') or '').strip()]
    n = max(most('SeatNum17'), len(benches))
    return {'p': val('PATI_Prior'), 'done': val('PATI_Prgrm') == 'PATI Complete', 'n': n, 'b': benches,
            't': most('Trash17') > 0, 'k': most('BikeRks17') > 0, 'x': any((r.get('BlkdPath17') or '').strip() == 'Yes' for r in recs)}


def osm_stops(box, want):
    """{MBTA stop id: {'id': node id, tag: [value, year the value was set]}} for the stops in `want` (id -> lon, lat)."""
    path = os.path.join(CACHE, 'bus-trips-osm.json')
    if not os.path.exists(path):
        q = (f'[out:json][timeout:120];node["highway"="bus_stop"]'
             f'({box[1]:.4f},{box[0]:.4f},{box[3]:.4f},{box[2]:.4f});out meta;')
        for url in OVERPASS:
            try:
                blob = get(url + '?' + urllib.parse.urlencode({'data': q}), tries=2)
                json.loads(blob)
                with open(path, 'wb') as f:
                    f.write(blob)
                break
            except Exception as e:
                print(f'  overpass {url[:40]}… failed ({e})', file=sys.stderr)
    if not os.path.exists(path):
        print('  OpenStreetMap: no server answered; the page shows the MBTA survey only', file=sys.stderr)
        return {}
    with open(path) as f:
        nodes = json.load(f)['elements']
    byref = {n['tags']['ref']: n for n in nodes if n.get('tags', {}).get('ref')}
    out = {}
    for sid, (lon, lat) in want.items():
        n = byref.get(sid)
        if not n:                                 # no MBTA number on the node: the nearest stop within 30 m
            near = min(nodes, key=lambda n: math.hypot((n['lon'] - lon) * 82000, (n['lat'] - lat) * 111000), default=None)
            if near and math.hypot((near['lon'] - lon) * 82000, (near['lat'] - lat) * 111000) < 30 and not near['tags'].get('ref'):
                n = near
        if not n or not any(k in n['tags'] for k in OSM_TAGS):
            if n:
                out[sid] = {'id': n['id']}
            continue
        name = f"osm-hist/{n['id']}-v{n['version']}.json"                     # refetched when the stop changes
        fresh = not os.path.exists(os.path.join(CACHE, name))
        hist = cached(name, OSM_API.format(n['id']), quiet=True)
        if fresh:
            time.sleep(0.3)                       # go easy on the OpenStreetMap API
        with open(hist) as f:
            vers = sorted(json.load(f)['elements'], key=lambda e: e['version'])
        rec = {'id': n['id']}
        for k in OSM_TAGS:
            v = n['tags'].get(k)
            if v is None:
                continue
            i = len(vers) - 1
            while i > 0 and vers[i - 1].get('tags', {}).get(k) == v:
                i -= 1
            rec[k] = [v, int(vers[i]['timestamp'][:4])]
        out[sid] = rec
    return out


def somerville_routes():
    with open(os.path.join(ROOT, 'docs', 'snow', 'data', 'bus-stops.json')) as f:
        d = json.load(f)
    return sorted({r for s in d['stops'] for r in s['routes']}, key=lambda r: (len(r), r))


def trips(routes):
    """{day: [(route, [(stop_id, on, off), ...] in stop order, direction, start minute), ...]} for the latest Fall season."""
    z = zipfile.ZipFile(cached('mbta-bus-ridership.zip', RIDERSHIP))
    name = sorted(n for n in z.namelist() if '_Fall_' in n and n.endswith('.csv'))[-1]
    season = 'Fall ' + name.rsplit('_', 1)[1][:4]
    rows = defaultdict(list)
    with z.open(name) as fh:
        for r in csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig')):
            if r['GTFS route_id'] in routes and r['Day Type'] in DAYS:
                key = (r['Day Type'], r['GTFS route_id'], r['GTFS direction_id'], r['trip start time'], r['Route/Variant'])
                rows[key].append((int(r['stop sequence']), r['GTFS stop_id'], float(r['Boardings'] or 0), float(r['Alightings'] or 0)))
    out = defaultdict(list)
    for (day, rid, dirn, start, _), rs in rows.items():
        rs.sort()
        out[day].append((rid, [(sid, on, off) for _, sid, on, off in rs], dirn, minutes(start)))
    return season, out


def minutes(t):
    """'25:30:00' -> 1530 (schedule times run past midnight)."""
    h, m, *_ = (int(x) for x in t.split(':'))
    return h * 60 + m


def by_hour(by_day, offset):
    """{day: {stop: [riders getting on in each clock hour 0..23] + [getting off, same]}}. The hour the bus is at a
    stop is the trip's start time plus the schedule's usual minutes from the first stop to that stop."""
    out = {}
    for day, tl in by_day.items():
        h = defaultdict(lambda: [0.0] * 48)
        for rid, stops, dirn, start in tl:
            last = 0
            for sid, on, off in stops:
                last = offset.get((rid, dirn, sid), last)
                hr = int((start + last) // 60) % 24
                h[sid][hr] += on; h[sid][24 + hr] += off
        out[day] = h
    return out


def merge_unknown(by_day, known):
    """A stop the schedule doesn't have is counted at the next stop on its trip (the last one: the stop before)."""
    moved = defaultdict(float)
    for day, tl in by_day.items():
        for k, (rid, stops, *rest) in enumerate(tl):
            out = []
            carry_on = carry_off = 0.0
            for sid, on, off in stops:
                if sid not in known:
                    carry_on += on; carry_off += off; moved[sid] += on + off
                    continue
                out.append([sid, on + carry_on, off + carry_off]); carry_on = carry_off = 0.0
            if out and (carry_on or carry_off):
                out[-1][1] += carry_on; out[-1][2] += carry_off
            tl[k] = (rid, [tuple(x) for x in out], *rest)
    return moved


def estimate(trip_list):
    """{(from_stop, to_stop, route, direction): riders a day}. On each trip, the people getting off at a stop
    are a mix of everyone on board, in proportion to where they got on."""
    od = defaultdict(float)
    for rid, stops, dirn, _ in trip_list:
        aboard = {}                               # stop they got on -> riders still on board
        for sid, on, off in stops:
            total = sum(aboard.values())
            if total > 0 and off > 0:
                k = min(1.0, off / total)
                for o in list(aboard):
                    n = aboard[o] * k
                    if o != sid:
                        od[(o, sid, rid, dirn)] += n
                    aboard[o] -= n
            if on > 0:
                aboard[sid] = aboard.get(sid, 0) + on
        last = stops[-1][0]
        for o, n in aboard.items():               # still on board at the end of the trip
            if n > 1e-9 and o != last:
                od[(o, last, rid, dirn)] += n
    return od


def main():
    routes = somerville_routes()
    print('routes:', ', '.join(routes))
    season, by_day = trips(set(routes))
    z, feed = gtfs(season)
    stopinfo = {r['stop_id']: r for r in table(z, 'stops.txt')}
    moved = merge_unknown(by_day, stopinfo)
    if moved:
        print('  counted at the next stop (no location in the schedule): ' + ', '.join(f'{k} ({v:.0f} a day, all days)' for k, v in moved.items()), file=sys.stderr)
    od = {day: estimate(by_day[day]) for day in DAYS}

    # route patterns, their representative trips and shapes
    patterns = [{**p, 'route_id': FROM_SCHEDULE.get(p['route_id'], p['route_id'])} for p in table(z, 'route_patterns.txt')]
    want_trips = {p['representative_trip_id'] for p in patterns if p['route_id'] in routes or p['route_id'] in RAPID}
    trip_shape = {t['trip_id']: t['shape_id'] for t in table(z, 'trips.txt') if t['trip_id'] in want_trips}
    want_shapes = set(trip_shape.values())
    shape_pts = defaultdict(list)
    for r in table(z, 'shapes.txt'):
        if r['shape_id'] in want_shapes:
            shape_pts[r['shape_id']].append((int(r['shape_pt_sequence']), float(r['shape_pt_lon']), float(r['shape_pt_lat'])))
    shape = {k: [(x, y) for _, x, y in sorted(v)] for k, v in shape_pts.items()}
    route_trip = {t['trip_id']: (FROM_SCHEDULE.get(t['route_id'], t['route_id']), t['direction_id']) for t in table(z, 'trips.txt')
                  if FROM_SCHEDULE.get(t['route_id'], t['route_id']) in routes}
    trip_stops, times = defaultdict(list), defaultdict(list)
    for r in table(z, 'stop_times.txt'):
        if r['trip_id'] in want_trips:
            trip_stops[r['trip_id']].append(r['stop_id'])
        if r['trip_id'] in route_trip and r['arrival_time']:
            times[r['trip_id']].append((int(r['stop_sequence']), r['stop_id'], minutes(r['arrival_time'])))
    per = defaultdict(list)
    for t, rows in times.items():
        rows.sort()
        rid, dirn = route_trip[t]
        for _, sid, m in rows:
            per[(rid, dirn, sid)].append(m - rows[0][2])
    offset = {k: sorted(v)[len(v) // 2] for k, v in per.items()}
    hours = by_hour(by_day, offset)

    # stops: every stop on the routes' patterns, and every stop in the ridership file
    stop_routes = defaultdict(set)
    for p in patterns:
        if p['route_id'] in routes:
            for sid in trip_stops.get(p['representative_trip_id'], []):
                stop_routes[sid].add(p['route_id'])
    for day_trips in by_day.values():
        for rid, stops, *_ in day_trips:
            for sid, *_ in stops:
                stop_routes[sid].add(rid)
    meta = {s: stopinfo[s] for s in stop_routes}
    lons = [float(a['stop_lon']) for a in meta.values()]
    lats = [float(a['stop_lat']) for a in meta.values()]
    LON0, LAT0 = (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2
    KX, KY = 111320 * math.cos(math.radians(LAT0)), 110540

    def xy(lon, lat):
        return [round((lon - LON0) * KX), round((LAT0 - lat) * KY)]

    # route shapes, whole, both directions: the usual patterns and branches (typicality 1 and 2), plus any rarer
    # pattern that serves a stop none of those reach (a school trip, a garage trip)
    names = {r['route_id']: r for r in table(z, 'routes.txt')}
    mine = [p for p in patterns if p['route_id'] in routes]
    covered = {sid for p in mine if p['route_pattern_typicality'] in ('1', '2') for sid in trip_stops.get(p['representative_trip_id'], [])}
    drawn = {p['route_pattern_id'] for p in mine if p['route_pattern_typicality'] in ('1', '2')
             or set(trip_stops.get(p['representative_trip_id'], [])) - covered}
    rshapes = []
    for rid in routes:
        paths = []
        for p in patterns:
            if p['route_id'] == rid and p['route_pattern_id'] in drawn:
                pts = shape.get(trip_shape.get(p['representative_trip_id']))
                if pts:
                    paths.append([xy(*q) for q in simplify(pts, 0.00005)])
        straight = False
        if not paths:                             # no shape in the schedule (the 194): join its stops in trip order
            longest = {}
            for day_trips in by_day.values():
                for r, stops, dirn, _ in day_trips:
                    if r == rid and len(stops) > len(longest.get(dirn, [])):
                        longest[dirn] = stops
            paths = [[xy(float(stopinfo[sid]['stop_lon']), float(stopinfo[sid]['stop_lat'])) for sid, *_ in st] for st in longest.values()]
            straight = True
        a = names.get(SCHEDULE_ID.get(rid, rid), {})
        rshapes.append({'id': rid, 'name': a.get('route_short_name') or rid, 'long': a.get('route_long_name', ''), 'paths': paths,
                        **({'straight': True} if straight else {})})

    # the map's extent: every stop, plus a margin
    pad = 0.012
    box = (min(lons) - pad, min(lats) - pad, max(lons) + pad, max(lats) + pad)

    # rapid transit, clipped to the map
    def inbox(lon, lat):
        return box[0] <= lon <= box[2] and box[1] <= lat <= box[3]
    rapid = []
    for rid, color in RAPID.items():
        paths, stations = [], {}
        for p in patterns:
            if p['route_id'] != rid or p['route_pattern_typicality'] != '1' or p['direction_id'] != '0':
                continue
            run = []
            for q in shape.get(trip_shape.get(p['representative_trip_id']), []):
                if inbox(*q):
                    run.append(q)
                elif run:
                    paths.append(run); run = []
            if run:
                paths.append(run)
            for sid in trip_stops.get(p['representative_trip_id'], []):
                st = stopinfo.get(stopinfo[sid].get('parent_station') or sid, stopinfo[sid])
                lon, lat = float(st['stop_lon']), float(st['stop_lat'])
                if inbox(lon, lat):
                    stations[st['stop_id']] = {'n': st['stop_name'], 'p': xy(lon, lat)}
        if paths:
            rapid.append({'id': rid, 'color': color, 'paths': [[xy(*q) for q in simplify(r, 0.00004)] for r in paths if len(r) > 1],
                          'stations': list(stations.values())})

    # towns
    with open(cached('bus-trips-towns.json', TOWNS, {
            'where': '1=1', 'geometry': ','.join(f'{v:.4f}' for v in box), 'geometryType': 'esriGeometryEnvelope',
            'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'TOWN', 'outSR': 4326,
            'maxAllowableOffset': 0.0002, 'f': 'json'})) as f:
        tj = json.load(f)
    towns = []
    for ft in tj['features']:
        rings = [[xy(*q) for q in r] for r in ft['geometry']['rings'] if len(r) > 3]
        towns.append({'n': ft['attributes']['TOWN'].title(), 'rings': rings})

    # water, cut to the map
    with open(cached('bus-trips-water.json', WATER, {
            'where': 'POLY_CODE IN (1,6,8) AND Shape__Area > 5000 AND Shape__Area < 1e9',
            'geometry': ','.join(f'{v:.4f}' for v in box), 'geometryType': 'esriGeometryEnvelope', 'inSR': 4326,
            'spatialRel': 'esriSpatialRelIntersects', 'outFields': 'NAME', 'outSR': 4326,
            'maxAllowableOffset': 0.00008, 'f': 'json'})) as f:
        wj = json.load(f)
    water = []
    for ft in wj['features']:
        for r in ft['geometry']['rings']:
            r = clip(r, box)
            if len(r) > 3:
                water.append([xy(*q) for q in r])

    pati_at = pati(box)
    osm_at = osm_stops(box, {s: (float(meta[s]['stop_lon']), float(meta[s]['stop_lat'])) for s in meta})

    # stops in the page: only those with a location; ids become indexes
    ids = sorted(meta, key=lambda s: (meta[s]['stop_name'], s))
    ix = {s: i for i, s in enumerate(ids)}
    ri = {r: i for i, r in enumerate(routes)}
    stops = [{'id': s, 'n': meta[s]['stop_name'], 't': meta[s].get('municipality') or '', 'p': xy(float(meta[s]['stop_lon']), float(meta[s]['stop_lat'])),
              'r': sorted(ri[r] for r in stop_routes[s]), 'w': int(meta[s].get('wheelchair_boarding') or 0),
              **({'a': amenities(pati_at[s])} if s in pati_at else {}), **({'o': osm_at[s]} if s in osm_at else {})} for s in ids]
    print(f'  PATI: {sum(1 for s in ids if s in pati_at)} of {len(ids)} stops; OpenStreetMap: {len(osm_at)} matched, '
          f'{sum(1 for v in osm_at.values() if "shelter" in v)} with a shelter tag', file=sys.stderr)
    # each route's two directions, named by where the bus is headed (the schedule's direction destination)
    dest = {(FROM_SCHEDULE.get(r['route_id'], r['route_id']), r['direction_id']): r['direction_destination']
            for r in table(z, 'directions.txt')}
    combos = sorted({(rid, dirn) for tl in by_day.values() for rid, _, dirn, _ in tl}, key=lambda k: (ri[k[0]], k[1]))
    rdi = {k: i for i, k in enumerate(combos)}
    rd = [[ri[rid], int(dirn), dest.get((rid, dirn), '')] for rid, dirn in combos]
    # which directions stop at each stop, and the stop the bus goes to next (the most common one)
    nxt = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for tl in by_day.values():
        for rid, seq, dirn, _ in tl:
            for k, (sid, *_) in enumerate(seq):
                nxt[sid][rdi[(rid, dirn)]][seq[k + 1][0] if k + 1 < len(seq) else None] += 1
    # and the stretch of the route's own shape from the stop to that next stop, so the map's arrow follows the street
    pat_shapes = defaultdict(list)                # (route, direction) -> shapes of its patterns, usual ones first
    for p in sorted(patterns, key=lambda p: p['route_pattern_typicality']):
        pts = shape.get(trip_shape.get(p['representative_trip_id']))
        if p['route_id'] in routes and pts:
            pat_shapes[(p['route_id'], p['direction_id'])].append((set(trip_stops.get(p['representative_trip_id'], [])), pts))
    ll = lambda sid: (float(stopinfo[sid]['stop_lon']), float(stopinfo[sid]['stop_lat']))
    traced = 0
    for st in stops:
        st['d'] = []
        for k, c in sorted(nxt[st['id']].items()):
            nsid = max(c, key=c.get)
            path = None
            if nsid:
                rid, dirn = combos[k]
                for served, pts in pat_shapes.get((rid, dirn), []):
                    if st['id'] in served and nsid in served:
                        path = piece(pts, ll(st['id']), ll(nsid))
                        if path:
                            break
            traced += bool(path)
            st['d'].append([k, ix.get(nsid, -1) if nsid else -1] + ([[xy(*q) for q in simplify(path, 0.00002)]] if path else []))
    print(f'  arrows along the route: {traced} of {sum(len(st["d"]) for st in stops)} stop directions', file=sys.stderr)
    flows, totals = {}, {}
    for day, d in od.items():
        per = defaultdict(list)
        for (a, b, rid, dirn), n in d.items():
            if n >= MIN_RIDERS and a in ix and b in ix:
                per[ix[a]].append([ix[b], rdi[(rid, dirn)], round(n * 10)])
        flows[day] = {str(k): sorted(v, key=lambda e: -e[2]) for k, v in per.items()}
        totals[day] = round(sum(n for n in d.values()))
    hourly = {day: {str(ix[sid]): [round(x * 10) for x in v] for sid, v in h.items() if sid in ix and sum(v) >= 0.05}
              for day, h in hours.items()}
    payload = {'season': season, 'feed': feed, 'days': DAYS, 'hours': hourly, 'routes': rshapes, 'rd': rd, 'rapid': rapid, 'towns': towns, 'water': water,
               'stops': stops, 'flows': flows, 'totals': totals}
    blob = json.dumps(payload, separators=(',', ':'))
    with open(os.path.join(HERE, 'trips_template.html')) as f:
        page = f.read().replace('/*DATA*/null', blob)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'trips.html'), 'w') as f:
        f.write(page)
    shutil.copy(os.path.join(OUT, 'trips.html'), os.path.join(ROOT, 'docs', 'bus-trips.html'))
    pairs = sum(len(v) for d in flows.values() for v in d.values())
    print(f'{season}: {len(stops)} stops, {len(rshapes)} routes, {len(towns)} towns, {pairs} stop pairs; '
          f'riders a day: ' + ', '.join(f'{DAYS[d]} {totals[d]:,}' for d in DAYS) + f'; page {len(page) // 1024} KB')


if __name__ == '__main__':
    main()
