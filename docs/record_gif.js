// Records figures/explorer.gif: the explorer stepping through 1958-2019.
// Needs Node with Playwright (npm i playwright). Run from the repo root:
//   node docs/record_gif.js && python3 docs/make_gif.py
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const out = path.resolve('data/gif_frames'); fs.mkdirSync(out, { recursive: true });
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1000, height: 1400 }, colorScheme: 'light' });
  await p.goto('file://' + path.resolve('docs/index.html')); await p.waitForTimeout(800);
  const top = await p.evaluate(() => document.getElementById('box').getBoundingClientRect().top - 8);
  const bot = await p.evaluate(() => document.getElementById('hist').getBoundingClientRect().bottom + 30);
  let k = 0;
  for (let y = 1958; y <= 2019; y++) {
    await p.evaluate(y => { const r = document.getElementById('yr'); r.value = y; r.dispatchEvent(new Event('input')); }, y);
    await p.waitForTimeout(40);
    await p.screenshot({ path: `${out}/f${String(k++).padStart(3, '0')}.png`, clip: { x: 0, y: top, width: 1000, height: bot - top } });
  }
  await b.close();
})();
