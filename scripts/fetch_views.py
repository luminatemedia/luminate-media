#!/usr/bin/env python3
"""Raknar snittvisningar per kreator fran deras senaste videos och skriver
data/views.json.

Samma metod som i vara offertunderlag: snittet over de senaste 20 videorna.
Kors av .github/workflows/stats.yml. Misslyckas en profil behalls forra
vardet, sa filen blir aldrig samre an senaste lyckade korning.
"""
import json
import pathlib
import statistics
import subprocess
import sys
import time

LAST_N = 20

root = pathlib.Path(__file__).resolve().parents[1]
stats_path = root / "data" / "stats.json"
out = root / "data" / "views.json"

handles = list(json.loads(stats_path.read_text())["creators"].keys())
old = json.loads(out.read_text()) if out.exists() else {}
creators = dict(old.get("creators", {}))

ok = 0
for h in handles:
    try:
        p = subprocess.run(
            ["yt-dlp", "--flat-playlist", "-J", "--playlist-end", str(LAST_N),
             f"https://www.tiktok.com/@{h}"],
            capture_output=True, text=True, timeout=120,
        )
        entries = [e for e in json.loads(p.stdout).get("entries", []) if e.get("view_count")]
        views = [e["view_count"] for e in entries[:LAST_N]]
        if len(views) >= 5:
            creators[h] = {
                "avg": int(statistics.mean(views)),
                "median": int(statistics.median(views)),
                "n": len(views),
            }
            ok += 1
            print(f"  {h}: snitt {creators[h]['avg']:,} over {len(views)} videos")
        else:
            print(f"  {h}: for fa videos ({len(views)}) - behaller gammalt varde")
    except Exception as e:
        print(f"  {h}: {type(e).__name__} - behaller gammalt varde")
    time.sleep(2)

if ok == 0:
    print("Ingen profil gick att lasa - views.json lamnas orord.")
    sys.exit(0)

avgs = [c["avg"] for c in creators.values()]
data = {
    "updated": json.loads(stats_path.read_text())["updated"],
    "method": f"snitt over senaste {LAST_N} videos per kreator",
    "fetched_ok": ok,
    "totals": {
        "creators": len(creators),
        "avg_views": int(statistics.mean(avgs)),
        "median_views": int(statistics.median(avgs)),
        "sum_avg_views": sum(avgs),
    },
    "creators": creators,
}
out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")
print(f"{ok}/{len(handles)} profiler -> median {data['totals']['median_views']:,} visningar/video")
