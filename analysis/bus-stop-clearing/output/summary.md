# Bus stop clearing order: results

Built by build.py from MBTA Fall 2025 weekday ridership. 189 stops the City clears (18 more are on route 109, which the MBTA clears), 15,293 weekday riders: 7,663 getting on and 7,630 getting off.

Half of those riders use 20 stops.

| | Route by route | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.7 h | 5.1 h |
| Riders' stops clear after 1 h | 3% | 27% |
| Riders' stops clear after 2 h | 7% | 40% |
| Riders' stops clear after 4 h | 17% | 58% |
| Riders' stops clear after 8 h | 56% | 74% |
| Riders' stops clear after 12 h | 85% | 86% |
| All stops clear | 21.2 h | 18.0 h |
| Hours driving | 12.1 h | 8.1 h |
| Distance driven | 90.8 km | 58.9 km |
| Jumps (drives over 800 m to the next stop) | 20 (51.4 km) | 10 (19.4 km) |

Hours are working hours, from when the crews start at their first stops. The bobcats drive along the street, stop to stop, and never drive past a waiting stop.

Assumptions: crews = 4; service_min = 20; drive_m_per_min = 134; cross_m = 60; on_route_m = 25; turn_min = 1; max_link_m = 900; lookahead = 8; start_apart_m = 1200; jump_m = 800; jump_min = 30; sweep_after = 0.7; mbta_routes = ['109'].

## If an assumption is off

| Change | Average wait (route by route → riders first) | Riders' stops clear after 4 h | All stops clear |
| --- | --- | --- | --- |
| 2 crews | 18.9 h → 11.1 h | 6% → 40% | 38.1 h → 36.2 h |
| 6 crews | 5.9 h → 3.3 h | 26% → 70% | 15.6 h → 12.2 h |
| 10 min a stop | 4.3 h → 2.8 h | 49% → 72% | 13.4 h → 10.4 h |
| 30 min a stop | 11.1 h → 7.4 h | 10% → 45% | 29.0 h → 26.7 h |
| bobcat at 3 mph | 8.3 h → 5.4 h | 14% → 57% | 24.7 h → 20.3 h |
| bobcat at 8 mph | 7.4 h → 4.8 h | 32% → 60% | 19.3 h → 17.4 h |

## How many crews?

| Crews | Average wait (route by route → riders first) | All stops clear |
| --- | --- | --- |
| 1 | 37.9 h → 21.5 h | 75.9 h → 72.0 h |
| 2 | 18.9 h → 11.1 h | 38.1 h → 36.2 h |
| 3 | 13.3 h → 6.7 h | 25.5 h → 24.6 h |
| 4 | 7.7 h → 5.1 h | 21.2 h → 18.0 h |
| 5 | 6.6 h → 4.2 h | 15.9 h → 14.8 h |
| 6 | 5.9 h → 3.3 h | 15.6 h → 12.2 h |
| 7 | 5.6 h → 3.5 h | 15.6 h → 10.6 h |
| 8 | 5.5 h → 2.7 h | 15.6 h → 10.1 h |
| 9 | 5.4 h → 2.4 h | 15.6 h → 8.1 h |
| 10 | 5.4 h → 2.1 h | 15.6 h → 7.8 h |
