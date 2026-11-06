# Which bus stops first?

PTAC analysis of the order in which the City's bobcat crews could clear bus stops after a storm. Not a City plan.

**See it live at [vitorpamplona.com/somersnow/bus-stops.html](https://vitorpamplona.com/somersnow/bus-stops.html)**, or open [`output/map.html`](output/map.html) in a browser, for the illustrated version: a map you can play hour by hour, the two plans side by side, each crew's day on a map, and the reasoning.

## The goal

The most riders at a clear stop, as fast as possible. We measure it as the **average wait for a rider's stop**: the hour each stop is clear, counted once for every weekday boarding there. Lower is better.

## The idea

1. **Riders are bunched.** Half of the weekday boardings at the stops the City clears happen at 15 of its 189 stops. The 3 busiest (Davis, Clarendon Hill Busway, Holland St @ Dover St) see more riders than the 151 quietest stops together.
2. **Busiest per minute next.** The bobcats drive from stop to stop. Each crew drives next to the stop that clears the most riders for the minutes it costs: the drive there plus the time to clear it.
3. **Then tidy up.** The plan tries moving each stop to another place in a crew's day, or to another crew, and flipping stretches of a crew's day, and keeps every change that lowers the average wait. That mostly cuts driving (from 22.5 to 16.0 hours across the 4 crews) and finishes earlier.

## Result

Same 4 crews, same stops, different order (hours of work from when the crews start at their first stops; every number is in `output/summary.md`):

| | Route by route (today, as modeled) | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.0 h | 3.4 h |
| Riders' stops clear after 2 h | 7% | 54% |
| Riders' stops clear after 4 h | 42% | 70% |
| All stops clear | 19.7 h | 20.1 h |
| Hours driving between stops | 11.0 h | 16.0 h |

Riders first drives more (about 129 km against 88 km in all) and finishes about 24 minutes later, in exchange for halving the average wait. The longest single drive is about 39 minutes.

The answer holds when any one assumption changes (2 or 6 crews, 10 or 30 minutes a stop, a bobcat at 3 or 8 mph, streets 60% longer than a straight line): riders first cuts the average wait by at least half every time. The finishing time moves both ways, from 2 hours later (2 crews) to 2 hours sooner (6 crews). The table is in `output/summary.md` and on the page.

## How the model works

- **Stops:** the MBTA bus stops in Somerville with their average weekday boardings (Fall 2025). The 18 stops on route 109 are left out: the MBTA clears all of them itself.
- **Driving:** a bobcat drives from one stop to the next at about 5 mph; street distance is taken as 1.3 times the straight line.
- **Clearing:** 20 minutes a stop (boarding area, shelter, bench).
- **Start:** each crew begins at its first stop at hour 0. Getting the bobcats there from the yard isn't counted; it is the same for both plans.
- **Route by route:** a stand-in for today's practice, since the City's 4 routes aren't published: whole bus routes, stop by stop in the order the bus runs, in route-number order, split among 4 crews so each has about the same number of stops.
- **Riders first:** the two steps above. The clean-up pass runs up to 8 rounds (3 in the what-if table, to keep the build quick).

Every assumption is at the top of `build.py` (`A = {...}`); change one and rebuild. A full build takes about 15 seconds.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | The model. Python standard library only. Run `python3 analysis/bus-stop-clearing/build.py` from the repo root. |
| `map_template.html` | The page; `build.py` fills in the data. |
| `data/bus-stops.json` | Copy of `docs/data/bus-stops.json`: MBTA stops in Somerville, weekday boardings, routes and route shapes (from `scripts/fetch_data.py`). |
| `data/wards.json` | Copy of `docs/data/wards.json`: ward outlines for the map. |
| `output/plan.csv` | Every stop in each crew's order for both plans: minutes driven to reach it and the hour it is clear. A list DPW could start from. |
| `output/summary.md` | The headline numbers and the what-if table. |
| `output/map.html` | The illustrated explainer (self-contained; open it in any browser). |
| `../../docs/bus-stops.html` | The same page on the public site, copied by `build.py`. Don't edit it by hand. |

`build.py` copies the two data files from `docs/data/` each time it runs, so `npm run data` followed by this script uses the latest ridership.

## Limits

- **Not the City's list.** The City says it clears 281 stops; the MBTA lists 207 in Somerville (189 without route 109). We can only rank stops we can see.
- **Assumed times.** Crews, minutes a stop and bobcat speed are estimates. The what-if table shows the ranking doesn't depend on them, but the hours do.
- **Straight lines, not streets.** Distances are straight lines times 1.3, not routed on the street grid; one-way streets and turns are ignored. Some drives in the plan are long (up to about 39 minutes); whether a bobcat can drive that far on Somerville streets is a question for the City.
- **Boardings only.** Ridership counts people getting on. A stop where many people get off (near a hospital or a school) ranks lower than its real use; the City could move such stops up by hand.
- **No storm timing.** Hours are hours of work, not clock time; overnight pauses, shift changes and street plowing aren't modeled.
- **Not the best possible order.** The plan is a good order found by a simple rule and a clean-up pass, not a proven optimum.

## What would make it better

From the City: its list of 281 stops and 4 routes; how many bobcats and crews clear bus stops; how long a stop takes; how far a bobcat can drive between stops and where the crews start. From the MBTA: which stops on routes 77 and 104 it clears.

Sources: weekday boardings by stop ([MBTA open data](https://mbta-massdot.opendata.arcgis.com/)); stops and routes ([MBTA V3 API](https://api-v3.mbta.com/)); route 109 cleared by the MBTA ([MBTA: bus service during winter storms](https://www.mbta.com/winter-weather/bus-service-during-winter-storms)); 281 stops in "4 Routes" ([City snow page](https://www.somervillema.gov/snow)); ward outlines (City GIS, `ym5n-phxd`).
