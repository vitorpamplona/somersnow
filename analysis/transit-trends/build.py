"""Transit in Somerville over time: weekday boardings at Somerville's bus stops and at the T stations its people use,
every fall season the MBTA has published. Writes output/trends.html, copied to ../../docs/transit-trends.html.

Python standard library only. Run from the repo root: npm run trends (or python3 analysis/transit-trends/build.py).
Downloads are cached in ../../.cache/ (the bus ridership file is shared with analysis/bus-trips).

Sources (all public, no keys):
  - MBTA Bus Ridership by Trip, Season, Route/Line and Stop: average boardings and alightings per scheduled trip and
    stop, every fall from 2016 (ArcGIS item 8daf4a33925a4df59183f860826d29ee).
  - The MBTA schedule (GTFS) archive: each season's stop locations, read from the last feed of that season with HTTP
    range requests (only stops.txt is fetched, not the whole feed).
  - MassGIS municipalities: the Somerville outline (a stop is in Somerville if it's inside it) and its neighbors.
  - MBTA rail ridership: Fall 2017-2019 by time period (item 9fea7862...), Fall 2023 by time period (80a379eb...),
    Fall 2024 by hour (8f20b4e8...), Fall 2025 by hour (6494749a..., CSV). No rail files for Fall 2020-2022.
"""
import csv, gzip, io, json, math, os, re, shutil, sys, urllib.error, urllib.parse, urllib.request, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
CACHE = os.path.join(ROOT, '.cache')
OUT = os.path.join(HERE, 'output')
UA = 'somerwalks-transit-trends (PTAC; github.com/vitorpamplona/somerwalks)'

RIDERSHIP = 'https://www.arcgis.com/sharing/rest/content/items/8daf4a33925a4df59183f860826d29ee/data'
FEEDS = 'https://cdn.mbta.com/archive/archived_feeds.txt'
TOWNS = ('https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/'
         'Massachusetts_Municipalities_Hosted/FeatureServer/0/query')
NEIGHBORS = ['SOMERVILLE', 'CAMBRIDGE', 'MEDFORD', 'ARLINGTON', 'EVERETT', 'BOSTON', 'MALDEN']
RAIL_ITEMS = {  # season -> (ArcGIS item, kind)
    'Fall 2017': ('9fea7862501f4c59ab2c001ad6ae19b0', 'old'), 'Fall 2018': ('9fea7862501f4c59ab2c001ad6ae19b0', 'old'),
    'Fall 2019': ('9fea7862501f4c59ab2c001ad6ae19b0', 'old'), 'Fall 2023': ('80a379ebaa374cfd836ca4d3880ceda4', 'service'),
    'Fall 2024': ('8f20b4e8d24e466fbca157cca63f6e16', 'service'), 'Fall 2025': ('6494749a29c648018820d0e49636205c', 'csv'),
}
# The T stations people in Somerville use: the seven inside the city, plus Porter (Cambridge, at the city line) and
# Sullivan Square (Charlestown, where many Somerville buses end). Lechmere is left out: it's close
# to the city line (about 220 m), but the Somerville land next to it is industrial rather than homes, and few in
# Somerville use it as their station.
STATIONS = [
    ('place-davis', 'Davis', 'Red', True), ('place-portr', 'Porter', 'Red', False),
    ('place-astao', 'Assembly', 'Orange', True), ('place-sull', 'Sullivan Square', 'Orange', False),
    ('place-unsqu', 'Union Square', 'Green', True), ('place-esomr', 'East Somerville', 'Green', True),
    ('place-gilmn', 'Gilman Square', 'Green', True), ('place-mgngl', 'Magoun Square', 'Green', True),
    ('place-balsq', 'Ball Square', 'Green', True),
]
OLD_NAMES = {'Davis': 'place-davis', 'Porter': 'place-portr', 'Assembly': 'place-astao', 'Sullivan Square': 'place-sull'}
ROUTE_NAME = {'747': 'CT2', '194': '89/93'}
ROUTE_ID = {v: k for k, v in ROUTE_NAME.items()}
ROUTE_NAME_TIMES = {'747': 'CT2'}                         # route ids in the arrival-time files
BIKES = 'https://s3.amazonaws.com/hubway-data/'      # Bluebikes (Hubway until 2018) monthly trip files
BIKE_MONTHS = (9, 10, 11)                            # "fall" for bikes: September to November
ACS_TABLE = 'https://data.census.gov/api/access/data/table'   # Census tables, no key; Somerville city = 160XX00US2562535
LODES = 'https://lehd.ces.census.gov/data/lodes/LODES8/ma/{kind}/ma_{kind}_S000_JT00_{year}.csv.gz'
LODES_XWALK = 'https://lehd.ces.census.gov/data/lodes/LODES8/ma/ma_xwalk.csv.gz'   # census block → town
FIRST_YEAR = 2015
SAME_STOP = 12                                    # metres: stop ids this close are one place on the map
MIN_ROUTE = 50                                    # routes with fewer weekday riders in Somerville every season are left out


def get(url, params=None, tries=4, headers=None):
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - retry anything, then give up loudly
            if k == tries - 1:
                raise
            print(f'  retry {url[:80]}: {e}', file=sys.stderr)


def cached(name, url, params=None):
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        blob = get(url, params)
        with open(path, 'wb') as f:
            f.write(blob)
    return path


class RemoteFile(io.RawIOBase):
    """A file on a web server read with HTTP range requests, so zipfile can pull one member out of a big archive."""
    def __init__(self, url):
        self.url, self.pos = url, 0
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': UA})
        self.size = int(urllib.request.urlopen(req, timeout=60).headers['Content-Length'])

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def readinto(self, b):
        n = min(len(b), self.size - self.pos)
        if n <= 0:
            return 0
        data = get(self.url, headers={'Range': f'bytes={self.pos}-{self.pos + n - 1}'})
        b[:len(data)] = data
        self.pos += len(data)
        return len(data)


def season_stops(feed_date, url):
    """{stop_id: [lon, lat, name]} from one archived feed's stops.txt, cached as JSON."""
    path = os.path.join(CACHE, f'gtfs-stops-{feed_date}.json')
    if not os.path.exists(path):
        z = zipfile.ZipFile(io.BufferedReader(RemoteFile(url), buffer_size=1 << 20))
        out = {}
        for r in csv.DictReader(io.TextIOWrapper(z.open('stops.txt'), encoding='utf-8-sig')):
            if r.get('stop_lat'):
                out[r['stop_id']] = [round(float(r['stop_lon']), 6), round(float(r['stop_lat']), 6), r['stop_name']]
        os.makedirs(CACHE, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(out, f)
    with open(path) as f:
        return json.load(f)


def fall_feeds():
    """{year: (feed_start_date, archive_url)}: the last feed published for each fall season."""
    pick = {}
    for r in csv.DictReader(io.StringIO(get(FEEDS).decode('utf-8-sig'))):
        v = r['feed_version']
        if v.startswith('Fall '):
            y = int(v[5:9])
            if y not in pick or r['feed_start_date'] > pick[y][0]:
                pick[y] = (r['feed_start_date'], r['archive_url'])
    return pick


def inside(rings, x, y):
    hit = False
    for ring in rings:
        j = len(ring) - 1
        for i in range(len(ring)):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                hit = not hit
            j = i
    return hit


def towns():
    path = cached('trends-towns.geojson', TOWNS, {
        'where': 'TOWN IN (' + ','.join(f"'{t}'" for t in NEIGHBORS) + ')', 'outFields': 'TOWN', 'outSR': 4326,
        'maxAllowableOffset': 0.0002, 'f': 'geojson'})
    with open(path) as f:
        g = json.load(f)
    out = {}
    for ft in g['features']:
        geom = ft['geometry']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        out[ft['properties']['TOWN'].title()] = [ring for poly in polys for ring in poly]
    return out


def somerville_exact():
    """Somerville's outline at full detail, for deciding what's inside. The map's simplified outline (about 20 m) put a
    Cambridge Bluebikes dock (Inman Square at Springfield St) inside the city in 2019 and 2020."""
    path = cached('trends-somerville-exact.geojson', TOWNS, {"where": "TOWN = 'SOMERVILLE'", 'outFields': 'TOWN',
                                                             'outSR': 4326, 'f': 'geojson'})
    with open(path) as f:
        g = json.load(f)
    rings = []
    for ft in g['features']:
        geom = ft['geometry']
        for poly in (geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]):
            rings += poly
    return rings


def start_min(t):
    """Minutes after midnight a trip starts ("7:05:00", or a fraction of a day like 0.538 in some Fall 2025 rows)."""
    t = t.strip()
    if ':' in t:
        h, m = t.split(':')[:2]
        return int(h) * 60 + int(m)
    return int(round(float(t) * 1440))


def start_hour(t):
    """Hour a trip starts, from "7:05:00" or (some rows of the Fall 2025 file) a fraction of a day like 0.538."""
    t = t.strip()
    return int(t.split(':')[0]) if ':' in t else int(float(t) * 24)


# the ridership file's columns, by year (the names changed in Fall 2024 and Fall 2025)
COLS = {'route': ('route_id', 'GTFS route_id'), 'stop': ('stop_id', 'GTFS stop_id'), 'day': ('day_type_name', 'Day Type'),
        'on': ('boardings', 'Boardings'), 'off': ('alightings', 'Alightings'), 'start': ('trip_start_time', 'trip start time'),
        'name': ('stop_name', 'Stop Name'), 'variant': ('route_variant', 'Route/Variant'), 'dir': ('direction_id', 'GTFS direction_id'),
        'load': ('load_', 'load', 'Load'), 'samples': ('sample_size', 'sample_count', '# of Trip Samples ')}


def bus(som_rings):
    """Per fall season: weekday/Saturday/Sunday boardings in Somerville and systemwide; weekday by route, by stop and by
    the hour the trip started."""
    z = zipfile.ZipFile(cached('mbta-bus-ridership.zip', RIDERSHIP))
    feeds = fall_feeds()
    DAY = {'weekday': 'wk', 'Wkdy': 'wk', 'Fri': 'fri', 'saturday': 'sat', 'Sat': 'sat', 'sunday': 'sun', 'Sun': 'sun'}
    seasons, stops_all = {}, {}
    files = sorted(n for n in z.namelist() if n.endswith('.csv') and '_Fall_' in n)
    years = [int(n.rsplit('_', 1)[1][:4]) for n in files]
    feed_locs = {y: season_stops(*feeds[y]) for y in years}
    for n, year in zip(files, years):
        # The fall's last feed can miss stops that had riders earlier that fall (a detour, a stop closed in Nov): use
        # the same stop id from the nearest other fall's feed, then this fall's own on top.
        locs = {}
        for y in sorted(years, key=lambda y: -abs(y - year)):
            locs.update(feed_locs[y])
        som = {s for s, (x, y, _) in locs.items() if inside(som_rings, x, y)}
        r = csv.DictReader(io.TextIOWrapper(z.open(n), encoding='utf-8-sig'))
        col = {k: next(c for c in v if c in r.fieldnames) for k, v in COLS.items()}
        tot = defaultdict(Counter)                     # day -> {'som','sys','som_off'}
        route = defaultdict(Counter)                   # day -> route -> riders (wk, fri)
        stop = defaultdict(Counter)
        hour = defaultdict(Counter)
        names, unknown = {}, 0.0
        trips = defaultdict(set)                       # route -> weekday trips that stop in Somerville (Mon-Thu from 2025)
        for row in r:
            d = DAY.get(row[col['day']])
            if not d:
                continue
            on = float(row[col['on']] or 0)
            off = float(row[col['off']] or 0)
            sid = row[col['stop']]
            tot[d]['sys'] += on
            if sid not in locs:
                unknown += on
            if sid in som:
                tot[d]['som'] += on
                tot[d]['som_off'] += off
                if d in ('wk', 'fri'):
                    rt = ROUTE_NAME.get(row[col['route']].strip(), row[col['route']].strip())
                    route[d][rt] += on
                    if d == 'wk':
                        trips[rt].add((row[col['variant']], row[col['dir']], row[col['start']]))
                    stop[d][sid] += on
                    h = start_hour(row[col['start']])
                    hour[d][h if h >= 3 else h + 24] += on
                    names[sid] = row[col['name']]
        # Fall 2025 on: "Wkdy" is Monday to Thursday and Friday is its own day type; combine them as a Monday-Friday
        # average (4 to 1) so every season means the same thing.
        def wkavg(c_wk, c_fri):
            if not c_fri:
                return c_wk
            keys = set(c_wk) | set(c_fri)
            return Counter({k: (4 * c_wk[k] + c_fri[k]) / 5 for k in keys})
        wk = wkavg(tot['wk'], tot.get('fri'))
        s = f'Fall {year}'
        seasons[s] = {
            'som': {'wk': round(wk['som']), 'sat': round(tot['sat']['som']), 'sun': round(tot['sun']['som'])},
            'sys': {'wk': round(wk['sys']), 'sat': round(tot['sat']['sys']), 'sun': round(tot['sun']['sys'])},
            'off': round(wk['som_off']),
            'routes': {k: round(v) for k, v in wkavg(route['wk'], route.get('fri')).items() if v >= 0.5},
            'trips': {k: len(v) for k, v in trips.items()},
            'locs': locs,
            'stops': {k: round(v, 1) for k, v in wkavg(stop['wk'], stop.get('fri')).items() if v >= 0.05},
            'hours': [round(wkavg(hour['wk'], hour.get('fri'))[h]) for h in range(4, 28)],
            'nstops': len([1 for v in wkavg(stop['wk'], stop.get('fri')).values() if v >= 0.05]),
            'unmatched': round(100 * unknown / max(1, sum(tot[d]['sys'] for d in tot)), 2),
        }
        for sid in seasons[s]['stops']:
            x, y, gname = locs[sid]
            stops_all[sid] = [x, y, gname]                # newest season wins (files are read oldest first)
        print(f"  {s}: Somerville {seasons[s]['som']['wk']:,} a weekday at {seasons[s]['nstops']} stops; "
              f"all MBTA buses {seasons[s]['sys']['wk']:,}; unmatched stops {seasons[s]['unmatched']}%", file=sys.stderr)
    return seasons, stops_all


def holidays(y):
    """Federal holidays in September to November: Labor Day, Columbus/Indigenous Peoples' Day, Veterans Day,
    Thanksgiving and the Friday after (people ride differently on them)."""
    def nth(month, weekday, n):
        d = date(y, month, 1)
        d += timedelta((weekday - d.weekday()) % 7)
        return d + timedelta(7 * (n - 1))
    thanks = nth(11, 3, 4)
    vets = date(y, 11, 11)
    vets += timedelta({5: -1, 6: 1}.get(vets.weekday(), 0))     # observed on Friday or Monday when it falls on a weekend
    return {nth(9, 0, 1), nth(10, 0, 2), vets, thanks, thanks + timedelta(1)}


def places(pts, metres=40):
    """How many distinct places a list of (lon, lat, ...) points makes: ids renumbered at the same dock count once."""
    kept = []
    for x, y, *_ in pts:
        kx = 111320 * math.cos(math.radians(y))
        if all(math.hypot((x - a) * kx, (y - b) * 110540) > metres for a, b in kept):
            kept.append((x, y))
    return len(kept)


def bluebikes(som_rings, years):
    """Per fall (Sep-Nov): average Bluebikes trips a weekday and a weekend day that start or end at a dock in Somerville,
    split into trips within the city, leaving it and arriving in it (a trip within the city counts once); the docks in
    Somerville that had trips, and the share of those trips on e-bikes (from 2024, when the files say)."""
    keys = {}
    for k in re.findall(r'<Key>([^<]+)</Key>', get(BIKES).decode()):
        m = re.match(r'(\d{4})(\d{2})-(?:hubway|bluebikes)-tripdata\.(?:csv\.)?zip$', k)
        if m:
            keys[(int(m.group(1)), int(m.group(2)))] = k
    out = {}
    for y in years:
        path = os.path.join(CACHE, f'trends-bikes-v3-{y}.json')
        if not os.path.exists(path):
            # place each station by its dock: classic bikes start and end at the dock; from 2024 e-bike trips carry the
            # bike's GPS position, which near the city line can fall on the wrong side
            loc, name, trips, n2id = {}, {}, [], {}            # n2id: station name -> id (2025 has a few trips with the name only)
            for mo in BIKE_MONTHS:
                if (y, mo) not in keys:
                    continue
                z = zipfile.ZipFile(cached(keys[(y, mo)], BIKES + keys[(y, mo)]))
                f = next(n for n in z.namelist() if n.endswith('.csv') and not n.startswith('__'))
                with z.open(f) as fh:
                    for r in csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig', newline='')):
                        st = r.get('started_at') or r.get('starttime')
                        na, nb = r.get('start_station_name') or r.get('start station name'), r.get('end_station_name') or r.get('end station name')
                        a = r.get('start_station_id') or r.get('start station id') or (na and '@' + na)
                        b = r.get('end_station_id') or r.get('end station id') or (nb and '@' + nb)
                        for sid, nm in ((a, na), (b, nb)):
                            if sid and nm and not sid.startswith('@'):
                                n2id[nm] = sid
                        if not st or not (a or b):
                            continue
                        t = r.get('rideable_type') or ''
                        eb = t == 'electric_bike'
                        for sid, la, lo, nm in ((a, r.get('start_lat') or r.get('start station latitude'), r.get('start_lng') or r.get('start station longitude'), r.get('start_station_name') or r.get('start station name')),
                                                (b, r.get('end_lat') or r.get('end station latitude'), r.get('end_lng') or r.get('end station longitude'), r.get('end_station_name') or r.get('end station name'))):
                            if sid and la and lo and (sid not in loc or (not eb and loc[sid][2])):
                                try:
                                    loc[sid] = (float(lo), float(la), eb)
                                except ValueError:
                                    pass
                            if sid:
                                name[sid] = nm or sid
                        trips.append((st[:10], a, b, eb))
            fix = lambda k: n2id.get(k[1:], k) if k and k.startswith('@') else k   # a name-only trip takes its station's id
            for k in [k for k in loc if k.startswith('@')]:
                v = loc.pop(k)
                if fix(k) not in loc:
                    loc[fix(k)] = v
            trips = [(d, fix(a), fix(b), eb) for d, a, b, eb in trips]
            name = {fix(k): v for k, v in name.items()}
            here = {k for k in loc if inside(som_rings, loc[k][0], loc[k][1])}
            per = defaultdict(Counter)                         # date -> within / out / in
            used, ebike, total = set(), 0, 0
            for d, a, b, eb in trips:
                ia, ib = a in here, b in here
                if not (ia or ib):
                    continue
                per[d]['within' if ia and ib else 'out' if ia else 'in'] += 1
                used.update(x for x in (a, b) if x in here)
                total += 1; ebike += eb
            hol = holidays(y)
            alld = [date(y, mo, 1) + timedelta(i) for mo in BIKE_MONTHS for i in range(31)
                    if (date(y, mo, 1) + timedelta(i)).month == mo]
            wk = [d for d in alld if d.weekday() < 5 and d not in hol]
            we = [d for d in alld if d.weekday() >= 5]
            avg = lambda ds, k: round(sum(per[d.isoformat()][k] for d in ds) / len(ds))
            res = {'wk': sum(avg(wk, k) for k in ('within', 'out', 'in')), 'we': sum(avg(we, k) for k in ('within', 'out', 'in')),
                   'parts': {'wk': {k: avg(wk, k) for k in ('within', 'out', 'in')}, 'we': {k: avg(we, k) for k in ('within', 'out', 'in')}},
                   'docks': places([loc[k] for k in used if 'temp' not in name.get(k, '').lower()]),
                   'ebike': round(100 * ebike / total, 1) if ebike else None,
                   'months': sum((y, mo) in keys for mo in BIKE_MONTHS)}
            os.makedirs(CACHE, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(res, f)
        with open(path) as f:
            out[f'Fall {y}'] = json.load(f)
        b = out[f'Fall {y}']
        print(f"  bikes Fall {y}: {b['wk']:,} trips a weekday to, from or within Somerville ({b['parts']['wk']}), "
              f"{b['we']:,} a weekend day, {b['docks']} docks, e-bikes {b['ebike']}%, months {b['months']}", file=sys.stderr)
    return out


def get_maybe(url, params=None):
    """Like get(), but None when the server has nothing (HTTP 204 or 404): a year not published (yet)."""
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': 'curl/8.5.0 ' + UA})   # the Census site refuses some clients
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read() if r.status != 204 else None
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):                          # 400: a table that year doesn't have (2020 1-year)
            return None
        raise


def acs():
    """Somerville residents who work, and how they get there, from the American Community Survey 1-year tables: B08006
    (means of transportation to work, by sex: its totals equal B08301's), B23025 (employment status), B01001 (age).
    Use B08006, not B08301: the Census Bureau left B08301 blank for Somerville in 2022 and 2023 but published B08006.
    There are no 1-year tables for 2020; that year is left out."""
    out, this = {}, datetime.now().year
    for y in range(FIRST_YEAR, this):
        path = os.path.join(CACHE, f'trends-acs-b08006-{y}.json')
        if not os.path.exists(path):
            res = {}
            for t in ('B08006', 'B23025', 'B01001'):
                blob = get_maybe(ACS_TABLE, {'id': f'ACSDT1Y{y}.{t}', 'g': '160XX00US2562535'})
                if not blob:
                    res = None
                    break
                d = json.loads(blob)['response']['data']
                row = dict(zip(d[0], d[1]))
                if not row.get(f'{t}_001E'):              # listed, but the values left blank
                    res = None
                    break
                res.update(row)
            if res is None and y >= this - 2:
                continue                                  # maybe not released yet: ask again next build
            os.makedirs(CACHE, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(res, f)
        with open(path) as f:
            res = json.load(f)
        if not res:
            print(f'  survey {y}: not published for Somerville', file=sys.stderr)
            continue
        n = lambda k: float(res.get(k) or 0)
        older = sum(n(f'B01001_{k:03d}E') for k in list(range(20, 26)) + list(range(44, 50)))
        out[y] = {'workers': round(n('B08006_001E')), 'workers_moe': round(n('B08006_001M')),
                  'wfh': round(n('B08006_017E')), 'wfh_moe': round(n('B08006_017M')),
                  'transit': round(n('B08006_008E')), 'transit_moe': round(n('B08006_008M')), 'alone': round(n('B08006_003E')),
                  'carpool': round(n('B08006_004E')), 'walk': round(n('B08006_015E')), 'walk_moe': round(n('B08006_015M')), 'bike': round(n('B08006_014E')), 'bike_moe': round(n('B08006_014M')),
                  'bus': round(n('B08006_009E')), 'subway': round(n('B08006_010E')), 'lrail': round(n('B08006_012E')),
                  'employed': round(n('B23025_004E')), 'employed_moe': round(n('B23025_004M')),
                  'older': round(100 * older / n('B01001_001E'), 1)}
        w = out[y]
        print(f"  survey {y}: {w['workers']:,} working, from home {100 * w['wfh'] / w['workers']:.1f}%, "
              f"transit {100 * w['transit'] / w['workers']:.1f}%", file=sys.stderr)
    return out


def lodes():
    """Jobs in Somerville (by workplace) and jobs held by Somerville residents (by home), each year, from the Census
    Bureau's LEHD Origin-Destination Employment Statistics: jobs covered by unemployment insurance, all jobs (JT00).
    Somerville's census blocks come from the LODES crosswalk (county subdivision "Somerville city"); a tract range
    would take in a Medford block."""
    som_blocks = set()
    for r in csv.DictReader(gzip.open(cached('trends-lodes-xwalk.csv.gz', LODES_XWALK), 'rt', encoding='utf-8')):
        if r['ctycsubname'].startswith('Somerville city'):
            som_blocks.add(r['tabblk2020'])
    som = som_blocks.__contains__
    out, this = {}, datetime.now().year
    for y in range(FIRST_YEAR, this):
        path = os.path.join(CACHE, f'trends-lodes-blocks-{y}.json')
        if not os.path.exists(path):
            res = {}
            for kind, geo, key in (('wac', 'w_geocode', 'jobs_in'), ('rac', 'h_geocode', 'jobs_res')):
                blob = get_maybe(LODES.format(kind=kind, year=y))
                if not blob:
                    res = None
                    break
                rows = csv.DictReader(io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(blob))))
                res[key] = sum(int(r['C000']) for r in rows if som(r[geo]))
            if res is None:
                continue                                  # not published yet
            os.makedirs(CACHE, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(res, f)
        with open(path) as f:
            out[y] = json.load(f)
        print(f"  jobs {y}: in Somerville {out[y]['jobs_in']:,}, held by residents {out[y]['jobs_res']:,}", file=sys.stderr)
    return out


def item_url(item):
    return json.loads(get(f'https://www.arcgis.com/sharing/rest/content/items/{item}', {'f': 'json'}))['url']


def rail():
    """{season: {station: weekday boardings}} for the stations in STATIONS."""
    want = {s for s, *_ in STATIONS}
    out = {}
    for season, (item, kind) in RAIL_ITEMS.items():
        path = os.path.join(CACHE, f"trends-rail-{season.replace(' ', '-')}.json")
        if not os.path.exists(path):
            res = Counter()
            if kind == 'csv':
                # Rows per route, direction and hour, each an average over its own number of service days (a branch
                # can run fewer days at a station): add total boardings and divide by the station's weekdays.
                blob = get(f'https://www.arcgis.com/sharing/rest/content/items/{item}/data')
                tot, days = Counter(), Counter()
                for r in csv.DictReader(io.StringIO(blob.decode('utf-8-sig'))):
                    if r['day_type_name'] == 'Weekday' and r['parent_station'] in want:
                        st = r['parent_station']
                        tot[st] += float(r['total_ons'] or 0)
                        days[st] = max(days[st], int(float(r['number_service_days'] or 0)))
                res = Counter({st: tot[st] / days[st] for st in tot if days[st]})
            else:
                url = item_url(item) + '/0/query'
                if kind == 'old':
                    where = f"season='{season}' AND day_type_name='weekday' AND stop_name IN ({','.join(repr(k) for k in OLD_NAMES)})"
                    group, key = 'stop_name', lambda a: OLD_NAMES[a['stop_name']]
                else:
                    where = f"day_type_name='Weekday' AND parent_station IN ({','.join(repr(k) for k in want)})"
                    group, key = 'parent_station', lambda a: a['parent_station']
                d = json.loads(get(url, {'where': where, 'groupByFieldsForStatistics': group, 'f': 'json',
                                         'outStatistics': json.dumps([{'statisticType': 'sum', 'onStatisticField': 'average_ons',
                                                                       'outStatisticFieldName': 'ons'}])}))
                for f in d['features']:
                    res[key(f['attributes'])] += f['attributes']['ons'] or 0
            os.makedirs(CACHE, exist_ok=True)
            with open(path, 'w') as f:
                json.dump({k: round(v) for k, v in res.items()}, f)
        with open(path) as f:
            out[season] = json.load(f)
        print(f"  rail {season}: " + ', '.join(f'{k[6:]} {v:,}' for k, v in out[season].items()), file=sys.stderr)
    return out


GATES = 'https://www.arcgis.com/sharing/rest/content/items/7859894afb5641ce91a2bb03599fdf5b/data'  # GSE_by_year.zip
GATED = ('place-davis', 'place-portr', 'place-astao', 'place-sull')   # the Green Line Extension stations have no gates


def gates(years):
    """{season: {station: average weekday fare-gate entries}} for the gated stations, September to November, federal
    holidays out, from the MBTA's Gated Station Entries (unscaled taps at the gates; children and fare evasion aren't
    counted). Days with no entries at a station (a closure, a shutdown) are left out of its average."""
    out = {}
    z = None
    for y in years:
        path = os.path.join(CACHE, f'trends-gates-{y}.json')
        if not os.path.exists(path):
            if z is None:
                z = zipfile.ZipFile(cached('mbta-gated-entries.zip', GATES))
            name = next((n for n in z.namelist() if n.endswith(f'_{y}.csv')), None)
            if not name:
                continue
            per = defaultdict(Counter)                      # station -> date -> entries
            hol = holidays(y)
            with z.open(name) as fh:
                for r in csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig')):
                    if r['stop_id'] not in GATED:
                        continue
                    ds = r['service_date'][:10].replace('/', '-')
                    d = date(int(ds[:4]), int(ds[5:7]), int(ds[8:10]))
                    if d.month in BIKE_MONTHS and d.weekday() < 5 and d not in hol:
                        per[r['stop_id']][d] += float(r['gated_entries'] or 0)
            res = {st: round(sum(v for v in per[st].values() if v > 0) / max(1, sum(1 for v in per[st].values() if v > 0)))
                   for st in GATED if per[st]}
            os.makedirs(CACHE, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(res, f)
        with open(path) as f:
            out[f'Fall {y}'] = json.load(f)
        print(f"  gates Fall {y}: " + ', '.join(f'{k[6:]} {v:,}' for k, v in out[f'Fall {y}'].items()), file=sys.stderr)
    return out


HUBS = {'place-davis': 'Davis', 'place-portr': 'Porter', 'place-harsq': 'Harvard', 'place-cntsq': 'Central', 'place-knncl': 'Kendall',
        'place-lech': 'Lechmere', 'place-sull': 'Sullivan', 'place-unsqu': 'Union Sq', 'place-astao': 'Assembly', 'place-welln': 'Wellington',
        'place-mlmnl': 'Malden Ctr', 'place-rugg': 'Ruggles', 'place-mdftf': 'Medford/Tufts', 'place-gilmn': 'Gilman Sq', 'place-balsq': 'Ball Sq',
        'place-mgngl': 'Magoun Sq', 'place-esomr': 'E. Somerville', 'place-alfcl': 'Alewife'}


def route_paths(feed, ids):
    """{'route|direction': {'h': headsign, 'p': [[lon, lat], ...]}} from one archived feed: per direction the longest path among
    those run on at least 5% as many trips as the most-run one (so a route that still reaches its far end is drawn to it)."""
    date, url = feed
    path = os.path.join(CACHE, f'trends-paths-{date}.json')
    if os.path.exists(path):
        with open(path) as f:
            out = json.load(f)
        if all(f'{r}|{d}' in out for r in ids for d in '01'):
            return out
    z = zipfile.ZipFile(io.BufferedReader(RemoteFile(url), buffer_size=1 << 22))
    cnt, head = Counter(), {}
    for r in csv.DictReader(io.TextIOWrapper(z.open('trips.txt'), encoding='utf-8-sig')):
        if r['route_id'] in ids and r['shape_id']:
            k = (r['route_id'], r['direction_id'], r['shape_id']); cnt[k] += 1; head[k] = r['trip_headsign']
    need = {k[2] for k in cnt}; pts = defaultdict(list)
    for r in csv.DictReader(io.TextIOWrapper(z.open('shapes.txt'), encoding='utf-8-sig')):
        if r['shape_id'] in need:
            pts[r['shape_id']].append((int(r['shape_pt_sequence']), float(r['shape_pt_lon']), float(r['shape_pt_lat'])))
    def length(sh):
        p = [(x * 82000, y * 110540) for _, x, y in sorted(pts[sh])]
        return sum(math.dist(a, b) for a, b in zip(p, p[1:]))
    out = {}
    for rid in ids:
        for d in '01':
            cand = [(n, k) for k, n in cnt.items() if k[0] == rid and k[1] == d]
            if not cand:
                continue
            top = max(n for n, _ in cand)
            _, k = max(((n, k) for n, k in cand if n >= 0.05 * top), key=lambda t: length(t[1][2]))
            out[f'{rid}|{d}'] = {'h': head[k], 'p': [[round(x, 6), round(y, 6)] for _, x, y in sorted(pts[k[2]])]}
    os.makedirs(CACHE, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(out, f)
    return out


def trip_loads(seasons_wanted, route_ids):
    """{season: {(route id, direction): {(variant, start): [start minute, days counted, {stop: riders on board leaving it}]}}}
    for weekday departures (Monday-Thursday from Fall 2025), read again from the ridership file for the routes asked."""
    z = zipfile.ZipFile(cached('mbta-bus-ridership.zip', RIDERSHIP)); out = {}
    for se in seasons_wanted:
        n = next(n for n in z.namelist() if n.endswith(f"_Fall_{se[5:]}.csv"))
        r = csv.DictReader(io.TextIOWrapper(z.open(n), encoding='utf-8-sig'))
        c = lambda k: next(x for x in COLS[k] if x in r.fieldnames)
        R, D, T, V, DIR, ST, L, SA = (c(k) for k in ('route', 'day', 'start', 'variant', 'dir', 'stop', 'load', 'samples'))
        res = defaultdict(dict)
        for row in r:
            rid = row[R].strip()
            if rid not in route_ids or row[D] not in ('weekday', 'Wkdy'):
                continue
            t = res[(rid, row[DIR].strip())].setdefault((row[V], row[T]), [start_min(row[T]), int(float(row[SA] or 0)), {}])
            t[2][row[ST]] = float(row[L] or 0)
        out[se] = res
    return out


BUS_TIMES = {  # MBTA Bus Arrival Departure Times, a yearly collection (one CSV a month); the same files as the storm replays
    2025: '924df13d845f4907bb6a6c3ed380d57a',
}


def bus_runs(year, route_ids):
    """{(route id, direction): [run, ...]} for September to November weekdays (federal holidays out): each run is one bus on
    one day, its timing stops in order as [stop id, actual seconds, scheduled seconds at the first one]."""
    item = BUS_TIMES.get(year)
    if not item:
        print(f'  bus speeds: no arrival-time file listed for {year} (add it to BUS_TIMES)', file=sys.stderr)
        return {}
    z = zipfile.ZipFile(cached(f'bus-{year}.zip', f'https://www.arcgis.com/sharing/rest/content/items/{item}/data'))
    hol = holidays(year)
    sec = lambda t: (int(t[8:10]) - 1) * 86400 + int(t[11:13]) * 3600 + int(t[14:16]) * 60 + int(t[17:19])   # "1900-01-0DTHH:MM:SSZ" (local time)
    gid = {ROUTE_NAME_TIMES.get(r, r): r for r in route_ids}        # the CT2 is "CT2" here, 747 in the schedules
    trips = defaultdict(list)
    for mo in BIKE_MONTHS:
        n = next((n for n in z.namelist() if n.endswith(f'{year}-{mo:02d}.csv')), None)
        if not n:
            continue
        for r in csv.DictReader(io.TextIOWrapper(z.open(n), encoding='utf-8-sig')):
            rt = r['route_id'].lstrip('0')
            if rt not in gid or not r['actual'] or not r['half_trip_id']:
                continue
            d = date.fromisoformat(r['service_date'])
            if d.weekday() >= 5 or d in hol:
                continue
            trips[(gid[rt], '1' if r['direction_id'] == 'Inbound' else '0', r['service_date'], r['half_trip_id'])].append(
                (int(r['time_point_order']), r['stop_id'], sec(r['actual']), sec(r['scheduled']) if r['scheduled'] else None))
    out = defaultdict(list)
    for (rid, d, _, _), pts in trips.items():
        pts.sort()
        out[(rid, d)].append([[p[1], p[2]] for p in pts] + [pts[0][3]])
    print(f'  bus speeds {year}: {sum(len(v) for v in out.values()):,} weekday runs on {len(out)} route directions', file=sys.stderr)
    return out


def profiles(seasons, base, last, names, som_rings):
    """Load profiles: riders on board leaving each stop on weekdays, along each route's path, for the base fall and
    the latest. Stops are placed by distance along the latest path; stops more than 150 m off it, stops past its ends, and
    stops only a few trips serve (school trips, short variants) are left out."""
    ids = {ROUTE_ID.get(n, n): n for n in names}
    paths = route_paths(fall_feeds()[int(last[5:])], sorted(ids))
    TL = trip_loads([base, last], set(ids))
    RUNS = bus_runs(int(last[5:]), set(ids))
    K = (math.cos(math.radians(42.39)) * 111320, 110540)
    xy = lambda p: (p[0] * K[0], p[1] * K[1])
    pn, pidx, out = [], {}, []
    def name_id(n):
        if n not in pidx:
            pidx[n] = len(pn); pn.append(n)
        return pidx[n]
    clean = lambda h: h.replace(' (Limited Stops)', '').replace(' via Sullivan', '')
    for rid, nm in ids.items():
        dirs = []
        for d in ('1', '0'):
            if f'{rid}|{d}' not in paths:
                continue
            shape = paths[f'{rid}|{d}']['p']; P = [xy(p) for p in shape]; cum = [0.0]
            for a, b in zip(P, P[1:]):
                cum.append(cum[-1] + math.dist(a, b))
            total = cum[-1]
            def proj(p):
                q = xy(p); best = (1e18, 0.0)
                for i, (a, b) in enumerate(zip(P, P[1:])):
                    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy or 1
                    t = max(0, min(1, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / L2))
                    dd = math.dist(q, (a[0] + t * dx, a[1] + t * dy))
                    if dd < best[0]:
                        best = (dd, cum[i] + t * math.sqrt(L2))
                return best
            bands, start = [], None
            for i, p in enumerate(shape):
                isin = inside(som_rings, p[0], p[1])
                if isin and start is None:
                    start = cum[i]
                if not isin and start is not None:
                    bands.append([round(start), round(cum[i])]); start = None
            if start is not None:
                bands.append([round(start), round(total)])
            locs = seasons[last]['locs']
            stops, sidx = [], {}                              # the latest fall's stops along the path: [distance, name]
            for sid in {sid for t in TL[last].get((rid, d), {}).values() for sid in t[2]}:
                if sid not in locs:
                    continue
                dd, a = proj(locs[sid][:2])
                if dd < 150 and not (dd > 40 and (a < 30 or a > total - 30)):
                    stops.append([round(a), name_id(locs[sid][2]), sid])
            stops.sort()
            for i, st in enumerate(stops):
                sidx[st[2]] = i
            avg, cnt = {}, {}
            for key, se in (('b', base), ('n', last)):
                if key == 'b' and not seasons[base]['routes'].get(nm):
                    continue                                    # not a Somerville route then (the 109): no before line
                lc = seasons[se]['locs']; trips = [t for t in TL[se].get((rid, d), {}).values() if t[1] >= 3]
                cnt[key] = len(trips); acc = defaultdict(lambda: [0.0, 0])
                for t in trips:
                    for sid, ld in t[2].items():
                        acc[sid][0] += ld; acc[sid][1] += 1
                pts = []
                for sid, (sm, k_) in acc.items():
                    if sid not in lc or k_ < max(2, 0.3 * len(trips)):
                        continue                            # stops only a few trips serve (school trips, short variants)
                    dd, a = proj(lc[sid][:2])
                    if dd < 150 and not (dd > 40 and (a < 30 or a > total - 30)):
                        pts.append([round(a), round(sm / k_, 1), name_id(lc[sid][2])])
                avg[key] = sorted(pts)
            deps = []                                           # each latest-fall departure: [start minute, first stop, loads]
            for t in sorted(TL[last].get((rid, d), {}).values()):
                idx = sorted((sidx[sid], ld) for sid, ld in t[2].items() if sid in sidx)
                if len(idx) < 3 or t[1] < 3:
                    continue
                first, lastx = idx[0][0], idx[-1][0]; row = [-1] * (lastx - first + 1)
                for i, ld in idx:
                    row[i - first] = round(ld)
                deps.append([t[0], first, row])
            hubs = []
            for hid, hn in HUBS.items():
                if hid in seasons[last]['locs']:
                    dd, a = proj(seasons[last]['locs'][hid][:2])
                    if dd < 220:
                        hubs.append([round(a), hn])
            other = paths.get(f'{rid}|{"0" if d == "1" else "1"}', {'h': ''})['h']
            # speeds: miles per hour between consecutive timing stops on each run, placed along the same path
            pos, segs, runs_by_dep = {}, {}, defaultdict(list)
            for run in RUNS.get((rid, d), []):
                tps, sched = run[:-1], run[-1]; got = []
                for (s1, t1), (s2, t2) in zip(tps, tps[1:]):
                    for sid in (s1, s2):
                        if sid not in pos:
                            pos[sid] = proj(locs[sid][:2]) if sid in locs else (1e9, 0)
                    (d1, a1), (d2, a2) = pos[s1], pos[s2]
                    if d1 > 150 or d2 > 150 or a2 - a1 < 150 or t2 <= t1:
                        continue                                # off the path, out of order, or a clock glitch
                    mph = (a2 - a1) / (t2 - t1) * 2.23694
                    if 1 <= mph <= 45:
                        segs[(s1, s2)] = (a1, a2); got.append(((s1, s2), mph))
                if got and sched is not None:
                    runs_by_dep[sched // 60].append(dict(got))
            seg = sorted(segs, key=lambda k: segs[k])
            med = lambda xs: sorted(xs)[len(xs) // 2] if xs else None
            allv = {k: [r[k] for rs in runs_by_dep.values() for r in rs if k in r] for k in seg}
            keep = []                                           # one chain of stretches that don't overlap: the most-run first
            for k in sorted((k for k in seg if len(allv[k]) >= 20), key=lambda k: -len(allv[k])):
                a1, a2 = segs[k]
                if all(a2 <= segs[q][0] + 50 or a1 >= segs[q][1] - 50 for q in keep):
                    keep.append(k)
            keep.sort(key=lambda k: segs[k])
            sp = None
            if keep:
                mm = [med(allv[k]) for k in keep]
                dist = sum(segs[k][1] - segs[k][0] for k in keep)
                sp = {'seg': [[round(segs[k][0]), round(segs[k][1]), name_id(locs[k[0]][2]), name_id(locs[k[1]][2])] for k in keep],
                      'med': [round(v, 1) for v in mm],
                      'all': round(dist / sum((segs[k][1] - segs[k][0]) / v for k, v in zip(keep, mm)), 1),
                      'runs': sum(len(v) for v in runs_by_dep.values()),
                      'dep': [[m, [round(med(x), 1) if (x := [r[k] for r in rs if k in r]) else -1 for k in keep]]
                              for m, rs in sorted(runs_by_dep.items()) if len(rs) >= 5]}
            dirs.append({'to': clean(paths[f'{rid}|{d}']['h']), 'from': clean(other), 'len': round(total), 'som': bands,
                         'hubs': sorted(hubs), 's': [st[:2] for st in stops], 'avg': avg, 'cnt': cnt, 'dep': deps, 'v': sp})
        out.append({'r': nm, 'dirs': dirs})
    print(f'  load profiles: {len(out)} routes, {sum(len(r["dirs"]) for r in out)} directions', file=sys.stderr)
    return {'routes': out, 'names': pn}


def main():
    tw = towns()
    som = somerville_exact()
    seasons, stops_all = bus(som)
    rails = rail()
    bikes = bluebikes(som, sorted(int(s[5:]) for s in seasons))
    gate = gates(sorted(int(s[5:]) for s in seasons))
    work = {'acs': acs(), 'lodes': lodes()}
    # map frame: Somerville plus a margin; neighbors cut to it
    xs = [p[0] for r in tw['Somerville'] for p in r]
    ys = [p[1] for r in tw['Somerville'] for p in r]
    box = (min(xs) - 0.012, min(ys) - 0.008, max(xs) + 0.012, max(ys) + 0.008)
    lat0 = (box[1] + box[3]) / 2
    kx = math.cos(math.radians(lat0))

    def xy(lon, lat):                                   # metres-ish, y down
        return [round((lon - box[0]) * kx * 111320), round((box[3] - lat) * 110540)]

    def keep(ring):
        return any(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in ring)
    towns_out = [{'n': n, 'rings': [[xy(*p) for p in r] for r in rings if len(r) > 3 and keep(r)]} for n, rings in tw.items()]
    towns_out = [t for t in towns_out if t['rings']]
    stations = []
    st_locs = {}
    for date_url in [fall_feeds()[max(fall_feeds())]]:
        locs = season_stops(*date_url)
        for sid, name, line, here in STATIONS:
            st_locs[sid] = locs[sid][:2]
    for sid, name, line, here in STATIONS:
        stations.append({'id': sid, 'n': name, 'line': line, 'in': here, 'p': xy(*st_locs[sid]),
                         'v': {s: rails[s].get(sid) for s in rails if rails[s].get(sid) is not None},
                         'g': {s: gate[s][sid] for s in gate if sid in gate[s]}})
    # one map dot per place: a stop that only got a new number (the bus redesign renumbered many) or moved a few metres
    # is the same stop; stops on opposite sides of a street (20 m and more apart) stay apart
    order = sorted(seasons, key=lambda s: int(s[5:]))
    riders = Counter()
    for se in order:
        riders.update(seasons[se]['stops'])
    pts = {k: xy(stops_all[k][0], stops_all[k][1]) for k in stops_all}
    canon, grid, stops = {}, defaultdict(list), []
    for k in sorted(stops_all, key=lambda k: (-riders[k], k)):     # busiest first, so it names the place
        x, y = pts[k]
        gx, gy = x // SAME_STOP, y // SAME_STOP
        near = [c for dx in (-1, 0, 1) for dy in (-1, 0, 1) for c in grid[(gx + dx, gy + dy)]
                if math.hypot(stops[c]['p'][0] - x, stops[c]['p'][1] - y) <= SAME_STOP]
        if near:
            canon[k] = near[0]
            continue
        canon[k] = len(stops)
        grid[(gx, gy)].append(len(stops))
        stops.append({'id': k, 'n': stops_all[k][2], 'p': [x, y]})
    merged = len(stops_all) - len(stops)
    print(f'  map: {len(stops_all)} stop ids at {len(stops)} places ({merged} renumbered or moved a few metres)', file=sys.stderr)
    def per_place(d):
        c = Counter()
        for k, v in d.items():
            c[canon[k]] += v
        return [[i, round(v, 1)] for i, v in c.items()]
    routes = sorted({r for s in order for r, v in seasons[s]['routes'].items()},
                    key=lambda r: -max(seasons[s]['routes'].get(r, 0) for s in order))
    routes = [r for r in routes if max(seasons[s]['routes'].get(r, 0) for s in order) >= MIN_ROUTE]
    payload = {
        'seasons': order,
        'bus': {s: {k: seasons[s][k] for k in ('som', 'sys', 'off', 'hours', 'nstops')} for s in order},
        'routes': [{'r': r, 'v': [seasons[s]['routes'].get(r, 0) for s in order], 't': [seasons[s]['trips'].get(r, 0) for s in order]} for r in routes],
        'prof': profiles(seasons, 'Fall 2019', order[-1], [r for r in routes if seasons[order[-1]]['routes'].get(r, 0) >= MIN_ROUTE], som),
        'stopv': {s: per_place(seasons[s]['stops']) for s in order},
        'stops': stops, 'stations': stations, 'towns': towns_out, 'bikes': bikes, 'work': work,
        'size': xy(box[2], box[1]),
    }
    blob = json.dumps(payload, separators=(',', ':'))
    with open(os.path.join(HERE, 'trends_template.html')) as f:
        page = f.read().replace('/*DATA*/null', blob)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'trends.html'), 'w') as f:
        f.write(page)
    shutil.copy(os.path.join(OUT, 'trends.html'), os.path.join(ROOT, 'docs', 'transit-trends.html'))
    last, base = order[-1], 'Fall 2019'
    tl = lambda s: seasons[s]['som']['wk'] + sum(rails.get(s, {}).values())
    print(f"{base} → {last}: buses in Somerville {seasons[base]['som']['wk']:,} → {seasons[last]['som']['wk']:,}; "
          f"buses + T {tl(base):,} → {tl(last):,}; page {len(page) // 1024} KB")


if __name__ == '__main__':
    main()
