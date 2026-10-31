"""Extra sources for the storm replays, collected per storm window (Somerville local time, hourly).

Used by fetch_data.py. Every function takes the list of windows [(id, t0, t1), ...] with naive local datetimes
and returns {id: {...}} with values indexed by hour from t0. Missing coverage returns None, so the page can
say "not available" instead of showing a false zero. Big downloads are cached in .cache/ (git-ignored).

  warnings   National Weather Service watches/warnings/advisories for Somerville's zone (MAZ014), IEM VTEC archive
  police     Somerville police dispatch (CAD): snow emergency tows and disabled vehicles, per 8-hour shift (2017+)
  crashes    Somerville police crash reports (March 2018+)
  calls311   Somerville 311 parking and trash requests per hour (non-snow types that rise with storms)
  tEntries   MBTA gated entries at stations in Somerville per hour, and the same hour's average over the 4 previous weeks
  bikes      Bluebikes trips starting at stations inside Somerville per hour, with the same 4-week baseline
  alerts     MBTA service alerts created during the window on Somerville bus routes and stations (2020+)
"""
import csv, io, json, os, sys, urllib.parse, zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

TZ = ZoneInfo('America/New_York')
UTC = timezone.utc
HOUR = timedelta(hours=1)

VTEC = 'https://mesonet.agron.iastate.edu/json/vtec_events_byugc.php'
CAD = 'https://data.somervillema.gov/resource/mdb2-mgc7.json'
CRASHES = 'https://data.somervillema.gov/resource/mtik-28va.json'
S311 = 'https://data.somervillema.gov/resource/4pyi-uqq6.json'
GSE_ZIP = 'https://www.arcgis.com/sharing/rest/content/items/7859894afb5641ce91a2bb03599fdf5b/data'
BIKES = 'https://s3.amazonaws.com/hubway-data/'
ALERT_ZIPS = {  # MBTA Service Alerts archives (CSV collections on the MBTA open data portal)
    '2020-2023': 'https://www.arcgis.com/sharing/rest/content/items/21ea74717cda441db3ae40d2cbc79a15/data',
    '2024': 'https://www.arcgis.com/sharing/rest/content/items/f960d5089e164fb8b6c6936c70719d72/data',
    '2025': 'https://www.arcgis.com/sharing/rest/content/items/ef115f7cf6684360b040b6d1d033eff0/data',
    '2026': 'https://www.arcgis.com/sharing/rest/content/items/d233f1820cf54139bd18e75e30dd2c6c/data',
}
STATIONS = {'place-davis': 'Davis', 'place-asmql': 'Assembly', 'place-unsqu': 'Union Square', 'place-esomr': 'East Somerville',
            'place-gilmn': 'Gilman Square', 'place-mgngl': 'Magoun Square', 'place-balsq': 'Ball Square'}
PARKING = ['Illegal parking', 'Car booted/towed inquiry', 'Parking information']
TRASH = ['Verification of sanitation schedule', 'Trash questions', 'Trash/recycling out too early or late']
SHIFT_START = {'Day': 8, 'First': 16, 'Last': 0}  # police shifts: Day 8–16, First Half 16–24, Last Half 0–8


def _local(iso_utc):
    return datetime.fromisoformat(iso_utc.replace('Z', '+00:00')).astimezone(TZ).replace(tzinfo=None)


def _idx(t, t0):
    return int((t - t0).total_seconds() // 3600)


# ---------- NWS ----------
def warnings(get, windows):
    out = {}
    for sid, t0, t1 in windows:
        q = {'ugc': 'MAZ014', 'sdate': (t0 - timedelta(2)).date().isoformat(), 'edate': (t1 + timedelta(1)).date().isoformat()}
        ev = json.loads(get(VTEC + '?' + urllib.parse.urlencode(q))).get('events', [])
        items = []
        for e in ev:
            a, b = _local(e['issue']), _local(e['expire'])
            if b <= a or b <= t0 or a >= t1:
                continue  # upgraded or cancelled before it began, or outside the window
            items.append({'name': e['name'], 'from': a.isoformat(timespec='minutes'), 'to': b.isoformat(timespec='minutes'), 'code': e['phenomena'] + '.' + e['significance']})
        out[sid] = sorted(items, key=lambda x: x['from'])
    return out


# ---------- City open data ----------
def police(get, windows):
    years = sorted({y for _, t0, t1 in windows for y in (t0.year, t1.year)})
    q = {'$select': 'day_and_month,year,police_shift,ward,inctype', '$where': "inctype in ('SNOEMTOW','DISABLED MV') and year in (%s)" % ','.join("'%d'" % y for y in years), '$limit': 50000}
    rows = json.loads(get(CAD, q))
    have = {int(r['year']) for r in json.loads(get(CAD, {'$select': 'year', '$group': 'year'}))}
    out = {}
    for sid, t0, t1 in windows:
        if t0.year not in have:
            out[sid] = None
            continue
        tows, disabled, wards = Counter(), Counter(), Counter()
        for r in rows:
            m, d = map(int, r['day_and_month'].split('/'))
            start = datetime(int(r['year']), m, d, SHIFT_START[r['police_shift'].split()[0]])
            if not (t0 <= start < t1):
                continue
            i = _idx(start, t0)
            if r['inctype'] == 'SNOEMTOW':
                tows[i] += 1
                if r.get('ward'): wards[r['ward']] += 1
            else:
                disabled[i] += 1
        out[sid] = {'tows': sorted(tows.items()), 'disabled': sorted(disabled.items()), 'towsByWard': dict(wards)}
    return out


def crashes(get, windows):
    out = {}
    for sid, t0, t1 in windows:
        if t1 < datetime(2018, 3, 23):
            out[sid] = None
            continue
        q = {'$select': 'dtcrash,roadsurfdesc,nonmotoristpedestrian', '$where': f"dtcrash >= '{t0.isoformat()}' and dtcrash < '{t1.isoformat()}'", '$limit': 1000}
        rows = json.loads(get(CRASHES, q))
        out[sid] = [[_idx(datetime.fromisoformat(r['dtcrash'][:16]), t0), (r.get('roadsurfdesc') or '').strip().title(), int(r.get('nonmotoristpedestrian') or 0) > 0] for r in rows]
    return out


def calls311(get, windows):
    out = {}
    types = PARKING + TRASH
    for sid, t0, t1 in windows:
        q = {'$select': 'type,date_created', '$where': "type in (%s) and date_created >= '%s' and date_created < '%s'" % (','.join("'%s'" % t for t in types), t0.isoformat(), t1.isoformat()), '$limit': 20000}
        park, trash = Counter(), Counter()
        for r in json.loads(get(S311, q)):
            i = _idx(datetime.strptime(r['date_created'][:16], '%Y-%m-%d %H:%M'), t0)
            (park if r['type'] in PARKING else trash)[i] += 1
        out[sid] = {'parking': sorted(park.items()), 'trash': sorted(trash.items())}
    return out


# ---------- baselines ----------
def _with_baseline(counts, t0, t1, first_day):
    """Hourly series for [t0, t1) plus the average of the same hour 7, 14, 21 and 28 days earlier (weeks with data only)."""
    n = int((t1 - t0).total_seconds() // 3600)
    now = [counts.get(t0 + k * HOUR, 0) for k in range(n)]
    base = []
    for k in range(n):
        t = t0 + k * HOUR
        prev = [counts.get(t - timedelta(weeks=w), 0) for w in (1, 2, 3, 4) if (t - timedelta(weeks=w)).date() >= first_day]
        base.append(round(sum(prev) / len(prev), 1) if prev else None)
    return now, base


# ---------- MBTA gated station entries (30-minute counts, 2014+) ----------
def t_entries(cached, windows):
    z = zipfile.ZipFile(cached('gse_by_year.zip', GSE_ZIP))
    need = defaultdict(set)  # year -> dates
    for _, t0, t1 in windows:
        d = (t0 - timedelta(weeks=4)).date()
        while d <= t1.date():
            need[d.year].add(d.isoformat()); d += timedelta(1)
    counts, seen_days = Counter(), set()
    names = set(STATIONS.values())
    for y, days in sorted(need.items()):
        f = next((n for n in z.namelist() if n.endswith(f'GSE_{y}.csv')), None)
        if not f:
            continue
        print(f'    station entries {y}…', file=sys.stderr)
        with z.open(f) as fh:
            for r in csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig')):
                if r['service_date'] in days:
                    seen_days.add(r['service_date'])
                    if r['station_name'] in names or r['stop_id'] in STATIONS:
                        h = int(r['time_period'].strip('()')[:2])
                        counts[datetime.fromisoformat(r['service_date']) + h * HOUR] += float(r['gated_entries'] or 0)
    out = {}
    for sid, t0, t1 in windows:
        if t0.date().isoformat() not in seen_days:
            out[sid] = None
            continue
        first = min(date.fromisoformat(d) for d in seen_days)
        now, base = _with_baseline(counts, t0, t1, first)
        out[sid] = {'now': [round(v) for v in now], 'base': base}
    return out


# ---------- Bluebikes (trips per month, 2016+) ----------
def bikes(cached, windows, inside):
    months = sorted({(d.year, d.month) for _, t0, t1 in windows for d in (t0 - timedelta(weeks=4), t0, t1)})
    counts, have, where = Counter(), set(), {}
    for y, m in months:
        name = f'{y}{m:02d}-{"hubway" if (y, m) < (2018, 5) else "bluebikes"}-tripdata.zip'
        try:
            z = zipfile.ZipFile(cached(name, BIKES + name))
        except Exception as e:
            print(f'    bikes {name}: {e}', file=sys.stderr)
            continue
        f = next(n for n in z.namelist() if n.endswith('.csv') and not n.startswith('__'))
        print(f'    bikes {y}-{m:02d}…', file=sys.stderr)
        have.add((y, m))
        with z.open(f) as fh:
            for r in csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig')):
                st = r.get('started_at') or r.get('starttime')
                lat = r.get('start_lat') or r.get('start station latitude')
                lon = r.get('start_lng') or r.get('start station longitude')
                if not st or not lat or not lon:
                    continue
                key = (lat, lon)
                if key not in where:
                    try: where[key] = inside(float(lon), float(lat))
                    except ValueError: where[key] = False
                if where[key]:
                    counts[datetime.fromisoformat(st[:13] + ':00')] += 1
    out = {}
    for sid, t0, t1 in windows:
        if (t0.year, t0.month) not in have or (t1.year, t1.month) not in have and t1.day > 1:
            out[sid] = None
            continue
        first = min(date(y, m, 1) for y, m in have)
        now, base = _with_baseline(counts, t0, t1, first)
        out[sid] = {'now': now, 'base': base}
    return out


# ---------- MBTA service alerts (2020+) ----------
def alerts(cached, windows, routes, stops):
    files = {}
    for key, url in ALERT_ZIPS.items():
        try:
            files[key] = zipfile.ZipFile(cached(f'alerts-{key}.zip', url))
        except Exception as e:
            print(f'    alerts {key}: {e}', file=sys.stderr)
    out = {}
    for sid, t0, t1 in windows:
        if t0 < datetime(2020, 1, 1):
            out[sid] = None
            continue
        months = sorted({(d.year, d.month) for d in (t0, t1)})
        seen = {}
        for y, m in months:
            z = files.get('2020-2023' if y <= 2023 else str(y))
            if not z:
                continue
            f = next((n for n in z.namelist() if n.endswith((f'alerts_{y}_{m:02d}.csv', f'{y}-{m:02d}_ALERTS.csv'))), None)
            if not f:
                continue
            with z.open(f) as fh:
                for r in csv.DictReader(io.TextIOWrapper(fh, encoding='utf-8-sig')):
                    if r['alert_id'] in seen or not r.get('created_dt'):
                        continue
                    t = _local(r['created_dt'])
                    if not (t0 <= t < t1):
                        continue
                    if r['route_id'] in routes or r['stop_id'] in stops or r['stop_id'] in STATIONS:
                        eff = r['effect']
                        head = ' '.join(r['header'].split())
                        kind = ('access' if eff == 'ACCESSIBILITY_ISSUE' else 'detour' if eff in ('DETOUR', 'STOP_MOVED', 'STOP_CLOSURE')
                                else 'reduced' if eff in ('REDUCED_SERVICE', 'NO_SERVICE', 'SUSPENSION', 'MODIFIED_SERVICE', 'SHUTTLE')
                                else 'delay' if 'delay' in head.lower() or eff == 'DELAY' else 'other')
                        label = r['route_id'] or STATIONS.get(r['stop_id'], '')
                        seen[r['alert_id']] = [_idx(t, t0), kind, label, head[:170]]
        out[sid] = sorted(seen.values())
    return out
