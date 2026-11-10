// npm run lights: render the "Somerville's lights" animation for the cards gallery, from the pulse page in its
// Holiday lights look (docs/bus-pulse.html#lights): the evening rush, 4:30 to 6:30 p.m., in 12 seconds, phone size.
// Writes docs/snow/cards/somerville-lights.gif (480×854, 12 fps), .mp4 (540×960, 15 fps) and .jpg (the poster).
// Needs `npm run dev` (or any server on docs/) at http://localhost:8080, and ffmpeg.
// The page's clock is driven frame by frame (no real time), so every frame is evenly spaced and sharp (2×).
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const { chromium } = await import('playwright').catch(() => createRequire(import.meta.url)('playwright'));

const FPS = 15, SECONDS = 12, START = 16.5 * 60, END = 18.5 * 60;   // 10 minutes of the day a second
const OUT = 'docs/snow/cards/somerville-lights';
const dir = mkdtempSync(join(tmpdir(), 'lights-'));

const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 405, height: 720 }, deviceScaleFactor: 2 });
await p.addInitScript(() => {                         // a clock the script moves, instead of the real one
  window.__fake = 0; const real = performance.now.bind(performance);
  performance.now = () => (window.__drive ? window.__fake : real());
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = (cb) => (window.__drive ? 0 : raf(cb));
});
await p.goto('http://localhost:8080/bus-pulse.html#lights');
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(800);
// only the title, the clock and the map; a footer with the address
await p.addStyleTag({ content: `
  .bar,.dock,.stats,.key,#about,#tip{display:none!important}
  .hud{left:0;right:0;top:34px;text-align:center;max-width:none}
  .hud h1{font-size:34px}
  .hud .sub{font-size:15px}
  .clock{font-size:64px;margin-top:8px}
  .gfoot{position:absolute;left:0;right:0;bottom:26px;text-align:center;pointer-events:none}
  .gfoot b{font:800 22px/1 'Barlow Condensed',sans-serif;letter-spacing:1.5px;text-transform:uppercase;color:#fff}
  .gfoot b span{color:#FF8A3D}
  .gfoot div{margin-top:6px;font-size:13px;color:#A9C4E4}` });
await p.evaluate((START) => {
  const f = document.createElement('div'); f.className = 'gfoot';
  f.innerHTML = '<b>Somer<span>Walks</span>.org</b><div>Every weekday bus, every stop · red: getting on · green: getting off</div>';
  document.querySelector('.stage').appendChild(f);
  window.__drive = true; window.__fake = 100000;
  size(); sizeWave();
  const top = 190, bottom = 90;                        // Somerville between the title and the footer
  const k = Math.min((W - 30) / (HOME.x1 - HOME.x0), (H - top - bottom) / (HOME.y1 - HOME.y0));
  K0 = k; view = { k, x: (HOME.x0 + HOME.x1) / 2, y: (HOME.y0 + HOME.y1) / 2 - ((top - bottom) / 2) / k };
  makeSnow(); viewChanged(); playing = true;
  seek(START - 30);                                    // half an hour early, so the lights are already on
  for (let i = 0; i < 30; i++) { window.__fake += 1000 / 15; advance(T + 1); draw(1 / 15); }
}, START);
const n = FPS * SECONDS, step = (END - START) / n;
for (let i = 0; i < n; i++) {
  await p.evaluate(({ step, FPS }) => { window.__fake += 1000 / FPS; advance(T + step); draw(1 / FPS); hud(true); }, { step, FPS });
  await p.screenshot({ path: join(dir, `f${String(i).padStart(4, '0')}.png`) });
}
await b.close();

const ff = (...args) => execFileSync('ffmpeg', ['-loglevel', 'error', '-y', ...args], { stdio: 'inherit' });
const frames = ['-framerate', String(FPS), '-i', join(dir, 'f%04d.png')];
// GIF: 12 fps, 480 wide, 128 colors (the snow changes every frame, so a bigger GIF grows past what apps take)
ff(...frames, '-vf', 'fps=12,scale=480:854:flags=lanczos,palettegen=max_colors=128:stats_mode=diff', join(dir, 'pal.png'));
ff(...frames, '-i', join(dir, 'pal.png'), '-lavfi', 'fps=12,scale=480:854:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle', '-loop', '0', OUT + '.gif');
ff(...frames, '-vf', 'scale=540:960:flags=lanczos,format=yuv420p', '-c:v', 'libx264', '-crf', '20', '-movflags', '+faststart', OUT + '.mp4');
ff('-i', join(dir, `f${String(Math.round(n * 0.6)).padStart(4, '0')}.png`), '-vf', 'scale=540:960:flags=lanczos', '-q:v', '3', OUT + '.jpg');
rmSync(dir, { recursive: true, force: true });
console.log(`wrote ${OUT}.gif, .mp4, .jpg`);
