# Bus stop clearing order: results

Built by build.py from MBTA Fall 2025 weekday boardings. 189 stops the City clears (18 more are on route 109, which the MBTA clears), 7,663 weekday boardings.

Half of those boardings happen at 15 stops.

| | Route by route | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 6.9 h | 4.3 h |
| Riders' stops clear after 1 h | 4% | 36% |
| Riders' stops clear after 2 h | 7% | 47% |
| Riders' stops clear after 4 h | 42% | 64% |
| Riders' stops clear after 8 h | 64% | 80% |
| Riders' stops clear after 12 h | 81% | 88% |
| All stops clear | 20.2 h | 19.1 h |
| Hours driving | 11.5 h | 11.1 h |
| Distance driven | 92.4 km | 89.5 km |

Hours are working hours, from when the crews start at their first stops. The bobcats drive along the street, stop to stop, and never drive past a waiting stop.

Assumptions: crews = 4; service_min = 20; drive_m_per_min = 134; cross_m = 60; lookahead = 8; start_apart_m = 1200; sweep_after = 0.7; mbta_routes = ['109'].

## If an assumption is off

| Change | Average wait (route by route → riders first) | Riders' stops clear after 4 h | All stops clear |
| --- | --- | --- | --- |
| 2 crews | 17.4 h → 10.8 h | 8% → 41% | 37.3 h → 38.2 h |
| 6 crews | 5.3 h → 3.0 h | 48% → 75% | 16.0 h → 13.2 h |
| 10 min a stop | 3.9 h → 2.4 h | 60% → 78% | 12.4 h → 11.0 h |
| 30 min a stop | 10.0 h → 6.3 h | 10% → 54% | 28.1 h → 26.5 h |
| bobcat at 3 mph | 7.6 h → 4.6 h | 40% → 62% | 23.3 h → 21.1 h |
| bobcat at 8 mph | 6.6 h → 4.2 h | 43% → 65% | 18.5 h → 17.6 h |

## How many crews?

| Crews | Average wait (route by route → riders first) | All stops clear |
| --- | --- | --- |
| 1 | 36.0 h → 20.1 h | 75.3 h → 71.4 h |
| 2 | 17.4 h → 10.8 h | 37.3 h → 38.2 h |
| 3 | 12.3 h → 6.2 h | 25.8 h → 25.7 h |
| 4 | 6.9 h → 4.3 h | 20.2 h → 19.1 h |
| 5 | 5.9 h → 3.6 h | 16.0 h → 15.1 h |
| 6 | 5.3 h → 3.0 h | 16.0 h → 13.2 h |
| 7 | 5.0 h → 2.7 h | 16.0 h → 11.2 h |
| 8 | 4.9 h → 2.4 h | 16.0 h → 10.0 h |
| 9 | 4.8 h → 2.2 h | 16.0 h → 8.8 h |
| 10 | 4.8 h → 2.0 h | 16.0 h → 8.4 h |
