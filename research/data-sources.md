# Data for snow visualizations

> Short version for agents: the coverage table and data rules are in `AGENTS.md` ("Storm replays and data"). This file has the details, numbers and queries, in the order they were found.

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
- **Bus routes on the ward map** — [MBTA V3 API](https://api-v3.mbta.com/route_patterns?filter[route]=87&include=representative_trip.shape) `route_patterns` with `include=representative_trip.shape`: for each route that serves a Somerville stop, the typical patterns (`typicality` 1, both directions) and their shapes (Google encoded polylines), clipped to a box around the city and simplified; the page clips them to the ward outlines. These are **today's** routes. Routes 194 and 747 have stops in the ridership file but no route patterns in the API, so they have no line. "194" is the ridership file's id for the schedule's route `8993` ("89/93", Clarendon Hill – Haymarket via Sullivan, one supplemental early trip a day: 4:30 a.m. weekdays, 4:33 Sat, 5:16 Sun in both files).
- **Routes change over time.** In the bus arrival/departure data, routes with a timing stop inside Somerville were 80, 85, 86, 87, 88, 89, 90, 91, 94, 96, 101, CT2 (plus 194 in late 2020) in Dec 2020 and Jan 2022, and the same without the 86 (with the 109) in Feb 2026. So a storm's bus lane counts the routes that served Somerville then: today's routes that ran that month, plus any route with a timing stop in Somerville that month (the data lists only timing stops, so the second rule alone misses the 83 and 95). The same routes are used for the storm and its normal weeks. The map says which routes of the time are no longer running there. The CT2 is route 747 in the API and ridership files.
- **MBTA archive times ending in "Z" are local time, not UTC.** In the Rapid Transit Travel Times files (2025 on), `from_stop_departure_datetime` equals the service date plus `from_stop_departure_sec`, i.e. Boston wall-clock time. In the alerts archive, `created_dt` peaks at 7–8 a.m. with almost nothing 1–3 a.m., and active periods start at 04:30 (the start of the service day). Both are read as local. (Before this fix the 2026 subway lane and every storm's alerts were shifted 4–5 hours early.) NWS times from IEM are real UTC.
- **Smaller storms count (Nov 2026).** Under the first rule (a 6-inch day at Logan) there was no storm from March 2022 to January 2026: no day reached 6 inches in winters 2022–23 (12.4 in all winter), 2023–24 (9.8) or 2024–25 (28.1; biggest day 5.2 in on Dec 20, 2024), nor in 2019–20 (15.8). Residents say small storms leave the worst ice, so the replays now cover every storm with 3 inches or more in total (consecutive days of half an inch or more): about 42 since 2016 instead of 15. The index groups them by winter.
- **Bus speed (stand-in for traffic).** No public data counts cars on Somerville streets: the City's only counts are a one-hour fall bike/ped count (`qu9x-4xq5`), and MassDOT's Traffic Count Data System (hourly counters on state roads) returned 403 here. From the MBTA bus arrival/departure data already collected: on each trip, the time between consecutive timing stops that are both inside Somerville, divided by that stretch's median at the same hour (weekdays and weekends apart) over the 4 weeks before; the hourly median gives "% slower". Trip ids are blank on about 50 rows a month (ignored).
- **Card spending.** [Opportunity Insights Economic Tracker](https://github.com/OpportunityInsights/EconomicTracker), `Affinity - County - Daily.csv`, Middlesex County (FIPS 25017), `spend_all`: card spending vs. January 2020, seasonally adjusted, 7-day average. Daily through mid-2022, weekly after (too coarse for a storm), ending June 2024. Each storm day is shown as its change from the average of the 4 weeks before. Jan 29, 2022 blizzard: about −4% to −5% for several days. County-wide and smoothed; not City revenue. The City publishes no daily revenue: "Parking Meters" (`jich-f4v9`) is meter locations from 2017, citations are moving violations only, parking permits stop in 2020.
- **Fire Department calls (NFIRS).** The City publishes no fire or EMS data (only station locations). FEMA/USFA's National Fire Incident Reporting System public release has every Somerville Fire Department incident (FDID 17274), 2019–2025, about 14,000–17,000 a year, with alarm time, type found on arrival and street, on ArcGIS as "U.S. Fire Department Responses (NFIRS, <year>)" (`services.arcgis.com/XG15cJAlne2vxtgt/.../NFIRS_PDR_Light_Service_<year>`; 2021 is `NFIRS_PDR_Light_2021`). Full releases 2014–2025 are on OpenFEMA. NFIRS was replaced by NERIS in January 2026, so 2026 storms aren't covered. No incidents at all on Feb 25–28 and Dec 10–15, 2022 (gaps in the release). Compared with the same days of the 4 weeks before (2019–2025, small samples): wires down/arcing +82% on snow days (21 storms; +188% in storms of 6 inches or more); vehicle crashes −36% during big storms and +76% in the 3 days after; carbon monoxide calls +27% on snow days; medical calls +3% to +12% during, +14% in the 3 days after the small snows found through 311 (the release doesn't say why, so not a count of falls). Water leaks follow cold, not snow (76 on Feb 4–5, 2023, the record cold). The police dispatch log (`mdb2-mgc7`) misses most medical calls; there, fire alarms were +46% in the 4 days after big storms and "injured person" calls +18% on melt-and-refreeze days.
- **Snow periods, not fixed weeks (Nov 2026).** The first replays showed 2 days before to 7 days after the last snow. Measured instead: the day sidewalk reports die down (the first of two days in a row at no more than 1/20 of the peak day, or 2 reports). The median snowfall takes 7 days; 21 of 54 took longer, 4 more than 2 weeks, and in 10 cases more snow fell first. So snowfalls are merged into snow periods: any snow of half an inch or more that starts before reports died down joins the period, and the replay runs until they die down (cap 35 days). 54 snowfalls make 44 periods; the longest: Feb 2025 (Feb 2, 6, 9, 16: reports for 23 days), Jan 25 – Feb 10, 2026 (20 days), Jan 26 – Feb 9, 2021 (17 days).
- **Freezing rain and sleet (Nov 2026).** The Logan reports we already read for snow also code freezing rain (FZRA), freezing drizzle (FZDZ) and ice pellets / sleet (PL). 20 of the 44 snow periods have some; the most hours: Jan 26 – Feb 9, 2021 (18), Jan 29 – Feb 4, 2022 (13), Jan 20, 2019 and Dec 29, 2015 (12 each). Most of the small snows that drew heavy sidewalk complaints had freezing rain or sleet (Dec 2015, Dec 2017, Jan 2019, Dec 2019, Feb 2022), which fits what residents say: small storms leave the worst ice.
- **Snow on the ground (Nov 2026).** Logan has reported no snow depth on any winter day since 2015 (ACIS `snwd` all missing), and the CoCoRaHS stations inside Somerville report depth only a few days a winter. Medford 1.2 W (just over the city line) reports 48–107 winter days a year and Winchester 0.7 SE 97–121, so the replays use Medford, else Winchester, measured around 7 a.m., and name the station. Dec 11, 2022 (0.9 in) was gone by the next morning, yet drew enough sidewalk reports to count.
- **Smaller snows found through 311.** 311 shows problem periods the snowfall rule misses: after a small snow (often under 2 inches at Logan), sidewalk reports jumped. Rule: outside every snow storm's window (2 days before to 7 after), sidewalk reports over 3 days reach 3% of that winter's sidewalk reports and at least 30, after a day with half an inch or more at Logan (in the 4 days before or during the burst). A share of the winter, not a fixed count, because sidewalk reports per winter went from about 220–760 through 2023–24 to 2,019 (2024–25) and 3,182 (2025–26). It finds 12: Dec 29, 2015; Dec 25, 2017; Jan 20, 2019; Feb 12, 2019; Dec 17, 2019; Feb 4, 2022; Dec 11, 2022; Feb 23, 2023; Jan 11, 2025; Feb 2, 2025; Dec 14, 2025; Mar 3, 2026. Dec 14, 2025 (1.3 in) drew 90 sidewalk reports the next day; Mar 3, 2026 (1.0 in) drew 104. Only sidewalk reports are used: snow-emergency questions follow City announcements, not weather (Feb 12, 2024: 91 questions, no snow at Logan). They look like any other storm on the site (no label, by choice), but are left out of the "peak 1 to 3 days after" count, since they were chosen by their reports.
- **Caveat:** this is Boston (Logan), not Somerville, so call it "Boston snowfall".

### 3. MBTA bus stops and riders

- **Stops:** [MBTA V3 API](https://api-v3.mbta.com/stops?filter[route_type]=3&page[limit]=10000), no key for light use, browser-friendly. Filter `municipality == "Somerville"`: **207 bus stops**, 197 marked wheelchair-accessible. (The City says it clears 281 stops; its count differs from MBTA's.)
- **Riders:** [MBTA Bus Ridership by Trip, Season, Route/Line and Stop](https://mbta-massdot.opendata.arcgis.com/datasets/8daf4a33925a4df59183f860826d29ee), a 73 MB zip of CSVs, Fall 2016–Fall 2025. Sum `Boardings` over `Day Type = Wkdy` per `GTFS stop_id`. Day types in Fall 2025: `Wkdy`, `Fri`, `Sat`, `Sun`. Each row is one scheduled trip (`trip start time`, `Route/Variant`) at one stop (`stop sequence`), with average boardings, alightings and load; no stop-to-stop table, so `analysis/bus-trips/` estimates one. Stop id `2169` ("Bennett Alley", first stop of Harvard trips on the 71, 73, 74, 75, 77, 78, 96 and 109) is in no schedule feed (2022, 2024, 2025 checked).
- **Schedules of past seasons:** the [MBTA's GTFS feed archive](https://cdn.mbta.com/archive/archived_feeds.txt) lists every feed with its season (`feed_version` starts with e.g. "Fall 2025"); about 16 MB each. Use it to draw routes and stops as they ran when riders were counted: today's API has no stops for the CT2 (747). The schedule's routes include branches marked typicality 2 (the 87 and 89 to Clarendon Hill); drawing typicality 1 only leaves Broadway west of Davis without the 89.
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

`npm run data` (`scripts/fetch_data.py`, Python standard library, no keys) collects sources 1–3 and 5, the ward outlines and the hourly Logan weather into small files in `docs/data/`, including an hour-by-hour file for each storm of 3 inches or more since 2016 (the 15 with a 6-inch day at first). The storm replays (`docs/storms/<id>.html`, written by `scripts/build_pages.py`) embed them.

City snow emergency times come from the City's news posts. Its online archive reaches back only to about May 2022; it has both notices for Feb 22–24, 2026, only the declaration for Jan 25–27, 2026, and only the end notice for Feb 25, 2022 (which gives the City's own deadline, 12:30 p.m. Feb 26; the guide's calculator says 12:24 p.m.). Earlier storms replay without parking messages (question 48). Re-run it each fall before the first storm.

Hourly weather comes from the [Iowa Environmental Mesonet ASOS archive](https://mesonet.agron.iastate.edu/request/download.phtml?network=MA_ASOS) (Logan, `BOS`; free, CORS-enabled). Its present-weather codes (`-SN`, `SN`, `+SN`) give when snow started and stopped, which the daily NOAA totals can't.

**What the February 22–24, 2026 replay shows** (City notices + 311 + Logan):
- The City declared the emergency on Saturday, effective Sunday at noon (odd side by 4 p.m.).
- At Logan, snow fell from about 8 p.m. Sunday to about 10 p.m. Monday. It was heaviest from 6 a.m. to noon Monday, with visibility a quarter mile and winds over 30 knots.
- Snow stopped after dark, so the 6 daylight hours started at sunrise: the guide's calculator says **12:28 p.m. Tuesday**. The City's notice said "the shoveling deadline was 1 p.m."
- What people asked 311 changed by phase: parking and emergency questions at the declaration; plow and street requests while it snowed and on Tuesday morning; sidewalk reports after the deadline, peaking Wednesday midday; space-saver reports by Thursday. Only 38 of 841 sidewalk reports between the first snow and March 1 (about 1 in 20) came before the deadline.
- In 12 of 15 big storms since 2016, sidewalk reports peaked 1 to 3 days after the last day of snow.

## More sources to correlate with a storm (checked Nov 1, 2026, on the Feb 22–24, 2026 storm)

| Source | Access | What it showed for this storm | Time detail |
|---|---|---|---|
| **NWS warnings** for Somerville's zone MAZ014 | [IEM VTEC API](https://mesonet.agron.iastate.edu/json/vtec_events_byugc.php?ugc=MAZ014&sdate=2026-02-15&edate=2026-02-28), no key | Blizzard Warning from 4 p.m. Sun to 7:32 p.m. Mon (after a Winter Storm Watch) | minutes |
| **Police dispatch (CAD)** `mdb2-mgc7` | City open data | 102 `SNOEMTOW` (snow emergency tow) calls Feb 22–25: 53 Sun 4 p.m.–midnight, right after the 4 p.m. move deadline, then 42 overnight. Also `DISABLED MV`, crashes. Tows per year since 2017 (2026: 156). | police shift (8 h) and ward |
| **Crashes** `mtik-28va` | City open data | 13 crashes Feb 22–28, 8 on snow-covered roads, none involving pedestrians | minutes |
| **Other 311 types** `4pyi-uqq6` | City open data | Illegal parking (148), towed/booted car questions (25), trash schedule (106) spike with the emergency | minutes |
| **MBTA gated station entries** | [ArcGIS feature service](https://services1.arcgis.com/ceiitspzDAHrdGO1/arcgis/rest/services/GSE/FeatureServer/0) | Somerville stations: about 7,300 entries on a normal Monday (Feb 9), **812 on Mon Feb 23 (−89%)**, about −40% on Tuesday, normal by Wednesday. Mostly Davis and Assembly: Green Line Extension stations record very few gated entries. | 30 min |
| **MBTA service alerts 2026** | [CSV, monthly](https://mbta-massdot.opendata.arcgis.com/datasets/d233f1820cf54139bd18e75e30dd2c6c) | Sunday-level subway and bus service announced for Monday; 45 alerts on Somerville routes and stations Feb 22–25: delays up to 30+ min (85, 87, 88, 89, 109), route 90 snow detour, Union Sq detour, elevator outages at Gilman, Union and Ball Square | minutes |
| **Bluebikes trips** | [monthly zip](https://s3.amazonaws.com/hubway-data/index.html), no key | Trips starting at the 41 stations inside Somerville: about 340–400 on a normal weekday, **0 on Mon Feb 23**, 77 on Tuesday, normal by Thursday | minutes |
| **MBTA bus arrival/departure 2026** | [CSV, 318 MB](https://mbta-massdot.opendata.arcgis.com/datasets/9d8a8cad277545c984c1b25ed10b7d3c) | Not processed yet: would give on-time performance per Somerville route during the storm | minutes |
| **Boston 311** (2026) | [data.boston.gov](https://data.boston.gov/dataset/311-service-requests), SQL API | 2,484 "Unshoveled Sidewalk" and 3,223 plowing requests Feb 22–Mar 1. A neighbor to compare the complaint wave with. | minutes |
| NWS spotter reports (PNS) | [IEM AFOS](https://mesonet.agron.iastate.edu/cgi-bin/afos/retrieve.py?pil=PNSBOX) | No Somerville report; nearest partial: Arlington 11.8" by 2:09 p.m. Mon | — |
| Cambridge snow and ice code cases `6qf3-rbkf` | Cambridge open data | Has violation types (ramp blocked, icy, path under 4 ft, no crosswalk access); Dec 2019 – Mar 2026 (2,240 cases; checked Nov 5, 2026) | — |

## In the replays (Nov 1, 2026)

All the sources in the table above except Boston 311, the NWS spotter reports and Cambridge's data are now collected for every storm by `scripts/storm_extras.py` and shown in each replay's chart and "Getting around" panel (bus arrival times were added the same day; see below). Coverage: NWS warnings and 311 for every storm; police dispatch from 2017; crashes from March 2018; MBTA alerts from 2020; T entries (yearly archive, 30-minute counts) and Bluebikes for every storm. "Normal" for the T and Bluebikes is the same hour on the 4 weeks before the storm window (holidays in those weeks lower it; e.g. Feb 23, 2026 shows −86% against that average, −89% against Feb 9 alone). Bluebikes had no trips from Somerville stations in the winters of 2016 and 2017 (both during the storms and the weeks before), so those replays say so.

### Added Nov 1, 2026

- **Snow in Somerville** — [CoCoRaHS](https://www.cocorahs.org/) volunteer observers inside Somerville (stations "SOMERVILLE 0.5 SSE", "0.5 W", "0.7 SSE", "0.8 SSE", "1.0 S"; 1998 to now), via ACIS `StnMeta`/`StnData`, no key. Daily snowfall for the 24 hours to about 7 a.m., averaged over the stations reporting. Coverage is uneven: some storms have every day reported (Jan 25–27, 2026: 19.0 in vs. 23.2 at Logan; Dec 16–17, 2020: 13.5 in), some only some days (shown as "partial report"), and in the 2022 storms and Feb 2026 the observer reported only melted precipitation, not snow.
- **City website traffic** — [Website Analytics](https://data.somervillema.gov/d/754v-8e35) (`754v-8e35`): views of the top 20 pages per day, 2020 to May 15, 2023. Snow pages (URL contains "snow") per day vs. the average of the 28 days before: e.g. Jan 7, 2022: 8,188 views vs. about 17 a normal day; Jan 29, 2022 blizzard: 6,972 and 7,306. Only covers the Dec 2020 and the three 2022 storms. Pages outside the day's top 20 aren't counted, so "normal" is a low estimate.
- **MBTA bus arrival and departure times** — yearly CSV collections on the MBTA open data portal (2020–2026, about 300 MB each, cached). For routes serving Somerville: trips that left their first stop per hour, and the median minutes late at timepoints, each vs. the same hour on the 4 weeks before. Covers the Dec 2020, 2022 and 2026 storms.

### Checked on the City portal and left out (Nov 1, 2026)

All 54 datasets on data.somervillema.gov were listed. Used: 311 (`4pyi-uqq6`), police dispatch (`mdb2-mgc7`), crashes (`mtik-28va`), website analytics (`754v-8e35`), wards (`ym5n-phxd`). Left out: traffic citations (`3mqx-eye9`: moving violations only, e.g. phone use, unlicensed driving; parking and snow-emergency tickets aren't in it), permits and licenses (`nneb-s3f7`, `vxgw-vmky`: dumpsters, curb cuts, occupancy), the Winter Warming Center survey (`e7ix-nqn6`: about the shelter), the ADA survey (`usj9-kz3f`: no codebook for `sidewalks`), crime reports and the other surveys.

**Worth adding next:** the Happiness Survey (`wmeh-zuz2`) has `year`, `ward` and, for 2019, 2023 and 2025, how people get around (`transportation_walk_yn`, `transportation_public_transit_yn`, …) plus street-crossing safety and street-maintenance satisfaction. 2025: 1,185 of 1,392 respondents walk, 988 ride transit. By ward, it would show where sidewalks matter most next to the sidewalk-report map. It's a voluntary survey (about 150–200 answers per ward), not a census.

### Added Nov 1, 2026 (later)

- **Subway speed** — [MBTA Rapid Transit Travel Times](https://mbta-massdot.opendata.arcgis.com/datasets/682fd13544ac4c518620019a1cb819b1) (yearly CSV collections, 2021 on; monthly files per heavy/light rail, each row one train between two stations). For segments in or touching Somerville, each train's time divided by that segment's median over the 4 weeks before; the hourly median gives "% slower than usual". Trains per hour vs. the same hour on the 4 weeks before flags hours with under half the usual trains.
- **Melt and refreeze** — from the hourly Logan temperatures already collected: an hour counts as refreezing when it's at or below 32°F within 12 hours after an hour at 34°F or warmer, from the first snow on. Shown with 311 "Salting request" counts (now kept separately in each storm file as `salting`).
- **Who walks, by ward** — Happiness Survey (`wmeh-zuz2`), 2025: "In the past week, which of the following transportation options did you use? Check all that apply." Shares of residents who walked and rode transit, by ward (about 180–240 answers per ward; a random sample, not a census). In 2025, Ward 1 reported the lowest walking share (68%) and Wards 2 and 6 the highest (95%).

- **Sidewalk widths (Nov 2026, for the Council letter).** MassDOT Road Inventory 2025 ([layer 11](https://gis.massdot.state.ma.us/arcgis/rest/services/Roads/RoadInventoryYearEndFiles/FeatureServer/11), `City=274`, fields `Lt_Sidewlk`, `Rt_Sidewlk`, `Length`), both sides summed: 197.7 side-miles have a recorded width, 194.5 of them (98.4%) 4 ft or more; 55.6 side-miles are recorded as 0 (no sidewalk) and 18.8 have no width (MassDOT leaves the opposite direction of undivided roads blank to avoid double counting). Widths are whole feet; the published fields don't say whether they include the tree strip or obstructions, so the clear path can be narrower. Most common: 7 ft (90 side-miles), 5 ft (28), 6 ft (25), 10 ft (21).
