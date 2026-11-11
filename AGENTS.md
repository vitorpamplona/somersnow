# SomerWalks: guide for coding agents

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor and others) and for people new to the repo. `CLAUDE.md` points here. Read this file first, then the guide for the area you're working in (the "Read first" column below).

## What this is

**somerwalks.org**: projects by the **Somerville Pedestrian & Transit Advisory Committee (PTAC)** for people who walk, roll or ride the bus in Somerville, MA. Volunteer-made, public, MIT license. **Not an official City or MBTA site**, and nothing here may say or look otherwise.

The first and biggest project is the **snow guide**: Somerville's sidewalk snow and ice rules, for new residents first and everyone second. Its goal: more people shovel on time, down to the pavement, ramps included, so walking to transit works in winter. Around it: storm replays (what actually happens in a storm, hour by hour, from public data, every snow period since the winter of 2015–16), and tools about the buses.

## Map of the repo

| Area | Live at | What it is | Read first |
|---|---|---|---|
| `docs/` | somerwalks.org | The whole website, served as-is by GitHub Pages. Home page `docs/index.html` (a tile per project). | this file |
| `docs/snow/` | /snow/ | The snow guide: one page, its scripts, translations, cards gallery, two flyers. | [`docs/snow/AGENTS.md`](docs/snow/AGENTS.md) |
| `docs/snow/storms/`, `docs/snow/data/`, `scripts/` | /snow/storms/ | Storm replays: a page per snow period since the winter of 2015–16, built from public data by Python scripts; `scripts/` also renders cards, flyer, GIF and the Council letter. | [`scripts/AGENTS.md`](scripts/AGENTS.md), then [`docs/snow/data/README.md`](docs/snow/data/README.md) |
| `cards/src/` | /snow/cards.html | 34 phone-size social cards, editable HTML; rendered to `docs/snow/cards/`. | [`docs/snow/AGENTS.md`](docs/snow/AGENTS.md) |
| `analysis/bus-trips/` | /bus-trips.html, /bus-pulse.html | "Where bus riders go" (pick a stop, see where its riders get off) and "Somerville's pulse" (a weekday on the buses, animated). One build writes both. | [`analysis/bus-trips/AGENTS.md`](analysis/bus-trips/AGENTS.md) |
| `analysis/bus-stop-clearing/` | /bus-planner.html | Bus stop clearing planner: design and score the routes crews take to clear bus stops after a storm. | [`analysis/bus-stop-clearing/AGENTS.md`](analysis/bus-stop-clearing/AGENTS.md) |
| `research/` | (not served) | The law, verified facts, open questions for officials, sources, data-source notes, PTAC's letter to the City Council. | [`research/facts.md`](research/facts.md) |
| `test/` | | `node --test` tests for the guide's deadline and live-storm logic. | |

Per-project READMEs (`analysis/*/README.md`, `docs/snow/data/README.md`) are for humans: what the page shows, the method and its limits. The `AGENTS.md` next to them is for changing the code.

## Run it

Needs Node 22+ and Python 3 (standard library only). `npm install` once, for Playwright (renders cards, flyer and GIF); if it can't find a browser, `npx playwright install chromium`.

```sh
npm run dev      # serve docs/ at http://localhost:8080 (home at /, guide at /snow/); ES modules don't load from file://
npm test         # unit tests (deadline math, live storm mode)
npm run verify   # recompute the storm replays' published numbers from docs/snow/data and check them against the pages (no downloads)
```

Builders (each writes into `docs/`; run the one for what you changed):

| Command | Rebuilds | Needs |
|---|---|---|
| `npm run data` | storm data (`docs/snow/data/`) and pages, from public sources | network, about 9 GB cached in `.cache/`, about an hour |
| `npm run pages` | storm pages only, from `docs/snow/data/` | nothing |
| `npm run cards` (`-- 23-fines` for one) | card PNGs from `cards/src/` | Playwright |
| `npm run flyer` | `docs/snow/flyer-phone.png` | `npm run dev` running |
| `npm run trips` | `docs/bus-trips.html` and `docs/bus-pulse.html` | network: big downloads are cached in `.cache/` after the first run, but every build fetches the MBTA's small feed list; delete `.cache/bus-trips-osm.json` to pick up new OpenStreetMap edits |
| `npm run planner` | `docs/bus-planner.html` | `docs/snow/data/bus-stops.json` and `wards.json` (no network) |
| `npm run lights` | the "Somerville's lights" GIF and video in the cards gallery | `npm run dev` running, ffmpeg |
| `npm run letter` | `research/ordinance-proposals.pdf` (git-ignored) | network for fonts |

## How changes reach the site

- **`main` is live.** GitHub Pages serves `docs/` from `main`; anything merged there is on somerwalks.org within a minute or two. There is no build step on the server: what's committed in `docs/` is what's served.
- **Work on a branch and open a pull request** against `main`. Don't push to `main` unless a maintainer asked you to. CI (`.github/workflows/test.yml`) runs `npm test` and `npm run verify` on every push and pull request.
- **Generated files are committed, and never edited by hand.** Edit the source, rebuild, commit both. Sources → outputs: `cards/src/*.html` → `docs/snow/cards/*.png`; `scripts/storm_page.html` + `docs/snow/data/` → `docs/snow/storms/*.html`; `analysis/*/…_template.html` + `build.py` → `analysis/*/output/` → copied to `docs/*.html`; `docs/snow/flyer-phone.html` → `flyer-phone.png`.
- **Before you push:** `npm test` and `npm run verify` (CI runs both); open the page with `npm run dev` and check it at phone width (390 px): nothing scrolls sideways, nothing overlaps, no errors in the console. Check desktop too.
- **Commits:** a short subject that says what changed for the reader of the site ("Bus trips: the hourly chart follows the bus picked"), then why, in plain sentences.
- **Update the docs in the same change**: the area's `AGENTS.md` when how things work changes, its README when what the page shows changes, `research/facts.md` when a fact changes.

## Ground rules

1. **Every fact needs a source.** Law from `research/source-files/` or Municode; City practice from somervillema.gov; MBTA facts from mbta.com. A source seen only as a search snippet is marked * in `research/sources.md`. Never add a fact from memory. Unconfirmed? Add it to "Not yet confirmed" in `research/facts.md` and to `research/questions.md`, not to the site.
2. **Not official.** Every page says it's PTAC's, not the City's or the MBTA's. No City or MBTA logos. Don't soften the "not an official City page" line.
3. **Estimates say so.** Anything modeled (where riders get off, buses on schedule, a computed deadline) is labeled an estimate on the page, with the method a click away.
4. **Missing data is "not available", never zero**, with the reason.
5. **Privacy.** No house numbers for incidents (crashes, fire calls: street or intersection only); no personal data; complaint counts are complaints, not conditions. Area guides have the specifics.
6. **Public data, no keys.** Builders use public sources and the standard library (Python) or Playwright (Node). Big downloads go to `.cache/` (git-ignored). Credit sources on the page (OpenStreetMap data needs "© OpenStreetMap contributors", ODbL).
7. **Accessible.** Works on a phone first; keyboard reachable; text contrast on the dark panels; animations stop or calm down with `prefers-reduced-motion`; charts and maps have a text equivalent (`aria-label`, tables, tooltips).
8. **Somerville since 2015.** The city changed a lot after 2014 (Assembly station 2014, the pandemic 2020, the Green Line Extension 2022, the bus network redesign from Dec 2024): data from before 2015 is context only, never "how Somerville moves", and every number carries its year. Mind those breaks in any series ([`research/mobility-data.md`](research/mobility-data.md#read-first-somerville-since-2015)).
9. **No build tooling on the site.** Plain HTML, CSS and JavaScript modules; links between pages are relative; no frameworks, no bundler, no tracking.

## Voice and design

- **Short sentences, pictures first.** The owner cut the first version of the guide for having too many words. One headline and one short line per idea; icon tiles over paragraphs. Plain and direct ("Ice can never happen.", "Blue lights? Move your car.").
- **Colors** (same as the cards): navy `#10243A`, panel `#1A3A5F`, snow `#EEF3F7`, orange `#FF8A3D` (on dark), rust `#B93D06` (on light), ice `#A9C4E4`, mute `#47607C`. On the bus pages, orange `#E36F28`/`#FF8A3D` means getting on and blue `#4F98DE` getting off, everywhere on the page.
- **Fonts:** Barlow Condensed 700/800 for headings (uppercase), Barlow for body, from Google Fonts.
- **Every page:** the dark header bar with the SomerWalks brand linking home (`./` or `../`), a title like `Where bus riders go · SomerWalks`, and the PTAC / not-official line.

## Recipes

**Add a new PTAC project page.** A page with no data (text, a form, a calculator) is written straight into `docs/<name>.html`. A page built from data follows the bus pages: `analysis/<name>/` with a `build.py` (standard library) that writes `output/<name>.html` from a template (data replaces a `/*DATA*/null` placeholder, so the page works from one file) and copies it to `docs/<name>.html`; an npm script for it. Either way: start from an existing page's `<head>` and header bar (`analysis/bus-trips/trips_template.html` has the fonts, colors, the SomerWalks brand linking home and the PTAC / not-official line); a `README.md` (what it shows, method, limits, sources) and an `AGENTS.md` (files, build, gotchas) plus a one-line `CLAUDE.md` (`@AGENTS.md`) in its folder; a tile on `docs/index.html`; a row in the root `README.md` projects table and in the map above.

**Change a rule or a number in the snow guide** (a fine, the even/odd side, the lots): follow the checklist in [`docs/snow/AGENTS.md`](docs/snow/AGENTS.md#change-a-rule-or-a-number). It touches the facts list, every language file, the page, both flyers, `docs/llms.txt`, the cards and the law notes.

**Add a data source to the storm replays:** see [`scripts/AGENTS.md`](scripts/AGENTS.md#add-a-source). Every new number must be checkable: hourly CSV, raw records, the data guide, and `verify.mjs` for headline numbers.

**Rename or move a page:** leave a small forwarding page at the old address that keeps `location.search + location.hash` (see `docs/bus-stops.html`), and fix every link (`grep -rn old-name docs analysis scripts *.md`).

## Where the knowledge lives

| File | What's in it |
|---|---|
| [`research/facts.md`](research/facts.md) | Verified facts the site states, with their sources; what's not yet confirmed; resident feedback. |
| [`research/questions.md`](research/questions.md) | Questions and proposals for City, MBTA and State officials (numbered; pages cite them as "question 47"). |
| [`research/ordinance.md`](research/ordinance.md), [`research/source-files/`](research/source-files/) | The ordinance text and fines, and the original PDFs. |
| [`research/sources.md`](research/sources.md) | Every source, * for search-snippet-only. |
| [`research/mobility-data.md`](research/mobility-data.md) | Catalog of public data on how Somerville moves (buses and stops, the T, walking, biking, cars, parking, safety, surveys): what, where, years, status, links. Start here before looking for a new dataset. |
| [`research/data-sources.md`](research/data-sources.md) | Public datasets for the storm replays: what each holds, queries, caveats. |
| [`research/ordinance-proposals.md`](research/ordinance-proposals.md) | PTAC's letter to the City Council proposing amendments to the snow ordinances. |
| [`research/translation-review.md`](research/translation-review.md) | Checklist for native speakers reviewing a translation. |
| [`docs/llms.txt`](docs/llms.txt) | Plain-text summary of the rules for AI assistants that read the live site. Keep it in sync with the facts. |

## Site structure and history

- Domain bought Nov 2026; DNS on Squarespace points to GitHub Pages (`docs/CNAME`, HTTPS enforced). Repository `vitorpamplona/somerwalks`, renamed from `somersnow` in Nov 2026; the old address (vitorpamplona.com/somersnow/) stopped working then, and PTAC moves people to the new site by hand (no forwarding repository, by choice).
- The guide used to sit at the top of `docs/`; it moved to `docs/snow/` in Nov 2026. Every old page path has a small forwarding page to its new place (written once by `scripts/build_redirects.py`, which skips real pages); `docs/404.html` sends any other old address (card images, data files) to the same path under `snow/`; old guide links with `#section`, `?lang=` or `?live=` reach the home page, which sends them on. New pages never need forwarding pages.
- Built Oct–Nov 2026: the guide's sections, cards and research; the animated corner, the redrawn "Who clears this?" map, flyers, draft translations, live storm mode; storm replays (one storm, then all 44 snow periods with "Getting around" data); then the bus tools and the PTAC home page. The git log has the details.

## For maintainers

Working copies on claude.ai (private to the owner; the repo copies are what others should use):
- Card canvas (Design): https://claude.ai/artifact/AcoF5JNBV3Eg96bzdTDnZe (`cards/src` is an export of it).
- Questions doc: https://claude.ai/artifact/2oc3c9e1vG2C7EkckRYyr2 (`research/questions.md` is a copy).
- Proposed ordinance amendments: https://claude.ai/artifact/7vG43e3w32sGB4efaCwyZE (`research/ordinance-proposals.md` is a copy; `npm run letter` typesets it; keep only the PDF actually sent, in `research/source-files/`).
- First single-file version of the site: https://claude.ai/artifact/VHq19kkjN4reR43fhd98du
