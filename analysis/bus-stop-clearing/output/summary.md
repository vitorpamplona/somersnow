# Bus stop clearing order: results

Built by build.py from MBTA Fall 2025 weekday ridership. 189 stops the City clears (18 more are on route 109, which the MBTA clears), 15,293 weekday riders: 7,663 getting on and 7,630 getting off.

Half of those riders use 20 stops.

| | Route by route | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.7 h | 6.0 h |
| Riders' stops clear after 1 h | 3% | 26% |
| Riders' stops clear after 2 h | 7% | 33% |
| Riders' stops clear after 4 h | 17% | 44% |
| Riders' stops clear after 8 h | 57% | 63% |
| Riders' stops clear after 12 h | 85% | 86% |
| All stops clear | 20.5 h | 19.2 h |
| Hours driving | 11.0 h | 6.9 h |
| Distance driven | 83.5 km | 49.8 km |
| Jumps (drives over 800 m to the next stop) | 18 (43.5 km) | 5 (7.4 km) |
| Pairs of stops on one stretch of street cleared by different crews | 83 | 0 |
| Driving back over a link the same crew already drove | 23.3 km | 8.3 km |
| Driving along another crew's streets | 14.9 km | 0.2 km |
| Leaving a street with own stops on it still waiting (and coming back later) | 14 | 3 |

Hours are working hours, from when the crews start at their first stops. The bobcats drive along the street, stop to stop, and never drive past a waiting stop.

Assumptions: crews = 4; service_min = 20; drive_m_per_min = 134; cross_m = 60; on_route_m = 25; turn_min = 1; max_link_m = 900; lookahead = 8; start_apart_m = 1200; stretch_stops = 10; jump_m = 800; jump_min = 60; jump_km_min = 120; break_min = 180; finish_w = 2; sweep_after = 0.7; mbta_routes = ['109'].

## If an assumption is off

| Change | Average wait (route by route → riders first) | Riders' stops clear after 4 h | All stops clear |
| --- | --- | --- | --- |
| 2 crews | 18.7 h → 11.6 h | 6% → 29% | 37.1 h → 35.8 h |
| 6 crews | 5.9 h → 3.9 h | 26% → 59% | 15.6 h → 12.8 h |
| 10 min a stop | 4.3 h → 2.9 h | 49% → 70% | 12.6 h → 10.7 h |
| 30 min a stop | 11.1 h → 8.9 h | 10% → 35% | 28.3 h → 29.0 h |
| bobcat at 3 mph | 8.3 h → 6.2 h | 14% → 47% | 23.5 h → 20.1 h |
| bobcat at 8 mph | 7.4 h → 5.2 h | 32% → 55% | 18.8 h → 18.1 h |

## How many crews?

| Crews | Average wait (route by route → riders first) | All stops clear |
| --- | --- | --- |
| 1 | 37.5 h → 23.4 h | 74.7 h → 70.9 h |
| 2 | 18.7 h → 11.6 h | 37.1 h → 35.8 h |
| 3 | 13.1 h → 8.2 h | 25.3 h → 24.4 h |
| 4 | 7.7 h → 6.0 h | 20.5 h → 19.2 h |
| 5 | 6.6 h → 4.9 h | 15.7 h → 16.0 h |
| 6 | 5.9 h → 3.9 h | 15.6 h → 12.8 h |
| 7 | 5.6 h → 4.0 h | 15.6 h → 12.7 h |
| 8 | 5.5 h → 3.3 h | 15.6 h → 12.4 h |
| 9 | 5.4 h → 2.7 h | 15.6 h → 11.5 h |
| 10 | 5.4 h → 2.4 h | 15.6 h → 9.8 h |
