# Bus stop clearing order: results

Built by build.py from MBTA Fall 2025 weekday boardings. 189 stops the City clears (18 more are on route 109, which the MBTA clears), 7,663 weekday boardings.

Half of those boardings happen at 15 stops.

| | Route by route | Ridership first |
| --- | --- | --- |
| Average wait for a rider's stop | 8.2 h | 5.0 h |
| Riders' stops clear after 2 h | 6% | 44% |
| Riders' stops clear after 4 h | 15% | 63% |
| Riders' stops clear after 6 h | 47% | 69% |
| Riders' stops clear after 8 h | 58% | 75% |
| Riders' stops clear after 12 h | 77% | 85% |
| All stops clear | 22.5 h | 21.4 h |
| Trailer moves | 27 | 22 |
| Time spent moving | 18.6 h | 16.6 h |

Hours are working hours for the crews, from the time they start on bus stops.

Assumptions: crews = 4; service_min = 20; drive_m_per_min = 134; detour = 1.3; drive_max_m = 800; trailer_min = 30; mbta_routes = ['109']; max_stretch = 12; sweep_after = 0.6.

## If an assumption is off

| Change | Average wait (route by route → ridership first) | Riders' stops clear after 4 h | All stops clear | Trailer moves |
| --- | --- | --- | --- | --- |
| 2 crews | 19.4 h → 9.4 h | 8% → 48% | 42.3 h → 39.5 h | 27 → 19 |
| 6 crews | 6.4 h → 3.8 h | 22% → 66% | 17.2 h → 15.2 h | 28 → 24 |
| 10 min a stop | 5.2 h → 3.4 h | 48% → 68% | 14.7 h → 12.2 h | 27 → 22 |
| 30 min a stop | 11.2 h → 6.9 h | 8% → 56% | 30.3 h → 29.0 h | 27 → 19 |
| 15 min to trailer | 7.3 h → 4.5 h | 40% → 63% | 19.7 h → 18.9 h | 27 → 26 |
| 45 min to trailer | 9.0 h → 5.7 h | 11% → 57% | 25.2 h → 21.9 h | 27 → 22 |
| drive at most 500 m | 8.6 h → 5.1 h | 13% → 61% | 23.8 h → 22.3 h | 41 → 33 |
| drive up to 1.5 km | 7.9 h → 5.2 h | 36% → 62% | 21.4 h → 19.4 h | 20 → 13 |
| bobcat at 3 mph | 8.5 h → 5.4 h | 13% → 61% | 23.4 h → 21.2 h | 27 → 22 |
