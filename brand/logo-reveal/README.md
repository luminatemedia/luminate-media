# Luminate — logo reveal

6,5 s logo reveal för reels, TikTok, annonser och intro/outro i videor.

| Fil | Användning |
| --- | --- |
| `luminate-logo-reveal-9x16.mp4` | Reels, TikTok, Stories, Shorts (1080×1920) |
| `luminate-logo-reveal-4x5.mp4` | Instagram/Facebook-feed (1080×1350) |
| `luminate-logo-reveal-1x1.mp4` | Kvadratiskt flöde, LinkedIn (1080×1080) |
| `luminate-logo-reveal-16x9.mp4` | YouTube, presentationer, webb (1920×1080) |
| `luminate-endcard-*.jpg` | Slutbild, t.ex. omslag/thumbnail |
| `luminate-logo-reveal.wav` | Ljudet separat (för att mixa under egen musik) |

Alla MP4:or är 60 fps, H.264 + AAC, med ljud.

## Händelseförlopp

| Tid | Vad händer |
| --- | --- |
| 0,0–0,8 s | Ett ljusstreck öppnar bilden och kollapsar till en flare |
| 0,6–1,7 s | LM-konturen ritas fram i rosa neon |
| 1,4–1,9 s | L:et och M:et flyger in från var sitt håll, med riser i ljudet |
| 1,9 s | Smäll: blixt, chockvågor, gnistor, kameraskak och basdrop |
| 2,2 s | Ljussvep över loggan |
| 2,6–3,8 s | Loggan lyfter, **LUMINATE** reser sig bokstav för bokstav |
| 3,5 s | *Media* tonar in |
| 4,2 s → slut | luminatemedia.se, ljusstrålar och ett andra glint; slutbilden står kvar |

Klipp vid ~4,8 s om ni vill ha en kortare version (då är loggan, texten och URL:en på plats).

## Ändra / rendera om

Animationen är ren kod (canvas) i `index.html`, byggd på den riktiga vektorloggan, sajtens färger
och typsnitten Archivo Black, Instrument Serif och Schibsted Grotesk.

- Förhandsvisa: öppna `brand/logo-reveal/` via en lokal server (t.ex. `python3 -m http.server` i repo-roten).
- Tidslinjen styrs av objektet `T` i `index.html`. Ändrar ni tiderna, uppdatera samma tider överst i
  `scripts/logo_reveal_audio.py` så att ljudet följer med.
- Rendera alla format: `node scripts/render_logo_reveal.js` (eller t.ex. `... 9x16`). Kräver Playwright,
  ffmpeg och python3 med numpy.

Ljudet är helt syntetiserat (inga samplingar eller licenser) och fritt att använda.
