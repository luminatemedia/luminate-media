#!/usr/bin/env python3
"""Bygger en mediakit-sida per kreatör: kreatorer/<handle>.html.

Kreatörskorten på startsidan länkar hit i stället för direkt till TikTok.
Kontakten går alltid via kreatörens @luminatemedia.se-adress (data/creators.json),
så att förfrågningar om samarbeten hamnar hos oss.

Siffrorna läses ur data/stats.json (följare, likes) och data/views.json
(snitt och median över de senaste 20 videorna) — samma källor som startsidan.
Prisklassen följer TIERS i index.html, samma som priser.html. Körs nattligen.
"""
import html as H
import json
import pathlib
import re
from datetime import datetime
from urllib.parse import quote

root = pathlib.Path(__file__).resolve().parents[1]
idx = (root / "index.html").read_text(encoding="utf-8")
prices = (root / "priser.html").read_text(encoding="utf-8")
creators = json.loads((root / "data/creators.json").read_text(encoding="utf-8"))
stats = json.loads((root / "data/stats.json").read_text(encoding="utf-8"))
views = json.loads((root / "data/views.json").read_text(encoding="utf-8"))

TIERS = [{"label": l, "range": r, "price": int(p)}
         for l, r, p in re.findall(r"\{key:'\w+',\s*label:'([^']+)',\s*range:'([^']+)',\s*max:\d+,\s*price:(\d+),", idx)]
FONTS = re.search(r"<style>\s*(@font-face.*?)</style>", prices, re.S).group(1)
LOGO = re.search(r'<a class="brand" href="/">(<svg.*?</svg>)', prices, re.S).group(1)
BOOK = "https://calendar.app.google/8vFghCDtFN2itfJU8"

sv = lambda n: f"{int(round(n)):,}".replace(",", " ")


def short(n):
    if n is None:
        return "–"
    if n >= 1e6:
        return f"{n/1e6:.1f}".replace(".", ",") + " M"
    if n >= 1e4:
        return f"{round(n/1000)}K"
    return sv(n)


def tier(followers):
    # Klassgränser enligt prislistan: 190K+, 90K+, 60K+, 20K+, annars micro.
    bounds = [190_000, 90_000, 60_000, 20_000, 0]
    for t, b in zip(TIERS, bounds):
        if followers >= b:
            return t
    return TIERS[-1]


try:
    upd = datetime.fromisoformat(stats["updated"].replace("Z", "+00:00"))
    MON = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
    updated = f"{upd.day} {MON[upd.month-1]} {upd.year}"
except Exception:
    updated = ""

out_dir = root / "kreatorer"
out_dir.mkdir(exist_ok=True)

for handle, c in creators.items():
    s = stats.get("creators", {}).get(handle, {})
    v = views.get("creators", {}).get(handle, {})
    followers = s.get("followers")
    t = tier(followers or 0)
    name = H.escape(c["name"])
    email = H.escape(c["email"])
    has_video = (root / "assets/creators/video" / f"{handle}.mp4").exists()
    media = (f'<video src="/assets/creators/video/{handle}.mp4" poster="/assets/creators/{handle}.webp" '
             f'muted loop playsinline autoplay preload="metadata"></video>' if has_video
             else f'<img src="/assets/creators/{handle}.webp" alt="{name}" width="400" height="500">')
    tiles = [
        (short(followers), "följare"),
        (short(s.get("likes")), "likes totalt"),
        (short(v.get("avg")), "snittvisningar per video"),
        (short(v.get("median")), "median per video"),
    ]
    tiles_html = "\n".join(f'      <div class="tile"><b>{a}</b><span>{b}</span></div>' for a, b in tiles)
    subject = quote(f"Samarbete med {c['name']}")
    page = f'''<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/svg+xml" href="/assets/luminate-icon.svg">
<link rel="apple-touch-icon" href="/assets/luminate-icon-180.png">
<title>{name} — media kit · Luminate Media</title>
<meta name="description" content="Media kit för {name} (@{handle}) på TikTok: följare, snittvisningar och kontakt för samarbeten via Luminate Media.">
<link rel="canonical" href="https://www.luminatemedia.se/kreatorer/{handle}.html">
<meta name="theme-color" content="#2A1A1D">
<meta property="og:type" content="profile">
<meta property="og:title" content="{name} — media kit">
<meta property="og:description" content="{short(followers)} följare på TikTok. Samarbeten via Luminate Media.">
<meta property="og:image" content="https://www.luminatemedia.se/assets/creators/{handle}.webp">
<link rel="preload" href="/assets/fonts/archivo-black.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/schibsted-grotesk.woff2" as="font" type="font/woff2" crossorigin>
<style>
{FONTS}</style>
<style>
:root{{--pink:#E7999C;--plum:#2A1A1D;--plum-3:#180D10;--white:#fff;
--black:"Archivo Black","Arial Black",sans-serif;--sans:"Schibsted Grotesk","Helvetica Neue",sans-serif;
--ease:cubic-bezier(.16,1,.3,1);--pad:clamp(20px,4.5vw,64px)}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--sans);background:linear-gradient(180deg,var(--plum) 0%,var(--plum-3) 100%);
color:var(--white);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;min-height:100vh}}
a{{color:inherit}}
::selection{{background:var(--pink);color:var(--plum)}}
.wrap{{max-width:960px;margin:0 auto;padding:clamp(26px,5vw,52px) var(--pad) 90px}}
.top{{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:clamp(30px,5vw,50px)}}
.brand{{display:flex;align-items:center;gap:12px;text-decoration:none;min-height:44px}}
.brand svg{{width:28px;height:auto;color:var(--pink)}}
.brand b{{font-family:var(--black);font-weight:400;font-size:13px;letter-spacing:.08em;text-transform:uppercase}}
.back{{font-size:11px;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:rgba(255,255,255,.6);text-decoration:none;display:inline-flex;align-items:center;min-height:44px;padding:0 4px}}
.back:hover{{color:var(--pink)}}
.kit{{display:grid;grid-template-columns:minmax(0,320px) 1fr;gap:clamp(24px,4vw,48px);align-items:start}}
.media{{border-radius:22px;overflow:hidden;aspect-ratio:4/5;background:#000;box-shadow:0 22px 44px rgba(0,0,0,.35)}}
.media video,.media img{{width:100%;height:100%;object-fit:cover;display:block}}
.label{{display:block;font-size:11px;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:rgba(231,153,156,.9);margin-bottom:10px}}
h1{{font-family:var(--black);font-weight:400;font-size:clamp(30px,5.6vw,56px);line-height:1.04;text-transform:uppercase;margin-bottom:6px}}
.handle{{font-size:15px;font-weight:600;color:rgba(255,255,255,.6);margin-bottom:24px}}
.tiles{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin-bottom:12px}}
.tile{{border:1px solid rgba(231,153,156,.25);border-radius:16px;padding:16px 18px}}
.tile b{{display:block;font-family:var(--black);font-weight:400;font-size:clamp(22px,3vw,30px);line-height:1.1}}
.tile span{{display:block;font-size:12.5px;color:rgba(255,255,255,.6);margin-top:4px}}
.price{{border-left:3px solid var(--pink);padding:4px 0 4px 16px;margin:18px 0 26px;font-weight:500;color:rgba(255,255,255,.85)}}
.price strong{{color:var(--pink);white-space:nowrap}}
.contact{{background:rgba(231,153,156,.1);border:1px solid rgba(231,153,156,.3);border-radius:20px;padding:22px}}
.contact h2{{font-family:var(--black);font-weight:400;font-size:18px;text-transform:uppercase;margin-bottom:6px}}
.contact p{{font-size:14.5px;color:rgba(255,255,255,.75);margin-bottom:16px}}
.btns{{display:flex;gap:10px;flex-wrap:wrap}}
.book{{display:inline-block;font-family:var(--black);font-weight:400;font-size:12px;letter-spacing:.12em;
text-transform:uppercase;background:var(--pink);color:var(--plum);padding:15px 24px;border-radius:999px;
text-decoration:none;transition:transform .35s var(--ease)}}
.book:hover{{transform:translateY(-3px)}}
.book.ghost{{background:transparent;color:var(--white);box-shadow:inset 0 0 0 2px rgba(231,153,156,.7)}}
.mail{{display:block;font-weight:700;color:var(--pink);font-size:15px;margin-bottom:16px;word-break:break-all}}
.social{{margin-top:22px;display:flex;gap:10px;flex-wrap:wrap}}
.note{{font-size:12.5px;color:rgba(255,255,255,.45);margin-top:22px;max-width:620px}}
.foot{{margin-top:clamp(44px,7vw,70px);padding-top:22px;border-top:1px solid rgba(231,153,156,.18);
display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}}
.foot span,.foot a{{font-size:11px;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:rgba(255,255,255,.4)}}
@media (max-width:700px){{.kit{{grid-template-columns:1fr}} .media{{max-width:340px}}}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
</head>
<body>
<main>
<div class="wrap">
  <div class="top">
    <a class="brand" href="/">{LOGO}<b>Luminate</b></a>
    <a class="back" href="/#kreatorer">← Alla kreatörer</a>
  </div>
  <div class="kit">
    <div class="media">{media}</div>
    <div>
      <span class="label">Media kit{(" · uppdaterat " + updated) if updated else ""}</span>
      <h1>{name}</h1>
      <div class="handle">@{handle} · TikTok</div>
      <div class="tiles">
{tiles_html}
      </div>
      <div class="price">Storleksklass: <strong>{H.escape(t["label"])}</strong> · från <strong>{sv(t["price"])} kr</strong> per video, före volymrabatt. <a href="/priser.html">Hela prislistan →</a></div>
      <div class="contact">
        <h2>Samarbeten</h2>
        <p>Alla förfrågningar om samarbeten med {name} går via Luminate Media. Vi återkommer med upplägg och pris.</p>
        <a class="mail" href="mailto:{email}?subject={subject}">{email}</a>
        <div class="btns">
          <a class="book" href="mailto:{email}?subject={subject}">Skicka förfrågan</a>
          <a class="book ghost" href="{BOOK}" target="_blank" rel="noopener">Boka möte</a>
        </div>
      </div>
      <div class="social">
        <a class="book ghost" href="https://www.tiktok.com/@{handle}" target="_blank" rel="noopener">TikTok →</a>
      </div>
      <p class="note">Siffrorna hämtas automatiskt från TikTok varje natt. Snitt och median räknas på de senaste 20 videorna.</p>
    </div>
  </div>
  <div class="foot">
    <a href="/">luminatemedia.se</a>
    <span>Lund — Sverige</span>
  </div>
</div>
</main>
</body>
</html>
'''
    (out_dir / f"{handle}.html").write_text(page, encoding="utf-8")

print(f"byggde {len(creators)} mediakit-sidor i kreatorer/")
