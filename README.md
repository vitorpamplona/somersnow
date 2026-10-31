# Somerville Snow Guide

Somerville's sidewalk snow and ice rules, for everyone who walks, rolls or rides the bus. Made by the Somerville Pedestrian & Transit Advisory Committee (PTAC). Not an official City of Somerville page: the [City's rules](https://www.somervillema.gov/snow) apply.

**Live site:** https://vitorpamplona.com/somersnow/

- **6 daylight hours** after the snow stops. Night doesn't count.
- **36 inches** wide, down to bare pavement. Ice too.
- **Curb ramp to the crosswalk.** Required for businesses, asked of everyone.

## What's in the repo

- `docs/`: the website (plain HTML, CSS and JavaScript modules, no build step), including a deadline calculator that uses Somerville sunrise and sunset times, a "who clears this?" street corner, a salt-or-sand thermometer and a fine calculator.
- `docs/storm.html`: a replay of the February 22–24, 2026 storm, hour by hour, built from public data (`npm run data` refreshes `docs/data/`).
- `docs/flyer.html`: a one-page printable flyer with a QR code, for doors, building lobbies and shop windows.
- `docs/cards/` and `cards/src/`: 34 phone-size cards to share, as PNGs and as editable HTML. Gallery at `/cards.html`.
- `research/`: the ordinance text and fines, questions and proposals for City, MBTA and State officials, and sources.

## Work on it

```sh
npm run dev      # serve the site at http://localhost:8080
npm test         # check the deadline math
npm run data     # refresh docs/data/ from public sources (Python 3, no keys)
npm i && npm run cards   # re-render card PNGs after editing cards/src (uses Playwright)
```

All English text is in `docs/i18n/en.js`. To add a language, copy it to `docs/i18n/<code>.js`, translate the values, have a native speaker review it, and list it in `docs/i18n/languages.js`. Spanish, Portuguese, Haitian Creole and Nepali drafts are waiting for review: preview them with `?lang=es`, `?lang=pt`, `?lang=ht` or `?lang=ne`, and see `research/translation-review.md`.

GitHub Pages serves the `docs/` folder from `main` (**Settings → Pages → Deploy from a branch → `main` / `/docs`**). GitHub Actions runs the tests on every push.

AI agents: `AGENTS.md` holds the project context, verified facts, open questions, style rules and how to change things (`CLAUDE.md` points to it). `docs/llms.txt` is a plain-text summary of the rules for AI assistants that read the live site.
