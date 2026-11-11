# Transit over time

How many people ride the bus and the T in Somerville, and how many Bluebikes trips start or end there, every fall since 2016. A PTAC page, from the MBTA's counts; **not an MBTA or City page**.

**Open it at [somerwalks.org/transit-trends.html](https://somerwalks.org/transit-trends.html)**, or open [`output/trends.html`](output/trends.html) in a browser.

## What it shows

- **The answer first:** one sentence (weekday boardings as a share of 2019, and why), then four numbers for a weekday in the latest fall: bus and T boardings, bus boardings, T station boardings and Bluebikes trips, each as a share of Fall 2019.
- **A decade of boardings:** stacked columns, each fall: buses at stops in Somerville, then the Red, Green and Orange Line stations; for the falls with no published T boardings (2016, 2020–22), fare-gate entries at Davis, Porter, Assembly and Sullivan, hatched. Marked: the pandemic (2020), the Green Line Extension (2022), the bus network redesign (from Dec 2024).
- **Bluebikes:** trips a weekday that start or end at a dock in Somerville each fall (September to November), stacked: within the city, leaving it, arriving in it; with the number of docks.
- **How far back to 2019?** Each fall as a percentage of Fall 2019: Somerville's buses, the T stations (boardings), the four gated stations' fare-gate entries (every fall, dashed), Bluebikes, and every MBTA bus for comparison; weekday, Saturday or Sunday (buses only on weekends).
- **Why: more work from home:** Somerville residents with a job each year and how they get to work (worked from home, transit, drove alone, walked, biked; transit split into subway, bus and light rail on hover), and people with jobs: residents working (survey), jobs held by residents and jobs located in Somerville (payroll counts).
- **When people ride the bus:** weekday riders by the hour their trip started, Fall 2019 vs the latest fall, as counts or as a share of the day.
- **The stations:** weekday boardings at each station, every fall with a count.
- **Where riders went:** every bus stop in Somerville, sized by riders and colored by the change between any two falls you pick; stops that are new or gone are rings, counted under the map. A stop renumbered or moved less than 12 m is the same stop.
- **Every route:** each route's weekday riders at Somerville stops and the weekday trips it runs through the city, Fall 2019 vs the latest fall: a small chart per route with both as a share of 2019, so a gap between the lines means riders fell more than service (a ranked list with both numbers on phones; trips by route in the table).
- **How full are the buses?** Every route through Somerville, one after another, both directions: riders on board after each stop, a thin line for each weekday departure in the latest fall and the weekday average of each fall (2019 and the latest) on top, with the stretch inside Somerville shaded, a line at 36 seats, and how many departures go over it.
- **All the numbers** in a table, and how it's counted, both folded away at the end.

What it found, Fall 2019 → Fall 2025: buses in Somerville 15,181 → 9,437 a weekday (62%), every MBTA bus 80%; the T stations 34,202 → 23,818 (70%; the four gated stations' fare-gate entries 33,707 → 18,084, 54%); together 49,383 → 33,255 (67%). Bluebikes trips to, from or within Somerville went the other way: 956 → 1,547 a weekday (162%; docks 28 → 39), about a quarter of them within the city. It isn't retirement: about as many residents have jobs (55,391 → 59,103, 2019 → 2025, within the survey's margin; payroll counts 47,773 → 46,706 jobs held by residents, 2019 → 2024) and the share aged 65+ stayed about 9%. Working from home went from 4.5% to 16.6% (36.5% in 2021, then down every year). About as many residents mostly take transit to work (16,294 → 15,331, within the margin), so hybrid work (fewer days a week) likely explains much of the drop in boardings. On weekends the gap is wider: Saturday buses are back to 77%, weekend-day Bluebikes trips to 195%. Somerville's buses were flat from 2016 to 2019 and have been roughly flat again since 2022; Assembly is the only station above 2019 by the MBTA's boardings, but not by its fare-gate entries (see Limits).

## How it's counted

- **Buses:** the MBTA's average boardings per scheduled trip and stop, each fall season, added up for every weekday trip at stops inside Somerville. Each stop is placed with the archived schedule of that fall (only `stops.txt` is read, with HTTP range requests) and matched to the city's outline from MassGIS. Fall 2025 on, the MBTA reports Monday–Thursday ("Wkdy") and Friday separately; they're combined 4 to 1 into a Monday–Friday average.
- **Fare-gate entries:** the MBTA's gated station entries by station and day, averaged over the weekdays of September to November (holidays out; days with no entries at a station, such as a shutdown, left out), at Davis, Porter, Assembly and Sullivan.
- **The T:** average weekday boardings at Davis, Assembly, the five Green Line Extension stations in the city (Union Square, East Somerville, Gilman, Magoun and Ball Squares), and two stations just outside it that many in Somerville use: Porter (Cambridge) and Sullivan Square (Charlestown). Lechmere is left out: it's close to the city line (about 220 m), but the Somerville land next to it is industrial rather than homes, and few in Somerville use it as their station.
- **Bluebikes:** every trip that starts or ends at a dock inside Somerville (a trip within the city counts once; split into within, leaving and arriving), from Bluebikes' monthly trip files (Hubway until 2018), averaged over the weekdays and weekend days of September to November, without Labor Day, Columbus Day, Veterans Day (as observed), Thanksgiving and the Friday after. A dock is inside Somerville by the city's full-detail outline (the map's simplified outline put a Cambridge dock, Inman Square at Springfield St, inside in 2019–20). Each station is placed at its dock, from its classic-bike trips (starts and ends): from 2024 the files give e-bike trips the bike's GPS position, which near the city line can fall on the wrong side. E-bikes are marked only from 2024 (about 30% of trips); 2023 calls every bike "docked" and earlier files have no bike type. In Fall 2025 a few trips name a station but leave its id blank; they take the id that name has elsewhere in the files.
- **Who's working:** the American Community Survey's 1-year tables for Somerville city (B08006 means of transportation to work, B23025 employment, B01001 age), from the Census Bureau's table service (no key), and LODES payroll counts summed over Somerville's census blocks (from the LODES crosswalk). The survey asks how people usually got to work in the week before, with a margin of error; there are no 1-year tables for 2020. (B08301, the usual commute table, is blank for Somerville in 2022 and 2023; B08006 has the same counts for every year.) Two years differ only when the gap is bigger than their margins combined; the page says "about as many" otherwise. LODES counts jobs with unemployment insurance (no self-employed).
- **Trips:** for each route, the distinct weekday trips (variant, direction, start time) in the MBTA's ridership file that stop at least once in Somerville; Monday–Thursday from Fall 2025, when Friday became its own schedule.
- **Load profiles:** the MBTA's average load (riders on board leaving each stop) for each scheduled weekday departure, over the days it counted that departure in the fall (17–20 days for every Fall 2025 departure; departures counted on fewer than 3 days are left out). A departure line is one scheduled trip on a typical day, not one bus on one day. The averages are per stop over the weekday departures that serve it, all day. Each stop is placed by its distance along the route's path in the latest fall's schedule (per direction, the longest path among those run on at least 5% as many trips as the most-run one). Left out: stops more than 150 m off that path (branches, 2019 detours), stops past its ends, and stops served by fewer than 30% of the trips (school trips and short variants made one full bus look like the average). Seats: 36, the MBTA's 40-foot buses (Service Delivery Policy, Dec 2025, Table B1: 36–39 seats); the data doesn't say which bus ran a trip. The 109 has no 2019 line: it didn't run through Somerville then.
- **Routes:** riders getting on at Somerville stops, by route; routes under 50 riders a weekday in every fall are left out. Route `747` is shown as CT2 and `194` as 89/93, as on the other bus pages.

## Limits

- **No T station boardings for Fall 2016 or Fall 2020–2022.** The MBTA's boardings files skip them. Those years show its [gated station entries](https://mbta-massdot.opendata.arcgis.com/datasets/7859894afb5641ce91a2bb03599fdf5b) instead, hatched: a different count (successful taps at the gates; children, free riders and fare evasion aren't counted, per the MBTA) at the four gated stations only, so the Green Line Extension is missing from 2022's bar.
- **Boardings, not people.** A rider who takes a bus to Davis or Sullivan and gets on the T there is counted at both.
- **Bluebikes counts trips, not boardings**, and grows with the docks: 12 in 2016–17, 21 in 2018, 33–39 since 2022 (a dock is a place: ids renumbered at one dock count once; temporary winter docks are left out).
- **Porter and Sullivan are shared** with Cambridge, Charlestown, Everett and Malden riders.
- **The Green Line Extension stations** have no fare gates (riders validate at the fare machines, [MBTA](https://www.mbta.com/projects/green-line-extension-glx)); their boardings swing 30–40% from one fall to the next and run well above their alightings.
- **Boardings and gate entries drifted apart after 2019.** In 2017–19 the MBTA's boardings ran 0–5% above its fare-gate entries at Davis, Porter, Sullivan and Assembly; in 2023–25 up to 15% at Davis and Porter, up to 23% at Sullivan, and 28–57% at Assembly. By gate entries Assembly in Fall 2025 is about 75% of 2019, not 115%, so its rise is uncertain.
- **Averages from a sample** of trips with automatic passenger counters, not every rider.
- **Stops missing from a fall's schedule file** (a detour, a stop closed during the fall: 14 Somerville stops in 2019) are placed with the same stop id from the nearest other fall's file.
- **Stops change:** a stop that moved more than 12 m shows on the map as one stop gone and one new; within 12 m (often just a new number) it's one stop.
- **The hour** is when the bus trip started; the bus reaches a Somerville stop up to about half an hour later.
- **Somerville since 2015:** compare years with the city's breaks in mind (Assembly 2014, the pandemic 2020, the Green Line Extension 2022, the bus redesign from Dec 2024).

## Files

| Path | What it is |
| --- | --- |
| `build.py` | Downloads and adds up everything (cached in `../../.cache/`), writes the page. Python standard library only. `npm run trends` from the repo root. |
| `trends_template.html` | The page: the charts, the map, the table. `build.py` replaces `/*DATA*/null` with the data. |
| `output/trends.html` | The page (self-contained). |
| `../../docs/transit-trends.html` | The same page on the public site, copied by `build.py`. Don't edit it by hand. |
| `AGENTS.md` | Notes for changing the code. |

## Sources

- [MBTA Bus Ridership by Trip, Season, Route/Line and Stop](https://mbta-massdot.opendata.arcgis.com/datasets/8daf4a33925a4df59183f860826d29ee) (Fall 2016 – Fall 2025).
- MBTA rail ridership: [by season, time period and stop](https://mbta-massdot.opendata.arcgis.com/datasets/9fea7862501f4c59ab2c001ad6ae19b0) (Fall 2017–2019), [Fall 2023](https://mbta-massdot.opendata.arcgis.com/datasets/80a379ebaa374cfd836ca4d3880ceda4), [Fall 2024](https://mbta-massdot.opendata.arcgis.com/datasets/8f20b4e8d24e466fbca157cca63f6e16), [Fall 2025](https://mbta-massdot.opendata.arcgis.com/datasets/6494749a29c648018820d0e49636205c).
- Stop locations: the [MBTA schedule archive](https://cdn.mbta.com/archive/archived_feeds.txt), the last feed of each fall.
- Bluebikes: [system data](https://bluebikes.com/system-data) (monthly trip files on [S3](https://s3.amazonaws.com/hubway-data/)).
- Seats: [MBTA Service Delivery Policy, December 2025](https://www.mbta.com/policies/service-delivery-policy).
- Who's working: [American Community Survey](https://data.census.gov/table/ACSDT1Y2024.B08006?g=160XX00US2562535) 1-year tables; [LEHD LODES](https://lehd.ces.census.gov/data/).
- Town outlines: [MassGIS municipalities](https://www.mass.gov/info-details/massgis-data-municipalities).
