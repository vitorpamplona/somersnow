# Scripts and the storm replays (`scripts/`)

Agent guide for the storm replay pipeline and the other renderers in this folder. Start with the root [`AGENTS.md`](../AGENTS.md). For what every data file and field means, read [`docs/snow/data/README.md`](../docs/snow/data/README.md); for each source's queries and caveats, [`research/data-sources.md`](../research/data-sources.md).

## What's here

| File | Command | What it does |
|---|---|---|
| `fetch_data.py` | `npm run data` | Finds the storms, groups them into snow periods, collects hourly data for each from public sources, writes `docs/snow/data/*.json` (plus `bus-stops.json` and `wards.json`, used by the bus tools), the raw records and `sources.json`, then runs `build_pages.py`. Python standard library, no keys. Re-run each fall. |
| `storm_extras.py` | (used by `fetch_data.py`) | The extra collectors: warnings, police, crashes, 311 calls, T entries, Bluebikes, alerts, Somerville snowfall, web views, buses and bus speed, spending, snow depth, Fire Department, subway. |
| `build_pages.py` + `storm_page.html` | `npm run pages` | Writes `docs/snow/storms/<id>.html` and `storms/index.html` from the template, with the data embedded as JSON and the text (title, intro, description, prev/next, storm cards) already written; also the per-storm CSVs (`hourly_csv()`). Script and CSS URLs carry a content hash (`?v=`) so browsers never mix a new page with an old cached script. |
| `verify.mjs` | `npm run verify` | Recomputes the published numbers from `docs/snow/data` and checks them against the pages; runs in CI. `-- --cache` also re-fingerprints `.cache/` against `sources.json`. |
| `render-cards.mjs` | `npm run cards` | Card PNGs from `cards/src/` (Playwright). |
| `render-flyer.mjs` | `npm run flyer` | `docs/snow/flyer-phone.png` (needs `npm run dev`). |
| `render-lights.mjs` | `npm run lights` | The "Somerville's lights" GIF, video and poster for the cards gallery (needs `npm run dev` and ffmpeg). |
| `build_letter.py` + `print-letter.mjs` | `npm run letter` | Typesets `research/ordinance-proposals.md` as `research/ordinance-proposals.pdf` (git-ignored; needs the network for fonts). |
| `build_redirects.py` | (run once, Nov 2026) | Wrote the forwarding pages at the guide's old addresses. Skips real pages. |

The replays are analysis, not rules: the guide teaches the rules; `docs/snow/storms/` shows what actually happens in a storm, hour by hour, so PTAC can show residents and officials the pattern (sidewalk complaints peak 1 to 3 days after the snow stops, long after the deadline). Nothing there changes what the guide tells people to do.

## How the pipeline fits together

1. **Storms.** `fetch_data.py` finds every storm since July 2015 with 3 inches or more at Logan (`STORM_MIN`; consecutive days of half an inch or more; until Nov 2026 the rule was a 6-inch day, and ids didn't change), plus smaller snows found through 311 (`complaint_storms()`: outside every snow storm's window, sidewalk reports over 3 days reach 3% of that winter's total and at least 30, after a day of half an inch or more; `kind: '311'` in the data, not labeled on the site).
2. **Snow periods** (`snow_periods()`): after a period's last snowfall, sidewalk reports have died down on the first of two days in a row at no more than 1/20 of the peak day so far, or 2 reports; any snow of half an inch or more at Logan that starts before that joins the period (emergency or not). Each period's window runs from 2 days before its first snow to the day after reports died down (capped at 35 days), but never into a neighbor: it starts no earlier than the day the previous period's reports died down and ends before the next period's first snow day. Its id is its last day of snow; the other seed snowfalls' ids are `aliases` (forwarding pages). Each storm file lists its `snowfalls` (own start, stop and so deadline), `clear` (the day reports died down) and `lasted` (days from the end of the first snowfall to `clear`). Today: 54 snowfalls in 44 periods.
3. **Data.** Hourly data for each window from the sources below. Downloads over a few MB are cached in `.cache/` (a full rebuild downloads about 9 GB; delete a file there to refresh it).
4. **Pages.** `build_pages.py` writes the pages; `docs/snow/js/storm.js` + `docs/snow/css/storm.css` only draw: the guide's "storm mode" messages in a phone (a sketch of what the guide could say at each hour, not something the City said), the main chart (snow, NWS warnings, 311 by type, markers), "Getting around" lanes (drawn at real pixel width so text stays readable), counters, and the ward map. The phone sits beside the title and intro (above the slider on phones), so the charts get the full width; the panel has a fixed height (the intro's height or 80% of the hours on desktop, a typical hour on phones) and the busiest hours scroll inside it. Dragging the chart or lanes moves the time.
5. **Checkable.** `docs/snow/data/` holds the data guide, one CSV per storm (one row per hour), the records behind the counts (`raw/<id>/`, written by `write_raw()`; streets without house numbers, medical calls without a street), a fingerprint of every download (`sources.json`: address, date, size, SHA-256), and each replay's sources list links to its CSV, JSON, raw folder, the guide and the scripts.

What a replay shows: snow at Logan, NWS warnings, the City's snow emergency, the deadline (from `deadline.js`), 311 requests, a ward map, snowfall from volunteer observers inside Somerville next to Logan's, and "Getting around": T entries, MBTA bus trips run, lateness and speed on Somerville routes (2020+), card spending in the county (2020–22), how slow the subway ran (2022+), and Bluebikes vs. a normal week; melt-and-refreeze periods with salting requests. The ward map shows who walks there (Happiness Survey), the T (Red, Orange, Green D and E in MBTA colors, with stations, out to the next station beyond the city line), the bus routes of the time (one color each, side by side where they share a street, out to each route's next stop beyond the city line) and every bus stop (the busiest 19 larger), with a button per line to highlight it; views of the City's snow pages (2020 to May 2023); police snow-emergency tows, parking calls, MBTA alerts and crashes; Fire Department medical calls, wires down, carbon monoxide and crashes (2019–2025). English only. The index is grouped by winter (a winter without a storm says so).

## Sources and coverage

| Source | Where | Covers |
|---|---|---|
| Hourly weather at Logan (snow start/stop from METAR codes; falling snow only, lulls under 6 h are one storm) | Iowa Environmental Mesonet ASOS | all storms |
| Daily snowfall at Logan, winters since 1891 | NOAA via ACIS (`BOSthr`) | all |
| Snowfall inside Somerville | CoCoRaHS volunteers via ACIS | 9 storms, 4 complete ("partial report" otherwise) |
| NWS warnings for zone MAZ014 | IEM VTEC archive | all |
| 311 snow requests (sidewalk, street, emergency questions, space savers) and parking/trash calls | City open data `4pyi-uqq6` | all |
| Snow emergency tows, disabled vehicles (per 8-hour police shift) | City open data `mdb2-mgc7` | 2017 on |
| Crashes (time, street or intersection without house number, what happened, road/weather/light, injuries, pedestrian or cyclist and where they were; shown on hover/tap) | City open data `mtik-28va` | March 2018 on |
| Views of the City's snow pages | City open data `754v-8e35` (top 20 pages a day) | Dec 2020 – May 2023 |
| T gated entries at Somerville stations (30-minute) | MBTA open data, yearly archive | all |
| Bus trips run and minutes late, on the routes that served Somerville at the time | MBTA bus arrival/departure times | Dec 2020 on |
| Bus speed: each bus's time between consecutive timing stops inside Somerville vs. that stretch at the same hour (weekday/weekend) in the 4 weeks before; the stand-in for traffic (no public car counts) | same bus data | Dec 2020 on |
| Card spending, Middlesex County, 7-day average, each day vs. the 4 weeks before (county-wide spending, not City revenue; the City publishes no daily revenue) | Opportunity Insights Economic Tracker (Affinity) | daily 2020 – early 2022 |
| MBTA service alerts on Somerville routes and stations | MBTA alerts archive | 2020 on |
| Somerville Fire Department calls: medical (EMS 321 + medical assist 311) per hour vs. a normal week; ticks for wires down/arcing (440–445), carbon monoxide (424, CO detectors 736/746) and vehicle crashes (322–324), street without house number | FEMA/USFA NFIRS public release, "U.S. Fire Department Responses" on ArcGIS, FDID 17274 (`fire_dept()`; cached in `.cache/nfirs-<year>.json`) | 2019–2025 (no incidents filed Feb 25–28 and Dec 10–15, 2022: those storms show not available) |
| Bluebikes trips from stations inside Somerville | Bluebikes system data | all (no winter trips in 2016–17) |
| Subway: % slower than usual and trains run, Red/Orange/Green Line segments in Somerville (Alewife–Davis–Porter, Sullivan–Assembly–Wellington, Green Line Extension) | MBTA rapid transit travel times (about 1–1.5 GB a year, cached) | Jan 2022 on (Green Line Extension from late 2022) |
| Melt and refreeze (back at or below 32°F within 12 h after 34°F+) and salting requests | Logan hourly temperature; 311 "Salting request" | all |
| Freezing rain, freezing drizzle and sleet (ice pellets), per hour, 0–3 (`hours[i][4]`): light blue on the chart, a "Freezing rain" card in the guide panel | Logan report codes FZRA, FZDZ, PL (same IEM ASOS reports) | all (20 of 44 periods have some) |
| Snow on the ground each morning (`extra.snowDepth`, "Snow on the ground" lane) | CoCoRaHS via ACIS: Medford 1.2 W, else Winchester 0.7 SE (`snow_depth()`); Logan stopped reporting depth, Somerville's stations report it too rarely | all |
| Who walked / rode transit in the past week, by ward | Happiness Survey `wmeh-zuz2` (2025, random sample, ~200 per ward) | ward map |
| City snow emergency times and notices | somervillema.gov news, typed into `CITY` in `fetch_data.py` with source URLs (the City's online news archive only goes back to 2022) | Feb 2022 (end only), Jan 2026 (start only), Feb 2026 (both) |
| Ward outlines (State Plane, converted); MBTA stops and Fall 2025 weekday boardings; today's bus route shapes | City GIS `ym5n-phxd`; MBTA V3 API (`route_patterns` + shapes) and ridership | — |

**Checked on the City portal (data.somervillema.gov) and left out:** traffic citations (moving violations only; no parking or snow tickets), permits and licenses (dumpsters, curb cuts), the Winter Warming Center survey (about the shelter), the ADA survey (`sidewalks` column has no codebook), crime reports and the other surveys. **Not public:** sidewalk tickets issued, clean-and-lien jobs, plow GPS, a list of snow emergencies, snow spending, the 22 blue-light locations, curb-ramp inventory (questions 47–54). **Asked, not public:** hourly car counts on Somerville streets (MassDOT's count site refused automated access), daily City parking/meter revenue, parking tickets (questions 55–57).

**Ideas not built yet:** Boston 311 "Unshoveled Sidewalk" for comparison; more 311 types (fallen trees, potholes); Census ACS by ward (free key); pavement temperature from state road sensors (free token).

## Rules for this data

Counting and wording:
- "Normal" for the T, buses and Bluebikes is the same hour on the 4 weeks before the window. Holidays in those weeks distort it (Feb 2026: −86% vs. that average, −89% vs. Feb 9 alone); say "compared with a normal week", not "usual".
- 311 counts complaints, not unshoveled sidewalks. Reports per inch of snow jumped after 2023 (likely easier reporting), so don't present a trend as worse shoveling (question 47).
- When a source doesn't cover a storm, show "not available" with the reason, never a zero.
- Storms found through 311 were picked by their complaints, so they never count toward "reports peak 1 to 3 days after" (circular); the index lede counts snow-picked storms only. The 311 cutoff is a share of the winter because sidewalk reports per winter went from about 220–760 (through 2023–24) to 2,019 and 3,182.
- Fire Department medical calls say nothing about why help was needed: never call them falls. The type is what the department found on arrival.

Time:
- Socrata compares dates as text (`'2026-03-01 09:42' < '2026-03-01T00:00'` is true), so always re-check each record's time in Python against the window, as `storm_extras.py` does.
- MBTA archive times that end in "Z" (alerts `created_dt`, newer subway `..._datetime` columns) are Boston local time, not UTC; use them as wall-clock time (subway: service date + seconds). IEM/NWS times are real UTC. NFIRS alarm times are Boston wall-clock time (calls bottom out at 3–5 a.m.).
- MBTA station entries are counted by service day, which runs past midnight: periods before 3 a.m. belong to the next calendar day (`t_entries()` shifts them). Bus times carry their own date offset (`1900-01-02` = after midnight). Police "Last Half (Midnight–8 AM)" shifts are dated by calendar day (checked against the Feb 2026 emergency).
- Holidays (New Year, MLK Day, Presidents' Day, Patriots' Day, Thanksgiving, Christmas) empty the T on their own: the lanes name them on the day axis, the counters say so, and page summaries skip them and look for the biggest drop only from the first snow to 3 days after it stops. The weeks around Christmas still distort "a normal week".

Storms:
- A storm's start and stop (and so its deadline and title) span from the first to the last run of 3+ snowy hours at Logan that overlaps its snow days; a passing flurry doesn't count, as in live mode. (Before Nov 2026 it took the longest run, which ended Jan 2021 and Feb 2025 a day early.) Titles typed into `CITY` win over computed ones.
- Reports take a median of about 6 days after the snow to die down, more than 2 weeks when snow keeps falling (Feb 2025: 23 days; Jan 25 – Feb 10, 2026: 20); that's why replays are snow periods with windows that end when reports die down. The "normal week" stays the 4 weeks before the period starts, so it says less toward the end of a long period. The page-wide deadline (map text, emergency end) is the period's biggest snowfall's; each snowfall still gets its own lines and phone messages.
- Winters 2022–23 to 2024–25 had no 6-inch day at Logan; with the 3-inch rule they have storms. The index still marks any winter without a storm.
- The deadline comes from `docs/snow/js/deadline.js`. Two City notices let us check it: Feb 26, 2022 (City 12:30 p.m., calculator 12:24) and Feb 24, 2026 (City "1 p.m.", calculator 12:28).

Transit:
- **Bus routes change** (the 86 stopped in Somerville in 2020–22, not in 2026). Never apply today's route list to old data: `buses()` picks each storm's routes from that month's data (today's routes that ran, plus any route with a timing stop in Somerville), and the map names routes of the time that no longer run there. The CT2 is `747` in the API and ridership files.
- Bluebikes: a month the system hasn't published is left out of the normal week (Nov 2025 was missing), and a storm whose normal week has under 100 trips from Somerville (winters 2015–17) shows "not available", not zero.

Pages and privacy:
- Nothing on a replay may change height while dragging: the phone, the map's side text and the counters reserve their tallest version (`lockPhoneHeight`, `lockLateHeight` in `storm.js`).
- Crash locations are trimmed to the street or intersection (no house number): the City publishes exact addresses, but a single crash with an injury shouldn't point at a home.
- New City facts found in data work go through the root rules (a source, then [`research/facts.md`](../research/facts.md)); e.g. the even-side rule for 2026/27 came from a City notice.

## Add a source

1. A collector in `storm_extras.py` (`def thing(get_or_cached, windows)`), cached in `.cache/` if it's big; re-check every record's time against the window in Python.
2. Call it from `fetch_data.py`, store its result in the storm JSON, and fingerprint the download (`sources.json`).
3. Draw it in `storm.js` (a lane, a tick, a counter), with "not available" and the reason where it doesn't cover a storm.
4. Make it checkable: its hourly numbers in `hourly_csv()` (`build_pages.py`), its records in `write_raw()` (same privacy rules), its fields in `docs/snow/data/README.md`, and a check in `verify.mjs` if it's a headline number.
5. Add a row to the sources table above and its details to `research/data-sources.md`.
6. `npm run data` (or `npm run pages` if only drawing changed), `npm run verify`, then look at a few storms at phone width.
