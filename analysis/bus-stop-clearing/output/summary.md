# Bus stop clearing order: results

Built by build.py from MBTA Fall 2025 weekday boardings. 189 stops the City clears (18 more are on route 109, which the MBTA clears), 7,663 weekday boardings.

Half of those boardings happen at 15 stops.

| | Route by route | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.3 h | 4.4 h |
| Riders' stops clear after 1 h | 4% | 37% |
| Riders' stops clear after 2 h | 9% | 47% |
| Riders' stops clear after 4 h | 16% | 62% |
| Riders' stops clear after 8 h | 58% | 79% |
| Riders' stops clear after 12 h | 87% | 89% |
| All stops clear | 22.9 h | 19.7 h |
| Hours driving | 15.2 h | 14.3 h |
| Distance driven | 91.8 km | 86.3 km |

Hours are working hours, from when the crews start at their first stops. The bobcats drive along the street, stop to stop, and never drive past a waiting stop.

Assumptions: crews = 4; service_min = 20; drive_m_per_min = 134; cross_m = 60; on_route_m = 25; turn_min = 5; max_link_m = 900; lookahead = 8; start_apart_m = 1200; sweep_after = 0.7; mbta_routes = ['109'].

## If an assumption is off

| Change | Average wait (route by route → riders first) | Riders' stops clear after 4 h | All stops clear |
| --- | --- | --- | --- |
| 2 crews | 18.3 h → 10.8 h | 7% → 43% | 39.7 h → 40.1 h |
| 6 crews | 5.6 h → 3.0 h | 28% → 72% | 15.8 h → 14.3 h |
| 10 min a stop | 4.2 h → 2.4 h | 54% → 77% | 15.1 h → 11.9 h |
| 30 min a stop | 10.5 h → 6.4 h | 12% → 55% | 30.7 h → 27.2 h |
| bobcat at 3 mph | 7.9 h → 4.7 h | 14% → 62% | 26.4 h → 23.3 h |
| bobcat at 8 mph | 7.0 h → 4.2 h | 39% → 65% | 20.9 h → 18.6 h |

## How many crews?

| Crews | Average wait (route by route → riders first) | All stops clear |
| --- | --- | --- |
| 1 | 37.1 h → 21.7 h | 79.2 h → 77.3 h |
| 2 | 18.3 h → 10.8 h | 39.7 h → 40.1 h |
| 3 | 13.2 h → 6.0 h | 26.6 h → 26.7 h |
| 4 | 7.3 h → 4.4 h | 22.9 h → 19.7 h |
| 5 | 6.2 h → 3.5 h | 17.5 h → 15.9 h |
| 6 | 5.6 h → 3.0 h | 15.8 h → 14.3 h |
| 7 | 5.3 h → 2.6 h | 15.8 h → 12.2 h |
| 8 | 5.1 h → 2.3 h | 15.8 h → 11.0 h |
| 9 | 5.1 h → 2.2 h | 15.8 h → 10.3 h |
| 10 | 5.1 h → 1.9 h | 15.8 h → 9.3 h |
