# Which bus stops first?

PTAC analysis of the order in which the City's bobcat crews could clear bus stops after a storm. Not a City plan.

**See it live at [vitorpamplona.com/somersnow/bus-stops.html](https://vitorpamplona.com/somersnow/bus-stops.html)**, or open [`output/map.html`](output/map.html) in a browser, for the illustrated version: a map you can play hour by hour, the two plans side by side, each crew's day on a map, and the reasoning.

## The goal

The most riders at a clear stop, as fast as possible. We measure it as the **average wait for a rider's stop**: the hour each stop is clear, counted once for every weekday boarding there. Lower is better.

## The idea

1. **Riders are bunched.** Half of the weekday boardings at the stops the City clears happen at 15 of its 189 stops. The 3 busiest (Davis, Clarendon Hill Busway, Holland St @ Dover St) see more riders than the 151 quietest stops together.
2. **Follow the street.** The bobcats drive along the bus routes, stop to stop, and cross the street to the stop on the other side. A crew never drives past a waiting stop: it clears it. It may drive through stops that are already clear.
3. **Finish the corner.** After reaching a stop, a crew clears every waiting stop within 100 m of it (across the street, the same intersection) before driving on, so it never leaves a small stop behind at a hub.
4. **Busiest run first.** Crews start at busy stops at least 1.2 km apart. At each stop, a crew heads where the next few waiting stops along the street (up to 8) clear the most riders per minute of driving and clearing.
5. **Then the nearest.** Once stops with 70% of riders are clear, each crew takes the nearest waiting stop along the street, so no one drives across town for the last few.

## Result

Same 4 crews, same stops, same streets, different order (hours of work from when the crews start at their first stops; every number is in `output/summary.md`):

| | Route by route (today, as modeled) | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.0 h | 4.7 h |
| Riders' stops clear after 2 h | 7% | 45% |
| Riders' stops clear after 4 h | 42% | 58% |
| All stops clear | 21.4 h | 18.6 h |
| Distance driven | 102 km | 81 km |

Riders first gets riders their stop sooner, finishes sooner and drives less. It holds when any one assumption changes (2 or 6 crews, 10 or 30 minutes a stop, a bobcat at 3 or 8 mph): the average wait drops by about a third or more, and every stop is clear sooner, every time. `output/summary.md` also has the same comparison for 1 to 10 crews.

## How the model works

- **Stops:** the MBTA bus stops in Somerville with their average weekday boardings (Fall 2025). The 18 stops on route 109 are left out: the MBTA clears all of them itself. They stay on the street network, so crews can drive past them.
- **Streets:** each stop is linked to the next stop along every bus route that serves it, at the route's own length, and to any stop within 60 m (across the street). Stops more than 900 m apart on a route aren't linked: a gap that long means stops in between were matched to the route's other direction, and the link would let a crew skip them. Where the bus routes leave pieces unconnected, the closest stops are linked (4 links). Crews drive the shortest way along these links.
- **On the map:** each link is drawn along the bus route's own shape between the two stops, so trails follow the street and share it where routes do (links across the street and the 4 joining links are straight).
- **Driving:** about 5 mph. **Clearing:** 20 minutes a stop (boarding area, shelter, bench).
- **Start:** each crew begins at its first stop at hour 0. Getting the bobcats there from the yard isn't counted; it is the same for both plans.
- **Route by route:** a stand-in for today's practice, since the City's 4 routes aren't published: whole bus routes, stop by stop in the order the bus runs, in route-number order, split among 4 crews so each has about the same number of stops.
- **Riders first:** the rules above. The 100 m corner, the 1.2 km spacing, the 8-stop lookahead and the 70% switch were picked by trying a few values; they give sensible starting points (Davis, Clarendon Hill Busway, Broadway @ Marshall St, McGrath Hwy) and beat route by route on every measure.

Every assumption is at the top of `build.py` (`A = {...}`); change one and rebuild. A build takes about a second, and the same inputs always give the same plan.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | The model. Python standard library only. Run `python3 analysis/bus-stop-clearing/build.py` from the repo root. |
| `map_template.html` | The page; `build.py` fills in the data. |
| `data/bus-stops.json` | Copy of `docs/data/bus-stops.json`: MBTA stops in Somerville, weekday boardings, routes and route shapes (from `scripts/fetch_data.py`). |
| `data/wards.json` | Copy of `docs/data/wards.json`: ward outlines for the map. |
| `output/plan.csv` | Every stop in each crew's order for both plans: meters and minutes driven to reach it, the stops it drives through on the way, and the hour it is clear. A list DPW could start from. |
| `output/summary.md` | The headline numbers and the what-if table. |
| `output/map.html` | The illustrated explainer (self-contained; open it in any browser). |
| `../../docs/bus-stops.html` | The same page on the public site, copied by `build.py`. Don't edit it by hand. |

`build.py` copies the two data files from `docs/data/` each time it runs, so `npm run data` followed by this script uses the latest ridership.

## Limits

- **Not the City's list.** The City says it clears 281 stops; the MBTA lists 207 in Somerville (189 without route 109). We can only rank stops we can see.
- **Assumed times.** Crews, minutes a stop and bobcat speed are estimates. The what-if table shows the ranking doesn't depend on them, but the hours do.
- **Bus routes, not every street.** Crews drive only along bus routes (plus 4 short links where routes don't meet). Side streets, one-way streets and turns aren't modeled.
- **Boardings only.** Ridership counts people getting on. A stop where many people get off (near a hospital or a school) ranks lower than its real use; the City could move such stops up by hand.
- **No storm timing.** Hours are hours of work, not clock time; overnight pauses, shift changes and street plowing aren't modeled.
- **Not the best possible order.** The plan comes from simple rules, not a proven optimum; small changes to the settings move the hours a little.

## What would make it better

From the City: its list of 281 stops and 4 routes; how many bobcats and crews clear bus stops; how long a stop takes; how far a bobcat can drive between stops and where the crews start. From the MBTA: which stops on routes 77 and 104 it clears.

Sources: weekday boardings by stop ([MBTA open data](https://mbta-massdot.opendata.arcgis.com/)); stops and routes ([MBTA V3 API](https://api-v3.mbta.com/)); route 109 cleared by the MBTA ([MBTA: bus service during winter storms](https://www.mbta.com/winter-weather/bus-service-during-winter-storms)); 281 stops in "4 Routes" ([City snow page](https://www.somervillema.gov/snow)); ward outlines (City GIS, `ym5n-phxd`).
