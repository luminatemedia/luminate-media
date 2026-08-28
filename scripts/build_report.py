#!/usr/bin/env python3
"""Bygger en kampanjrapport per kampanj: rapport-<slug>.html

Sidan uppdateras varje natt sa lange kampanjen loper. Siffrorna bakas in i
HTML:en. Rapporten ar noindex och lankas inte publikt - den delas som lank.
"""
import datetime
import json
import pathlib

root = pathlib.Path(__file__).resolve().parents[1]
camp_dir = root / "data" / "campaigns"
MON = ["jan", "feb", "mars", "april", "maj", "juni", "juli", "aug", "sep", "okt", "nov", "dec"]
sv = lambda n: f"{int(n):,}".replace(",", " ")

LOGO = ('<svg viewBox="0 0 400 435" aria-hidden="true"><g transform="translate(0,435) scale(0.1,-0.1)">'
        '<path fill="currentColor" d="M62 2174 l3 -2119 1230 -2 c677 -2 1243 1 1259 5 29 8 29 8 -140 183 -93 96 -232 240 -309 320 '
        'l-140 147 -655 1 -655 0 -3 1499 -2 1500 -291 288 c-159 159 -292 291 -295 293 -2 2 -3 -949 -2 -2115z M3694 2953 '
        'c-136 -142 -386 -400 -554 -573 -168 -173 -387 -399 -485 -502 -98 -104 -182 -188 -185 -188 -4 0 -42 37 -86 83 -517 '
        '538 -911 945 -1141 1177 l-243 245 0 -459 0 -458 88 -92 c48 -51 247 -261 442 -467 315 -331 791 -834 891 -941 49 -53 '
        '20 -76 400 329 189 202 390 414 446 472 l102 106 1 -811 0 -812 23 -6 c12 -3 142 -6 290 -6 l267 0 0 1580 c0 869 -2 '
        '1580 -4 1580 -2 0 -115 -116 -252 -257z"/></g></svg>')


def build(cfg_path):
    cfg = json.loads(cfg_path.read_text())
    slug = cfg["slug"]
    dpath = camp_dir / f"{slug}-data.json"
    data = json.loads(dpath.read_text()) if dpath.exists() else {"videos": {}, "history": [], "updated": None}
    vids = sorted(data["videos"].values(), key=lambda v: -v["views"])
    hist = data.get("history", [])
    total = sum(v["views"] for v in vids)
    expected = cfg.get("expected_videos", 0)
    by_creator = {}
    for v in vids:
        b = by_creator.setdefault(v["name"], {"views": 0, "n": 0})
        b["views"] += v["views"]
        b["n"] += 1

    upd = data.get("updated")
    if upd:
        d = datetime.datetime.fromisoformat(upd.replace("Z", "+00:00"))
        stamp = f"{d.day} {MON[d.month-1]} kl {d.strftime('%H:%M')}"
    else:
        stamp = "inte hämtad än"

    # daglig utveckling
    spark = ""
    if len(hist) >= 2:
        mx = max(p["views"] for p in hist) or 1
        pts = "".join(
            f'<div class="d"><span style="height:{max(3, round(p["views"]/mx*100))}%"></span>'
            f'<i>{p["date"][8:10]}/{int(p["date"][5:7])}</i></div>' for p in hist[-30:])
        spark = f'<h2>Utveckling</h2><div class="days">{pts}</div>'

    if vids:
        rows = "\n".join(
            f'''      <tr>
        <th scope="row"><a href="{v["url"]}" target="_blank" rel="noopener">{v["name"]}</a>
          <span class="cap">{v["caption"] or "—"}</span></th>
        <td class="num">{sv(v["views"])}</td>
      </tr>''' for v in vids)
        table = f'''<h2>Publicerade videor</h2>
  <div class="scroller"><table>
    <thead><tr><th scope="col">Kreatör &amp; video</th><th scope="col">Visningar</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table></div>'''
        empty = ""
    else:
        table = ""
        empty = f'''<div class="empty">
    <b>Inga videor publicerade än</b>
    <p>Kampanjen har {len(cfg["creators"])} kreatörer inbokade och {expected} videor planerade. Så fort en video går live hittar vi den automatiskt och den dyker upp här — sidan uppdateras varje natt.</p>
  </div>'''

    creators = "".join(
        f'<div class="cr"><b>{n}</b><span>{sv(b["views"])} visningar · {b["n"]} video{"r" if b["n"]!=1 else ""}</span></div>'
        for n, b in sorted(by_creator.items(), key=lambda kv: -kv[1]["views"]))
    creator_block = f'<h2>Per kreatör</h2><div class="crs">{creators}</div>' if creators else ""

    html = f'''<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{cfg["client"]} × Luminate — kampanjrapport</title>
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" type="image/png" href="/assets/luminate-icon-96.png" sizes="96x96">
<link rel="icon" type="image/png" href="/assets/luminate-icon-192.png" sizes="192x192">
<link rel="icon" type="image/svg+xml" href="/assets/luminate-icon.svg">
<link rel="apple-touch-icon" href="/assets/luminate-icon-180.png">
<meta name="theme-color" content="#2A1A1D">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Instrument+Serif:ital@1&family=Schibsted+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{--pink:#E7999C;--plum:#2A1A1D;--plum-3:#180D10;--white:#fff;
--black:"Archivo Black","Arial Black",sans-serif;--sans:"Schibsted Grotesk","Helvetica Neue",sans-serif;
--pad:clamp(20px,4.5vw,64px)}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:var(--sans);background:linear-gradient(180deg,var(--plum) 0%,var(--plum-3) 100%);
color:var(--white);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;min-height:100vh}}
a{{color:inherit}}
.wrap{{max-width:900px;margin:0 auto;padding:clamp(26px,5vw,52px) var(--pad) 80px}}
.top{{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:clamp(36px,6vw,60px)}}
.brand{{display:flex;align-items:center;gap:12px;text-decoration:none}}
.brand svg{{width:28px;height:auto;color:var(--pink)}}
.brand b{{font-family:var(--black);font-weight:400;font-size:13px;letter-spacing:.08em;text-transform:uppercase}}
.live{{display:inline-flex;align-items:center;gap:8px;font-size:10px;font-weight:700;letter-spacing:.16em;
text-transform:uppercase;color:var(--pink);border:1px solid rgba(231,153,156,.45);padding:6px 13px;border-radius:999px}}
.live i{{width:6px;height:6px;border-radius:50%;background:var(--pink);animation:p 1.6s ease-in-out infinite}}
@keyframes p{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
.label{{display:block;font-size:11px;font-weight:700;letter-spacing:.26em;text-transform:uppercase;color:rgba(231,153,156,.9);margin-bottom:12px}}
h1{{font-family:var(--black);font-weight:400;font-size:clamp(28px,5.6vw,58px);line-height:1.04;text-transform:uppercase;margin-bottom:10px}}
h1 em{{font-family:"Instrument Serif",Georgia,serif;font-style:italic;text-transform:none;color:var(--pink);font-size:1.06em}}
.sub{{color:rgba(255,255,255,.7);font-weight:500;margin-bottom:clamp(30px,5vw,48px)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1px;background:rgba(231,153,156,.2);
border:1px solid rgba(231,153,156,.2);margin-bottom:clamp(30px,5vw,48px)}}
.kpi{{background:#241519;padding:clamp(20px,3vw,30px)}}
.kpi b{{display:block;font-family:var(--black);font-weight:400;font-size:clamp(30px,5vw,52px);line-height:1}}
.kpi span{{display:block;margin-top:8px;font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.55)}}
h2{{font-family:var(--black);font-weight:400;font-size:clamp(17px,2.4vw,24px);text-transform:uppercase;margin:0 0 14px}}
.empty{{border:1px dashed rgba(231,153,156,.4);border-radius:18px;padding:clamp(24px,4vw,40px);margin-bottom:36px}}
.empty b{{display:block;font-family:var(--black);font-weight:400;font-size:clamp(18px,2.6vw,26px);text-transform:uppercase;margin-bottom:10px}}
.empty p{{color:rgba(255,255,255,.68);max-width:560px}}
.scroller{{overflow-x:auto;margin-bottom:36px}}
table{{width:100%;border-collapse:collapse;min-width:460px}}
th,td{{text-align:left;padding:13px 12px;border-bottom:1px solid rgba(231,153,156,.16);font-size:15px;vertical-align:top}}
thead th{{font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:rgba(255,255,255,.5)}}
tbody th{{font-weight:700}}
tbody th a{{text-decoration:none;border-bottom:1px solid rgba(231,153,156,.5)}}
.cap{{display:block;font-weight:400;font-size:12.5px;color:rgba(255,255,255,.45);margin-top:4px;max-width:460px}}
.num{{font-variant-numeric:tabular-nums;font-family:var(--black);font-weight:400;font-size:18px;white-space:nowrap}}
.crs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-bottom:36px}}
.cr{{border:1px solid rgba(231,153,156,.2);border-radius:14px;padding:14px 16px}}
.cr b{{display:block;font-family:var(--black);font-weight:400;font-size:14px;text-transform:uppercase}}
.cr span{{font-size:12.5px;color:rgba(255,255,255,.55)}}
.days{{display:flex;align-items:flex-end;gap:5px;height:120px;margin-bottom:36px}}
.days .d{{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;height:100%;gap:6px}}
.days .d span{{width:100%;background:var(--pink);border-radius:4px 4px 0 0;display:block}}
.days .d i{{font-style:normal;font-size:9px;color:rgba(255,255,255,.35)}}
.note{{font-size:12.5px;color:rgba(255,255,255,.45);border-top:1px solid rgba(231,153,156,.18);padding-top:20px}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <a class="brand" href="/">{LOGO}<b>Luminate</b></a>
    <span class="live"><i></i>Uppdaterad {stamp}</span>
  </div>

  <span class="label">Kampanjrapport · {cfg["client"]}</span>
  <h1>{cfg["title"]} <em>i realtid</em></h1>
  <p class="sub">Sidan uppdateras automatiskt varje natt så länge kampanjen löper. Ingen väntan på slutrapport — ni ser utfallet samma dygn som det sker.</p>

  <div class="kpis">
    <div class="kpi"><b>{sv(total)}</b><span>Visningar totalt</span></div>
    <div class="kpi"><b>{len(vids)}<span style="color:var(--pink)">/{expected}</span></b><span>Videor publicerade</span></div>
    <div class="kpi"><b>{sv(total/len(vids)) if vids else "–"}</b><span>Snitt per video</span></div>
    <div class="kpi"><b>{len(cfg["creators"])}</b><span>Kreatörer</span></div>
  </div>

  {empty}
  {spark}
  {table}
  {creator_block}

  <p class="note">Visningarna hämtas direkt från TikTok en gång per dygn. Videor hittas automatiskt på kreatörernas konton — dyker en video inte upp här inom ett dygn efter publicering hör av er, så lägger vi in den manuellt. Frågor: <a href="mailto:hello@luminatemedia.se">hello@luminatemedia.se</a></p>
</div>
</body>
</html>
'''
    (root / f"rapport-{slug}.html").write_text(html)
    print(f"rapport-{slug}.html byggd — {len(vids)} videos, {sv(total)} visningar")


for p in sorted(x for x in camp_dir.glob("*.json") if not x.stem.endswith("-data")):
    build(p)
