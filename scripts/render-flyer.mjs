// npm run flyer: render docs/snow/flyer-phone.html to docs/snow/flyer-phone.png (1080 px wide, as tall as the flyer),
// the image people save or share. Needs `npm run dev` (or any server on docs/) at http://localhost:8080.
import { createRequire } from 'node:module';
// the project's Playwright (npm i -D playwright), or one installed globally
const { chromium } = await import('playwright').catch(() => createRequire(import.meta.url)('playwright'));
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 432, height: 900 }, deviceScaleFactor: 2.5 }); // 432 × 2.5 = 1080
await p.goto('http://localhost:8080/snow/flyer-phone.html?shot');
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(500);
await (await p.$('.page')).screenshot({ path: 'docs/snow/flyer-phone.png' });
await b.close();
console.log('wrote docs/snow/flyer-phone.png');
