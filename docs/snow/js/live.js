/* Live "storm mode": a banner at the top of the guide while snow is on the way, falling, or just ended.
 *
 * Sources (free, no key, browser-friendly): National Weather Service API
 *   - forecast grid for Somerville (BOX 70,102): snowfall amounts by time interval
 *   - active alerts for Somerville's zone (MAZ014): winter storm warnings etc.
 *   - observations at Boston Logan (KBOS): is it snowing now, when did it stop
 * The deadline uses the guide's own calculator (deadline.js). Everything here is an estimate and says so.
 * The City's snow emergency has no public feed, so the banner tells people how to check, never guesses it.
 *
 * liveState() is pure (tested in test/live.test.js); fetchLive() does the network; ?live=<state> shows a demo.
 */
import { deadline } from './deadline.js';

const HOUR = 36e5;
const NWS = 'https://api.weather.gov';
export const GRID = `${NWS}/gridpoints/BOX/70,102`;
export const ALERTS = `${NWS}/alerts/active?zone=MAZ014`;
export const OBS = `${NWS}/stations/KBOS/observations?limit=60`;

/** Falling snow in a METAR report (before RMK). Blowing/drifting snow (BLSN, DRSN) is wind, not new snow. */
export function metarSnow(raw) {
  if (!raw) return false;
  const body = raw.split(' RMK')[0].split(' ').slice(2);
  return body.some((w) => /^[-+]?(VC)?(SH|TS|FZ)?[A-Z]*SN[A-Z]*$/.test(w) && !/BLSN|DRSN/.test(w));
}

/** NWS interval "2026-02-22T21:00:00+00:00/PT3H" (or P1DT6H) -> [startMs, endMs]. */
export function interval(validTime) {
  const [start, dur] = validTime.split('/');
  const m = dur.match(/P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?/);
  const hours = (+(m[1] || 0)) * 24 + (+(m[2] || 0)) + (+(m[3] || 0)) / 60;
  const a = Date.parse(start);
  return [a, a + hours * HOUR];
}

/**
 * Decide what the banner shows.
 * @param {object} p
 * @param {Array<{t:number, snow:boolean}>} p.obs  Logan observations (any order)
 * @param {Array<{from:number, to:number, mm:number}>} p.snowfall  forecast snowfall intervals
 * @param {Array<{event:string, ends:number|null}>} p.alerts  active NWS alerts for the zone
 * @param {number} p.now  UTC ms
 * @returns {{phase:'quiet'|'forecast'|'snowing'|'stopped'|'passed', ...}}
 */
export function liveState({ obs = [], snowfall = [], alerts = [], now }) {
  const winter = alerts.filter((a) => /winter|snow|blizzard|ice|freezing/i.test(a.event));
  const recent = obs.filter((o) => o.t <= now && o.t > now - 36 * HOUR).sort((a, b) => a.t - b.t);
  const latest = recent[recent.length - 1];
  const snowingNow = !!latest && latest.snow && latest.t > now - 2 * HOUR;
  const lastSnow = [...recent].reverse().find((o) => o.snow);

  // forecast: snow in the next 48 hours (ignore traces under 1 mm per interval)
  const ahead = snowfall.filter((s) => s.to > now && s.from < now + 48 * HOUR && s.mm >= 1).sort((a, b) => a.from - b.from);
  // the next storm: consecutive snowy intervals with gaps under 6 hours
  const storm = [];
  for (const s of ahead) { if (!storm.length || s.from - storm[storm.length - 1].to < 6 * HOUR) storm.push(s); else break; }
  const inches = storm.reduce((a, s) => a + s.mm, 0) / 25.4;
  const fStart = storm.length ? storm[0].from : null;
  const fEnd = storm.length ? storm[storm.length - 1].to : null;
  const base = { alerts: winter, inches: Math.round(inches * 10) / 10, forecastStart: fStart, forecastEnd: fEnd };

  if (snowingNow) {
    const stopGuess = fEnd && fEnd > now ? fEnd : null;
    return { ...base, phase: 'snowing', estimatedStop: stopGuess, estimatedDeadline: stopGuess ? deadline(stopGuess).end : null };
  }
  // a real snowfall, not a passing flurry: at least 3 reports of falling snow (about 3 hours) in the last 36
  if (lastSnow && recent.filter((o) => o.snow).length >= 3) {
    // stopped: the first observation without snow after the last snowy one
    const after = recent.find((o) => o.t > lastSnow.t && !o.snow);
    const stop = after ? after.t : lastSnow.t;
    const dl = deadline(stop).end;
    if (now < dl) return { ...base, phase: 'stopped', stop, deadline: dl, moreSnow: fStart && fStart < now + 12 * HOUR ? fStart : null };
    if (now < dl + 30 * HOUR) return { ...base, phase: 'passed', stop, deadline: dl };
  }
  if (storm.length && inches >= 0.3) return { ...base, phase: 'forecast' };
  if (winter.length) return { ...base, phase: 'forecast' };
  return { ...base, phase: 'quiet' };
}

/** Fetch the three NWS feeds and turn them into liveState() input. Throws on network failure. */
export async function fetchLive(now = Date.now()) {
  const get = (u) => fetch(u, { headers: { Accept: 'application/geo+json' } }).then((r) => { if (!r.ok) throw new Error(`${r.status} ${u}`); return r.json(); });
  const [grid, alerts, obs] = await Promise.all([get(GRID), get(ALERTS).catch(() => ({ features: [] })), get(OBS).catch(() => ({ features: [] }))]);
  return {
    now,
    snowfall: (grid.properties.snowfallAmount?.values || []).map((v) => { const [from, to] = interval(v.validTime); return { from, to, mm: v.value || 0 }; }),
    alerts: alerts.features.map((f) => ({ event: f.properties.event, ends: Date.parse(f.properties.ends || f.properties.expires) || null })),
    obs: obs.features.map((f) => ({ t: Date.parse(f.properties.timestamp), snow: metarSnow(f.properties.rawMessage) })),
  };
}

/** Demo inputs relative to now, for ?live=forecast|snowing|stopped|passed (the banner is marked "demo"). */
export function demoInput(kind, now = Date.now()) {
  const h = (n) => now + n * HOUR;
  const obsRange = (from, to, snow) => Array.from({ length: Math.max(0, to - from) }, (_, k) => ({ t: h(from + k), snow: snow(from + k) }));
  if (kind === 'forecast') return { now, obs: obsRange(-10, 0, () => false), snowfall: [{ from: h(14), to: h(20), mm: 90 }, { from: h(20), to: h(26), mm: 110 }], alerts: [{ event: 'Winter Storm Warning', ends: h(30) }] };
  if (kind === 'snowing') return { now, obs: obsRange(-8, 1, (k) => k >= -6), snowfall: [{ from: h(-6), to: h(0), mm: 80 }, { from: h(0), to: h(5), mm: 70 }], alerts: [{ event: 'Winter Storm Warning', ends: h(6) }] };
  if (kind === 'stopped') return { now, obs: obsRange(-20, 1, (k) => k >= -16 && k < -3), snowfall: [], alerts: [] };
  if (kind === 'passed') return { now, obs: obsRange(-34, 1, (k) => k >= -34 && k < -28), snowfall: [], alerts: [] };
  return null;
}

/** An .ics calendar file with a reminder before the deadline. */
export function icsFor(deadlineMs, title, details) {
  const z = (ms) => new Date(ms).toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
  return ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Somerville PTAC//Snow Guide//EN', 'BEGIN:VEVENT',
    `UID:shovel-${deadlineMs}@somersnow`, `DTSTAMP:${z(Date.now())}`, `DTSTART:${z(deadlineMs - HOUR)}`, `DTEND:${z(deadlineMs)}`,
    `SUMMARY:${title}`, `DESCRIPTION:${details}`, 'BEGIN:VALARM', 'TRIGGER:-PT1H', 'ACTION:DISPLAY', `DESCRIPTION:${title}`, 'END:VALARM',
    'END:VEVENT', 'END:VCALENDAR'].join('\r\n');
}
