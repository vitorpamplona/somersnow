# Somerville Snow Guide

Somerville's sidewalk snow and ice rules, for everyone who walks, rolls or rides the bus. Made by the Somerville Pedestrian & Transit Advisory Committee (PTAC). Not an official City of Somerville page: the [City's rules](https://www.somervillema.gov/snow) apply.

**Live site:** https://vitorpamplona.com/somersnow/

- **6 daylight hours** after the snow stops. Night doesn't count.
- **36 inches** wide, down to bare pavement. Ice too.
- **Curb ramp to the crosswalk.** Required for businesses, asked of everyone.

## What's in the repo

- `docs/`: the website (plain HTML, CSS and JavaScript modules, no build step), including a deadline calculator that uses Somerville sunrise and sunset times, a "who clears this?" street corner, a salt-or-sand thermometer and a fine calculator.
- Storm mode: while snow is on the way, falling or just ended, the top of the guide shows a live banner from the National Weather Service (forecast, warnings, when the snow stopped at Logan) with an estimated shoveling deadline and a calendar reminder. Preview it with `?live=stopped` (or `forecast`, `snowing`, `passed`).
- `docs/storms/`: a replay page for every storm of 3 inches or more since 2016, hour by hour, built from public data: snow at Logan and inside Somerville, weather warnings, the City's snow emergency, the shoveling deadline, 311 reports by ward, the T, buses, Bluebikes, tows, MBTA alerts and crashes. `npm run data` refreshes the data and the pages, and `npm run verify` checks the published numbers against the pages; the data guide (`docs/data/README.md`) explains every file, with one CSV per storm and the records behind the counts; what each source covers and its caveats are in `AGENTS.md` ("Storm replays and data") and `research/data-sources.md`.
- `docs/flyer.html`: a one-page printable flyer with a QR code, for doors, building lobbies and shop windows.
- `docs/cards/` and `cards/src/`: 34 phone-size cards to share, as PNGs and as editable HTML. Gallery at `/cards.html`.
- `research/`: the ordinance text and fines, questions and proposals for City, MBTA and State officials, and sources.

## Work on it

```sh
npm run dev      # serve the site at http://localhost:8080
npm test         # check the deadline math
npm run data     # refresh docs/data/ and the storm pages from public sources (Python 3, no keys)
npm run pages    # rebuild only the storm pages in docs/storms/
npm i && npm run cards   # re-render card PNGs after editing cards/src (uses Playwright)
```

All English text is in `docs/i18n/en.js`. To add a language, copy it to `docs/i18n/<code>.js`, translate the values, have a native speaker review it, and list it in `docs/i18n/languages.js`. Spanish, Portuguese, Haitian Creole and Nepali drafts are waiting for review: preview them with `?lang=es`, `?lang=pt`, `?lang=ht` or `?lang=ne`, and see `research/translation-review.md`.

GitHub Pages serves the `docs/` folder from `main` (**Settings → Pages → Deploy from a branch → `main` / `/docs`**). GitHub Actions runs the tests on every push.

AI agents: `AGENTS.md` holds the project context, verified facts, open questions, style rules and how to change things (`CLAUDE.md` points to it). `docs/llms.txt` is a plain-text summary of the rules for AI assistants that read the live site.
