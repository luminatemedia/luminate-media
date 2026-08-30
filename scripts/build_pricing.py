#!/usr/bin/env python3
"""Bygger priser.html ur kalkylatorns egna varden i index.html.

Priser, rabattrappa och Spark Ads-pasllag lases direkt ur index.html sa att
sidan och kalkylatorn aldrig kan visa olika siffror. Kors nattligen.
"""
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[1]
h = (root / "index.html").read_text(encoding="utf-8")

TIERS = [{"key": k, "label": l, "range": r, "max": int(m), "price": int(p), "views": int(v)}
         for k, l, r, m, p, v in re.findall(
             r"\{key:'(\w+)',\s*label:'([^']+)',\s*range:'([^']+)',\s*max:(\d+),\s*price:(\d+),\s*views:(\d+)\}", h)]
SPARK = [{"label": l, "up": int(u)} for l, u in re.findall(r"\{label:'([^']+)',\s*up:\.(\d+)\}", h)]
d = re.search(r'return videos>=26\?(\d+) : videos>=20\?(\d+) : videos>=15\?(\d+) : videos>=10\?(\d+) : videos>=6\?(\d+) : videos>=3\?(\d+)', h)
LADDER = [(26, int(d.group(1))), (20, int(d.group(2))), (15, int(d.group(3))),
          (10, int(d.group(4))), (6, int(d.group(5))), (3, int(d.group(6)))]
FREE_N, FREE_VIEWS = 3, 22000
KM_MAX = sum(t["max"] for t in TIERS)
W = [.15, .22, .25, .26, .12]

sv = lambda n: f"{int(round(n)):,}".replace(",", " ")
kr = lambda n: sv(n) + " kr"
views_fmt = lambda n: (f"{round(n/1e5)/10:.1f}".replace(".", ",") + " M") if n >= 1e6 else sv(round(n/1000)) + "K"


def alloc(n):
    n = min(n, KM_MAX)
    counts = [0] * len(TIERS)
    caps = [t["max"] for t in TIERS]
    if n >= 1: counts[0] = 1
    if n >= 2: counts[1] = 1
    left = n - sum(counts)
    for i, w in enumerate(W):
        counts[i] += min(int(w * left), caps[i] - counts[i])
    left = n - sum(counts)
    guard = 0
    while left > 0 and guard < 200:
        guard += 1
        placed = False
        for i in [2, 1, 3, 0, 4]:
            if left <= 0: break
            if counts[i] < caps[i]:
                counts[i] += 1; left -= 1; placed = True
        if not placed: break
    return counts


def discount(videos):
    for threshold, pct in LADDER:
        if videos >= threshold:
            return pct
    return 0


def calc(n, v=1):
    c = alloc(n)
    n = sum(c)
    lst = sum(c[i] * TIERS[i]["price"] for i in range(len(TIERS))) * v
    vw = (sum(c[i] * TIERS[i]["views"] for i in range(len(TIERS))) + FREE_VIEWS) * v
    disc = discount(n * v)
    return {"n": n, "counts": c, "list": lst, "disc": disc,
            "final": lst * (1 - disc / 100), "views": vw}


rows = "\n".join(
    f'''      <tr><th scope="row">{t["label"]}<span class="sub">{t["range"]}</span></th>'''
    f'''<td class="num">{kr(t["price"])}</td><td class="num dim">{sv(t["views"])}</td>'''
    f'''<td class="num dim">{t["max"]} st</td></tr>''' for t in TIERS)

ladder_rows = "\n".join(
    f'<tr><th scope="row">{n}+ videor</th><td class="num">−{p} %</td></tr>'
    for n, p in sorted(LADDER))

spark_rows = "\n".join(
    f'<tr><th scope="row">{s["label"]}</th><td class="num">+{s["up"]} %</td>'
    f'<td class="num dim">{kr(TIERS[3]["price"] * s["up"] / 100)}</td></tr>' for s in SPARK)

EX = [3, 5, 10, KM_MAX]
ex_cards = "\n".join(f'''    <div class="ex">
      <span class="ex-n">{e["n"]} kreatörer</span>
      <b>{kr(e["final"])}</b>
      <span class="ex-v">≈ {views_fmt(e["views"])} estimerade visningar</span>
      <span class="ex-d">{e["n"] + FREE_N} videor · −{e["disc"]} % volymrabatt</span>
    </div>''' for e in (calc(n) for n in EX))

cheapest, priciest = min(t["price"] for t in TIERS), max(t["price"] for t in TIERS)
five = calc(5)

FAQ = [
 ("Vad kostar influencer marketing i Sverige?",
  f"Hos oss kostar en creator-video mellan {kr(cheapest)} och {kr(priciest)} beroende på kreatörens räckvidd, och priset per video sjunker med upp till {LADDER[0][1]} % när ni bokar fler. En kampanj med fem kreatörer landar på {kr(five['final'])} och ger uppskattningsvis {views_fmt(five['views'])} visningar. Alla priser är exklusive moms."),
 ("Vad ingår i priset per video?",
  "Koncept, manus, inspelning, redigering, publicering, en revisionsrunda, deadlinehantering och rapportering. Videon ligger kvar publicerad i minst tolv månader. Ni godkänner både manus och färdig video innan publicering."),
 ("Varför kostar en kreatör mer än en annan?",
  "Vi prissätter på vad kontot faktiskt levererar, inte på följarantal. En kreatör med färre följare men högre snittvisningar kan kosta mer än en större kreatör som presterar sämre. Siffrorna hämtas från TikTok varje natt och räknas som snittet över de senaste 20 videorna."),
 ("Vad kostar Spark Ads?",
  f"Spark Ads-rättigheter är ett påslag på kreatörens grundpris: +{SPARK[0]['up']} % för {SPARK[0]['label']} upp till +{SPARK[-1]['up']} % för {SPARK[-1]['label']}. Ni köper dem först efter publicering, när ni sett vilka videor som presterat organiskt. Mediebudgeten betalar ni själva i ert eget annonskonto."),
 ("Finns det någon minsta beställning?",
  f"Nej. Ni kan boka en enskild video, och {FREE_N} mindre kreatörer följer alltid med utan kostnad oavsett hur stor beställningen är. Prisbilden blir dock bättre per video ju fler ni bokar."),
 ("Vad kostar det jämfört med att köpa annonsräckvidd?",
  "Publicerade CPM-nivåer för TikTok-annonsering 2026 ligger på ungefär 4–13 USD per 1 000 visningar. Organisk räckvidd genom creators har i våra kampanjer legat väsentligt under det, samtidigt som en rekommendation från en kreatör bär en trovärdighet en annons inte har."),
]
faq_html = "\n".join(f'''    <div class="faq-item">
      <h3>{q}</h3>
      <p>{a}</p>
    </div>''' for q, a in FAQ)

strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()
schema = [
 {"@context": "https://schema.org", "@type": "FAQPage",
  "mainEntity": [{"@type": "Question", "name": strip(q),
                  "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in FAQ]},
 {"@context": "https://schema.org", "@type": "Service",
  "name": "Creator marketing på TikTok", "serviceType": "Influencer marketing",
  "provider": {"@type": "ProfessionalService", "name": "Luminate Media", "@id": "https://luminatemedia.se/#org"},
  "areaServed": {"@type": "Country", "name": "Sverige"},
  "offers": [{"@type": "Offer", "name": f'{t["label"]} — {t["range"]}',
              "price": t["price"], "priceCurrency": "SEK",
              "description": f'En TikTok-video från en kreatör med {t["range"]}. Snittvisningar {sv(t["views"])}.'}
             for t in TIERS]},
 {"@context": "https://schema.org", "@type": "BreadcrumbList",
  "itemListElement": [
   {"@type": "ListItem", "position": 1, "name": "Luminate Media", "item": "https://luminatemedia.se/"},
   {"@type": "ListItem", "position": 2, "name": "Priser", "item": "https://luminatemedia.se/priser.html"}]},
]
schema_html = "\n".join('<script type="application/ld+json">\n' + json.dumps(s, ensure_ascii=False, indent=1) + '\n</script>' for s in schema)

LOGO = ('<svg viewBox="0 0 400 435" aria-hidden="true"><g transform="translate(0,435) scale(0.1,-0.1)">'
        '<path fill="currentColor" d="M62 2174 l3 -2119 1230 -2 c677 -2 1243 1 1259 5 29 8 29 8 -140 183 -93 96 -232 240 -309 320 '
        'l-140 147 -655 1 -655 0 -3 1499 -2 1500 -291 288 c-159 159 -292 291 -295 293 -2 2 -3 -949 -2 -2115z M3694 2953 '
        'c-136 -142 -386 -400 -554 -573 -168 -173 -387 -399 -485 -502 -98 -104 -182 -188 -185 -188 -4 0 -42 37 -86 83 -517 '
        '538 -911 945 -1141 1177 l-243 245 0 -459 0 -458 88 -92 c48 -51 247 -261 442 -467 315 -331 791 -834 891 -941 49 -53 '
        '20 -76 400 329 189 202 390 414 446 472 l102 106 1 -811 0 -812 23 -6 c12 -3 142 -6 290 -6 l267 0 0 1580 c0 869 -2 '
        '1580 -4 1580 -2 0 -115 -116 -252 -257z"/></g></svg>')

html = f'''<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" href="/assets/luminate-icon-96.png" sizes="96x96">
<link rel="icon" type="image/png" href="/assets/luminate-icon-192.png" sizes="192x192">
<link rel="icon" type="image/svg+xml" href="/assets/luminate-icon.svg">
<link rel="apple-touch-icon" href="/assets/luminate-icon-180.png">
<title>Vad kostar influencer marketing i Sverige? Priser 2026 — Luminate Media</title>
<meta name="description" content="En creator-video kostar {kr(cheapest)}–{kr(priciest)} beroende på räckvidd, och priset sjunker med upp till {LADDER[0][1]} % vid fler videor. Hela prislistan öppet, med volymrabatt, Spark Ads-påslag och räkneexempel.">
<link rel="canonical" href="https://luminatemedia.se/priser.html">
<meta name="theme-color" content="#2A1A1D">
<meta property="og:type" content="website">
<meta property="og:url" content="https://luminatemedia.se/priser.html">
<meta property="og:title" content="Vad kostar influencer marketing i Sverige?">
<meta property="og:description" content="Hela prislistan öppet: {kr(cheapest)}–{kr(priciest)} per creator-video, volymrabatt upp till {LADDER[0][1]} % och Spark Ads-påslag.">
<meta property="og:image" content="https://luminatemedia.se/assets/og-share.png">
<meta name="twitter:card" content="summary_large_image">
{schema_html}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Instrument+Serif:ital@1&family=Schibsted+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{--pink:#E7999C;--plum:#2A1A1D;--plum-3:#180D10;--white:#fff;
--black:"Archivo Black","Arial Black",sans-serif;--sans:"Schibsted Grotesk","Helvetica Neue",sans-serif;
--ease:cubic-bezier(.16,1,.3,1);--pad:clamp(20px,4.5vw,64px)}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--sans);background:linear-gradient(180deg,var(--plum) 0%,var(--plum-3) 100%);
color:var(--white);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;min-height:100vh}}
a{{color:inherit}}
::selection{{background:var(--pink);color:var(--plum)}}
.wrap{{max-width:900px;margin:0 auto;padding:clamp(26px,5vw,52px) var(--pad) 90px}}
.top{{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:clamp(34px,6vw,58px)}}
.brand{{display:flex;align-items:center;gap:12px;text-decoration:none}}
.brand svg{{width:28px;height:auto;color:var(--pink)}}
.brand b{{font-family:var(--black);font-weight:400;font-size:13px;letter-spacing:.08em;text-transform:uppercase}}
.back{{font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.6);text-decoration:none}}
.back:hover{{color:var(--pink)}}
.label{{display:block;font-size:11px;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:rgba(231,153,156,.9);margin-bottom:12px}}
h1{{font-family:var(--black);font-weight:400;font-size:clamp(28px,5.4vw,54px);line-height:1.06;text-transform:uppercase;margin-bottom:20px}}
h1 em{{font-family:"Instrument Serif",Georgia,serif;font-style:italic;text-transform:none;color:var(--pink);font-size:1.06em}}
.answer{{border-left:3px solid var(--pink);padding-left:clamp(16px,2.6vw,26px);margin-bottom:clamp(34px,5vw,52px)}}
.answer p{{font-size:clamp(16px,2vw,21px);font-weight:500;color:rgba(255,255,255,.9);max-width:660px}}
.answer strong{{color:var(--pink);font-weight:700;white-space:nowrap}}
h2{{font-family:var(--black);font-weight:400;font-size:clamp(20px,3.2vw,32px);text-transform:uppercase;margin:clamp(34px,5vw,54px) 0 8px}}
h2 em{{font-family:"Instrument Serif",Georgia,serif;font-style:italic;text-transform:none;color:var(--pink);font-size:1.06em}}
.intro{{color:rgba(255,255,255,.72);font-weight:500;margin-bottom:20px;max-width:660px}}
.scroller{{overflow-x:auto;position:relative}}
table{{width:100%;border-collapse:collapse;min-width:480px;margin-bottom:8px}}
th,td{{text-align:left;padding:14px 12px;border-bottom:1px solid rgba(231,153,156,.16);font-size:15px;vertical-align:top}}
thead th{{font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.5);border-bottom-color:rgba(231,153,156,.35)}}
tbody th{{font-family:var(--black);font-weight:400;font-size:16px;text-transform:uppercase}}
tbody th .sub{{display:block;font-family:var(--sans);font-weight:500;font-size:12.5px;text-transform:none;color:rgba(255,255,255,.5);margin-top:3px}}
.num{{font-variant-numeric:tabular-nums;font-weight:700;white-space:nowrap}}
.dim{{color:rgba(255,255,255,.5);font-weight:500}}
.note{{font-size:12.5px;color:rgba(255,255,255,.45);max-width:660px;margin-top:12px}}
.exs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(205px,1fr));gap:12px;margin-top:8px}}
.ex{{border:1px solid rgba(231,153,156,.25);border-radius:18px;padding:20px}}
.ex-n{{display:block;font-size:10.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--pink);margin-bottom:8px}}
.ex b{{display:block;font-family:var(--black);font-weight:400;font-size:clamp(19px,2.7vw,26px);line-height:1.05;margin-bottom:8px;white-space:nowrap}}
.ex-v{{display:block;font-size:13.5px;color:rgba(255,255,255,.75)}}
.ex-d{{display:block;font-size:12px;color:rgba(255,255,255,.45);margin-top:5px}}
.faq-item{{border-top:1px solid rgba(231,153,156,.18);padding:20px 0}}
.faq-item h3{{font-family:var(--black);font-weight:400;font-size:clamp(15.5px,2vw,19px);text-transform:uppercase;margin-bottom:9px}}
.faq-item p{{color:rgba(255,255,255,.8);font-weight:500;font-size:15px;max-width:680px}}
.cta{{margin-top:clamp(36px,6vw,56px);display:flex;gap:14px;flex-wrap:wrap}}
.book{{display:inline-block;font-family:var(--black);font-weight:400;font-size:13px;letter-spacing:.14em;
text-transform:uppercase;background:var(--pink);color:var(--plum);padding:18px 32px;border-radius:999px;
text-decoration:none;transition:transform .35s var(--ease)}}
.book:hover{{transform:translateY(-3px)}}
.book.ghost{{background:transparent;color:var(--white);box-shadow:inset 0 0 0 2px rgba(231,153,156,.7)}}
.foot{{margin-top:clamp(48px,8vw,78px);padding-top:22px;border-top:1px solid rgba(231,153,156,.18);
display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}}
.foot span,.foot a{{font-size:11px;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:rgba(255,255,255,.4)}}
@media (max-width:640px){{
  /* "I nätverket" är sekundär info — vi fäller in den så tabellen ryms utan svep */
  table{{min-width:0}}
  table th:nth-child(4),table td:nth-child(4){{display:none}}
  th,td{{padding:12px 8px;font-size:14px}}
  thead th{{font-size:9px;letter-spacing:.06em}}
  tbody th{{font-size:14.5px}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <a class="brand" href="/">{LOGO}<b>Luminate</b></a>
    <a class="back" href="/">← Till startsidan</a>
  </div>

  <span class="label">Priser · uppdaterade löpande</span>
  <h1>Vad kostar influencer marketing <em>i Sverige?</em></h1>

  <div class="answer">
    <p>En creator-video kostar <strong>{kr(cheapest)}–{kr(priciest)}</strong> beroende på kreatörens räckvidd. Priset per video sjunker med upp till <strong>{LADDER[0][1]} %</strong> ju fler videor ni bokar, och en kampanj med fem kreatörer landar på <strong>{kr(five['final'])}</strong> för uppskattningsvis <strong>{views_fmt(five['views'])} visningar</strong>. Alla priser är exklusive moms, och {FREE_N} mindre kreatörer följer alltid med utan kostnad.</p>
  </div>

  <h2>Pris <em>per video</em></h2>
  <p class="intro">Vi prissätter på vad kontot faktiskt levererar, inte på följarantal. Snittvisningarna nedan är medianen i varje klass, mätt på de senaste 20 videorna och hämtad från TikTok varje natt.</p>
  <div class="scroller">
  <table>
    <thead><tr><th scope="col">Storleksklass</th><th scope="col">Pris per video</th><th scope="col">Snittvisningar</th><th scope="col">I nätverket</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
  </div>
  <p class="note">Ingår per video: koncept, manus, inspelning, redigering, publicering, en revisionsrunda, deadlinehantering och rapportering. Ni godkänner manus och färdig video innan publicering, och videon ligger kvar i minst tolv månader.</p>

  <h2>Volymrabatt</h2>
  <p class="intro">Samordningen kostar lika mycket oavsett om kampanjen har tre eller tjugo kreatörer, och vi förhandlar bättre när vi bokar flera videor åt gången. Den skillnaden får ni.</p>
  <div class="scroller">
  <table>
    <thead><tr><th scope="col">Antal videor</th><th scope="col">Avdrag</th></tr></thead>
    <tbody>
{ladder_rows}
    </tbody>
  </table>
  </div>

  <h2>Spark Ads — <em>köp vinnarna</em></h2>
  <p class="intro">Vill ni annonsera med en video köper ni rättigheterna först efter publicering, när ni sett vad den gjorde organiskt. Påslaget räknas på kreatörens grundpris. Exempelkolumnen visar en kreatör i klassen {TIERS[3]["label"].lower()}.</p>
  <div class="scroller">
  <table>
    <thead><tr><th scope="col">Period</th><th scope="col">Påslag</th><th scope="col">Exempel</th></tr></thead>
    <tbody>
{spark_rows}
    </tbody>
  </table>
  </div>
  <p class="note">Mediebudgeten betalar ni själva i ert eget annonskonto och äger den fullt ut. Vill ni att vi sätter upp och optimerar kampanjerna tar vi 15 % av mediespenden.</p>

  <h2>Räkneexempel</h2>
  <p class="intro">Färdiga upplägg med organiska rättigheter, inklusive de {FREE_N} kreatörerna som följer med utan kostnad.</p>
  <div class="exs">
{ex_cards}
  </div>
  <p class="note">Visningarna är estimat byggda på varje klass faktiska medianvisningar, inte på löften. Räkna på ert eget upplägg i kalkylatorn på startsidan — den använder exakt samma siffror som den här sidan.</p>

  <h2>Vanliga frågor <em>om pris</em></h2>
{faq_html}

  <div class="cta">
    <a class="book" href="/#kreatorer">Räkna på er kampanj →</a>
    <a class="book ghost" href="https://calendar.app.google/8vFghCDtFN2itfJU8" target="_blank" rel="noopener">Boka möte</a>
  </div>

  <div class="foot">
    <a href="/">luminatemedia.se</a>
    <span>Lund — Sverige</span>
  </div>
</div>
</body>
</html>
'''
(root / "priser.html").write_text(html)
print(f"priser.html byggd — {len(TIERS)} klasser, {kr(cheapest)}–{kr(priciest)}, 5 kreatörer = {kr(five['final'])}")
