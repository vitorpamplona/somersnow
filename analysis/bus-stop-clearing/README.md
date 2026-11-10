# Bus stop clearing planner

A PTAC tool for designing the routes the City's bobcat crews take to clear bus stops after a storm, and scoring them. Not a City plan.

The page starts with the plan an earlier version of `build.py` computed (riders first, one street at a time; `data/computed-plan.json`), as a base to edit or compare against; "+ Computed" adds it again when it isn't there.

**Open it at [somerwalks.org/bus-planner.html](https://somerwalks.org/bus-planner.html)**, or open [`output/map.html`](output/map.html) in a browser.

## What it does

The page is one full-window dashboard: the map, with the chart of riders whose stop is clear (one line per plan, and a marker at the hour shown) in its top corner and the hour slider along its bottom, and a sidebar with the plans, the crews and the crew's route. The map browses by default: drag to move it, scroll or use + / − to zoom (stops keep their size, so the two sides of a street come apart), tap a stop for its riders and crew (a stop in a route also opens its crew in the sidebar and picks it in the list). Right-click a stop for a menu to add it to a crew (as its last stop), move it to another crew, or take it off. Editing is on only when you press ✏️ (or E); a bar on the map says which crew you're editing, and Done (or Esc) stops. The selected crew stands out; the others dim. The **Settings ▾** menu at the top holds the settings, saving and sharing, and the sources. On a phone the parts stack.

An operator builds plans. Each plan has its own crews, and each crew a list of stops in the order it clears them:

- **Build a route.** Pick a crew, press ✏️ (or E), then press on the map and drag across stops: every stop the pointer passes is added, in order, until you let go (a stop of another crew moves to this one; a drag never takes stops off). Or tap stops one by one (tapping one of the crew's own stops takes it off), or add them by name. Hover a stop in the crew's list to ring it on the map; click it to keep the ring and the stop's popup, and glide the map to it (click again to let go). Drag stops in the list to reorder them (or use the arrow keys on a stop's ⠿ handle). Reverse a route, clear a crew, add or remove crews. Undo (Ctrl/Cmd+Z, or ↶ on the map) takes back any change, a whole drag as one step; Redo (Ctrl/Cmd+Shift+Z or Ctrl+Y, or ↷) puts it back.
- **See how it does.** Play runs the day hour by hour on the map, each crew in its own color, with the share of riders' stops clear at that hour. Every stop in the crew's list shows when it's clear and how far the crew drove to it, and flags drives past stops still waiting.
- **Compare plans.** Make as many plans as you like, with different numbers of crews: new, copy, rename, delete. The chart draws one line per plan, the open plan's thicker.
- **Change the assumptions** (Settings menu). All plans share them, so they compare on the same terms:
  - minutes to clear a stop (20);
  - bobcat speed (5 mph);
  - minutes to cross the road (1);
  - whether route 109 stops, which the MBTA clears, are included (no).
- **Save and share** (Settings menu). Plans and settings save in the browser as you go. Export them to a file and import a file to add its plans to yours. A copied link opens all the plans and settings in another browser.

## How a plan is scored

- **Stops and riders:** the MBTA bus stops in Somerville with their average weekday riders (Fall 2025): people getting on plus people getting off. Someone stepping off the bus needs a clear stop too. The 18 stops on route 109 are off by default: the MBTA clears them itself.
- **Streets:** crews drive only along the bus routes.
  - Each direction of a route is its own leg. A stop belongs to the leg it stands on the right of (buses stop on the right), and to every leg that passes it.
  - Each stop links to the next stop on its leg, at the route's own length. Stops more than 900 m apart aren't linked, because stops must be missing in between.
  - A crew may also drive back along a leg.
  - A crew can cross the street anywhere: from a stop to the stops just before and after it on the other side, measured along the street (like Somerville Ave @ Linden St to Somerville Ave @ Merriam St, 89 m). Stops within 60 m of each other are across the street too. Each crossing costs the crossing minutes. So does turning where a leg leaves the city, like the bus.
  - Stops within 300 m of each other that share no bus route (in a square, at a crossing, like Prospect St and Somerville Ave at Union Sq) get a short link both ways, counted 30% longer than the straight line for the corners. These are drawn straight.
  - The two Boston Ave stops at the Medford line, reached through Medford, are linked to College Ave @ Professors Row. That link is drawn dotted.
- **The day:** each crew starts at its first stop at hour 0 (getting there from the yard isn't counted). It works through its list in order: the quickest drive along the streets to the next stop, then the minutes to clear it. Crews don't wait for each other. Hours are hours of work, not clock time.
- **Driving past a waiting stop:** counted whenever a crew's drive goes through a stop that isn't clear yet at that moment, its own or another crew's, or one in no route. It's a sign the order could be better, not a rule the page enforces.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | Builds the street network and writes the page. Python standard library only. Run `npm run planner` (or `python3 analysis/bus-stop-clearing/build.py`) from the repo root. The page's default settings are at its top (`SETTINGS`); the network's are in `A`. |
| `map_template.html` | The page: map, route editor, plans, scoring, settings, saving. `build.py` fills in the data. |
| `data/bus-stops.json` | Copy of `docs/snow/data/bus-stops.json`: MBTA stops in Somerville, weekday boardings (`riders`) and alightings (`off`), routes and route shapes (from `scripts/fetch_data.py`). |
| `data/computed-plan.json` | The starting plan: the 4 crews' routes an earlier version of `build.py` computed (commit 3cc3f4d). |
| `data/wards.json` | Copy of `docs/snow/data/wards.json`: ward outlines for the map. |
| `output/map.html` | The page (self-contained; open it in any browser). |
| `../../docs/bus-planner.html` | The same page on the public site, copied by `build.py`. Don't edit it by hand. (Until Nov 2026 it was `bus-stops.html`, which now forwards here.) |
| `AGENTS.md` | Notes for changing the code. |

`build.py` copies the two data files from `docs/snow/data/` each time it runs, so `npm run data` followed by this script uses the latest ridership.

## Limits

- **Not the City's list.** The City says it clears 281 stops; the MBTA lists 207 in Somerville (189 without route 109). The page can only show stops the MBTA lists.
- **Bus routes, not every street.** Crews drive along bus routes, plus short straight links between nearby stops on different routes. Side streets aren't modeled, so some drives are longer than a real bobcat would take. A crossing takes the same minutes everywhere, even on McGrath Hwy.
- **Averages, not storm days.** Riders are a normal fall weekday's. Who rides after a storm, and when, isn't known.
- **No storm timing.** Overnight pauses, shift changes, breaks and street plowing aren't modeled.

## What would make it better

From the City: its list of 281 stops and its 4 routes, which could be loaded as a plan to score; how many bobcats and crews clear bus stops; how long a stop takes; where the crews start. From the MBTA: which stops on routes 77 and 104 it clears.

Sources: weekday boardings and alightings by stop ([MBTA open data](https://mbta-massdot.opendata.arcgis.com/)); stops and routes ([MBTA V3 API](https://api-v3.mbta.com/)); route 109 cleared by the MBTA ([MBTA: bus service during winter storms](https://www.mbta.com/winter-weather/bus-service-during-winter-storms)); 281 stops in "4 Routes" ([City snow page](https://www.somervillema.gov/snow)); ward outlines (City GIS, `ym5n-phxd`).
