import { test } from 'node:test';
import assert from 'node:assert/strict';
import { metarSnow, interval, liveState, demoInput } from '../docs/js/live.js';

test('METAR: falling snow counts, blowing snow and remarks do not', () => {
  assert.equal(metarSnow('KBOS 230654Z 03028G40KT 1/4SM +SN FZFG VV005 M03/M04 A2950'), true);
  assert.equal(metarSnow('KBOS 230254Z 03023KT 1SM -SN BR OVC008 01/M01 A2960'), true);
  assert.equal(metarSnow('KBOS 230254Z 03023KT 3SM -SHSN BKN020 01/M01 A2960'), true);
  assert.equal(metarSnow('KBOS 240254Z 33025G35KT 10SM BLSN FEW030 M05/M14 A2990'), false);
  assert.equal(metarSnow('KBOS 240254Z 33015KT 10SM FEW030 M05/M14 A2990 RMK AO2 SNE15'), false);
  assert.equal(metarSnow('KBOS 312254Z 35005KT 10SM BKN200 11/M04 A3040 RMK AO2'), false);
  assert.equal(metarSnow(''), false);
});

test('NWS intervals', () => {
  const [a, b] = interval('2026-02-22T21:00:00+00:00/PT3H');
  assert.equal(b - a, 3 * 36e5);
  const [c, d] = interval('2026-10-31T13:00:00+00:00/P3DT11H');
  assert.equal(d - c, (3 * 24 + 11) * 36e5);
});

test('quiet with no snow anywhere', () => {
  assert.equal(liveState({ now: Date.UTC(2026, 10, 1, 12), obs: [], snowfall: [], alerts: [] }).phase, 'quiet');
});

test('each demo lands in its phase', () => {
  const now = Date.UTC(2027, 0, 15, 15); // 10 a.m. in Somerville
  for (const k of ['forecast', 'snowing', 'stopped', 'passed']) assert.equal(liveState(demoInput(k, now)).phase, k, k);
});

test('stopped: deadline is 6 daylight hours after the snow stopped', () => {
  const now = Date.UTC(2027, 0, 15, 15);
  const s = liveState(demoInput('stopped', now));
  assert.ok(s.deadline > s.stop);
  assert.ok(s.deadline > now);
});

test('forecast: inches add up over consecutive snowy intervals only', () => {
  const now = Date.UTC(2027, 0, 15, 15); const h = (n) => now + n * 36e5;
  const s = liveState({ now, obs: [], alerts: [], snowfall: [{ from: h(2), to: h(5), mm: 25.4 }, { from: h(5), to: h(8), mm: 25.4 }, { from: h(30), to: h(33), mm: 254 }] });
  assert.equal(s.phase, 'forecast');
  assert.equal(s.inches, 2);
  assert.equal(s.forecastStart, h(2));
});

test('a passing flurry does not start the clock', () => {
  const now = Date.UTC(2027, 0, 15, 15); const h = (n) => now + n * 36e5;
  const obs = [{ t: h(-5), snow: false }, { t: h(-4), snow: true }, { t: h(-3), snow: false }, { t: h(-1), snow: false }];
  assert.equal(liveState({ now, obs, snowfall: [], alerts: [] }).phase, 'quiet');
});
