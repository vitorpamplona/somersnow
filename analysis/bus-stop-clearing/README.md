# Which bus stops first?

PTAC analysis of the order in which the City's bobcat crews could clear bus stops after a storm. Not a City plan.

**See it live at [vitorpamplona.com/somersnow/bus-stops.html](https://vitorpamplona.com/somersnow/bus-stops.html)**, or open [`output/map.html`](output/map.html) in a browser, for the illustrated version: a map you can play hour by hour, the two plans side by side, each crew's day on a map, and the reasoning.

## The goal

The most riders at a clear stop, as fast as possible. We measure it as the **average wait for a rider's stop**: the hour each stop is clear, counted once for every person who gets on or off there on a weekday. Lower is better. People getting off count as much as people getting on: someone stepping off the bus needs a clear stop too, and riders often get off across the street from where they got on.

## The idea

1. **Riders are bunched.** Half of the weekday riders (getting on or off) at the stops the City clears use 20 of its 189 stops. The 3 busiest (Davis, Clarendon Hill Busway, Holland St @ Dover St) see more riders than the 129 quietest stops together.
2. **Follow the street.** The bobcats drive along the bus routes, stop to stop. A crew never drives past a waiting stop of its own: it clears it. It may drive past stops that are already clear, or that are another crew's.
3. **One street at a time, both sides.** A crew keeps going along one side of a street, the way the bus goes, while the next stop ahead waits. At the end of its part of the street it crosses and clears the other side on the way back. Only then does it move on to another street. To get somewhere, a crew may also drive back along a street.
4. **One crew per stretch of street.** Each street is cut into stretches of up to 10 stops, in order along it, both sides. The first crew to clear a stop on a stretch owns it: no other crew clears its stops, so two crews never work the same street at the same place. A long street like Broadway can go to two crews, in two whole pieces.
5. **Busiest run first, then the nearest.** Crews start at busy stops at least 1.2 km apart. When a run is done, a crew heads where the next few waiting stops of its own along the street (up to 8) clear the most riders per minute of driving and clearing, leaving other crews the stops just ahead of them. Once stops with 70% of riders are clear, each crew takes the nearest.
6. **No jumping around.** A jump is a drive of more than 800 m to the next stop, past stops already clear: a crew moving to a different place, which is slow, costly and annoying. Rules 1–5 plan the day one stop at a time and can't see that leaving a pocket behind forces a jump hours later. So the model then looks at the whole day: it tries moving each stretch, and each piece of a crew's day between two jumps, into every crew's day next to the stops closest to it (by driving and as the crow flies), either way round. It keeps a change when the score goes down: the average wait in minutes, plus 60 for every jump, plus 120 for every km of jumps or of driving along another crew's streets, plus 180 every time a crew leaves a street before its own stops there are clear, plus 2 for every minute until the last stop is clear (so no crew is left with a much longer day). Work is only ever inserted where a crew moves from one street to another, never in the middle of a street. It repeats until no move helps.

Every build checks the plan and stops with an error if two crews share a stretch of street or a crew comes back to a street after another crew's piece of it. `output/summary.md` lists the checks: jumps, driving back over the same link, driving along another crew's streets, and leaving a street unfinished.

## Result

Same 4 crews, same stops, same streets, different order (hours of work from when the crews start at their first stops; every number is in `output/summary.md`):

| | Route by route (today, as modeled) | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.7 h | 6.0 h |
| Riders' stops clear after 2 h | 7% | 33% |
| Riders' stops clear after 4 h | 17% | 44% |
| All stops clear | 20.5 h | 19.2 h |
| Distance driven | 84 km | 50 km |
| Jumps (drives over 800 m to the next stop) | 18 | 5 |
| Pairs of stops on one stretch cleared by different crews | 83 | 0 |
| Driving along another crew's streets | 15 km | 0.2 km |
| Leaving a street with own stops on it still waiting | 14 | 3 |

Riders first gets riders their stop sooner, drives less, keeps each crew to its own streets and finishes one street, both sides, before the next. Its 5 jumps are 0.8 to 2.2 km; one ends a crew's day at the two Boston Ave stops on the Medford line (reached through Medford, drawn dotted), another takes a crew to the Assembly Row loop. The 3 streets left and come back to are where two streets cross (Prospect St and Webster Ave at Union Sq; Medford St and Pearl St). With any one assumption changed (2 or 6 crews, 10 or 30 minutes a stop, a bobcat at 3 or 8 mph), the average wait is always lower, by 20% (30 minutes a stop) to 38%; the last stop is clear sooner except with 30 minutes a stop (42 minutes later). `output/summary.md` also has the same comparison for 1 to 10 crews.

## How the model works

- **Stops:** the MBTA bus stops in Somerville with their average weekday riders (Fall 2025): people getting on plus people getting off. The 18 stops on route 109 are left out: the MBTA clears all of them itself. They stay on the street network, so crews can drive past them.
- **Streets, one side at a time:** for clearing, each direction of a bus route is its own one-way leg. A stop belongs to the leg it stands on the right of (buses stop on the right), and to every leg that passes it, since branches share streets; a stop on the left of every leg of a route is served by buses running the other way on a pattern the route data doesn't carry, so it goes on that street driven the other way. Each stop links to the next one on its leg, in the bus's direction, at the route's own length. Stops more than 900 m apart on a leg aren't linked: a gap that long means stops are missing in between, and the link would let a crew skip them.
- **Turning around:** a crew reaches the stop across the street (within 60 m) by crossing the road, which costs 1 minute (these are small roads). Where a leg leaves the city, the crew turns like the bus does, to the nearest stop of the same route's other direction. Where pieces still can't reach each other, the closest stops are linked both ways, preferring a stop on the same route (3 pairs: Assembly Row, Mystic Ave and Boston Ave at the Medford line). Crews take the quickest way along these links, and may drive back along a leg (against the bus) to get somewhere.
- **On the map:** each link is drawn along the bus route's own shape between the two stops, so trails follow the street and share it where routes do. Both sides of a street follow the same line. Turnarounds and joining links are straight.
- **Driving:** about 5 mph. **Clearing:** 20 minutes a stop (boarding area, shelter, bench).
- **Start:** each crew begins at its first stop at hour 0. Getting the bobcats there from the yard isn't counted; it is the same for both plans.
- **Route by route:** a stand-in for today's practice, since the City's 4 routes aren't published: whole bus routes, stop by stop in the order the bus runs, in route-number order, split among 4 crews so each has about the same number of stops.
- **Riders first:** the rules above. The 10-stop stretches, the 800 m jump, the weights in the score, the 1.2 km spacing, the 8-stop lookahead (also how far ahead another crew's run is left to it) and the 70% switch were picked by trying a few values; they give sensible starting points and beat route by route on every measure.

Every assumption is at the top of `build.py` (`A = {...}`); change one and rebuild. A build takes about two minutes (16 what-if plans, side by side), and the same inputs always give the same plan.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | The model. Python standard library only. Run `python3 analysis/bus-stop-clearing/build.py` from the repo root. |
| `map_template.html` | The page; `build.py` fills in the data. |
| `data/bus-stops.json` | Copy of `docs/data/bus-stops.json`: MBTA stops in Somerville, weekday boardings and alightings, routes and route shapes (from `scripts/fetch_data.py`). |
| `data/wards.json` | Copy of `docs/data/wards.json`: ward outlines for the map. |
| `output/plan.csv` | Every stop in each crew's order for both plans: meters and minutes driven to reach it, the stops it drives through on the way, and the hour it is clear. A list DPW could start from. |
| `output/summary.md` | The headline numbers and the what-if table. |
| `output/map.html` | The illustrated explainer (self-contained; open it in any browser). |
| `../../docs/bus-stops.html` | The same page on the public site, copied by `build.py`. Don't edit it by hand. |

`build.py` copies the two data files from `docs/data/` each time it runs, so `npm run data` followed by this script uses the latest ridership.

## Limits

- **Not the City's list.** The City says it clears 281 stops; the MBTA lists 207 in Somerville (189 without route 109). We can only rank stops we can see.
- **Assumed times.** Crews, minutes a stop and bobcat speed are estimates. The what-if table shows riders get their stop sooner whichever one changes, but the hours, and how much sooner, do depend on them.
- **Bus routes, not every street.** Crews drive only along bus routes (plus 3 joining links where routes don't meet). Side streets aren't modeled, so a crew sometimes drives back along a street it already cleared to get somewhere else; with side streets it could often take a shorter way. A crossing takes the same minute everywhere, even on McGrath Hwy.
- **Averages, not storm days.** Riders are a normal fall weekday's. Who rides after a storm, and when, isn't known.
- **No storm timing.** Hours are hours of work, not clock time; overnight pauses, shift changes and street plowing aren't modeled.
- **Not the best possible order.** The plan comes from simple rules and a search that keeps the first change that helps, not a proven optimum; small changes to the settings move the hours, and sometimes which crew gets a stretch.

## What would make it better

From the City: its list of 281 stops and 4 routes; how many bobcats and crews clear bus stops; how long a stop takes; how far a bobcat can drive between stops and where the crews start. From the MBTA: which stops on routes 77 and 104 it clears.

Sources: weekday boardings and alightings by stop ([MBTA open data](https://mbta-massdot.opendata.arcgis.com/)); stops and routes ([MBTA V3 API](https://api-v3.mbta.com/)); route 109 cleared by the MBTA ([MBTA: bus service during winter storms](https://www.mbta.com/winter-weather/bus-service-during-winter-storms)); 281 stops in "4 Routes" ([City snow page](https://www.somervillema.gov/snow)); ward outlines (City GIS, `ym5n-phxd`).
