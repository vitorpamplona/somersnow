# The snow guide (`docs/snow/`)

Agent guide for the guide itself, its cards and flyers. Start with the root [`AGENTS.md`](../../AGENTS.md). The storm replays (`storms/`, `data/`) are built by scripts: see [`scripts/AGENTS.md`](../../scripts/AGENTS.md).

Live at **somerwalks.org/snow/**. Plain HTML, CSS and JavaScript modules; no build step.

## Files

| File | What it is |
|---|---|
| `index.html` | All the guide's markup. Every piece of English text is tagged `data-i18n="section.NN"`. |
| `i18n/en.js` | Every English string: `page` (mirrors the `data-i18n` tags) and `ui` (text scripts write, e.g. `ui.live` for storm mode). |
| `i18n/languages.js` | Languages in the switcher. The switcher stays hidden while only English is listed. |
| `i18n/drafts.js`, `es.js`, `pt.js`, `ht.js`, `ne.js` | AI-drafted translations waiting for native-speaker review. Not in the switcher; preview with `?lang=es` (a banner marks them as drafts). Checklist: [`research/translation-review.md`](../../research/translation-review.md). |
| `js/deadline.js` | Pure sunrise/sunset and 6-daylight-hour deadline math. Tested by `test/deadline.test.js`. Also used by the storm replays. |
| `js/live.js` | Live "storm mode": an orange banner above the hero, shown only while snow is on the way, falling, or just ended. See below. Logic in `liveState()`, tested by `test/live.test.js`. |
| `js/shovel.js` | The animated street corner for "Down to the pavement" (steps 1–5). Each step plays one short animation; CSS under "shovel scene" in `css/style.css`. |
| `js/corner.js` | The street-corner SVG for "Who clears this?". |
| `js/main.js` | Wires the page: steps, who-clears map, calculator (starts at "just now" from Oct 1 to May 1), salt slider, fines, share-this-card links, nav. |
| `css/style.css` | The guide's styles (also used by `cards.html`; the flyers carry their own). |
| `cards.html` | Gallery: the two flyers first, then the 34 cards from `cards/cards.json`, then the bonus "Somerville's lights" animation. ("Flyers and cards" on the home page.) |
| `cards/` | Card PNGs (1080×1920) rendered from `../../cards/src/*.html`; `cards.json` lists them in story order. Plus `somerville-lights.gif` (480×854, about 10 MB), `.mp4` (540×960) and `.jpg` (poster). |
| `flyer.html` | One-page US Letter flyer to print and post, with a QR code (`qr.svg`, to https://somerwalks.org/snow/). |
| `flyer-phone.html`, `flyer-phone.png` | The same facts in one tall column for phones and social media; the PNG (1080 px wide) is what people save. `npm run flyer` re-renders it (with `npm run dev` running). |
| `storm.html` | Forwards `storm.html?storm=<id>` to the fixed replay page. |
| `../llms.txt` | Plain-text summary of the rules for AI assistants that read the live site. |

## Live storm mode (`js/live.js`)

Reads the National Weather Service API in the browser (forecast grid BOX 70,102 snowfall, active alerts for zone MAZ014, Logan KBOS observations), refreshed every 15 minutes. Phases: forecast → snowing (estimated deadline if it stops when forecast) → stopped ("Shovel by" from `deadline.js`, a countdown, "Add to my calendar" .ics) → deadline passed (311, ice, space savers) for 30 hours. A passing flurry (under 3 snowy reports) doesn't start the clock. Everything is labeled an estimate; the City's snow emergency has no feed, so the banner says how to check. Preview with `?live=forecast`, `?live=snowing`, `?live=stopped` or `?live=passed` (marked "Demo"). Text: `ui.live` in `en.js`.

## Change text

Edit `index.html` and `i18n/en.js` together: keys in `en.js` must match the `data-i18n` attributes, and new visible text gets a new key. Add the new keys to the draft translations too, or they fall back to English.

## Change a rule or a number

A new fine, a new even/odd side, new parking lots: update it everywhere it appears, in this order, then search the repo for the old value before you finish.

1. [`research/facts.md`](../../research/facts.md) (with its source).
2. `i18n/en.js`, and every translation that has the text (`es.js`, `pt.js`, `ht.js`, `ne.js`; their values are in their own language, so search for the number).
3. `index.html`, and numbers the scripts hold: `js/main.js` (`FINES`, the fine calculator, written without `$`) and `js/storm.js` (the replays' phone messages, e.g. "Space savers … $100"); then `npm run pages` if `storm.js` changed.
4. `flyer.html` and `flyer-phone.html` (each has its own copy of the key facts), then `npm run flyer`.
5. `../llms.txt`.
6. The affected cards in `../../cards/src/`, then `npm run cards -- <card>` (e.g. `23-fines`).
7. [`research/ordinance.md`](../../research/ordinance.md) if it's law.

When you search (e.g. `grep -rn '\$100' --include=*.html --include=*.js --include=*.md --include=*.txt .`), many hits are other fines with the same amount (space savers, tow-zone and hydrant tickets): change only the one that changed. Leave alone `research/ordinance-proposals.md` (the letter as sent), `research/source-files/` (original documents) and the storm data.

## Cards

The 34 cards are standalone HTML in `cards/src/` (an export of the owner's Design canvas on claude.ai). Edit the HTML, then `npm run cards` (all) or `npm run cards -- 23-fines` (one). Text on a card must match the guide and the facts list. The gallery counts "34 cards" in several places (home tile, `cards.html` description, guide text, translations); the bonus animation is not counted. `npm run lights` remakes the animation (the pulse page's Holiday lights look over the evening rush, 4:30–6:30 p.m., 10 minutes of the day a second, 12 s; needs `npm run dev` and ffmpeg; the page's clock is stepped frame by frame).

## Rules for the guide's words

- Say **sidewalk** explicitly. Say who the duty falls on.
- **Never imply homes must legally clear curb ramps** (only businesses must; for homes it's a City request).
- Present it as **PTAC's guide, not an official City page**. Cite ordinance sections in the footer, not inline.
- **Crosswalk stripes run parallel to traffic** (the long side along the road) in every drawing. This was corrected once already.
- **Translations** need native-speaker review before they go into `languages.js`. Somerville publishes its own rules in 9 languages; Spanish, Portuguese, Haitian Creole and Nepali are the priorities.
- Resident feedback worth keeping in mind (not data): small storms leave the worst ice; the first December storm is when people relearn the rules.
