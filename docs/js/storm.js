/* Storm replay (docs/storms/<id>.html): one past storm, hour by hour.
   Each page is written ahead of time by scripts/build_pages.py, with its data embedded as JSON (#storm-data):
   this script only draws and animates. The deadline uses the guide's own calculator.
   The left column sketches what the guide could show at each hour ("storm mode"); the City notices are quoted. */
import { deadline, sunTimes, wall, zoned } from './deadline.js';

const $ = (s) => document.querySelector(s);
const HOUR = 36e5;
const TZ = 'America/New_York';
const GROUP = {
  sidewalk: { label: 'Sidewalk not shoveled', color: '#FF8A3D' },
  street: { label: 'Plow, salt or snow removal', color: '#A9C4E4' },
  ask: { label: 'Snow emergency and parking questions', color: '#3B82F6' },
  spacesaver: { label: 'Space savers', color: '#F4C95D' },
  feedback: { label: 'Feedback', color: '#47607C' },
};

const { storm: S, wards: WARD_LIST, survey: SURVEY, bus: BUS, holidays: HOLIDAYS = {} } = JSON.parse($('#storm-data').textContent);
// holidays in the window (New Year, Christmas…): the T and the streets empty on their own, so the lanes name them
const holidayOf = (t) => { const w = wall(t); return HOLIDAYS[`${w.y}-${String(w.m).padStart(2, '0')}-${String(w.d).padStart(2, '0')}`]; };
const WARDS = { wards: WARD_LIST };
const X = S.extra || {};

/* ---------- time helpers (all instants are UTC ms; the data's hours are Somerville wall-clock) ---------- */
const ms = (iso) => { const [d, t = '00:00'] = iso.split('T'); const [y, m, dd] = d.split('-').map(Number); const [h, mi] = t.split(':').map(Number); return zoned(y, m, dd, h, mi); };
const naive = (iso) => { const [d, t = '00:00'] = iso.split('T'); const [y, m, dd] = d.split('-').map(Number); const [h, mi] = t.split(':').map(Number); return Date.UTC(y, m - 1, dd, h, mi); };
const N0 = naive(S.from);
const N = S.hours.length;
const tOf = (i) => { const g = new Date(N0 + i * HOUR); return zoned(g.getUTCFullYear(), g.getUTCMonth() + 1, g.getUTCDate(), g.getUTCHours(), 0); };
const idxOf = (t) => { const w = wall(t); return (Date.UTC(w.y, w.m - 1, w.d, w.h, w.mi) - N0) / HOUR; };
const fmt = (t, o) => new Intl.DateTimeFormat('en-US', { timeZone: TZ, ...o }).format(t);
const tm = (t) => fmt(t, { hour: 'numeric', minute: '2-digit' }).replace(':00', '').replace('AM', 'a.m.').replace('PM', 'p.m.');
const dayTm = (t) => `${fmt(t, { weekday: 'short' })} ${tm(t)}`;
const dur = (d) => { const h = Math.floor(d / HOUR); const m = Math.round((d % HOUR) / 6e4); return h ? `${h} h ${m} min` : `${m} min`; };

/* ---------- the storm's key moments ---------- */
// What the City announced. Any of these can be missing: some storms have no notice online, some only the start or the end.
const E = Object.fromEntries(Object.entries(S.emergency || {}).map(([k, v]) => [k, typeof v === 'string' && v.includes('T') ? ms(v) : v]));
const has = (k) => typeof E[k] === 'number';
const SIDE = (E.side || '').toUpperCase();
const sideTxt = SIDE ? `the ${SIDE} side` : 'the posted side';
// A snow period can hold several snowfalls: each has its own start, stop and shoveling deadline. The page-wide
// deadline (map text, emergency end) is the one for the period's biggest snowfall.
const FALLS = (S.snowfalls && S.snowfalls.length ? S.snowfalls : [{ start: S.snowStart, stop: S.snowStop, snow: S.snowTotal }])
  .map((f) => { const stop = ms(f.stop); const d = deadline(stop); return { start: ms(f.start), stop, snow: f.snow, DL: d.end, clockFrom: d.days.find((x) => x.from).from }; });
const MAIN = FALLS.reduce((a, f) => (f.snow > a.snow ? f : a), FALLS[0]);
const fallAt = (t) => FALLS.filter((f) => f.start <= t).pop() || FALLS[0];
const snowStart = FALLS[0].start;
const snowStop = MAIN.stop;
const DL = MAIN.DL;
const CLEAR = S.clear ? zoned(...S.clear.split('-').map(Number), 0, 0) : null; // the day sidewalk reports died down
const cityDL = S.cityDeadline ? ms(S.cityDeadline) : null;
const notices = (S.notices || []).map((n) => ({ ...n, at: ms(n.t) }));
const declared = notices[0]?.at ?? (has('start') ? E.start - 24 * HOUR : snowStart);
// When we know the emergency was on: from its start (or the City's notice about it) to its end (or, if the end isn't known, the shoveling deadline).
const emOn = has('moveBy') ? E.moveBy : has('start') ? E.start : (S.emergency && notices.length ? notices[0].at : null);
const emOff = has('end') ? E.end : DL;

/* ---------- requests, cumulative by hour ---------- */
const groups = S.groups;
const reqAt = (i) => S.requests[i] || groups.map(() => 0);
const cum = [];
const wardCum = [];
{
  let c = groups.map(() => 0);
  let w = {};
  for (let i = 0; i < N; i++) {
    c = c.map((v, k) => v + reqAt(i)[k]);
    w = { ...w };
    Object.entries(S.sidewalkByWard[i] || {}).forEach(([k, v]) => { w[k] = (w[k] || 0) + v; });
    cum.push(c);
    wardCum.push(w);
  }
}
const gi = (g) => groups.indexOf(g);
// Refreezing: at or below 32°F within 12 hours after it was 34°F or warmer, from the first snow on.
const REFREEZE = S.hours.map((h, k) => {
  if (h[1] == null || h[1] > 32 || tOf(k) < snowStart) return false;
  for (let j = Math.max(0, k - 12); j < k; j++) if (S.hours[j][1] != null && S.hours[j][1] >= 34) return true;
  return false;
});
// Counters and the map count this storm only: from the first snowy hour (earlier reports belong to earlier snow).
const BASE = Math.max(0, Math.floor(idxOf(snowStart)));
const since = (i) => (i < BASE ? groups.map(() => 0) : cum[i].map((v, k) => v - (BASE ? cum[BASE - 1][k] : 0)));
const wardSince = (i) => { if (i < BASE) return {}; const a = wardCum[i]; const b = BASE ? wardCum[BASE - 1] : {}; return Object.fromEntries(Object.keys(a).map((k) => [k, a[k] - (b[k] || 0)])); };

/* ---------- what the guide would say at time t ---------- */
function messages(t, i) {
  const out = [];
  const add = (cls, icon, b, s, big, k) => out.push({ cls: cls && `m-${cls}`, icon, b, s: s.replace(/\.\.(?=$|\s|<)/g, '.'), big, k });
  const h = S.hours[Math.max(0, Math.min(N - 1, i))] || [];
  (X.warnings || []).forEach((w) => { if (t >= ms(w.from) && t < ms(w.to)) add('warn', 'snow', w.name, `National Weather Service, until ${dayTm(ms(w.to))}.`); });
  notices.forEach((n) => { if (t >= n.at && t < n.at + 20 * HOUR) add('city', 'city', `City · ${n.approx ? fmt(n.at, { weekday: 'short', month: 'short', day: 'numeric' }) : dayTm(n.at)}`, `${n.text} <a href="${n.src}">Read it</a>`); });

  const F = fallAt(t); // the snowfall this hour belongs to
  if (t < Math.min(declared, snowStart)) {
    add('now', 'snow', 'Snow on the way', 'Buy salt or sand now. Stores run out.');
    add('', 'phone', 'Get City Alerts', 'somervillema.gov/alerts');
  } else if (has('start') && t < E.start) {
    add('em', 'car', `Snow emergency ${dayTm(E.start)}`, `Then 4 hours to move to ${sideTxt}, or into a City lot.`);
    add('now', 'bag', 'Salt before it starts', 'It stops snow from sticking.');
  } else if (has('start') && has('moveBy') && t < E.moveBy) {
    add('em', 'car', 'Move your car', `${SIDE ? `${SIDE} side` : 'The posted side'} or a City lot by ${tm(E.moveBy)}.`, `${dur(E.moveBy - t)} left`);
  } else if (emOn != null && t >= emOn && t < emOff) {
    add('em', 'car', 'Snow emergency on', `Park on ${sideTxt}. Not within 20 feet of a corner.`);
  }

  if (has('start') && t >= E.start && t < snowStart) add('now', 'bag', 'Salt now', 'Snow is coming. Salt stops it from sticking.');
  if (t >= F.start && t < F.stop) {
    add('now', 'snow', h[0] === 3 ? 'Heavy snow' : F !== FALLS[0] ? 'Snowing again' : 'Snowing', 'The 6-hour clock starts when it stops. Night doesn\'t count.', undefined, 'snowing');
  }
  if (t >= F.stop && t < F.clockFrom) {
    add('now', 'clock', 'Snow stopped', `Night doesn't count. The clock starts at sunrise, ${tm(F.clockFrom)}.`, `Shovel by ${dayTm(F.DL)}`);
  }
  if (t >= F.clockFrom && t < F.DL) {
    add('now', 'shovel', 'Shovel now', '36 inches wide. Down to the pavement. Open the ramp.', `${dur(F.DL - t)} left`);
  }
  if (t >= F.DL && t < F.DL + 30 * HOUR) {
    add('warn', 'phone', 'Deadline passed', `It was ${dayTm(F.DL)}${cityDL && F === MAIN ? ` (the City said ${tm(cityDL)})` : ''}. Still buried? Report it: 311.`);
  }
  if (REFREEZE[i] && t >= FALLS[0].stop) add('warn', 'ice', 'Refreezing now', 'It went above freezing, now it is back below. Meltwater turns to ice: salt or sand.');
  else if (t >= F.DL) add('', 'ice', 'Check for ice', 'Meltwater refreezes overnight. Sand or salt it.');
  if (has('end') && t >= E.end) {
    if (has('lotsBy') && t < E.lotsBy) add('em', 'car', 'Emergency over', `Out of City lots by ${dayTm(E.lotsBy)}.`);
    else if (has('permitsBy') && t < E.permitsBy) add('em', 'car', 'Permit visible', `Clear your parking permit by ${dayTm(E.permitsBy)}.`);
    else if (has('carsBy') && t < E.carsBy) add('em', 'car', 'Dig out your car', `Fully cleared by ${dayTm(E.carsBy)}.`);
  }
  if (t >= (has('end') ? E.end : DL)) add('', 'ban', 'Space savers', 'Banned. $100. Thrown out.');
  // the latest MBTA alert on a Somerville route or station in the past 6 hours (delays, detours, cuts, elevators)
  const al = (X.alerts || []).filter(([k]) => k <= i && k > i - 6).pop();
  // last, so an alert coming and going never pushes a rule card out of the panel (and makes it blink)
  if (al) out.push({ k: 'mbta', cls: 'm-t', icon: 'bus', b: `MBTA · ${al[2].replace(/^Green-/, 'Green Line ')}`, s: al[3] });
  return out.slice(0, 5);
}

// Each card is kept by its kind and title: a card that stays only updates its text (a countdown ticking), a new card
// grows in, and a card that's no longer true shrinks away. Nothing else moves, so playing doesn't make the panel blink.
const msgKey = (m) => m.k || `${m.cls}|${m.icon}|${m.b}`; // a card can name itself (snowing, MBTA) to update in place
const msgInner = (m) => `<svg class="ico" aria-hidden="true"><use href="#i-${m.icon}"/></svg><b>${m.b}</b><span>${m.big ? `<span class="big">${m.big}</span><br>` : ''}${m.s}</span>`;
const calm = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
function renderMessages(t, i, instant = true) {
  const box = $('#msgs'); const list = messages(t, i);
  if (instant || calm) {
    box.innerHTML = list.map((m) => `<div class="msg ${m.cls}" data-k="${attr(msgKey(m))}">${msgInner(m)}</div>`).join('');
    return;
  }
  const keep = new Map([...box.children].filter((el) => !el.classList.contains('leaving')).map((el) => [el.dataset.k, el]));
  const want = list.map((m) => {
    const k = msgKey(m); let el = keep.get(k);
    if (el) { keep.delete(k); const html = msgInner(m); if (el.dataset.h !== html) { el.innerHTML = html; el.dataset.h = html; } return [el, false]; }
    el = document.createElement('div'); el.className = `msg ${m.cls}`; el.dataset.k = k; el.innerHTML = el.dataset.h = msgInner(m);
    return [el, true];
  });
  keep.forEach((el) => { // no longer true: shrink away where it is
    el.classList.add('leaving');
    const h = el.offsetHeight;
    el.animate([{ opacity: 1, height: `${h}px`, marginBottom: '10px' }, { opacity: 0, height: '0px', marginBottom: '0px', paddingTop: '0px', paddingBottom: '0px' }], { duration: 260, easing: 'ease-in' })
      .onfinish = () => el.remove();
  });
  let cursor = box.firstElementChild; // place the cards in order, leaving the shrinking ones where they are
  want.forEach(([el, isNew]) => {
    while (cursor && cursor.classList.contains('leaving')) cursor = cursor.nextElementSibling;
    if (el === cursor) { cursor = cursor.nextElementSibling; return; }
    box.insertBefore(el, cursor);
    if (isNew) {
      const h = el.offsetHeight;
      el.animate([{ opacity: 0, height: '0px', marginBottom: '0px', paddingTop: '0px', paddingBottom: '0px', transform: 'translateX(-12px)' }, { opacity: 1, height: `${h}px`, marginBottom: '10px', transform: 'none' }], { duration: 300, easing: 'ease-out' });
    }
  });
}

// The number of message cards changes hour by hour. Reserve the tallest the phone ever gets, so scrubbing
// never changes its height and nothing on the page jumps (on phones the chart sits right below it).
// The line under the map's second number changes text while dragging; keep room for its longest version so the
// page below never jumps.
function lockLateHeight() {
  const el = $('#m-late-l'); const keep = el.textContent; el.style.minHeight = '';
  let h = 0;
  for (const txt of ['The snow hasn\'t started yet. Press play or drag the line.', `came after the ${tm(DL)} deadline (8888 before it)`, `came after the deadline (it's ${dayTm(DL)})`]) {
    el.textContent = txt; h = Math.max(h, el.offsetHeight);
  }
  el.textContent = keep; el.style.minHeight = `${h}px`;
  // the counters under the lanes name a holiday when the line is on one; keep room for that longer label too
  const t2 = $('#tally2'); t2.style.minHeight = '';
  const hol = Array.from({ length: N }, (_, k) => k).find((k) => holidayOf(tOf(k)));
  if (hol != null) { const cur = +scrub.value; render(hol); const hh = t2.offsetHeight; render(cur); t2.style.minHeight = `${Math.max(hh, t2.offsetHeight)}px`; }
}

function lockPhoneHeight() {
  const box = $('#msgs'); const phone = $('.phone');
  const cur = +scrub.value;
  phone.style.minHeight = ''; phone.style.height = ''; box.style.maxHeight = ''; box.classList.remove('scrolls');
  const hs = [];
  for (let i = 0; i < N; i++) { renderMessages(tOf(i + 1), i); hs.push(box.offsetHeight); }
  const cs = getComputedStyle(phone);
  const extra = parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom) + parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth) + 10;
  const mx = Math.max(...hs);
  // The box sits beside the title (above it on phones): fit 80% of the hours, or the height of the intro next to it
  // if that's taller, and let the rare busiest hours scroll inside it, so the page never jumps.
  const intro = $('.r-intro'); const side = window.innerWidth > 900 && intro ? intro.offsetHeight - 40 - extra : 0;
  const q = window.innerWidth > 900 ? 0.8 : 0.5; // phones: room for a typical hour, the slider stays close below
  const fit = Math.max(200, side, [...hs].sort((a, b) => a - b)[Math.floor(hs.length * q)]);
  if (fit < mx) { box.style.maxHeight = `${fit}px`; box.classList.add('scrolls'); }
  phone.style.height = `${Math.ceil(Math.min(mx, fit) + extra)}px`;
  renderMessages(tOf(cur + 1), cur);
}

/* ---------- timeline chart ---------- */
// Drawn at the panel's real pixel width (measured in buildChart), so text keeps its size on phones instead of
// shrinking with a desktop-sized drawing.
let CW = 900; const PAD = 8; const TOP = 56; const SNOW_H = 54; const REQ_TOP = TOP + SNOW_H + 14; const REQ_H = 170; const BOT = REQ_TOP + REQ_H;
const xOf = (i) => PAD + (i / N) * (CW - 2 * PAD);
let bw = (CW - 2 * PAD) / N;
const maxReq = Math.max(1, ...Array.from({ length: N }, (_, i) => reqAt(i).reduce((a, b) => a + b, 0)));
function buildChart() {
  CW = Math.max(300, Math.round($('#chart').clientWidth || 900)); bw = (CW - 2 * PAD) / N;
  const wideC = CW >= 620;
  let s = `<svg viewBox="0 0 ${CW} ${BOT + 26}" width="${CW}" height="${BOT + 26}" role="img" aria-label="Hour-by-hour timeline: snowfall intensity at Logan, and 311 snow requests stacked by type">`;
  // night shading
  for (let i = 0; i < N; i++) {
    const t = tOf(i); const w = wall(t);
    const [rise, set] = sunOf(w);
    const night = t + HOUR / 2 < rise || t + HOUR / 2 > set;
    if (night) s += `<rect x="${xOf(i)}" y="${TOP}" width="${bw + 0.5}" height="${BOT - TOP}" fill="#0E2238"/>`;
  }
  // day labels at local noon
  // long periods: label every 2nd, 3rd… day so the labels never run together
  const every = Math.max(1, Math.ceil((wideC ? 62 : 40) / (24 * (CW - 2 * PAD) / N)));
  for (let i = 0, nd = 0; i < N; i++) { const w = wall(tOf(i)); if (w.h === 12 && (nd++ % every === 0) && xOf(i) > 20 && xOf(i) < CW - 20) s += `<text x="${xOf(i)}" y="${BOT + 20}" text-anchor="middle" class="cap" font-size="${wideC ? 15 : 13}" fill="#A9C4E4">${every > 1 && !wideC ? `${w.m}/${w.d}` : `${fmt(tOf(i), { weekday: 'short' }).toUpperCase()}${wideC ? ` ${w.d}` : ''}`}</text>`; }
  // snow intensity
  S.hours.forEach((h, i) => { if (h[0]) s += `<rect x="${xOf(i)}" y="${TOP + SNOW_H - h[0] * 17}" width="${bw + 0.4}" height="${h[0] * 17}" fill="#fff" opacity="${0.35 + h[0] * 0.2}"/>`; });
  (X.warnings || []).forEach((w) => {
    const a = Math.max(0, idxOf(ms(w.from))); const b = Math.min(N, idxOf(ms(w.to)));
    if (b > a) s += `<rect x="${xOf(a)}" y="${TOP + SNOW_H + 3}" width="${xOf(b) - xOf(a)}" height="7" rx="3" fill="${NWS[w.code] || '#C084FC'}"><title>${w.name}</title></rect>`;
  });
  s += `<text x="${PAD + 4}" y="${TOP + 14}" class="cap" font-size="13" fill="#A9C4E4">SNOW AT LOGAN</text>`;
  if (X.snowSomerville) {
    const txt = wideC ? `SOMERVILLE OBSERVERS: ${X.snowSomerville.total} IN${X.snowSomerville.partial ? ' (PARTIAL REPORT)' : ''}` : `SOMERVILLE: ${X.snowSomerville.total} IN${X.snowSomerville.partial ? ' (PARTIAL)' : ''}`;
    s += wideC ? `<text x="${CW - PAD - 4}" y="${TOP + 14}" text-anchor="end" class="cap" font-size="13" fill="#A9C4E4">${txt}</text>`
      : `<text x="${PAD + 4}" y="${TOP + 30}" class="cap" font-size="12" fill="#A9C4E4">${txt}</text>`; // phones: under "Snow at Logan"
  }
  s += `<text x="${PAD + 4}" y="${REQ_TOP + 14}" class="cap" font-size="13" fill="#A9C4E4">311 REQUESTS PER HOUR</text>`;
  // requests, stacked (sidewalk on the bottom)
  const order = ['sidewalk', 'street', 'ask', 'spacesaver', 'feedback'];
  for (let i = 0; i < N; i++) {
    let y = BOT;
    order.forEach((g) => { const v = reqAt(i)[gi(g)] || 0; if (!v) return; const hh = (v / maxReq) * REQ_H; y -= hh; s += `<rect x="${xOf(i)}" y="${y}" width="${Math.max(1, bw - 0.6)}" height="${hh}" fill="${GROUP[g].color}"/>`; });
  }
  // markers
  // every snowfall gets its lines; the period's biggest one is labeled "Snow stops", later ones "More snow"
  const marks = [[E.start, 'Emergency', '#3B82F6'], [snowStart, 'Snow starts', '#fff'], [E.end, 'Emergency ends', '#3B82F6'], [CLEAR, 'Reports die down', '#7FD4C1']];
  FALLS.forEach((f, k) => { // only the biggest snowfall's moments are labeled; the others keep their lines
    if (k > 0) marks.push([f.start, FALLS.length === 2 && f.start > MAIN.stop ? 'More snow' : '', '#fff']);
    marks.push([f.stop, f === MAIN ? 'Snow stops' : '', '#fff']);
    marks.push([f.DL, f === MAIN ? 'Deadline' : '', '#FF8A3D']);
  });
  marks.splice(0, marks.length, ...marks.filter(([t]) => typeof t === 'number' && idxOf(t) >= 0 && idxOf(t) <= N));
  // Marker lines and labels; labelMarkers() places the labels once they can be measured (no overlaps).
  marks.forEach(([t, label, c]) => {
    const x = xOf(idxOf(t));
    s += `<path class="mk-line" data-x="${x}" d="M${x} ${TOP - 4} V${BOT}" stroke="${c}" stroke-width="${label === 'Deadline' ? 3 : 2}" ${c === '#FF8A3D' ? '' : 'stroke-dasharray="5 5"'}${c === '#FF8A3D' && label !== 'Deadline' ? ' opacity=".7"' : ''}/>`;
    if (label) s += `<text class="mk cap" data-x="${x}" x="${x + 4}" y="14" font-size="${wideC ? 14 : 12}" fill="${c}">${label.toUpperCase()}</text>`;
  });
  s += `<rect id="future" x="0" y="${TOP}" width="0" height="${BOT - TOP + 2}" fill="#1A3A5F" opacity=".78"/>`;
  s += `<path id="head" d="M0 ${TOP - 6} V${BOT + 4}" stroke="#fff" stroke-width="2.5"/>`;
  s += `<g id="knob"><circle r="11" fill="#FF8A3D" stroke="#fff" stroke-width="3"/><path d="M-3 -4 V4 M3 -4 V4" stroke="#10243A" stroke-width="2" stroke-linecap="round"/></g>`;
  s += '</svg>';
  $('#chart').innerHTML = s;
  labelMarkers();
  const seen = new Set();
  const warnLegend = (X.warnings || []).filter((w) => !seen.has(w.name) && seen.add(w.name)).map((w) => `<span><i style="background:${NWS[w.code] || '#C084FC'}"></i>${w.name}</span>`).join('');
  $('#legend').innerHTML = ['sidewalk', 'street', 'ask', 'spacesaver'].map((g) => `<span><i style="background:${GROUP[g].color}"></i>${GROUP[g].label}</span>`).join('') + '<span><i style="background:#0E2238"></i>Night</span>' + warnLegend;
}
// National Weather Service map colors for winter products
const NWS = { 'BZ.W': '#FF4500', 'WS.W': '#FF69B4', 'WS.A': '#4682B4', 'WW.Y': '#7B68EE', 'WC.Y': '#AFEEEE', 'WC.W': '#B0C4DE', 'EC.W': '#0000FF', 'HW.W': '#DAA520', 'WI.Y': '#D2B48C' };
// Put each marker label in the first free spot: three rows, to the right of its line, else to the left.
function labelMarkers() {
  const ROWS = [14, 30, 46]; const placed = [];
  const free = (row, a, b) => a >= 0 && b <= CW && placed.every((p) => p.row !== row || b + 6 <= p.a || a >= p.b + 6);
  // most important first, so the deadline always gets a spot; on a phone a label with no free spot is left out (the
  // buttons under the slider name the same moments)
  const PRI = ['DEADLINE', 'SNOW STOPS', 'REPORTS DIE DOWN', 'SNOW STARTS', 'MORE SNOW', 'EMERGENCY', 'EMERGENCY ENDS'];
  const items = [...document.querySelectorAll('#chart .mk')].sort((m1, m2) => PRI.indexOf(m1.textContent) - PRI.indexOf(m2.textContent));
  items.forEach((el) => {
    el.style.display = '';
    const x = +el.dataset.x; const w = el.getComputedTextLength ? el.getComputedTextLength() : el.textContent.length * 10;
    let spot = null;
    for (const row of [0, 1, 2]) {
      if (free(row, x + 4, x + 4 + w)) { spot = [row, x + 4, x + 4 + w, 'start']; break; }
      if (free(row, x - 4 - w, x - 4)) { spot = [row, x - 4 - w, x - 4, 'end']; break; }
    }
    const line = [...document.querySelectorAll('#chart .mk-line')].find((l) => l.dataset.x === el.dataset.x);
    if (!spot && CW < 620) { el.style.display = 'none'; if (line) line.setAttribute('d', `M${x} ${TOP - 4} V${BOT}`); return; }
    spot = spot || [2, x + 4, x + 4 + w, 'start'];
    const [row, a, b, anchor] = spot;
    placed.push({ row, a, b });
    el.setAttribute('y', ROWS[row]); el.setAttribute('x', anchor === 'start' ? x + 4 : x - 4); el.setAttribute('text-anchor', anchor);
    if (line) line.setAttribute('d', `M${x} ${ROWS[row] + 4} V${BOT}`);
  });
}
const sunCache = {};
function sunOf(w) {
  const k = `${w.y}-${w.m}-${w.d}`;
  if (!sunCache[k]) sunCache[k] = sunTimes(w.y, w.m, w.d);
  return sunCache[k];
}

/* ---------- getting around: lanes on the same time axis as the chart ---------- */
// Drawn at the panel's real pixel width (not scaled down like the main chart), so the text stays readable on phones.
const LABEL = 24; const STRIP = 40; const GAP = 14; const LH = LABEL + STRIP + GAP;
const ALERT = { delay: '#F4C95D', detour: '#FF8A3D', reduced: '#FF6B6B', access: '#C084FC', other: '#A9C4E4' };
const LANES = [
  { key: 'tEntries', label: 'T entries at Somerville stations', note: 'bars: this week · line: a normal week', color: '#A9C4E4', kind: 'vsBase', from: 'no T entry counts' },
  { key: 'busTrips', label: 'Buses run on Somerville routes', note: 'bars: bus trips started each hour (buses, not riders) · line: a normal week', color: '#7FD4C1', kind: 'vsBase', from: 'MBTA bus records start in 2020' },
  { key: 'busLate', label: 'How late the buses ran', note: 'median minutes late · line: a normal week', color: '#FF6B6B', kind: 'late', from: 'MBTA bus records start in 2020' },
  { key: 'busSpeed', label: 'How much slower the buses moved', note: 'bars: % slower than a normal week, same hour (taller = slower; none = normal)', color: '#5EEAD4', kind: 'slow', unit: 'bus runs timed', few: false, from: 'MBTA bus records start in 2020' },
  { key: 'subway', label: 'How much slower the T ran in Somerville', note: 'bars: % slower than usual (taller = slower) · red: under half the usual trains', color: '#7DD3FC', kind: 'slow', from: 'MBTA travel times start in 2021' },
  { key: 'bikes', label: 'Bluebikes trips from Somerville', note: 'bars: this week · line: a normal week', color: '#F4C95D', kind: 'vsBase', from: 'no Bluebikes data, or too few trips from Somerville that winter' },
  { key: 'spending', label: 'Card spending, Middlesex County', note: 'per day vs. the 4 weeks before · 7-day average', color: '#F59E0B', kind: 'change', from: 'daily county spending data covers 2020 to early 2022' },
  { key: 'web', label: 'Views of the City\'s snow pages', note: 'per day · line: a normal day', color: '#C084FC', kind: 'daily', from: 'the City\'s page-view data covers 2020 to May 2023' },
  { key: 'tows', label: 'Snow emergency tows (police)', note: 'per 8-hour shift', color: '#3B82F6', kind: 'shift', from: 'police dispatch data starts in 2017' },
  { key: 'parking', label: 'Parking calls to 311', note: 'illegal parking, towed cars', color: '#7FA7F5', kind: 'hourly' },
  { key: 'alerts', label: 'MBTA alerts, Somerville routes', note: 'yellow delay · orange detour · red cuts · purple elevator', kind: 'ticks', from: 'the MBTA alerts archive starts in 2020' },
  { key: 'thaw', label: 'Melt and refreeze', note: 'line: temperature · dashes: 32°F · blue: freezing again after a thaw · bars: salting requests', kind: 'thaw' },
  { key: 'crashes', label: 'Crashes', note: 'orange: pedestrian or cyclist · large: someone hurt · tap for details', kind: 'dots', from: 'crash data starts in March 2018' },
  { key: 'fireEms', label: 'Medical calls (Fire Dept.)', note: 'bars: this week · line: a normal week', color: '#F87171', kind: 'vsBase', from: 'Fire Department records cover 2019–2025 (none were filed Feb 25–28 and Dec 10–15, 2022)' },
  { key: 'fireEvents', label: 'Wires down, carbon monoxide, crashes', note: 'yellow wires · purple CO · red crash (Fire Dept.) · tap for details', kind: 'events', from: 'Fire Department records cover 2019–2025 (none were filed Feb 25–28 and Dec 10–15, 2022)' },
];
let LW = CW; // lanes width in px, measured when built
const lx = (i) => PAD + (i / N) * (LW - 2 * PAD);
const lbw = () => (LW - 2 * PAD) / N;
function laneData(key) {
  if (key === 'tows') return X.police ? X.police.tows : null;
  if (key === 'parking') return X.calls311 ? X.calls311.parking : null;
  if (key === 'busTrips') return X.buses ? X.buses.trips : null;
  if (key === 'thaw') return S.hours.some((h) => h[1] != null) ? { temps: S.hours.map((h) => h[1]), salting: S.salting || [] } : null;
  if (key === 'busLate') return X.buses ? X.buses.late : null;
  if (key === 'busSpeed') return X.buses ? X.buses.speed || null : null;
  if (key === 'fireEms') return X.fire ? X.fire.ems : null;
  if (key === 'fireEvents') return X.fire ? X.fire.events : null;
  return X[key] ?? null;
}
function buildLanes() {
  LW = Math.max(300, Math.round($('#lanes').clientWidth || CW));
  const wide = LW >= 620;
  const bw_ = lbw();
  const H = LANES.length * LH + 18;
  // On narrow screens the note wraps after its first sentence, so it never spills out of the strip.
  const msg = (y, text) => {
    const cut = text.indexOf(': ');
    if (wide || text.length * 6.6 < LW - 2 * PAD || cut < 0) return `<text x="${LW / 2}" y="${y}" text-anchor="middle" font-size="13" fill="#9DB2CA">${text}</text>`;
    return `<text x="${LW / 2}" y="${y - 8}" text-anchor="middle" font-size="12" fill="#9DB2CA">${text.slice(0, cut + 1)}<tspan x="${LW / 2}" dy="15">${text.slice(cut + 2)}</tspan></text>`;
  };
  let s = `<svg viewBox="0 0 ${LW} ${H}" width="${LW}" height="${H}" role="img" aria-label="How the city got around during the storm: T entries, bus trips, lateness and speed, subway speed, Bluebikes trips, card spending, tows, parking calls, MBTA alerts, crashes and Fire Department calls, hour by hour">`;
  let labels = ''; // drawn last, above the "future" shading and the time line
  LANES.forEach((L, k) => {
    const y0 = k * LH; const top = y0 + LABEL; const base = top + STRIP;
    labels += `<rect x="${PAD - 4}" y="${y0 + 1}" width="${LW - 2 * PAD + 8}" height="${LABEL - 3}" fill="#1A3A5F"/>`;
    labels += `<text x="${PAD}" y="${y0 + 16}" class="cap" font-size="15" letter-spacing="1" fill="#fff">${L.label.toUpperCase()}</text>`;
    if (wide) labels += `<text x="${LW - PAD}" y="${y0 + 16}" text-anchor="end" font-size="13" fill="#A9C4E4">${L.note}</text>`;
    s += `<rect x="${PAD}" y="${top}" width="${LW - 2 * PAD}" height="${STRIP}" rx="4" fill="#16304F"/>`;
    for (let i = 0; i < N; i++) { const t = tOf(i); const [rise, set] = sunOf(wall(t)); if (t + HOUR / 2 < rise || t + HOUR / 2 > set) s += `<rect x="${lx(i)}" y="${top}" width="${bw_ + 0.5}" height="${STRIP}" fill="#0E2238"/>`; }
    const d = laneData(L.key);
    const inner = STRIP - 6; const yb = base - 2;
    if (d == null) { s += msg(top + STRIP / 2 + 5, `Not available for this storm: ${L.from}.`); return; }
    if (L.kind === 'vsBase' && !d.now.some(Boolean) && !d.base.some(Boolean)) { s += msg(top + STRIP / 2 + 5, 'No trips from Somerville stations in these weeks.'); return; }
    if (L.kind === 'vsBase') {
      const mx = Math.max(1, ...d.now, ...d.base.filter((v) => v != null));
      d.now.forEach((v, i) => { if (v) s += `<rect x="${lx(i)}" y="${yb - (v / mx) * inner}" width="${Math.max(1, bw_ - 0.4)}" height="${(v / mx) * inner}" fill="${L.color}"/>`; });
      const line = d.base.map((v, i) => (v == null ? null : `${lx(i).toFixed(1)} ${(yb - (v / mx) * inner).toFixed(1)} ${lx(i + 1).toFixed(1)} ${(yb - (v / mx) * inner).toFixed(1)}`)).filter(Boolean);
      if (line.length) s += `<path d="M${line.join(' L')}" fill="none" stroke="#fff" stroke-width="1.5" opacity=".9"/>`;
    } else if (L.kind === 'thaw') {
      const ts = d.temps.filter((v) => v != null); const lo = Math.min(...ts, 28) - 2; const hi = Math.max(...ts, 36) + 2;
      const ty = (v) => top + 3 + (1 - (v - lo) / (hi - lo)) * (STRIP - 6);
      REFREEZE.forEach((on, k) => { if (on) s += `<rect x="${lx(k)}" y="${top}" width="${bw_ + 0.5}" height="${STRIP}" fill="#A9C4E4" opacity=".38"/>`; });
      const smax = Math.max(1, ...d.salting.map(([, n]) => n));
      d.salting.forEach(([k, n]) => { const hh = (n / smax) * (STRIP * 0.55); s += `<rect x="${lx(k)}" y="${top + STRIP - hh}" width="${Math.max(1.5, bw_ - 0.4)}" height="${hh}" fill="#F4C95D"/>`; });
      s += `<path d="M${lx(0)} ${ty(32)} H${lx(N)}" stroke="#DCE8F5" stroke-width="1" stroke-dasharray="4 4" opacity=".8"/>`;
      const pts = d.temps.map((v, k) => (v == null ? null : `${(lx(k) + bw_ / 2).toFixed(1)} ${ty(v).toFixed(1)}`));
      let path = ''; let pen = false;
      pts.forEach((p) => { if (p == null) { pen = false; return; } path += `${pen ? 'L' : 'M'}${p} `; pen = true; });
      s += `<path d="${path}" fill="none" stroke="#fff" stroke-width="1.8"/>`;
      s += `<text x="${PAD + 4}" y="${ty(32) - 3}" font-size="11" fill="#DCE8F5">32°F</text>`;
    } else if (L.kind === 'slow') {
      // % slower than usual on Red, Orange and Green Line segments in Somerville (capped), and hours with under half the trains
      const cap = (v) => Math.max(0, Math.min(v, 150));
      const mx = Math.max(25, ...d.slow.filter((v) => v != null).map(cap));
      d.slow.forEach((v, i) => {
        const few = L.few !== false && d.trains.base[i] >= 4 && d.trains.now[i] < d.trains.base[i] / 2;
        const unit = L.unit || 'trains';
        const tipTxt = `<b>${dayTm(tOf(i))}</b><br>${v == null ? `Too few ${unit.split(' ')[0] === 'bus' ? 'buses' : 'trains'} to time` : `${v > 0 ? `${v}% slower` : v < 0 ? `${-v}% faster` : 'Usual speed'} than usual`}<br>${d.trains.now[i]} ${unit} (usually ${Math.round(d.trains.base[i] ?? 0)})`;
        if (v != null && v > 0) s += `<rect x="${lx(i)}" y="${yb - (cap(v) / mx) * inner}" width="${Math.max(1, bw_ - 0.4)}" height="${(cap(v) / mx) * inner}" fill="${L.color}"/>`;
        if (few) s += `<rect x="${lx(i)}" y="${top + 2}" width="${Math.max(1.5, bw_ - 0.4)}" height="5" fill="#FF6B6B"/>`;
        if (v != null || few) s += `<rect data-tip="${attr(tipTxt)}" x="${lx(i)}" y="${top}" width="${Math.max(2, bw_)}" height="${STRIP}" fill="transparent"/>`;
      });
    } else if (L.kind === 'late') {
      // minutes late (early counts as 0), capped so one stuck bus doesn't flatten the rest
      const cap = (v) => Math.max(0, Math.min(v, 45));
      const mx = Math.max(5, ...d.now.filter((v) => v != null).map(cap), ...d.base.filter((v) => v != null).map(cap));
      d.now.forEach((v, i) => { if (v != null && v > 0) s += `<rect x="${lx(i)}" y="${yb - (cap(v) / mx) * inner}" width="${Math.max(1, bw_ - 0.4)}" height="${(cap(v) / mx) * inner}" fill="${L.color}"><title>${v} min late</title></rect>`; });
      const line = d.base.map((v, i) => (v == null ? null : `${lx(i).toFixed(1)} ${(yb - (cap(v) / mx) * inner).toFixed(1)} ${lx(i + 1).toFixed(1)} ${(yb - (cap(v) / mx) * inner).toFixed(1)}`)).filter(Boolean);
      if (line.length) s += `<path d="M${line.join(' L')}" fill="none" stroke="#fff" stroke-width="1.5" opacity=".9"/>`;
    } else if (L.kind === 'change') {
      // % change per day from the 4 weeks before: bars up or down from a middle line
      const mid = top + STRIP / 2; const mx = Math.max(5, ...d.days.map(([, , r]) => Math.abs(r)));
      s += `<path d="M${lx(0)} ${mid} H${lx(N)}" stroke="#fff" stroke-width="1" opacity=".6"/>`;
      d.days.forEach(([i, v, r], k) => {
        const end = k + 1 < d.days.length ? d.days[k + 1][0] : N; const w = lx(end) - lx(i) - 2; const hh = (Math.abs(r) / mx) * (STRIP / 2 - 3);
        s += `<rect x="${lx(i) + 1}" y="${r >= 0 ? mid - hh : mid}" width="${Math.max(1, w)}" height="${Math.max(0.5, hh)}" fill="${r < 0 ? L.color : '#6B7F95'}"/>`;
        const lab = `${r > 0 ? '+' : r < 0 ? '−' : ''}${Math.abs(r).toFixed(0)}%`;
        if (w >= 30) s += `<text x="${lx(i) + 1 + w / 2}" y="${r >= 0 ? mid + 13 : mid - 4}" text-anchor="middle" font-size="12" font-weight="700" fill="#fff">${lab}</text>`;
        s += `<rect data-tip="${attr(`<b>${fmt(tOf(Math.min(N - 1, i + 12)), { weekday: 'short', month: 'short', day: 'numeric' })}</b><br>Card spending ${lab} vs. the 4 weeks before<br><small>Middlesex County, 7-day average (Opportunity Insights)</small>`)}" x="${lx(i)}" y="${top}" width="${Math.max(2, lx(end) - lx(i))}" height="${STRIP}" fill="transparent"/>`;
      });
    } else if (L.kind === 'daily') {
      const mx = Math.max(1, d.base, ...d.days.map(([, n]) => n));
      d.days.forEach(([i, n], k) => {
        const end = k + 1 < d.days.length ? d.days[k + 1][0] : N; const w = lx(end) - lx(i) - 2; const hh = (n / mx) * inner;
        s += `<rect x="${lx(i) + 1}" y="${yb - hh}" width="${Math.max(1, w)}" height="${hh}" fill="${L.color}"/>`;
        if (n && w >= 30) s += `<text x="${lx(i) + 1 + w / 2}" y="${hh > 16 ? yb - hh + 13 : yb - hh - 3}" text-anchor="middle" font-size="12" font-weight="700" fill="#fff">${n.toLocaleString('en-US')}</text>`;
      });
      const yb_ = yb - (d.base / mx) * inner;
      s += `<path d="M${lx(0)} ${yb_} H${lx(N)}" stroke="#fff" stroke-width="1.5" opacity=".9"/>`;
    } else if (L.kind === 'shift' || L.kind === 'hourly') {
      const w = L.kind === 'shift' ? 8 : 1;
      const mx = Math.max(1, ...d.map(([, n]) => n));
      d.forEach(([i, n]) => {
        const hh = (n / mx) * inner;
        s += `<rect x="${lx(i)}" y="${yb - hh}" width="${Math.max(1, w * bw_ - 1)}" height="${hh}" fill="${L.color}"/>`;
        if (w > 1 && n && w * bw_ >= 18) s += `<text x="${lx(i) + (w * bw_) / 2}" y="${hh > 16 ? yb - hh + 13 : yb - hh - 3}" text-anchor="middle" font-size="12" font-weight="700" fill="#fff">${n}</text>`;
      });
    } else if (L.kind === 'ticks') {
      d.forEach(([i, kind, label, head]) => {
        const tip = `<b>${dayTm(tOf(i))} · MBTA ${esc(label.replace(/^Green-/, 'Green Line '))}</b><br>${esc(head)}`;
        s += `<g data-tip="${attr(tip)}"><rect x="${lx(i) - 3}" y="${top}" width="${Math.max(2, bw_) + 6}" height="${STRIP}" fill="transparent"/><rect x="${lx(i)}" y="${top + 4}" width="${Math.max(2, bw_)}" height="${STRIP - 8}" fill="${ALERT[kind]}"/></g>`;
      });
      if (!d.length) s += msg(top + STRIP / 2 + 5, 'No alerts on Somerville routes or stations.');
    } else if (L.kind === 'events') {
      // Fire Department calls: one tick each, colored by type; street only, never a house number
      const FIRE = { wires: '#F4C95D', co: '#C084FC', crash: '#FF6B6B' };
      d.forEach(([i, kind, label, street]) => {
        const tip = `<b>${dayTm(tOf(i))} · Fire Dept.</b><br>${esc(label)}${street ? `<br>${esc(street)}` : ''}`;
        s += `<g data-tip="${attr(tip)}"><rect x="${lx(i) - 3}" y="${top}" width="${Math.max(2, bw_) + 6}" height="${STRIP}" fill="transparent"/><rect x="${lx(i)}" y="${top + 4}" width="${Math.max(2, bw_)}" height="${STRIP - 8}" fill="${FIRE[kind]}"/></g>`;
      });
      if (!d.length) s += msg(top + STRIP / 2 + 5, 'No wires down, carbon monoxide calls or crashes.');
    } else if (L.kind === 'dots') {
      d.forEach((c) => {
        const nonMotor = c.ped || c.bike; const hurt = c.hurt && c.hurt !== 'none';
        const cx = lx(c.i) + bw_ / 2; const cy = top + STRIP / 2;
        s += `<g data-tip="${attr(crashTip(c))}"><circle cx="${cx}" cy="${cy}" r="14" fill="transparent"/><circle cx="${cx}" cy="${cy}" r="${hurt ? 7.5 : 5}" fill="${nonMotor ? '#FF8A3D' : '#DCE8F5'}"${hurt ? ' stroke="#fff" stroke-width="2"' : ''}/></g>`;
      });
      if (!d.length) s += msg(top + STRIP / 2 + 5, 'No crashes reported.');
    }
  });
  const lastBase = (LANES.length - 1) * LH + LABEL + STRIP;
  const every = Math.max(1, Math.ceil((wide ? 62 : 40) / (24 * (LW - 2 * PAD) / N))); // long periods: every 2nd, 3rd… day
  for (let i = 0, nd = 0; i < N; i++) {
    const w = wall(tOf(i)); if (w.h !== 12) continue;
    const hol = holidayOf(tOf(i));
    if ((nd++ % every !== 0 && !hol) || lx(i) < 20 || lx(i) > LW - 20) continue;
    s += `<text x="${lx(i)}" y="${lastBase + 17}" text-anchor="middle" class="cap" font-size="14" fill="${hol ? '#FF8A3D' : '#A9C4E4'}">${hol ? hol.toUpperCase() : every > 1 && !wide ? `${w.m}/${w.d}` : `${fmt(tOf(i), { weekday: 'short' }).toUpperCase()}${wide ? ` ${w.d}` : ''}`}</text>`;
  }
  s += `<rect id="future2" x="0" y="${LABEL - 4}" width="0" height="${lastBase - LABEL + 6}" fill="#1A3A5F" opacity=".72" pointer-events="none"/>`;
  s += `<path id="head2" d="M0 ${LABEL - 4} V${lastBase + 2}" stroke="#fff" stroke-width="2.5"/>`;
  s += labels + '</svg>';
  $('#lanes').innerHTML = s;
}
// tooltips for crash dots and MBTA alert ticks (hover with a mouse, tap on a phone)
const esc = (v) => String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const attr = (v) => v.replace(/"/g, '&quot;');
const HURT = { fatal: 'Someone was killed', serious: 'Serious injury', minor: 'Minor injury', possible: 'Possible injury', none: 'No injuries', '': 'Injuries not reported' };
function crashTip(c) {
  const [hh, mm] = c.t.split(':').map(Number);
  const when = dayTm(tOf(c.i) + mm * 6e4);
  const what = c.what ? `${c.what}${c.how && !/^not a collision/i.test(c.how) ? ` (${c.how.toLowerCase()})` : ''}` : 'Crash';
  const cond = [c.surface && `${c.surface.toLowerCase()} road`, c.weather && c.weather.toLowerCase(), c.light && c.light.toLowerCase()].filter(Boolean).join(' · ');
  const who = c.ped || c.bike ? `<br><b>${c.ped ? 'Pedestrian' : 'Cyclist'}</b>${[c.pedWhere, c.pedDoing].filter(Boolean).length ? `: ${esc([c.pedWhere, c.pedDoing].filter(Boolean).join(', ').toLowerCase())}` : ''}` : '';
  return `<b>${when}${c.where ? ` · ${esc(c.where)}` : ''}</b><br>${esc(what)}${cond ? `<br>${esc(cond)}` : ''}${who}<br>${HURT[c.hurt] ?? ''}${c.hitRun ? ' · hit and run' : ''}`;
}
function enableTips(svg) {
  const panel = svg.closest('.panel');
  let tip = panel.querySelector('.hovertip');
  if (!tip) { tip = document.createElement('div'); tip.className = 'hovertip'; tip.hidden = true; tip.setAttribute('role', 'tooltip'); panel.appendChild(tip); }
  const show = (els) => {
    const el = els[0];
    tip.innerHTML = els.map((x) => x.dataset.tip).join('<hr>'); tip.hidden = false;
    const pr = panel.getBoundingClientRect(); const r = el.getBoundingClientRect();
    const w = tip.offsetWidth; const h = tip.offsetHeight;
    const x = Math.max(8, Math.min(pr.width - w - 8, r.left + r.width / 2 - pr.left - w / 2));
    const above = r.top - pr.top - h - 8;
    tip.style.left = `${x}px`; tip.style.top = `${above >= 0 ? above : r.bottom - pr.top + 8}px`;
  };
  // Dots and ticks can sit a few pixels apart: pick the one nearest the pointer in that lane, not whichever is on top.
  const pick = (e) => {
    const r = svg.getBoundingClientRect(); const k = svg.viewBox.baseVal.width / r.width;
    const x = (e.clientX - r.left) * k; const y = (e.clientY - r.top) * k;
    const near = [];
    svg.querySelectorAll('[data-tip]').forEach((el) => {
      const b = el.getBBox();
      if (y < b.y - 4 || y > b.y + b.height + 4) return;
      const d = x >= b.x && x <= b.x + b.width ? 0 : Math.abs(b.x + b.width / 2 - x); // inside a wide bar counts
      if (d < 18) near.push([d, el]);
    });
    if (!near.length) return null;
    const bd = Math.min(...near.map(([d]) => d));
    return near.filter(([d]) => d <= bd + 2).map(([, el]) => el).slice(0, 4); // dots that overlap: show them all
  };
  svg.addEventListener('pointermove', (e) => { if (e.buttons) return; const els = pick(e); if (els) show(els); else tip.hidden = true; });
  svg.addEventListener('pointerleave', () => { tip.hidden = true; });
  svg.addEventListener('pointerdown', (e) => { const els = pick(e); if (els) setTimeout(() => show(els)); else tip.hidden = true; });
}

// "today so far" vs. the same hours in a normal week, for the counters under the lanes
function todayVsNormal(series, i) {
  if (!series) return null;
  const w = wall(tOf(i)); let a = 0; let b = 0;
  for (let k = i; k >= 0; k--) { const wk = wall(tOf(k)); if (wk.d !== w.d) break; a += series.now[k] || 0; b += series.base[k] || 0; }
  return b >= 5 ? a / b - 1 : null;
}

/* ---------- ward map ---------- */
const lat0 = 42.39; const kx = Math.cos(lat0 * Math.PI / 180);
const allPts = WARDS.wards.flatMap((w) => w.rings.flat());
const minX = Math.min(...allPts.map((p) => p[0] * kx)); const maxX = Math.max(...allPts.map((p) => p[0] * kx));
const minY = Math.min(...allPts.map((p) => p[1])); const maxY = Math.max(...allPts.map((p) => p[1]));
const MW = 640; const sc = (MW - 20) / (maxX - minX); const MH = Math.round((maxY - minY) * sc + 20);
const px = ([lon, lat]) => [10 + (lon * kx - minX) * sc, 10 + (maxY - lat) * sc];
const finalWard = wardSince(N - 1);
const wardMax = Math.max(1, ...Object.values(finalWard));
const mix = (a, b, f) => { const p = (h) => [1, 3, 5].map((k) => parseInt(h.slice(k, k + 2), 16)); const [A, B] = [p(a), p(b)]; return `rgb(${A.map((v, k) => Math.round(v + (B[k] - v) * f)).join(',')})`; };
const topStops = BUS.stops.slice(0, 19);
function buildMap() {
  let s = `<svg viewBox="0 0 ${MW} ${MH}" role="img" aria-label="Map of Somerville's seven wards, shaded by sidewalk reports so far, with every bus route and stop in the city">`;
  const wardD = WARDS.wards.map((w) => [w, w.rings.map((r) => `M${r.map((p) => px(p).map((v) => v.toFixed(1)).join(' ')).join(' L')} Z`).join(' ')]);
  s += `<defs><clipPath id="city">${wardD.map(([, d]) => `<path d="${d}"/>`).join('')}</clipPath></defs>`;
  wardD.forEach(([w, d]) => { s += `<path class="ward" data-w="${w.ward}" d="${d}" fill="#DCE8F5" stroke="#1A3A5F" stroke-width="3"/>`; });
  // bus routes (the usual path, both directions), clipped to the city line; a wide invisible stroke makes them easy to hover
  const routes = Object.entries(BUS.routes || {}).filter(([, r]) => r.paths.length);
  const rd = (r) => r.paths.map((p) => `M${p.map((q) => px(q).map((v) => v.toFixed(1)).join(' ')).join(' L')}`).join(' ');
  s += `<g clip-path="url(#city)" fill="none" stroke-linejoin="round" stroke-linecap="round">${routes.map(([id, r]) => `<g class="route" data-r="${id}" data-long="${attr(esc(r.long))}"><path d="${rd(r)}" class="rt-line" stroke="#1A3A5F" stroke-opacity=".5" stroke-width="2.5"/><path d="${rd(r)}" stroke="transparent" stroke-width="12"/></g>`).join('')}</g>`;
  // every stop: small dots, the busiest 19 (half of all boardings) larger, drawn last so they sit on top
  const dot = (b, big) => { const [x, y] = px([b.lon, b.lat]); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${big ? (2.5 + Math.sqrt(b.riders) / 4).toFixed(1) : 2.6}" fill="${big ? '#10243A' : '#fff'}" stroke="${big ? '#fff' : '#1A3A5F'}" stroke-width="${big ? 1.5 : 1.2}" class="stop${big ? ' big' : ''}" data-name="${attr(esc(b.name))}" data-riders="${b.riders}" data-routes="${b.routes.join(', ')}"/>`; };
  BUS.stops.slice(19).forEach((b) => { s += dot(b, false); });
  topStops.forEach((b) => { s += dot(b, true); });
  WARDS.wards.forEach((w) => {
    // label at the ward's area centroid (in screen space), so it sits inside the shape
    const ring = w.rings.reduce((a, r) => (r.length > a.length ? r : a)).map(px);
    let A = 0; let cx = 0; let cy = 0;
    ring.forEach(([x1, y1], k) => { const [x2, y2] = ring[(k + 1) % ring.length]; const f = x1 * y2 - x2 * y1; A += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f; });
    const [x, y] = [cx / (3 * A), cy / (3 * A)];
    s += `<g class="wl" pointer-events="none"><text x="${x.toFixed(1)}" y="${(y - 4).toFixed(1)}" text-anchor="middle" class="cap" font-size="14" fill="#10243A">WARD ${w.ward}</text><text data-n="${w.ward}" x="${x.toFixed(1)}" y="${(y + 24).toFixed(1)}" text-anchor="middle" class="cap" font-size="26" fill="#10243A">0</text>${SURVEY && SURVEY.wards[w.ward] ? `<text data-s="${w.ward}" x="${x.toFixed(1)}" y="${(y + 40).toFixed(1)}" text-anchor="middle" class="cap" font-size="12" fill="#10243A">${SURVEY.wards[w.ward].walk}% WALK</text>` : ''}</g>`;
  });
  s += '</svg>';
  $('#map').innerHTML = s;
  $('#m-season').textContent = BUS.season;
  // Routes change: the map shows today's; say which ones also stopped in Somerville at the time of this storm.
  const today = new Set(BUS.stops.flatMap((b) => b.routes).map((r) => (r === '747' ? 'CT2' : r)));
  const then = (X.buses && X.buses.routes) || null;
  const when = new Date(`${S.id}T12:00:00`).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const gone = then ? then.filter((r) => !today.has(r)) : [];
  $('#m-routes').textContent = gone.length ? `In ${when} the ${gone.join(' and ')} also ran here.` : '';
}

// Ward tooltips: who walks and rides transit there (Happiness Survey), and sidewalk reports so far.
let wardNow = {};
function enableWardTips() {
  const svg = $('#map svg'); const panel = svg.closest('.panel');
  const tip = document.createElement('div'); tip.className = 'hovertip'; tip.hidden = true; tip.setAttribute('role', 'tooltip'); panel.appendChild(tip);
  let lit = null;
  const light = (r) => { if (lit === r) return; if (lit) lit.classList.remove('on'); lit = r; if (r) { r.classList.add('on'); r.parentNode.appendChild(r); } };
  const show = (path, e) => {
    light(path.classList.contains('route') ? path : null);
    if (path.classList.contains('route')) {
      const n = BUS.stops.filter((b) => b.routes.includes(path.dataset.r)).length;
      tip.innerHTML = `<b>Bus ${path.dataset.r}</b>${path.dataset.long ? `: ${path.dataset.long}` : ''}<br>${n} stops in Somerville<br><small>Usual route · MBTA</small>`;
    } else if (path.classList.contains('stop')) {
      tip.innerHTML = `<b>${path.dataset.name}</b>: bus stop<br>${(+path.dataset.riders).toLocaleString('en-US')} weekday boardings<br><small>Routes ${path.dataset.routes} · MBTA, ${BUS.season}</small>`;
    } else {
    const k = path.dataset.w; const sv = SURVEY && SURVEY.wards[k];
    tip.innerHTML = `<b>Ward ${k}</b>: ${wardNow[k] || 0} sidewalk reports since the snow started` +
      (sv ? `<br>In the past week, <b>${sv.walk}%</b> walked and <b>${sv.transit}%</b> rode transit<br><small>${SURVEY.year} Happiness Survey, ${sv.n} residents</small>` : '');
    }
    tip.hidden = false;
    const pr = panel.getBoundingClientRect(); const w = tip.offsetWidth; const h = tip.offsetHeight;
    tip.style.left = `${Math.max(8, Math.min(pr.width - w - 8, e.clientX - pr.left - w / 2))}px`;
    tip.style.top = `${Math.max(8, e.clientY - pr.top - h - 14)}px`;
  };
  const pick = (e) => e.target.closest('.stop, .route, .ward');
  svg.addEventListener('pointermove', (e) => { const p = pick(e); if (p) show(p, e); else { tip.hidden = true; light(null); } });
  svg.addEventListener('pointerdown', (e) => { const p = pick(e); if (p) show(p, e); });
  svg.addEventListener('pointerleave', () => { tip.hidden = true; light(null); });
}

/* ---------- render one hour ---------- */
const scrub = $('#scrub');
scrub.max = String(N - 1);
function render(i) {
  i = Math.max(0, Math.min(N - 1, i));
  const t = tOf(i + 1); // each step shows the end of hour i: requests and weather through that hour
  const h = S.hours[i];
  $('#now-time').textContent = `${fmt(t, { weekday: 'short', month: 'short', day: 'numeric' })} · ${tm(t)}`;
  const sky = h[0] === 3 ? 'Heavy snow' : h[0] === 2 ? 'Snow' : h[0] === 1 ? 'Light snow' : 'No snow';
  $('#now-wx').textContent = [sky, h[1] != null ? `${h[1]}°F` : '', h[2] != null && h[0] ? `visibility ${h[2] < 1 ? `${h[2]} mi` : `${h[2]} mi`}` : '', h[3] ? `wind ${h[3]} kn` : ''].filter(Boolean).join(' · ') + ' at Logan';
  renderMessages(t, i, false);
  const x = xOf(i + 1);
  $('#future').setAttribute('x', x); $('#future').setAttribute('width', Math.max(0, CW - x));
  $('#head').setAttribute('d', `M${x} ${TOP - 6} V${BOT + 4}`);
  $('#knob').setAttribute('transform', `translate(${x} ${BOT + 4})`);
  const x2 = lx(i + 1);
  $('#future2').setAttribute('x', x2); $('#future2').setAttribute('width', Math.max(0, LW - x2));
  const lastBase = (LANES.length - 1) * LH + LABEL + STRIP;
  $('#head2').setAttribute('d', `M${x2} ${LABEL - 4} V${lastBase + 2}`);
  const pct = (r) => (r == null ? '–' : `${r > 0 ? '+' : r < 0 ? '−' : ''}${Math.abs(Math.round(r * 100))}%`);
  const sumTo = (pairs) => (pairs ? pairs.filter(([k]) => k <= i).reduce((a, [, n]) => a + n, 0) : null);
  const tows = X.police ? sumTo(X.police.tows.filter(([k]) => k >= BASE - 24)) : null;
  $('#tally2').innerHTML = [
    [pct(todayVsNormal(X.tEntries, i)), `T entries today vs. a normal week${holidayOf(tOf(i)) ? ` (${holidayOf(tOf(i))})` : ''}`, '#A9C4E4'],
    [pct(todayVsNormal(X.buses && X.buses.trips, i)), 'Buses run today vs. normal', '#7FD4C1'],
    [pct(todayVsNormal(X.bikes, i)), 'Bluebikes trips today vs. normal', '#F4C95D'],
    [tows ?? '–', 'Snow emergency tows so far', '#3B82F6'],
  ].map(([v, l, c]) => `<div><b>${v}</b><span><i style="background:${c}"></i>${l}</span></div>`).join('');
  const c = since(i);
  $('#tally').innerHTML = ['sidewalk', 'street', 'ask', 'spacesaver'].map((g) => `<div><b>${c[gi(g)]}</b><span><i style="background:${GROUP[g].color}"></i>${GROUP[g].label}</span></div>`).join('');
  // map
  const w = wardSince(i);
  // light blue (none) → orange → rust (the ward with the most reports by the end of the storm)
  const ramp = (f) => (f <= 0 ? '#DCE8F5' : f < 0.5 ? mix('#F6D3BC', '#FF8A3D', f / 0.5) : mix('#FF8A3D', '#B93D06', (f - 0.5) / 0.5));
  document.querySelectorAll('#map .ward').forEach((p) => { const n = w[p.dataset.w] || 0; p.setAttribute('fill', ramp(Math.min(1, n / wardMax))); });
  // labels: navy on light wards, white on dark ones, each with a halo of the opposite color so bus stops never hide them
  const ink = (dark) => (el) => { el.setAttribute('fill', dark ? '#fff' : '#10243A'); el.setAttribute('stroke', dark ? 'rgba(16,36,58,.85)' : 'rgba(255,255,255,.85)'); };
  document.querySelectorAll('#map [data-n]').forEach((el) => { const dark = (w[el.dataset.n] || 0) / wardMax >= 0.6; ink(dark)(el); if (el.previousElementSibling) ink(dark)(el.previousElementSibling); });
  document.querySelectorAll('#map [data-n]').forEach((el) => { el.textContent = w[el.dataset.n] || 0; });
  document.querySelectorAll('#map [data-s]').forEach((el) => { ink((w[el.dataset.s] || 0) / wardMax >= 0.6)(el); });
  wardNow = w;
  const total = c[gi('sidewalk')];
  const lateFrom = Math.floor(idxOf(DL)); // the hour the deadline falls in counts as late
  const before = lateFrom > 0 ? since(Math.min(i, lateFrom - 1))[gi('sidewalk')] : 0;
  $('#m-total').textContent = total;
  $('#m-late').textContent = i >= lateFrom ? `${total - before}` : '0';
  $('#m-late-l').textContent = i < BASE ? 'The snow hasn\'t started yet. Press play or drag the line.'
    : i >= lateFrom ? `came after the ${tm(DL)} deadline (${before} before it)` : `came after the deadline (it's ${dayTm(DL)})`;
  scrub.value = String(i);
}

/* ---------- controls ---------- */
const jumps = [[has('start') ? 'City declares' : 'City notice', notices.length ? declared : null], ['Emergency', E.start], ['Snow starts', snowStart], ['Heaviest', S.hours.some((h) => h[0] === 3) ? tOf(S.hours.findIndex((h) => h[0] === 3) + 1) : null], ['Snow stops', snowStop], ['Deadline', DL], ['Emergency ends', E.end], ['Day 3', DL + 48 * HOUR],
  ...FALLS.filter((f) => f !== MAIN && f !== FALLS[0]).map((f) => [`Snow ${fmt(f.start, { month: 'short', day: 'numeric' })}`, f.start]), ['Reports die down', CLEAR]];
$('#jumps').innerHTML = jumps.filter(([, t]) => typeof t === 'number' && idxOf(t) >= 0 && idxOf(t) < N).sort((a, b) => a[1] - b[1]).map(([l, t]) => `<button class="chip" data-i="${Math.max(0, Math.ceil(idxOf(t)) - 1)}">${l}</button>`).join('');
$('#jumps').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { stop(); render(+b.dataset.i); } });
scrub.addEventListener('input', () => { stop(); render(+scrub.value); });
// Grab the line on the chart (or tap anywhere on it) and drag through the hours. Called once the chart exists.
function enableDrag(svg) {
  const W = svg.viewBox.baseVal.width;
  const hourAt = (e) => { const r = svg.getBoundingClientRect(); const x = ((e.clientX - r.left) / r.width) * W; return Math.round((x - PAD) / ((W - 2 * PAD) / N)) - 1; };
  let dragging = false;
  svg.addEventListener('pointerdown', (e) => { dragging = true; svg.setPointerCapture(e.pointerId); stop(); render(hourAt(e)); });
  svg.addEventListener('pointermove', (e) => { if (dragging) render(hourAt(e)); });
  ['pointerup', 'pointercancel'].forEach((ev) => svg.addEventListener(ev, () => { dragging = false; }));
  svg.addEventListener('keydown', (e) => {
    const step = { ArrowRight: 1, ArrowLeft: -1, PageUp: 24, PageDown: -24 }[e.key];
    if (step) { e.preventDefault(); stop(); render(+scrub.value + step); }
  });
  svg.setAttribute('tabindex', '0');
}
let timer = null;
function stop() { clearInterval(timer); timer = null; $('#play-ico').setAttribute('d', 'M7 4 L20 12 L7 20 Z'); $('#play').setAttribute('aria-label', 'Play'); }
$('#play').addEventListener('click', () => {
  if (timer) return stop();
  if (+scrub.value >= N - 1) render(0);
  $('#play-ico').setAttribute('d', 'M6 4 H10 V20 H6 Z M14 4 H18 V20 H14 Z'); $('#play').setAttribute('aria-label', 'Pause');
  timer = setInterval(() => { const i = +scrub.value + 1; if (i >= N) return stop(); render(i); }, 120);
});

/* ---------- go ---------- */
buildChart();
document.fonts?.ready.then(() => { labelMarkers(); lockPhoneHeight(); }); // re-place labels once the web font has its real widths
buildLanes();
enableDrag($('#chart svg'));
enableDrag($('#lanes svg'));
enableTips($('#lanes svg'));
buildMap();
enableWardTips();
render(Math.max(0, Math.ceil(idxOf(declared)) - 1));
lockPhoneHeight(); lockLateHeight();
{
  let timer2 = null; let lastW = LW;
  window.addEventListener('resize', () => {
    clearTimeout(timer2);
    timer2 = setTimeout(() => {
      const w = Math.round($('#lanes').clientWidth);
      if (Math.abs(w - lastW) < 4) return;
      lastW = w; buildChart(); enableDrag($('#chart svg')); buildLanes(); enableDrag($('#lanes svg')); enableTips($('#lanes svg')); render(+scrub.value); lockPhoneHeight(); lockLateHeight();
    }, 150);
  });
}
