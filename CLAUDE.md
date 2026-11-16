# Luminate Media

## Skicka aldrig något utan godkännande

Skicka aldrig mail, svar, kalenderinbjudningar eller andra meddelanden utan att användaren först har sett den exakta texten och uttryckligen skrivit "skicka". Gör utkast och visa texten i stället. Gäller även när en uppgift låter som en instruktion att skicka, till exempel "Electra ska ha ett mail".

## Design för allt som går till kunder

Kampanjrapporter, presentationer och andra kundsidor ska alltid ha samma tema som luminatemedia.se: vitt och rosa.

- Bakgrund vit (#FFFFFF), ytor och kort ljusrosa (#FBEDEE), linjer #F2CFD1.
- Accent rosa #E7999C, mörkrosa #B05661 för etiketter, text plommon #2A1A1D.
- Typsnitt: Archivo Black (rubriker, versaler), Schibsted Grotesk (brödtext), Instrument Serif kursiv (accentord).
- Ingen mörk plommonbakgrund som huvudtema.

Mallen för kampanjrapporter finns i `scripts/build_report.py`.

## Kampanjassistenten (chatten på startsidan)

Sektionen `#bygg` i `index.html` är en styrd chatt som bygger ett kampanjförslag med namngivna kreatörer.

- **Ingen server, ingen AI-modell, ingen API-nyckel.** Allt räknas i webbläsaren. Fritext tolkas med ordlistan i `assets/kampanj-motor.js` (`tolkaAmnen`, `tolkaBelopp`). Lägg aldrig en nyckel i det här repot: det är publikt.
- **Motorn har inga egna priser.** `assets/kampanj-motor.js` får `TIERS`, `SPARK`, `kmDiscount` och `KM_FREE` från `index.html`, samma konstanter som kalkylatorn och `scripts/build_pricing.py` läser. Ändra priser där och bara där.
- **`data/match.json`** (antal videor och median per kreatör och ämne) byggs i Company-Brain, `research/kategorianalys-2026-11/bygg.py`, och kopieras hit. Den byggs inte av nattjobbet. En kreatör som saknas i filen föreslås aldrig automatiskt; lägg inte till någon för hand.
- **Regler som testet håller:** förslaget ryms i budgeten, ingen kreatör föreslås utan underlag i ämnet, de tre minsta kontona prissätts aldrig. Kör `node scripts/test_kampanjmotor.mjs` efter varje ändring i motorn, priserna eller `match.json`.
- Spark-förslaget (andel av budgeten, antal videor) är förslagsvärden överst i motorn: `SPARK_ANDEL`, `SPARK_VIDEOANDEL`.
