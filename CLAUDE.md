# Somerville Snow Guide (somersnow)

A public guide to Somerville, MA's sidewalk snow and ice rules, for people who walk, roll or ride the bus. Made by the **Somerville Pedestrian & Transit Advisory Committee (PTAC)**. Audience: new residents first, everyone second. Goal: more people shovel on time, down to the pavement, ramps included, so walking to transit works in winter.

## What's here

| Path | What it is |
|---|---|
| `docs/` | The website. GitHub Pages serves this folder straight from `main` (Settings → Pages → Deploy from a branch → `main`, `/docs`). No build step. |
| `docs/index.html` | All page markup. English text lives here, each piece tagged `data-i18n="section.NN"`. |
| `docs/i18n/en.js` | Every English string: `page` (mirrors the `data-i18n` tags) and `ui` (text scripts write). |
| `docs/i18n/languages.js` | Languages in the switcher. The switcher stays hidden while only English is listed. |
| `docs/js/deadline.js` | Pure sunrise/sunset + 6-daylight-hour deadline math. Covered by `test/`. |
| `docs/js/corner.js` | The street-corner SVG used by the step-by-step and "Who clears this?". |
| `docs/js/main.js` | Wires the page: steps, who-clears map, calculator, salt slider, fines, nav. |
| `cards/src/` | The 34 phone-size (1080×1920) social cards as standalone HTML (the editable source). |
| `docs/cards/` | Rendered PNGs, served by the site with a gallery at `docs/cards.html`. `cards.json` lists them in story order. Regenerate with `npm run cards` (or `npm run cards -- 23-fines` for one). |
| `research/` | `ordinance.md` (law text + fines), `questions.md` (questions and proposals for officials), `sources.md`, and `source-files/` (the ordinance PDFs and the WalkBoston report). |

Commands: `npm run dev` (serve `docs/` at http://localhost:8080; ES modules don't load from file://), `npm test`, `npm run cards`.
Deploy: anything pushed to `main` under `docs/` goes live within a minute or two. `.github/workflows/test.yml` runs `npm test` on every push and pull request.

## Voice and design rules

- **Short sentences and illustrations first.** The owner cut the first web version for having too many words. One headline + one short line per idea; icon tiles over paragraphs. Punchy, plain, direct ("Ice can never happen.", "Blue lights? Move your car.").
- Say **sidewalk** explicitly. Say who the duty falls on. Never imply homes must legally clear ramps (only businesses must).
- Always present this as **PTAC's guide, not an official City page**. Cite ordinance sections in the footer, not inline.
- Design system (same as the cards): navy `#10243A`, panel `#1A3A5F`, snow `#EEF3F7`, orange `#FF8A3D` (on dark), rust `#B93D06` (on light), ice `#A9C4E4`, mute `#47607C`. Fonts: Barlow Condensed 700/800 for headings (uppercase), Barlow for body.
- Crosswalk stripes run **parallel to traffic** (long side along the road). This was corrected once already.
- Translations need native-speaker review before being added to `languages.js`. Somerville publishes its own rules in 9 languages; Spanish, Portuguese, Haitian Creole and Nepali are the priorities.

## Verified facts (from the Code of Ordinances unless noted)

- **Deadline:** snow/ice may not remain more than **6 hours between sunrise and sunset following the conclusion of a weather event** (Sec. 12-8(a)). The clock pauses overnight. Applies to any snowfall, emergency or not. The City may extend.
- **Width/finish:** path at least **36 inches**, cleared to the surface, or sanded where clearing is impractical (12-8(a)).
- **Who:** "a person, including an owner, occupant, tenant, or agent, in charge of land or a building" (12-8(a)). Tenants can be ticketed.
- **Curb ramps:** buildings with only commercial units, or ground-floor commercial units abutting an accessible curb ramp, must clear the ramp with clear, direct access to the crosswalk (12-8(a)(1), Ord. 2025-25, effective **Dec 11, 2025**). For homes it's a City request, not law.
- **Fines (Sec. 1-11):** 1–3 unit homes $100 / $200 / $300; 4+ units and businesses $150 / $300. Same fines for putting snow in the street (12-9). Counted **Oct 1 – May 1**. Unpaid fines can become a lien or block City licenses/permits (1-11(c)). City may clear and lien (12-8(c)).
- **Snow into the street:** banned unless broken up, spread ≤ 3 inches, in daylight, on a day with mean temperature above 40°F (12-9).
- **Downspouts:** buildings may not shed water onto sidewalks (12-2).
- **Space savers:** illegal under 12-18 (no objects in a way without a DPW permit); $100; each day a new offense; City may discard them.
- **Snow emergency (City page / Sec. 1-11):** announced by City Alert and blue lights at 22 intersections; 4 hours to move to the **even** side (winter 2026/27); tow zone, hydrant and 20-ft-of-intersection tickets $100; 13 free City lots; Tufts Dowling Garage free for Wards 6 & 7 (register first); after it ends: 2 h leave lots, 24 h permit rules return, 48 h dig out. Tows: Stephen's Towing 781-395-0808, pickup at Dilboy Stadium, $132 + $35/day.
- **Landlords (105 CMR 410.260):** keep shared exits, stairs, walkways clear; a lease can't shift that. Tenants only for an exit that is theirs alone, if a written agreement says so.
- **Bus stops:** City clears most of its 281 stops after streets (City page). MBTA clears all route 109 stops plus some on 77 (Mass Ave) and 104 (Sullivan Sq) within 24 hours (MBTA page). Snow routes: 85, 93.
- **Deicers (Minnesota Pollution Control Agency, not a City rule):** rock salt to 15°F, magnesium chloride to −10°F, calcium chloride to −20°F, CMA to 20°F, sand never melts. ~12 oz covers 10 sidewalk squares.
- **Report:** 311 / 617-666-3311, 311Somerville app, 311requests@somervillema.gov. Teen shovelers: 617-625-6600 x2321.

## Not yet confirmed (see research/questions.md)

Who clears residential corner ramps; when the City clears and liens (24 h after snow vs after the emergency); whether tickets go to tenants in practice; teen-shoveler 2026/27 prices (cards still show 2024/25: $25, $60 corner); MBTA routes after the bus network redesign; Green Line station access; state-road sidewalks; whether the even-side rule and the 13 lots are unchanged for 2026/27.

Resident feedback (not data): small storms leave the worst ice; the first December storm is when people relearn the rules.

## Related artifacts on claude.ai

- Card canvas (Design): https://claude.ai/artifact/AcoF5JNBV3Eg96bzdTDnZe — `cards/src` is an export of it.
- Questions doc: https://claude.ai/artifact/2oc3c9e1vG2C7EkckRYyr2 — `research/questions.md` is a copy.
- First single-file version of the site: https://claude.ai/artifact/VHq19kkjN4reR43fhd98du
