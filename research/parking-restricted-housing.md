# Housing without resident parking permits

Somerville's new housing near the T can't get on-street resident permits. How much housing is that, and how fast is it growing? Researched Nov 11, 2026, from public City records. On the site as "New neighbors near the T" in [Riding transit in Somerville](https://somerwalks.org/transit-trends.html): tiles with these homes from the buildings occupied since 2025 on; the ones not built yet are on the housing pipeline map, each marked as on the list in its tooltip (built 2025–26: 132 homes; under construction 740; planned 79), with the T lines, stations and the bus routes through Somerville, built from [`analysis/transit-trends/restricted_housing.csv`](../analysis/transit-trends/restricted_housing.csv) (this table, with permit numbers and coordinates).

## The rule

- **What:** residents of new housing developments in a **Transit Area** (within ½ mile of the MBTA Red, Orange or Green Line, per the City's walkshed map) are not eligible for resident or guest parking permits. "New development" includes entirely new buildings and the redevelopment or modification of existing buildings that adds new units. Properties in the Transit Area zoned **Neighborhood Residence (NR)** are excluded from the restriction.
- **Since:** approved by the Traffic Commission on Dec 12, 2019; applies to properties granted their **first building permit on or after Jan 15, 2020**.
- **Waivers:** persons with disabilities, occupants of affordable dwelling units, and residents with extenuating circumstances can apply.
- **Sources:** [Parking Department page](https://www.somervillema.gov/departments/parking-department) ("Addresses with Resident Permit Restrictions"); [Schedule W, list of restricted addresses](https://s3.amazonaws.com/somervillema-live/s3fs-public/schedule-w-list-of-restricted-addresses.pdf) ("As of 5/5/26. List of addresses subject to change."); [FAQ](https://s3.amazonaws.com/somervillema-live/s3fs-public/parking-permit-restrictions-transit-areas-faq.pdf); [Transit Area map](https://s3.amazonaws.com/somervillema-live/s3fs-public/walkshed-map-a.pdf); [waiver application](https://s3.amazonaws.com/somervillema-live/s3fs-public/waiver-application-resident-permit-restrictions.pdf).

## Units on the list

Schedule W lists 37 address entries and no unit counts. Units and dates below come from the City's [Applications for Permits and Licenses](https://data.somervillema.gov/resource/nneb-s3f7.json) (Citizenserve, 2014 on): the building permit's project description gives the units; the Certificate of Occupancy (CO) gives when it was finished. "Permit" is the first building permit issued (often a foundation-only permit). Counts are what the permits say; a final building can differ.

| Address (Schedule W) | Units | First permit issued | Occupied (CO issued) | Status, Nov 2026 |
|---|---|---|---|---|
| 20–50 Prospect St (Union Square D2) | 450 | 2021-01 (enabling work), 2021-04 | 2023-10 | Built |
| 344–346 Somerville Ave | 94 | 2021-03 | 2023-05 | Built |
| 3–5 Hawkins St | 59 | 2021-11 | 2024-09 | Built |
| 31 Tufts St | 16 | 2022-05 | 2024-06 (temporary) | Built |
| 26–28 South St | 19 | 2022-07 | 2025-01 | Built |
| 379 Somerville Ave | 10 | 2021-12 | 2025-04 | Built |
| 115 Thurston St | 9 | 2022-07 | 2025-04 (first units; final 2026-10) | Built |
| 394 McGrath Hwy | 15 | 2024-04 | 2025-08 | Built |
| 24–28 Mount Pleasant St | 32 | 2022-11 | 2025-12 | Built |
| 872 Broadway | 12 | 2022-04 | 2026-02 | Built |
| 595 Broadway | 7 | 2024-04 | 2026-04 | Built |
| 13 Warwick St | 28 | 2023-02 | 2026-09 | Built |
| 13–17 Allen St | 40 | 2024-10 | applied 2026-04 | Under construction |
| 82–86 Prospect St | 29 | 2024-08 | applied 2026-09 | Under construction |
| 19–27 Allen St | 69 | 2024-02 (foundation) | | Under construction |
| 2–4 Alpine St | 26 | 2024-04 | | Under construction |
| 59–61 Bow St | 13 | 2024-07 | | Under construction |
| 299 Broadway (Building B) | 204 | 2026-01 | | Under construction |
| 15 Temple St (Building A) | 115 | 2026-01 | | Under construction |
| 366 Broadway | 50 | 2025-12 | | Under construction |
| 24 Webster Ave | 42 | 2026-03 (foundation) | | Under construction |
| 118 Prospect St | 29 | 2021-12 | | Under construction |
| 121 Prospect St | 32 | 2022-07 | | Under construction |
| 108–110 Prospect St | 29 | 2025-11 | | Under construction |
| 0–14 White Street Pl | 25 | 2024-12 | | Under construction |
| 371 Highland Ave | 22 | 2026-04 (foundation) | | Under construction |
| 60–64 Medford St | 9 (6 + 3) | 2026-09 (foundation) | | Under construction |
| 53 Chester St | 3 | 2026-03 | | Under construction |
| 181 Pearl St | 3 | 2025-12 | | Under construction |
| 37 Allen St | 24 | — | | Planned (applied 2023, 2025, 2026) |
| 73 Summer St | 27 | — | | Planned (applied 2022, 2025) |
| 199 Elm St | 10 | — | | Planned (applied 2025) |
| 171 Cedar St | 6 (2021 application) or 15 (2026 application) | 2024-06 (foundation for the 6-unit plan) | | Planned |
| 10 Oak St | 3 | — | | Planned (NR district per the 2025–26 applications, yet on the list) |
| 14 Sewall St, 30 Sewall St, 11 Temple St | ? | no building permit found | | Unknown |

**Totals:** built and occupied **751 units** (544 occupied in 2023, 75 in 2024, 85 in 2025, 47 in 2026 so far); under construction **740**; planned about **79**; three entries unknown. About 1,570 units in all once built.

For scale: the Census survey counts about 36,000–40,000 housing units in Somerville in 2021–2025 (ACS 1-year B25001, ± about 2,000), so built restricted housing is about 2% of the city's homes, and about 4% with what's under construction.

## People, roughly

At 1.97 people per home (the average Somerville renter household, ACS 1-year 2025 B25010, ± 0.12): about 1,480 people in the built homes, 1,460 more under construction, 160 planned. An estimate: new buildings have many studios and one-bedrooms, so it may be high. 59% of the homes are within 400 m (a 5-minute walk, straight line) of a Red, Orange or Green Line station; half are within 364 m.

## Accessory dwelling units (ADUs)

- The permit applications have no ADU type; searching project descriptions for "ADU", "accessory dwelling" or "accessory apartment" (whole words) finds **85 applications**: 1 in 2015, then 2 (2021), 1 (2022), 2 (2023), 3 (2024), **32 (2025)** and **44 (2026 to date)**. Of them, 56 are building permits at 43 addresses; 22 addresses have an issued permit (first issued: 1 in 2015, 2 in 2024, 4 in 2025, 15 in 2026). Mostly garage conversions and detached backyard cottages.
- A floor, not a count: an ADU permit whose description doesn't say so is missed.
- Whether an ADU in a Transit Area counts as "new development that adds new units" under the parking restriction isn't stated by the City; none is on Schedule W (question 65).

## Permits over time

- The City's [parking permits dataset](https://data.somervillema.gov/resource/xavb-4s9w.json) (one row per permit, with addresses: publish totals only) runs Jan 2017 – Nov 2020 and was frozen in Dec 2020. Resident permits (types A1 "Residential" and A2 "65+") a year: 33,330 (2017), 32,530 (2018), 32,616 (2019), 23,913 (2020, Jan–Nov). Visitor (G1): 16,717, 15,416, 14,812, 9,180.
- The City's 2022 Parking & Curb Use Study reports 52,243 "resident permits" for 19,761 permit spaces; that is far above the yearly counts above and likely counts something else (visitor permits too, or two years). Don't put them on one chart until the City explains it.
- Nothing public after 2020 (questions 56–57).

## The pace of new housing

- **Census Building Permits Survey** (place file `ne{year}a.txt`, Somerville FIPS place 62535): new units authorized 604 (2015), 182, 214, 170, 146 (2019), 103 (2020), 140 (2021), 115 (2022), 101 (2023), 83 (2024), 90 (2025). **Unreliable for Somerville since 2020:** its "months reported" field is 4 (2020), 0 (2021), 0 (2022), 1 (2024) and 0 (2025), so those years are Census estimates, and they miss real projects (Union Square D2's 450 units appear nowhere).
- **MAPC MassBuilds** ([API](https://api.massbuilds.com/developments), updated to Jul 2025): 326 Somerville developments; completed housing units by year 2020–2024: 115, 526, 329, 490, 160. Crowd-maintained: it has Union Square D2 but none of the small projects above.
- **MassGIS property tax parcels** (statewide service, Somerville `TOWN_ID` 274, 19,065 parcels): Somerville leaves `UNITS` empty on nearly every parcel, so it can't count units.
- **Better:** the City's permit applications (above) give units and occupancy dates per project. Done for the whole city in the housing pipeline on the site ("What's coming", [Riding transit in Somerville](https://somerwalks.org/transit-trends.html)): every "New Construction" building permit since 2021, Nov 2026: 1,077 homes under construction (67 projects), 317 in permitting (26), plus 2,158 planned and 1,559 long range from MassBuilds and the City's records below (less what the permits already have), and 61 buildable vacant lots (17 acres). Big public sites with no permit yet are added by hand ([`pipeline_sites.csv`](../analysis/transit-trends/pipeline_sites.csv)): 90 Washington St (the Somerville Redevelopment Authority chose Wood Partners on Jul 13, 2026; 418 rental homes, 84 affordable, in its updated proposal), 297 Medford St (Just A Start and the Somerville Community Land Trust, about 50 affordable homes) and the City-owned Homans lot at Gilman Square (no housing plan yet); and Union Square's remaining D-blocks from the City's 2017 master plan permit (D3.2, D4.3, D5.3, D7: 521 to 611 homes in its estimates, at most 548 more under the 998 cap with D2's 450 built), replacing MassBuilds' D-block entries, which add up to far more than the cap. Method in [`analysis/transit-trends/AGENTS.md`](../analysis/transit-trends/AGENTS.md).

## Open questions for the City (questions 62–65 in [`questions.md`](questions.md))

- How many resident and visitor permits were issued each year since 2020, and what the 2022 study's 52,243 counts.
- Whether Schedule W is complete (every property with a first building permit since Jan 15, 2020 in a Transit Area outside NR zoning), and what 14 and 30 Sewall St and 11 Temple St are.
- How many waivers have been granted.
- Whether ADUs in a Transit Area are restricted, and how many ADUs the City has permitted.
