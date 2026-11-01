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
  snowSomerville  daily snowfall from volunteer observers inside Somerville (CoCoRaHS via ACIS), and the storm total
  web        daily views of the City's snow pages (top 20 pages per day; the City's data covers 2020 to May 2023)
  buses      MBTA bus trips run and median minutes late on routes serving Somerville, per hour, with the 4-week baseline (2020+)
"""
import csv, io, json, os, re, sys, urllib.parse, zipfile
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


def _nice(v):
    """'COLLISION WITH PARKED MOTOR VEHICLE  ' -> 'Collision with parked motor vehicle'; '' for empty/unknown."""
    v = ' '.join((v or '').split())
    return '' if v.upper() in ('', 'UNKNOWN', 'NOT REPORTED', 'OTHER', 'NONE') else v[0].upper() + v[1:].lower()


def _street(addr):
    """Street or intersection only, no house number: '230 SOMERVILLE AVE. Somerville, MA' -> 'Somerville Ave'.
    The City publishes exact addresses; we trim them so a single crash can't point at a home."""
    a = re.sub(r',?\s*Somerville,?\s*MA.*$', '', addr or '', flags=re.I).strip()
    a = re.sub(r'^\d+[A-Z]?(-\d+)?\s+', '', a).rstrip('.').strip()
    return ' '.join(w.capitalize() if not re.match(r'^(and|at|of)$', w, re.I) else w.lower() for w in a.split())


def crashes(get, windows):
    """Crash reports in each window, with what a reader needs to understand one crash (see the dataset's columns)."""
    out = {}
    for sid, t0, t1 in windows:
        if t1 < datetime(2018, 3, 23):
            out[sid] = None
            continue
        q = {'$where': f"dtcrash >= '{t0.isoformat()}' and dtcrash < '{t1.isoformat()}'", '$limit': 1000, '$order': 'dtcrash'}
        items = []
        for r in json.loads(get(CRASHES, q)):
            t = datetime.fromisoformat(r['dtcrash'][:16])
            if not (t0 <= t < t1):  # the API compares text ('2026-03-01 09:42' < '2026-03-01T00:00'): check the real time
                continue
            n = lambda k: int(float(r.get(k) or 0))
            hurt = ('fatal' if n('fatalinjury') else 'serious' if n('suspectedseriousinjury') else 'minor' if n('suspectedminorinjury')
                    else 'possible' if n('possibleinjury') else 'none' if n('noapparentinjury') else '')
            items.append({
                'i': _idx(t, t0), 't': t.strftime('%H:%M'), 'where': _street(r.get('address')),
                'what': _nice(r.get('hrmfeventdesc2')), 'how': _nice(r.get('manrcolldesc')),
                'surface': _nice(r.get('roadsurfdesc')), 'weather': _nice(r.get('weathcond1desc')), 'light': _nice(r.get('ambntlightdesc')),
                'hurt': hurt, 'ped': n('nonmotoristpedestrian'), 'bike': n('nonmotoristcyclist'),
                'pedWhere': _nice(r.get('nonmtrstlocdesc')), 'pedDoing': _nice(r.get('nonmtrstactdesc')),
                'hitRun': (r.get('hitrunflag') or '').strip().upper() == 'Y',
            })
        out[sid] = items
    return out


def calls311(get, windows):
    out = {}
    types = PARKING + TRASH
    for sid, t0, t1 in windows:
        q = {'$select': 'type,date_created', '$where': "type in (%s) and date_created >= '%s' and date_created < '%s'" % (','.join("'%s'" % t for t in types), t0.isoformat(), t1.isoformat()), '$limit': 20000}
        park, trash = Counter(), Counter()
        for r in json.loads(get(S311, q)):
            t = datetime.strptime(r['date_created'][:16], '%Y-%m-%d %H:%M')
            if not (t0 <= t < t1):  # see crashes(): text comparison lets the next morning in
                continue
            i = _idx(t, t0)
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
        d = (t0 - timedelta(weeks=4, days=1)).date()  # one extra service day: its after-midnight entries fall on the first day
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
                        # A service day runs past midnight: periods before 3 a.m. belong to the next calendar day.
                        day = datetime.fromisoformat(r['service_date']) + (timedelta(days=1) if h < 3 else timedelta(0))
                        counts[day + h * HOUR] += float(r['gated_entries'] or 0)
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


# ---------- Somerville's own snowfall (CoCoRaHS volunteer observers, via ACIS) ----------
ACIS_META = 'https://data.rcc-acis.org/StnMeta'
ACIS_DATA = 'https://data.rcc-acis.org/StnData'


def somerville_snow(get, windows, storms):
    """Daily snowfall reported by volunteer observers inside Somerville (24 hours to about 7 a.m.), averaged over
    the stations reporting that day, and the storm total from the first snow day to the morning after the last."""
    meta = json.loads(get(ACIS_META, data=json.dumps({'bbox': '-71.135,42.37,-71.07,42.42', 'elems': 'snow', 'meta': 'name,sids,valid_daterange'}).encode()))['meta']
    stations = [m for m in meta if m['name'].upper().startswith('SOMERVILLE')]
    span = {st['end']: (st['start'], st['end']) for st in storms}
    out = {}
    for sid, t0, t1 in windows:
        per_day = defaultdict(list)
        names = set()
        for m in stations:
            a, b = m['valid_daterange'][0]
            if b < t0.date().isoformat() or a > t1.date().isoformat():
                continue
            q = {'sid': m['sids'][0].split()[0], 'sdate': t0.date().isoformat(), 'edate': t1.date().isoformat(), 'elems': [{'name': 'snow'}]}
            for d, v in json.loads(get(ACIS_DATA, data=json.dumps(q).encode())).get('data', []):
                if v not in ('M', 'S', ''):
                    per_day[d].append(0.0 if v == 'T' else float(v.rstrip('A')))
                    names.add(m['name'])
        first, last = span[sid]
        storm_days = [(date.fromisoformat(first) + timedelta(k)).isoformat() for k in range((date.fromisoformat(last) - date.fromisoformat(first)).days + 2)]
        # Observers skip some days; a missing day may mean no snow or no report. Sum what was reported and say
        # when some storm days have no report ("partial").
        got = [d for d in storm_days if per_day.get(d)]
        total = round(sum(sum(per_day[d]) / len(per_day[d]) for d in got), 1) if got else None
        out[sid] = ({'days': [[d, round(sum(v) / len(v), 1), len(v)] for d, v in sorted(per_day.items())], 'total': total,
                     'partial': len(got) < len(storm_days), 'stations': sorted(names)} if got and total else None)
    return out


# ---------- City website: views of snow pages (top 20 pages per day, 2020 to May 2023) ----------
WEB = 'https://data.somervillema.gov/resource/754v-8e35.json'


def web_views(get, windows):
    have = json.loads(get(WEB, {'$select': 'min(date) as a, max(date) as b'}))[0]
    lo, hi = datetime.fromisoformat(have['a'][:10]), datetime.fromisoformat(have['b'][:10])
    out = {}
    for sid, t0, t1 in windows:
        if t0 - timedelta(weeks=4) < lo or t1 - timedelta(days=1) > hi:
            out[sid] = None
            continue
        a = (t0 - timedelta(weeks=4)).date().isoformat()
        q = {'$select': 'date,url,pageviews', '$where': f"date >= '{a}' and date < '{t1.date().isoformat()}' and upper(url) like '%SNOW%'", '$limit': 5000}
        day = Counter()
        for r in json.loads(get(WEB, q)):
            day[r['date'][:10]] += int(r['pageviews'])
        days, k = [], t0.replace(hour=0)
        while k < t1:
            days.append([_idx(max(k, t0), t0), day.get(k.date().isoformat(), 0)])
            k += timedelta(days=1)
        before = [day.get((t0 - timedelta(days=n)).date().isoformat(), 0) for n in range(1, 29)]
        out[sid] = {'days': days, 'base': round(sum(before) / len(before))}
    return out


# ---------- MBTA bus arrival and departure times (2020+) ----------
BUS_ZIPS = {
    2020: 'https://www.arcgis.com/sharing/rest/content/items/4c1293151c6c4a069d49e6b85ee68ea4/data',
    2021: 'https://www.arcgis.com/sharing/rest/content/items/2d415555f63b431597721151a7e07a3e/data',
    2022: 'https://www.arcgis.com/sharing/rest/content/items/ef464a75666349f481353f16514c06d0/data',
    2023: 'https://www.arcgis.com/sharing/rest/content/items/b7b36fdb7b3a4728af2fccc78c2ca5b7/data',
    2024: 'https://www.arcgis.com/sharing/rest/content/items/96c77138c3144906bce93d0257531b6a/data',
    2025: 'https://www.arcgis.com/sharing/rest/content/items/924df13d845f4907bb6a6c3ed380d57a/data',
    2026: 'https://www.arcgis.com/sharing/rest/content/items/9d8a8cad277545c984c1b25ed10b7d3c/data',
}
_T0 = datetime(1900, 1, 1)


def buses(cached, windows, routes):
    """Per hour, on bus routes that serve Somerville: trips that left their first stop, and the median minutes
    late at timepoints; each with the same hour's value on the 4 weeks before."""
    want = {r.lstrip('0') for r in routes}
    need_days, months = set(), set()
    for _, t0, t1 in windows:
        if t0.year < 2020 or (t0 - timedelta(weeks=4)).year < 2020:
            continue
        d = (t0 - timedelta(weeks=4)).date()
        while d <= t1.date():
            need_days.add(d.isoformat()); months.add((d.year, d.month)); d += timedelta(1)
    trips, late = Counter(), defaultdict(list)
    have_months = set()
    MON = {m: k + 1 for k, m in enumerate('Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split())}

    def file_months(name, y):
        """Months a file covers: monthly '..._2021-12.csv', or quarterly '... Oct-Dec 2020.csv' (2020)."""
        base = name.rsplit('/', 1)[-1]
        if base.endswith(f'_{y}-' + base[-6:-4] + '.csv'):
            return {int(base[-6:-4])}
        for a in MON:
            for b in MON:
                if f'{a}-{b} {y}' in base or f'{a}-{b[:3]}' in base and str(y) in base:
                    return set(range(MON[a], MON[b] + 1))
        return set()

    def when(v):
        """'1900-01-01 05:05:00.000' or '1900-01-01T05:05:00Z' -> datetime; None for 'NA' or empty."""
        if not v or v == 'NA':
            return None
        return datetime.strptime(v.replace('T', ' ')[:19], '%Y-%m-%d %H:%M:%S')

    for y in sorted({y for y, _ in months}):
        try:
            z = zipfile.ZipFile(cached(f'bus-{y}.zip', BUS_ZIPS[y]))
        except Exception as e:
            print(f'    buses {y}: {e}', file=sys.stderr)
            continue
        wanted = {mm for yy, mm in months if yy == y}
        for f in sorted(n for n in z.namelist() if n.endswith('.csv')):
            got = file_months(f, y) & wanted
            if not got:
                continue
            print(f'    buses {y} {sorted(got)}…', file=sys.stderr)
            have_months.update((y, m) for m in got)
            with z.open(f) as fh:
                rd = csv.reader(io.TextIOWrapper(fh, encoding='utf-8-sig'))
                head = [h.strip().lower().replace(' ', '') for h in next(rd)]
                col = {k: head.index(k) for k in head}
                ci = lambda *names: next(col[n] for n in names if n in col)
                i_day, i_rt, i_pt = ci('service_date', 'servicedate'), ci('route_id', 'route'), ci('point_type', 'pointtype')
                i_sch, i_act = ci('scheduled'), ci('actual')
                for r in rd:
                    if r[i_rt].lstrip('0') not in want or r[i_day][:10] not in need_days:
                        continue
                    a_ = when(r[i_act])
                    if a_ is None:
                        continue
                    base = datetime.fromisoformat(r[i_day][:10])
                    act = base + (a_ - _T0)
                    k = act.replace(minute=0, second=0, microsecond=0)
                    if r[i_pt] == 'Startpoint':
                        trips[k] += 1
                    else:
                        s_ = when(r[i_sch])
                        if s_ is not None:
                            late[k].append((act - (base + (s_ - _T0))).total_seconds() / 60)
    out = {}
    for sid, t0, t1 in windows:
        if not all(((t0 - timedelta(weeks=4)).year, (t0 - timedelta(weeks=4)).month) in have_months and (t.year, t.month) in have_months for t in (t0, t1 - timedelta(hours=1))):
            out[sid] = None
            continue
        first = date(*min(have_months), 1)
        now, base = _with_baseline(trips, t0, t1, first)
        med = {k: sorted(v)[len(v) // 2] for k, v in late.items() if len(v) >= 20}  # quiet hours with few buses are too noisy
        n = len(now)
        late_now = [round(med[t0 + k * HOUR], 1) if (t0 + k * HOUR) in med else None for k in range(n)]
        late_base = []
        for k in range(n):
            t = t0 + k * HOUR
            prev = [med[t - timedelta(weeks=w)] for w in (1, 2, 3, 4) if (t - timedelta(weeks=w)) in med]
            late_base.append(round(sorted(prev)[len(prev) // 2], 1) if prev else None)
        out[sid] = {'trips': {'now': now, 'base': base}, 'late': {'now': late_now, 'base': late_base}}
    return out
