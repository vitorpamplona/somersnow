# Transit over time (`analysis/transit-trends/`)

Agent guide. Start with the root [`AGENTS.md`](../../AGENTS.md). What the page shows, how it's counted, its limits and sources are in [`README.md`](README.md); keep it current when the page changes.

`docs/transit-trends.html` (somerwalks.org/transit-trends.html, a tile on the home page): weekday boardings at Somerville's bus stops and the T stations its people use, every fall since 2016. Analysis from the MBTA's counts, labeled as such.

## Build

`npm run trends` (Python standard library). It writes `output/trends.html` from `trends_template.html` (the data replaces `/*DATA*/null`) and copies it to `docs/transit-trends.html`: never edit the copy. Cached in `../../.cache/`: `mbta-bus-ridership.zip` (shared with `analysis/bus-trips`), `gtfs-stops-<feed date>.json` (each fall's stop locations, read from the archived feed with HTTP range requests, no full download), `trends-towns.geojson`, `trends-rail-<season>.json`, the Bluebikes monthly zips (about 400 MB for Sep–Nov 2016–2025) and `trends-bikes-<year>.json`. Also `trends-acs-<year>.json` and `trends-lodes-<year>.json` (a year not published yet isn't cached, so the next build asks again; a year the Bureau never published for Somerville is cached as empty). Delete a cache file to refresh it. The build prints each season's totals; check them against the previous run.

**A new season** (the MBTA adds a fall each year): the bus file picks it up by itself. For the T, add the new rail file's ArcGIS item to `RAIL_ITEMS` (kind `csv` for a downloadable CSV, `service` for a feature service with `parent_station`, `old` for the 2017–19 service keyed by `stop_name`).

## Choices to keep

- **Which stations:** the seven inside Somerville plus Porter and Sullivan Square (`STATIONS`). Lechmere is left out on purpose (farther from the city line, next to industrial land, few in Somerville use it). Change the list only with a reason on the page.
- **Somerville stops** are matched to the city outline per season, with that season's stop locations, never today's list (stops and routes change: the 86 left Somerville in Dec 2024, the 109 came in).
- **Weekday** is Monday–Friday: from Fall 2025 the file splits `Wkdy` (Mon–Thu) and `Fri`; `bus()` combines them 4 to 1.
- **Routes** are named as on the other bus pages (`747` → CT2, `194` → 89/93); routes under `MIN_ROUTE` (50) riders in every season are dropped.
- **Bluebikes** (`bluebikes()`): trips by start station, each station placed at its dock (a classic-bike trip's start position; from 2024 e-bike trips carry GPS positions), Sep–Nov, federal holidays out (`holidays()`). The file names change over time (`hubway`, `bluebikes`, `.csv.zip`): they're found from the bucket listing.
- **Who's working** (`acs()`, `lodes()`): the survey's 1-year tables for Somerville city (the table service answers 204 or 400 for a year it doesn't have: left out, shown as "no survey"), and LODES summed over Somerville's census tracts. Keep the note about hybrid work next to the transit-commuter line: the survey's "usual mode" can't show fewer days a week.
- **Missing T years** (2016, 2020–22) are shown as "no data", never zero.

## Charts and colors

Colors were checked with the dataviz palette validator on the navy surface (`#10243A`): the stacked columns go bus `#4F98DE`, Red `#DA291C`, Green `#1B9B6A`, Orange `#D57200` (red and orange never touch); the index chart uses bus blue, the T `#C08A14`, Bluebikes `#2FA37A` and every MBTA bus as a gray reference `#8A9BB0`; "Who's working" uses worked from home `#C8609C`, transit amber and drove alone gray, then residents working blue, residents' jobs teal and jobs in Somerville amber; the map is diverging orange `#E36F28` (fewer riders) to blue `#4F98DE` (more) through gray. Every chart has a legend, selective direct labels, a hover tooltip, an `aria-label`, and its numbers in the table. Axis scales (`ticks()`) always reach past the largest value. Map station labels are placed biggest first where they overlap nothing (short names on phones).
