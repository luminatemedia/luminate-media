#!/usr/bin/env python3
"""Bygger benchmark.html ur data/stats.json + data/views.json.

Siffrorna bakas in i HTML:en (inte hamtade i webblasaren) sa att sokmotorer,
lankforhandsvisningar och besokare utan JS ser dem. Kors nattligen.
"""
import datetime
import json
import pathlib
import statistics

root = pathlib.Path(__file__).resolve().parents[1]
S = json.loads((root / "data" / "stats.json").read_text())
V = json.loads((root / "data" / "views.json").read_text())
cre, vw = S["creators"], V["creators"]

BANDS = [("5–20K", 5000, 20000), ("20–60K", 20000, 60000), ("60–90K", 60000, 90000),
         ("90–150K", 90000, 150000), ("150K+", 150000, 10**9)]

rows = []
for name, lo, hi in BANDS:
    xs = [(cre[h]["followers"], vw[h]["avg"]) for h in vw
          if h in cre and lo <= cre[h]["followers"] < hi]
    if len(xs) < 2:
        continue
    rows.append({
        "band": name,
        "n": len(xs),
        "views": int(statistics.median(v for _, v in xs)),
        "ratio": statistics.median(v / f for f, v in xs),
    })

n_total = sum(r["n"] for r in rows)
all_views = [vw[h]["avg"] for h in vw if h in cre]
all_ratio = [vw[h]["avg"] / cre[h]["followers"] for h in vw
             if h in cre and cre[h]["followers"] > 1000]
med_views, med_ratio = int(statistics.median(all_views)), statistics.median(all_ratio)
best, worst = rows[0], rows[-1]
factor = round(best["ratio"] / worst["ratio"], 1)

MON = ["januari", "februari", "mars", "april", "maj", "juni", "juli",
       "augusti", "september", "oktober", "november", "december"]
d = datetime.datetime.fromisoformat(S["updated"].replace("Z", "+00:00"))
datum = f"{d.day} {MON[d.month - 1]} {d.year}"
mx = max(r["ratio"] for r in rows)

sv = lambda n: f"{n:,}".replace(",", " ")
komma = lambda x: f"{x:.2f}".replace(".", ",")

bars = "\n".join(
    f'''      <tr>
        <th scope="row">{r["band"]}</th>
        <td class="num">{sv(r["views"])}</td>
        <td class="num">{komma(r["ratio"])}×</td>
        <td class="bar"><span style="width:{max(4, round(r["ratio"] / mx * 100))}%"></span></td>
        <td class="num dim">{r["n"]}</td>
      </tr>''' for r in rows)

html = f'''<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TikTok-benchmark: mode &amp; beauty i Sverige — Luminate Media</title>
<meta name="description" content="Hur mycket räckvidd ger en svensk TikTok-kreatör per följare? Median­visningar per video och räckvidd per följare, uppdelat på storleksklass. Mätt på {n_total} svenska kreatörer, {datum}.">
<link rel="icon" href="/assets/luminate-icon-64.png" sizes="64x64">
<link rel="apple-touch-icon" href="/assets/luminate-icon-180.png">
<meta name="theme-color" content="#2A1A1D">
<meta property="og:type" content="article">
<meta property="og:url" content="https://luminatemedia.se/benchmark.html">
<meta property="og:title" content="TikTok-benchmark: mode &amp; beauty i Sverige">
<meta property="og:description" content="Mikro-kreatörer får {komma(best["ratio"])}× sitt följarantal i visningar per video. De största får {komma(worst["ratio"])}×. Mätt på {n_total} svenska kreatörer.">
<meta property="og:image" content="https://luminatemedia.se/assets/og-share.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Instrument+Serif:ital@1&family=Schibsted+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{--pink:#E7999C;--plum:#2A1A1D;--plum-2:#211316;--plum-3:#180D10;--white:#fff;
--black:"Archivo Black","Arial Black",sans-serif;--sans:"Schibsted Grotesk","Helvetica Neue",sans-serif;
--ease:cubic-bezier(.16,1,.3,1);--pad:clamp(20px,4.5vw,72px)}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--sans);background:linear-gradient(180deg,var(--plum) 0%,var(--plum-3) 100%);
color:var(--white);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;min-height:100vh}}
a{{color:inherit}}
::selection{{background:var(--pink);color:var(--plum)}}
.wrap{{max-width:940px;margin:0 auto;padding:clamp(26px,5vw,56px) var(--pad) 90px}}
.top{{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:clamp(40px,7vw,72px)}}
.brand{{display:flex;align-items:center;gap:12px;text-decoration:none}}
.brand svg{{width:30px;height:auto;color:var(--pink)}}
.brand b{{font-family:var(--black);font-weight:400;font-size:14px;letter-spacing:.08em;text-transform:uppercase}}
.back{{font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.6);text-decoration:none}}
.back:hover{{color:var(--pink)}}
.label{{display:block;font-size:11px;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:rgba(231,153,156,.9);margin-bottom:14px}}
h1{{font-family:var(--black);font-weight:400;font-size:clamp(30px,6.2vw,66px);line-height:1.04;text-transform:uppercase;margin-bottom:18px}}
h1 em{{font-family:"Instrument Serif",Georgia,serif;font-style:italic;text-transform:none;color:var(--pink);font-size:1.06em}}
.lead{{font-size:clamp(16px,1.9vw,20px);font-weight:500;color:rgba(255,255,255,.8);max-width:660px;margin-bottom:clamp(34px,5vw,54px)}}
.key{{border:1px solid rgba(231,153,156,.35);background:rgba(231,153,156,.08);border-radius:20px;
padding:clamp(22px,3.5vw,34px);margin-bottom:clamp(34px,5vw,54px)}}
.key b{{display:block;font-family:var(--black);font-weight:400;font-size:clamp(26px,5vw,54px);line-height:1.05;margin-bottom:10px}}
.key b span{{color:var(--pink)}}
.key p{{color:rgba(255,255,255,.8);font-weight:500;max-width:620px}}
h2{{font-family:var(--black);font-weight:400;font-size:clamp(20px,3vw,30px);text-transform:uppercase;margin:0 0 16px}}
.scroller{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;min-width:560px}}
th,td{{text-align:left;padding:14px 12px;border-bottom:1px solid rgba(231,153,156,.18);font-size:15px}}
thead th{{font-size:10.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.55);border-bottom-color:rgba(231,153,156,.35)}}
tbody th{{font-family:var(--black);font-weight:400;font-size:16px;white-space:nowrap}}
.num{{font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap}}
.dim{{color:rgba(255,255,255,.45);font-weight:500}}
.bar{{width:34%}}
.bar span{{display:block;height:9px;border-radius:999px;background:var(--pink)}}
.note{{font-size:12.5px;color:rgba(255,255,255,.45);margin-top:18px;max-width:660px}}
.cta{{margin-top:clamp(40px,6vw,64px);display:flex;gap:14px;flex-wrap:wrap;align-items:center}}
.book{{display:inline-block;font-family:var(--black);font-weight:400;font-size:13px;letter-spacing:.14em;
text-transform:uppercase;background:var(--pink);color:var(--plum);padding:18px 32px;border-radius:999px;
text-decoration:none;transition:transform .35s var(--ease)}}
.book:hover{{transform:translateY(-3px)}}
.book.ghost{{background:transparent;color:var(--white);box-shadow:inset 0 0 0 2px rgba(231,153,156,.7)}}
.foot{{margin-top:clamp(48px,8vw,80px);padding-top:24px;border-top:1px solid rgba(231,153,156,.18);
display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}}
.foot span{{font-size:11px;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:rgba(255,255,255,.4)}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <a class="brand" href="/">
      <svg viewBox="0 0 400 435" aria-hidden="true"><g transform="translate(0,435) scale(0.1,-0.1)"><path fill="currentColor" d="M62 2174 l3 -2119 1230 -2 c677 -2 1243 1 1259 5 29 8 29 8 -140 183 -93 96 -232 240 -309 320 l-140 147 -655 1 -655 0 -3 1499 -2 1500 -291 288 c-159 159 -292 291 -295 293 -2 2 -3 -949 -2 -2115z M3694 2953 c-136 -142 -386 -400 -554 -573 -168 -173 -387 -399 -485 -502 -98 -104 -182 -188 -185 -188 -4 0 -42 37 -86 83 -517 538 -911 945 -1141 1177 l-243 245 0 -459 0 -458 88 -92 c48 -51 247 -261 442 -467 315 -331 791 -834 891 -941 49 -53 20 -76 400 329 189 202 390 414 446 472 l102 106 1 -811 0 -812 23 -6 c12 -3 142 -6 290 -6 l267 0 0 1580 c0 869 -2 1580 -4 1580 -2 0 -115 -116 -252 -257z"/></g></svg>
      <b>Luminate</b>
    </a>
    <a class="back" href="/">← Till startsidan</a>
  </div>

  <span class="label">Benchmark · uppdaterad {datum}</span>
  <h1>Så mycket räckvidd ger en svensk <em>TikTok-kreatör</em></h1>
  <p class="lead">Vi mäter våra kreatörers konton varje natt. Här är siffrorna öppet, uppdelat på storleksklass — medianvisningar per video och hur många visningar varje följare faktiskt ger.</p>

  <div class="key">
    <b>Mikro-kreatörer får <span>{komma(best["ratio"])}×</span> sitt följarantal i visningar.<br>De största får <span>{komma(worst["ratio"])}×</span>.</b>
    <p>Skillnaden är {komma(factor).replace(",00", "")} gånger. Räckvidd följer alltså inte följarantalet — det är därför ett urval byggt på färska siffror slår ett urval byggt på storlek.</p>
  </div>

  <h2>Per storleksklass</h2>
  <div class="scroller">
  <table>
    <thead>
      <tr><th scope="col">Följare</th><th scope="col">Median visningar/video</th><th scope="col">Visningar per följare</th><th scope="col">&nbsp;</th><th scope="col">Kreatörer</th></tr>
    </thead>
    <tbody>
{bars}
    </tbody>
  </table>
  </div>
  <p class="note"><strong>Metod:</strong> {n_total} svenska TikTok-kreatörer inom mode, beauty och lifestyle — samtliga i Luminate Medias nätverk. Snittvisningar räknas på de senaste 20 videorna per kreatör, hämtade direkt från TikTok {datum}. Vi visar median i varje klass så att en enskild viral video inte drar upp resultatet. Hela nätverkets median: {sv(med_views)} visningar per video och {komma(med_ratio)}× följarantalet. Underlaget är vårt eget nätverk, inte ett slumpmässigt urval av svenska konton — läs siffrorna som en branschindikation, inte som officiell statistik.</p>

  <div class="cta">
    <a class="book" href="https://calendar.app.google/8vFghCDtFN2itfJU8" target="_blank" rel="noopener">Boka möte →</a>
    <a class="book ghost" href="/#kreatorer">Se kreatörerna →</a>
  </div>

  <div class="foot">
    <span>© 2026 Luminate Media</span>
    <span>Lund — Sverige</span>
  </div>
</div>
</body>
</html>
'''

(root / "benchmark.html").write_text(html)
print(f"benchmark.html byggd — {n_total} kreatörer, {len(rows)} klasser, {datum}")
