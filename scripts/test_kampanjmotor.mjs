#!/usr/bin/env node
/* Testar kampanjmotorn mot sajtens riktiga data och priser.

   Kör:  node scripts/test_kampanjmotor.mjs            (regler, avslutar med felkod om något bryter)
         node scripts/test_kampanjmotor.mjs --exempel   (skriver ut förslag för exempelföretag)

   Priserna läses ur index.html med samma mönster som scripts/build_pricing.py,
   så testet går sönder om kalkylatorn och motorn glider isär.
*/
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const M = createRequire(import.meta.url)(path.join(root, 'assets', 'kampanj-motor.js'));
const h = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const json = f => JSON.parse(fs.readFileSync(path.join(root, 'data', f), 'utf8'));

const tiers = [...h.matchAll(/\{key:'(\w+)',\s*label:'([^']+)',\s*range:'([^']+)',\s*max:(\d+),\s*price:(\d+),\s*views:(\d+)\}/g)]
  .map(m => ({ key: m[1], label: m[2], range: m[3], max: +m[4], price: +m[5], views: +m[6] }));
const spark = [...h.matchAll(/\{label:'([^']+)',\s*up:\.(\d+)\}/g)].map(m => ({ label: m[1], up: +('0.' + m[2]) }));
const d = h.match(/return videos>=26\?(\d+) : videos>=20\?(\d+) : videos>=15\?(\d+) : videos>=10\?(\d+) : videos>=6\?(\d+) : videos>=3\?(\d+)/);
const trappa = [[26, +d[1]], [20, +d[2]], [15, +d[3]], [10, +d[4]], [6, +d[5]], [3, +d[6]]];
const discount = v => (trappa.find(([t]) => v >= t) || [0, 0])[1];
const fri = h.match(/const KM_FREE = \{count:(\d+), views:(\d+)\}/);
const namn = Object.fromEntries([...h.matchAll(/class="ccard" data-handle="([^"]+)"[^>]*>.*?<div class="cc-info"><b>([^<]+)<\/b>/g)].map(m => [m[1], m[2].replace(/&amp;/g, '&')]));

const stats = json('stats.json').creators, views = json('views.json').creators, match = json('match.json');
/* Samma sammanslagning som i kampanj-chatt.js: kort på sajten + övriga kreatörer i match.json. */
const alla = [...new Set([...Object.keys(namn), ...Object.keys(match.creators)])];
const ctx = {
  tiers, spark, discount, free: { count: 0, views: 0 }, match,   /* som chatten: inga gratiskreatörer */
  creators: alla.map(k => {
    const m = match.creators[k] || {};
    return { handle: k, name: namn[k] || m.name || k, kort: !!namn[k],
             followers: stats[k]?.followers || m.followers || 0, median: views[k]?.median || m.own || 0 };
  }),
};

let fel = 0;
const krav = (ok, text) => { if (!ok) { fel++; console.error('FEL: ' + text); } };

krav(tiers.length === 5 && spark.length === 4 && fri, 'priserna gick inte att läsa ur index.html');
krav(Object.keys(namn).length >= 20, 'kreatörskorten gick inte att läsa ur index.html');

const minsta = [...ctx.creators].filter(c => c.followers > 0 && c.median > 0)
  .sort((a, b) => a.followers - b.followers).slice(0, ctx.free.count).map(c => c.handle);
const amnen = match.categories.map(c => c.key);
const budgetar = [null, 5000, 15000, 30000, 60000, 100000, 250000];

for (const cats of [[], ...amnen.map(a => [a]), ['mode', 'skonhet'], ['har', 'hudvard', 'skonhet']]) {
  for (const budget of budgetar) for (const videos of [1, 2]) for (const sp of [false, 0, 3]) {
    const p = M.build({ cats, budget, videos, spark: sp }, ctx);
    const id = `${cats.join('+') || 'brett'} / ${budget} kr / ${videos} v / spark ${sp}`;
    if (budget) krav(p.total <= budget, `${id}: totalt ${p.total} över budget`);
    krav(new Set(p.creators.map(k => k.handle)).size === p.creators.length, `${id}: samma kreatör två gånger`);
    for (const k of p.creators) {
      krav(match.creators[k.handle], `${id}: ${k.handle} saknas i match.json`);
      krav(!minsta.includes(k.handle), `${id}: ${k.handle} är ett av de minsta kontona och ska inte prissättas`);
      krav(k.name && k.name !== k.handle, `${id}: ${k.handle} saknar namn`);
      krav(k.views >= k.price && k.followers >= 5000, `${id}: ${k.handle} ger under en visning per krona eller har under 5 000 följare`);
      if (cats.length) {
        const m = match.creators[k.handle];
        const harUnderlag = cats.some(c => m.cats[c] || m.profil.includes(c));
        krav(harUnderlag, `${id}: ${k.handle} föreslås utan underlag i ämnet`);
        if (k.niva === 'bevisad') krav(cats.some(c => m.cats[c]?.n >= M.MIN_BEVISAD), `${id}: ${k.handle} kallas bevisad utan ${M.MIN_BEVISAD} videor`);
      }
    }
    krav(p.list === p.creators.reduce((s, k) => s + k.price, 0) * videos, `${id}: listpriset stämmer inte med kreatörerna`);
    krav(p.disc === discount(p.creators.length * videos), `${id}: fel volymrabatt`);
    if (p.spark) krav(p.spark.rights > 0 && p.spark.media > 0 && p.spark.total === p.spark.rights + p.spark.media, `${id}: Spark-rekommendationen stämmer inte`);
    krav(p.free === null && p.videoCount === p.creators.length * videos, `${id}: gratiskreatörer får inte finnas i förslaget`);
    krav(p.total === p.organic, `${id}: Spark Ads får aldrig räknas in i totalen`);
    if (sp !== false) {
      const utan = M.build({ cats, budget, videos, spark: false }, ctx);
      krav(utan.creators.map(k => k.handle).join() === p.creators.map(k => k.handle).join(), `${id}: Spark Ads ändrade vilka kreatörer som valdes`);
    }
    if (!p.creators.length) krav(p.notes.length > 0, `${id}: tomt förslag utan förklaring`);
  }
}

krav(JSON.stringify(M.tolkaAmnen('vi säljer schampo och hårvård')) === '["har"]', 'tolkaAmnen: hårvård');
krav(M.tolkaAmnen('barnkläder och skor').includes('mode'), 'tolkaAmnen: kläder');
krav(M.tolkaAmnen('hej').length === 0, 'tolkaAmnen: inget ämne');
krav(JSON.stringify(M.tolkaAmnen('vi har 60 000 kr och säljer smink')) === '["skonhet"]', 'tolkaAmnen: verbet har är inte hår');
krav(M.tolkaAmnen('kolla vår hemsida och vårt material').length === 0, 'tolkaAmnen: hemsida och material är inga ämnen');
krav(M.tolkaBelopp('30 000 kr') === 30000 && M.tolkaBelopp('30k') === 30000 && M.tolkaBelopp('ca 45 tkr') === 45000, 'tolkaBelopp');
krav(M.tolkaBelopp('vet inte') === null, 'tolkaBelopp: inget tal');
krav(M.tolkaBudget('vi säljer barnkläder och har 50 000 kr, 2 videor per kreatör') === 50000, 'tolkaBudget: belopp bland antal');
krav(M.tolkaBudget('2 videor och 5 kreatörer i 30 dagar') === null, 'tolkaBudget: antal är ingen budget');
krav(M.tolkaBudget('30k') === 30000 && M.tolkaBudget('ca 45 tkr') === 45000 && M.tolkaBudget('60000') === 60000 && M.tolkaBudget('0,1 mkr') === 100000, 'tolkaBudget: enheter');
krav(M.tolkaBudget('vad kostar en video?') === null && M.tolkaBudget('500 kr') === null, 'tolkaBudget: inget belopp');
krav(M.tolkaAmnen('jag vill bygga en kampanj').length === 0, 'tolkaAmnen: en mening utan produkt ger inget ämne');
krav(M.tolkaAmnen('vi säljer barnkläder och leksaker').includes('mode'), 'tolkaAmnen: barnkläder');
krav(match.creators.lunamaarkovic && match.creators.ebbasimonsbacka, 'alla kreatörer i nätverket ska finnas i match.json');

if (process.argv.includes('--exempel')) {
  const kr = n => Math.round(n).toLocaleString('sv-SE') + ' kr';
  const fil = process.argv[process.argv.indexOf('--exempel') + 1];
  const exempel = fil && fs.existsSync(fil) ? JSON.parse(fs.readFileSync(fil, 'utf8')) : [
    { namn: 'Hårvårdsmärke', cats: ['har'], budget: 40000, spark: 0 },
    { namn: 'Modebutik', cats: ['mode'], budget: 60000, spark: false },
  ];
  for (const e of exempel) {
    const p = M.build({ cats: e.cats, budget: e.budget, videos: e.videos || 1, spark: e.spark ?? false }, ctx);
    console.log(`\n## ${e.namn} · ${e.cats.map(c => p.labels[c]).join(', ') || 'brett'} · budget ${kr(e.budget)}${e.spark === false || e.spark == null ? '' : ' · Spark ' + spark[e.spark].label}`);
    for (const k of p.creators) console.log(`- ${k.name} (${k.tierLabel}, ${kr(k.price)}): ≈ ${k.views.toLocaleString('sv-SE')} visningar · ${M.motivering(k, p.labels)}`);
    console.log(`  ${p.creators.length} kreatörer · ${p.videoCount} videor · ≈ ${p.views.toLocaleString('sv-SE')} visningar`);
    console.log(`  kreatörer ${kr(p.list)}${p.disc ? ' − ' + p.disc + ' %' : ''} = ${kr(p.organic)}` +
      ` · totalt ${kr(p.total)}` + (p.spark ? ` · OVANPÅ: Spark-rättigheter ${p.spark.videos} st ${kr(p.spark.rights)} + mediebudget ${kr(p.spark.media)}` : ''));
    for (const n of p.notes) console.log('  OBS: ' + n);
  }
}

console.log(fel ? `\n${fel} fel` : '\nAlla regler håller.');
process.exit(fel ? 1 : 0);
