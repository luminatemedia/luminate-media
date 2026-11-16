#!/usr/bin/env node
/*
 * Renderar Luminate-logo-revealen (brand/logo-reveal/index.html) till MP4.
 *
 *   node scripts/render_logo_reveal.js                 # båda teman, alla format
 *   node scripts/render_logo_reveal.js pink 9x16 1x1   # bara valda teman/format
 *
 * Kräver: playwright (chromium) och ffmpeg. Videorna är utan ljud.
 * Varje bildruta ritas deterministiskt via window.frameDataURL(t) och skickas
 * som PNG till ffmpeg — ingen skärminspelning, så inga tappade frames.
 */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'brand', 'logo-reveal');
const ALL = ['9x16', '4x5', '1x1', '16x9'];
const THEMES = ['white', 'pink'];
const args = process.argv.slice(2);
const formats = args.filter(a => ALL.includes(a)).length ? args.filter(a => ALL.includes(a)) : ALL;
const themes = args.filter(a => THEMES.includes(a)).length ? args.filter(a => THEMES.includes(a)) : THEMES;
const MIME = { '.html': 'text/html', '.woff2': 'font/woff2', '.js': 'text/javascript', '.css': 'text/css' };

const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT)) { res.statusCode = 403; return res.end(); }
  fs.readFile(p, (err, data) => {
    if (err) { res.statusCode = 404; return res.end(); }
    res.setHeader('Content-Type', MIME[path.extname(p)] || 'application/octet-stream');
    res.end(data);
  });
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}/brand/logo-reveal/index.html`;
  const browser = await chromium.launch();

  for (const theme of themes) for (const f of formats) {
    const q = `?export&theme=${theme}&f=${f}`;
    const page = await browser.newPage();
    page.on('pageerror', e => console.error('page error:', e.message));
    await page.goto(base + q);
    await page.evaluate(() => window.ready);
    const { DUR, FPS } = await page.evaluate(() => ({ DUR: window.DUR, FPS: window.FPS }));
    const frames = Math.round(DUR * FPS);
    const name = `luminate-logo-reveal-${theme}-${f}`;
    const out = path.join(OUT, `${name}.mp4`);

    const ff = spawn('ffmpeg', [
      '-v', 'error', '-y',
      '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
      '-profile:v', 'high', '-movflags', '+faststart',
      out,
    ], { stdio: ['pipe', 'inherit', 'inherit'] });
    const done = new Promise((res, rej) => ff.on('close', c => (c ? rej(new Error(`ffmpeg exit ${c}`)) : res())));

    const t0 = Date.now();
    for (let i = 0; i < frames; i++) {
      const url = await page.evaluate(t => window.frameDataURL(t), i / FPS);
      const buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 60 === 0) process.stdout.write(`\r${name}: ${i}/${frames}`);
    }
    ff.stdin.end();
    await done;
    await page.close();
    const mb = (fs.statSync(out).size / 1e6).toFixed(1);
    console.log(`\r${name}: ${frames} frames -> ${path.relative(ROOT, out)} (${mb} MB, ${((Date.now() - t0) / 1000).toFixed(0)} s)`);

    // stillbild av slutrutan (för thumbnails / omslag)
    const still = await browser.newPage();
    await still.goto(base + q);
    await still.evaluate(() => window.ready);
    const png = await still.evaluate(t => window.frameDataURL(t, 'image/png'), DUR - 1 / FPS);
    fs.writeFileSync(path.join(OUT, `luminate-endcard-${theme}-${f}.png`), Buffer.from(png.split(',')[1], 'base64'));
    await still.close();
  }

  await browser.close();
  server.close();
})().catch(e => { console.error(e); process.exit(1); });
