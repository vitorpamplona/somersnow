import { corner } from './corner.js';
import { shovelScene } from './shovel.js';
import { snowfall } from './snowfall.js';
import { deadline, sunTimes, wall, zoned, SOMERVILLE } from './deadline.js';
import { t, listeners, initLanguage } from './i18n.js';
import { liveState, fetchLive, demoInput, icsFor } from './live.js';

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* ---------- Street corner: step-by-step ---------- */
$('#fig').innerHTML = shovelScene('corner1');
$('#fig2').innerHTML = corner('corner2', true);
const svg1 = $('#corner1');
const steps = $$('.step');
const stepIO = new IntersectionObserver((es) => es.forEach((e) => {
  if (!e.isIntersecting) return;
  steps.forEach((s) => s.classList.remove('on'));
  e.target.classList.add('on');
  svg1.dataset.s = e.target.dataset.step;
}), { rootMargin: '-45% 0px -45% 0px' });
steps.forEach((s) => stepIO.observe(s));
steps[0].classList.add('on');
// The picture starts snowed-in (step 0) so step 1's snowfall plays when the reader gets there, not at page load.

/* ---------- Who clears this? ---------- */
const WHO_KEYS = ['sidewalk', 'corner', 'ramp', 'crosswalk', 'street', 'bus', 'hydrant', 'drain', 'building'];
const WHO_KIND = { sidewalk: 'law', corner: 'law', ramp: 'law', building: 'law', crosswalk: 'city', street: 'city', bus: 'city', hydrant: 'ask', drain: 'ask' };
const info = $('#info');
const keys = $('#keys');
let whoSel = 'ramp';
function renderKeys() {
  keys.innerHTML = '';
  WHO_KEYS.forEach((k) => {
    const b = document.createElement('button');
    b.className = 'chip';
    b.dataset.k = k;
    b.textContent = t(`who.${k}.t`);
    b.setAttribute('aria-pressed', k === whoSel);
    keys.appendChild(b);
  });
}
function pick(k) {
  whoSel = k;
  info.innerHTML = `<span class="tag ${WHO_KIND[k]}">${t(`who.${k}.tag`)}</span><h3>${t(`who.${k}.t`)}</h3>`
    + `<div class="who-line">${t(`who.${k}.who`)}</div><p class="lede" style="margin-top:14px">${t(`who.${k}.b`)}</p>`
    + `<p class="cite" style="margin-top:14px">${t(`who.${k}.c`)}</p>`;
  $$('#corner2 .hot').forEach((h) => h.classList.toggle('sel', h.dataset.k === k));
  $$('.chip', keys).forEach((c) => c.setAttribute('aria-pressed', c.dataset.k === k));
}
$('#corner2').addEventListener('click', (e) => { const h = e.target.closest('.hot'); if (h) pick(h.dataset.k); });
$('#corner2').addEventListener('keydown', (e) => {
  const h = e.target.closest('.hot');
  if (h && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); pick(h.dataset.k); }
});
keys.addEventListener('click', (e) => { const c = e.target.closest('.chip'); if (c) pick(c.dataset.k); });

/* ---------- Deadline calculator ---------- */
const TZ = SOMERVILLE.tz;
const dDate = $('#d-date');
const dTime = $('#d-time');
// Date formats per page language: US Spanish and Brazilian Portuguese. Latin digits everywhere, to match the rest of the page.
const LOCALE = { en: 'en-US', es: 'es-US', pt: 'pt-BR' };
function fmt(ms, opts) { const l = document.documentElement.lang; return new Intl.DateTimeFormat(LOCALE[l] || l || 'en-US', { timeZone: TZ, numberingSystem: 'latn', ...opts }).format(ms); }
const niceTime = (ms) => fmt(ms, { hour: 'numeric', minute: '2-digit' }).replace('AM', 'a.m.').replace('PM', 'p.m.');
function renderDeadline() {
  if (!dDate.value || !dTime.value) return;
  const [y, m, d] = dDate.value.split('-').map(Number);
  const [h, mi] = dTime.value.split(':').map(Number);
  const stop = zoned(y, m, d, h, mi);
  const r = deadline(stop);
  $('#d-out').textContent = niceTime(r.end);
  $('#d-day').textContent = fmt(r.end, { weekday: 'long', month: 'short', day: 'numeric' });
  const first = r.days[0];
  let why;
  if (stop < first.rise) why = t('why.beforeRise', { time: niceTime(first.rise) });
  else if (stop >= first.set) why = t('why.afterSet');
  else if (r.days.length > 1) {
    const used = (first.to - first.from) / 36e5;
    const hh = Math.floor(used);
    const mm = Math.round((used - hh) * 60);
    const dur = [hh ? t('why.hours', { h: hh }) : '', t('why.minutes', { m: mm })].filter(Boolean).join(' ');
    why = t('why.split', { dur });
  } else why = t('why.oneDay');
  $('#d-why').textContent = why;

  const W0 = 4, W1 = 21; // the strip shows 4 a.m. to 9 p.m.
  const pct = (ms) => { const w = wall(ms); return Math.max(0, Math.min(100, ((w.h + w.mi / 60) - W0) / (W1 - W0) * 100)); };
  $('#d-days').innerHTML = r.days.map((day, i) => {
    const noon = zoned(day.y, day.m, day.d, 12, 0);
    let inner = `<div class="dl" style="left:${pct(day.rise)}%;width:${pct(day.set) - pct(day.rise)}%"></div>`;
    if (day.from) inner += `<div class="ct" style="left:${pct(day.from)}%;width:${Math.max(0.6, pct(day.to) - pct(day.from))}%"></div>`;
    if (day.stop != null) {
      const s = wall(day.stop); const hrs = s.h + s.mi / 60;
      if (hrs >= W0 && hrs <= W1) inner += `<div class="mk" style="left:${pct(day.stop)}%" title="${t('track.stopped')}"></div>`;
    }
    if (i === r.days.length - 1 && day.to) inner += `<div class="mk end" style="left:calc(${pct(day.to)}% - 2px)" title="${t('track.deadline')}"></div>`;
    return `<div class="dayrow"><span class="lab">${fmt(noon, { weekday: 'short' })}<br><span class="muted" style="font-size:14px">${day.m}/${day.d}</span></span><div class="track">${inner}</div></div>`;
  }).join('');
}
[dDate, dTime].forEach((el) => el.addEventListener('input', () => {
  $$('.presets .chip').forEach((c) => c.setAttribute('aria-pressed', 'false'));
  renderDeadline();
}));
const pad = (n) => String(n).padStart(2, '0');
function nowStamp() { const w = wall(Date.now()); return `${w.y}-${pad(w.m)}-${pad(w.d)}T${pad(w.h)}:${pad(w.mi)}`; }
$('.presets').addEventListener('click', (e) => {
  const c = e.target.closest('.chip'); if (!c) return;
  const [dd, tt] = (c.dataset.p === 'now' ? nowStamp() : c.dataset.p).split('T');
  dDate.value = dd; dTime.value = tt;
  $$('.presets .chip').forEach((x) => x.setAttribute('aria-pressed', x === c));
  renderDeadline();
});
// In snow season (Oct 1 – May 1, the season fines are counted in) start at "just now" in Somerville,
// and move the example chips to today. Out of season, keep the January example written in the HTML.
{
  const w = wall(Date.now());
  if (w.m >= 10 || w.m <= 4) {
    const today = nowStamp().split('T')[0];
    $$('.presets .chip').forEach((c) => {
      if (c.dataset.p === 'now') c.hidden = false;
      else c.dataset.p = `${today}T${c.dataset.p.split('T')[1]}`;
    });
    $('.presets .chip[data-p="now"]').click();
  }
}

/* ---------- Salt or sand ---------- */
// Lowest pavement temperature (°F) each product still melts at. Source: Minnesota Pollution Control Agency.
const MELTS = [['rock', 15], ['mgcl', -10], ['cacl', -20], ['cma', 20], ['sand', null]];
const tR = $('#t-range');
function renderSalt() {
  const temp = +tR.value;
  $('#t-out').textContent = `${temp}°F`;
  $('#melts').innerHTML = MELTS.map(([k, lim]) => {
    const cls = lim === null ? 'grip' : temp >= lim ? 'ok' : 'no';
    const st = lim === null ? t('melts.grip') : temp >= lim ? t('melts.works') : t('melts.tooCold');
    const range = lim === null ? '' : ` <span class="muted" style="font-weight:500">${t('melts.upTo', { temp: `${lim < 0 ? '−' + Math.abs(lim) : lim}°F` })}</span>`;
    return `<div class="melt ${cls}"><span class="nm">${t(`melts.${k}`)}${range}</span><span class="st">${st}</span></div>`;
  }).join('');
}
tR.addEventListener('input', renderSalt);

/* ---------- Fines (Code of Ordinances Sec. 1-11) ---------- */
const FINES = { home: [100, 200, 300], big: [150, 300, 300] };
let fb = 'home';
let fn = 1;
function renderFines() {
  $('#f-out').textContent = `$${FINES[fb][fn - 1]}`;
  $('#f-ladder').innerHTML = FINES[fb].map((v, i) => `<div class="${i === fn - 1 ? 'on' : ''}" style="height:${30 + (v / 300) * 70}%">$${v}</div>`).join('');
  $$('[data-b]').forEach((b) => b.setAttribute('aria-pressed', b.dataset.b === fb));
  $$('[data-n]').forEach((b) => b.setAttribute('aria-pressed', +b.dataset.n === fn));
}
$$('[data-b]').forEach((b) => b.addEventListener('click', () => { fb = b.dataset.b; renderFines(); }));
$$('[data-n]').forEach((b) => b.addEventListener('click', () => { fn = +b.dataset.n; renderFines(); }));

/* ---------- Share this card: native share sheet with the PNG where the browser supports it, else open the PNG ---------- */
document.addEventListener('click', async (e) => {
  const a = e.target.closest('a.share'); if (!a || !navigator.canShare) return;
  e.preventDefault();
  try {
    const blob = await (await fetch(a.href)).blob();
    const file = new File([blob], `somerville-snow-${a.dataset.card}.png`, { type: 'image/png' });
    if (navigator.canShare({ files: [file] })) await navigator.share({ files: [file], url: location.href.split('#')[0] });
    else window.open(a.href, '_blank');
  } catch (err) { if (err.name !== 'AbortError') window.open(a.href, '_blank'); }
});

/* ---------- Nav highlight ---------- */
const links = $$('.nav a');
const secIO = new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting) links.forEach((a) => a.classList.toggle('on', a.getAttribute('href') === `#${e.target.id}`));
}), { rootMargin: '-40% 0px -55% 0px' });
links.forEach((a) => { const s = $(a.getAttribute('href')); if (s) secIO.observe(s); });

/* ---------- Replay teaser: the latest big storm's sidewalk reports by day (data/storms.json, from npm run data) ---------- */
let latestStorm = null;
fetch('data/storms.json').then((r) => r.json()).then((d) => { latestStorm = d.storms[d.storms.length - 1]; renderReplay(); }).catch(() => {});
function renderReplay() {
  const card = $('#replay-card');
  if (!card || !latestStorm) return;
  const st = latestStorm;
  const v = st.days.map((d) => d[2].sidewalk || 0); // 2 days before to 7 days after the last day of snow
  const mx = Math.max(1, ...v);
  const pk = v.indexOf(mx);
  const date = new Date(`${st.end}T12:00:00Z`).toLocaleDateString(document.documentElement.lang || 'en-US', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' });
  const bw = 32; const gap = 8; const W = 20 + 10 * (bw + gap) - gap; const base = 150; const H = 110;
  const bars = v.map((n, k) => {
    const h = Math.max(2, (n / mx) * H); const x = 10 + k * (bw + gap);
    return `<rect x="${x}" y="${base - h}" width="${bw}" height="${h}" rx="4" fill="${k === 2 ? '#10243A' : '#FF8A3D'}"/>`;
  }).join('');
  const px = 10 + pk * (bw + gap) + bw / 2;
  card.href = `storms/${st.end}.html`;
  const latestBtn = document.querySelector('#replay .btn:not(.ghost)'); if (latestBtn) latestBtn.href = card.href;
  card.innerHTML = `<span class="k">${t('replay.title')}</span><span class="sub">${t('replay.storm', { date, inches: st.snow })}</span>`
    + `<svg viewBox="0 0 ${W} 180" role="img" aria-label="${t('replay.title')}">${bars}`
    + `<path d="M6 ${base + 1} H${W - 6}" stroke="#C9D6E3" stroke-width="2"/>`
    + `<text x="${10 + 2 * (bw + gap) + bw / 2}" y="${base + 22}" text-anchor="middle" class="cap" font-size="15" fill="#47607C">${t('replay.last').toUpperCase()}</text>`
    + `<text x="${px}" y="${base - (mx / mx) * H - 8}" text-anchor="middle" class="cap" font-size="16" fill="#B93D06">${t('replay.peak', { n: mx }).toUpperCase()}</text></svg>`
    + `<span class="go">${t('replay.open')}</span>`;
}

/* ---------- Live storm mode (js/live.js): a banner while snow is on the way, falling or just ended ---------- */
let liveInput = null;
const liveDemo = new URLSearchParams(location.search).get('live');
const durTxt = (ms) => { const h = Math.floor(ms / 36e5); const m = Math.round((ms % 36e5) / 6e4); return h ? `${h} h ${m} min` : `${m} min`; };
const dayTime = (ms) => `${fmt(ms, { weekday: 'short' })} ${niceTime(ms)}`;
function renderLive() {
  const box = $('#live');
  if (!box || !liveInput) return;
  const now = liveDemo ? liveInput.now : Date.now();
  const st = liveState({ ...liveInput, now });
  $$('.now a').forEach((a) => a.classList.remove('lit'));
  if (st.phase === 'quiet') { box.hidden = true; return; }
  const lit = { forecast: '#saltsand', snowing: '#saltsand', stopped: '#deadline' }[st.phase];
  if (lit) $(`.now a[href="${lit}"]`)?.classList.add('lit');
  const alert = st.alerts[0] ? `<p class="live-alert">${t('live.alert', { event: st.alerts[0].event })}</p>` : '';
  let title = ''; let line = ''; let big = ''; let todo = []; let note = ''; let actions = '';
  const calendar = (dl) => `<button class="btn" data-ics="${dl}">${t('live.calendar')}</button>`;
  if (st.phase === 'forecast') {
    title = t('live.forecastTitle');
    line = st.forecastStart ? (st.inches >= 1 ? t('live.forecastInches', { inches: Math.round(st.inches), when: dayTime(st.forecastStart) }) : t('live.forecastMaybe', { when: dayTime(st.forecastStart) })) : '';
    todo = ['todoSalt', 'todoCar', 'todoAlerts']; note = t('live.forecastNote');
  } else if (st.phase === 'snowing') {
    title = t('live.snowingTitle'); line = t('live.snowingLine');
    if (st.estimatedDeadline) { big = `<p class="live-if">${t('live.snowingIf', { stop: dayTime(st.estimatedStop) })}</p><div class="live-big"><span>${t('live.shovelBy')}</span> <b>${dayTime(st.estimatedDeadline)}</b></div>`; actions = calendar(st.estimatedDeadline); note = t('live.estimate'); }
    todo = ['todoCar', 'todoHeart', 'todoAlerts'];
  } else if (st.phase === 'stopped') {
    title = t('live.stoppedTitle', { when: dayTime(st.stop) });
    big = `<div class="live-big"><span>${t('live.shovelBy')}</span> <b>${dayTime(st.deadline)}</b></div><p class="live-if">${t('live.left', { dur: durTxt(st.deadline - now) })}</p>`;
    line = st.moreSnow ? t('live.moreSnow', { when: dayTime(st.moreSnow) }) : '';
    actions = calendar(st.deadline); note = t('live.estimate');
    todo = ['todoPath', 'todoRamp', 'todoSand'];
  } else {
    title = t('live.passedTitle'); line = t('live.passedLine', { when: dayTime(st.deadline) });
    actions = `<a class="btn" href="tel:6176663311">${t('live.call')}</a>`;
    todo = ['todoReport', 'todoIce', 'todoSpace'];
  }
  box.innerHTML = (`<div class="wrap live-grid"><div class="live-main">
    <div class="live-tag"><i aria-hidden="true"></i>${liveDemo ? t('live.demo') : t('live.tag')}</div>
    <h2>${title}</h2>${alert}${line ? `<p class="live-line">${line}</p>` : ''}${big}
    ${actions ? `<div class="live-actions">${actions}</div>` : ''}
    <p class="live-note">${note}${note ? ' ' : ''}${liveDemo ? '' : t('live.updated', { time: niceTime(now) })}</p>
  </div><ul class="live-todo">${todo.map((k) => `<li>${t(`live.${k}`)}</li>`).join('')}</ul></div>`).replace(/\.\.(?=[\s<]|$)/g, '.'); // a time ending a sentence: 'a.m..' -> 'a.m.'
  box.hidden = false;
}
$('#live')?.addEventListener('click', (e) => {
  const b = e.target.closest('[data-ics]'); if (!b) return;
  const blob = new Blob([icsFor(+b.dataset.ics, t('live.icsTitle'), t('live.icsDetails'))], { type: 'text/calendar' });
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'shovel-deadline.ics';
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 1000);
});
async function loadLive() {
  try { liveInput = liveDemo ? demoInput(liveDemo) : await fetchLive(); } catch { liveInput = null; }
  renderLive();
}
loadLive();
if (!liveDemo) { setInterval(loadLive, 15 * 60e3); setInterval(renderLive, 60e3); }

/* ---------- Render, and re-render when the language changes ---------- */
function renderAll() { renderKeys(); pick(whoSel); renderDeadline(); renderSalt(); renderFines(); renderReplay(); renderLive(); }
listeners.add(renderAll);
renderAll();
initLanguage($('.bar .wrap'));
snowfall($('#snowfall'));

// Keep the sunrise math reachable from the console for checking: sunTimes(2027, 1, 15)
window.sunTimes = sunTimes;
