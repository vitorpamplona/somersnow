# Mobility data for Somerville: a catalog

Public data about how people move in Somerville: buses and bus stops, the T, walking, biking, cars, parking and safety. What each source holds, how fine-grained it is, the years it covers, whether we use it, and how to get it. Every source below was opened or queried on **Nov 11, 2026** unless the row says otherwise (2026-10/11 for sources already in use). For the storm replays' sources in depth (queries, counts, caveats), see [`data-sources.md`](data-sources.md) and [`scripts/AGENTS.md`](../scripts/AGENTS.md).

## Read first: Somerville since 2015

The city changed a lot after 2014, so **data from before 2015 is context only**: never present it as how Somerville moves today, and say the year next to any number. Mind these breaks in any series:

| When | What changed |
|---|---|
| Sep 2, 2014 | Assembly station opens on the Orange Line ([City news](https://somervillema.gov/news/orange-line-assembly-station-opens-92)). |
| Mar 2020 – 2021 | The pandemic: transit, driving and rideshare collapse, then partly recover; working from home stays high. ACS 5-year windows that include 2020–21 mix both worlds. |
| Mar 21 and Dec 12, 2022 | The Green Line Extension opens: the Union Square branch, then the Medford branch with East Somerville, Gilman, Magoun and Ball Squares ([CLF](https://www.clf.org/newsroom/green-line-extension-to-medford-finally-opens/), [MBTA](https://www.mbta.com/projects/green-line-extension-glx)). Any transit data before then is a different network. |
| Dec 2024 – 2029 | The MBTA's bus network redesign changes Somerville routes in phases (route 86 in Dec 2024; CT2, 85, 87 and 101 in April 2026; more quarterly; [MBTA](https://www.mbta.com/projects/bus-network-redesign/next-5-years-bus-service-changes)). Never apply today's route list to old data. |
| Jul 2026 | New residential permit and meter fees (City news, May 21, 2026); the Parking Department page still shows the old ones. |

**Status** in the tables: **In use** (on somerwalks.org now), **Open** (public download or API, not used yet), **PDF** (numbers only in a report), **Snapshot** (one point in time), **Key** (needs a free key), **Blocked** (refused automated access), **Restricted / paid**, **Not public**.

## Buses and bus stops

| Source | Publisher, link | What it holds | Where, how fine | Years | Status |
|---|---|---|---|---|---|
| Bus ridership by trip, season, route and stop | MBTA, [ArcGIS item `8daf4a33…`](https://mbta-massdot.opendata.arcgis.com/datasets/8daf4a33925a4df59183f860826d29ee) | Average boardings and alightings per scheduled trip and stop | Stop × trip; weekday, Saturday, Sunday | Fall 2016 – Fall 2025, plus Spring 2024 | **In use** (Fall 2025: bus trips, pulse, planner; every fall: transit over time) |
| Archived schedules (GTFS) | MBTA, [archived feeds](https://cdn.mbta.com/archive/archived_feeds.txt) | Stops, routes, shapes, every scheduled trip | Stop, trip | Every feed since Apr 2009 | **In use** |
| Bus arrival and departure times | MBTA, yearly ArcGIS collections (`BUS_ZIPS` in `scripts/storm_extras.py`) | Actual times at timing stops | Timing stop, trip | 2020 – 2026 | **In use** (replays: trips run, lateness, speed). No published on-time table: compute it from these. |
| Comfort (crowding) metric | MBTA, [item `f669fc7a…`](https://mbta-massdot.opendata.arcgis.com/datasets/f669fc7a9b1c49b292532b1b7b936e97) | Share of passenger-minutes in crowded conditions | Route, day type | Fall 2019 – Fall 2025 | Open |
| Bus network redesign: active network | MBTA, [item `1e1c98ac…`](https://www.arcgis.com/home/item.html?id=1e1c98ac062c442ca30ae5fa8d371105); dates on [mbta.com](https://www.mbta.com/projects/bus-network-redesign/next-5-years-bus-service-changes) | 261 route patterns of the redesigned network (no dates in the layer); draft layers May and Nov 2022 | Route pattern | Plan 2018–2029 | Open |
| Bus stop accessibility and amenities (PATI) | MBTA, [item `24a97982…`](https://www.arcgis.com/home/item.html?id=24a97982b39f4febb504c9e6cb55879b) | ADA status and priority; benches, bins, bike racks, narrowed paths | Stop | ADA Jan 2024; amenities 2017 survey | **In use** |
| Bus stop details mapped by volunteers | OpenStreetMap (ODbL) | Shelter, bench, bin, lit, tactile paving, live sign, each with the year it was set | Stop | Continuous | **In use** |
| Bus stops (state layer) | MassGIS | 259 stops in Somerville, no amenity fields | Stop | Current | Open (nothing new) |
| Prediction accuracy | MBTA, [item `155ab68d…`](https://mbta-massdot.opendata.arcgis.com/datasets/155ab68df00145cabddfb90377201b0e) | Weekly accuracy of arrival predictions | Bus: systemwide only | Aug 2020 – now | Open (low value) |
| Shelters, real-time signs | — | Which stops have them, who owns and clears them | — | — | **Not public** (questions 58–60). Cambridge publishes its shelters; the City's 2026 Safe Streets report names 4 new and 3 replaced shelters. |

## Rapid transit

| Source | Publisher, link | What it holds | Where, how fine | Years | Status |
|---|---|---|---|---|---|
| Gated station entries | MBTA (`GSE_ZIP` in `scripts/storm_extras.py`) | Fare-gate entries per 30 minutes | Station | 2014 – now | **In use** (replays) |
| Rapid transit travel times | MBTA, yearly collections (`RT_ZIPS`) | Each train's time between stations | Segment, trip | 2021 – now | **In use** (replays: how slow the subway ran) |
| Rail ridership by hour, line and stop | MBTA, [Fall 2025 `6494749a…`](https://mbta-massdot.opendata.arcgis.com/datasets/6494749a29c648018820d0e49636205c), Fall 2024 `8f20b4e8…`; Fall 2017–19 in `9fea7862…` | Average boardings, alightings and load by hour | Station × hour, day type | Fall 2017–19, Fall 2024, Fall 2025 | **In use** (transit over time: weekday boardings at Somerville's stations, Porter and Sullivan; Fall 2017–19, 2023–25; the Fall 2023 file is by time period). Green Line Extension stops are split across the B, C, D and E route ids: sum them. 2017–19 is before the extension. |
| Monthly ridership by mode and line | MBTA (NTD reporting) | Monthly riders | Line, mode | Jul 2018 – Sep 2026 | Open (not by stop) |
| Service alerts archive | MBTA (`ALERT_ZIPS`) | Every alert: delays, detours, elevators | Route, stop | 2020 – now | **In use** (replays) |
| Customer satisfaction | MBTA, item `a15bbd44…` | Monthly systemwide survey | Systemwide | Feb 2016 – now | Open (low value) |
| TransitMatters dashboard API | TransitMatters (third party) | Travel times, headways from MBTA data | Segment | 2016 – now | Open (repeats MBTA data) |

## Walking, biking, scooters

| Source | Publisher, link | What it holds | Where, how fine | Years | Status |
|---|---|---|---|---|---|
| Bicycle and pedestrian counts | City, [`qu9x-4xq5`](https://data.somervillema.gov/resource/qu9x-4xq5.json) | Volunteer screen-line counts, one AM and one PM hour each fall, bikes and pedestrians | 42 locations (36 until 2015) | 2010 – 2025 | Open. 2010–14 context only. Totals: 17,491 (2020), 34,539 (2025). |
| Bluebikes trips | Bluebikes, [system data](https://s3.amazonaws.com/hubway-data/) | Every trip: start and end station, times | Station, trip | Monthly files from Jan 2015 (older Hubway years in yearly files); no Somerville winter trips 2016–17 | **In use** (replays; transit over time: trips a weekday from Somerville docks, each fall) |
| Bluebikes stations (GBFS) | Lyft, [station_information.json](https://gbfs.lyft.com/gbfs/1.1/bos/en/station_information.json) | Station list, capacity, location | Station | Live | Open: 40 stations in region 9 (Somerville) plus some with no region |
| Bike network by year | MassDOT, [BikeInventoryYearEndFiles](https://gis.massdot.state.ma.us/arcgis/rest/services/Multimodal/BikeInventoryYearEndFiles/FeatureServer) (layers 0–5) | Bike lanes, separated lanes, shared-use paths | Segment (`City=274`) | 2020 – 2025 | Open. Somerville, 2020 → 2025: bike lane 13.9 → 10.9, separated 2.5 → 10.9, shared-use path 5.3 → 7.1 (units likely miles: check before publishing). |
| Sidewalk condition inventory | City, Safe Routes to School map: [SRTS_online_map2, layer 4](https://services7.arcgis.com/Tco18eJkayyK2DZU/arcgis/rest/services/SRTS_online_map2/FeatureServer/4) | 3,021 sidewalk segments: width, slope, material, curb reveal, damaged area, last rebuilt (`Constr_Dat`), Sidewalk Condition Index (`F2016_SCI`, 0–100; mean 67.1), 102 marked accessible (`AAB_COMP`), the City's network priority (`NPR`) | Sidewalk segment (polygon) | Inventory from the [2013 Pedestrian Accessibility Study](https://somervillema.gov/sites/default/files/2013-pedestrian-accessibility-study.pdf); inspected up to Dec 2016; scores as of 2016 | Open, **old** (2013–16): sidewalks rebuilt since aren't in it. The City keeps a current version with a consultant ("annual sidewalk condition surveys", [FY2024 program memo](https://s3.amazonaws.com/somervillema-live/s3fs-public/FY2024%20Pavement%20Management%20Program%20Detail%20Memo_0.pdf)); not published. |
| Safe Routes to School layers | City, [SRTS_online_map2](https://services7.arcgis.com/Tco18eJkayyK2DZU/arcgis/rest/services/SRTS_online_map2/FeatureServer) | 1,623 crosswalks (status 2020–23), 88 signals with crash sums, 44 crossing guards, 36 school entrances, 20 mph safety zones | Crossing, point | 2020 – 2025 | Open |
| Traffic calming installed | City (same ArcGIS org) | Speed humps, raised crossings, curb extensions | Point, year | 2020 – 2025, plus planned | Open: 14, 37, 59, 56, 105, 72 a year |
| Safe Streets Ordinance annual reports | City, [2026 report](https://s3.amazonaws.com/somervillema-live/s3fs-public/somerville-safe-streets-ordinance-2026-annual-report.pdf) (2025 also) | Miles of separated bike lanes, sidewalks and curb ramps built; bus stop and shelter work | Citywide, project | 2024, 2025 | PDF |
| Sidewalk widths | MassDOT Road Inventory | Sidewalk width per road segment | Segment | Yearly | Open (see `data-sources.md` §4) |
| Scooter trips | MAPC (Lime, 2019) | Trips | — | 2019 | **Restricted** (DataCommon token not authorized) |
| Staff MBTA pass pilot | City, `qsv6-v7hu` | Card taps by mode and time, with survey answers | Program | Spring 2023 | Open (narrow) |

## Cars and traffic

| Source | Publisher, link | What it holds | Where, how fine | Years | Status |
|---|---|---|---|---|---|
| Traffic volumes (AADT) by road segment | MassDOT, [TrafficInventoryYearEnd](https://gis.massdot.state.ma.us/arcgis/rest/services/Roads/TrafficInventoryYearEnd/FeatureServer) (layer 1 = 2024, 0 = 2023; Road Inventory 2014–2025 in `RoadInventoryYearEndFiles`) | Average daily traffic, how it was derived, truck share, lanes | Segment (`City=274`: 2,731) | Yearly | Open, **mostly estimates**: by length 68 mi modeled, 33 mi grown from 2021 counts, 0.16 mi counted in 2024. Label as estimates. |
| Vehicle miles traveled | MassDOT, `Roads/VMT` layers 2–12 | AADT × length per segment | Segment | 2015 – 2025 (no 2018) | Open (estimate). Daily VMT on Somerville roads incl. I-93: 770,573 (2015), 873,070 (2019), 610,279 (2020), 872,941 (2025). |
| Traffic count stations (TCDS) | MassDOT, [ms2soft TCDS](https://mhd.public.ms2soft.com/tcds/tsearch.asp?loc=Mhd&mod=TCDS); station points in `Roads/TrafficCountLocations` | Hourly counts at count stations | Station, hour | Varies | **Blocked** (HTTP 403 to automated access; question 55). Stations in Somerville: 8000 Prospect St, 8001 Broadway, 8081 I-93, 8089 Route 28, I-93 continuous 809801/809802/809901. Counts by hand from the website. |
| City traffic counts | City: [traffic calming assessments](https://www.somervillema.gov/departments/ospcd/transportation-and-infrastructure/traffic-calming) (PDF, 2023–26), mobility KPI PDFs (2020–25) | Street counts and speeds (e.g. Ashland St 2026: 174 vehicles a weekday, 85th percentile 20 mph); a permanent Davis Square camera counter | Street | 2020 – 2026 | **PDF**; the City's count database isn't published |
| Vehicles registered | MassDOT Vehicle Census, ArcGIS CSVs: [by municipality, quarterly](https://www.arcgis.com/sharing/rest/content/items/a07d1c0d09e546acb24a1b757c0fd7a9/data), [yearly](https://www.arcgis.com/sharing/rest/content/items/0e7873d506d547d88b555545e3627ca8/data), [by block group](https://www.arcgis.com/sharing/rest/content/items/4bf69d191aaf4be68d024819366256a4/data) ([yearly](https://www.arcgis.com/sharing/rest/content/items/68c6746085b8474789211df9427055fa/data)), ZIP versions | Vehicles by use, fuel, type, age; daily or annual miles driven | Municipality, block group, ZIP | Quarterly 2020-01 – 2026-10; yearly 2020–2025 | Open. Somerville passenger vehicles 39,214 (Jan 2020) → 38,645 (Oct 2026); miles a day per vehicle 22.0 → 24.3. Vehicles registered here, not traffic here. Block-group file has out-of-state GEOIDs: filter. |
| Vehicle Census 2009–2014 | MAPC | Same idea, older | Grid, municipality | 2009 – 2014 | Context only; page says "coming soon"; downloads reportedly need contact details (search snippet, not checked) |
| Rideshare (Uber, Lyft) trips | MA DPU, [2025 report](https://www.mass.gov/info-details/2025-rideshare-data-report), [CSV](https://www.mass.gov/files/csv/2026-05/yoy-2025-v2.csv) (+ origin–destination XLSX) | Trips starting in each municipality | Municipality, year | 2017 – 2025 | Open. Somerville: 2.73M (2017), 3.46M (2019), 1.16M (2020), 2.55M (2025). |
| Traffic citations | City, [`3mqx-eye9`](https://data.somervillema.gov/resource/3mqx-eye9.json) | Moving violations: charge, location, ward, warning flag | Point, ward | 2017 – Oct 2026 (74,286) | Open. Enforcement, not behavior; no parking tickets. |
| Waze for Cities, StreetLight, Replica, INRIX | Commercial | Traffic, speeds, trips | — | — | **Restricted / paid** (not opened) |

## Parking

| Source | Publisher, link | What it holds | Where, how fine | Years | Status |
|---|---|---|---|---|---|
| Parking permits issued | City, [`xavb-4s9w`](https://data.somervillema.gov/resource/xavb-4s9w.json) | One row per permit: type, issued/effective/expiry dates, address, unit, ZIP | Address (no ward or zone column) | Jan 2017 – Nov 2020 (288,530; frozen Dec 2020) | Open. Residential (A1) a year: 29,446 (2017), 28,611, 28,886, 20,563 (2020, Jan–Nov). **Rows have house number and unit: publish only totals by type, ZIP or street.** Group by `type_code` (some codes have two names). |
| Parking calls to 311 | City, [`4pyi-uqq6`](https://data.somervillema.gov/resource/4pyi-uqq6.json) | Permit questions (77,019), temporary no-parking signs (47,247), illegal parking (34,744), ticket appeals (15,009), booted/towed (2,237), meter problems (894)… | Address, time | Jul 2015 – now | **In use** (replays: three parking types); the rest open |
| Snow emergency tows | City, [`mdb2-mgc7`](https://data.somervillema.gov/resource/mdb2-mgc7.json) | Tows and disabled vehicles per police shift | Citywide, shift | 2017 – now | **In use** (replays) |
| Parking & Curb Use Study: Parking Profile | City / Nelson\Nygaard, [PDF (Feb 2022)](https://s3.amazonaws.com/somervillema-live/s3fs-public/2024-11/2022%20February%20COS%20Parking%20Profile%20and%20Use%20Assessment%20NELSON%20NYGARD%20%281%29.pdf); [project page](https://voice.somervillema.gov/parking-study) | ~24,000–25,000 on-street spaces (every curb inventoried 2021–22); 52,243 resident permits for 19,761 permit spaces (2.47 a space); resident spaces 67% full at the overnight peak; 9 public lots (370 spaces) | 6 subareas plus Assembly, Inner Belt, Brickbottom | 2021 – 2022 | **PDF, snapshot**; the curb inventory and counts aren't published as data. The Final Report link didn't download. |
| Parking meters | City, [shapefile `jich-f4v9`](https://data.somervillema.gov/api/file_data/e8f99451-625a-4413-bfdd-383853d4daba?filename=ParkingMeters.zip) | 892 meter poles: id, street, status | Point | Surveyed June 2016 | Open, **old snapshot** (kiosks have replaced many meters since) |
| Tickets and meter revenue, yearly | City budget books ([FY18](https://www.somervillema.gov/sites/default/files/fy18-budget.pdf), FY19, FY20; [index](https://www.somervillema.gov/budget)) | Violations issued, meter revenue, violation revenue | Citywide, fiscal year | FY15 – FY18 actuals | **PDF**. Violations: 270,672 / 274,823 / 273,918 / 250,396; meter revenue $1.66M → $2.13M; violation revenue $5.46M → $5.70M (FY15 → FY18). The definition changed in FY20; FY21 on are on ClearGov (didn't render). Partly answers questions 56–57. |
| Accessible parking spaces | City, [ArcGIS `Parking_Spaces`](https://services7.arcgis.com/Tco18eJkayyK2DZU/arcgis/rest/services/Parking_Spaces/FeatureServer/0) | 162 spaces, on- or off-street | Point | Current (edited 2026-06) | Open |
| EV chargers | City, ArcGIS `Existing_Chargers` | 12 public stations | Point | Dec 2024 | Open (latitude field broken) |
| Parking zones and utilization, 2017 | ArcGIS account "u3agis" (not the City) | Block-face utilization High/Med/Low (65 segments), private lots | Block face | 2017 | Open, unclear origin; likely Union Square planning |
| Perfect Fit Parking | MAPC, [CSV](https://datacommon.mapc.org/api/export?token=datacommon&database=ds&schema=tabular&table=trans_perfect_fit_parking&format=csv) | Overnight counts at residential buildings | 5 sites in Somerville | ~2015 – 2016 | Context only (latitude and longitude columns swapped) |
| Parking Department page | City, [somervillema.gov](https://www.somervillema.gov/departments/parking-department) | 8 permit renewal zones, fees, meter rate, tow fee, permit-restricted addresses | — | Current (fees not yet updated for July 2026) | Reference |
| Daily meter or ParkMobile revenue; parking tickets by day; permits by zone after 2020; curb inventory data | — | — | — | — | **Not public** (questions 56–57) |

## Safety

| Source | Publisher, link | What it holds | Where, how fine | Years | Status |
|---|---|---|---|---|---|
| Crashes (City) | City, [`mtik-28va`](https://data.somervillema.gov/resource/mtik-28va.json) | Time, place, what happened, injuries, pedestrian or cyclist | Point (we trim to street) | Mar 2018 – now | **In use** (replays) |
| Crashes, older (City) | City, `ezmv-8wys` | 4,059 crash reports with bike/ped/injury flags | Point | 2010 – 2018 | Open; before 2015 context only |
| Crashes (state) | MassDOT, `MASSDOT_ODP_OPEN_{YEAR}` (2021–26; 2023 is `_2023v`) at `gis.crashdata.dot.mass.gov`; `CrashClosedYear{YEAR}` (2002–19) and `CrashClosedYears` (2020) at `gis.massdot.state.ma.us` | Severity, hour, manner, non-motorist type, weather, light, road AADT and speed limit; vehicle and person tables | Point (`CITY_TOWN_NAME='SOMERVILLE'`) | 2002 – now (open years change) | Open. Somerville: 790 (2015), 829 (2019), 585 (2020), 710 (2022), 627 (2024). Has street numbers: publish street only. The IMPACT web app's certificate had expired. |
| Injury crashes, Vision Zero | Boston Region MPO, [VZDashboard_Crashes_Spatial](https://services1.arcgis.com/jIRgb54Jq9V3BUeD/arcgis/rest/services/VZDashboard_Crashes_Spatial/FeatureServer/0) | Injury crashes with mode flags, near schools and transit | Point | 2018 – Sep 2026 | Open (1,654 in Somerville, 216 with pedestrians) |
| Vision Zero intersections | City, [Vision Zero page](https://www.somervillema.gov/visionzero) (Google Sheet, Feb 2021 GIS zip) | Crashes and rates by intersection, ward | Intersection | to Feb 2021 | Open, snapshot |

## Who travels how

| Source | Publisher, link | What it holds | Where, how fine | Years | Status |
|---|---|---|---|---|---|
| Commute mode (ACS B08301) | MAPC DataCommon, [CSV by tract](https://datacommon.mapc.org/api/export?token=datacommon&database=ds&schema=tabular&table=b08301_means_transportation_to_work_by_residence_acs_ct&format=csv); also [Census Reporter API](https://api.censusreporter.org/1.0/data/show/latest?table_ids=B08301&geo_ids=140%7C16000US2562535) | Workers by how they get to work, with margins of error | Census tract (25) | Every 5-year window 2006–10 … 2020–24 | Open, no key. 2020–24 city: drove alone 29.9%, transit 19.3%, walked 8.5%, bike 5.4%, worked from home 31.3%. The Census API itself now needs a key. |
| Cars per household (ACS B08201, B25044) | Census summary files (keyless), e.g. [`acsdt5y2024-b08201.dat`](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b08201.dat) | Households by vehicles available | Tract, city | 5-year 2020–24 (and earlier) | Open (national file, 63–88 MB). Somerville: 7,700 of 35,715 households (21.6%) have no car. |
| Commute mode, work from home, employment and age, every year (ACS 1-year: B08301, B23025, B01001) | Census Bureau, [data.census.gov table service](https://data.census.gov/table/ACSDT1Y2024.B08301?g=160XX00US2562535) (`https://data.census.gov/api/access/data/table?id=ACSDT1Y{year}.{table}&g=160XX00US2562535`) | Residents who worked, how they usually got there the week before (drove alone, transit, walked, biked, worked from home), margins of error; employed residents; age | Somerville city, year | 2015 – 2025 (none for 2020; Somerville not published for 2022 or 2023; earlier years exist, context only) | **In use** (transit over time: "Who's working"). No key; the site refuses some clients, so send a common client name. 2019 → 2025: residents working 54,403 → 58,726; worked from home 4.5% → 16.6% (36.5% in 2021); took transit 30.0% → 26.1%; age 65+ about 9%. It counts hybrid workers by their usual mode, so it misses fewer days a week on transit. |
| Jobs by workplace and by residence (LODES) | Census Bureau LEHD, [LODES 8](https://lehd.ces.census.gov/data/) (`ma_wac_S000_JT00_{year}.csv.gz`, `ma_rac_…`) | Jobs covered by unemployment insurance, all jobs, by census block where the job is (WAC) or where the worker lives (RAC); also by age, earnings, industry; origin–destination files link the two | Census block (sum Somerville's tracts 25017-350100 to 351599) | 2002 – 2024 | **In use** (transit over time: "People with jobs"). Jobs located in Somerville 35,444 (2019) → 34,158 (2024); jobs held by residents 47,613 → 46,498. No self-employed; one person can hold two jobs. The origin–destination files could show where residents work. |
| MBTA passenger survey 2025 | MBTA, [Passenger Survey layer](https://services1.arcgis.com/ceiitspzDAHrdGO1/arcgis/rest/services/MBTA_2025_System-Wide_Passenger_Survey/FeatureServer/0) | Weighted shares with sample size and margin: how riders reach the T, trip purpose, frequency, income, race, age, cars, fare | Station or reporting area (Union, East Somerville/Gilman, Magoun/Ball, Assembly, Davis, route 86; bus areas "Somerville/Medford/Charlestown – East" n=700 and "– West" n=1,395) | 2025 | Open (18,584 rows; no rider-level records). E.g. 93.7% of West-area bus riders walked to their first ride. |
| MBTA passenger survey 2015–17 | CTPS, [survey site](https://www.ctps.org/dv/mbtasurvey2018/index.html) | Same kinds of questions | Station, route (some paired) | 2015 – 2017 | Open (Excel); before the Green Line Extension: a before/after with 2025 |
| Happiness Survey | City, [`wmeh-zuz2`](https://data.somervillema.gov/resource/wmeh-zuz2.json) | Walk / transit in the past week; crossing safety; street maintenance | Ward | 2019, 2023, 2025 (transport questions) | **In use** (2025, replay ward map) |
| ADA Community Survey | City, `usj9-kz3f` | Accessibility survey incl. a "sidewalks" field (no codebook) | Respondent | Feb – Jun 2023 | Open (hard to use) |

## Not public, or asked

Questions for officials are in [`questions.md`](questions.md):
- Employed residents by month (BLS Local Area Unemployment Statistics, series `LAUCT256253500000005` for Somerville city): **blocked** from here (the BLS API's daily limit without a key was used up on this network, and its bulk file `la.data.65.City` answered 403). The yearly survey and LODES cover the same question.
- Hourly traffic counts on Somerville streets (55). Partial: MassDOT segment estimates and the City's PDF counts above.
- Daily parking meter and ParkMobile revenue (56). Partial: yearly totals FY15–FY18 above.
- Parking tickets per day, snow emergency tickets and tow fees (57). Partial: yearly totals FY15–FY18 above.
- The City's current sidewalk condition data (Sidewalk Condition Index by segment, from its annual surveys): not yet a question; worth asking with 58–61.
- Bus shelters and who owns and clears them (58); what's at each stop today (59); real-time signs (60).
- Also not found: City walking/biking counter data (an Eco-Counter or the Davis Square camera), a sidewalk condition inventory newer than 2016 (the City's current Sidewalk Condition Index, updated by annual surveys, feeds its repair rankings but isn't published; ask for it), the City's crash dashboard data (2017–22), the curb inventory as data, permits by zone after 2020, bus speed or slow-zone datasets.

## Leads not checked yet

- The City's Parking & Curb Use Study Final Report (the link returned a web page, not the PDF).
- Traffic & Parking performance tables for FY21–FY27 in the ClearGov budget books (the app didn't render).
- The MassDOT pedestrian and bike crash cluster layers (`Roads/CrashClusters_ODP/FeatureServer/33`, `35`, 2014–2023).
- Boston Region MPO / CTPS traffic counts; SomerVision and mobility plan data files.
- MAPC DataCommon: access to jobs by transit (2019), bike facilities (Apr 2025), household vehicles.
- MBTA "Ratings & Seasons" table (listed, undescribed).
- An archived 2019 "Updated Somerville Bike Network" layer (owner Account_Archive).

## What these could show on SomerWalks

- **Who depends on the bus:** car-free households (21.6% citywide) and transit commuters by tract, next to the bus trips map; MBTA survey shares on how riders reach each station.
- **Before and after the Green Line Extension:** Fall 2017–19 vs Fall 2024–25 rail ridership by hour, the 2015–17 vs 2025 passenger surveys, and nearby bus stops' riders by season.
- **Walking and biking trends:** the City's yearly counts (2015 on) beside the bike network's growth (2020–25) and traffic calming installed.
- **Cars:** vehicles registered and miles driven (2020–26), rideshare pickups (2017–25), estimated traffic on main roads: labeled as estimates.
- **Parking pressure:** 2.47 resident permits per permit space (2022 study), permits by type and ZIP (2017–20), meters (2016).
- **Safety:** state crashes back to 2015 to extend the City's series, by mode and hour.
