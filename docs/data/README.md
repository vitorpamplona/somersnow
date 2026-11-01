# Storm replay data: a guide

Everything the storm replays (`docs/storms/`) show comes from public sources, through the scripts in `scripts/`. This folder holds what they produced, so anyone can check a number on a page, rebuild it from scratch, or reuse it. Made by the Somerville Pedestrian & Transit Advisory Committee (PTAC); not an official City dataset. MIT license.

Live copies: `https://vitorpamplona.com/somersnow/data/<file>`. Method notes and caveats per source: [`research/data-sources.md`](../../research/data-sources.md).

## Check it, or rebuild it

| You want to… | Do this |
|---|---|
| Look at one storm in a spreadsheet | Open `csv/<id>.csv` (one row per hour). |
| See the records behind a count | Open `raw/<id>/` (one CSV per source). |
| Check the published numbers add up | `npm run verify` (needs Node; reads only this folder and the pages, no downloads). |
| Rebuild everything from the sources | `npm run data` (Python 3 standard library, no keys; downloads about 9 GB of public archives into `.cache/`, about an hour), then compare with `sources.json`. |

Sources change after the fact (311 records get edited, archives get republished), so a rebuild months later can differ slightly. `sources.json` records what this run used.

## Files

| File | What it is |
|---|---|
| `storms.json` | The list of snow periods (one replay page each). |
| `storm-<id>.json` | Everything one replay page shows, hour by hour. Embedded in `storms/<id>.html`. |
| `csv/<id>.csv` | The hourly numbers of `storm-<id>.json` as a flat table. |
| `raw/<id>/*.csv` | Record-level extracts for that storm's window (below). |
| `sources.json` | Every download behind this folder: address, date fetched, size, SHA-256. |
| `winters.json` | Snowfall at Boston Logan per winter since 1891 and the 1991–2020 median. |
| `wards.json` | Ward outlines (lon/lat) and the Happiness Survey shares (walked / rode transit in the past week) per ward. |
| `bus-stops.json` | MBTA bus stops in Somerville with average weekday boardings, and today's bus route shapes. |

## Ids, periods and windows

A **snow period** groups snowfalls whose sidewalk reports overlap: a seed snowfall (3 inches or more at Logan over consecutive days of half an inch or more, or a smaller snow that drew many sidewalk reports) plus any snow of half an inch or more that starts before reports **die down**: the first of two days in a row with no more than 1/20 of the period's peak day, or 2 reports (`snow_periods()` in `scripts/fetch_data.py`).

- **id**: the period's last day of snow (`YYYY-MM-DD`). A snowfall merged into a longer period keeps its old address as a page that forwards (`aliases`).
- **window** (`from`, `to`): from 6 a.m. two days before the first snow to midnight after the day reports died down (35 days at most), never into a neighboring period's snow or tail. Every hourly list has one entry per hour of the window: index `i` is the hour starting at `from + i hours`.
- Times are **Boston wall-clock time** (`2026-02-23T22:00`), no time zone suffix.

## `storms.json`

`{"storms": [...]}`, one entry per period, oldest first:

| Field | Meaning |
|---|---|
| `id`, `start`, `end` | Last day of snow; first and last snow day (dates). |
| `snow` | Inches at Logan, all snowfalls in the period. |
| `kind` | `snow` (has a snowfall of 3 inches or more) or `311` (picked because sidewalk reports jumped; left out of the "peaked 1 to 3 days after" count, which would be circular). |
| `snowfalls` | `[{start, end, snow, kind}]` dates of each snowfall; `kind` is `snow`, `311` or `small` (half an inch or more, joined because reports hadn't died down). |
| `clear` | The day sidewalk reports died down. |
| `lasted` | Days from the end of the first snowfall to `clear`: the "reports for N days" on the cards. |
| `from`, `to` | First and last day of the window. |
| `aliases` | Ids of merged snowfalls that forward here. |
| `days` | `[date, inches at Logan, {311 group: count}]` per day of the window: the bars on the cards. |

## `storm-<id>.json`

| Field | Meaning |
|---|---|
| `title` | Dates of the snow (from the hourly reports), or a title typed from a City notice. |
| `from`, `to` | Window, hour precision. |
| `snowfalls` | `[{start, stop, snow}]` per snowfall, hour precision: falling snow at Logan, from the first to the last run of 3+ snowy hours (lulls under 6 hours count as one run). Each `stop` gives that snowfall's shoveling deadline: 6 daylight hours later (`docs/js/deadline.js`). |
| `snowStart`, `snowStop` | First snowfall's start, last snowfall's stop. The page-wide deadline is the biggest snowfall's. |
| `snowTotal`, `clear`, `lasted` | As in `storms.json`. |
| `emergency`, `notices`, `cityDeadline` | Only where the City's notices are online (typed in `CITY` in `fetch_data.py`, each with its source link). |
| `groups` | Order of the 311 groups in `requests`: `ask` (snow emergency questions), `street` (plowing, salting, snow removal), `sidewalk` ("snow/ice on sidewalk not shoveled"), `spacesaver`, `feedback`. |
| `hours` | Per hour: `[falling snow 0–3 (none, light, moderate, heavy), °F, visibility miles, wind knots]` at Logan. |
| `requests` | `{hour index: [count per group]}`, 311 snow requests created that hour (hours with none are left out). |
| `sidewalkByWard` | `{hour index: {ward: count}}`, sidewalk reports by ward. |
| `salting` | `[[hour index, count]]`, 311 "Salting request". |
| `extra` | The other sources, below. `null` means the source doesn't cover this storm: the page says "not available", never zero. |

`extra` (each hourly `now` list has a `base` list: the same hour in the 4 weeks before the window, averaged, which the page calls "a normal week"):

| Key | Shape | Source |
|---|---|---|
| `warnings` | `[{name, code, from, to}]` | National Weather Service, zone MAZ014 (IEM VTEC archive). |
| `police` | `{tows, disabled: [[hour index of the 8-hour shift start, count]], towsByWard}` | Somerville police dispatch (`mdb2-mgc7`), 2017 on. |
| `crashes` | `[{i, t, where, what, how, surface, weather, light, hurt, ped, bike, pedWhere, pedDoing, hitRun}]` | Somerville police crash reports (`mtik-28va`), March 2018 on; street only, no house number. |
| `calls311` | `{parking, trash: [[hour index, count]]}` | 311 parking and trash calls. |
| `tEntries` | `{now, base}` | MBTA gated entries at Somerville stations. |
| `bikes` | `{now, base}` | Bluebikes trips starting at stations inside Somerville. |
| `alerts` | `[[hour index, kind, route or station, header]]` | MBTA alerts archive, 2020 on (`kind`: delay, detour, reduced, access, other). |
| `snowSomerville` | `{days: [[date, inches, stations]], total, partial, stations}` | CoCoRaHS observers inside Somerville (via ACIS). |
| `web` | `{days: [[hour index, views]], base}` | City website analytics, snow pages (Dec 2020 – May 2023). |
| `buses` | `{trips, late: {now, base}, routes, speed: {slow, trains}}` | MBTA bus arrival/departure times, Dec 2020 on. `trips`: trips leaving their first stop; `late`: median minutes late at timing stops; `speed.slow`: % slower than the same stretch at the same hour in the 4 weeks before (`trains` there counts bus runs timed); `routes`: routes counted (those that served Somerville that month). |
| `subway` | `{slow, trains: {now, base}, segments}` | MBTA rapid transit travel times, 2022 on: % slower than usual on Somerville segments, trains run. |
| `spending` | `{base, days: [[hour index, value, % vs. 4 weeks before]]}` | Opportunity Insights, card spending, Middlesex County, 2020 – early 2022. |
| `fire` | `{ems: {now, base}, events: [[hour index, kind, label, street]]}` | FEMA/USFA fire incident reports (NFIRS), Somerville Fire Department, 2019–2025. |

## `csv/<id>.csv`

One row per hour (`hour_start`), the hourly numbers above flattened: weather, each 311 group, salting, `refreezing` (1 when it's at or below 32°F within 12 hours after 34°F or warmer, from the first snow on: the light-blue hours on the page), parking and trash calls, police tows and disabled vehicles (counted at the start of the 8-hour shift), and each `now` / `_normal` pair. Empty cell: not covered.

## `raw/<id>/`

The records behind the counts, inside the storm's window. Same privacy as the pages: streets without house numbers; medical calls without any street.

| File | Rows |
|---|---|
| `weather_logan.csv` | Every Logan weather report (METAR codes); falling snow (0–3) is read from these, so this is where snow start and stop, and so the deadline, come from. |
| `311_snow.csv` | Each 311 snow request: time created, group, type, ward. |
| `311_parking_trash.csv` | Each parking or trash call. |
| `police.csv` | Each snow-emergency tow and disabled vehicle: shift, type, ward. |
| `crashes.csv` | Each crash, as on the crash lane. |
| `fire_dept.csv` | Each Fire Department medical call (time, type), wires down / carbon monoxide / crash call (time, type, street). |
| `mbta_alerts.csv`, `nws_warnings.csv`, `snow_somerville.csv` | As in `extra`. |

The T, bus, subway, Bluebikes, spending and page-view numbers are counted from archives of millions of rows (a few GB a year), so they're published as hourly counts only; `sources.json` fingerprints the archives they came from.

## Numbers on the pages, and where they come from

| On the page | Computed from |
|---|---|
| "Reports for N days" (cards), "kept coming for N days" (intro) | `lasted` |
| "After the snow stops… N days in a typical storm", "more than a week in N of M", "more than two weeks in N" (index) | median and counts of `lasted` over `kind: snow` periods |
| "Peaked 1 to 3 days after the snow in N of M storms" (index) | single-snowfall `kind: snow` periods: the day with the most sidewalk reports in `days`, counted from `end` |
| Deadline, "Shovel by", "came after the deadline" | `docs/js/deadline.js` on each snowfall's `stop` (checked against two City notices: Feb 26, 2022 and Feb 24, 2026) |
| "N sidewalk reports to 311" (summary), the ward map | `requests` / `sidewalkByWard` from the first snowy hour on |
| "T entries −N% on <day>" (summary) | `extra.tEntries`, the day with the biggest drop vs. a normal week from the first snow to 3 days after it stops, holidays skipped |

`npm run verify` recomputes these from this folder and checks them against the pages.
