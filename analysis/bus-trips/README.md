# Where bus riders go

A PTAC map of every bus route with a stop in Somerville, drawn whole through the cities and towns it serves. Pick a stop to see about where its riders get off, or switch to where riders getting off there got on, on a weekday, Saturday or Sunday. **An estimate**, not MBTA data.

**Open it at [somerwalks.org/bus-trips.html](https://somerwalks.org/bus-trips.html)**, or open [`output/trips.html`](output/trips.html) in a browser. Not linked from the guide.

## What it shows

- The map opens centered on Somerville, with its neighbors around it; ⤢ zooms out to every route, still centered there. On it: town outlines, the subway, the 15 routes (as they ran in Fall 2025) and their 548 stops, sized by riders.
- With no stop picked: how many riders get on a bus in Somerville, and the 10 busiest stops, to pick one.
- With a stop picked: which way its buses go, by route and direction ("87 → Lechmere", from the schedule's direction names; "90 ends here" where a trip ends), with an arrow on the map that follows the route's own line toward each bus's next stop (the stretch of the schedule's shape between the two stops; straight where no pattern matches, 2 of 870). Riders are counted per route and direction, so a stop served both ways (Davis, Clarendon Hill) keeps them apart, and each direction has its own row.
- With a stop picked, "At this stop", as icon tiles (bright: there; dim and slashed: not there; dashed: no data), each with its source and year ("OSM 2023", "MBTA 2017"). Each item comes from its newest source: OpenStreetMap where volunteers tagged it (shelter, bench, trash, lit, tactile paving, live sign), else the MBTA's 2017 accessibility survey (bench, trash; bike rack and paths narrowed under 36 inches come only from it); ADA status from the MBTA (Jan 2024); wheelchair boarding from the schedule. Tap a tile, or the same icon in the row of buttons along the bottom of the map (no stop needs to be picked), to find that item on the map: every stop with it turns into a dark dot (an orange dot gets a thick dark ring), and a bar on the map switches between Yes, No and No data with counts for all the stops on the map; tap the tile again, ✕ or Esc to stop. An "Edit on OSM" link opens the stop in OpenStreetMap, for volunteers who check it on foot. For Somerville's stops, OpenStreetMap's bench and trash values are newer than 2017 almost everywhere; they agree with the survey at about two thirds of stops, and at 57 OSM has a bench where the 2017 survey had none.
- With a stop picked: two big counts that are also the switch (riders getting on here, and where they get off; or getting off here, and where they got on), then a chart of riders getting on and off there by hour (the trip's start time plus the schedule's usual minutes to that stop), for every bus or only the bus picked.
- With a stop picked: the stops where its riders get off light up in orange (bigger: more riders; stops with under 1 rider a day are left out) and its routes take their colors; a row per route and direction, with its riders and a bar for its share (tap one to show only its riders; "Every bus" goes back); the top 5 stops where they get off, then all of them. Hover a stop or a row for its numbers.
- A stop where buses end their trip has no one getting on; the page offers where its riders got on instead.
- The address keeps the stop, day and view (`#stop=5104&day=Sat&show=on`), so a link opens the same view.

## How it's estimated

The MBTA publishes, for every scheduled trip, the average number of people getting on and off at each stop, but not who gets off where. So, trip by trip:

1. Everyone on the bus is equally likely to get off at the next stop: the people getting off at a stop are a mix of everyone on board, in proportion to where they got on.
2. Then the people getting on join.
3. Whoever is still on board at the last stop gets off there.

Adding up every trip of the day gives about how many riders go from each stop to each other stop, on each route. The totals match the MBTA's counts: everyone who gets on gets off somewhere later on the same trip.

## Limits

- **Where riders leave the bus, not where they end up.** Many who get off at Davis, Sullivan, Harvard or Lechmere change to the subway or another bus. A trip with a transfer shows as two.
- **An assumption, not a survey.** Real riders aren't equally likely to get off anywhere: few ride one stop. The pairs are a best guess; the totals by stop are the MBTA's.
- **Only Somerville's routes.** A stop in Cambridge shows only the riders on these 15 routes, not on other routes that stop there.
- **Fall 2025.** Routes, stops and riders are from that season (the newest the MBTA has published). Some routes have changed since: today's MBTA API has no stops for the CT2 (747).
- **Route "194" is the 89/93.** The ridership file calls it 194; the schedule calls it 89/93 (route id `8993`, "Clarendon Hill – Haymarket Station", a supplemental bus): one early trip a day via Sullivan, at the same times in both (4:30 a.m. weekdays, 4:33 Saturday, 5:16 Sunday). The page shows it as 89/93, with the schedule's shape. About 15 riders a weekday.
- **Branches.** Each route is drawn with its usual patterns and branches (the schedule's typicality 1 and 2, such as the 87 and 89 to Clarendon Hill), plus any rarer pattern that serves a stop none of those reach.
- **Bennett Alley.** The ridership file starts Harvard trips of the 96 and 109 at "Bennett Alley", a stop id no schedule has (checked in the 2022, 2024 and 2025 feeds); it comes right before Harvard's upper busway, so its riders are counted there.
- **Friday** is in the file on its own and left out; "Weekday" is the file's `Wkdy`, as in the bus stop clearing planner.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | Downloads the data (cached in `../../.cache/`), makes the estimate, writes the page. Python standard library only. Run `npm run trips` (or `python3 analysis/bus-trips/build.py`) from the repo root. |
| `trips_template.html` | The page: map, panel, interaction. `build.py` fills in the data. |
| `pulse_template.html` | Somerville's pulse (below). Same data placeholder. |
| `output/trips.html`, `output/pulse.html` | The pages (self-contained). |
| `../../docs/bus-trips.html`, `../../docs/bus-pulse.html` | The same pages on the public site, copied by `build.py`. Don't edit them by hand. |
| `AGENTS.md` | Notes for changing the code. |

## Somerville's pulse

**[somerwalks.org/bus-pulse.html](https://somerwalks.org/bus-pulse.html)**: a weekday on these routes, played back. Every weekday trip (1,090) moves along its route at its own scheduled times (matched to the schedule by route, direction and start time: 954 of them; the rest use the route's usual minutes between stops, so they don't slow down at rush hour). At each stop, riders getting on and off are the trip's average counts: an orange ring for getting on, a blue ring for getting off, and a glow that keeps the last few minutes. A bus grows with its riders and leaves a fading trail; the Buses button hides them. Every Red, Orange, Green and Blue Line train on the map (2,436 on a weekday) moves along its line at its scheduled times, a dot in its line's color that grows with its riders; T stations glow orange and blue as riders get on and off, on a gentler scale than bus stops (a station has far more riders). Station riders are the MBTA's average weekday counts for each hour, line and direction (Fall 2025), shared evenly among that hour's trains: an estimate. The Trains button hides trains and stations; the count "on a train now" is riders on trains on the map. Somerville's outline brightens with the activity. The waveform along the bottom is the whole day, getting on above the line and getting off below, every 5 minutes; drag it to pick a time. Holiday lights (the star, or `#lights` in the address) turns it into red and green lights with twinkling bulbs and snow.

Same limits as above, plus: buses and trains run exactly on schedule, every day the same; a train's riders are its hour's average, not counted train by train; trips logged before 3 a.m. are counted at the end of the service day.

## Sources

- Riders: [MBTA Bus Ridership by Trip, Season, Route/Line and Stop](https://mbta-massdot.opendata.arcgis.com/datasets/8daf4a33925a4df59183f860826d29ee), the newest Fall season (Fall 2025), average boardings and alightings per trip and stop.
- Train riders: [MBTA rail ridership by season, time period and stop](https://mbta-massdot.opendata.arcgis.com/datasets/6494749a29c648018820d0e49636205c), Fall 2025, by hour, line and direction (weekday riders getting on, off, and on board leaving each station).
- Stops, towns, route shapes, subway lines and stations: the MBTA schedule (GTFS), the last feed of the same season from the [MBTA's feed archive](https://cdn.mbta.com/archive/archived_feeds.txt) (Fall 2025, from Nov 24, 2025).
- Routes: every route with a stop in Somerville in `docs/snow/data/bus-stops.json` (from the same ridership file).
- What's at each stop: [MBTA PATI Bus Stops](https://www.arcgis.com/home/item.html?id=24a97982b39f4febb504c9e6cb55879b) (status as of Jan 2024; amenities from 2017). A stop with benches has one record with the count and one per bench with its type and condition; `build.py` merges them. 511 of the 548 stops are in it.
- What volunteers mapped at each stop: [OpenStreetMap](https://www.openstreetmap.org/copyright) bus stops (© OpenStreetMap contributors, ODbL), from an Overpass server, matched to MBTA stops by `ref` (the MBTA stop number; else the nearest stop without one within 30 m), with the year each value was set from the stop's edit history (OpenStreetMap API, cached in `.cache/osm-hist/` by node and version, so only changed stops are fetched again). Delete `.cache/bus-trips-osm.json` to refresh. 531 of 548 stops match. The OSM-derived fields in the page are under the ODbL.
- Town outlines: [MassGIS municipalities with generalized coast](https://www.mass.gov/info-details/massgis-data-municipalities).
- Rivers and ponds: [MassDEP Hydrography (1:25,000)](https://www.arcgis.com/home/item.html?id=22e491ae01cc4907934d8a81f2e0b40b) water bodies from MassGIS, codes 1 (reservoirs), 6 (rivers and ponds) and 8 (tidal water), over 5,000 m², cut to the map. Town lines run down the middle of the Charles and the Mystic, so the town outlines alone left them out. The unnamed codes 2, 5 and 7 look like marsh and wetland and are left out (the codebook on mass.gov wasn't reachable).
