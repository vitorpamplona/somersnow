# Where bus riders go

A PTAC map of every bus route with a stop in Somerville, drawn whole through the cities and towns it serves. Pick a stop to see about where its riders get off, or switch to where riders getting off there got on, on a weekday, Saturday or Sunday. **An estimate**, not MBTA data.

**Open it at [vitorpamplona.com/somersnow/bus-trips.html](https://vitorpamplona.com/somersnow/bus-trips.html)**, or open [`output/trips.html`](output/trips.html) in a browser. Not linked from the guide.

## What it shows

- The map opens centered on Somerville, with its neighbors around it; ⤢ zooms out to every route, still centered there. On it: town outlines, the subway, the 15 routes (as they ran in Fall 2025) and their 548 stops, sized by riders.
- With no stop picked: riders who get on in Somerville, and the share who get off in each city or town; the busiest stops in Somerville.
- With a stop picked: which way its buses go, by route and direction ("87 → Lechmere", from the schedule's direction names; "90 ends here" where a trip ends), with an arrow on the map toward each bus's next stop. Riders are counted per route and direction, so a stop served both ways (Davis, Clarendon Hill) keeps them apart, and the buttons show one direction at a time.
- With a stop picked: a chart of riders getting on and off there by hour (the trip's start time plus the schedule's usual minutes to that stop).
- With a stop picked: the stops where its riders get off light up in orange (bigger: more riders; stops with under 1 rider a day are left out) and its routes take their colors; the share by city or town, a list of the stops, and one button per route to show only that route. Hover a stop or a row for its numbers.
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
- **Friday** is in the file on its own and left out; "Weekday" is the file's `Wkdy`, as in the bus stop routes tool.

## Files

| Path | What it is |
| --- | --- |
| `build.py` | Downloads the data (cached in `../../.cache/`), makes the estimate, writes the page. Python standard library only. Run `npm run trips` (or `python3 analysis/bus-trips/build.py`) from the repo root. |
| `trips_template.html` | The page: map, panel, interaction. `build.py` fills in the data. |
| `output/trips.html` | The page (self-contained). |
| `../../docs/bus-trips.html` | The same page on the public site, copied by `build.py`. Don't edit it by hand. |

## Sources

- Riders: [MBTA Bus Ridership by Trip, Season, Route/Line and Stop](https://mbta-massdot.opendata.arcgis.com/datasets/8daf4a33925a4df59183f860826d29ee), the newest Fall season (Fall 2025), average boardings and alightings per trip and stop.
- Stops, towns, route shapes, subway lines and stations: the MBTA schedule (GTFS), the last feed of the same season from the [MBTA's feed archive](https://cdn.mbta.com/archive/archived_feeds.txt) (Fall 2025, from Nov 24, 2025).
- Routes: every route with a stop in Somerville in `docs/data/bus-stops.json` (from the same ridership file).
- Town outlines: [MassGIS municipalities with generalized coast](https://www.mass.gov/info-details/massgis-data-municipalities).
- Rivers and ponds: [MassDEP Hydrography (1:25,000)](https://www.arcgis.com/home/item.html?id=22e491ae01cc4907934d8a81f2e0b40b) water bodies from MassGIS, codes 1 (reservoirs), 6 (rivers and ponds) and 8 (tidal water), over 5,000 m², cut to the map. Town lines run down the middle of the Charles and the Mystic, so the town outlines alone left them out. The unnamed codes 2, 5 and 7 look like marsh and wetland and are left out (the codebook on mass.gov wasn't reachable).
