#!/usr/bin/env python3
"""Collect the public data behind the storm replay and the charts, and write small JSON files to docs/data/.

Run with `npm run data` (Python 3 standard library only, no API keys). Re-run each fall before the first storm.
Sources, caveats and what each file holds: research/data-sources.md.

  docs/data/winters.json        Boston snowfall per winter since 1891, and Somerville 311 snow requests per winter
  docs/data/storms.json         every 6-inch-plus storm since July 2015: daily snowfall and 311 requests around it
  docs/data/wards.json          Somerville ward outlines (lon/lat), simplified
  docs/data/bus-stops.json      MBTA bus stops in Somerville with average weekday boardings
  docs/data/storm-<id>.json     each big storm hour by hour (id = last day of snow): weather at Logan, 311 requests, City notices
"""
import csv, io, json, math, os, statistics, struct, sys, tempfile, time, urllib.parse, urllib.request, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'data')
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

# Every big storm in storms.json gets an hour-by-hour replay file, named by its last day of snow (storm-<id>.json).
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


def get(url, params=None, data=None, tries=4):
    if params:
        url += ('&' if '?' in url else '?') + urllib.parse.urlencode(params)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, **({'Content-Type': 'application/json'} if data else {})})
            with urllib.request.urlopen(req, timeout=300) as r:
                return r.read()
        except Exception as e:  # network hiccup: back off and retry
            if i == tries - 1:
                raise
            print(f'  retry {url[:70]}… ({e})', file=sys.stderr)
            time.sleep(2 ** (i + 1))


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
            out.append((datetime.strptime(r['date_created'][:16], '%Y-%m-%d %H:%M'), g, r.get('ward')))
    print(f'  311: {len(out)} snow requests')
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


def fetch_hourly_weather(t0, t1):
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
        h = hours.setdefault(k, {'snow': 0, 'temp': None, 'vis': None, 'wind': None, 'wx': ''})
        h['snow'] = max(h['snow'], snow)
        if r['tmpf'] != 'M': h['temp'] = round(float(r['tmpf']))
        if r['vsby'] != 'M': h['vis'] = float(r['vsby'])
        if r['sknt'] != 'M': h['wind'] = round(float(r['sknt']))
        if wx: h['wx'] = wx
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

def main():
    print('311 requests…'); reqs = fetch_311()
    print('Snowfall…'); daily = fetch_snow_daily('2015-07-01'); winters = fetch_snow_winters()

    # winters.json
    per = defaultdict(Counter)
    for t, g, _ in reqs:
        per[season_of(t)][g] += 1
    first311 = 2015
    write('winters.json', {
        'snow': [[s, winters[s]] for s in sorted(winters)],
        'requests': [[s, dict(per[s])] for s in sorted(per) if s >= first311 and s in winters],
        # median winter, 1991/92–2020/21 (the current 30-year climate normal period)
        'normal': round(statistics.median(winters[s] for s in range(1991, 2021)), 1) if all(s in winters for s in range(1991, 2021)) else None,
    })

    # storms.json: consecutive snow days with a 6-inch-plus day
    by_day = defaultdict(Counter)
    for t, g, _ in reqs:
        by_day[t.date()][g] += 1
    days = sorted(daily)
    storms, used = [], set()
    for d in days:
        if daily[d] >= 6 and d not in used:
            a = b = date.fromisoformat(d)
            while daily.get((a - timedelta(1)).isoformat(), 0) >= 0.5: a -= timedelta(1)
            while daily.get((b + timedelta(1)).isoformat(), 0) >= 0.5: b += timedelta(1)
            span = [(a + timedelta(k)).isoformat() for k in range((b - a).days + 1)]
            used.update(span)
            storms.append({
                'start': a.isoformat(), 'end': b.isoformat(), 'snow': round(sum(daily[x] for x in span), 1),
                'days': [[(b + timedelta(k)).isoformat(), daily.get((b + timedelta(k)).isoformat(), 0), dict(by_day[b + timedelta(k)])]
                         for k in range(-2, 8)],
            })
    write('storms.json', {'storms': storms})

    print('Wards…'); write('wards.json', {'wards': fetch_wards()})
    print('Bus stops and riders…'); write('bus-stops.json', fetch_bus_stops())

    MONTHS = 'January February March April May June July August September October November December'.split()
    for st in storms:
        sid = st['end']
        first, last = date.fromisoformat(st['start']), date.fromisoformat(st['end'])
        t0 = datetime.combine(first - timedelta(2), datetime.min.time()).replace(hour=6)
        t1 = datetime.combine(last + timedelta(6), datetime.min.time())
        print(f'Replay {sid}…')
        wx = fetch_hourly_weather(t0.isoformat(), t1.isoformat())
        hours = []
        t = t0
        while t < t1:
            w = wx.get(t, {})
            hours.append([w.get('snow', 0), w.get('temp'), w.get('vis'), w.get('wind')])
            t += timedelta(hours=1)
        # The storm: snowy hours at Logan, with lulls under 6 hours counted as the same storm.
        # Pick the run that overlaps the storm's snow days (the window can include other, smaller snows).
        snowing = [k for k, w in sorted(wx.items()) if w['snow'] and t0 <= k < t1]
        runs, cur = [], []
        for k in snowing:
            if cur and (k - cur[-1]) > timedelta(hours=6):
                runs.append(cur); cur = []
            cur.append(k)
        if cur: runs.append(cur)
        lo, hi = datetime.combine(first, datetime.min.time()), datetime.combine(last + timedelta(1), datetime.min.time())
        near = [r for r in runs if r[-1] >= lo and r[0] < hi] or runs
        main_run = max(near, key=len)
        start, stop = main_run[0], main_run[-1] + timedelta(hours=1)
        req = defaultdict(lambda: [0] * len(GROUPS))
        wards = defaultdict(lambda: Counter())
        order = list(GROUPS)
        for tt, g, ward in reqs:
            if t0 <= tt < t1:
                i = int((tt - t0).total_seconds() // 3600)
                req[i][order.index(g)] += 1
                if g == 'sidewalk' and ward:
                    wards[i][ward] += 1
        a_, b_ = start.date(), (stop - timedelta(minutes=1)).date()
        title = (f'{MONTHS[a_.month - 1]} {a_.day}, {a_.year}' if a_ == b_ else
                 f'{MONTHS[a_.month - 1]} {a_.day}–{b_.day}, {a_.year}' if a_.month == b_.month else
                 f'{MONTHS[a_.month - 1]} {a_.day} – {MONTHS[b_.month - 1]} {b_.day}, {b_.year}')
        write(f'storm-{sid}.json', {
            'id': sid, 'title': title,
            'from': t0.isoformat(timespec='minutes'), 'to': t1.isoformat(timespec='minutes'),
            **CITY.get(sid, {}),
            'groups': order,
            'snowStart': start.isoformat(timespec='minutes'),
            'snowStop': stop.isoformat(timespec='minutes'),
            'snowTotal': st['snow'],  # same total as the storm's card in storms.json
            'hours': hours,
            'requests': {str(i): v for i, v in sorted(req.items())},
            'sidewalkByWard': {str(i): dict(v) for i, v in sorted(wards.items())},
            'sources': {
                'weather': 'Hourly observations at Boston Logan (BOS), Iowa Environmental Mesonet ASOS archive',
                'requests': '311 Service, Information, and Feedback Requests, data.somervillema.gov (4pyi-uqq6)',
                'snowfall': 'NOAA daily snowfall, Boston, via ACIS (BOSthr)',
            },
        })
    print('Done.')


if __name__ == '__main__':
    main()
