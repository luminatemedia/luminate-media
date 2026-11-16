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

Sektionen `#bygg` i `index.html` är en chatt som bygger ett kampanjförslag med namngivna kreatörer. Besökaren skriver fritt; det finns inga kategoriknappar.

- **Ingen server, ingen AI-modell, ingen API-nyckel.** Allt räknas i webbläsaren. Fritext tolkas med ordlistor och mönster (`tolkaAmnen`, `tolkaBudget` i `assets/kampanj-motor.js`, småprat i `SVAR` i `assets/kampanj-chatt.js`). Lägg aldrig en nyckel i det här repot: det är publikt.
- **Motorn har inga egna priser.** Den får `TIERS`, `SPARK` och `kmDiscount` från `index.html`, samma konstanter som kalkylatorn och `scripts/build_pricing.py` läser. Ändra priser där och bara där.
- **Inga gratiskreatörer i förslag** (Willem 31 okt 2026). Chatten skickar `free: {count: 0}` till motorn även om kalkylatorn har `KM_FREE`.
- **Spark Ads ligger ovanpå budgeten** (Love 16 nov 2026). Hela budgeten går till kreatörsvideor; rättigheter och mediebudget visas som en rekommendation i en egen ruta och räknas aldrig in i totalen. Nivån styrs av `SPARK_VIDEOANDEL` och `SPARK_MEDIAANDEL` överst i motorn.
- **Alla kreatörer i nätverket kan föreslås**, även de utan kort på sajten (de får en bokstav i stället för bild och ingen länk). `data/match.json` (antal videor och median per kreatör och ämne, plus namn och följare för dem utan kort) byggs i Company-Brain, `research/kategorianalys-2026-11/bygg.py`, och kopieras hit. Den byggs inte av nattjobbet. En kreatör som saknas i filen föreslås aldrig; lägg inte till någon för hand, det kan finnas ett skäl till att hon inte är med.
- **Regler som testet håller:** kreatörerna ryms i budgeten, ingen föreslås utan underlag i ämnet, ingen under 5 000 följare eller under en visning per krona, Spark Ads ändrar aldrig urvalet eller totalen. Kör `node scripts/test_kampanjmotor.mjs` efter varje ändring i motorn, priserna eller `match.json`.
