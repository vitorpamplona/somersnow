# Transit over time

How many people ride the bus and the T in Somerville, every fall the MBTA has published since 2016. A PTAC page, from the MBTA's counts; **not an MBTA or City page**.

**Open it at [somerwalks.org/transit-trends.html](https://somerwalks.org/transit-trends.html)**, or open [`output/trends.html`](output/trends.html) in a browser.

## What it shows

- **Headline numbers:** weekday boardings in the latest fall for buses and the T together, buses alone and the T alone, each as a share of Fall 2019.
- **A decade of boardings:** stacked columns, each fall: buses at stops in Somerville, then the Red, Green and Orange Line stations. Marked: the pandemic (2020), the Green Line Extension (2022), the bus network redesign (from Dec 2024).
- **How far back to 2019?** Each fall as a share of Fall 2019: Somerville's buses, the T stations, and every MBTA bus for comparison; weekday, Saturday or Sunday (buses only on weekends).
- **The stations:** weekday boardings at each station, every fall with a count.
- **Every route:** a small chart per route of its weekday riders at Somerville stops, Fall 2019 vs the latest fall.
- **Where riders went:** every bus stop in Somerville, sized by riders and colored by the change between any two falls you pick; stops that are new or gone are rings.
- **When people ride the bus:** weekday riders by the hour their trip started, Fall 2019 vs the latest fall, as counts or as a share of the day.
- **All the numbers** in a table.

What it found, Fall 2019 → Fall 2025: buses in Somerville 15,124 → 9,429 a weekday (62%), every MBTA bus 80%; the T stations 34,202 → 23,845 (70%); together 49,326 → 33,274 (67%). Somerville's buses were flat from 2016 to 2019 and have been roughly flat again since 2022; Assembly is the only station above 2019.

## How it's counted

- **Buses:** the MBTA's average boardings per scheduled trip and stop, each fall season, added up for every weekday trip at stops inside Somerville. Each stop is placed with the archived schedule of that fall (only `stops.txt` is read, with HTTP range requests) and matched to the city's outline from MassGIS. Fall 2025 on, the MBTA reports Monday–Thursday ("Wkdy") and Friday separately; they're combined 4 to 1 into a Monday–Friday average.
- **The T:** average weekday boardings at Davis, Assembly, the five Green Line Extension stations in the city (Union Square, East Somerville, Gilman, Magoun and Ball Squares), and two stations just outside it that many in Somerville use: Porter (Cambridge) and Sullivan Square (Charlestown). Lechmere is left out: it's farther from the city line, next to industrial land rather than homes, and few in Somerville use it as their station.
- **Routes:** riders getting on at Somerville stops, by route; routes under 50 riders a weekday in every fall are left out. Route `747` is shown as CT2 and `194` as 89/93, as on the other bus pages.

## Limits

- **No T counts for Fall 2016 or Fall 2020–2022.** The MBTA hasn't published them; those years show buses only, and the T's line has gaps.
- **Boardings, not people.** A rider who takes a bus to Davis or Sullivan and gets on the T there is counted at both.
- **Porter and Sullivan are shared** with Cambridge, Charlestown, Everett and Malden riders.
- **The Green Line Extension stations** have no fare gates; their counts come from samples and jump around from year to year.
- **Averages from a sample** of trips with automatic passenger counters, not every rider.
- **Stops change:** a stop that moved or got a new number shows on the map as one stop gone and one new.
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
- Town outlines: [MassGIS municipalities](https://www.mass.gov/info-details/massgis-data-municipalities).
