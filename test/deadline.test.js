import { test } from 'node:test';
import assert from 'node:assert/strict';
import { deadline, sunTimes, wall, zoned } from '../docs/snow/js/deadline.js';

const at = (ms) => { const w = wall(ms); return `${w.m}/${w.d} ${String(w.h).padStart(2, '0')}:${String(w.mi).padStart(2, '0')}`; };
const near = (ms, expected, tolMin = 3) => {
  const [md, hm] = expected.split(' ');
  const [m, d] = md.split('/').map(Number);
  const [h, mi] = hm.split(':').map(Number);
  const want = zoned(new Date(ms).getUTCFullYear(), m, d, h, mi);
  assert.ok(Math.abs(ms - want) <= tolMin * 6e4, `got ${at(ms)}, expected about ${expected}`);
};

test('sunrise and sunset in Somerville match published times (within 3 min)', () => {
  const [rise, set] = sunTimes(2027, 1, 15);
  near(rise, '1/15 07:11');
  near(set, '1/15 16:36');
  const [r2, s2] = sunTimes(2026, 12, 21);
  near(r2, '12/21 07:10');
  near(s2, '12/21 16:15');
});

test('snow stops at 3 p.m. in January: the clock pauses overnight', () => {
  const r = deadline(zoned(2027, 1, 15, 15, 0));
  near(r.end, '1/16 11:34');
  assert.equal(r.days.length, 2);
});

test('snow stops overnight: 6 hours from sunrise', () => {
  near(deadline(zoned(2027, 1, 15, 2, 0)).end, '1/15 13:11');
});

test('snow stops in the morning: done the same afternoon', () => {
  near(deadline(zoned(2027, 1, 15, 9, 0)).end, '1/15 15:00', 1);
});

test('snow stops after sunset: the clock starts the next morning', () => {
  near(deadline(zoned(2027, 1, 15, 19, 0)).end, '1/16 13:11');
});

test('daylight saving time is handled (March 14, 2027 starts DST)', () => {
  const r = deadline(zoned(2027, 3, 13, 22, 0));
  const w = wall(r.end);
  assert.equal(w.d, 14);
  assert.ok(w.h >= 12 && w.h <= 14, `got ${at(r.end)}`);
});
