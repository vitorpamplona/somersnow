/* Storm replay (storm.html): one past storm, hour by hour.
   Data comes from docs/data/ (written by scripts/fetch_data.py). The deadline uses the guide's own calculator.
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

const load = (f) => fetch(`data/${f}`).then((r) => r.json());
const STORMS = await load('storms.json');
// ?storm=<last day of snow>; default: the most recent big storm
const IDS = STORMS.storms.map((st) => st.end);
const asked = new URLSearchParams(location.search).get('storm');
const id = IDS.includes(asked) ? asked : IDS[IDS.length - 1];
const [S, WARDS, BUS] = await Promise.all([load(`storm-${id}.json`), load('wards.json'), load('bus-stops.json')]);

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
const snowStart = ms(S.snowStart);
const snowStop = ms(S.snowStop);
const D = deadline(snowStop);
const DL = D.end;
const clockFrom = D.days.find((d) => d.from).from;
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
// Counters and the map count this storm only: from the first snowy hour (earlier reports belong to earlier snow).
const BASE = Math.max(0, Math.floor(idxOf(snowStart)));
const since = (i) => (i < BASE ? groups.map(() => 0) : cum[i].map((v, k) => v - (BASE ? cum[BASE - 1][k] : 0)));
const wardSince = (i) => { if (i < BASE) return {}; const a = wardCum[i]; const b = BASE ? wardCum[BASE - 1] : {}; return Object.fromEntries(Object.keys(a).map((k) => [k, a[k] - (b[k] || 0)])); };

/* ---------- what the guide would say at time t ---------- */
function messages(t, i) {
  const out = [];
  const add = (cls, icon, b, s, big) => out.push({ cls: cls && `m-${cls}`, icon, b, s: s.replace(/\.\.(?=$|\s|<)/g, '.'), big });
  const h = S.hours[Math.max(0, Math.min(N - 1, i))] || [];
  notices.forEach((n) => { if (t >= n.at && t < n.at + 20 * HOUR) add('city', 'city', `City · ${n.approx ? fmt(n.at, { weekday: 'short', month: 'short', day: 'numeric' }) : dayTm(n.at)}`, `${n.text} <a href="${n.src}">Read it</a>`); });

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
  if (t >= snowStart && t < snowStop) {
    add('now', 'snow', h[0] === 3 ? 'Heavy snow' : 'Snowing', 'The 6-hour clock starts when it stops. Night doesn\'t count.');
  }
  if (t >= snowStop && t < clockFrom) {
    add('now', 'clock', 'Snow stopped', `Night doesn't count. The clock starts at sunrise, ${tm(clockFrom)}.`, `Shovel by ${dayTm(DL)}`);
  }
  if (t >= clockFrom && t < DL) {
    add('now', 'shovel', 'Shovel now', '36 inches wide. Down to the pavement. Open the ramp.', `${dur(DL - t)} left`);
  }
  if (t >= DL && t < DL + 30 * HOUR) {
    add('warn', 'phone', 'Deadline passed', `It was ${dayTm(DL)}${cityDL ? ` (the City said ${tm(cityDL)})` : ''}. Still buried? Report it: 311.`);
  }
  if (t >= DL) add('', 'ice', 'Check for ice', 'Meltwater refreezes overnight. Sand or salt it.');
  if (has('end') && t >= E.end) {
    if (has('lotsBy') && t < E.lotsBy) add('em', 'car', 'Emergency over', `Out of City lots by ${dayTm(E.lotsBy)}.`);
    else if (has('permitsBy') && t < E.permitsBy) add('em', 'car', 'Permit visible', `Clear your parking permit by ${dayTm(E.permitsBy)}.`);
    else if (has('carsBy') && t < E.carsBy) add('em', 'car', 'Dig out your car', `Fully cleared by ${dayTm(E.carsBy)}.`);
  }
  if (t >= (has('end') ? E.end : DL)) add('', 'ban', 'Space savers', 'Banned. $100. Thrown out.');
  return out.slice(0, 4);
}

function renderMessages(t, i) {
  $('#msgs').innerHTML = messages(t, i).map((m) => `<div class="msg ${m.cls}"><svg class="ico" aria-hidden="true"><use href="#i-${m.icon}"/></svg><b>${m.b}</b><span>${m.big ? `<span class="big">${m.big}</span><br>` : ''}${m.s}</span></div>`).join('');
}

/* ---------- timeline chart ---------- */
const CW = 900; const PAD = 8; const TOP = 40; const SNOW_H = 54; const REQ_TOP = TOP + SNOW_H + 14; const REQ_H = 170; const BOT = REQ_TOP + REQ_H;
const xOf = (i) => PAD + (i / N) * (CW - 2 * PAD);
const bw = (CW - 2 * PAD) / N;
const maxReq = Math.max(1, ...Array.from({ length: N }, (_, i) => reqAt(i).reduce((a, b) => a + b, 0)));
function buildChart() {
  let s = `<svg viewBox="0 0 ${CW} ${BOT + 26}" role="img" aria-label="Hour-by-hour timeline: snowfall intensity at Logan, and 311 snow requests stacked by type">`;
  // night shading
  for (let i = 0; i < N; i++) {
    const t = tOf(i); const w = wall(t);
    const [rise, set] = sunOf(w);
    const night = t + HOUR / 2 < rise || t + HOUR / 2 > set;
    if (night) s += `<rect x="${xOf(i)}" y="${TOP}" width="${bw + 0.5}" height="${BOT - TOP}" fill="#0E2238"/>`;
  }
  // day labels at local noon
  for (let i = 0; i < N; i++) { const w = wall(tOf(i)); if (w.h === 12) s += `<text x="${xOf(i)}" y="${BOT + 20}" text-anchor="middle" class="cap" font-size="15" fill="#A9C4E4">${fmt(tOf(i), { weekday: 'short' }).toUpperCase()} ${w.d}</text>`; }
  // snow intensity
  S.hours.forEach((h, i) => { if (h[0]) s += `<rect x="${xOf(i)}" y="${TOP + SNOW_H - h[0] * 17}" width="${bw + 0.4}" height="${h[0] * 17}" fill="#fff" opacity="${0.35 + h[0] * 0.2}"/>`; });
  s += `<text x="${PAD + 4}" y="${TOP + 14}" class="cap" font-size="13" fill="#A9C4E4">SNOW AT LOGAN</text>`;
  s += `<text x="${PAD + 4}" y="${REQ_TOP + 14}" class="cap" font-size="13" fill="#A9C4E4">311 REQUESTS PER HOUR</text>`;
  // requests, stacked (sidewalk on the bottom)
  const order = ['sidewalk', 'street', 'ask', 'spacesaver', 'feedback'];
  for (let i = 0; i < N; i++) {
    let y = BOT;
    order.forEach((g) => { const v = reqAt(i)[gi(g)] || 0; if (!v) return; const hh = (v / maxReq) * REQ_H; y -= hh; s += `<rect x="${xOf(i)}" y="${y}" width="${Math.max(1, bw - 0.6)}" height="${hh}" fill="${GROUP[g].color}"/>`; });
  }
  // markers
  const marks = [[E.start, 'Emergency', '#3B82F6'], [snowStart, 'Snow starts', '#fff'], [snowStop, 'Snow stops', '#fff'], [DL, 'Deadline', '#FF8A3D'], [E.end, 'Emergency ends', '#3B82F6']]
    .filter(([t]) => typeof t === 'number' && idxOf(t) >= 0 && idxOf(t) <= N);
  marks.forEach(([t, label, c], k) => {
    const x = xOf(idxOf(t));
    s += `<path d="M${x} ${TOP - (k % 2 ? 4 : 20)} V${BOT}" stroke="${c}" stroke-width="${label === 'Deadline' ? 3 : 2}" ${label === 'Deadline' ? '' : 'stroke-dasharray="5 5"'}/>`;
    s += `<text x="${x + 4}" y="${k % 2 ? 34 : 18}" class="cap" font-size="14" fill="${c}">${label.toUpperCase()}</text>`;
  });
  s += `<rect id="future" x="0" y="${TOP}" width="0" height="${BOT - TOP + 2}" fill="#1A3A5F" opacity=".78"/>`;
  s += `<path id="head" d="M0 ${TOP - 6} V${BOT + 4}" stroke="#fff" stroke-width="2.5"/>`;
  s += `<g id="knob"><circle r="11" fill="#FF8A3D" stroke="#fff" stroke-width="3"/><path d="M-3 -4 V4 M3 -4 V4" stroke="#10243A" stroke-width="2" stroke-linecap="round"/></g>`;
  s += '</svg>';
  $('#chart').innerHTML = s;
  $('#legend').innerHTML = ['sidewalk', 'street', 'ask', 'spacesaver'].map((g) => `<span><i style="background:${GROUP[g].color}"></i>${GROUP[g].label}</span>`).join('') + '<span><i style="background:#0E2238"></i>Night</span>';
}
const sunCache = {};
function sunOf(w) {
  const k = `${w.y}-${w.m}-${w.d}`;
  if (!sunCache[k]) sunCache[k] = sunTimes(w.y, w.m, w.d);
  return sunCache[k];
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
  let s = `<svg viewBox="0 0 ${MW} ${MH}" role="img" aria-label="Map of Somerville's seven wards, shaded by sidewalk reports so far, with the 19 busiest bus stops">`;
  WARDS.wards.forEach((w) => {
    const d = w.rings.map((r) => `M${r.map((p) => px(p).map((v) => v.toFixed(1)).join(' ')).join(' L')} Z`).join(' ');
    s += `<path class="ward" data-w="${w.ward}" d="${d}" fill="#DCE8F5" stroke="#1A3A5F" stroke-width="3"/>`;
  });
  topStops.forEach((b) => { const [x, y] = px([b.lon, b.lat]); s += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(2.5 + Math.sqrt(b.riders) / 4).toFixed(1)}" fill="#10243A" stroke="#fff" stroke-width="1.5"><title>${b.name}: ${b.riders} weekday boardings</title></circle>`; });
  WARDS.wards.forEach((w) => {
    // label at the ward's area centroid (in screen space), so it sits inside the shape
    const ring = w.rings.reduce((a, r) => (r.length > a.length ? r : a)).map(px);
    let A = 0; let cx = 0; let cy = 0;
    ring.forEach(([x1, y1], k) => { const [x2, y2] = ring[(k + 1) % ring.length]; const f = x1 * y2 - x2 * y1; A += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f; });
    const [x, y] = [cx / (3 * A), cy / (3 * A)];
    s += `<g class="wl" pointer-events="none"><text x="${x.toFixed(1)}" y="${(y - 4).toFixed(1)}" text-anchor="middle" class="cap" font-size="14" fill="#10243A">WARD ${w.ward}</text><text data-n="${w.ward}" x="${x.toFixed(1)}" y="${(y + 20).toFixed(1)}" text-anchor="middle" class="cap" font-size="26" fill="#10243A">0</text></g>`;
  });
  s += '</svg>';
  $('#map').innerHTML = s;
  $('#m-season').textContent = BUS.season;
}

/* ---------- every big storm ---------- */
function buildMultiples() {
  const list = STORMS.storms.filter((st) => st.days.some((d) => (d[2].sidewalk || 0) > 0));
  let peaks13 = 0;
  $('#multiples').innerHTML = list.map((st) => {
    const v = st.days.map((d) => d[2].sidewalk || 0);
    const mx = Math.max(1, ...v); const pk = v.indexOf(mx) - 2;
    if (pk >= 1 && pk <= 3) peaks13++;
    const end = new Date(`${st.end}T12:00:00Z`);
    const label = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
    const bars = v.map((n, k) => `<rect x="${k * 20 + 2}" y="${60 - (n / mx) * 56}" width="16" height="${(n / mx) * 56}" rx="2" fill="${k === 2 ? '#10243A' : '#FF8A3D'}"/>`).join('');
    const sel = st.end === id;
    return `<a class="mini${sel ? ' sel' : ''}" href="storm.html?storm=${st.end}"${sel ? ' aria-current="page"' : ''}><h4>${label}</h4><small>${st.snow} in · peak ${mx} on day ${pk >= 0 ? '+' : ''}${pk}</small><svg viewBox="0 0 200 74">${bars}<path d="M0 61 H200" stroke="#C9D6E3"/><text x="51" y="73" text-anchor="middle" font-size="10" fill="#47607C">LAST SNOW</text></svg><span class="go">${sel ? 'Showing above' : 'Replay this storm →'}</span></a>`;
  }).join('');
  $('#all-lede').textContent = `In ${peaks13} of ${list.length} big storms, sidewalk reports peaked 1 to 3 days after the last day of snow.`;
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
  renderMessages(t, i);
  const x = xOf(i + 1);
  $('#future').setAttribute('x', x); $('#future').setAttribute('width', Math.max(0, CW - x));
  $('#head').setAttribute('d', `M${x} ${TOP - 6} V${BOT + 4}`);
  $('#knob').setAttribute('transform', `translate(${x} ${BOT + 4})`);
  const c = since(i);
  $('#tally').innerHTML = ['sidewalk', 'street', 'ask', 'spacesaver'].map((g) => `<div><b>${c[gi(g)]}</b><span><i style="background:${GROUP[g].color}"></i>${GROUP[g].label}</span></div>`).join('');
  // map
  const w = wardSince(i);
  document.querySelectorAll('#map .ward').forEach((p) => { const n = w[p.dataset.w] || 0; p.setAttribute('fill', mix('#DCE8F5', '#FF8A3D', Math.min(1, n / wardMax))); });
  document.querySelectorAll('#map [data-n]').forEach((el) => { el.textContent = w[el.dataset.n] || 0; });
  const total = c[gi('sidewalk')];
  const lateFrom = Math.floor(idxOf(DL)); // the hour the deadline falls in counts as late
  const before = lateFrom > 0 ? since(Math.min(i, lateFrom - 1))[gi('sidewalk')] : 0;
  $('#m-total').textContent = total;
  $('#m-late').textContent = i >= lateFrom ? `${total - before}` : '0';
  $('#m-late-l').textContent = i >= lateFrom ? `came after the ${tm(DL)} deadline (${before} before it)` : `came after the deadline (it's ${dayTm(DL)})`;
  scrub.value = String(i);
}

/* ---------- controls ---------- */
const jumps = [[has('start') ? 'City declares' : 'City notice', notices.length ? declared : null], ['Emergency', E.start], ['Snow starts', snowStart], ['Heaviest', S.hours.some((h) => h[0] === 3) ? tOf(S.hours.findIndex((h) => h[0] === 3) + 1) : null], ['Snow stops', snowStop], ['Deadline', DL], ['Emergency ends', E.end], ['Day 3', DL + 48 * HOUR]];
$('#jumps').innerHTML = jumps.filter(([, t]) => typeof t === 'number' && idxOf(t) >= 0 && idxOf(t) < N).map(([l, t]) => `<button class="chip" data-i="${Math.max(0, Math.ceil(idxOf(t)) - 1)}">${l}</button>`).join('');
$('#jumps').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { stop(); render(+b.dataset.i); } });
scrub.addEventListener('input', () => { stop(); render(+scrub.value); });
// Grab the line on the chart (or tap anywhere on it) and drag through the hours. Called once the chart exists.
function enableDrag() {
  const svg = $('#chart svg');
  const hourAt = (e) => { const r = svg.getBoundingClientRect(); const x = ((e.clientX - r.left) / r.width) * CW; return Math.round((x - PAD) / bw) - 1; };
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
$('#r-title').textContent = S.title;
document.title = `Storm replay: ${S.title} · Somerville Snow Guide`;
const missing = !S.emergency ? ' The City\'s snow emergency notices for this storm aren\'t online, so parking messages are left out.'
  : !has('start') ? ' Only the City\'s notice about the end of the emergency is online.'
    : !has('end') ? ' The City\'s notice about the end of the emergency isn\'t online.' : '';
$('#r-lede').textContent = `${S.snowTotal} inches at Logan. Snow from ${dayTm(snowStart)} to ${dayTm(snowStop)}.${missing} Press play, or drag the time.`.replace(/\.\./g, '.');
{
  const k = IDS.indexOf(id);
  const short = (sid) => new Date(`${sid}T12:00:00Z`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  $('#storm-nav').innerHTML = [
    k > 0 ? `<a href="storm.html?storm=${IDS[k - 1]}">← ${short(IDS[k - 1])}</a>` : '<span></span>',
    `<a href="#all">All ${IDS.length} storms</a>`,
    k < IDS.length - 1 ? `<a href="storm.html?storm=${IDS[k + 1]}">${short(IDS[k + 1])} →</a>` : '<span></span>',
  ].join('');
}
buildChart();
enableDrag();
buildMap();
buildMultiples();
render(Math.max(0, Math.ceil(idxOf(declared)) - 1));
