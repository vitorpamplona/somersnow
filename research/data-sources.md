# Data for snow visualizations

What public data exists for charts and maps about snow work in Somerville, what it shows, and how to get it. Every source below was opened and queried on **Oct 31, 2026**; the numbers are from those queries. None of this is on the site yet.

**Read first:** 311 reports count *complaints*, not unshoveled sidewalks. They depend on who reports and how easy reporting is. Say "reports", never "unshoveled sidewalks", and don't compare years without the caveat in §1.

---

## Strongest sources (ready to use, no key, browser-friendly)

### 1. Somerville 311 requests (City open data)

- **Dataset:** [311 Service, Information, and Feedback Requests](https://data.somervillema.gov/d/4pyi-uqq6) (`4pyi-uqq6`), updated daily, July 2015 to now. Socrata API, no key: `https://data.somervillema.gov/resource/4pyi-uqq6.json`
- **Fields that matter:** `type`, `category` (`Snow`), `date_created`, `most_recent_status`, `most_recent_status_date`, `ward`, `block_code` (2010/2020 Census block). No street address or coordinates.
- **Snow-related types (all years):** Snow/sidewalk not shoveled 9,465 · Snow removal request 4,721 · Snow emergency inquiry 3,484 · Snow emergency parking inquiry 2,437 · Salting request 1,713 · Plowing request 1,513 · Snow related feedback 1,142 · Space saver report 769 · Sand barrel 500 · Bike facility snow maintenance 144.
- **Query used:** `$where=category='Snow' or upper(type) like '%SNOW%' or type in ('Salting request','Plowing request')&$limit=100000` (25,970 rows).

**What it shows**

"Snow/sidewalk not shoveled" reports per winter, next to Boston's snowfall (§2):

| Winter | Snow (in) | Reports | Reports per inch |
|---|---|---|---|
| 2015/16 | 36.1 | 219 | 6 |
| 2016/17 | 47.6 | 571 | 12 |
| 2017/18 | 59.9 | 755 | 13 |
| 2018/19 | 27.4 | 399 | 15 |
| 2019/20 | 15.8 | 479 | 30 |
| 2020/21 | 38.6 | 325 | 8 |
| 2021/22 | 54.0 | 757 | 14 |
| 2022/23 | 12.4 | 301 | 24 |
| 2023/24 | 9.8 | 458 | 47 |
| 2024/25 | 28.1 | 2,019 | 72 |
| 2025/26 | 62.8 | 3,182 | 51 |

- **The complaint wave.** Summed over the 16 days since 2015 with 6"+ of snow, reports by day after the snow: day 0: 88, day 1: 629, **day 2: 1,012, day 3: 1,041**, day 4: 751, day 5: 394. Reports peak two to three days after a big storm, well past the 6-daylight-hour deadline. Jan 25–26, 2026 (16.7" + 6.5"): 273 reports on Jan 28. Feb 23, 2026 (17.1"): 269 on Feb 26.
- **Wards, 2025/26:** Ward 1: 1,010 · 2: 839 · 3: 373 · 4: 184 · 5: 354 · 6: 280 · 7: 142. Wards are drawn to similar populations, so raw counts are roughly comparable, but they still reflect who reports.
- **Time to close:** every report is "Closed"; median 22.5 hours from report to closed (quartiles 12 h / 71 h). "Closed" means the City handled the request, not necessarily that the sidewalk was cleared.
- **When people report:** mostly 8 a.m.–5 p.m. on weekdays. A third come by app, a third by phone and a third by web.

**Caveats**

- Reports per inch jumped from 6–15 (2015–2022) to 51–72 (2024–2026). That more likely reflects easier reporting, publicity or enforcement than worse shoveling. Ask the City (→ `questions.md`) before drawing a trend.
- "Plowing request" only exists from 2022/23 on; "Snow removal request" was used more before that.
- To map below ward level, join `block_code` to Census block shapes ([TIGERweb](https://tigerweb.geo.census.gov/), no key).

### 2. Boston snowfall since 1891 (NOAA, via ACIS)

- **API:** `POST https://data.rcc-acis.org/StnData`, no key. Station `BOSthr` (the "Boston Area" threaded record).
  - Daily: `{"sid":"BOSthr","sdate":"2025-11-01","edate":"2026-04-30","elems":[{"name":"snow"},{"name":"snwd"}]}`
  - Monthly: `{"sid":"BOSthr","sdate":"1891-07","edate":"2026-06","elems":[{"name":"snow","interval":"mly","duration":"mly","reduce":"sum"}]}`
- **What it shows:** 135 complete winters, 1891/92–2025/26. Median 1991–2020: 42.9". Last winter (2025/26): 62.8". The biggest days were Feb 23, 2026 (17.1") and Jan 25, 2026 (16.7"). The record in this series is 2014/15 at 110.6".
- **Caveat:** this is Boston (Logan), not Somerville, so call it "Boston snowfall".

### 3. MBTA bus stops and riders

- **Stops:** [MBTA V3 API](https://api-v3.mbta.com/stops?filter[route_type]=3&page[limit]=10000), no key for light use, browser-friendly. Filter `municipality == "Somerville"`: **207 bus stops**, 197 marked wheelchair-accessible. (The City says it clears 281 stops; its count differs from MBTA's.)
- **Riders:** [MBTA Bus Ridership by Trip, Season, Route/Line and Stop](https://mbta-massdot.opendata.arcgis.com/datasets/8daf4a33925a4df59183f860826d29ee), a 73 MB zip of CSVs, Fall 2016–Fall 2025. Sum `Boardings` over `Day Type = Wkdy` per `GTFS stop_id`.
- **What it shows (Fall 2025, average weekday):** about **9,400 boardings at Somerville stops**. **Half of them happen at 19 stops**, and a quarter at just 3: Davis busway 1,574, Clarendon Hill busway 497, Somerville Ave @ Union Sq 362. Next: Holland St @ Dover St 232, Somerville Ave @ Union Sq (other direction) 203, Broadway @ Marshall St 199, Elm St @ Chester St 194, Washington St @ Caldwell Ave 175. Most of the top 19 are on Broadway, Washington St and Somerville Ave.
- **Caveat:** column names differ in older files (Fall 2019 and earlier), so trends need per-year parsing.

### 4. Sidewalk widths (MassDOT Road Inventory)

- **Service:** [Road Inventory 2025](https://gis.massdot.state.ma.us/arcgis/rest/services/Roads/RoadInventoryYearEndFiles/FeatureServer/11), ArcGIS REST, no key. Somerville = `City=274` (2,297 segments). Fields: `Lt_Sidewlk`, `Rt_Sidewlk` (sidewalk width in feet), `Curb`, `Jurisdictn`, `St_Name`, `Length` (miles).
- Also: [Pedestrian Facilities](https://gis.massdot.state.ma.us/arcgis/rest/services/Roads/PedestrianFacilities/FeatureServer/0), sidewalk lines with width and **condition** (`Left_Cond`, `Right_Cond`); 2,502 features around Somerville.
- **What it shows:** 136 road miles. Of 272 "side-miles" (each side of each road), about 198 have a sidewalk. Most common width: 7 ft (90 side-miles). Widths of 5–6 ft: 53 side-miles. **4 ft or narrower: about 10 side-miles**, where a 36" path plus a snow bank barely fits.
- **Caveats:** widths are coarse (whole feet, from aerial photos). Highways (I-93, McGrath) count as "no sidewalk". Decode `Jurisdictn` against the MassDOT data dictionary before showing state vs. City streets. This could help answer the open question on state-road sidewalks.

### 5. The City's snow page

- [somervillema.gov/snow](https://www.somervillema.gov/snow) lists the City's **clearing priority order**: 1. streets, 2. municipal and school lots and access routes, 3. public bus stops (281, in 4 routes), ramps and bridges, 4. City squares and traffic islands, 5. sidewalks next to municipal property and schools, 6. sidewalks and crosswalks next to bus stops, 7. sidewalks next to private property. That makes a clear "who gets cleared when" graphic: private sidewalks come last, which is why they're on you.
- **The Broadway & School St program** ([page](https://www.somervillema.gov/departments/programs/sidewalk-snow-clearing-pilot)), since 2021: more enforcement, more City clearing of stops and ramps, and City clearing of late sidewalks along the full length of both streets. Its 2021 overview memo is a scanned PDF (no text).

## Live feeds (for a "storm mode")

- **National Weather Service:** `https://api.weather.gov/points/42.3876,-71.0995` → grid **BOX 70,102**. The gridpoint data (`/gridpoints/BOX/70,102`) has hourly `snowfallAmount` and `probabilityOfPrecipitation`. Free, CORS-enabled, needs a `User-Agent`. Use it to show "Snow tonight" and an estimated deadline, labeled as a forecast.
- **MBTA alerts:** `https://api-v3.mbta.com/alerts?filter[route_type]=3` gives live bus delays, detours and stop closures (e.g. `STOP_CLOSURE`). Filter to Somerville stops.

## Weaker or blocked

- **Crashes** ([Police Data: Crashes](https://data.somervillema.gov/d/mtik-28va), 2018–now): 155 crashes on snow, ice or slush out of about 3,550. Only 8 involved pedestrians, too few to chart honestly.
- **ADA Community Survey 2023** ([`usj9-kz3f`](https://data.somervillema.gov/d/usj9-kz3f)): has a `sidewalks` 0–10 column among ADA "areas of focus", but no codebook. Ask the Racial and Social Justice Department what the number means.
- **Census ACS** (car-free households, residents 65+, disability, by tract): the Census API now needs a free key. Alternative: [MAPC DataCommon](https://datacommon.mapc.org/) downloads. This would show where sidewalks matter most.
- **City base maps** on the portal: Wards (`ym5n-phxd`), Streets (`7jtq-qmnf`), FY2025 Tax Parcels (`gw4w-w7cw`, could count corner lots), Neighborhoods (`n5md-vqta`).

## Looked for, not found

A curb-ramp inventory (City or MassDOT); a list of declared snow emergencies; the 22 blue-light intersections; plow GPS history; sidewalk-snow tickets issued; snow and ice spending (likely only in budget PDFs). Worth asking the City (→ `questions.md`).

## Visualization ideas, strongest first

1. **The complaint wave.** One storm as a snowflake bar, then the bars of reports climbing on days 2–3. "The rule is 6 daylight hours. Complaints peak on day 3." (§1, §2)
2. **19 stops.** A Somerville map with stop dots sized by weekday riders. "Half of Somerville's bus riders board at 19 stops. Clear yours." (§3)
3. **Who gets cleared when.** The City's 7-step priority order as an animated ladder, with private sidewalks last. (§5)
4. **135 winters.** A strip of Boston snowfall since 1891, with last winter and the 42.9" normal marked. "Big or small, every winter needs shovels." (§2)
5. **Where 36 inches is tight.** A sidewalk-width map highlighting stretches of 4 ft or less. (§4)
6. **Reports by ward.** Seven small bars per winter, with the "reports, not conditions" caveat. (§1)

## Collected

`npm run data` (`scripts/fetch_data.py`, Python standard library, no keys) collects sources 1–3 and 5, the ward outlines and the hourly Logan weather into small files in `docs/data/`. The storm replay (`docs/storm.html`) reads them. Re-run it each fall before the first storm.

Hourly weather comes from the [Iowa Environmental Mesonet ASOS archive](https://mesonet.agron.iastate.edu/request/download.phtml?network=MA_ASOS) (Logan, `BOS`; free, CORS-enabled). Its present-weather codes (`-SN`, `SN`, `+SN`) give when snow started and stopped, which the daily NOAA totals can't.

**What the February 22–24, 2026 replay shows** (City notices + 311 + Logan):
- The City declared the emergency on Saturday, effective Sunday at noon (odd side by 4 p.m.).
- At Logan, snow fell from about 8 p.m. Sunday to about 10 p.m. Monday. It was heaviest from 6 a.m. to noon Monday, with visibility a quarter mile and winds over 30 knots.
- Snow stopped after dark, so the 6 daylight hours started at sunrise: the guide's calculator says **12:28 p.m. Tuesday**. The City's notice said "the shoveling deadline was 1 p.m."
- What people asked 311 changed by phase: parking and emergency questions at the declaration; plow and street requests while it snowed and on Tuesday morning; sidewalk reports after the deadline, peaking Wednesday midday; space-saver reports by Thursday. Only 38 of 841 sidewalk reports between the first snow and March 1 (about 1 in 20) came before the deadline.
- In 12 of 15 big storms since 2016, sidewalk reports peaked 1 to 3 days after the last day of snow.
