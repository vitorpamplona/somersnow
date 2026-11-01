# Somerville Snow Guide (somersnow)

Instructions for AI coding agents (Claude Code, Codex, Copilot, Cursor and others) and for people new to the project. `CLAUDE.md` points here.

A public guide to Somerville, MA's sidewalk snow and ice rules, for people who walk, roll or ride the bus. Made by the **Somerville Pedestrian & Transit Advisory Committee (PTAC)**. Audience: new residents first, everyone second. Goal: more people shovel on time, down to the pavement, ramps included, so walking to transit works in winter.

## What's here

| Path | What it is |
|---|---|
| `docs/` | The website. GitHub Pages serves this folder straight from `main` (Settings → Pages → Deploy from a branch → `main`, `/docs`). No build step. |
| `docs/index.html` | All page markup. English text lives here, each piece tagged `data-i18n="section.NN"`. |
| `docs/i18n/en.js` | Every English string: `page` (mirrors the `data-i18n` tags) and `ui` (text scripts write). |
| `docs/i18n/languages.js` | Languages in the switcher. The switcher stays hidden while only English is listed. |
| `docs/i18n/drafts.js` + `es.js`, `pt.js`, `ht.js`, `ne.js` | AI-drafted translations awaiting native-speaker review. Not in the switcher; preview with `?lang=es` (a banner marks them as drafts). Review checklist: `research/translation-review.md`. Add new English keys to these too, or they fall back to English. |
| `docs/js/deadline.js` | Pure sunrise/sunset + 6-daylight-hour deadline math. Covered by `test/deadline.test.js`. |
| `docs/js/shovel.js` | The animated street corner for "Down to the pavement" (steps 1–5). Each step plays one short animation; CSS under "shovel scene" in `style.css`. |
| `docs/js/corner.js` | The street-corner SVG for the "Who clears this?" map. |
| `docs/js/live.js` | Live "storm mode": an orange banner above the hero, shown only while snow is on the way, falling, or just ended (hidden otherwise). Reads the National Weather Service API in the browser (forecast grid BOX 70,102 snowfall, active alerts for zone MAZ014, Logan KBOS observations), refreshed every 15 minutes. Phases: forecast → snowing (estimated deadline if it stops when forecast) → stopped ("Shovel by" from `deadline.js`, countdown, "Add to my calendar" .ics) → deadline passed (311, ice, space savers) for 30 hours. A passing flurry (under 3 snowy reports) doesn't start the clock. Everything is labeled an estimate; the City's snow emergency has no feed, so the banner says how to check. Preview with `?live=forecast`, `?live=snowing`, `?live=stopped` or `?live=passed` (marked "Demo"). Logic in `liveState()`, tested in `test/live.test.js`. Text: `ui.live` in `en.js`. |
| `docs/js/main.js` | Wires the page: steps, who-clears map, calculator (starts at "just now" from Oct 1 to May 1), salt slider, fines, share-this-card links, nav. |
| `cards/src/` | The 34 phone-size (1080×1920) social cards as standalone HTML (the editable source). |
| `docs/cards/` | Rendered PNGs, served by the site with a gallery at `docs/cards.html`. `cards.json` lists them in story order. Regenerate with `npm run cards` (or `npm run cards -- 23-fines` for one). |
| `docs/flyer.html` | One-page printable US Letter flyer (English) with a QR code (`docs/qr.svg`, to https://vitorpamplona.com/somersnow/). Has its own copy of the key facts: update it when a rule or fine changes. |
| `docs/storms/` | Storm replays: one fixed page per snow period since 2016 (`storms/<last day of snow>.html`): every snow of 3 inches or more, plus smaller snows that drew many sidewalk reports, merged with any snow that fell before sidewalk reports died down; the page runs until they did. Index grouped by winter (a winter without one says so). A snowfall merged into a longer period keeps its old address as a small page that forwards there. Written by `scripts/build_pages.py` from the template `scripts/storm_page.html`, with the title, summary, storm cards and all data written into each page; `js/storm.js` + `css/storm.css` only draw and animate. Each replay shows snow at Logan, NWS warnings, the City's snow emergency, the deadline (from `deadline.js`), 311 requests, a ward map, snowfall from volunteer observers inside Somerville next to Logan's, and "Getting around": T entries, MBTA bus trips run, lateness and speed on Somerville routes (2020+), card spending in the county (2020–22), how slow the subway ran (2022+), and Bluebikes vs. a normal week; melt-and-refreeze periods with salting requests; the ward map shows who walks there (Happiness Survey), today's bus routes and every bus stop (the busiest 19 larger); views of the City's snow pages (2020 to May 2023); police snow-emergency tows, parking calls, MBTA alerts and crashes; Fire Department medical calls, wires down, carbon monoxide and crashes (2019–2025). English only. `storm.html?storm=<id>` forwards to the fixed page. |
| `docs/data/` + `scripts/fetch_data.py`, `scripts/storm_extras.py` | `npm run data` (Python standard library, no keys) collects every source into small JSON files and then builds the pages; `npm run pages` rebuilds the pages only. Big downloads are cached in `.cache/` (git-ignored). Re-run each fall. To add what the City announced for a storm (emergency times, notices), add it to `CITY` in `fetch_data.py` with source URLs; the City's online news archive only goes back to 2022. Sources and caveats: `research/data-sources.md`. |
| `docs/llms.txt` | Plain-text summary of the rules for AI assistants that read the live site. Keep it in sync with the facts below. |
| `research/` | `ordinance.md` (law text + fines), `questions.md` (questions and proposals for officials), `sources.md`, and `source-files/` (the ordinance PDFs and the WalkBoston report). |

Commands: `npm run dev` (serve `docs/` at http://localhost:8080; ES modules don't load from file://), `npm test`, `npm run cards`, `npm run data`, `npm run pages`.
Deploy: anything pushed to `main` under `docs/` goes live within a minute or two. `.github/workflows/test.yml` runs `npm test` on every push and pull request.

## Making changes

- **A rule or number changes** (new fine, new even/odd side, new lots): update it everywhere it appears, in this order: the "Verified facts" list below, `docs/i18n/en.js` (and any translations), `docs/index.html`, `docs/flyer.html`, `docs/llms.txt`, the affected cards in `cards/src/` (then `npm run cards -- <card>`), and `research/ordinance.md` if it's law. Search the repo for the old value before you finish.
- **Every fact needs a source.** Law comes from `research/source-files/` or Municode; City practice from somervillema.gov; MBTA facts from mbta.com. If a source is a search snippet, mark it * in `research/sources.md`. Don't add facts from memory. If something is unconfirmed, add it to "Not yet confirmed" and to `research/questions.md`, not to the site.
- **Text:** edit `docs/index.html` and `docs/i18n/en.js` together. Keys in `en.js` must match the `data-i18n` attributes. New visible text gets a new key.
- **Before pushing:** `npm test`, then open `npm run dev` and check the page at phone width (390px) with no sideways scroll.
- **Don't** describe the site as official, put City or MBTA logos on it, or soften the "not an official City page" line.

## Storm replays and data

The guide teaches the rules; `docs/storms/` shows what actually happens in a storm, hour by hour, so PTAC can show residents and officials the pattern (sidewalk complaints peak 1 to 3 days after the snow stops, long after the deadline). Treat it as analysis, not rules: nothing there changes what the guide tells people to do.

**How it fits together**
1. `scripts/fetch_data.py` (`npm run data`) finds every storm since July 2015 with 3 inches or more at Logan (`STORM_MIN`; consecutive days of half an inch or more; until Nov 2026 the rule was a 6-inch day, and ids didn't change), plus smaller snows found through 311 (`complaint_storms()`: outside every snow storm's window, sidewalk reports over 3 days reach 3% of that winter's total and at least 30, after a day of half an inch or more; `kind: '311'` in the data, not labeled on the site) then groups them into snow periods (`snow_periods()`): after a period's last snowfall, sidewalk reports have died down on the first of two days in a row at no more than 1/20 of the peak day so far, or 2 reports; any snow of half an inch or more at Logan that starts before that joins the period (emergency or not). Each period's window runs from 2 days before its first snow to the day after reports died down (capped at 35 days), but never into a neighbor: it starts no earlier than the day the previous period's reports died down and ends before the next period's first snow day; its id is its last day of snow, and the other seed snowfalls' ids are `aliases` (forwarding pages). It then collects hourly data for each window from public sources. Each storm file lists its `snowfalls` (own start, stop and so deadline), `clear` (the day reports died down) and `lasted` (days from the end of the first snowfall to `clear`). `scripts/storm_extras.py` holds the extra collectors. Output: `docs/data/*.json`. Downloads over a few MB are cached in `.cache/` (about 2 GB; delete a file there to refresh it).
2. `scripts/build_pages.py` (`npm run pages`, also run at the end of `npm run data`) writes `docs/storms/<id>.html` and `docs/storms/index.html` from `scripts/storm_page.html`, with the data embedded as JSON and the text (title, intro, description, prev/next, storm cards) already written. Script and CSS URLs carry a content hash (`?v=`) so browsers never mix a new page with an old cached script.
3. `docs/js/storm.js` only draws: the guide's "storm mode" messages in a phone (a sketch of what the guide could say at each hour, not something the City said), the main chart (snow, NWS warnings, 311 by type, markers), "Getting around" lanes (drawn at real pixel width so text stays readable), counters, and the ward map. The guide's messages sit beside the title and intro (above the slider on phones), so the charts get the full width; the panel has a fixed height (the intro's height or 80% of the hours on desktop, a typical hour on phones) and the busiest hours scroll inside it. Dragging the chart or lanes moves the time; nothing on the page may change height while dragging.

**Sources and coverage** (details, numbers and queries: `research/data-sources.md`)

| Source | Where | Covers |
|---|---|---|
| Hourly weather at Logan (snow start/stop from METAR codes; falling snow only, lulls under 6 h are one storm) | Iowa Environmental Mesonet ASOS | all storms |
| Daily snowfall at Logan, winters since 1891 | NOAA via ACIS (`BOSthr`) | all |
| Snowfall inside Somerville | CoCoRaHS volunteers via ACIS | 9 storms, 4 complete ("partial report" otherwise) |
| NWS warnings for zone MAZ014 | IEM VTEC archive | all |
| 311 snow requests (sidewalk, street, emergency questions, space savers) and parking/trash calls | City open data `4pyi-uqq6` | all |
| Snow emergency tows, disabled vehicles (per 8-hour police shift) | City open data `mdb2-mgc7` | 2017 on |
| Crashes (time, street or intersection without house number, what happened, road/weather/light, injuries, pedestrian or cyclist and where they were; shown on hover/tap) | City open data `mtik-28va` | March 2018 on |
| Views of the City's snow pages | City open data `754v-8e35` (top 20 pages a day) | Dec 2020 – May 2023 |
| T gated entries at Somerville stations (30-minute) | MBTA open data, yearly archive | all |
| Bus trips run and minutes late, on the routes that served Somerville at the time | MBTA bus arrival/departure times | Dec 2020 on |
| Bus speed: each bus's time between consecutive timing stops inside Somerville vs. that stretch at the same hour (weekday/weekend) in the 4 weeks before; the stand-in for traffic (no public car counts) | same bus data | Dec 2020 on |
| Card spending, Middlesex County, 7-day average, each day vs. the 4 weeks before (county-wide spending, not City revenue; the City publishes no daily revenue) | Opportunity Insights Economic Tracker (Affinity) | daily 2020 – early 2022 |
| MBTA service alerts on Somerville routes and stations | MBTA alerts archive | 2020 on |
| Somerville Fire Department calls: medical (EMS 321 + medical assist 311) per hour vs. a normal week; ticks for wires down/arcing (440–445), carbon monoxide (424, CO detectors 736/746) and vehicle crashes (322–324), street without house number | FEMA/USFA NFIRS public release, "U.S. Fire Department Responses" on ArcGIS, FDID 17274 (`fire_dept()`; cached in `.cache/nfirs-<year>.json`) | 2019–2025 (no incidents filed Feb 25–28 and Dec 10–15, 2022: those storms show not available) |
| Bluebikes trips from stations inside Somerville | Bluebikes system data | all (no winter trips in 2016–17) |
| Subway: % slower than usual and trains run, Red/Orange/Green Line segments in Somerville (Alewife–Davis–Porter, Sullivan–Assembly–Wellington, Green Line Extension) | MBTA rapid transit travel times (about 1–1.5 GB a year, cached) | Jan 2022 on (Green Line Extension from late 2022) |
| Melt and refreeze (back at or below 32°F within 12 h after 34°F+) and salting requests | Logan hourly temperature; 311 "Salting request" | all |
| Who walked / rode transit in the past week, by ward | Happiness Survey `wmeh-zuz2` (2025, random sample, ~200 per ward) | ward map |
| City snow emergency times and notices | somervillema.gov news, typed into `CITY` in `fetch_data.py` | Feb 2022 (end only), Jan 2026 (start only), Feb 2026 (both) |
| Ward outlines (State Plane, converted); MBTA stops and Fall 2025 weekday boardings; today's bus route shapes | City GIS `ym5n-phxd`; MBTA V3 API (`route_patterns` + shapes) and ridership | — |

**Rules for this data**
- "Normal" for the T, buses and Bluebikes is the same hour on the 4 weeks before the window. Holidays in those weeks distort it (Feb 2026: −86% vs. that average, −89% vs. Feb 9 alone); say "compared with a normal week", not "usual".
- 311 counts complaints, not unshoveled sidewalks. Reports per inch of snow jumped after 2023 (likely easier reporting), so don't present a trend as worse shoveling (question 47).
- When a source doesn't cover a storm, show "not available" with the reason, never a zero.
- Socrata compares dates as text (`'2026-03-01 09:42' < '2026-03-01T00:00'` is true), so always re-check each record's time in Python against the window, as `storm_extras.py` does.
- **Bus routes change** (the 86 stopped in Somerville in 2020–22, not in 2026). Never apply today's route list to old data: `buses()` picks each storm's routes from that month's data (today's routes that ran, plus any route with a timing stop in Somerville), and the map names routes of the time that no longer run there. The CT2 is `747` in the API and ridership files.
- MBTA archive times that end in "Z" (alerts `created_dt`, newer subway `..._datetime` columns) are Boston local time, not UTC; use them as wall-clock time (subway: service date + seconds). IEM/NWS times are real UTC.
- Winters 2022–23 to 2024–25 had no 6-inch day at Logan; with the 3-inch rule they have storms. The index still marks any winter without a storm.
- Fixed windows hid the long tails: reports take a median of about 7 days after the snow to die down, more than 2 weeks when snow keeps falling (Feb 2025: 23 days; Jan 25 – Feb 10, 2026: 20). That's why replays are snow periods with a window that ends when reports die down. The "normal week" stays the 4 weeks before the period starts, so it says less toward the end of a long period. The page-wide deadline (map text, emergency end) is the period's biggest snowfall's; each snowfall still gets its own lines and phone messages.
- Storms found through 311 were picked by their complaints, so they never count toward "reports peak 1 to 3 days after" (circular); the index lede counts snow-picked storms only. The 311 cutoff is a share of the winter because sidewalk reports per winter went from about 220–760 (through 2023–24) to 2,019 and 3,182.
- A storm's start and stop (and so its deadline and title) span from the first to the last run of 3+ snowy hours at Logan that overlaps its snow days; a passing flurry doesn't count, as in live mode. (Before Nov 2026 it took the longest run, which ended Jan 2021 and Feb 2025 a day early.) Titles typed into `CITY` win over computed ones.
- Holidays (New Year, MLK Day, Presidents' Day, Patriots' Day, Thanksgiving, Christmas) empty the T on their own: the lanes name them on the day axis, the counters say so, and page summaries skip them and look for the biggest drop only from the first snow to 3 days after it stops. The weeks around Christmas still distort "a normal week".
- Bluebikes: a month the system hasn't published is left out of the normal week (Nov 2025 was missing), and a storm whose normal week has under 100 trips from Somerville (winters 2015–17) shows "not available", not zero.
- Nothing on a replay may change height while dragging: the phone, the map's side text and the counters reserve their tallest version (`lockPhoneHeight`, `lockLateHeight`).
- Fire Department (NFIRS) alarm times are Boston wall-clock time (calls bottom out at 3–5 a.m.). Medical calls say nothing about why help was needed: never call them falls. The type is what the department found on arrival.
- MBTA station entries are counted by service day, which runs past midnight: periods before 3 a.m. belong to the next calendar day (`t_entries()` shifts them). Bus times carry their own date offset (`1900-01-02` = after midnight). Police "Last Half (Midnight–8 AM)" shifts are dated by calendar day (checked against the Feb 2026 emergency).
- Crash locations are trimmed to the street or intersection (no house number): the City publishes exact addresses, but a single crash with an injury shouldn't point at a home.
- The deadline comes from `deadline.js`. Two City notices let us check it: Feb 26, 2022 (City 12:30 p.m., calculator 12:24) and Feb 24, 2026 (City "1 p.m.", calculator 12:28).
- New City facts found in data work go through the "Making changes" rules above (a source, then the facts list); e.g. the even-side rule for 2026/27 came from a City notice.

**Checked on the City portal (data.somervillema.gov) and left out:** traffic citations (moving violations only; no parking or snow tickets), permits and licenses (dumpsters, curb cuts), the Winter Warming Center survey (about the shelter), the ADA survey (`sidewalks` column has no codebook), crime reports and the other surveys. **Not public:** sidewalk tickets issued, clean-and-lien jobs, plow GPS, a list of snow emergencies, snow spending, the 22 blue-light locations, curb-ramp inventory (questions 47–54).

**Asked, not public:** hourly car counts on Somerville streets (MassDOT's count site refused this environment), daily City parking/meter revenue, parking tickets (questions 55–57).

**Ideas not built yet:** Boston 311 "Unshoveled Sidewalk" for comparison; more 311 types (fallen trees, potholes); Census ACS by ward (free key); pavement temperature from state road sensors (free token).

## History

- Site: guide sections, cards, research, then (Oct–Nov 2026) the animated "Down to the pavement" corner, the redrawn "Who clears this?" map, shorter phone layout, "What's happening?" buttons, share-this-card links, printable flyer, calculator starting "just now", draft translations, and the "Replay a past storm" section.
- Live storm mode on the main guide (Nov 2026).
- Storm replays: one storm (Feb 2026), then all 15 big storms (a 6-inch day) with fixed pages, then "Getting around" (T, Bluebikes, tows, parking calls, alerts, crashes), then buses, Somerville snowfall and City page views, then crash details, subway speed, melt-and-refreeze and the ward survey, then bus routes on the map, route changes over time, MBTA local-time fixes, and smaller storms (3 inches or more, plus 12 small snows found through 311), then bus speed, card spending and Fire Department calls, then snow periods (54 snowfalls in 44 periods, windows until reports die down). The git log has the details.

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
- **Snow emergency (City page / Sec. 1-11):** announced by City Alert and blue lights at 22 intersections; 4 hours to move to the **even** side (winter 2026/27: the City's rule is that the side matches the year winter begins, odd in 2025/26 and even in 2026/27, per its Feb 21, 2026 snow emergency notice); tow zone, hydrant and 20-ft-of-intersection tickets $100; 13 free City lots; Tufts Dowling Garage free for Wards 6 & 7 (register first); after it ends: 2 h leave lots, 24 h permit rules return, 48 h dig out. Tows: Stephen's Towing 781-395-0808, pickup at Dilboy Stadium, $132 + $35/day.
- **Landlords (105 CMR 410.260):** keep shared exits, stairs, walkways clear; a lease can't shift that. Tenants only for an exit that is theirs alone, if a written agreement says so.
- **Bus stops:** City clears most of its 281 stops after streets (City page). MBTA clears all route 109 stops plus some on 77 (Mass Ave) and 104 (Sullivan Sq) within 24 hours (MBTA page). Snow routes: 85, 93.
- **Deicers (Minnesota Pollution Control Agency, not a City rule):** rock salt to 15°F, magnesium chloride to −10°F, calcium chloride to −20°F, CMA to 20°F, sand never melts. ~12 oz covers 10 sidewalk squares.
- **Report:** 311 / 617-666-3311, 311Somerville app, 311requests@somervillema.gov. Teen shovelers: 617-625-6600 x2321.

## Not yet confirmed (see research/questions.md)

Who clears residential corner ramps; when the City clears and liens (24 h after snow vs after the emergency); whether tickets go to tenants in practice; teen-shoveler 2026/27 prices (cards still show 2024/25: $25, $60 corner); MBTA routes after the bus network redesign; Green Line station access; state-road sidewalks; whether the 13 lots are unchanged for 2026/27; the teen-shoveler extension (the City's Feb 2026 notices say Council on Aging x2300, this file says x2321).

Resident feedback (not data): small storms leave the worst ice; the first December storm is when people relearn the rules.

## Related artifacts on claude.ai

- Card canvas (Design): https://claude.ai/artifact/AcoF5JNBV3Eg96bzdTDnZe — `cards/src` is an export of it.
- Questions doc: https://claude.ai/artifact/2oc3c9e1vG2C7EkckRYyr2 — `research/questions.md` is a copy.
- First single-file version of the site: https://claude.ai/artifact/VHq19kkjN4reR43fhd98du
