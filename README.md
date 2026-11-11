# SomerWalks

Projects for people who walk, roll or ride the bus in Somerville, MA, by the Somerville Pedestrian & Transit Advisory Committee (PTAC). Volunteer-made, public data, MIT license. **Not an official City of Somerville or MBTA site.**

**Live:** https://somerwalks.org

## The projects

| Project | Live | What it is |
|---|---|---|
| **Snow guide** | [/snow/](https://somerwalks.org/snow/) | Somerville's sidewalk snow and ice rules in short lines and pictures: **6 daylight hours** after the snow stops (night doesn't count), **36 inches** wide down to bare pavement (ice too), **the curb ramp to the crosswalk** (required for businesses, asked of everyone). A deadline calculator with Somerville's sunrise and sunset, a "who clears this?" street corner, salt or sand, fines, and a live storm banner from the National Weather Service (preview with `?live=stopped`). The [City's rules](https://www.somervillema.gov/snow) apply. |
| **Storm replays** | [/snow/storms/](https://somerwalks.org/snow/storms/) | Every snow period since 2016, hour by hour, from public data: snow at Logan and inside Somerville, warnings, the snow emergency, the deadline, 311 reports by ward, the T, buses, Bluebikes, tows, alerts, crashes and Fire Department calls. Every number is checkable: [the data guide](docs/snow/data/README.md), one CSV per storm, the records behind the counts, and `npm run verify`. |
| **Flyers and cards** | [/snow/cards.html](https://somerwalks.org/snow/cards.html) | A printable flyer with a QR code, a phone flyer, 34 phone-size cards to share, and "Somerville's lights", an animation of the evening rush. |
| **Where bus riders go** | [/bus-trips.html](https://somerwalks.org/bus-trips.html) | Pick a bus stop: about where its riders get off, when it's busy, and what's at the stop (shelter, bench, accessibility). An estimate from the MBTA's counts. [Method](analysis/bus-trips/README.md). |
| **Somerville's pulse** | [/bus-pulse.html](https://somerwalks.org/bus-pulse.html) | A weekday on the buses, played back: every trip, every stop. Try [Holiday lights](https://somerwalks.org/bus-pulse.html#lights). |
| **Transit over time** | [/transit-trends.html](https://somerwalks.org/transit-trends.html) | How many ride the bus, the T and Bluebikes in Somerville, every fall since 2016: by route, station, stop and hour, against 2019. From the MBTA's counts. [Method](analysis/transit-trends/README.md). |
| **Bus stop clearing planner** | [/bus-planner.html](https://somerwalks.org/bus-planner.html) | Design and score the routes crews take to clear bus stops after a storm. Not a City plan. [How it works](analysis/bus-stop-clearing/README.md). |

Behind them, `research/` holds the ordinance text and fines, the verified facts, questions and proposals for City, MBTA and State officials, every source, and [a catalog of public mobility data for Somerville](research/mobility-data.md).

## Work on it

```sh
npm install      # once: Playwright, for rendering cards, the flyer and the animation
npm run dev      # serve the site at http://localhost:8080
npm test         # unit tests
npm run verify   # check the storm replays' numbers against their data
```

The site is plain HTML, CSS and JavaScript with no build step; GitHub Pages serves the `docs/` folder from `main`. Pages built from data (storm replays, bus pages, cards) have a script that writes them: see the table in [`AGENTS.md`](AGENTS.md#run-it).

**Contributing:** open an issue or a pull request against `main`. [`AGENTS.md`](AGENTS.md) is the guide for anyone changing the code, person or AI agent: the map of the repo, how changes go live, the ground rules (every fact needs a source; nothing official-looking; estimates say so) and recipes. Each area has its own `AGENTS.md` next to its code.

**Translations:** all English text of the guide is in `docs/snow/i18n/en.js`. Spanish, Portuguese, Haitian Creole and Nepali drafts are waiting for native-speaker review: preview them with `?lang=es`, `?lang=pt`, `?lang=ht` or `?lang=ne`, and see [`research/translation-review.md`](research/translation-review.md).

**AI assistants reading the site:** [`docs/llms.txt`](docs/llms.txt) is a plain-text summary of the rules.
