// npm run letter: print PTAC's letter to the City Council as a US Letter PDF.
// scripts/build_letter.py first turns research/ordinance-proposals.md into .cache/letter.html;
// this prints that page with Chromium. Fonts come from Google Fonts, so it needs the network.
// Usage: node scripts/print-letter.mjs [input.html] [output.pdf]
import { createRequire } from 'node:module';
import path from 'node:path';
// the project's Playwright (npm i -D playwright), or one installed globally
const { chromium } = await import('playwright').catch(() => createRequire(import.meta.url)('playwright'));
const [inp = '.cache/letter.html', out = 'research/ordinance-proposals.pdf'] = process.argv.slice(2);
const footer = '<div style="width:100%;font:8px Helvetica,Arial,sans-serif;color:#5F5F5F;padding:0 0.9in;'
  + 'display:flex;justify-content:space-between"><span>Somerville PTAC · Sidewalk snow rules: proposed amendments</span>'
  + '<span><span class="pageNumber"></span> of <span class="totalPages"></span></span></div>';
const b = await chromium.launch();
const p = await b.newPage();
await p.goto('file://' + path.resolve(inp), { waitUntil: 'networkidle' });
await p.evaluate(() => document.fonts.ready);
await p.pdf({ path: out, format: 'Letter', printBackground: true, preferCSSPageSize: true,
  displayHeaderFooter: true, headerTemplate: '<span></span>', footerTemplate: footer });
await b.close();
console.log('wrote', out);
