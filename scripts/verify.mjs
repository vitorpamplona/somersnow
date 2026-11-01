// npm run verify: recompute the storm replays' published numbers from docs/data and check them against the pages.
// No downloads: it reads only docs/data and docs/storms. Pass --cache to also re-fingerprint the archives in .cache/
// against docs/data/sources.json (after `npm run data`). Exits 1 if anything doesn't match.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { deadline, zoned, wall } from '../docs/js/deadline.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const DATA = path.join(ROOT, 'docs', 'data');
const read = (f) => fs.readFileSync(path.join(ROOT, f), 'utf8');
const json = (f) => JSON.parse(read(f));
const DAY = 864e5;
let fails = 0; let checks = 0;
const check = (ok, what) => { checks++; if (!ok) { fails++; console.log(`  ✗ ${what}`); } };
const csvRows = (text) => {
  const rows = []; let row = []; let cell = ''; let q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') q = false; else cell += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(cell); cell = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(cell); rows.push(row); row = []; cell = ''; }
    else cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows;
};
const local = (s) => { const [d, t = '00:00'] = s.split('T'); const [y, m, dd] = d.split('-').map(Number); const [h, mi] = t.split(':').map(Number); return zoned(y, m, dd, h, mi); };
const addDays = (d, n) => new Date(Date.parse(`${d}T12:00:00Z`) + n * DAY).toISOString().slice(0, 10);
const html = (s) => s.replace(/&amp;/g, '&').replace(/&#x27;|&#39;/g, "'").replace(/&quot;/g, '"');

const { storms } = json('docs/data/storms.json');
console.log(`Checking ${storms.length} storm periods…`);

for (const st of storms) {
  const S = json(`docs/data/storm-${st.id}.json`);
  const n = S.hours.length;
  const t0 = local(S.from);
  const hrs = (Date.parse(`${S.to}:00Z`) - Date.parse(`${S.from}:00Z`)) / 36e5;
  check(n === hrs, `${st.id}: ${n} hours of weather, window is ${hrs} hours`);
  const k = S.groups.indexOf('sidewalk');
  const sw = (i) => (S.requests[i] || [])[k] || 0;

  // 1. the hourly table is the same data
  const csvFile = `docs/data/csv/${st.id}.csv`;
  check(fs.existsSync(path.join(ROOT, csvFile)), `${st.id}: ${csvFile} is missing (npm run pages writes it)`);
  const rows = fs.existsSync(path.join(ROOT, csvFile)) ? csvRows(read(csvFile)).filter((r) => r.length > 1) : [[]];
  const head = rows.shift();
  check(rows.length === n, `${st.id}: csv has ${rows.length} rows, expected ${n}`);
  const col = (name) => rows.map((r) => r[head.indexOf(name)]);
  check(col('311_sidewalk').reduce((a, v) => a + +v, 0) === Array.from({ length: n }, (_, i) => sw(i)).reduce((a, b) => a + b, 0), `${st.id}: csv sidewalk total differs from the json`);

  // 2. the raw records add up to the counts
  const rawDir = path.join(DATA, 'raw', st.id);
  const raw = (f) => (fs.existsSync(path.join(rawDir, f)) ? csvRows(fs.readFileSync(path.join(rawDir, f), 'utf8')).filter((r) => r.length > 1).slice(1) : null);
  const r311 = raw('311_snow.csv');
  if (r311) check(r311.filter((r) => r[1] === 'sidewalk').length === Array.from({ length: n }, (_, i) => sw(i)).reduce((a, b) => a + b, 0), `${st.id}: raw 311 sidewalk rows differ from the hourly counts`);
  const pol = raw('police.csv'); const P = S.extra && S.extra.police;
  if (pol && P) check(pol.filter((r) => r[2] === 'SNOEMTOW').length === P.tows.reduce((a, [, c]) => a + c, 0), `${st.id}: raw police tows differ from the tows lane`);
  const fire = raw('fire_dept.csv'); const F = S.extra && S.extra.fire;
  if (fire && F) check(fire.filter((r) => r[2] === 'medical').length === F.ems.now.reduce((a, b) => a + b, 0), `${st.id}: raw medical calls differ from the medical lane`);
  const wx = raw('weather_logan.csv');
  if (wx) { // the snowy hours on the page come from these reports
    const snowy = new Set(wx.filter((r) => +r[5] > 0).map((r) => r[0].slice(0, 13)));
    const pageSnowy = S.hours.map((h, i) => [h[0] > 0, new Date(t0 + i * 36e5)]).filter(([s]) => s).length;
    const inWin = [...snowy].filter((h) => { const t = local(h.replace(' ', 'T') + ':00'); return t >= t0 && t < t0 + n * 36e5; }).length;
    check(inWin === pageSnowy, `${st.id}: ${pageSnowy} snowy hours on the page, ${inWin} in the Logan reports`);
  }

  // 3. "died down" and "reports for N days", from the daily counts
  const days = Object.fromEntries(st.days.map(([d, , g]) => [d, g.sidewalk || 0]));
  const last = st.snowfalls[st.snowfalls.length - 1].end;
  let peak = 0; for (let d = st.start; d <= last; d = addDays(d, 1)) peak = Math.max(peak, days[d] ?? 0);
  let clear = null;
  for (let d = addDays(last, 1); days[d] !== undefined; d = addDays(d, 1)) {
    peak = Math.max(peak, days[d]); const thr = Math.max(2, peak / 20);
    if (days[addDays(d, 1)] === undefined) break; // window ends here (next storm): can't see the second day
    if (days[d] <= thr && days[addDays(d, 1)] <= thr) { clear = d; break; }
  }
  if (clear) check(clear === st.clear, `${st.id}: reports died down ${clear} by the rule, data says ${st.clear}`);
  check(st.lasted === Math.round((Date.parse(st.clear) - Date.parse(st.snowfalls[0].end)) / DAY), `${st.id}: lasted ${st.lasted} doesn't match clear`);

  // 4. the page shows these numbers
  const page = read(`docs/storms/${st.id}.html`);
  const lede = html((page.match(/id="r-lede"[^>]*>([^<]*)/) || [])[1] || '');
  if (st.lasted > 1) check(lede.includes(`kept coming for ${st.lasted} days`), `${st.id}: intro doesn't say ${st.lasted} days`);
  const base = Math.floor((local(S.snowStart) - t0) / 36e5);
  const total = Object.entries(S.requests).filter(([i]) => +i >= base).reduce((a, [, v]) => a + v[k], 0);
  const desc = html((page.match(/<meta name="description" content="([^"]*)"/) || [])[1] || '');
  check(desc.includes(`${total.toLocaleString('en-US')} sidewalk report`), `${st.id}: summary should say ${total} sidewalk reports`);
  const emb = page.match(/<script type="application\/json" id="storm-data">([\s\S]*?)<\/script>/);
  const E = emb && JSON.parse(emb[1].replace(/<\\\//g, '</'));
  check(E && JSON.stringify(E.storm) === JSON.stringify(S), `${st.id}: the page embeds different data than storm-${st.id}.json`);
}

// 5. the index's headline numbers
const snowy = storms.filter((s) => s.kind === 'snow');
const lasted = snowy.map((s) => s.lasted).sort((a, b) => a - b);
const med = lasted[Math.floor(lasted.length / 2)];
const week = lasted.filter((x) => x > 7).length; const two = lasted.filter((x) => x > 14).length;
const single = snowy.filter((s) => s.snowfalls.length === 1);
const peaks = single.filter((s) => {
  const v = s.days.map((d) => d[2].sidewalk || 0); const mx = Math.max(1, ...v);
  const off = Math.round((Date.parse(s.end) - Date.parse(s.days[0][0])) / DAY);
  const p = Math.max(...v) ? v.indexOf(mx) - off : -99; return p >= 1 && p <= 3;
}).length;
const index = html(read('docs/storms/index.html'));
for (const [what, txt] of [['typical storm', `keep coming for ${med} days in a typical storm`], ['over a week', `more than a week in ${week} of ${snowy.length} snow periods`],
  ['over two weeks', `more than two weeks in ${two}`], ['peaks', `in ${peaks} of ${single.length} storms`]]) check(index.includes(txt), `index: "${txt}" (${what}) not on the page`);

// 6. the deadline calculator against the City's own notices
for (const [id, city, ours] of [['2022-02-25', '12:30 p.m. Feb 26, 2022', '2022-02-26T12:24'], ['2026-03-03', '1 p.m. Feb 24, 2026', '2026-02-24T12:28']]) {
  const S = json(`docs/data/storm-${id}.json`);
  const main = S.snowfalls.reduce((a, f) => (f.snow > a.snow ? f : a));
  const w = wall(deadline(local(main.stop)).end);
  const got = `${w.y}-${String(w.m).padStart(2, '0')}-${String(w.d).padStart(2, '0')}T${String(w.h).padStart(2, '0')}:${String(w.mi).padStart(2, '0')}`;
  check(got === ours, `deadline for ${id}: calculator says ${got}, expected ${ours} (the City said ${city})`);
  console.log(`  deadline ${id}: calculator ${got.slice(11)}, City ${city}`);
}

// 7. optional: the downloaded archives are the ones recorded
if (process.argv.includes('--cache')) {
  const { downloads } = json('docs/data/sources.json');
  for (const d of downloads.filter((x) => x.cache_file)) {
    const f = path.join(ROOT, '.cache', d.cache_file);
    if (!fs.existsSync(f)) { console.log(`  · ${d.cache_file}: not downloaded here`); continue; }
    const h = crypto.createHash('sha256');
    await new Promise((res, rej) => fs.createReadStream(f).on('data', (c) => h.update(c)).on('end', res).on('error', rej));
    check(h.digest('hex') === d.sha256, `${d.cache_file}: fingerprint differs from sources.json (the source changed since)`);
  }
}

console.log(fails ? `${fails} of ${checks} checks failed.` : `All ${checks} checks passed.`);
process.exit(fails ? 1 : 0);
