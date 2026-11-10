# Bus stop clearing planner (`analysis/bus-stop-clearing/`)

Agent guide. Start with the root [`AGENTS.md`](../../AGENTS.md). What the page does, how a plan is scored, its limits and sources are in [`README.md`](README.md); keep it current when the page changes.

A PTAC tool for designing the routes the City's bobcat crews take to clear bus stops after a storm, and scoring them. **Not a City plan.** Live at somerwalks.org/bus-planner.html (`docs/bus-planner.html`; called "Bus stop routes" and served as `bus-stops.html` until Nov 2026; `docs/bus-stops.html` now forwards there, keeping a shared plan's `#plan=`).

## Files and build

| File | What it is |
|---|---|
| `build.py` | Builds the street network from the bus routes and writes the page. Python standard library only, no network. `python3 analysis/bus-stop-clearing/build.py` from the repo root. Defaults at the top: `SETTINGS` (the page's) and `A` (the network's). |
| `map_template.html` | The page: map, plans, crews, route editor, scoring, settings, saving. `build.py` fills in the data. |
| `data/bus-stops.json`, `data/wards.json` | Copied from `docs/snow/data/` on every build (made by `npm run data`): stops with weekday riders (`riders` getting on, `off` getting off), routes and shapes; ward outlines. |
| `data/computed-plan.json` | The starting plan an earlier version computed (riders first, one street at a time). |
| `output/map.html` → `../../docs/bus-planner.html` | The built page and its public copy. **Never edit the copy.** |

## The model, briefly

- **Street network** (`build.py`): crews drive only along bus routes. Each side of a street is its own one-way leg, the way the bus goes, and crews may drive back along it. A crew may cross the street anywhere, to the stops just before and after it on the other side, measured along the street (crossing minutes each). Legs leaving the city turn like the bus. Stops within 300 m that share no route get a short straight link, 30% longer. One joining link reaches the Boston Ave stops at the Medford line.
- **The day** (in the page): each crew works its list in order (quickest drive, then minutes to clear); the page plays it hour by hour: the share of riders whose stop is clear (one chart line per plan), when each stop is clear, the drive to it, and drives past stops still waiting.
- **Settings** shared by all plans: minutes a stop, mph, crossing minutes, include route 109 (the MBTA clears those). Riders are always people getting on plus getting off. A jump is fixed at 800 m.

## The page

One full-window dashboard: the map (zoom and pan), the riders-clear chart and hour slider over it, a sidebar with plans, crews and the route editor, and a **Settings ▾** menu (settings, save/share, sources). The map browses by default; ✏️ (or E) turns on editing, where you drag across stops to add them to the selected crew (other crews dim), tap them, or add them by name; Done or Esc stops. Reorder by dragging in the list (hovering a row rings its stop; clicking it shows its popup and glides the map there). Tapping a stop on the map while browsing opens its crew and picks it in the list; right-click opens a menu to add it to, move it to or take it off a crew. Undo and redo.

## Saving and sharing

Plans and settings save in `localStorage` under `somersnow.busstops.v2` (the older `…v1` is read once). **Don't rename the key**: people's saved plans live under it, on every page name. Export/import as JSON; "share" makes a link with the plans in `#plan=`. A page rename must keep a forwarding page that passes the hash on.
