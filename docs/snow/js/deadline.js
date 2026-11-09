/*
 * The 6-daylight-hour shoveling deadline (Somerville Code of Ordinances, Sec. 12-8(a)):
 * snow may not remain "for more than six hours between sunrise and sunset following
 * the conclusion of a weather event". The clock runs only in daylight and pauses overnight.
 *
 * Pure functions, no DOM: imported by the page and by test/deadline.test.js.
 */

export const SOMERVILLE = { lat: 42.3876, lon: -71.0995, tz: 'America/New_York' };
const RD = Math.PI / 180;
const HOUR = 36e5;
export const DAYLIGHT_HOURS = 6;

/** Sunrise and sunset (UTC ms) for a calendar date, using the standard sunrise equation. */
export function sunTimes(y, m, d, { lat, lon } = SOMERVILLE) {
  const jd = Date.UTC(y, m - 1, d, 12) / 864e5 + 2440587.5;
  const n = Math.round(jd - 2451545);
  const js = n - lon / 360;
  const M = (357.5291 + 0.98560028 * js) % 360;
  const C = 1.9148 * Math.sin(M * RD) + 0.02 * Math.sin(2 * M * RD) + 0.0003 * Math.sin(3 * M * RD);
  const L = (M + C + 180 + 102.9372) % 360;
  const jt = 2451545 + js + 0.0053 * Math.sin(M * RD) - 0.0069 * Math.sin(2 * L * RD);
  const sd = Math.sin(L * RD) * Math.sin(23.4397 * RD);
  const cd = Math.cos(Math.asin(sd));
  const w = Math.acos((Math.sin(-0.833 * RD) - Math.sin(lat * RD) * sd) / (Math.cos(lat * RD) * cd)) / RD;
  const toMs = (j) => (j - 2440587.5) * 864e5;
  return [toMs(jt - w / 360), toMs(jt + w / 360)];
}

const parts = new Intl.DateTimeFormat('en-US', {
  timeZone: SOMERVILLE.tz, year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

/** Wall-clock date and time in Somerville for a UTC ms instant. */
export function wall(ms) {
  const o = {};
  parts.formatToParts(new Date(ms)).forEach((p) => (o[p.type] = p.value));
  return { y: +o.year, m: +o.month, d: +o.day, h: +o.hour % 24, mi: +o.minute };
}

/** UTC ms for a Somerville wall-clock date and time (handles daylight saving time). */
export function zoned(y, m, d, h, mi) {
  let g = Date.UTC(y, m - 1, d, h, mi);
  for (let i = 0; i < 2; i++) {
    const w = wall(g);
    const diff = Date.UTC(w.y, w.m - 1, w.d, w.h, w.mi) - g;
    g = Date.UTC(y, m - 1, d, h, mi) - diff;
  }
  return g;
}

/**
 * When must the sidewalk be clear?
 * @param {number} stop  UTC ms when the snow stopped
 * @returns {{end:number, days:Array}} end = deadline (UTC ms); days = per-day daylight and counted span
 */
export function deadline(stop, hours = DAYLIGHT_HOURS) {
  let rem = hours * HOUR;
  let t = stop;
  const days = [];
  for (let i = 0; i < 5 && rem > 0; i++) {
    const w = wall(t);
    const [rise, set] = sunTimes(w.y, w.m, w.d);
    const day = { y: w.y, m: w.m, d: w.d, rise, set, from: null, to: null, stop: i === 0 ? stop : null };
    if (t < rise) t = rise;
    if (t < set) {
      const avail = set - t;
      day.from = t;
      if (rem <= avail) { day.to = t + rem; rem = 0; } else { day.to = set; rem -= avail; }
    }
    days.push(day);
    if (rem > 0) {
      const next = wall(zoned(w.y, w.m, w.d, 12, 0) + 864e5);
      t = zoned(next.y, next.m, next.d, 0, 1);
    }
  }
  return { end: days[days.length - 1].to, days };
}
