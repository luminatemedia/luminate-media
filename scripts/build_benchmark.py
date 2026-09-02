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
small, big = rows[0], rows[-1]            # minsta resp. storsta klassen
reach_x = big["views"] / small["views"]   # sa mycket mer racvidd ett toppkonto ger

MON = ["januari", "februari", "mars", "april", "maj", "juni", "juli",
       "augusti", "september", "oktober", "november", "december"]
d = datetime.datetime.fromisoformat(S["updated"].replace("Z", "+00:00"))
datum = f"{d.day} {MON[d.month - 1]} {d.year}"
mxv = max(r["views"] for r in rows)

sv = lambda n: f"{n:,}".replace(",", " ")
komma = lambda x: f"{x:.2f}".replace(".", ",")
komma1 = lambda x: f"{x:.1f}".replace(".", ",")

bars = "\n".join(
    f'''      <tr>
        <th scope="row">{r["band"]}</th>
        <td class="num big">{sv(r["views"])}</td>
        <td class="bar"><span style="width:{max(4, round(r["views"] / mxv * 100))}%"></span></td>
        <td class="num dim">{r["n"]}</td>
        <td class="num dim">{komma(r["ratio"])}×</td>
      </tr>''' for r in rows)

html = f'''<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TikTok-benchmark: mode &amp; beauty i Sverige — Luminate Media</title>
<meta name="description" content="Hur många visningar ger en svensk TikTok-kreatör per video? Medianvisningar per storleksklass — ett toppkonto når {komma1(reach_x)}× så många som ett mikrokonto. Mätt på {n_total} svenska kreatörer inom mode och beauty, {datum}.">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" href="/assets/luminate-icon-96.png" sizes="96x96">
<link rel="icon" type="image/png" href="/assets/luminate-icon-192.png" sizes="192x192">
<link rel="icon" type="image/svg+xml" href="/assets/luminate-icon.svg">
<link rel="apple-touch-icon" href="/assets/luminate-icon-180.png">
<link rel="canonical" href="https://www.luminatemedia.se/benchmark.html">
<meta name="theme-color" content="#2A1A1D">
<meta property="og:type" content="article">
<meta property="og:url" content="https://www.luminatemedia.se/benchmark.html">
<meta property="og:title" content="TikTok-benchmark: mode &amp; beauty i Sverige">
<meta property="og:description" content="En video från ett toppkonto når {komma1(reach_x)}× så många som en video från ett mikrokonto — {sv(big["views"])} mot {sv(small["views"])} visningar. Mätt på {n_total} svenska kreatörer.">
<meta property="og:image" content="https://www.luminatemedia.se/assets/og-share.png">
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
.brand{{display:flex;align-items:center;gap:12px;text-decoration:none;min-height:44px}}
.brand svg{{width:30px;height:auto;color:var(--pink)}}
.brand b{{font-family:var(--black);font-weight:400;font-size:14px;letter-spacing:.08em;text-transform:uppercase}}
.back{{font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.6);text-decoration:none;display:inline-flex;align-items:center;min-height:44px;padding:0 4px}}
.back:hover{{color:var(--pink)}}
.label{{display:block;font-size:11px;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:rgba(231,153,156,.9);margin-bottom:14px}}
h1{{font-family:var(--black);font-weight:400;font-size:clamp(30px,6.2vw,66px);line-height:1.04;text-transform:uppercase;margin-bottom:18px}}
h1 em{{font-family:"Instrument Serif",Georgia,serif;font-style:italic;text-transform:none;color:var(--pink);font-size:1.06em}}
.lead{{font-size:clamp(16px,1.9vw,20px);font-weight:500;color:rgba(255,255,255,.8);max-width:660px;margin-bottom:clamp(34px,5vw,54px)}}
.key{{border:1px solid rgba(231,153,156,.35);background:rgba(231,153,156,.08);border-radius:22px;
padding:clamp(24px,4vw,40px);margin-bottom:clamp(34px,5vw,54px);
display:grid;grid-template-columns:minmax(0,auto) 1fr;gap:clamp(22px,4vw,44px);align-items:center}}
@media (max-width:760px){{.key{{grid-template-columns:1fr;gap:20px}}}}
.key-fig{{display:flex;flex-direction:column;gap:8px;border-right:1px solid rgba(231,153,156,.28);padding-right:clamp(22px,4vw,44px)}}
@media (max-width:760px){{.key-fig{{border-right:0;border-bottom:1px solid rgba(231,153,156,.28);padding:0 0 18px}}}}
.key-fig b{{font-family:var(--black);font-weight:400;font-size:clamp(64px,12vw,132px);line-height:.85;color:var(--pink);letter-spacing:-.02em}}
.key-fig span{{font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.6);line-height:1.6}}
.key-line{{font-family:var(--black);font-weight:400;font-size:clamp(17px,2.3vw,25px);line-height:1.35;text-transform:none;margin-bottom:12px}}
.key-line strong{{color:var(--pink);font-weight:400;white-space:nowrap}}
.key-sub{{color:rgba(255,255,255,.68);font-weight:500;font-size:14.5px}}
h2{{font-family:var(--black);font-weight:400;font-size:clamp(20px,3vw,30px);text-transform:uppercase;margin:0 0 16px}}
.scroller{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;min-width:560px}}
th,td{{text-align:left;padding:14px 12px;border-bottom:1px solid rgba(231,153,156,.18);font-size:15px}}
thead th{{font-size:10.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.55);border-bottom-color:rgba(231,153,156,.35)}}
tbody th{{font-family:var(--black);font-weight:400;font-size:16px;white-space:nowrap}}
.num{{font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap}}
.num.big{{font-family:var(--black);font-weight:400;font-size:clamp(17px,2.3vw,23px)}}
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
  <p class="lead">Vi mäter våra kreatörers konton varje natt. Här är siffrorna öppet, uppdelat på storleksklass — medianvisningar per video, räknat på de senaste 20 videorna.</p>

  <div class="key">
    <div class="key-fig">
      <b>{komma1(reach_x)}×</b>
      <span>så mycket räckvidd ger<br>en video från ett toppkonto</span>
    </div>
    <div class="key-body">
      <p class="key-line"><strong>{sv(big["views"])}</strong> visningar från ett konto i toppklassen. <strong>{sv(small["views"])}</strong> från ett mikrokonto. För att nå lika långt behövs alltså tre mikrokonton — tre samarbeten, tre manus och tre tidplaner i stället för ett.</p>
      <p class="key-sub">Toppkontona bär dessutom igenkänning. En profil publiken redan känner konverterar annorlunda när videon förstärks som Spark Ad, och det är där annonsbudgeten betalar sig.</p>
    </div>
  </div>

  <h2>Per storleksklass</h2>
  <div class="scroller">
  <table>
    <thead>
      <tr><th scope="col">Följare</th><th scope="col">Median visningar/video</th><th scope="col">&nbsp;</th><th scope="col">Kreatörer</th><th scope="col">Per följare</th></tr>
    </thead>
    <tbody>
{bars}
    </tbody>
  </table>
  </div>
  <p class="note"><strong>Metod:</strong> {n_total} svenska TikTok-kreatörer inom mode, beauty och lifestyle — samtliga i Luminate Medias nätverk. Snittvisningar räknas på de senaste 20 videorna per kreatör, hämtade direkt från TikTok {datum}. Vi visar median i varje klass så att en enskild viral video inte drar upp resultatet. Hela nätverkets median: {sv(med_views)} visningar per video. Kolumnen längst till höger visar visningar per följare — mikrokonton ligger högre där, men når färre personer totalt, och det är totalen som avgör en kampanjs räckvidd. Underlaget är vårt eget nätverk, inte ett slumpmässigt urval av svenska konton — läs siffrorna som en branschindikation, inte som officiell statistik.</p>

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
