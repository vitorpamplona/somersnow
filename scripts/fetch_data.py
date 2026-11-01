#!/usr/bin/env python3
"""Collect the public data behind the storm replay and the charts, and write small JSON files to docs/data/.

Run with `npm run data` (Python 3 standard library only, no API keys). Re-run each fall before the first storm.
Sources, caveats and what each file holds: research/data-sources.md.

  docs/data/winters.json        Boston snowfall per winter since 1891, and Somerville 311 snow requests per winter
  docs/data/storms.json         every 6-inch-plus storm since July 2015: daily snowfall and 311 requests around it
  docs/data/wards.json          Somerville ward outlines (lon/lat), simplified
  docs/data/bus-stops.json      MBTA bus stops in Somerville with average weekday boardings
  docs/data/storm-<id>.json     each storm (3 inches or more) hour by hour (id = last day of snow): weather at Logan, 311 requests, City notices
"""
import storm_extras
import csv, io, json, math, os, statistics, struct, sys, tempfile, time, urllib.parse, urllib.request, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'data')
CACHE = os.path.join(ROOT, '.cache')  # big downloads (station entries, bike trips, alert archives); git-ignored
UA = 'somersnow data script (Somerville PTAC snow guide)'

SOCRATA_311 = 'https://data.somervillema.gov/resource/4pyi-uqq6.json'
WARDS_ZIP = 'https://data.somervillema.gov/download/ym5n-phxd/application%2Fx-zip-compressed'
ACIS = 'https://data.rcc-acis.org/StnData'
IEM = 'https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py'
MBTA_STOPS = 'https://api-v3.mbta.com/stops?filter[route_type]=3&page[limit]=10000'
MBTA_RIDERSHIP = 'https://www.arcgis.com/sharing/rest/content/items/8daf4a33925a4df59183f860826d29ee/data'

# 311 request types, grouped by what the person needed. Order = stacking order in charts.
GROUPS = {
    'ask': ['Snow emergency inquiry', 'Snow emergency parking inquiry'],
    'street': ['Plowing request', 'Snow removal request', 'Salting request', 'Sand barrel', 'Bike facility snow maintenance',
               'Parks/Playgrounds snow maintenance', 'City/School building snow maintenance'],
    'sidewalk': ['Snow/sidewalk not shoveled'],
    'spacesaver': ['Space saver report'],
    'feedback': ['Snow related feedback'],
}
TYPE_GROUP = {t: g for g, ts in GROUPS.items() for t in ts}

# Every storm (3 inches or more) in storms.json gets an hour-by-hour replay file, named by its last day of snow (storm-<id>.json).
# CITY adds what the City announced for a storm: snow emergency times and notices, each with the page it came from.
# Times are Somerville local time. Storms without an entry replay without emergency messages.
NEWS = 'https://www.somervillema.gov/news/'
CITY = {
    '2022-02-25': {
        # Only the end notice is online; the declaration isn't, so the start time is unknown.
        'emergency': {'side': 'odd', 'end': '2022-02-26T08:00', 'lotsBy': '2022-02-26T10:00',
                      'permitsBy': '2022-02-27T08:00', 'carsBy': '2022-02-28T08:00'},
        'cityDeadline': '2022-02-26T12:30',
        'notices': [
            {'t': '2022-02-25T12:00', 'approx': True, 'text': 'City: the snow emergency ends 8 a.m. Saturday. Shovel by 12:30 p.m. Saturday.',
             'src': NEWS + 'somerville-snow-emergency-will-end-saturday-february-26-8-am%E2%80%8B%E2%80%8B%E2%80%8B-move-cars-city-lots-10-am'},
        ],
    },
    '2026-01-26': {
        # Only the declaration is online; the end time is unknown.
        'emergency': {'start': '2026-01-25T07:00', 'moveBy': '2026-01-25T11:00', 'side': 'odd'},
        'notices': [
            {'t': '2026-01-24T12:00', 'approx': True, 'text': 'City declares a snow emergency starting 7 a.m. Sunday. Odd side by 11 a.m.',
             'src': NEWS + 'somerville-declares-snow-emergency-effective-sunday-january-25-7-am'},
        ],
    },
    '2026-02-23': {
        'title': 'February 22–24, 2026',
        'emergency': {'start': '2026-02-22T12:00', 'moveBy': '2026-02-22T16:00', 'side': 'odd', 'end': '2026-02-24T20:00',
                      'lotsBy': '2026-02-25T10:00', 'permitsBy': '2026-02-25T20:00', 'carsBy': '2026-02-26T20:00'},
        'cityDeadline': '2026-02-24T13:00',
        'notices': [
            {'t': '2026-02-21T12:00', 'approx': True, 'text': 'City declares a snow emergency starting noon Sunday.',
             'src': NEWS + 'somerville-declares-snow-emergency-effective-sunday-february-22-12-pm-noon'},
            {'t': '2026-02-24T12:00', 'approx': True, 'text': 'City: the emergency ends 8 p.m. tonight. Shoveling deadline was 1 p.m. "You still have to shovel."',
             'src': NEWS + 'somerville-snow-emergency-will-end-tuesday-february-24-8-pm'},
        ],
    },
}


STORM_MIN = 3.0  # inches at Logan over the storm's consecutive snowy days (each with 0.5 in or more)

# Every download is recorded (address, date, size, SHA-256) and written to docs/data/sources.json, so a later run can
# tell whether it worked from the same inputs. Sources change: 311 records get edited, archives get republished.
PROV = {}


def _fingerprint(blob=None, path=None):
    import hashlib
    h = hashlib.sha256()
    if blob is not None:
        h.update(blob)
    else:
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(1 << 20), b''):
                h.update(chunk)
    return h.hexdigest()


def get(url, params=None, data=None, tries=4):
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, **({'Content-Type': 'application/json'} if data else {})})
            with urllib.request.urlopen(req, timeout=300) as r:
                blob = r.read()
                PROV[url + ('' if data is None else ' POST ' + data.decode()[:300])] = {
                    'url': url, **({'post': data.decode()} if data else {}), 'fetched': datetime.now().isoformat(timespec='seconds'),
                    'bytes': len(blob), 'sha256': _fingerprint(blob)}
                return blob
        except Exception as e:  # network hiccup: back off and retry
            if i == tries - 1:
                raise
            print(f'  retry {url[:70]}… ({e})', file=sys.stderr)
            time.sleep(2 ** (i + 1))


def cached(name, url):
    """Download once into .cache/ and return the local path (delete the file to refresh it)."""
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, name)
    if not os.path.exists(path):
        print(f'  downloading {name}…', file=sys.stderr)
        data = get(url)
        with open(path + '.part', 'wb') as f:
            f.write(data)
        os.replace(path + '.part', path)
    if url not in PROV:
        PROV[url] = {'url': url, 'cache_file': name, 'fetched': datetime.fromtimestamp(os.path.getmtime(path)).isoformat(timespec='seconds'),
                     'bytes': os.path.getsize(path), 'sha256': _fingerprint(path=path)}
    return path


def write(name, obj):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, 'w') as f:
        json.dump(obj, f, separators=(',', ':'), ensure_ascii=False)
    print(f'  wrote docs/data/{name} ({os.path.getsize(path) // 1024} KB)')


def season_of(d):  # winter "2025" = July 2025 – June 2026
    return d.year if d.month >= 7 else d.year - 1


# ---------- sources ----------

def fetch_311():
    where = "category='Snow' or type in (%s)" % ','.join("'%s'" % t for t in TYPE_GROUP)
    rows = json.loads(get(SOCRATA_311, {'$select': 'type,date_created,ward', '$where': where, '$limit': 200000}))
    out = []
    for r in rows:
        g = TYPE_GROUP.get(r.get('type'))
        if g and r.get('date_created'):
            out.append((datetime.strptime(r['date_created'][:16], '%Y-%m-%d %H:%M'), g, r.get('ward'), r.get('type')))
    print(f'  311: {len(out)} snow requests')
    return out


HAPPINESS = 'https://data.somervillema.gov/resource/wmeh-zuz2.json'


def fetch_ward_survey():
    """How residents got around, by ward, from the latest Happiness Survey that asked it: "In the past week, which of
    the following transportation options did you use? Check all that apply." (2019, 2023, 2025). A random-sample survey
    of about 200 residents per ward, not a census."""
    yn = lambda c: f"sum(case({c}='1',1,true,0))"
    q = {'$select': f"year,ward,count(*) as n,{yn('transportation_walk_yn')} as walk,{yn('transportation_public_transit_yn')} as transit,"
                    f"{yn('transportation_car_yn')} as car,{yn('transportation_bicycle_yn')} as bike",
         '$group': 'year,ward', '$order': 'year'}
    rows = [r for r in json.loads(get(HAPPINESS, q)) if r.get('ward') and int(r['walk']) > 0]
    year = max(r['year'] for r in rows)
    out = {'year': int(year), 'question': 'In the past week, which of the following transportation options did you use? Check all that apply.', 'wards': {}}
    for r in rows:
        if r['year'] == year:
            n = int(r['n'])
            out['wards'][str(int(float(r['ward'])))] = {'n': n, **{k: round(int(r[k]) / n * 100) for k in ('walk', 'transit', 'car', 'bike')}}
    print(f'  ward survey: {year}, {sum(w["n"] for w in out["wards"].values())} answers')
    return out


def fetch_snow_daily(start):
    body = json.dumps({'sid': 'BOSthr', 'sdate': start, 'edate': date.today().isoformat(), 'elems': [{'name': 'snow'}]}).encode()
    d = json.loads(get(ACIS, data=body))['data']
    return {day: (0.0 if v in ('T', 'M') else float(v)) for day, v in d}


def fetch_snow_winters():
    body = json.dumps({'sid': 'BOSthr', 'sdate': '1891-07', 'edate': date.today().strftime('%Y-%m'),
                       'elems': [{'name': 'snow', 'interval': 'mly', 'duration': 'mly', 'reduce': 'sum'}]}).encode()
    tot, missing, months = defaultdict(float), Counter(), Counter()
    for ym, v in json.loads(get(ACIS, data=body))['data']:
        y, m = map(int, ym.split('-'))
        s = y if m >= 7 else y - 1
        months[s] += 1
        if v == 'M':
            missing[s] += 1
        else:
            tot[s] += 0.0 if v == 'T' else float(v)
    return {s: round(tot[s], 1) for s in tot if months[s] == 12 and not missing[s]}


def fetch_hourly_weather(t0, t1, sid=None):
    a, b = datetime.fromisoformat(t0), datetime.fromisoformat(t1)
    p = {'station': 'BOS', 'data': ['tmpf', 'wxcodes', 'vsby', 'sknt'], 'tz': 'America/New_York', 'format': 'onlycomma',
         'latlon': 'no', 'missing': 'M', 'trace': 'T', 'report_type': '3',
         'year1': a.year, 'month1': a.month, 'day1': a.day, 'year2': b.year, 'month2': b.month, 'day2': b.day}
    text = get(IEM + '?' + urllib.parse.urlencode(p, doseq=True)).decode()
    hours = {}
    for r in csv.DictReader(io.StringIO(text)):
        t = datetime.strptime(r['valid'], '%Y-%m-%d %H:%M')
        k = t.replace(minute=0)
        wx = r['wxcodes'] if r['wxcodes'] != 'M' else ''
        # falling snow only (blowing/drifting snow is wind, not new snow); intensity from the METAR prefix
        falling = [w for w in wx.split() if 'SN' in w and 'BLSN' not in w and 'DRSN' not in w]
        snow = max([3 if w[0] == '+' else 1 if w[0] == '-' else 2 for w in falling], default=0)
        # freezing rain, freezing drizzle or ice pellets (sleet): the ice that small storms leave
        icy = [w for w in wx.split() if any(c in w for c in ('FZRA', 'FZDZ', 'PL'))]
        ice = max([3 if w[0] == '+' else 1 if w[0] == '-' else 2 for w in icy], default=0)
        h = hours.setdefault(k, {'snow': 0, 'ice': 0, 'temp': None, 'vis': None, 'wind': None, 'wx': ''})
        h['snow'] = max(h['snow'], snow)
        h['ice'] = max(h['ice'], ice)
        if r['tmpf'] != 'M': h['temp'] = round(float(r['tmpf']))
        if r['vsby'] != 'M': h['vis'] = float(r['vsby'])
        if r['sknt'] != 'M': h['wind'] = round(float(r['sknt']))
        if wx: h['wx'] = wx
        if sid:  # every report, as published: the snow start and stop (and so the deadline) come from these codes
            storm_extras.raw(sid, 'weather_logan', ['observed', 'temp_f', 'weather_codes', 'visibility_mi', 'wind_kn', 'falling_snow_0to3', 'freezing_rain_or_sleet_0to3'],
                             [r['valid'], r['tmpf'], wx, r['vsby'], r['sknt'], snow, ice])
    return hours


# Wards: shapefile in Massachusetts State Plane (Lambert conformal conic, US feet) -> lon/lat.
def lcc_inverse(E, N):
    a, f = 6378137.0, 1 / 298.257222101
    e = math.sqrt(2 * f - f * f)
    ft = 0.3048006096012192
    p1, p2, p0, l0 = map(math.radians, (41.71666666666667, 42.68333333333333, 41.0, -71.5))
    m = lambda p: math.cos(p) / math.sqrt(1 - (e * math.sin(p)) ** 2)
    t = lambda p: math.tan(math.pi / 4 - p / 2) / ((1 - e * math.sin(p)) / (1 + e * math.sin(p))) ** (e / 2)
    n = (math.log(m(p1)) - math.log(m(p2))) / (math.log(t(p1)) - math.log(t(p2)))
    F = m(p1) / (n * t(p1) ** n)
    r0 = a * F * t(p0) ** n
    x, y = (E - 656166.6666666665) * ft, r0 - (N - 2460625.0) * ft
    r = math.copysign(math.hypot(x, y), n)
    tt = (r / (a * F)) ** (1 / n)
    lon = math.atan2(x, y) / n + l0
    lat = math.pi / 2 - 2 * math.atan(tt)
    for _ in range(8):
        lat = math.pi / 2 - 2 * math.atan(tt * ((1 - e * math.sin(lat)) / (1 + e * math.sin(lat))) ** (e / 2))
    return math.degrees(lon), math.degrees(lat)


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


def fetch_wards():
    z = zipfile.ZipFile(io.BytesIO(get(WARDS_ZIP)))
    shp, dbf = z.read('Wards.shp'), z.read('Wards.dbf')
    # dbf: find a field that holds the ward number
    n, hlen = struct.unpack('<IH', dbf[4:10])
    rlen = struct.unpack('<H', dbf[10:12])[0]
    fields, off = [], 32
    while dbf[off] != 0x0D:
        name = dbf[off:off + 11].split(b'\0')[0].decode()
        fields.append((name, dbf[off + 16]))
        off += 32
    recs = []
    for i in range(n):
        r, pos, rec = dbf[hlen + i * rlen: hlen + (i + 1) * rlen], 1, {}
        for name, ln in fields:
            rec[name] = r[pos:pos + ln].decode(errors='ignore').strip()
            pos += ln
        recs.append(rec)
    key = next(k for k in recs[0] if 'WARD' in k.upper())
    wards, off, i = [], 100, 0
    while off < len(shp):
        clen = struct.unpack('>i', shp[off + 4:off + 8])[0] * 2
        c = shp[off + 8: off + 8 + clen]
        off += 8 + clen
        if struct.unpack('<i', c[:4])[0] != 5:
            i += 1
            continue
        nparts, npts = struct.unpack('<ii', c[36:44])
        parts = list(struct.unpack('<%di' % nparts, c[44:44 + 4 * nparts])) + [npts]
        p0 = 44 + 4 * nparts
        xy = [struct.unpack('<dd', c[p0 + 16 * k: p0 + 16 * k + 16]) for k in range(npts)]
        rings = []
        for a, b in zip(parts, parts[1:]):
            pts = xy[a:b]
            mid = len(pts) // 2  # a closed ring starts and ends on the same point: simplify each half
            ring = simplify(pts[:mid + 1], 25)[:-1] + simplify(pts[mid:], 25)  # 25 US feet
            rings.append([[round(v, 5) for v in lcc_inverse(*p)] for p in ring])
        wards.append({'ward': str(int(float(recs[i][key]))), 'rings': rings})
        i += 1
    print(f'  wards: {len(wards)} ({", ".join(w["ward"] for w in wards)})')
    return sorted(wards, key=lambda w: int(w['ward']))


def decode_polyline(s):
    """Google encoded polyline -> [(lat, lon), ...] (MBTA shapes use it)."""
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
        pts.append((lat / 1e5, lon / 1e5))
    return pts


def fetch_bus_routes(route_ids, wards):
    """The usual path of each bus route serving Somerville (typical patterns, both directions): the stretch inside the
    city, carried on to the route's next stop outside it at each end (so a route can be followed out of town), then
    simplified. {route: {'name', 'long', 'paths': [[[lon, lat], ...], ...], 'ends': [[lon, lat], ...]}}"""
    def inside(lon, lat):
        for w in wards:
            for ring in w['rings']:
                c = False
                for k in range(len(ring)):
                    (x1, y1), (x2, y2) = ring[k], ring[k - 1]
                    if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                        c = not c
                if c:
                    return True
        return False
    meters = lambda a, b: math.hypot((a[0] - b[0]) * 82000, (a[1] - b[1]) * 111000)  # lon/lat to meters near 42.4°N
    names = {r['id']: r['attributes'] for r in json.loads(get('https://api-v3.mbta.com/routes', {'filter[id]': ','.join(sorted(route_ids))}))['data']}
    out = {}
    for rid in sorted(route_ids, key=lambda r: (len(r), r)):
        d = json.loads(get('https://api-v3.mbta.com/route_patterns', {'filter[route]': rid, 'include': 'representative_trip.shape'}))
        shapes = {i['id']: i['attributes']['polyline'] for i in d.get('included', []) if i['type'] == 'shape'}
        trips = {i['id']: (i['relationships'].get('shape', {}).get('data') or {}).get('id') for i in d.get('included', []) if i['type'] == 'trip'}
        stops = [(s['attributes']['longitude'], s['attributes']['latitude'])
                 for s in json.loads(get('https://api-v3.mbta.com/stops', {'filter[route]': rid})).get('data', [])
                 if s['attributes']['longitude'] is not None and not inside(s['attributes']['longitude'], s['attributes']['latitude'])]
        at_stop = lambda p: any(meters(p, q) < 80 for q in stops)  # stop short of busway loops (Sullivan Square)
        paths, ends = [], []
        for pat in d['data']:
            if pat['attributes'].get('typicality') != 1:
                continue
            shp = shapes.get(trips.get(pat['relationships']['representative_trip']['data']['id']))
            if not shp:
                continue
            pts = [(lo, la) for la, lo in decode_polyline(shp)]
            ins = [inside(*p) for p in pts]
            k = 0
            while k < len(pts):
                if not ins[k]:
                    k += 1; continue
                a = b = k
                while b + 1 < len(pts) and ins[b + 1]:
                    b += 1
                # walk out of the city on both ends to the next stop (at most 2 km)
                lo_, walked = a, 0
                while lo_ > 0 and walked < 2000 and not (lo_ < a and at_stop(pts[lo_])):
                    walked += meters(pts[lo_], pts[lo_ - 1]); lo_ -= 1
                hi_, walked = b, 0
                while hi_ < len(pts) - 1 and walked < 2000 and not (hi_ > b and at_stop(pts[hi_])):
                    walked += meters(pts[hi_], pts[hi_ + 1]); hi_ += 1
                run = pts[lo_:hi_ + 1]
                if len(run) >= 2:
                    paths.append(run)
                    for e, at in ((pts[lo_], lo_ < a), (pts[hi_], hi_ > b)):
                        if at and at_stop(e):
                            ends.append([round(e[0], 5), round(e[1], 5)])
                k = b + 1
        keep = [[[round(x, 5), round(y, 5)] for x, y in (simplify(run, 0.00004) if len(run) > 2 else run)] for run in paths]
        a = names.get(rid, {})
        out[rid] = {'name': a.get('short_name') or rid, 'long': a.get('long_name', ''), 'paths': keep, 'ends': ends}
    print(f'  bus routes: {len(out)}, {sum(len(p) for r in out.values() for p in r["paths"])} points')
    return out


def fetch_bus_stops():
    stops = {s['id']: s['attributes'] for s in json.loads(get(MBTA_STOPS))['data'] if s['attributes']['municipality'] == 'Somerville'}
    with tempfile.TemporaryFile() as tmp:
        tmp.write(get(MBTA_RIDERSHIP))
        z = zipfile.ZipFile(tmp)
        falls = sorted(n for n in z.namelist() if '_Fall_' in n and n.endswith('.csv'))
        latest = falls[-1]
        season = 'Fall ' + latest.rsplit('_', 1)[1][:4]
        board, routes = defaultdict(float), defaultdict(set)
        with z.open(latest) as fh:
            for row in csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig')):
                sid = row.get('GTFS stop_id')
                if sid in stops and row.get('Day Type') == 'Wkdy':
                    try:
                        board[sid] += float(row['Boardings'] or 0)
                    except ValueError:
                        pass
                    routes[sid].add(row['GTFS route_id'])
    out = [{'id': s, 'name': a['name'], 'lat': round(a['latitude'], 5), 'lon': round(a['longitude'], 5),
            'riders': round(board.get(s, 0)), 'routes': sorted(routes[s], key=lambda r: (len(r), r))}
           for s, a in stops.items()]
    out.sort(key=lambda s: -s['riders'])
    print(f'  bus stops: {len(out)}, {season}, {sum(s["riders"] for s in out)} weekday boardings')
    return {'season': season, 'stops': out}


# ---------- build ----------


def complaint_storms(daily, by_day, storms):
    """Smaller snows that 311 shows were a problem anyway ("found through 311"). Outside every snow storm's window,
    a run of days where sidewalk reports over 3 days reach 3% of that winter's sidewalk reports (and at least 30).
    A share of the winter, not a fixed count, because reporting grew several times over after 2023. The storm is the
    latest run of days with half an inch or more at Logan in the 4 days before the burst or during it (its last day
    is the id, as for snow storms). Bursts with no such snow are skipped (ice from rain, or a late wave)."""
    sw = {d: c.get('sidewalk', 0) for d, c in by_day.items()}
    win = lambda d: d.year - (d.month < 7)
    total = Counter()
    for d, n in sw.items():
        total[win(d)] += n
    taken = set()
    for st in storms:
        d, b = date.fromisoformat(st['start']) - timedelta(2), date.fromisoformat(st['end']) + timedelta(7)
        while d <= b:
            taken.add(d); d += timedelta(1)
    bursts, d, end = [], min(sw), max(sw)
    while d <= end:
        s3 = sum(sw.get(d + timedelta(k), 0) for k in range(3))
        if total[win(d)] and s3 >= max(30, 0.03 * total[win(d)]) and not any(d + timedelta(k) in taken for k in range(3)):
            if bursts and (d - bursts[-1][1]).days <= 3:
                bursts[-1][1] = d
            else:
                bursts.append([d, d])
        d += timedelta(1)
    out, used = [], set()
    for a, b in bursts:
        snowy = [a - timedelta(k) for k in range(-(b - a).days, 5)]
        snowy = sorted(x for x in snowy if daily.get(x.isoformat(), 0) >= 0.5)
        if not snowy:
            print(f'  311 burst {a}–{b}: no snow day of 0.5 in at Logan, skipped')
            continue
        e = s_ = snowy[-1]
        while daily.get((s_ - timedelta(1)).isoformat(), 0) >= 0.5:
            s_ -= timedelta(1)
        if e in used:
            continue
        used.add(e)
        span = [(s_ + timedelta(k)).isoformat() for k in range((e - s_).days + 1)]
        out.append({
            'start': s_.isoformat(), 'end': e.isoformat(), 'snow': round(sum(daily[x] for x in span), 1), 'kind': '311',
            'days': [[(e + timedelta(k)).isoformat(), daily.get((e + timedelta(k)).isoformat(), 0), dict(by_day[e + timedelta(k)])]
                     for k in range(-2, 8)],
        })
    print(f'  found through 311: {len(out)} smaller storms ({", ".join(st["end"] for st in out)})')
    return out

PERIOD_MAX_DAYS = 35  # a replay window (2 days before the first snow to the day after reports die down) is capped here


def snow_periods(daily, by_day, seeds):
    """Group snowfalls into snow periods, so a page shows the whole tail of sidewalk reports, not a fixed week.
    A period starts with a seed snowfall (3 inches or more, or a small snow found through 311). After its last snowfall,
    sidewalk reports have "died down" on the first of two days in a row at no more than 1/20 of the period's peak day
    so far, or 2 reports. If another snowfall (a run of days with half an inch or more at Logan) starts before that,
    it joins the period, emergency or not, and the count starts again after it. The window runs from 2 days before the
    first snow to the day after reports die down, capped at PERIOD_MAX_DAYS. Id: the period's last day of snow."""
    sw = lambda d: by_day[d].get('sidewalk', 0)
    snowy = lambda d: daily.get(d.isoformat(), 0) >= 0.5
    seed_at = {date.fromisoformat(st['start']): st for st in seeds}
    periods, taken = [], set()
    for seed in seeds:
        if seed['end'] in taken:
            continue
        first = date.fromisoformat(seed['start'])
        cap = first - timedelta(2) + timedelta(PERIOD_MAX_DAYS - 2)  # last day that fits in the window
        falls = [dict(seed)]
        taken.add(seed['end'])
        while True:
            end = date.fromisoformat(falls[-1]['end'])
            d, peak, clear, nxt = end + timedelta(1), max(sw(first + timedelta(k)) for k in range((end - first).days + 1)), None, None
            while d <= cap:
                if snowy(d):
                    nxt = d; break
                peak = max(peak, sw(d))
                thr = max(2, peak / 20)
                if sw(d) <= thr and sw(d + timedelta(1)) <= thr:
                    clear = d; break
                d += timedelta(1)
            if nxt is None:
                break
            b = nxt
            while snowy(b + timedelta(1)):
                b += timedelta(1)
            span = [(nxt + timedelta(k)).isoformat() for k in range((b - nxt).days + 1)]
            s_ = seed_at.get(nxt)
            falls.append({'start': nxt.isoformat(), 'end': b.isoformat(), 'snow': round(sum(daily[x] for x in span), 1),
                          'kind': s_['kind'] if s_ else 'small'})
            if s_:
                taken.add(s_['end'])
        last = date.fromisoformat(falls[-1]['end'])
        if clear is None:
            clear = min(cap, max(last, d))
        days_to = clear + timedelta(1)  # the window includes the day after reports die down
        rng = [(first - timedelta(2)) + timedelta(k) for k in range((days_to - first).days + 3)]
        periods.append({
            'id': last.isoformat(), 'start': first.isoformat(), 'end': last.isoformat(), 'clear': clear.isoformat(),
            'snow': round(sum(f['snow'] for f in falls), 1),
            'kind': 'snow' if any(f['kind'] == 'snow' for f in falls) else '311',
            'snowfalls': [{k: f[k] for k in ('start', 'end', 'snow', 'kind')} for f in falls],
            # days of sidewalk reports from the end of the first snowfall until they died down
            'lasted': (clear - date.fromisoformat(falls[0]['end'])).days,
            'aliases': sorted({f['end'] for f in falls if f['kind'] != 'small'} - {last.isoformat()}),
            'days': [[x.isoformat(), daily.get(x.isoformat(), 0), dict(by_day[x])] for x in rng],
        })
    # Windows never show a neighbor's snow or tail: they start no earlier than the day the previous period's reports
    # died down (a quiet day; it can hold the City's notice for the next storm) and end before the next period's first
    # snow day (Jan 18-19, 2026 used to end on Jan 25, the day the blizzard began).
    for k, p in enumerate(periods):
        lo = date.fromisoformat(p['start']) - timedelta(2)
        hi = date.fromisoformat(p['clear']) + timedelta(1)  # last day shown
        if k > 0:
            lo = max(lo, date.fromisoformat(periods[k - 1]['clear']))
        if k + 1 < len(periods):
            hi = min(hi, date.fromisoformat(periods[k + 1]['start']) - timedelta(1))
        p['from'], p['to'] = lo.isoformat(), hi.isoformat()
        p['days'] = [d for d in p['days'] if lo.isoformat() <= d[0] <= hi.isoformat()]
    print(f'  {len(seeds)} snowfalls in {len(periods)} snow periods')
    return periods


def write_raw(storms, windows, extra):
    """docs/data/raw/<id>/<source>.csv: the records behind each storm's counts. Collected rows (311, police, fire,
    Logan weather reports) plus the per-record lists already kept in the storm data (crashes, alerts, warnings,
    Somerville observers). Privacy as on the pages: streets without house numbers, medical calls without a street."""
    import shutil
    root = os.path.join(OUT, 'raw')
    if os.path.isdir(root):
        shutil.rmtree(root)
    for st, (sid, t0, t1) in zip(storms, windows):
        tables = {src: v for (k, src), v in storm_extras.RAW.items() if k == sid}
        at = lambda i: (t0 + timedelta(hours=i)).isoformat(timespec='minutes')
        x = {k: v.get(sid) for k, v in extra.items()}
        if x.get('crashes'):
            tables['crashes'] = (['date_hour', 'time', 'where', 'what', 'how', 'surface', 'weather', 'light', 'hurt', 'pedestrian', 'cyclist',
                                  'pedestrian_where', 'pedestrian_doing', 'hit_and_run'],
                                 [[at(c['i']), c.get('t', ''), c.get('where', ''), c.get('what', ''), c.get('how', ''), c.get('surface', ''),
                                   c.get('weather', ''), c.get('light', ''), c.get('hurt', ''), c.get('ped', 0), c.get('bike', 0),
                                   c.get('pedWhere', ''), c.get('pedDoing', ''), c.get('hitRun', '')] for c in x['crashes']])
        if x.get('alerts'):
            tables['mbta_alerts'] = (['created_hour', 'kind', 'route_or_station', 'header'], [[at(a[0]), a[1], a[2], a[3]] for a in x['alerts']])
        if x.get('warnings'):
            tables['nws_warnings'] = (['name', 'code', 'from', 'to'], [[w['name'], w['code'], w['from'], w['to']] for w in x['warnings']])
        if x.get('snowSomerville'):
            tables['snow_somerville'] = (['date', 'inches_avg', 'stations_reporting'], [list(map(str, d)) for d in x['snowSomerville']['days']])
        d = os.path.join(root, sid)
        os.makedirs(d, exist_ok=True)
        for src, (head, rows) in sorted(tables.items()):
            with open(os.path.join(d, f'{src}.csv'), 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(head)
                w.writerows(sorted(rows, key=lambda r: str(r[0])))
    print(f'  wrote docs/data/raw/ ({len(storms)} storms)')


def main():
    print('311 requests…'); reqs = fetch_311()
    print('Snowfall…'); daily = fetch_snow_daily('2015-07-01'); winters = fetch_snow_winters()

    # winters.json
    per = defaultdict(Counter)
    for t, g, _, _ in reqs:
        per[season_of(t)][g] += 1
    first311 = 2015
    write('winters.json', {
        'snow': [[s, winters[s]] for s in sorted(winters)],
        'requests': [[s, dict(per[s])] for s in sorted(per) if s >= first311 and s in winters],
        # median winter, 1991/92–2020/21 (the current 30-year climate normal period)
        'normal': round(statistics.median(winters[s] for s in range(1991, 2021)), 1) if all(s in winters for s in range(1991, 2021)) else None,
    })

    # storms.json: runs of consecutive days with half an inch or more at Logan, 3 inches or more in all.
    # (Until Nov 2026 the cutoff was a 6-inch day; small storms also leave ice and complaints, so they count now.
    # A storm's id, its last day of snow, is the same under both rules.)
    by_day = defaultdict(Counter)
    for t, g, _, _ in reqs:
        by_day[t.date()][g] += 1
    days = sorted(daily)
    storms, used = [], set()
    for d in days:
        if daily[d] >= 0.5 and d not in used:
            a = b = date.fromisoformat(d)
            while daily.get((a - timedelta(1)).isoformat(), 0) >= 0.5: a -= timedelta(1)
            while daily.get((b + timedelta(1)).isoformat(), 0) >= 0.5: b += timedelta(1)
            span = [(a + timedelta(k)).isoformat() for k in range((b - a).days + 1)]
            used.update(span)
            if sum(daily[x] for x in span) < STORM_MIN:
                continue
            storms.append({
                'start': a.isoformat(), 'end': b.isoformat(), 'snow': round(sum(daily[x] for x in span), 1),
                'days': [[(b + timedelta(k)).isoformat(), daily.get((b + timedelta(k)).isoformat(), 0), dict(by_day[b + timedelta(k)])]
                         for k in range(-2, 8)],
            })
    for st in storms:
        st['kind'] = 'snow'
    seeds = sorted(storms + complaint_storms(daily, by_day, storms), key=lambda st: st['end'])
    storms = snow_periods(daily, by_day, seeds)
    write('storms.json', {'storms': storms})

    print('Wards…'); wards = fetch_wards(); survey = fetch_ward_survey()
    write('wards.json', {'wards': wards, 'survey': survey})
    print('Bus stops and riders…'); bus = fetch_bus_stops()
    bus['routes'] = fetch_bus_routes({r for st in bus['stops'] for r in st['routes']}, wards); write('bus-stops.json', bus)

    def in_somerville(lon, lat):
        for w in wards:
            for ring in w['rings']:
                c = False
                for k in range(len(ring)):
                    (x1, y1), (x2, y2) = ring[k], ring[k - 1]
                    if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                        c = not c
                if c:
                    return True
        return False

    # Each storm's window: 2 days before its first snow day to 6 days after its last (06:00 to 00:00, local time).
    windows = []
    for st in storms:
        first = date.fromisoformat(st['start'])
        # from 6 a.m. on the first day shown to midnight after the last (see snow_periods: never a neighbor's days)
        t0 = datetime.combine(date.fromisoformat(st['from']), datetime.min.time()).replace(hour=6)
        t1 = min(datetime.combine(date.fromisoformat(st['to']) + timedelta(1), datetime.min.time()),
                 datetime.combine(first - timedelta(2) + timedelta(PERIOD_MAX_DAYS), datetime.min.time()))
        windows.append((st['id'], t0, t1))
    print('Extra sources for each storm…')
    routes = {r for s_ in bus['stops'] for r in s_['routes']}
    stop_ids = {s_['id'] for s_ in bus['stops']}
    # every bus stop inside the city today (not only the ones in the ridership file), to find which routes served it
    som_stops = {s_['id'] for s_ in json.loads(get('https://api-v3.mbta.com/stops', {'filter[route_type]': '3', 'page[limit]': '20000'}))['data']
                 if s_['attributes']['latitude'] and in_somerville(s_['attributes']['longitude'], s_['attributes']['latitude'])}
    buses = storm_extras.buses(cached, windows, som_stops, routes)
    then = {}
    for sid, _, _ in windows:  # alerts: today's routes plus the ones that served Somerville at the time (CT2 is also 747)
        r_ = set(routes) | set((buses.get(sid) or {}).get('routes', []))
        then[sid] = r_ | ({'747'} if 'CT2' in r_ else set()) | ({'CT2'} if '747' in r_ else set())
    extra = {
        'warnings': storm_extras.warnings(get, windows),
        'police': storm_extras.police(get, windows),
        'crashes': storm_extras.crashes(get, windows),
        'calls311': storm_extras.calls311(get, windows),
        'tEntries': storm_extras.t_entries(cached, windows),
        'bikes': storm_extras.bikes(cached, windows, in_somerville),
        'alerts': storm_extras.alerts(cached, windows, then, stop_ids),
        'snowSomerville': storm_extras.somerville_snow(get, windows, storms),
        'web': storm_extras.web_views(get, windows),
        'buses': buses,
        'subway': storm_extras.subway(cached, windows, get),
        'spending': storm_extras.spending(cached, windows),
        'fire': storm_extras.fire_dept(get, windows, CACHE),
        'snowDepth': storm_extras.snow_depth(get, windows),
    }

    MONTHS = 'January February March April May June July August September October November December'.split()
    for st, (sid, t0, t1) in zip(storms, windows):
        print(f'Replay {sid}…')
        wx = fetch_hourly_weather(t0.isoformat(), t1.isoformat(), sid)
        hours = []
        t = t0
        while t < t1:
            w = wx.get(t, {})
            hours.append([w.get('snow', 0), w.get('temp'), w.get('vis'), w.get('wind'), w.get('ice', 0)])
            t += timedelta(hours=1)
        # The storm: snowy hours at Logan, with lulls under 6 hours counted as the same storm. A storm over several
        # days can have longer lulls: it runs from the first to the last run of 3 or more snowy hours that overlaps its
        # snow days (a passing flurry doesn't start or end it, as in live storm mode). The window can include other snows.
        snowing = [k for k, w in sorted(wx.items()) if w['snow'] and t0 <= k < t1]
        runs, cur = [], []
        for k in snowing:
            if cur and (k - cur[-1]) > timedelta(hours=6):
                runs.append(cur); cur = []
            cur.append(k)
        if cur: runs.append(cur)
        falls = []
        for f in st['snowfalls']:  # each snowfall in the period: its own start, stop (and so deadline)
            lo = datetime.combine(date.fromisoformat(f['start']), datetime.min.time())
            hi = datetime.combine(date.fromisoformat(f['end']) + timedelta(1), datetime.min.time())
            near = [r for r in runs if r[-1] >= lo and r[0] < hi]
            if not near:
                continue
            real = [r for r in near if len(r) >= 3] or [max(near, key=len)]
            falls.append({'start': real[0][0].isoformat(timespec='minutes'), 'stop': (real[-1][-1] + timedelta(hours=1)).isoformat(timespec='minutes'),
                          'snow': f['snow']})
        if not falls:  # no snow reported in the hourly data at all: use the days
            falls = [{'start': f'{st["start"]}T06:00', 'stop': f'{st["end"]}T18:00', 'snow': st['snow']}]
        start, stop = datetime.fromisoformat(falls[0]['start']), datetime.fromisoformat(falls[-1]['stop'])
        req = defaultdict(lambda: [0] * len(GROUPS))
        wards_ = defaultdict(lambda: Counter())
        order = list(GROUPS)
        salting = Counter()
        for tt, g, ward, typ in reqs:
            if t0 <= tt < t1:
                storm_extras.raw(sid, '311_snow', ['created', 'group', 'type', 'ward'], [tt.isoformat(timespec='minutes'), g, typ, ward or ''])
                i = int((tt - t0).total_seconds() // 3600)
                req[i][order.index(g)] += 1
                if typ == 'Salting request':
                    salting[i] += 1
                if g == 'sidewalk' and ward:
                    wards_[i][ward] += 1
        a_, b_ = start.date(), (stop - timedelta(minutes=1)).date()
        title = (f'{MONTHS[a_.month - 1]} {a_.day}, {a_.year}' if a_ == b_ else
                 f'{MONTHS[a_.month - 1]} {a_.day}–{b_.day}, {a_.year}' if a_.month == b_.month else
                 f'{MONTHS[a_.month - 1]} {a_.day} – {MONTHS[b_.month - 1]} {b_.day}, {b_.year}')
        # what the City announced, for any snowfall in the period (a typed title only fits a single snowfall)
        city = {}
        for k in [sid] + st['aliases']:
            for key, val in CITY.get(k, {}).items():
                if key == 'notices':
                    city.setdefault('notices', []).extend(val)
                elif key == 'title' and len(st['snowfalls']) > 1:
                    continue
                else:
                    city.setdefault(key, val)
        write(f'storm-{sid}.json', {
            'id': sid, 'title': title,
            'from': t0.isoformat(timespec='minutes'), 'to': t1.isoformat(timespec='minutes'),
            **city,
            'groups': order,
            'snowStart': start.isoformat(timespec='minutes'),
            'snowStop': stop.isoformat(timespec='minutes'),
            'snowfalls': falls,
            'clear': st['clear'], 'lasted': st['lasted'],
            'snowTotal': st['snow'],  # same total as the storm's card in storms.json
            'hours': hours,
            'requests': {str(i): v for i, v in sorted(req.items())},
            'sidewalkByWard': {str(i): dict(v) for i, v in sorted(wards_.items())},
            'salting': sorted(salting.items()),
            'extra': {k: v.get(sid) for k, v in extra.items()},
            'sources': {
                'weather': 'Hourly observations at Boston Logan (BOS), Iowa Environmental Mesonet ASOS archive',
                'requests': '311 Service, Information, and Feedback Requests, data.somervillema.gov (4pyi-uqq6)',
                'snowfall': 'NOAA daily snowfall, Boston, via ACIS (BOSthr)',
            },
        })
    write_raw(storms, windows, extra)
    write('sources.json', {'note': 'Every download behind docs/data, with its address, when it was fetched, its size and SHA-256. '
                                   'Big archives are kept in .cache/ (not published); a new run can compare fingerprints.',
                           'generated': datetime.now().isoformat(timespec='seconds'),
                           'downloads': sorted(PROV.values(), key=lambda p: p['url'])})
    # old storm files whose snowfall is now part of a longer period (its page forwards there)
    keep = {f'storm-{st["id"]}.json' for st in storms}
    for f in os.listdir(OUT):
        if f.startswith('storm-') and f.endswith('.json') and f not in keep:
            os.remove(os.path.join(OUT, f))
    print('Pages…'); import build_pages; build_pages.main()
    print('Done.')


if __name__ == '__main__':
    main()
