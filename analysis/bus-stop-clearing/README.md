# Which bus stops first?

PTAC analysis of the order in which the City's bobcat crews could clear bus stops after a storm. Not a City plan.

**See it live at [vitorpamplona.com/somersnow/bus-stops.html](https://vitorpamplona.com/somersnow/bus-stops.html)**, or open [`output/map.html`](output/map.html) in a browser, for the illustrated version: a map you can play hour by hour, the two plans side by side, and the reasoning.

## The idea in four lines

1. **Riders are bunched.** Half of the weekday boardings at the stops the City clears happen at 15 of its 189 stops. The 3 busiest (Davis, Clarendon Hill Busway, Holland St @ Dover St) see more riders than the 151 quietest stops together.
2. **Moving a bobcat costs time.** Putting it on a trailer and moving it takes about 30 minutes, so crews clear stretches of street, driving from stop to stop, as they do today.
3. **Busiest stretch first.** When a crew finishes a stretch, it takes the stretch that clears the most riders' stops per minute, counting the drive or the 30-minute trailer move to get there.
4. **Then sweep the rest.** Once stops with 60% of riders are taken, each crew clears the nearest stretch left, whole, so it stops crossing town.

## Result

Same crews, same work, different order (hours of work from when crews start on bus stops; see `output/summary.md` for every number):

| | Route by route (today, as modeled) | Ridership first |
| --- | --- | --- |
| Average wait for a rider's stop | 8.2 h | 5.0 h |
| Riders' stops clear after 4 h | 15% | 63% |
| All stops clear | 22.5 h | 21.4 h |
| Trailer moves | 27 | 22 |

The answer holds when any one assumption changes (2 or 6 crews, 10 or 30 minutes a stop, 15 or 45 minutes to trailer, a shorter or longer drive limit, a slower bobcat): ridership first always cuts the average wait by about a third or more and finishes the same time or sooner. The table is in `output/summary.md` and on the page.

## How the model works

- **Stops:** the MBTA bus stops in Somerville with their average weekday boardings (Fall 2025). The 18 stops on route 109 are left out: the MBTA clears all of them itself.
- **Stretches:** each route's stops in the order the bus passes them, cut wherever the next stop is too far to drive (more than 800 m by street, taken as 1.3 × the straight line). Both sides of the street are separate stretches, as the bus runs.
- **Moving:** a bobcat drives to a stop within 800 m at about 5 mph; anything farther, or the first stop of the day, costs a 30-minute trailer move.
- **Clearing:** 20 minutes a stop (boarding area, shelter, bench).
- **Route by route:** a stand-in for today's practice, since the City's 4 routes aren't published: whole bus routes, stop by stop in the order the bus runs, in route-number order, split among 4 crews so each has about the same number of stops.
- **Ridership first:** the two rules above (busiest stretch per minute, then sweep after 60%). The 60% switch point was chosen because it beats route by route on every measure; switching later clears riders a little sooner but adds trailer moves.

Every assumption is at the top of `build.py` (`A = {...}`); change one and rebuild.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | The model. Python standard library only. Run `python3 analysis/bus-stop-clearing/build.py` from the repo root. |
| `map_template.html` | The page; `build.py` fills in the data. |
| `data/bus-stops.json` | Copy of `docs/data/bus-stops.json`: MBTA stops in Somerville, weekday boardings, routes and route shapes (from `scripts/fetch_data.py`). |
| `data/wards.json` | Copy of `docs/data/wards.json`: ward outlines for the map. |
| `output/plan.csv` | Every stop in the order each plan clears it: crew, how the bobcat got there (drive or trailer), minutes moving, hour clear. A list DPW could start from. |
| `output/summary.md` | The headline numbers and the what-if table. |
| `output/map.html` | The illustrated explainer (self-contained; open it in any browser). |
| `../../docs/bus-stops.html` | The same page on the public site, copied by `build.py`. Don't edit it by hand. |

`build.py` copies the two data files from `docs/data/` each time it runs, so `npm run data` followed by this script uses the latest ridership.

## Limits

- **Not the City's list.** The City says it clears 281 stops; the MBTA lists 207 in Somerville (189 without route 109). We can only rank stops we can see.
- **Assumed times.** Crews, minutes a stop, bobcat speed and the 30-minute trailer move are estimates. The what-if table shows the ranking doesn't depend on them, but the hours do.
- **Straight lines, not streets.** Distances are straight lines times 1.3, not routed on the street grid; one-way streets and turns are ignored.
- **Boardings only.** Ridership counts people getting on. A stop where many people get off (near a hospital or a school) ranks lower than its real use; the City could move such stops up a tier by hand.
- **No storm timing.** Hours are hours of work, not clock time; overnight pauses, shift changes and street plowing aren't modeled.

## What would make it better

From the City: its list of 281 stops and 4 routes; how many bobcats and crews clear bus stops; how long a stop takes; where the crews start. From the MBTA: which stops on routes 77 and 104 it clears.

Sources: weekday boardings by stop ([MBTA open data](https://mbta-massdot.opendata.arcgis.com/)); stops and routes ([MBTA V3 API](https://api-v3.mbta.com/)); route 109 cleared by the MBTA ([MBTA: bus service during winter storms](https://www.mbta.com/winter-weather/bus-service-during-winter-storms)); 281 stops in "4 Routes" ([City snow page](https://www.somervillema.gov/snow)); ward outlines (City GIS, `ym5n-phxd`).
