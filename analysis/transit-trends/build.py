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
# Sullivan Square (Charlestown, where many Somerville buses end). Lechmere is left out: it's farther from the city line,
# next to industrial land rather than homes, and few in Somerville use it as their station.
STATIONS = [
    ('place-davis', 'Davis', 'Red', True), ('place-portr', 'Porter', 'Red', False),
    ('place-astao', 'Assembly', 'Orange', True), ('place-sull', 'Sullivan Square', 'Orange', False),
    ('place-unsqu', 'Union Square', 'Green', True), ('place-esomr', 'East Somerville', 'Green', True),
    ('place-gilmn', 'Gilman Square', 'Green', True), ('place-mgngl', 'Magoun Square', 'Green', True),
    ('place-balsq', 'Ball Square', 'Green', True),
]
OLD_NAMES = {'Davis': 'place-davis', 'Porter': 'place-portr', 'Assembly': 'place-astao', 'Sullivan Square': 'place-sull'}
ROUTE_NAME = {'747': 'CT2', '194': '89/93'}
BIKES = 'https://s3.amazonaws.com/hubway-data/'      # Bluebikes (Hubway until 2018) monthly trip files
BIKE_MONTHS = (9, 10, 11)                            # "fall" for bikes: September to November
ACS_TABLE = 'https://data.census.gov/api/access/data/table'   # Census tables, no key; Somerville city = 160XX00US2562535
LODES = 'https://lehd.ces.census.gov/data/lodes/LODES8/ma/{kind}/ma_{kind}_S000_JT00_{year}.csv.gz'
FIRST_YEAR = 2015
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


def bus(som_rings):
    """Per fall season: weekday/Saturday/Sunday boardings in Somerville and systemwide; weekday by route, by stop and by
    the hour the trip started."""
    z = zipfile.ZipFile(cached('mbta-bus-ridership.zip', RIDERSHIP))
    feeds = fall_feeds()
    COLS = {'route': ('route_id', 'GTFS route_id'), 'stop': ('stop_id', 'GTFS stop_id'), 'day': ('day_type_name', 'Day Type'),
            'on': ('boardings', 'Boardings'), 'off': ('alightings', 'Alightings'), 'start': ('trip_start_time', 'trip start time'),
            'name': ('stop_name', 'Stop Name')}
    DAY = {'weekday': 'wk', 'Wkdy': 'wk', 'Fri': 'fri', 'saturday': 'sat', 'Sat': 'sat', 'sunday': 'sun', 'Sun': 'sun'}
    seasons, stops_all = {}, {}
    for n in sorted(z.namelist()):
        if not n.endswith('.csv') or '_Fall_' not in n:
            continue
        year = int(n.rsplit('_', 1)[1][:4])
        date, url = feeds[year]
        locs = season_stops(date, url)
        som = {s for s, (x, y, _) in locs.items() if inside(som_rings, x, y)}
        r = csv.DictReader(io.TextIOWrapper(z.open(n), encoding='utf-8-sig'))
        col = {k: next(c for c in v if c in r.fieldnames) for k, v in COLS.items()}
        tot = defaultdict(Counter)                     # day -> {'som','sys','som_off'}
        route = defaultdict(Counter)                   # day -> route -> riders (wk, fri)
        stop = defaultdict(Counter)
        hour = defaultdict(Counter)
        names, unknown = {}, 0.0
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
                    stop[d][sid] += on
                    h = int(row[col['start']].split(':')[0])
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
    return {nth(9, 0, 1), nth(10, 0, 2), date(y, 11, 11), thanks, thanks + timedelta(1)}


def bluebikes(som_rings, years):
    """Per fall (Sep-Nov): average trips a weekday and a weekend day that start at a dock in Somerville, the docks in
    Somerville that had trips, and the share of trips on e-bikes (from 2020, when the files say)."""
    keys = {}
    for k in re.findall(r'<Key>([^<]+)</Key>', get(BIKES).decode()):
        m = re.match(r'(\d{4})(\d{2})-(?:hubway|bluebikes)-tripdata\.(?:csv\.)?zip$', k)
        if m:
            keys[(int(m.group(1)), int(m.group(2)))] = k
    out = {}
    for y in years:
        path = os.path.join(CACHE, f'trends-bikes-{y}.json')
        if not os.path.exists(path):
            # count by station; place each station by its dock (classic bikes start at the dock; from 2024 e-bike
            # trips carry the bike's GPS position, which near the city line can fall on the wrong side)
            per = defaultdict(Counter)                     # station -> day -> trips
            loc, eb = {}, Counter()
            for mo in BIKE_MONTHS:
                if (y, mo) not in keys:
                    continue
                z = zipfile.ZipFile(cached(keys[(y, mo)], BIKES + keys[(y, mo)]))
                f = next(n for n in z.namelist() if n.endswith('.csv') and not n.startswith('__'))
                with z.open(f) as fh:
                    for r in csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig', newline='')):
                        st = r.get('started_at') or r.get('starttime')
                        sid = r.get('start_station_id') or r.get('start station id') or r.get('start_station_name') or r.get('start station name')
                        lat = r.get('start_lat') or r.get('start station latitude')
                        lon = r.get('start_lng') or r.get('start station longitude')
                        if not st or not sid:
                            continue
                        t = r.get('rideable_type') or ''
                        per[sid][st[:10]] += 1
                        eb[sid] += t == 'electric_bike'
                        if lat and lon and (sid not in loc or (t != 'electric_bike' and loc[sid][2])):
                            try:
                                loc[sid] = (float(lon), float(lat), t == 'electric_bike')
                            except ValueError:
                                pass
            here = [k for k in per if k in loc and inside(som_rings, loc[k][0], loc[k][1])]
            days = Counter()
            for k in here:
                days.update(per[k])
            total = sum(days.values())
            ebike = sum(eb[k] for k in here)
            hol = holidays(y)
            alld = [date(y, mo, 1) + timedelta(i) for mo in BIKE_MONTHS for i in range(31)
                    if (date(y, mo, 1) + timedelta(i)).month == mo]
            wk = [d for d in alld if d.weekday() < 5 and d not in hol]
            we = [d for d in alld if d.weekday() >= 5]
            res = {'wk': round(sum(days[d.isoformat()] for d in wk) / len(wk)),
                   'we': round(sum(days[d.isoformat()] for d in we) / len(we)),
                   'docks': len(here), 'ebike': round(100 * ebike / total, 1) if ebike else None,
                   'months': sum((y, mo) in keys for mo in BIKE_MONTHS)}
            os.makedirs(CACHE, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(res, f)
        with open(path) as f:
            out[f'Fall {y}'] = json.load(f)
        b = out[f'Fall {y}']
        print(f"  bikes Fall {y}: {b['wk']:,} trips a weekday, {b['we']:,} a weekend day, {b['docks']} docks, "
              f"e-bikes {b['ebike']}%, months {b['months']}", file=sys.stderr)
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
    """Somerville residents who work, and how they get there, from the American Community Survey 1-year tables: B08301
    (means of transportation to work), B23025 (employment status), B01001 (age). The Census Bureau doesn't publish
    Somerville every year (none for 2020; none for 2022 or 2023); those years are left out."""
    out, this = {}, datetime.now().year
    for y in range(FIRST_YEAR, this):
        path = os.path.join(CACHE, f'trends-acs-{y}.json')
        if not os.path.exists(path):
            res = {}
            for t in ('B08301', 'B23025', 'B01001'):
                blob = get_maybe(ACS_TABLE, {'id': f'ACSDT1Y{y}.{t}', 'g': '160XX00US2562535'})
                if not blob:
                    res = None
                    break
                d = json.loads(blob)['response']['data']
                res.update(dict(zip(d[0], d[1])))
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
        out[y] = {'workers': round(n('B08301_001E')), 'wfh': round(n('B08301_021E')), 'wfh_moe': round(n('B08301_021M')),
                  'transit': round(n('B08301_010E')), 'transit_moe': round(n('B08301_010M')), 'alone': round(n('B08301_003E')),
                  'carpool': round(n('B08301_004E')), 'walk': round(n('B08301_019E')), 'bike': round(n('B08301_018E')),
                  'employed': round(n('B23025_004E')), 'older': round(100 * older / n('B01001_001E'), 1)}
        w = out[y]
        print(f"  survey {y}: {w['workers']:,} working, from home {100 * w['wfh'] / w['workers']:.1f}%, "
              f"transit {100 * w['transit'] / w['workers']:.1f}%", file=sys.stderr)
    return out


def lodes():
    """Jobs in Somerville (by workplace) and jobs held by Somerville residents (by home), each year, from the Census
    Bureau's LEHD Origin-Destination Employment Statistics: jobs covered by unemployment insurance, all jobs (JT00).
    Somerville's census tracts are 25017-350100 to 351599."""
    som = lambda g: g.startswith('25017') and 350100 <= int(g[5:11]) <= 351599
    out, this = {}, datetime.now().year
    for y in range(FIRST_YEAR, this):
        path = os.path.join(CACHE, f'trends-lodes-{y}.json')
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
                blob = get(f'https://www.arcgis.com/sharing/rest/content/items/{item}/data')
                for r in csv.DictReader(io.StringIO(blob.decode('utf-8-sig'))):
                    if r['day_type_name'] == 'Weekday' and r['parent_station'] in want:
                        res[r['parent_station']] += float(r['average_ons'] or 0)
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


def main():
    tw = towns()
    seasons, stops_all = bus(tw['Somerville'])
    rails = rail()
    bikes = bluebikes(tw['Somerville'], sorted(int(s[5:]) for s in seasons))
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
                         'v': {s: rails[s].get(sid) for s in rails if rails[s].get(sid) is not None}})
    ids = sorted(stops_all)
    stops = [{'id': s, 'n': stops_all[s][2], 'p': xy(stops_all[s][0], stops_all[s][1])} for s in ids]
    ix = {s: i for i, s in enumerate(ids)}
    order = sorted(seasons, key=lambda s: int(s[5:]))
    routes = sorted({r for s in order for r, v in seasons[s]['routes'].items()},
                    key=lambda r: -max(seasons[s]['routes'].get(r, 0) for s in order))
    routes = [r for r in routes if max(seasons[s]['routes'].get(r, 0) for s in order) >= MIN_ROUTE]
    payload = {
        'seasons': order,
        'bus': {s: {k: seasons[s][k] for k in ('som', 'sys', 'off', 'hours', 'nstops')} for s in order},
        'routes': [{'r': r, 'v': [seasons[s]['routes'].get(r, 0) for s in order]} for r in routes],
        'stopv': {s: [[ix[k], v] for k, v in seasons[s]['stops'].items()] for s in order},
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
