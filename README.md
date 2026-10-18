# Hagefugler

Kortstokk med 73 hagefugler i Norge: fuglene det er lettest å se i en hage, vinter og sommer (se «Kortstokken»). Du kan sveipe for å bla, snu kortene, søke på navn eller kjennetegn, registrere hvilke dager du har sett hver fugl, telle fugler til Hagefugltellingen, samle glinskort og merker og se statistikk. Menyen øverst til høyre har søk, forklaringskortene og innstillingene.

Kortene lages i repoet **Fuglekort-builder** (kortfabrikken, tidligere Fuglekort-builder). Dette repoet, **fuglekort**, er appen som viser dem.

Appen ligger på **https://jakob-byte-2d.github.io/fuglekort/** når GitHub Pages er slått på (se under).

Claude-versjonen (artifacten i Claude) bygges og publiseres ikke lenger fra oktober 2026. Den som ligger der, står som den er (versjon 57, før de tolv nye dyrekortene). Grunnen er at en artifact kan ha høyst 511 filer, og appen har flere enn det nå. Koden for delt lagring i Claude ligger fortsatt i `src/app.html`, men slår seg bare på inne i Claude.

Appen heter **Hagefugler** igjen fra 18. oktober 2026 (den het Fuglekort en periode), men adressen er fortsatt /fuglekort/, så hjemskjerm-appene virker videre. Navnet på hjemskjermen følger manifestet; på iPhone står det gamle navnet til appen legges til på nytt. Før lå appen på jakob-byte-2d.github.io/hagefugler/ (før det hagefugler-oslo/). Den gamle adressen virker ikke lenger. Avkrysningene og tellingene ligger på samme nettsted (jakob-byte-2d.github.io), så de følger med til den nye adressen i samme nettleser. Lagringsnøklene heter fortsatt `hagefugler…` av den grunn, og sikkerhetskopien har fortsatt `kortstokk: "hagefugler"`, så gamle kopier kan gjenopprettes. En hjemskjerm-app på iPhone har sitt eget lager: åpne den gamle appen (den virker fra hurtiglageret), trykk på ringen øverst og velg *Kopier sikkerhetskopi* under *Lagring* i fanen *Profil*, legg den nye adressen på hjemskjermen og velg *Gjenopprett* samme sted der.

## Innhold

```
fuglekort/
├── data/cards.json          Navn, sjeldenhet og teksten fra kortene (til søket) + posisjonen til SETT-ruta og datolinja
├── src/app.html             Selve appen (HTML, CSS og JavaScript i én fil)
├── src/sw.template.js       Mal for offline-støtte (service worker)
├── build.py                 Bygger docs/index.html fra src + data
├── importer_fuglekort.py    Henter kort, forklaringskort og bakside fra Fuglekort-builder
├── importer_baksider.py     Henter baksidene som kan kjøpes i Frøbutikken
├── velg_kortstokk.py        Velger de 73 fuglene i kortstokken (data/kortstokk.json) fra regnearket i Fuglekort-builder
├── data/bakside.webp        Hagefugler-baksiden (standardbaksiden og app-ikonene)
├── supabase/fuglekort.sql   Tabellene til ledertavlen og statistikken (limes inn i Supabase SQL Editor)
└── docs/                    Ferdig app – det er denne mappen GitHub Pages viser
    ├── index.html
    ├── manifest.webmanifest  Gjør at appen kan legges på hjemskjermen (PWA)
    ├── sw.js                 Gjør at appen virker uten nett etter første besøk
    ├── icons/                App-ikoner, laget av fuglen på baksiden
    ├── cards/                Kortbildene 001–100 med KI-illustrasjoner, dyrekortene b01–b05, forklaringskortene 000a og 000b,
    │                         bildekrediteringen for dyrekortene (b00) og bakside.webp
    ├── cards-foto/           Kortene som har fotografi (001–062, 064 og 073), dyrekortene med fotografi og kortene Bildekreditering (000c, b00)
    ├── cards-tegneserie/     Kortene som har tegneseriefugl (001–060 og 064) og dyrekortene i tegneseriestil (b01–b05)
    ├── pictures/             Store, stående fuglebilder (675 × 800) til fullskjermvisningen, KI (pictures-foto/ og pictures-tegneserie/ for de andre settene)
    └── sprites/              Små miniatyrer til søk og samlingen (cards/photos, cards-foto/photos-foto og cards-tegneserie/photos-tegneserie)
```

## Prøve lokalt

```
cd docs
python3 -m http.server 8000
```

Åpne http://localhost:8000 i nettleseren. På mobil på samme nett bruker du maskinens IP-adresse i stedet for localhost.

## Gjøre den til en egen app

**Som hjemskjerm-app (PWA) via GitHub Pages.** På GitHub: *Settings → Pages → Build and deployment → Deploy from a branch*, velg `main` og mappen `/docs`, og trykk *Save*. Etter et par minutter ligger appen på adressen over. Åpne den på telefonen:

- **iPhone (Safari):** Del-knappen → «Legg til på Hjem-skjerm».
- **Android (Chrome):** menyen ⋮ → «Installer app» eller «Legg til på startsiden».

Da starter den i fullskjerm med eget ikon, og kortene virker uten nett. Etter endringer: kjør `python3 build.py` og push. Telefonen henter de nye filene neste gang appen åpnes med nett.

**I App Store og Google Play.** Pakk `docs/` med [Capacitor](https://capacitorjs.com):

```
npm init -y
npm i @capacitor/core @capacitor/cli @capacitor/ios @capacitor/android
npx cap init "Fuglekort" no.fuglekort.app --web-dir docs
npx cap add ios && npx cap add android
npx cap open ios        # eller: npx cap open android
```

## KI-illustrasjoner, fotografier eller tegneseriefugler

Fuglekort-builder lager tre sett kort til appen: KI-illustrasjonene (`kort/`), fotografiene fra «Fotomappe (app)»
(nå `bilder_foto_ny`; `kort_foto/`, med fotokreditering) og tegneseriefuglene (`kort_tegneserie/`). Alle 100
fuglekortene finnes i alle tre valgene: kort uten fotografi eller tegneseriefugl viser KI-kortet. Kortnummeret
nederst på kortene er bare «001» (ikke «001/100»); appen leser ikke nummeret fra bildet eller fra `kortnr`.

- **Fotografier:** Importen kopierer bare kortene som faktisk har fotografi til `docs/cards-foto/`; de andre er like KI-kortene og gjenbrukes. I `data/cards.json` har disse kortene `bildeFoto`, `fotograf` og `lisens`, og `hjelpFoto` er forklaringskortene med Bildekreditering.
- **Fotografier:** 64 fuglekort (001–062, 064 og 073) og alle fem dyrekortene har fotografi.
- **Tegneseriefugler:** 61 fuglekort (001–060 og 064) har tegneseriebilde. Importen kopierer `tegneserie.kortbilde` til `docs/cards-tegneserie/NNN.webp` (mappen tømmes først), og kortene får `bildeTegneserie` i `cards.json`; `data.tegneserie` er `true` når settet finnes. Miniatyrene `sprites/cards-tegneserie.webp` og `sprites/photos-tegneserie.webp` er KI-miniatyrene med tegneseriekortene byttet inn (`tegneserie.bilde` til søket). Kort uten tegneseriebilde viser KI-kortet. Forklaringskortene er de samme som i KI-valget, uten Bildekreditering, og det står ingen fotograf på kortene.
- **Dyrekortene i tegneseriestil** (b01 ekorn … b05 rødrev) lages her, ikke i Fuglekort-builder (den har de samme tegneseriebildene i `bilder_tegneserie/`, men bruker dem bare i utskriften): tegneseriebildene ligger i `kilder/bonus_tegneserie/` (b01_ekorn.jpg …, stående 533 × 631 som bildefeltet på kortet). `python3 lag_bonus_tegneserie.py sti/til/Fuglekort-builder` bygger kortene med kortmalen og teksten fra Fuglekort-builder i en midlertidig kopi (Fuglekort-builder endres ikke) og legger dem i `kilder/bonus_tegneserie/kort/` og de stående bildene (675 × 800) i `kilder/bonus_tegneserie/bilder/`. Importen tar dem med i `docs/cards-tegneserie/`, gir bonuskortene `bildeTegneserie` og bytter dem inn i tegneserieminiatyrene. Får Fuglekort-builder egne bonuskort i tegneseriestil i `kort.json`, brukes de i stedet. Kjør skriptet på nytt hvis teksten på bonuskortene endres i Fuglekort-builder.
- **Fullskjerm:** Trykk på bildefeltet på forsiden av et kort (den gule rammen), så kommer bildet opp i fullskjerm i samme stående format som på kortet, med knappene **KI · Foto · Tegneserie**. Knappene og sveip til sidene viser de andre bildene av fuglen; bildene ligger side om side og glir inn i full styrke, ingenting toner over (rekkefølgen er som knappene, sett fuglen mangler hoppes over, og piltastene gjør det samme). Det endrer ikke kortet: bildene på kortene velges bare i Innstillinger, og under knappene står det hva kortene viser, med lenken «Endre i Innstillinger». Mangler fuglen et bilde i et sett, er knappen grå, og det står hva som mangler. Med Foto står fotografen nederst i bildet. Trykk på bildet (eller utenfor, eller Esc) for å gå tilbake til kortet. Tidligere versjoner hadde eget bildevalg per kort (`hagefugler:bildekort`); det slettes når appen åpnes, og alle kortene følger Innstillinger.
- **Store bilder:** Fullskjermvisningen bruker de stående fuglebildene (675 × 800, samme format og utsnitt som bildet på kortet) som Fuglekort-builder lager til appen (`bilder/`, `bilder_foto/`, `bilder_tegneserie/` og bonuskortenes), lagret på nytt som WebP (kvalitet 80) i `docs/pictures/`, `docs/pictures-foto/` og `docs/pictures-tegneserie/`, ett per kort og sett (til sammen rundt 14 MB). `data.storeBilder` er `true` når de finnes. De lastes ned sammen med appen, så de virker uten nett. Uten dem viser fullskjermen bildefeltet klippet fra kortbildet.
- Valget lagres i `hagefugler:bilder` (`ki`, `foto` eller `tegneserie`) først når man velger i Innstillinger. Uten et valg viser appen fotografiene (standard). En lagret verdi som ikke finnes i dataene, blir standard.
- Alle settene lagres på telefonen (service workeren), så man kan bytte også uten nett. Bildevalget i Innstillinger vises når minst ett av foto- og tegneseriesettet finnes, og hvert valg skjules hvis settet mangler.

## Hagefugltelling

I fanen **Telling** under ringen øverst til høyre finnes **Start telling**. Skriv gjerne inn området, og trykk Start.

- **Mens du teller** går klokka i en linje under toppen. Under kortstokken står telleren for kortet du ser på: − og + (eller skriv inn tallet) for det høyeste antallet du har sett **samtidig**. Kort med antall får et gult merke i hjørnet. På tastatur: + og −.
- **Telleliste** viser alle artene med hver sin teller: **Ekorn** øverst (det står i skjemaet på Fuglevennen.no; når ekornkortet er kjøpt, telles det på kortet), så de vanligste hagefuglene først, og til slutt bonusdyrene du har funnet. Du kan søke etter en art. Trykker du på navnet, kommer du til kortet. Tellinger fra før bonuskortene, der ekorn ble lagret som `ekorn`, flyttes over på ekornkortet (`sciurus-vulgaris`) når de leses.
- **Avslutt** viser tallene i alfabetisk rekkefølge, som skjemaet på Fuglevennen.no. Har tellingen vart under én time, står det en påminnelse om at Fuglevennen anbefaler minst én time. Du kan fortsette eller avslutte og lagre. Da får alle fuglene i tellingen en observasjonsdag (datoen tellingen startet). Frøene flyr til frøtallet når du lukker sammendraget. En lagret telling kan slettes fra sammendraget (appen spør først); dagene den ga, blir liggende.
- **Tidligere tellinger** ligger i fanen Telling. Der kan du kopiere tallene som tekst, dele dem, åpne Fuglevennen.no eller slette tellingen.
- Tellingen lagres fortløpende, så den fortsetter der du slapp hvis appen lukkes.

## Dyrekort (andre dyr)

17 dyrekort med andre dyr i hagen. b01–b05 er de vanligste ville pattedyrene i hager (ekorn, rådyr, hare, elg og rødrev, rangert etter Hagefugltellingen 2024–2026). b06–b17 er laget bare til appen: neslesommerfugl, sjuprikket marihøne, mørk jordhumle, hagesnegl, buttsnutefrosk, småskogmus, pinnsvin, krattspissmus, nordpadde, grevling, stålorm og hoggorm (stjernene er en skjønnsvurdering i Fuglekort-builder). De lages i Fuglekort-builder (arket Bonuskort) og kommer med i importen fra feltet `bonus` i `kort.json`. I `data/cards.json` har de `bonus: true`, `id` som `b01` og `lengde` i stedet for `vingespenn` (sommerfuglen har `vingespenn`). Alle 17 har tegneseriekort fra Fuglekort-builder; b06–b17 har ikke fotografi, så fotosettet viser KI-bildet for dem.
I appen heter de dyrekort, og ordet «bonus» står ingen steder (bortsett fra på kortbildet «Bildekreditering bonuskort» fra Fuglekort-builder).

**De kjøpes for solsikkefrø i Frøbutikken** (se Solsikkefrø), med én pris per antall stjerner (`DYRPRIS` i `src/app.html`). Butikken viser dem sortert etter stjerner, med stjernene som små overskrifter, og innenfor samme antall stjerner i rekkefølgen fra Fuglekort-builder:

| Stjerner | Dyrekort | Pris |
|---|---|---|
| ★ | Neslesommerfugl, Sjuprikket marihøne | 8 000 |
| ★★ | Ekorn, Mørk jordhumle, Hagesnegl, Buttsnutefrosk | 12 000 |
| ★★★ | Rådyr, Småskogmus, Pinnsvin, Krattspissmus, Nordpadde | 19 000 |
| ★★★★ | Hare, Elg, Rødrev, Grevling, Stålorm, Hoggorm | 32 000 |

(★★★★★ ville kostet 48 000.) Alle 17 koster 351 000 frø. Prisene er kalibrert sammen med resten av frøene (se Solsikkefrø): en vanlig bruker kjøper typisk ×2 og Ekorn i løpet av den første uka, har fem dyrekort etter tre uker og alle 17 etter et halvt år. Et kjøp beholder prisen det ble kjøpt for. (Før balanseringen i oktober 2026 kostet de 6 500 / 9 000 / 13 000 / 20 000.)

- I butikken står bare navnet og prisen, med baksiden og et spørsmålstegn som bilde.
- Før det er kjøpt, vises dyret ingen steder: ikke i kortstokken, scrubberen, søket, samlingen, «Sist sett», glinskortene, telleliste (ekorn står der som en vanlig rad, siden det er med i skjemaet til Fuglevennen; de andre dyrekortene kommer aldri med i tellelista, heller ikke når de er kjøpt) eller under **Om kortene**. `#b03` i adressen virker først når kortet er kjøpt. Kortet «Bildekreditering bonuskort» (b00) kommer under **?** når alle er kjøpt (navnet står på kortbildet fra Fuglekort-builder).
- **Når et dyrekort er kjøpt**, lukkes butikken, og et kort med baksiden opp faller inn på skjermen og vugger, med et lysende spørsmålstegn. Trykk, så snur det seg: blader virvler ut, et stempel sier DYREKORT, og det står hvilke kort det er stokket inn blant. Trykk igjen, så viser kortstokken hvor det havnet, og kortet lyser opp. Avsløringen vises én gang (i Claude lagres det i samlingen `bonusvist`); et dyrekort kjøpt på en annen enhet avsløres neste gang appen åpnes.
- Kortet stokkes inn blant fuglekortene med like mange stjerner, et sted mellom to av dem. Plassen er fast (regnes ut fra artsnavnet), så den er lik hver gang og på alle enheter. Ekorn (★★) havner blant kortene 018–032, rådyr (★★★) blant 033–048, og hare, elg og rødrev (★★★★) blant 049–068.
- Dyrekortene følger samme stige som fuglene (bronse, sølv, gull og holo) fra første registrering; et kjøpt kort som ikke er sett, har vanlig kant. Overskriften viser «Dyrekort» uten nummer, og samlingen viser «Dyr» på dem som ikke er sett. Fargestripa ved navnet er den fra Fuglekort-builder.
- Angres kjøpet (innen to minutter), forsvinner kortet igjen og avsløres på nytt hvis det kjøpes igjen.
- Dyrekortene får observasjonsdager, frø og glinskant som fuglene, men teller ikke med i fuglelista: ringen, «av 100 fugler sett», sjeldenhetsstolpene og merkene gjelder bare fuglene.
- De har KI-illustrasjoner og fotografier som fuglene: KI-kortene i `docs/cards/`, kortene med fotografi i `docs/cards-foto/` (med `bildeFoto`, `fotograf` og `lisens` i `cards.json`). Med fotografier står fotografen og lisensen også nederst på baksiden av kortet.
- (Fram til oktober 2026 var de bonuskort man fikk ved 5, 10, 20, 40 og 60 registreringer, og hvert av dem ga 10 000 frø.)

## Brukere på denne telefonen

Øverst i Innstillinger: lista over brukerne på telefonen («I bruk», «Bytt», «Gi nytt navn», «Slett») og «Legg til bruker». Fint for hytta (eget postnummer) eller for barna.

- **Hver bruker har sitt eget:** observasjoner, tellinger, frø og kjøp, titler, oppdrag, livslisten, brukernavn og postnummer på tavla, delingsvalget og innloggingen mot Supabase (hver bruker er sin egen anonyme bruker og har sin egen rad på tavla), enkel versjon, bildevalget, telleområdet og kortet man sto på. Resten av innstillingene (glinset, fanene) gjelder telefonen. Den første brukeren («meg») har nøklene appen alltid har brukt; de andre lagres med `@<id>` bak nøkkelen (`brukerNokkel`). Lista står i `fuglekort:brukere` og den aktive i `fuglekort:bruker`.
- **Navnet på telefonen** («Hytta», «Emma», 1–20 tegn, ikke likt et annet) er noe annet enn brukernavnet på tavla, som må være unikt og byttes i profilen. Hovedbrukeren heter «Meg» til den får et navn.
- **Ny bruker:** navn og type. *Vanlig:* appen bytter til brukeren og viser innføringen som første gang (brukernavn, postnummer, deling). *Barn:* tegneseriebilder, deler ikke (ingen navnesteg, ingen anonym bruker i Supabase; delingen kan slås på i Innstillinger), og innføringen vises én gang uten navnesteget.
- **Bytte:** det som venter på å bli sendt, sendes først (høyst halvannet sekund), så lagres valget og appen lastes på nytt, så alt leses for riktig bruker. Med flere brukere er navnet øverst en knapp (med ▾) som åpner «Bytt bruker», navnet på telefonen står først i linja under («Hytta · Kort 005 · 3 av 73 sett», ikke når det er det samme som navnet øverst), og Profil har «Bytt bruker».
- **Slette** (ikke hovedbrukeren, og ikke den som er i bruk): alt brukeren har på telefonen slettes, og det den har delt, slettes i Supabase med dens egen økt (`slett_meg`). Uten nett venter økten i `fuglekort:slett-brukere`, og slettingen gjøres når nettet er tilbake, uansett hvem som bruker appen da.
- Sikkerhetskopi og «Start på nytt» gjelder brukeren som er i bruk. Ingen ny SQL.

### Navnet øverst på hovedskjermen

Øverst på hovedskjermen står navnet til den som får frøene, i stedet for «Hagefugler» (`tittelNavn`, `paintTittel`):

1. brukernavnet på tavla («Modig Blåmeis 7»), også når delingen er slått av senere (navnet står lagret i `fuglekort:kallenavn`);
2. ellers navnet på telefonen («Emma»: et barn, eller en som valgte «Ikke del»);
3. ellers «Hagefugler» (én bruker uten navn).

Et navn som er stengt etter rapporter (`fuglekort:navn-stengt`), vises ikke før et nytt er valgt. Toppen følger med med en gang når brukernavnet lagres (`lagreKallenavn`, også når tavla gir det et nummer fordi det var tatt), når delingen slås av eller på, og når brukeren får nytt navn på telefonen. Et langt navn (som «Nysgjerrig Svarthvit fluesnapper 99») får to linjer i 14 px i stedet for å kuttes. Fanen i nettleseren og navnet på hjemskjermen er fortsatt «Hagefugler». Enkel versjon viser navnet på samme måte.

## Enkel versjon

Øverst i Innstillinger: bryteren **Bare registrering** (`fuglekort:enkel` = `ja`, per bruker på enheten, beholdes ved «Start på nytt»). Da er appen bare kortstokken, registreringen, livslisten, tellingen og statistikken:

- Borte: frøtelleren og Frøbutikken, tittelringen (Min fugleliste-knappen får et vanlig ikon), alle feiringer (glinskant, merker, titler, oppdrag, premier og dyrekort), frøene som flyr og frøpillene, oppdragsstripen, Merker-fanen, multiplikatoren på kortene, glinskanten (på kortene, i albumet og nivålinja på baksiden) og innstillingen for glinskort.
- Profil viser navnet, antall fugler, observasjonsdager og registreringer (ikke tittel, frø eller glinskort). Kort-fanen viser kjøpte dyrekort uten butikken. Tavla viser bare **Arter** (valget Frø · Arter er skjult).
- Introduksjonen hopper over «Frø og titler» og oppdragskortet; kort 2 sier «Trykk «Sett» på kortet hver dag du ser fuglen». Første gang appen åpnes, går den rett fra navnet til livslisten.
- Alt regnes som før (frø, titler, merker, oppdrag, og frøene sendes til tavla). Det som ville blitt feiret, slippes stille (`stilleFester`); titler, oppdrag og premier merkes som feiret. Slår man av bryteren, er alt tilbake med det man har samlet i mellomtiden, uten feiringer i ettertid.

## Solsikkefrø

Frøene tjenes ved å registrere fugler og samles i to tall: **frø samlet** (alt du har tjent) gir titlene, og **å bruke** (frø samlet minus det du har kjøpt for) er det du handler for i Frøbutikken. Å handle trekker aldri fra titlene. Alle tallene står samlet i `FRO` øverst i frødelen av `src/app.html`.

- **Alle fuglekortene er åpne** fra start, med bilde og tekst, så kortstokken kan brukes som oppslagsverk.
- **Tjene frø:** registrering (én observasjonsdag for en fugl) 200 × stjerner, hver dag med minst én fugl registrert 600 (én gang per dag), første gang man ser en art 1 000 × stjerner, bronse-/sølv-/gull-/holokant 500 / 1 500 / 3 000 / 6 000, og merkene: 10 / 15 / 20 / 25 / 30 / 50 arter 15 000 / 30 000 / 75 000 / 125 000 / 250 000 / 500 000, hele kortstokken 1 000 000, de første 5 observasjonsdagene 10 000 og hver 5. observasjonsdag etter det 2 000, årslisten (10 / 15 / 20 / 25 arter i et kalenderår) 5 000 / 12 500 / 25 000 / 50 000, sju på rad 5 000, fire årstider 10 000, Tellekorps 75 000 (én gang hvert kalenderår), Flokk 7 500. Et kort med multiplikator gir mer (se under).
- **Balansering (oktober 2026):** Beløp, priser og titler er kalibrert med en simulering av hager over tre år, med andelene fra Hagefugltellingen 2024–26 og sommeranslaget fra Fuglekort-builder. En vanlig bruker registrerer fugler 4 dager i uka, ca. 3,6 arter de dagene, og ser rundt 20 arter det første året. Hun får rundt 29 000 frø den første uka og 660 000 det første året; frøene kommer fra registreringer (29 %), dagene med fugler (19 %), kanter (18 %), hver 5. dag (14 %), artsmerker og årsliste (11 %), nye arter (5 %) og multiplikatorer (3 %). Hun har alle dyrekortene etter et halvt år og alle baksidene etter 17 måneder; ×3 kommer etter ca. 10 måneder, og ×10 er et mål for de ivrigste (ca. 20 måneder). Hun blir Fuglekonge etter litt over tre år. (Etter balanseringen ble multiplikatorene tre ganger så dyre og artsmerkene og Tellekorps større; tittelgrensene ble stående.) Frøene flyr fra SETT-ruta på kortet opp til frøtallet, som teller opp mens de lander. Frøene toner fram mens de forlater kortet, så de ikke ser ut til å ligge på det før de flyr.
- **Hva frøene var for:** Når frøene lander, kommer ett gult merke per post rett under frøtallet, uten sum (totalen ser du i frøtallet): «+800 Registrering 200 × 4★», «+4 000 Første gang 1 000 × 4★», «+600 Ny dag med fugler». Med multiplikator: «+400 Registrering 200 × 1★ × 2» (grunnpoeng × stjerner for sjeldenhet × multiplikatoren på kortet). Kanter som ikke får egen feiring, står som «Sølv- og gullkant»; etter en telling står postene samlet («Registreringer», «Multiplikator»).
- **Hendelser, én om gangen:** Etter en registrering kommer hendelsene i denne rekkefølgen: frøene for registreringen, ny kant, nye merker (hvert merke er en egen hendelse), ny tittel. Ingenting går videre av seg selv. Venter det en hendelse, blir frømerkene stående med «Trykk for neste ›», og det neste trykket hvor som helst (eller Enter, mellomrom, Esc eller tilbake-knappen) åpner den; det trykket gjør ingenting annet, så du kan ikke registrere en fugl ved et uhell. Venter det ingenting, forsvinner frømerkene av seg selv etter noen sekunder.
- **En feiring med frø** (kant eller merke) tar to trykk: «Trykk for å samle frøene» lar frøtallet lyse opp over feiringen, og en stor strøm av frø (30–120 frø, flere jo større beløp) renner inn i det mens tallet teller opp, med et frømerke som «+5 000 Gullkant Kjøttmeis» eller «+10 000 Merke: 5 dager». Så står det «Trykk for å gå videre», og neste trykk lukker feiringen og åpner neste hendelse med en gang. Frøene for kanter og merker vises ikke i frøtallet før de har strømmet inn. Strømmen tegnes på én canvas.
- **Frøtallet** øverst viser frøene du har å bruke. Et trykk på det åpner **Frøbutikken**.
- **Frøbutikken** har tre faner, Dyrekort, Multiplikatorer og Baksider (en fane uten noe å selge vises ikke), og hver fane får plass på én telefonskjerm uten å rulle (også på en liten skjerm som 375 × 667). Øverst står hvor mange frø du har å bruke og angreboksen, og fanene viser hvor mange ting du har råd til nå («Dyrekort 3»). Butikken åpner på fanen du brukte sist (`fuglekort:butikkfane` på enheten); «Til Frøbutikken» i fanen Kort åpner Dyrekort. Piltastene bytter fane.
  - **Dyrekort:** et rutenett med to kolonner, sortert etter stjerner, med baksiden og «?», navnet, stjernene og prisen. Det du har råd til, har grønn ramme og pris; kjøpte kort viser bildet og «Kjøpt», og et trykk viser kortet i kortstokken.
  - **Multiplikatorer:** de fem merkene på én rad med prisen under (bleke når du ikke har råd, med hake og kortets navn når de er kjøpt), én forklarende linje, «Slik virker det» som kan åpnes, og «På kortene dine» med flytteknappene.
  - **Baksider:** fem i bredden med pris, «Kjøpt» eller «I bruk» under; trykk på en for å se den stort med navn, kjøp eller bruk. Baksidene har «Hagefugler» på seg fra 18. oktober 2026 (samme navn, id-er og priser, så kjøpte baksider virker som før). I zip-fila var «Leken geometri» ødelagt nederst; den er standardbaksiden og ble ikke hentet inn.
  - Trykker du på noe du ikke har råd til, står det hvor mye du mangler. Hvert kjøp bekreftes i et spørsmål. Når du velger kortet til en multiplikator, viser butikken lista med søk i stedet for fanene, med «‹ Tilbake til butikken».
- **Angre:** Det siste kjøpet eller den siste flyttingen av et merke kan angres i to minutter (`FRO.angreTid`): øverst i butikken står «Siste kjøp: Ekorn · 12 000 frø · kan angres i 1:53» (eller «Siste flytting: ×2 til Bokfink · 1 500 frø»/«Gratis») med knappen Angre, og du får hele prisen tilbake; en flytting som angres, setter merket tilbake på kortet det kom fra. Bare det nyeste kan angres, og ikke etter to minutter.
- **Multiplikatorer:** ×2 15 000, ×3 45 000, ×4 126 000, ×5 375 000 og ×10 1 125 000 frø (omtrent tre ganger dyrere for hvert steg, `MULT` i `src/app.html`; tredoblet i oktober 2026). Du kan ha én av hver, og hvert kort kan ha ett merke. Du velger kortet når du kjøper: trykk på prisen, søk opp kortet (alle kortene i kortstokken uten merke, med sjeldenhet og hvor mange dager du har sett fuglen), og bekreft. I hylla står en kjøpt multiplikator som «Kjøpt · på Kjøttmeis».
- **Flytte et merke:** Under «På kortene dine» står hvert merke med kortet og «3 av 5 registreringer». Når fuglen er registrert 5 dager med merket (`XFRI`), er det gratis å flytte det til et annet kort; før det koster det 5 % av multiplikatorens pris for hver registrering som mangler (`FRO.flyttPerReg`), f.eks. ×2 fra 3 750 til 750 frø og ×10 fra 281 250 til 56 250. Trykk «Flytt», velg kortet og bekreft. Kortet merket kom fra, beholder frøene det har gitt. Merket gjelder på det nye kortet fra og med i dag, eller fra i morgen hvis en av de to fuglene alt er registrert i dag, så ingen dag teller dobbelt. Etter en flytting teller det 5 registreringer på nytt. Et merke fra før merkene kunne flyttes og det bare var lov med ett av hver, gjøres om (det eldste av hver faktor); har man flere med samme faktor, blir de andre sittende der de er. Fra og med dagen merket settes på, gir hver registrering av fuglen så mange ganger frøene (200 × stjerner × faktor), og det samme gjelder frøene for første gang hvis fuglen ikke er sett før. Er fuglen alt registrert den dagen, gjelder merket fra dagen etter, så det ikke kan settes på i etterkant. Kanter og merker ganges ikke. Merket vises bare på forsiden av kortet, som et klistremerke i øverste venstre hjørne: rundt og litt skjevt, med hvit kant, skygge og glans, og med nedre høyre kant som har løsnet litt fra kortet. Det er gull med «×2» og «FRØ» (×10 i regnbuefarger), og det stemples på når det kjøpes. Butikken viser hvilke kort som har merke.
- **Baksider:** Ni baksider kan kjøpes, med relativt høye priser: Nordisk minimal og Typografisk 37 000, Nordisk tresnitt og Japansk ro 44 000, Botanisk 52 000, Klassisk samlekort og Klassisk spillekort 58 000, Art deco 64 000 og Perlemor 86 000 frø. Hylla viser dem som et rutenett med standardbaksiden først; trykk på en bakside for å se den stort med kjøpsknappen, og spørsmålet før kjøpet viser den også. En kjøpt bakside kan velges («Bruk») og byttes tilbake til standard når som helst; valget huskes på enheten (`fuglekort:bakside`) og gjelder alle kortene og avsløringen av dyrekort. Baksidene hentes inn med `python3 importer_baksider.py STI/TIL/baksider.zip` (eller en mappe): nummer og navn tas fra filnavnet («Hagefugler_04_Botanisk_744x1039_300dpi.png»; ordet foran nummeret spiller ingen rolle), et bilde som er likt baksiden kortstokken har fra før (`docs/cards/bakside.webp`, her «Leken geometri»), hoppes over, resten lagres som `docs/cards/bakside-<id>.webp` (750 × 1050), og `data/baksider.json` får navn, bilde og pris (`PRISER` i skriptet; en bakside som alt står i fila, beholder prisen). `build.py` tar dem med i appen og i lagringen på telefonen. Fila ligger utenfor `cards.json`, så importen fra Fuglekort-builder ikke sletter den.
- **Profil:** delen «Solsikkefrø» viser frø samlet, frø å bruke, brukt i Frøbutikken, en knapp til butikken og hva frøene kom fra (registreringer, dager med fugler, første gang du så en art, glinskant, merker og multiplikatorer). Merkene viser hvor mange frø de gir.
- **Lagring:** Frøene regnes ut fra observasjonene, nivåene, merkene og multiplikatorene hver gang; sletter man en dag, går frøtallet ned av seg selv. Bare kjøpene lagres, i samlingen `kjop`: `kjop/dyr-sciurus-vulgaris = { pris, dato, ts }`, `kjop/x-2 = { pris, dato, ts, faktor, kort: [{ key, fra, pris, ts }, …] }` (én per faktor; `kort` er kortene merket har sittet på, med dagen det gjaldt fra og hva flyttingen kostet) og `kjop/bakside-natt = { pris, dato, ts }`. Prisen lagres med kjøpet. I Claude deles de, på telefonen ligger de i `localStorage` (`hagefugler:kjop:v1`), og de er med i sikkerhetskopien (versjon 8). Kjøp fra de grå kortene i eldre versjoner (dokumenter med bare fuglens navn) blir ikke lest.

## Oppdrag: «Kom i gang»

Små oppdrag for de første dagene, hvert med frø (`OPPDRAG` og `FRO.oppdrag`, til sammen 10 000):

| Oppdrag | Frø |
|---|---|
| Registrer din første fugl | 1 000 |
| Finn en fugl med søket (trykk på et søketreff) | 500 |
| Registrer tre ulike arter | 1 500 |
| Se deg selv på ledertavlen (bare når man deler) | 500 |
| Registrer fugler på to ulike dager | 1 500 |
| Kjøp noe i Frøbutikken | 1 000 |
| Registrer fem arter | 2 000 |
| Registrer fugler på tre ulike dager | 2 000 |

De fleste leses av observasjonene og kjøpene, som merkene. Et oppdrag som er gjort, forblir gjort (også om en registrering slettes eller et kjøp angres): dagen lagres per bruker på telefonen (`fuglekort:oppdrag`), og frøene regnes av den lista. Frøene teller som tjente frø (titler og tavle) og står som «Oppdrag» under Solsikkefrø i Profil (premiene fra ledertavla står som «Premier»). Neste oppdrag står i en smal stripe under toppen; et trykk åpner Merker, og × skjuler stripen (den kan hentes tilbake under Merker). I fanen Merker står «Kom i gang · 3 av 8» øverst med en sjekkliste og knapper til søket, tavlen og butikken, og nederst når alt er gjort. Hvert oppdrag feires som et merke med frøene som strømmer til telleren; oppdrag gjort i et panel feires når panelet lukkes. Oppdrag som var gjort før de fantes (eller kom med en sikkerhetskopi), samles i én feiring, f.eks. «5 oppdrag fullført! · Kom i gang · 7 000 frø».

## Testmodus

Mens appen testes, tas ikke gamle data vare på. `TESTMERKE` i `src/app.html`: når det endres, sletter appen observasjoner, tellinger, bonusvist, kjøp og feiret tittel på hver enhet neste gang den åpnes. Den delte databasen i Claude tømmes når en ny versjon publiseres. (Test-knappen «Nullstill alt (test)» er erstattet av «Start på nytt», se under.)

## Livslisten (arter sett før appen)

En livsliste ved siden av observasjonsdagene: fugler man har sett før man begynte med appen, med år hvis man husker det. Lagres bare på telefonen (`fuglekort:forsett:v1`, samlingen `ForSett`: `{ "pica-pica": { svar: "for", aar: 2015 } }`), deles ikke med Supabase, og gir ingen frø, titler, merker, oppdrag, glinskant eller plass på tavla – alt det følger observasjonsdagene. Første registrering i appen gir full belønning som ny art. Appen spør ikke ved første registrering lenger; gamle svar «ny» (fra det spørsmålet) fjernes når lista leses.

- **Gjennomgangen** (menyen «Livslisten», «Fyll ut livslisten» i Min fugleliste → Kort og i Innstillinger, «Endre i livslisten» på baksiden av kortet, og «Kom i gang» første gang appen åpnes): en stripe øverst («2 arter sett før», **Liste**, **Ferdig**), et panel nederst for kortet øverst (navn, dager i appen, år og knappen **Sett før**) og linja ««Sett før» går til neste fugl · sveip for å hoppe over». Man velger år først (valgfritt) og trykker **Sett før**; da går kortstokken til neste fuglekort (dyrekortene hoppes over, og etter siste kort kommer kort 001). Et år alene merker ingenting, men endrer året på en fugl som alt er merket. Trykk på **Sett før** igjen fjerner fuglen fra livslisten, og kortet blir stående. Man kan også sveipe og søke som vanlig. «Sett» registrerer ikke mens gjennomgangen er på. Ferdig viser hvor mange som er lagt inn og livslisten.
- **Lista** (Liste): alle fuglene alfabetisk med søk, avkrysning og år; alt lagres med en gang. **Lim inn en liste**: én art per linje (eller skilt med komma/semikolon), norske eller latinske navn, store og små bokstaver, med eller uten æøå og med én feil bokstav; et årstall (eller en dato) på linja blir året. Viser «Fant … · Fant ikke …» før **Legg til**; det tidligste året beholdes.
- **Visning**: forsiden har en grå hake og «før appen» eller året i grått når fuglen ikke er registrert i appen; baksiden «Første gang sett: 2015 (før appen)» med **Endre i livslisten** (starter gjennomgangen på kortet); Kort-fanen og søket viser dem som sett med en grå hake (tegnforklaring «sett før appen»); Profil «Livslisten: 64 arter – 52 i appen og 12 sett før». Søkefilteret «Sett» tar dem med.
- Med i sikkerhetskopien (versjon 9) og slettes med «Start på nytt».

## Start på nytt

Nederst i Innstillinger: «Start på nytt …» åpner ett spørsmål som viser hva du har («Du har 3 arter, 4 observasjonsdager, 1 kjøp og 16 100 frø. Det kan ikke angres.») og har knappene **Kopier sikkerhetskopi først** (spørsmålet blir stående; kopien kan hentes tilbake med «Gjenopprett»), **Nullstill fremgangen**, **Slett alt** og **Avbryt**.

- **Nullstill fremgangen** (`nullstillFremgang`): observasjoner, tellinger, kjøp (dyrekort, multiplikatorer og baksider; baksiden blir standard), arter sett før appen, avslørte dyrekort, feiret tittel, oppdragene, vunne premier, gjenopprettede frø og tempovarselet slettes. Frøene, titlene og merkene følger av dette. Brukernavn, postnummer, delingsvalget, bildevalget, glinsinnstillingen og skjulte navn beholdes. Du havner på kort 001 med 0 frø.
- **Slett alt**: det samme, og i tillegg brukernavn, postnummer, delingsvalget, skjulte navn og sist brukte telleområde. Introduksjonen kommer igjen.
- **Det som er delt** (`startPaNytt`): den anonyme brukeren slettes i Supabase som ved «Slett meg» (`slett_meg()`, on delete cascade). Uten nett skjer det når nettet kommer, og ingenting sendes imens. Med deling på og «Nullstill fremgangen» lages det deretter en ny anonym bruker med samme brukernavn (ledig, fordi den gamle raden slettes først), som starter på 0 på alle fire tavlene. Premier som er vunnet, blir stående i premielisten.

## Glinskort og merker

Alle kortene går gjennom fire kanter: bronse, sølv, gull og til slutt holo, etter hvert som du ser fuglen flere dager (én registrering er én dag). Antall dager dobles fra nivå til nivå, og én stjerne mindre dobler veien til holo; fem stjerner går ett nivå om dagen (`GRENSER` i `src/app.html`):

| Sjeldenhet | Bronse | Sølv | Gull | Holo |
|---|---|---|---|---|
| ★ | 8 | 16 | 32 | 64 |
| ★★ | 4 | 8 | 16 | 32 |
| ★★★ | 2 | 4 | 8 | 16 |
| ★★★★ | 1 | 2 | 4 | 8 |
| ★★★★★ | 1 | 2 | 3 | 4 |

Kantene gir 500 / 1 500 / 3 000 / 6 000 frø (1 000 / 2 000 / 5 000 / 15 000 før balanseringen i oktober 2026). (Fram til oktober 2026 var det tre nivåer, sølv, gull og holo, ved f.eks. 10 / 25 / 50 dager for ★ og holo med én gang for ★★★★★, og bronse bare for dyrekortene. Nivåene regnes ut på nytt fra dagene, så kortene fikk den nye kanten med en gang, uten feiring. Titlene kommer omtrent like fort som før, så tittelgrensene er ikke endret.)

- Bare den trykte kanten (den hvite kanten og den gule dobbeltstreken ytterst) byttes ut med **bronse**, **sølv**, **gull** eller **holo** (regnbue). Resten av kortet er uendret. En lysstripe glir sakte langs kanten av seg selv, følger fingeren når du drar i kortet og musa på datamaskin.
- **Vipping:** Under Innstillinger kan du la lyset følge telefonen når du vipper den. På Android er det på fra start; på iPhone må du slå det på, og telefonen spør om lov til å bruke bevegelsessensoren.
- **Merker:** 10, 15, 20, 25, 30 og 50 arter, hele kortstokken, sju dager på rad, et merke for hver 5. observasjonsdag (5, 10, 15 … uten slutt), fire årstider (vår, sommer, høst og vinter), Tellekorps (en hagefugltelling på minst én time; ett merke for hvert kalenderår, «Tellekorps 2027», med årene før under) og Flokk (minst 20 av én art i en telling).
- **Observasjonsdagene som streker:** I fanen Merker står observasjonsdagene som en strektelling i penn, som på en fengselsvegg: én strek for hver dag med fugler, og hver femte en skråstrek over de fire. Hver bunt er ett 5-dagersmerke. Ti bunter (50 dager) står på hver linje, med «50», «100» … i enden, og bunten som er på vei, har de manglende strekene prikket, med «3 dager igjen til neste merke · 2 000 frø» under. Strekene er litt skjeve som håndskrift, men like hver gang (`strekBunt`). Feiringen av et 5-dagersmerke viser en bunt på medaljen, der de fire strekene og så skråstreken tegnes.
- **Årslisten:** hvor mange arter du har sett i et kalenderår, med fire merker hvert år (10, 15, 20 og 25 arter i år). Den starter 1. januar året etter den første fuglen du registrerte (det første året gir allerede frø for nye arter og artsmerker), og begynner på nytt hvert 1. januar. Fanen Merker viser årets liste med de fire merkene og en linje for hvert år før. En vanlig hage har rundt 19 arter i et år: 10 kommer i januar, 15 i mars og 20 for omtrent annenhver hage om sommeren.
- Nivåer og merker regnes ut fra observasjonene og tellingene hver gang, så de lagres ikke for seg. Sletter du dager, kan et kort miste kanten igjen.
- Når et kort får bronse-, sølv-, gull- eller holokant, kommer kortet fram over alt annet med lysstråler bak, den nye kanten lyser opp, og nivået står med store bokstaver. Første trykk strømmer frøene for kanten fra kortet inn i frøtallet, det andre går videre, og kortet vises i kortstokken. Får flere kort nytt nivå samtidig, for eksempel etter en telling, vises de etter hverandre.
- Et nytt merke er en egen hendelse: medaljen kommer stort fram (gull, med tallet eller ikonet fra fanen Merker) med lysstråler bak, navnet («5 dager!»), hva det gjelder og hvor mange frø det gir. Første trykk strømmer frøene fra medaljen inn i frøtallet, det andre går videre. Får du flere merker samtidig, kommer de etter hverandre. Statistikken viser antall glinskort, hvilke kort som er nærmest neste nivå, og alle merkene med fremdrift. I samlingen har glinskortene sølv-, gull- eller holokant. Dyrekortene har bronsekant til de får et høyere nivå.
- Baksiden av et kort viser nivået og hvor mange dager som mangler til neste.

## Min fugleliste

Ringen øverst til høyre åpner **Min fugleliste**, delt i seks faner. Tittelen og fanene står fast øverst mens du ruller, og appen husker hvilken fane du brukte sist (på enheten, `fuglekort:fane`). Piltastene bytter fane.

- **Profil:** ikonet og tittelen din med en linje mot neste tittel (se under), brukernavnet ditt (trykk for å bytte; det samme som på tavlen), hvor mange fugler du har sett av 100, observasjonsdager, merker oppnådd, solsikkefrøene (frø samlet, å bruke, brukt og hva de kom fra, med knapp til Frøbutikken), glinskortene og lagring/sikkerhetskopi.
- **Statistikk:** sjeldneste funn, fuglen du har sett flest dager, observasjonsdager og registreringer, nye arter siste 12 måneder, «Pleier å dukke opp nå», fuglekalenderen, fordeling etter sjeldenhet, nye arter eller registreringer per måned (to valg over søylene; en registrering er én art én dag, og valget huskes på enheten) og «Sist sett».
  - **Når fuglene er sett (fuglekalender):** én rad per art du har sett (fuglene, og dyrekortene under «Andre dyr»), én kolonne per måned. Fargen er sterkere jo flere dager arten er sett den måneden (1, 2–3, 4–7, 8+). Valg: «I år» eller «Alle år», og «Etter kortnummer» eller «Etter når på året» (første dag i året arten er sett). Inneværende måned har grønn ramme, og måneder som ikke har kommet, står tomme. Trykk på en rute for antall dager, eller på navnet for arten. Valgene huskes på enheten (`fuglekort:kalender`).
  - **Arten:** egen visning i fanen (tilbake med «‹ Tilbake til statistikken», Esc eller tilbake-knappen): søyler per måned med antall dager (i år eller alle år), en merkelapp regnet ut fra alle årene («Helårsfugl i hagen din» når den er sett i minst 9 måneder, «Sommergjest: mai–august», «Vintergjest: november–mars», «På trekk vår og høst» eller «Vanligst i …»; krever minst 4 dager i minst 2 måneder), observasjonsdager, måneden med flest dager, først og sist sett, dager per år og «Gå til kortet». Statistikken vises ikke på selve kortet.
  - **Pleier å dukke opp nå:** arter sett innen to uker før eller etter dagens dato tidligere år, men ikke de siste to ukene i år; helårsfugler er holdt utenfor. Det første året (før det finnes et tidligere år) står det i stedet «Sett de siste 14 dagene».
  - Alt regnes ut fra dagene som er lagret (bare dato, ikke klokkeslett); ingenting nytt lagres.
- **Telling:** start eller fortsett en hagefugltelling, og tidligere tellinger.
- **Kort:** samlingen (fuglekortene med antall dager i hjørnet) og dyrekortene du har kjøpt, med en knapp til Frøbutikken.
- **Merker:** alle merkene, observasjonsdagene som streker og årslisten.
- **Tavle:** den felles ledertavlen (se Ledertavle og statistikk).

**Titler:** Hvor langt du har kommet, regnet ut fra alle frøene du har samlet. 13 titler med hvert sitt ikon: Egg (start), Nyklekket 15 000, Dununge 30 000, Reirunge 60 000, Flygeferdig 105 000, Hagegjest 155 000, Fuglevenn 220 000, Kikkertbærer 325 000, Fuglekikker 500 000, Artsjeger 700 000, Ornitolog 1 000 000, Mesterornitolog 1 350 000 og Fuglekonge 2 000 000 frø (`TITLER` i `src/app.html`). For en vanlig bruker (se Solsikkefrø) kommer de omtrent etter 6 dager, 8 dager (5-dagersmerket og 10 arter gir et hopp den andre uka), 2½ uke, 6 uker, 2½ måned, 4 måneder, et halvt år, 9 måneder, 13 måneder, 1½ år, 2 år og litt over 3 år; en ivrig bruker som også teller, blir Fuglekonge etter ca. 14½ måned. Det du bruker i Frøbutikken, trekkes ikke fra. Ikonet står også i ringen øverst til høyre i appen, med ringen fylt mot neste tittel. Ringen regnes av frøene som vises i frøtallet og flytter seg sist: når frøene har landet og tallet har talt ferdig (frø som venter på en feiring, kommer i ringen når de har strømmet inn). Øverst i Profil står ikonet, tittelen («Ornitolog 11 av 13») og en linje med «1 013 300 av 1 300 000 frø til Mesterornitolog» og neste ikon i grått; trykk på ikonet for å se alle titlene. En ny tittel feires én gang med ikonet stort (etter feiringene for kant og dyrekort), og hvilken tittel som er feiret, huskes per bruker på enheten (`fuglekort:tittel:v2`; ny nøkkel etter balanseringen i oktober 2026, så det som var feiret før, starter på nytt uten feiring). Første gang appen åpnes med titler, starter den på tittelen du har, uten feiring. Ikonene ligger i `kilder/titler/` (01_egg.jpg … 13_fuglekonge_med_krone.jpg, 512 × 512); `python3 lag_titler.py` setter dem sammen til `docs/sprites/titler.webp`. Poengene (stjerner per sett fugl) er tatt bort.

**Flere brukere senere:** I dag er det én bruker per enhet («meg»). Brukerne ligger i `fuglekort:brukere` (`[{ id: "meg", navn: "Jakob" }]`) og den aktive i `fuglekort:bruker`. Alt som hører til en person, lagres under nøkler fra `brukerNokkel()` og `brukerSamling()`: den første brukeren beholder nøklene og samlingene appen alltid har brukt (`hagefugler-oslo:sett:v1`, `sett` …), mens en ny bruker `u2` får `hagefugler-oslo:sett:v1@u2` på telefonen og `sett_u2` i Claude. Bildevalg, fane og andre innstillinger gjelder enheten. Det som mangler for flere brukere, er bare et sted å legge til og bytte bruker (f.eks. øverst i Profil).

## Lagring av observasjoner

All lagring går gjennom objektet `Store` øverst i skriptet i `src/app.html`:

- **Som Claude-artifact** (fram til oktober 2026, se øverst) lagres observasjonene i artifactens database (samlingen `sett`, ett dokument per art, f.eks. `sett/parus-major = { art, date, dager, ts }`), så de følger med på alle enheter der du er logget inn. `dager` er alle dagene fuglen er sett, eldste først, og `date` er den første av dem (feltet er beholdt så eldre versjoner av appen fortsatt kan lese lista).
- Tellingene ligger i samlingen `tellinger`, ett dokument per telling, f.eks. `tellinger/t1790700000000 = { start, slutt, omrade, arter: { "parus-major": 4, "ekorn": 1 }, ts }`. `start` og `slutt` er tidspunkter i millisekunder, og `slutt` er 0 mens tellingen pågår. I den frittstående appen ligger de i `localStorage` under `hagefugler:tellinger:v1`.
- Avkrysninger fra før observasjonsdagene kom (bare `date`) blir automatisk fuglens første observasjonsdag.
- **Som frittstående app** lagres de i nettleserens `localStorage` på enheten. Under «Lagring» i fanen Profil finnes «Kopier sikkerhetskopi» og «Gjenopprett», så du kan flytte listen mellom enheter. Gjenoppretting legger dagene i kopien til dem du har, og tar også imot eldre kopier med én dato per fugl. Sikkerhetskopien har også med de avsluttede tellingene og kjøpene i Frøbutikken.

Observasjonene, tellingene og kjøpene sendes også som en kopi til Supabase når man deler (se under). Telefonen er fortsatt fasit.

## Ledertavle og statistikk (Supabase)

Appen har en felles ledertavle, og observasjonene sendes anonymt til en felles database så man kan lage statistikk over hagefuglene etterpå. Prosjektet ligger i Supabase (`SUPA` i `src/app.html`: adressen og den offentlige publishable-nøkkelen). Tabellene lages ved å lime inn `supabase/fuglekort.sql` i SQL Editor og trykke Run (kan kjøres flere ganger). I Supabase er «Automatically expose new tables» av og «automatic RLS» på, så SQL-en gir tilgangen uttrykkelig med GRANT og slår på RLS selv.

- **Anonym bruker:** Hver person i appen blir en anonym Supabase-bruker (`/auth/v1/signup` uten e-post, som `signInAnonymously`), uten e-post eller passord. Økten (nøklene og ID-en) ligger på telefonen (`fuglekort:okt`) og fornyes før den går ut. Appen bruker vanlige `fetch`-kall, ikke supabase-js: publishable-nøkkelen i `apikey`, personens nøkkel i `Authorization`.
- **Første gang appen åpnes** kommer en kort innføring: fire kort man sveiper mellom (Velkommen til Hagefugler, Registrer fugler når du ser dem, Frø og titler og Livslisten), med «Hopp over» og «Neste». Så kommer **Velg brukernavn**: et ferdig forslag («Nytt forslag» lager et nytt), et valgfritt postnummer og teksten om hva som deles. «Neste» (eller Esc/tilbake) starter delingen; «Ikke del» varsler først at man da ikke får se ledertavlen. Når navnet er besvart, kommer det siste kortet, **Kom i gang**, med de tre første oppdragene, hvor mange som er igjen og frøene for alle; «Kom i gang» lukker innføringen og starter gjennomgangen av livslisten (se Livslisten), så man kan merke fuglene man har sett før. Fra menyen står det «Ferdig» i stedet, og det lukker bare. Navnet kan da ikke endres i innføringen (det byttes i profilen). Ingenting sendes før man har svart. Valget ligger i `fuglekort:deling` (`ja`/`nei`). De som har brukt appen før og ikke har svart, får bare siste steg. Slår man på delingen senere (bryteren i Innstillinger eller «Del og se ledertavlen»), kommer også navnesteget, så man ser navnet før det vises. Innføringen kan ses igjen under **Slik virker appen** i menyen: de fire kortene og Kom i gang, med hake på oppdragene som er gjort.
- **Det som sendes** (tabellene i SQL-en):
  - `ledertavle`: brukernavnet, tjente frø (det titlene regnes av), antall fuglearter, observasjonsdager, tittelen (0–12) og om artslista vises (`vis_arter`). Alle kan lese tavlen; hver bruker kan bare skrive sin egen rad.
  - `profil`: postnummer (valgfritt), appversjonen (`__VERSJON__`, satt av `build.py`), bildevalget og baksiden.
  - `sett`: observasjonsdagene, én rad per art med alle datoene, som på telefonen. Visningen `observasjoner` gir én rad per art og dag til statistikk.
  - `tellinger` og `kjop`: hagefugltellingene og kjøpene i Frøbutikken.
  - Alt utenom tavlen kan bare eieren av raden lese. Du som eier prosjektet ser alt i SQL Editor; nederst i SQL-fila står eksempler på statistikk.
- **Brukernavn:** fritekst, 3–30 tegn med bokstaver (også æøå), tall, mellomrom, bindestrek og punktum, minst to bokstaver. Forslaget er et ord, en fugl og et tall, f.eks. «Rask Kjøttmeis 42» (`ORD`). Navnet er det samme i profilen øverst i Min fugleliste og på tavlen, og byttes ved å trykke på navnet i profilen eller med «Bytt navn» i fanen Tavle. Det lagres på telefonen som `{ navn, forslag }` i `fuglekort:kallenavn`; eldre navn (ord, fugl og tall) gjøres om til tekst. Med nett spør appen databasen (`navn_status`) om navnet er ledig før det lagres. Er et navn valgt uten nett tatt når det sendes, får et forslag et nytt tall i stillhet, mens et selvvalgt navn får «2», «3» … og en melding i fanen Tavle. Databasen har siste ord: samme regler, ett navn per person uten å skille store og små bokstaver, og ordfilteret.
- **Moderering:** Appen og databasen sjekker navnet mot de samme ordene (`STENGTE` i appen, tabellen `stengte_ord` i Supabase; tall leses som bokstaver, f.eks. «f4en», og doble bokstaver som én). `helt_ord` betyr bare som eget ord, så «Thoresen» og «Torpedo» går fint. Nye ord kan legges til i Table Editor og gjelder med en gang. På tavlen kan man trykke på en annen rad og velge «Rapporter navnet»: navnet skjules for den som rapporterte med en gang (kan vises igjen i Innstillinger), og rapporten havner i `rapporter`. Rapporter fra tre forskjellige brukere sperrer navnet (`stengte_navn`) og fjerner det fra tavlen; eieren står som «Fuglevenn» og får beskjed i fanen Tavle om å velge et nytt. Du kan selv sperre og åpne navn i SQL Editor (eksempler nederst i SQL-fila). Google Play krever regler for brukerinnhold, rapportering og blokkering i apper der brukere ser hverandres innhold; regelen står ved navnefeltet.
- **Lagringslaget:** `samling()` har fått en `speil`. `connectRemote()` sender det som ikke er sendt, og hver `push(id)` legger endringen i en kø på telefonen (`fuglekort:usendt:<tabell>`) som sendes noen sekunder etter siste endring, når nettet kommer tilbake og når appen åpnes. Køen overlever at appen lukkes uten nett. Det som er på telefonen, skrives aldri over fra Supabase. Første gang en anonym bruker deler, sendes alt som finnes fra før.
- **Fanen Tavle** i Min fugleliste: din rad øverst (brukernavn, plassen og frøene på tavla som er valgt, og «Bytt navn»), så fire valg: **Uke, Måned, År og Totalt** (huskes på enheten), og topp 50 sortert etter frø med plass, tittelikon, brukernavn, arter og dager.
- **Uke, måned og år:** frøene tjent i perioden (ukene fra mandag, alt i norsk tid). Supabase lagrer frøene hver time når appen sender (`fro_logg`, tidspunktet settes av databasen), og frøene i en periode er det du har nå minus det du hadde før perioden startet; den som begynner å dele midt i en periode, starter på 0. Premier og frø og arter fra en sikkerhetskopi sendes for seg (`fro_utenfor`, `arter_utenfor`) og teller ikke i periodene. Over lista står perioden («Uke 42 · 12.–18. okt. · 3 dager igjen») og premiene, og under den forrige periodes tre beste.
- **Premier:** Når en periode er over, låses de tre beste med frø som ikke er merket (`premier`; likt: den som kom dit først): uke 2 000, 1 000 og 500, måned 5 000, 3 000 og 1 500, år 25 000, 15 000 og 7 500 frø. Periodene avsluttes av `avslutt_perioder()`: hver time med Cron slått på i Supabase (Integrations → Cron, og kjør SQL-en igjen), og ellers når noen åpner tavla eller appen sender (høyst én gang i timen per telefon). Appen henter premiene når den sender, og feirer hver med en medalje i gull, sølv eller bronse («1. plass! · Ukas ledertavle, uke 42 · 2 000 frø»). Premiene lagres per bruker på telefonen (`fuglekort:premier`), teller som tjente frø og står som «Premier» under Solsikkefrø.
- **Merking:** Får noen mer enn 300 000 frø eller mer enn 25 nye arter på et døgn (uten premier og sikkerhetskopier), merker databasen brukeren (`merket`, og `merket` på tavleraden, som appen ikke kan endre). Merkede har et lite «!» ved navnet, får en forklaring i fanen Tavle og kan ikke vinne premier. Du fjerner merket med `select public.godkjenn('<user_id>');` (eksempler nederst i SQL-fila); det som kom før, teller da ikke igjen. Registrerer man 15 nye arter i løpet av en time med SETT, kommer en advarsel om dette, én gang per dag. Et trykk på en annen rad viser tallene og «Rapporter navnet». Din rad er uthevet; er du utenfor topp 50, står den nederst etter «…». Tavlen hentes når fanen åpnes, hvert minutt mens den er åpen og når raden din er sendt på nytt, og lagres på telefonen, så uten nett står «Uten nett – viser tavlen fra kl. 10.16».
- **Innstillinger → Ledertavle og statistikk:** bryteren «Del med ledertavlen og statistikken», bryteren «Vis artslista mi» (se Profilen på tavla), postnummeret (fire sifre, valgfritt, bare til statistikk, vises ikke på tavlen), hva som venter på å bli sendt, navn du har skjult («Vis dem igjen»), og «Slett meg fra ledertavlen».
- **Slett meg** (også nederst i fanen Tavle, og når bryteren slås av): funksjonen `slett_meg()` sletter den anonyme brukeren i Supabase, og alle radene forsvinner med den (on delete cascade). Appen glemmer økten og slutter å sende; brukernavnet beholdes på telefonen. Uten nett venter slettingen (`fuglekort:slett`) og fullføres så snart nettet er tilbake; imens sendes ingenting og tavlen vises ikke. Observasjonene på telefonen beholdes. Slår man på deling igjen, blir man en ny anonym bruker.
- **Verdt å vite:** Tallene kommer fra telefonen, så en teknisk kyndig kan sende falske tall for sin egen rad; databasen sier nei til umulige verdier, og rader kan slettes i Supabase. Supabase tillater 30 anonyme innlogginger i timen fra samme IP-adresse, og anbefaler CAPTCHA (Cloudflare Turnstile) mot misbruk. Anonym ID sammen med observasjoner og postnummer er trolig personopplysninger etter GDPR, og Google Play krever personvernerklæring og opplysninger i skjemaet om datasikkerhet.

### Artstavla (Frø · Arter)

Over periodeknappene på Tavle-fanen velger man **Frø** eller **Arter** (huskes i `fuglekort:tavleetter`). Under Arter rangeres man etter antall fuglearter: for uke, måned og år arter med minst én observasjonsdag i perioden (norsk tid), for Totalt fuglearter registrert i appen (`arter` på tavla). Supabase teller det fra tabellen `sett` i `tavle_arter(hva)` (se `supabase/fuglekort.sql`); dyrekortene står i tabellen `dyrearter` og teller ikke, og «sett før appen» ligger bare på telefonen og teller ikke. Likt antall gir delt plass (1, 2, 2, 4), med flest frø først. Ingen premier på artstavla; periodelinja sier «Flest fuglearter registrert i perioden». Hver tavle lagres på telefonen (`fuglekort:tavle-arter:uke` …), så den vises uten nett. Mer enn 40 fuglearter registrert på samme dag gir merke på tavla (triggeren `sett_arter_dag`), med samme godkjenning som for frøene.

### Profilen på tavla

Trykker man på et navn på tavla (også sitt eget), viser fanen Tavle profilen: navnet, «42 fugler observert i hagen» og fuglene som en liste med bilde og navn i alfabetisk rekkefølge, som «Sett de siste 14 dagene». Trykk på en fugl går til kortet; «‹ Tilbake til tavla» eller Esc går tilbake. Under lista står «Rapporter navnet» (eller «Vis navnet igjen»), som før.

- Lista kommer fra `profil_arter(uid)` i Supabase: artene i `sett` for brukeren, uten datoer og antall dager, uten dyrekort (`dyrearter`) og uten «sett før appen». Bare for brukere på tavla. Den egne profilen bygges av observasjonene på telefonen.
- **Vis artslista mi** (Innstillinger → Ledertavle og statistikk, på fra start): slått av lagres `fuglekort:vis-arter` = `nei`, og tavleraden sendes med `vis_arter = false`. Andre ser da bare antallet («Artslista er skjult.»); man ser alltid sin egen. «Slett alt» fjerner valget.
- Lista som er hentet, huskes mens appen er åpen, så den vises uten nett («Uten nett – viser lista fra sist.»). Ellers står det «Lista hentes når du har nett.»
- SQL-en må kjøres før denne appversjonen publiseres, siden tavleraden sendes med `vis_arter`.
- Artene du registrerer, blir altså synlige for andre som deler. Det må stå i personvernerklæringen.

## Kortstokken: 73 hagefugler

Kortstokken har de 73 fuglene det er lettest å se i en hage i boligstrøk, etter det samme målet som stjernene og kortnumrene i Fuglekort-builder: det høyeste av (1) andelen fôringsplasser som så arten i Hagefugltellingen 2024–2026 (BirdLife Norge/Fuglevennen) × hagetilknytning og (2) sommeranslaget fra Artsobservasjoner × hagetilknytning² × «lander i hagen». Det er kort 001–073, fra Kjøttmeis til Fossekall, uten hull i numrene. Både vinterfuglene ved fôringsbrettet og sommerfuglene (Linerle, Løvsanger, svalene …) er med. Tallene står i arket «Sjeldenhetsvurdering» i regnearket til Fuglekort-builder. `python3 velg_kortstokk.py STI/TIL/Fuglekort-builder/data/fuglekort_data.xlsx [ANTALL]` regner dem ut (regnearket endres ikke) og skriver `data/kortstokk.json`: de 73 fuglene og de 27 som er ute (074–100), med tallet for hver («hage»).

(Fra 18. oktober 2026 til samme kveld hadde kortstokken 60 fugler valgt bare etter Hagefugltellingen. Den regelen tok ut sommerfuglene, så den ble byttet.)

- `build.py` merker fuglekortene som ikke står i lista, med `ute`. De står fortsatt i dataene, men er ikke i kortstokken, søket, albumet, statistikken, tellelista, livslisten eller profilen på tavla, og teller ikke i «av 73» eller på tavla (`arter`). Kortene og bildene deres lastes ikke ned.
- Det som alt er registrert av en fugl som er ute, slettes ikke, og frøene for det beholdes (registreringer, første gang, glinskant, dager og merker for antall arter), så ingen mister en tittel. Fuglen kan ikke registreres igjen.
- Toppen viser «Kort 005 · 3 av 73 sett».
- Dyrekortene er med som før.

## Hente nye kort fra Fuglekort-builder

1. I **Fuglekort-builder**: endre regnearket, bildene eller baksiden og push. GitHub bygger kortene. Last ned «app» under *Actions → Bygg fuglekort → Artifacts* og pakk den ut. (Eller kjør `python bygg.py --uten-pdf` der, så ligger den i `ut/app`.)
2. Her: `python3 importer_fuglekort.py sti/til/app`
3. Commit og push. GitHub Pages oppdaterer appen, og telefonene henter de nye kortene selv.

Artefakten «app» kan ikke lastes ned fra Claude sin arbeidsflate (GitHub sender nedlastingen til en adresse som er sperret der). Da bygges «app» fra den samme commiten i en egen kopi av Fuglekort-builder (`git clone`, `git checkout <commit>`, `python3 bygg.py --uten-pdf`), så selve repoet ikke røres. Sist: commit f095c26 (byggekjøring 39159184355), 18. oktober 2026: foto til 063 og 065–072, tegneseriefugler til 061–073 og ny 064, og alle kortbildene 6 px opp (SETT-ruta følger med).

Telefonene får de nye bildene fordi navnet på hurtigbufferen i service workeren regnes av innholdet (`build.py`). Ved installering henter den alle filene med `cache: 'reload'`, rett fra nettet og ikke fra nettleserens egen hurtigbuffer, så en ny versjon ikke får med et gammelt kortbilde.

Skriptet kopierer kortene, de to forklaringskortene, baksiden (Hagefugler-baksiden i `data/bakside.webp`; Fuglekort-builder har «Fuglekort» på sin), fotosettet og tegneseriesettet (se over), finner SETT-ruta og datolinja, lager `data/cards.json`, miniatyrene og app-ikonene, og kjører `build.py`. Avkrysningene lagres på artens latinske navn (f.eks. `parus-major`), ikke på kortnummeret, så de følger fuglen når kortene får ny rekkefølge. Avkrysninger fra før dette (lagret på kortnummer) flyttes over automatisk ved hjelp av `data/tidligere_nummer.json`.

Miniatyrene i `docs/sprites/` er rutenett med 10 kolonner og én rad per ti kort. Appen regner ut antall rader selv.

## Bruk

- **Hold** på kortet, så løftes det og følger fingeren. **Dra det til kanten** og slipp for neste (venstre) eller forrige (høyre) kort.
- **Sveip fort** for å bla gjennom mange kort. Farten avtar av seg selv, og **et trykk** stopper blaingen.
- **Trykk** på kortet for å snu det og se baksiden. Trykk på bildet for å se det i fullskjerm; sveip der for å se KI, foto og tegneserie. Bildene på kortene velger du i Innstillinger.
- **Zoom:** Selve appen kan ikke zoomes (viewport med `user-scalable=no`, `touch-action: pan-x pan-y` på siden, og to-finger-bevegelser og Safaris gesture-hendelser stoppes). To fingre på kortet øverst i bunken, på et forklaringskort eller på fuglebildet i fullskjerm forstørrer det rundt punktet mellom fingrene (opptil 4 ganger), og det spretter tilbake når en finger slippes. En kopi vises over alt annet, så ingenting under flytter seg. På PC gjør Ctrl + rullehjul (eller knip på styreflaten) det samme; Ctrl +/− er ikke sperret. Forklaringskortene sveipes med appens egen sveip, så to fingre kan zoome.
- **Trykk på SETT** når du ser fuglen. Første gang kommer haken og datoen på kortet. En senere dag legger et nytt trykk til en ny observasjonsdag, og tallet ved SETT (f.eks. «× 7») viser hvor mange dager du har sett den. Et nytt trykk samme dag viser lista over dagene. Det er ingen meldinger nederst på skjermen og ingen angreknapp; en registrering fjernes ved å slette dagen på baksiden. Det som skjer, leses opp for skjermlesere.
- **I dag:** En fugl du har registrert i dag, får en grønn merkelapp «✓ Sett i dag» nederst i hjørnet av bildet. I samlingen og søket viser det gule tallet i hjørnet hvor mange dager du har sett fuglen. I samlingen står en grønn hake ved siden av tallet når du har sett den i dag, og en tegnforklaring øverst forklarer begge (i søket blir tallet grønt i stedet), og under «Sist sett» står det «I dag». Merkingen forsvinner ved midnatt, også når appen står åpen. «Sjeldneste funn» i fanen Statistikk er fuglen med høyest kortnummer du har sett (kortene går fra den vanligste, 001, til den sjeldneste).
- **Baksiden** av et kort du har sett, viser alle dagene. Der kan du slette en dag (× og så «Slett» i spørsmålet som kommer, der det står at frøene for registreringen også forsvinner). Det går ikke å registrere bakover i tid: SETT registrerer i dag, og datoen på forsiden (første gang) kan ikke endres. En sikkerhetskopi kan fortsatt gjenopprettes (se Lagring).
- **Menyen** (☰ øverst til høyre) samler **Søk etter fugl**, **Om kortene** (forklaringskortene: Om kortene og Tegnforklaring) og **Innstillinger**. Øverst ellers: frøtallet (frø å bruke; åpner Frøbutikken) og ringen med ikonet for tittelen din. Ringen fylles mot neste tittel, ikonet spretter når du får ny tittel, og et trykk åpner Min fugleliste på fanen Profil.
- **Innstillinger**: Under «Bilder på kortene» velger du **Fotografier** fra Artsdatabanken og Artsobservasjoner (standard), **KI-illustrasjoner** (som på de trykte kortene) eller **Tegneseriefugler** (fuglene tegnet i tegneseriestil, for 61 av 100 fugler, og dyrekortene). Kort uten bilde i valgt sett viser illustrasjonen, og i fotovalget kommer kortet Bildekreditering med under **Om kortene**. Piltastene går gjennom alle valgene. Valget gjelder alle kortene, huskes på enheten og påvirker ikke avkrysningene. I fullskjerm kan du se de andre bildene uten å endre kortet.
- **Tilbake** (knappen eller bevegelsen på Android, og sveip fra kanten på iPhone) lukker det som ligger øverst: et spørsmål, fullskjermbildet, en feiring, menyen eller et panel, akkurat som Esc. Først når ingenting er åpent, går tilbake ut av appen. Appen legger til ett steg i nettleserhistorikken mens noe er åpent, og fjerner det igjen når du lukker med en knapp eller et trykk.
- **iPhone:** I Min fugleliste og Frøbutikken ligger tittelen og fanene fast øverst. Plassen til toppen av telefonen (`env(safe-area-inset-top)`) ligger bare i overskriften (`.s-topp`), ikke i arket i tillegg (`.med-topp`); ellers la Safari overskriften dobbelt så langt ned, og den dekket toppen av innholdet. Merkene på forsiden av kortet («Sett i dag», multiplikatoren og tallet under en telling) skjules når kortet er snudd, så de ikke skinner gjennom på baksiden i Safari.
- Tastatur: ← → blar, mellomrom snur kortet, S registrerer i dag, / åpner søk, ? viser forklaringskortene, Esc stopper blaing og lukker paneler.
