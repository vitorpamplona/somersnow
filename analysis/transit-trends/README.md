# Transit over time

How many people ride the bus and the T in Somerville, and how many Bluebikes trips start there, every fall since 2016. A PTAC page, from the MBTA's counts; **not an MBTA or City page**.

**Open it at [somerwalks.org/transit-trends.html](https://somerwalks.org/transit-trends.html)**, or open [`output/trends.html`](output/trends.html) in a browser.

## What it shows

- **The answer first:** one sentence (weekday boardings as a share of 2019, and why), then four numbers for a weekday in the latest fall: bus and T boardings, bus boardings, T station boardings and Bluebikes trips, each as a share of Fall 2019.
- **A decade of boardings:** stacked columns, each fall: buses at stops in Somerville, then the Red, Green and Orange Line stations; a fall with no T count has an outlined "T not counted" mark. Marked: the pandemic (2020), the Green Line Extension (2022), the bus network redesign (from Dec 2024).
- **How far back to 2019?** Each fall as a share of Fall 2019: Somerville's buses, the T stations, and every MBTA bus for comparison; weekday, Saturday or Sunday (buses only on weekends).
- **Why: more work from home:** Somerville residents with a job each year and how they get to work (worked from home, transit, drove alone; walked and biked on hover), and people with jobs: residents working (survey), jobs held by residents and jobs located in Somerville (payroll counts).
- **The stations:** weekday boardings at each station, every fall with a count.
- **Where riders went:** every bus stop in Somerville, sized by riders and colored by the change between any two falls you pick; stops that are new or gone are rings, counted under the map. A stop renumbered or moved less than 12 m is the same stop.
- **Every route:** each route's weekday riders at Somerville stops, Fall 2019 vs the latest fall (a small chart per route; a ranked list on phones).
- **When people ride the bus:** weekday riders by the hour their trip started, Fall 2019 vs the latest fall, as counts or as a share of the day.
- **Bluebikes:** trips a weekday from docks in Somerville each fall (September to November), with the number of docks.
- **All the numbers** in a table, and how it's counted, both folded away at the end.

What it found, Fall 2019 → Fall 2025: buses in Somerville 15,124 → 9,429 a weekday (62%), every MBTA bus 80%; the T stations 34,202 → 23,845 (70%); together 49,326 → 33,274 (67%). Bluebikes trips from Somerville docks went the other way: 662 → 963 a weekday (145%; docks 29 → 39). It isn't retirement: residents with a job went up (54,403 → 58,726, 2019 → 2025) and the share aged 65+ stayed about 9%; working from home went from 4.5% to 16.6%. Residents who mostly take transit to work fell only about 6%, so hybrid work (fewer days a week) likely explains much of the drop in boardings. On weekends the gap is wider: Saturday buses are back to 77%, weekend-day Bluebikes trips to 177%. Somerville's buses were flat from 2016 to 2019 and have been roughly flat again since 2022; Assembly is the only station above 2019.

## How it's counted

- **Buses:** the MBTA's average boardings per scheduled trip and stop, each fall season, added up for every weekday trip at stops inside Somerville. Each stop is placed with the archived schedule of that fall (only `stops.txt` is read, with HTTP range requests) and matched to the city's outline from MassGIS. Fall 2025 on, the MBTA reports Monday–Thursday ("Wkdy") and Friday separately; they're combined 4 to 1 into a Monday–Friday average.
- **The T:** average weekday boardings at Davis, Assembly, the five Green Line Extension stations in the city (Union Square, East Somerville, Gilman, Magoun and Ball Squares), and two stations just outside it that many in Somerville use: Porter (Cambridge) and Sullivan Square (Charlestown). Lechmere is left out: it's farther from the city line, next to industrial land rather than homes, and few in Somerville use it as their station.
- **Bluebikes:** every trip that starts at a dock inside Somerville, from Bluebikes' monthly trip files (Hubway until 2018), averaged over the weekdays and weekend days of September to November, without Labor Day, Columbus Day, Veterans Day, Thanksgiving and the Friday after. Each station is placed at its dock, from its classic-bike trips: from 2024 the files give e-bike trips the bike's GPS position, which near the city line can fall on the wrong side. E-bikes are marked only from 2024 (about 30% of trips); earlier files call every bike "docked".
- **Who's working:** the American Community Survey's 1-year tables for Somerville city (B08301 means of transportation to work, B23025 employment, B01001 age), from the Census Bureau's table service (no key), and LODES payroll counts summed over Somerville's census tracts (25017-350100 to 351599). The survey asks how people usually got to work in the week before, with a margin of error; there are no 1-year tables for 2020, and Somerville isn't in them for 2022 or 2023. LODES counts jobs with unemployment insurance (no self-employed).
- **Routes:** riders getting on at Somerville stops, by route; routes under 50 riders a weekday in every fall are left out. Route `747` is shown as CT2 and `194` as 89/93, as on the other bus pages.

## Limits

- **No T counts for Fall 2016 or Fall 2020–2022.** The MBTA hasn't published them; those years show buses only, and the T's line has gaps.
- **Boardings, not people.** A rider who takes a bus to Davis or Sullivan and gets on the T there is counted at both.
- **Bluebikes counts trips, not boardings**, and grows with the docks: 12 in 2016–17, 24 in 2018, 36–39 since 2022.
- **Porter and Sullivan are shared** with Cambridge, Charlestown, Everett and Malden riders.
- **The Green Line Extension stations** have no fare gates; their counts come from samples and jump around from year to year.
- **Averages from a sample** of trips with automatic passenger counters, not every rider.
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
- Who's working: [American Community Survey](https://data.census.gov/table/ACSDT1Y2024.B08301?g=160XX00US2562535) 1-year tables; [LEHD LODES](https://lehd.ces.census.gov/data/).
- Town outlines: [MassGIS municipalities](https://www.mass.gov/info-details/massgis-data-municipalities).
