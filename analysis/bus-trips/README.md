# Where bus riders go

A PTAC map of every bus route with a stop in Somerville, drawn whole through the cities and towns it serves. Pick a stop to see about where its riders get off, or switch to where riders getting off there got on, on a weekday, Saturday or Sunday. **An estimate**, not MBTA data.

**Open it at [vitorpamplona.com/somersnow/bus-trips.html](https://vitorpamplona.com/somersnow/bus-trips.html)**, or open [`output/trips.html`](output/trips.html) in a browser. Not linked from the guide.

## What it shows

- The map: town outlines, the subway, the 15 routes (as they ran in Fall 2025) and their 548 stops, sized by riders.
- With no stop picked: riders who get on in Somerville, and the share who get off in each city or town; the busiest stops in Somerville.
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
- **Fall 2025.** Routes, stops and riders are from that season (the newest the MBTA has published). Some routes have changed since: today's MBTA API has no stops for the 194 or the CT2 (747). The 194 (about 15 riders a weekday) has no route shape in the schedule, so its stops show without a line.
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
