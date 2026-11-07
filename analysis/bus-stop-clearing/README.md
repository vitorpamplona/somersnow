# Bus stop routes

A PTAC tool for designing the routes the City's bobcat crews take to clear bus stops after a storm, and scoring them. Not a City plan.

**Open it at [vitorpamplona.com/somersnow/bus-stops.html](https://vitorpamplona.com/somersnow/bus-stops.html)**, or open [`output/map.html`](output/map.html) in a browser.

## What it does

An operator builds plans. Each plan has its own crews, and each crew a list of stops in the order it clears them:

- **Build a route.** Pick a crew, then tap stops on the map in order, or add them by name. Tapping one of the crew's stops takes it off; tapping another crew's stop moves it to this crew. Reorder with ↑ / ↓, reverse a route, clear a crew, add or remove crews.
- **Score it.** The page plays the day hour by hour on the map, each crew in its own color, and scores the plan:
  - the average wait for a rider's stop (stops in a route);
  - the share of riders whose stop is in a route, and whose stop is clear after 2 and 4 hours;
  - when the last stop is clear;
  - kilometers driven between stops;
  - jumps (drives longer than the jump distance);
  - times a crew drives past a stop that's still waiting.

  Each crew gets the same numbers, and every stop in the editor shows when it's clear, how far the crew drove to it, and whether that was a jump or passed waiting stops.
- **Compare plans.** Make as many plans as you like, with different numbers of crews: new, copy, rename, delete. "Compare plans" lists every plan's scores side by side, and the chart draws one line per plan.
- **Change the assumptions.** All plans share the settings, so they compare on the same terms:
  - minutes to clear a stop (20);
  - bobcat speed (5 mph);
  - minutes to cross the road (1);
  - the jump distance (800 m);
  - whether people getting off count as riders (yes);
  - whether route 109 stops, which the MBTA clears, are included (no).
- **Save and share.** Plans and settings save in the browser as you go. Export them to a file and import a file to add its plans to yours. A copied link opens all the plans and settings in another browser.

## How a plan is scored

- **Stops and riders:** the MBTA bus stops in Somerville with their average weekday riders (Fall 2025): people getting on plus, by default, people getting off. Someone stepping off the bus needs a clear stop too. The 18 stops on route 109 are off by default: the MBTA clears them itself.
- **Streets:** crews drive only along the bus routes.
  - Each direction of a route is its own leg. A stop belongs to the leg it stands on the right of (buses stop on the right), and to every leg that passes it.
  - Each stop links to the next stop on its leg, at the route's own length. Stops more than 900 m apart aren't linked, because stops must be missing in between.
  - A crew may also drive back along a leg.
  - Stops within 60 m of each other are across the street; going between them costs the crossing minutes. So does turning where a leg leaves the city, like the bus.
  - Two pieces that can't otherwise be reached are linked at their closest stops: the two Boston Ave stops at the Medford line, and the Assembly Row loop. These links are drawn dotted.
- **The day:** each crew starts at its first stop at hour 0 (getting there from the yard isn't counted). It works through its list in order: the quickest drive along the streets to the next stop, then the minutes to clear it. Crews don't wait for each other. Hours are hours of work, not clock time.
- **Driving past a waiting stop:** counted whenever a crew's drive goes through a stop that isn't clear yet at that moment, its own or another crew's, or one in no route. It's a sign the order could be better, not a rule the page enforces.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | Builds the street network and writes the page. Python standard library only. Run `python3 analysis/bus-stop-clearing/build.py` from the repo root. The page's default settings are at its top (`SETTINGS`); the network's are in `A`. |
| `map_template.html` | The page: map, route editor, plans, scoring, settings, saving. `build.py` fills in the data. |
| `data/bus-stops.json` | Copy of `docs/data/bus-stops.json`: MBTA stops in Somerville, weekday boardings (`riders`) and alightings (`off`), routes and route shapes (from `scripts/fetch_data.py`). |
| `data/wards.json` | Copy of `docs/data/wards.json`: ward outlines for the map. |
| `output/map.html` | The page (self-contained; open it in any browser). |
| `../../docs/bus-stops.html` | The same page on the public site, copied by `build.py`. Don't edit it by hand. |

`build.py` copies the two data files from `docs/data/` each time it runs, so `npm run data` followed by this script uses the latest ridership.

## Limits

- **Not the City's list.** The City says it clears 281 stops; the MBTA lists 207 in Somerville (189 without route 109). The page can only show stops the MBTA lists.
- **Bus routes, not every street.** Crews drive only along bus routes. Side streets aren't modeled, so some drives are longer than a real bobcat would take. A crossing takes the same minutes everywhere, even on McGrath Hwy.
- **Averages, not storm days.** Riders are a normal fall weekday's. Who rides after a storm, and when, isn't known.
- **No storm timing.** Overnight pauses, shift changes, breaks and street plowing aren't modeled.

## What would make it better

From the City: its list of 281 stops and its 4 routes, which could be loaded as a plan to score; how many bobcats and crews clear bus stops; how long a stop takes; where the crews start. From the MBTA: which stops on routes 77 and 104 it clears.

Sources: weekday boardings and alightings by stop ([MBTA open data](https://mbta-massdot.opendata.arcgis.com/)); stops and routes ([MBTA V3 API](https://api-v3.mbta.com/)); route 109 cleared by the MBTA ([MBTA: bus service during winter storms](https://www.mbta.com/winter-weather/bus-service-during-winter-storms)); 281 stops in "4 Routes" ([City snow page](https://www.somervillema.gov/snow)); ward outlines (City GIS, `ym5n-phxd`).
