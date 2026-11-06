# Bus stop clearing order: results

Built by build.py from MBTA Fall 2025 weekday boardings. 189 stops the City clears (18 more are on route 109, which the MBTA clears), 7,663 weekday boardings.

Half of those boardings happen at 15 stops.

| | Route by route | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.0 h | 4.7 h |
| Riders' stops clear after 1 h | 4% | 33% |
| Riders' stops clear after 2 h | 7% | 45% |
| Riders' stops clear after 4 h | 42% | 58% |
| Riders' stops clear after 8 h | 64% | 77% |
| Riders' stops clear after 12 h | 81% | 88% |
| All stops clear | 21.4 h | 18.6 h |
| Hours driving | 12.7 h | 10.0 h |
| Distance driven | 101.8 km | 80.7 km |

Hours are working hours, from when the crews start at their first stops. The bobcats drive along the street, stop to stop, and never drive past a waiting stop.

Assumptions: crews = 4; service_min = 20; drive_m_per_min = 134; cross_m = 60; max_link_m = 900; corner_m = 100; lookahead = 8; start_apart_m = 1200; sweep_after = 0.7; mbta_routes = ['109'].

## If an assumption is off

| Change | Average wait (route by route → riders first) | Riders' stops clear after 4 h | All stops clear |
| --- | --- | --- | --- |
| 2 crews | 17.5 h → 10.8 h | 8% → 40% | 38.4 h → 37.1 h |
| 6 crews | 5.4 h → 3.2 h | 48% → 69% | 16.0 h → 13.2 h |
| 10 min a stop | 4.0 h → 2.5 h | 60% → 76% | 13.6 h → 10.8 h |
| 30 min a stop | 10.1 h → 6.8 h | 10% → 49% | 29.3 h → 26.4 h |
| bobcat at 3 mph | 7.7 h → 4.9 h | 40% → 57% | 25.3 h → 20.6 h |
| bobcat at 8 mph | 6.7 h → 4.5 h | 42% → 60% | 19.3 h → 17.4 h |

## How many crews?

| Crews | Average wait (route by route → riders first) | All stops clear |
| --- | --- | --- |
| 1 | 36.1 h → 21.1 h | 76.5 h → 72.0 h |
| 2 | 17.5 h → 10.8 h | 38.4 h → 37.1 h |
| 3 | 12.4 h → 6.5 h | 25.8 h → 24.3 h |
| 4 | 7.0 h → 4.7 h | 21.4 h → 18.6 h |
| 5 | 5.9 h → 3.9 h | 16.0 h → 15.5 h |
| 6 | 5.4 h → 3.2 h | 16.0 h → 13.2 h |
| 7 | 5.1 h → 2.8 h | 16.0 h → 11.9 h |
| 8 | 5.0 h → 2.5 h | 16.0 h → 10.3 h |
| 9 | 4.9 h → 2.3 h | 16.0 h → 9.5 h |
| 10 | 4.9 h → 2.0 h | 16.0 h → 8.7 h |
