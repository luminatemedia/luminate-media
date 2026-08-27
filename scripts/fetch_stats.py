#!/usr/bin/env python3
"""Hamtar foljare/likes for natverkets TikTok-konton och skriver data/stats.json.

Kors nattligen av .github/workflows/stats.yml (och kan koras manuellt).
Varden for profiler som inte gar att lasa (rate limit, tillfalligt fel)
behalls fran forra korningen, sa stats.json blir aldrig samre an sist.
"""
import datetime
import json
import pathlib
import re
import time
import urllib.request

HANDLES = [
    "aotterud", "michel1egrwm", "veira.larsson", "lovisa.haeger",
    "electrakarlsson200", "tildesundb", "vildavilma2",
    "elsa41612", "amandasundiin", "mirandaomatilda_westerbe",
    "bellawesterfelt", "coolneliaaa", "juliaberglunnd", "filippaiwar2",
    "ellaaxman", "lunamaarkovic", "ebbasimonsbacka", "jessprivatastory",
    "jacquelineekenstedt", "astridholmstromming", "linneafknahlqvist",
    "nezzysf", "svea.engstrom", "shoppargalet", "ellenkb", "alice.almm",
    "norvellan", "diihhva", "minoue.ranta", "tjejenshemlighet",
    "superhemligtmg", "emmalisenz", "leabelge_", "isabellamensahh",
]
UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}

root = pathlib.Path(__file__).resolve().parents[1]
out = root / "data" / "stats.json"
old = json.loads(out.read_text()) if out.exists() else {}
creators = dict(old.get("creators", {}))

ok = 0
for h in HANDLES:
    try:
        req = urllib.request.Request(f"https://www.tiktok.com/@{h}", headers=UA)
        raw = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
        f = re.search(r'"followerCount":(\d+)', raw)
        l = re.search(r'"heartCount":(\d+)', raw)
        if f and l:
            creators[h] = {"followers": int(f.group(1)), "likes": int(l.group(1))}
            ok += 1
            print(f"  {h}: {int(f.group(1)):,} foljare")
        else:
            print(f"  {h}: kunde inte lasa (behaller gammalt varde)")
    except Exception as e:
        print(f"  {h}: {e} (behaller gammalt varde)")
    time.sleep(1.5)

if ok == 0:
    print("Ingen profil gick att lasa - stats.json lamnas orord.")
    raise SystemExit(0)

data = {
    "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "fetched_ok": ok,
    "totals": {
        "followers": sum(c["followers"] for c in creators.values()),
        "likes": sum(c["likes"] for c in creators.values()),
        "creators": len(creators),
    },
    "creators": creators,
}
out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
print(f"{ok}/{len(HANDLES)} profiler, {data['totals']['followers']:,} foljare, "
      f"{data['totals']['likes']:,} likes -> {out}")
