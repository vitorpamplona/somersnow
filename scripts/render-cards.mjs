// Renders every card in cards/src/ to a 1080×1920 PNG in docs/snow/cards/.
// Usage: npm run cards   (needs Playwright: npm i -D playwright && npx playwright install chromium)
import { readdir } from 'node:fs/promises';
import { fileURLToPath, pathToFileURL } from 'node:url';
import path from 'node:path';
import { chromium } from 'playwright';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const srcDir = path.join(root, 'cards', 'src');
const outDir = path.join(root, 'docs', 'snow', 'cards');
const only = process.argv.slice(2);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
for (const f of (await readdir(srcDir)).filter((f) => f.endsWith('.html')).sort()) {
  if (only.length && !only.some((o) => f.includes(o))) continue;
  await page.goto(pathToFileURL(path.join(srcDir, f)).href, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(outDir, f.replace('.html', '.png')), clip: { x: 0, y: 0, width: 1080, height: 1920 } });
  console.log('rendered', f);
}
await browser.close();
