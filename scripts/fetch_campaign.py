#!/usr/bin/env python3
"""Hamtar dagliga siffror for kampanjvideos och skriver data/campaigns/<slug>-data.json.

Varje kampanj beskrivs i data/campaigns/<slug>.json. Skriptet letar upp
kreatorernas senaste videos, plockar ut dem som matchar kampanjens nyckelord
(eller som listats manuellt under "videos") och sparar en matpunkt per dygn.
Kors nattligen av .github/workflows/stats.yml.
"""
import datetime
import json
import pathlib
import subprocess
import sys
import time

SCAN = 40  # hur manga av kreatorens senaste videos vi tittar i

root = pathlib.Path(__file__).resolve().parents[1]
camp_dir = root / "data" / "campaigns"
today = datetime.date.today().isoformat()


def list_videos(handle):
    p = subprocess.run(
        ["yt-dlp", "--flat-playlist", "-J", "--playlist-end", str(SCAN),
         f"https://www.tiktok.com/@{handle}"],
        capture_output=True, text=True, timeout=180,
    )
    return json.loads(p.stdout).get("entries", []) or []


def run(cfg_path):
    cfg = json.loads(cfg_path.read_text())
    slug = cfg["slug"]
    out = camp_dir / f"{slug}-data.json"
    data = json.loads(out.read_text()) if out.exists() else {"videos": {}, "history": []}
    videos = data.get("videos", {})
    words = [w.lower() for w in cfg.get("match", [])]
    forced = set(str(v) for v in cfg.get("videos", []))
    excluded = set(str(v) for v in cfg.get("exclude", []))

    found = 0
    for c in cfg["creators"]:
        h = c["handle"]
        try:
            entries = list_videos(h)
        except Exception as e:
            print(f"  {h}: {type(e).__name__} - behaller gamla varden")
            continue
        for e in entries:
            vid = str(e.get("id") or "")
            if not vid or vid in excluded:
                continue
            caption = (e.get("title") or "")
            hit = vid in forced or any(w in caption.lower() for w in words)
            if not hit:
                continue
            prev = videos.get(vid, {})
            videos[vid] = {
                "handle": h,
                "name": c["name"],
                "caption": caption[:160],
                "views": e.get("view_count") or prev.get("views") or 0,
                "url": f"https://www.tiktok.com/@{h}/video/{vid}",
                "first_seen": prev.get("first_seen", today),
            }
            found += 1
        time.sleep(2)

    total = sum(v["views"] for v in videos.values())
    hist = [p for p in data.get("history", []) if p["date"] != today]
    hist.append({"date": today, "videos": len(videos), "views": total})
    hist.sort(key=lambda p: p["date"])

    out.write_text(json.dumps({
        "slug": slug,
        "updated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "videos": videos,
        "history": hist[-400:],
    }, ensure_ascii=False, indent=1) + "\n")
    print(f"{slug}: {len(videos)} videos ({found} traffar denna korning), {total:,} visningar")


cfgs = sorted(p for p in camp_dir.glob("*.json") if not p.stem.endswith("-data"))
if not cfgs:
    print("Inga kampanjer definierade.")
    sys.exit(0)
for p in cfgs:
    run(p)
