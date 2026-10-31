# Somerville Snow Guide

Somerville's sidewalk snow and ice rules, for everyone who walks, rolls or rides the bus. Made by the Somerville Pedestrian & Transit Advisory Committee (PTAC). Not an official City of Somerville page: the [City's rules](https://www.somervillema.gov/snow) apply.

**Live site:** https://vitorpamplona.github.io/somersnow/

- **6 daylight hours** after the snow stops. Night doesn't count.
- **36 inches** wide, down to bare pavement. Ice too.
- **Curb ramp to the crosswalk.** Required for businesses, asked of everyone.

## What's in the repo

- `site/`: the website (plain HTML, CSS and JavaScript modules, no build step), including a deadline calculator that uses Somerville sunrise and sunset times, a "who clears this?" street corner, a salt-or-sand thermometer and a fine calculator.
- `site/cards/` and `cards/src/`: 34 phone-size cards to share, as PNGs and as editable HTML. Gallery at `/cards.html`.
- `research/`: the ordinance text and fines, questions and proposals for City, MBTA and State officials, and sources.

## Work on it

```sh
npm run dev      # serve the site at http://localhost:8080
npm test         # check the deadline math
npm i && npm run cards   # re-render card PNGs after editing cards/src (uses Playwright)
```

All English text is in `site/i18n/en.js`. To add a language, copy it to `site/i18n/<code>.js`, translate the values, have a native speaker review it, and list it in `site/i18n/languages.js`.

Pushing to `main` tests and publishes the site through GitHub Actions. In the repo's **Settings → Pages**, set **Source** to **GitHub Actions** once.

Working with Claude Code: `CLAUDE.md` holds the project context, verified facts, open questions and style rules.
