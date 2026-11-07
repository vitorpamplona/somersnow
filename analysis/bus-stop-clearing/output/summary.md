# Bus stop clearing order: results

Built by build.py from MBTA Fall 2025 weekday ridership. 189 stops the City clears (18 more are on route 109, which the MBTA clears), 15,293 weekday riders: 7,663 getting on and 7,630 getting off.

Half of those riders use 20 stops.

| | Route by route | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.7 h | 4.9 h |
| Riders' stops clear after 1 h | 3% | 27% |
| Riders' stops clear after 2 h | 7% | 40% |
| Riders' stops clear after 4 h | 17% | 56% |
| Riders' stops clear after 8 h | 56% | 74% |
| Riders' stops clear after 12 h | 85% | 90% |
| All stops clear | 21.2 h | 19.2 h |
| Hours driving | 12.1 h | 12.3 h |
| Distance driven | 90.8 km | 90.8 km |

Hours are working hours, from when the crews start at their first stops. The bobcats drive along the street, stop to stop, and never drive past a waiting stop.

Assumptions: crews = 4; service_min = 20; drive_m_per_min = 134; cross_m = 60; on_route_m = 25; turn_min = 1; max_link_m = 900; lookahead = 8; start_apart_m = 1200; sweep_after = 0.7; mbta_routes = ['109'].

## If an assumption is off

| Change | Average wait (route by route → riders first) | Riders' stops clear after 4 h | All stops clear |
| --- | --- | --- | --- |
| 2 crews | 18.9 h → 11.4 h | 6% → 40% | 38.1 h → 37.0 h |
| 6 crews | 5.9 h → 3.4 h | 26% → 69% | 15.6 h → 13.1 h |
| 10 min a stop | 4.3 h → 2.7 h | 49% → 72% | 13.4 h → 11.1 h |
| 30 min a stop | 11.1 h → 7.1 h | 10% → 49% | 29.0 h → 27.2 h |
| bobcat at 3 mph | 8.3 h → 5.2 h | 14% → 55% | 24.7 h → 20.5 h |
| bobcat at 8 mph | 7.4 h → 4.8 h | 32% → 60% | 19.3 h → 18.0 h |

## How many crews?

| Crews | Average wait (route by route → riders first) | All stops clear |
| --- | --- | --- |
| 1 | 37.9 h → 22.2 h | 75.9 h → 74.0 h |
| 2 | 18.9 h → 11.4 h | 38.1 h → 37.0 h |
| 3 | 13.3 h → 6.7 h | 25.5 h → 25.2 h |
| 4 | 7.7 h → 4.9 h | 21.2 h → 19.2 h |
| 5 | 6.6 h → 4.1 h | 15.9 h → 15.7 h |
| 6 | 5.9 h → 3.4 h | 15.6 h → 13.1 h |
| 7 | 5.6 h → 3.0 h | 15.6 h → 11.2 h |
| 8 | 5.5 h → 2.6 h | 15.6 h → 9.8 h |
| 9 | 5.4 h → 2.3 h | 15.6 h → 8.8 h |
| 10 | 5.4 h → 2.1 h | 15.6 h → 8.1 h |
