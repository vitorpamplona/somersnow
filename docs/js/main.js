import { corner } from './corner.js';
import { shovelScene } from './shovel.js';
import { snowfall } from './snowfall.js';
import { deadline, sunTimes, wall, zoned, SOMERVILLE } from './deadline.js';
import { t, listeners, initLanguage } from './i18n.js';

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
function fmt(ms, opts) { return new Intl.DateTimeFormat(document.documentElement.lang || 'en-US', { timeZone: TZ, ...opts }).format(ms); }
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
$('.presets').addEventListener('click', (e) => {
  const c = e.target.closest('.chip'); if (!c) return;
  const [dd, tt] = c.dataset.p.split('T');
  dDate.value = dd; dTime.value = tt;
  $$('.presets .chip').forEach((x) => x.setAttribute('aria-pressed', x === c));
  renderDeadline();
});

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

/* ---------- Nav highlight ---------- */
const links = $$('.nav a');
const secIO = new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting) links.forEach((a) => a.classList.toggle('on', a.getAttribute('href') === `#${e.target.id}`));
}), { rootMargin: '-40% 0px -55% 0px' });
links.forEach((a) => { const s = $(a.getAttribute('href')); if (s) secIO.observe(s); });

/* ---------- Render, and re-render when the language changes ---------- */
function renderAll() { renderKeys(); pick(whoSel); renderDeadline(); renderSalt(); renderFines(); }
listeners.add(renderAll);
renderAll();
initLanguage($('.bar .wrap'));
snowfall($('#snowfall'));

// Keep the sunrise math reachable from the console for checking: sunTimes(2027, 1, 15)
window.sunTimes = sunTimes;
