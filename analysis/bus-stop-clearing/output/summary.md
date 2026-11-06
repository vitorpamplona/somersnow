# Bus stop clearing order: results

Built by build.py from MBTA Fall 2025 weekday boardings. 189 stops the City clears (18 more are on route 109, which the MBTA clears), 7,663 weekday boardings.

Half of those boardings happen at 15 stops.

| | Route by route | Riders first |
| --- | --- | --- |
| Average wait for a rider's stop | 7.0 h | 3.4 h |
| Riders' stops clear after 1 h | 4% | 39% |
| Riders' stops clear after 2 h | 7% | 54% |
| Riders' stops clear after 4 h | 42% | 70% |
| Riders' stops clear after 8 h | 64% | 86% |
| Riders' stops clear after 12 h | 80% | 95% |
| All stops clear | 19.7 h | 20.1 h |
| Hours driving between stops | 11.0 h | 16.0 h |
| Distance driven | 88.3 km | 128.5 km |

Hours are working hours, from when the crews start at their first stops. The bobcats drive from stop to stop.

Assumptions: crews = 4; service_min = 20; drive_m_per_min = 134; detour = 1.3; mbta_routes = ['109']; passes = 8.

## If an assumption is off

| Change | Average wait (route by route → riders first) | Riders' stops clear after 4 h | All stops clear |
| --- | --- | --- | --- |
| 2 crews | 17.5 h → 6.6 h | 8% → 54% | 38.0 h → 40.1 h |
| 6 crews | 5.3 h → 2.3 h | 48% → 79% | 16.0 h → 14.1 h |
| 10 min a stop | 4.0 h → 1.9 h | 59% → 85% | 11.9 h → 11.8 h |
| 30 min a stop | 10.0 h → 4.8 h | 11% → 60% | 27.6 h → 29.1 h |
| bobcat at 3 mph | 7.7 h → 3.7 h | 40% → 67% | 22.5 h → 22.5 h |
| bobcat at 8 mph | 6.7 h → 3.2 h | 42% → 71% | 18.2 h → 19.1 h |
| streets 60% longer than a straight line | 7.3 h → 3.6 h | 40% → 68% | 20.7 h → 21.1 h |
