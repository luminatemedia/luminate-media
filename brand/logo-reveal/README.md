# Luminate — logo reveal

En 5 sekunder lång logo reveal i samma formspråk som luminatemedia.se. Den kan användas som intro eller
outro i reels, annonser, case-videor och presentationer.

Det finns två versioner:

- **Vit** (`white`): vit bakgrund, rosa logga och mörk text, som på sajten.
- **Rosa** (`pink`): rosa bakgrund med vit logga och vit text, som profilbilden.

| Format | Användning | Vit | Rosa |
| --- | --- | --- | --- |
| 9:16 (1080×1920) | Reels, TikTok, Stories, Shorts | `luminate-logo-reveal-white-9x16.mp4` | `luminate-logo-reveal-pink-9x16.mp4` |
| 4:5 (1080×1350) | Instagram/Facebook-flödet | `luminate-logo-reveal-white-4x5.mp4` | `luminate-logo-reveal-pink-4x5.mp4` |
| 1:1 (1080×1080) | Kvadratiskt, LinkedIn | `luminate-logo-reveal-white-1x1.mp4` | `luminate-logo-reveal-pink-1x1.mp4` |
| 16:9 (1920×1080) | YouTube, presentationer, webb | `luminate-logo-reveal-white-16x9.mp4` | `luminate-logo-reveal-pink-16x9.mp4` |

`luminate-endcard-*.png` är slutbilden som stillbild och passar som omslag eller thumbnail.
Alla videor är i 60 fps, H.264 och **utan ljud**, så det går att lägga egen musik eller voiceover under.

## Förlopp

| Tid | Vad händer |
| --- | --- |
| 0,25–1,6 s | LM-konturen ritas fram, först L:et och sedan M:et |
| 1,35–2,05 s | Loggan fylls med färg underifrån |
| 2,2–3,35 s | Loggan krymper och glider åt vänster medan "Luminate" glider fram bredvid |
| 3,0–3,65 s | luminatemedia.se tonar in |
| 3,65–5,0 s | Slutbilden står kvar |

## Ändra eller rendera om

Animationen är skriven som kod i `index.html`. Den använder den riktiga vektorloggan, sajtens rosa
(#E7929C) och mörka textfärg (#1C1316), typsnittet Schibsted Grotesk och sajtens easing.

- **Förhandsvisa:** kör `python3 -m http.server` i repo-roten och öppna `/brand/logo-reveal/`.
  Där kan du byta tema och format.
- **Tider och färger:** tidslinjen styrs av objektet `T` och färgerna av `THEMES`, båda i `index.html`.
- **Rendera:** `node scripts/render_logo_reveal.js` renderar alla teman och format. Vill du bara ha
  vissa, skriv t.ex. `node scripts/render_logo_reveal.js pink 9x16`. Skriptet kräver Playwright och ffmpeg.
