# Fuglekort

Kortstokk med 100 fuglekort med hagefugler i Norge. Du kan sveipe for å bla, snu kortene, søke på navn eller kjennetegn, registrere hvilke dager du har sett hver fugl, telle fugler til Hagefugltellingen, samle glinskort og merker og se statistikk. Menyen øverst til høyre har søk, forklaringskortene og innstillingene.

Kortene lages i repoet **Fuglekort-builder** (kortfabrikken, tidligere Fuglekort-builder). Dette repoet, **fuglekort**, er appen som viser dem.

Appen ligger på **https://jakob-byte-2d.github.io/fuglekort/** når GitHub Pages er slått på (se under).

Appen het tidligere **Hagefugler** og lå på jakob-byte-2d.github.io/hagefugler/ (før det hagefugler-oslo/). Den gamle adressen virker ikke lenger. Avkrysningene, tellingene og kjøpene ligger på samme nettsted (jakob-byte-2d.github.io), så de følger med til den nye adressen i samme nettleser. Lagringsnøklene heter fortsatt `hagefugler…` av den grunn, og sikkerhetskopien har fortsatt `kortstokk: "hagefugler"`, så gamle kopier kan gjenopprettes. En hjemskjerm-app på iPhone har sitt eget lager: åpne den gamle appen (den virker fra hurtiglageret), trykk på ringen øverst og velg *Kopier sikkerhetskopi* under *Lagring* i fanen *Profil*, legg den nye adressen på hjemskjermen og velg *Gjenopprett* samme sted der.

## Innhold

```
fuglekort/
├── data/cards.json          Navn, sjeldenhet og teksten fra kortene (til søket) + posisjonen til SETT-ruta og datolinja
├── src/app.html             Selve appen (HTML, CSS og JavaScript i én fil)
├── src/sw.template.js       Mal for offline-støtte (service worker)
├── build.py                 Bygger docs/index.html og artifact.html fra src + data
├── importer_fuglekort.py    Henter kort, forklaringskort og bakside fra Fuglekort-builder
├── artifact.html            Versjonen som ligger publisert hos Claude
└── docs/                    Ferdig app – det er denne mappen GitHub Pages viser
    ├── index.html
    ├── manifest.webmanifest  Gjør at appen kan legges på hjemskjermen (PWA)
    ├── sw.js                 Gjør at appen virker uten nett etter første besøk
    ├── icons/                App-ikoner, laget av fuglen på baksiden
    ├── cards/                Kortbildene 001–100 med KI-illustrasjoner, bonuskortene b01–b05, forklaringskortene 000a og 000b,
    │                         bildekrediteringen for bonuskortene (b00) og bakside.webp
    ├── cards-foto/           Kortene som har fotografi (001–062, 064 og 073), bonuskortene med fotografi og kortene Bildekreditering (000c, b00)
    ├── cards-tegneserie/     Kortene som har tegneseriefugl (001–060 og 064) og bonuskortene i tegneseriestil (b01–b05)
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
- **Fotografier:** 64 fuglekort (001–062, 064 og 073) og alle fem bonuskortene har fotografi.
- **Tegneseriefugler:** 61 fuglekort (001–060 og 064) har tegneseriebilde. Importen kopierer `tegneserie.kortbilde` til `docs/cards-tegneserie/NNN.webp` (mappen tømmes først), og kortene får `bildeTegneserie` i `cards.json`; `data.tegneserie` er `true` når settet finnes. Miniatyrene `sprites/cards-tegneserie.webp` og `sprites/photos-tegneserie.webp` er KI-miniatyrene med tegneseriekortene byttet inn (`tegneserie.bilde` til søket). Kort uten tegneseriebilde viser KI-kortet. Forklaringskortene er de samme som i KI-valget, uten Bildekreditering, og det står ingen fotograf på kortene.
- **Bonuskortene i tegneseriestil** (b01 ekorn … b05 rødrev) lages her, ikke i Fuglekort-builder (den har de samme tegneseriebildene i `bilder_tegneserie/`, men bruker dem bare i utskriften): tegneseriebildene ligger i `kilder/bonus_tegneserie/` (b01_ekorn.jpg …, stående 533 × 631 som bildefeltet på kortet). `python3 lag_bonus_tegneserie.py sti/til/Fuglekort-builder` bygger kortene med kortmalen og teksten fra Fuglekort-builder i en midlertidig kopi (Fuglekort-builder endres ikke) og legger dem i `kilder/bonus_tegneserie/kort/` og de stående bildene (675 × 800) i `kilder/bonus_tegneserie/bilder/`. Importen tar dem med i `docs/cards-tegneserie/`, gir bonuskortene `bildeTegneserie` og bytter dem inn i tegneserieminiatyrene. Får Fuglekort-builder egne bonuskort i tegneseriestil i `kort.json`, brukes de i stedet. Kjør skriptet på nytt hvis teksten på bonuskortene endres i Fuglekort-builder.
- **Fullskjerm:** Trykk på bildefeltet på forsiden av et kort (den gule rammen), så kommer bildet opp i fullskjerm i samme stående format som på kortet, med knappene **KI · Foto · Tegneserie**. Knappene og sveip til sidene viser de andre bildene av fuglen; bildene ligger side om side og glir inn i full styrke, ingenting toner over (rekkefølgen er som knappene, sett fuglen mangler hoppes over, og piltastene gjør det samme). Det endrer ikke kortet: bildene på kortene velges bare i Innstillinger, og under knappene står det hva kortene viser, med lenken «Endre i Innstillinger». Mangler fuglen et bilde i et sett, er knappen grå, og det står hva som mangler. Med Foto står fotografen nederst i bildet. Trykk på bildet (eller utenfor, eller Esc) for å gå tilbake til kortet. Tidligere versjoner hadde eget bildevalg per kort (`hagefugler:bildekort`); det slettes når appen åpnes, og alle kortene følger Innstillinger.
- **Store bilder:** Fullskjermvisningen bruker de stående fuglebildene (675 × 800, samme format og utsnitt som bildet på kortet) som Fuglekort-builder lager til appen (`bilder/`, `bilder_foto/`, `bilder_tegneserie/` og bonuskortenes), lagret på nytt som WebP (kvalitet 80) i `docs/pictures/`, `docs/pictures-foto/` og `docs/pictures-tegneserie/`, ett per kort og sett (til sammen rundt 14 MB). `data.storeBilder` er `true` når de finnes. De lastes ned sammen med appen, så de virker uten nett. Uten dem viser fullskjermen bildefeltet klippet fra kortbildet.
- Valget lagres i `hagefugler:bilder` (`ki`, `foto` eller `tegneserie`). En lagret verdi som ikke finnes i dataene, blir `ki`.
- Alle settene lagres på telefonen (service workeren), så man kan bytte også uten nett. Bildevalget i Innstillinger vises når minst ett av foto- og tegneseriesettet finnes, og hvert valg skjules hvis settet mangler.

## Hagefugltelling

I fanen **Telling** under ringen øverst til høyre finnes **Start telling**. Skriv gjerne inn området, og trykk Start.

- **Mens du teller** går klokka i en linje under toppen. Under kortstokken står telleren for kortet du ser på: − og + (eller skriv inn tallet) for det høyeste antallet du har sett **samtidig**. Kort med antall får et gult merke i hjørnet. På tastatur: + og −.
- **Telleliste** viser alle artene med hver sin teller: **Ekorn** øverst (det står i skjemaet på Fuglevennen.no; når ekornkortet er funnet, telles det på kortet), så de vanligste hagefuglene først, og til slutt bonusdyrene du har funnet. Du kan søke etter en art. Trykker du på navnet, kommer du til kortet. Tellinger fra før bonuskortene, der ekorn ble lagret som `ekorn`, flyttes over på ekornkortet (`sciurus-vulgaris`) når de leses.
- **Avslutt** viser tallene i alfabetisk rekkefølge, som skjemaet på Fuglevennen.no. Har tellingen vart under én time, står det en påminnelse om at Fuglevennen anbefaler minst én time. Du kan fortsette eller avslutte og lagre. Da får alle fuglene i tellingen en observasjonsdag (datoen tellingen startet). Frøene flyr til frøtallet når du lukker sammendraget. En lagret telling kan slettes fra sammendraget (appen spør først); dagene den ga, blir liggende.
- **Tidligere tellinger** ligger i fanen Telling. Der kan du kopiere tallene som tekst, dele dem, åpne Fuglevennen.no eller slette tellingen.
- Tellingen lagres fortløpende, så den fortsetter der du slapp hvis appen lukkes.

## Bonuskort (andre dyr)

Fem bonuskort med de vanligste ville pattedyrene i hager: b01 ekorn, b02 rådyr, b03 hare, b04 elg og b05 rødrev
(rangert etter Hagefugltellingen 2024–2026). De lages i Fuglekort-builder (arket Bonuskort) og kommer med i importen fra
feltet `bonus` i `kort.json`. I `data/cards.json` har de `bonus: true`, `id` som `b01` og `lengde` i stedet for `vingespenn`.

**De er en belønning og en overraskelse.** Et bonuskort finnes ikke i appen før det er fortjent:

- Et bonuskort ved 5, 10, 20, 40 og 60 registreringer av fugler (`BONUS_GRENSER` i `src/app.html`), i rekkefølgen b01, b02 … En registrering er én observasjonsdag for én fugl, også de som kommer fra en hagefugltelling. Bonusdyrene teller ikke.
- Før det er fortjent, vises det ingen steder: ikke i kortstokken, scrubberen, søket, samlingen, «Sist sett», glinskortene, telleliste (ekorn står der som en vanlig rad, siden det er med i skjemaet) eller under **Om kortene**. `#b03` i adressen virker først når kortet er funnet. Kortet «Bildekreditering bonuskort» (b00) kommer under **?** når alle er funnet.
- Hint uten å si hva: fanen Profil har delen «Bonus» med et kort med spørsmålstegn og hvor mange registreringer som mangler, og skjermleseren sier «To registreringer til en bonus!» og «Én registrering til en bonus!».
- **Når et bonuskort er fortjent**, faller et kort med baksiden opp inn på skjermen og vugger, med et lysende spørsmålstegn. Trykk, så snur det seg: blader virvler ut, et stempel sier BONUSKORT, og det står hvilke kort det er stokket inn blant. Trykk igjen, så viser kortstokken hvor det havnet, og kortet lyser opp. Ingenting skjer av seg selv; hvert steg venter på et trykk. Avsløringen vises én gang (i Claude lagres det i samlingen `bonusvist`); bonuskort fortjent før denne versjonen avsløres første gang appen åpnes.
- Kortet stokkes inn blant fuglekortene med like mange stjerner, et sted mellom to av dem. Plassen er fast (regnes ut fra artsnavnet), så den er lik hver gang og på alle enheter. Ekorn (★★) havner blant kortene 018–032, rådyr (★★★) blant 033–048, og hare, elg og rødrev (★★★★) blant 049–068.
- Bonuskortene har **bronsekant** fra de er fortjent, og fargestripa til venstre for navnet er bronse med **BONUS** på høykant. Appen tegner stripa oppå kortbildet (fra skrifta på kortene, Barlow Condensed Bold, som en SVG-bane), så kortbildene fra Fuglekort-builder er uendret. Sølv, gull og holo erstatter bronsekanten når bonuskortet når de nivåene. Overskriften viser «Bonuskort» uten nummer, og samlingen viser bonuskortene med bronsekant og «Bonus» på dem som ikke er sett.
- Sletter du dager så du kommer under grensen, forsvinner kortet igjen, og det avsløres på nytt når det er fortjent.
- Bonuskortene får observasjonsdager og glinskant som fuglene, men teller ikke med i fuglelista: ringen, «av 100 fugler sett», poengene, sjeldenhetsstolpene og merkene gjelder bare fuglene.
- De har KI-illustrasjoner og fotografier som fuglene: KI-kortene i `docs/cards/`, kortene med fotografi i `docs/cards-foto/` (med `bildeFoto`, `fotograf` og `lisens` i `cards.json`). Med fotografier står fotografen og lisensen også nederst på baksiden av kortet.

## Solsikkefrø

Man tjener solsikkefrø og bruker dem til å låse opp kort. Alle tallene står samlet i `FRO` øverst i frødelen av `src/app.html`.

- **Åpne kort:** 001–025 er åpne fra start. 026–100 er grå kort: på sin plass i kortstokken, men bare navnet, stjernene, prisen og en lås vises. Bildet og teksten er skjult, også i samlingen, søket (grå kort finnes bare på navn), «Sist sett» og tellelista.
- **Tjene frø:** Premien vektes mot daglige observasjoner: registrering (én observasjonsdag for en fugl) 200 × stjerner, hver dag med minst én fugl registrert 300 (én gang per dag, også når det bare er grå kort), første gang man ser en art 400 × stjerner, sølv-/gull-/holokant 2 000 / 5 000 / 15 000, bonuskort 10 000, og merkene: 10 arter 2 500, 25 arter 5 000, 50 arter 15 000, hele kortstokken 50 000, sju på rad 5 000, hver 5. observasjonsdag 2 500, fire årstider 10 000, Tellekorps 7 500, Flokk 7 500. (Før oktober 2026 var det 100 × stjerner per registrering, 1 000 × stjerner første gang, ingen dagspremie og ett merke for 30 dager; saldoen regnes ut på nytt med de nye tallene.) Frøene flyr fra SETT-ruta på kortet opp til frøtallet, som teller opp mens de lander. Frøene toner fram mens de forlater kortet, så de ikke ser ut til å ligge på det før de flyr. Når de første frøene lander, vises et gult tall rett under frøtallet med hvor mye hendelsen ga (f.eks. «+1 100» eller «+10 000»); det forsvinner litt etter at det siste frøet har landet. Frø som låses til et grått kort, flyr til «frø venter»-merket på kortet i stedet. Frøene for en ny kant og for et bonuskort venter på feiringen: frøtallet viser dem ikke ennå. Når du trykker videre i feiringen, lyser frøtallet opp over feiringen, og en stor strøm av frø (30–120 frø, flere jo større beløp) renner fra kortet i feiringen inn i det, mens tallet teller opp. Når strømmen er ferdig, lukkes feiringen av seg selv og kortet vises i kortstokken. Står flere feiringer i kø, kommer neste litt etter, så kortet rekker å vises først. Strømmen tegnes på én canvas.
- **Grå kort:** Man kan registrere en fugl med grått kort, men får en advarsel hver gang og bare halvparten av frøene (registrering, første gang og nivåer). De frøene er låst til kortet («1 100 frø venter på kortet») og frigjøres når kortet låses opp. Registreringer på grå kort teller fullt mot bonuskort og merker. Glinskant vises først når kortet er åpnet.
- **Priser:** `pris = 3 000 × 1,035^(kortnr − 26) × stjernefaktor` (★★ 1,35 · ★★★ 1,8 · ★★★★ 2,4 · ★★★★★ 3,2), i hele frø uten avrunding (desimalene kuttes). Alle prisene er forskjellige og stiger bakover i kortstokken (appen sjekker det ved oppstart). Fra 026 Svartmeis 4 050 til 100 Lappugle 122 421, rundt 3 millioner til sammen.
- **Kjøpe:** Trykk på et grått kort («Lås opp Nøtteskrike for 7 359 frø?»), eller åpne Frøbutikken fra frøtallet øverst. Prisen trekkes fra frøtallet med en gang. **Angre:** Det siste kjøpet kan angres i to minutter (`FRO.angreTid`): øverst i Frøbutikken står «Siste kjøp: Svartmeis · 4 050 frø · kan angres i 1:53» med knappen Angre. Spørsmålet sier hvor mange frø du får tilbake (prisen minus frøene som legger seg på det grå kortet igjen). Kjøpet slettes fra `kjop`, og kortet blir grått. Bare det nyeste kjøpet kan angres, og ikke etter to minutter. Opplåsingen har sin egen hendelse: fargene fyller kortet nedenfra og frø drysser; den står til man trykker. Trykker du videre, strømmer frøene som ventet på kortet, inn i frøtallet på samme måte før kortet vises i kortstokken.
- **Profil:** delen «Solsikkefrø» viser saldo, tjent i alt, brukt, frø som venter på grå kort, åpne kort og hva frøene kom fra (registreringer, dager med fugler, første gang, glinskant, bonuskort, merker og frigjort fra låste kort). Merkene viser hvor mange frø de gir.
- **Lagring:** Saldoen regnes ut hver gang: tjent (fra observasjonene, nivåene, merkene og bonuskortene) minus brukt. Bare kjøpene lagres, i samlingen `kjop` (`kjop/garrulus-glandarius = { pris, dato, ts, graaDag? }`); i Claude deles de, på telefonen ligger de i `localStorage` (`hagefugler:kjop:v1`), og de er med i sikkerhetskopien. Frø fra dager før kjøpsdatoen gir halv verdi; dager fra og med kjøpsdatoen full verdi. Var fuglen allerede registrert på kjøpsdagen mens kortet var grått, lagres `graaDag: true`, og den dagen gir også halv verdi (ellers kunne man registrere grått og kjøpe samme dag for å få full verdi). Sletter man en dag, går saldoen ned av seg selv; kjøpte kort beholdes også om saldoen havner under null.
- **Tempo:** En simulering med fem registreringer om dagen (fugler trukket etter hvor vanlige de er, billigste kort kjøpes så snart frøene rekker) gir omtrent 35 åpne kort etter en uke, 45 etter en måned, 59 etter tre måneder, 71 etter et halvt år og 88 etter ett år. Med de gamle satsene ga samme simulering 36, 45, 55, 65 og 80: starten er den samme, men den som registrerer jevnt, kommer lenger.

## Testmodus

Mens appen testes, tas ikke gamle data vare på. `TESTMERKE` i `src/app.html`: når det endres, sletter appen observasjoner, tellinger, bonusvist og kjøp på hver enhet neste gang den åpnes. Den delte databasen i Claude tømmes når en ny versjon publiseres. Under Innstillinger finnes også «Nullstill alt (test)», som tømmer alt, også den delte lista.

## Glinskort og merker

Kanten på et kort blir sølv, gull eller holo når du har sett fuglen mange dager. Jo sjeldnere fugl, jo færre dager trengs:

| Sjeldenhet | Sølv | Gull | Holo |
|---|---|---|---|
| ★ | 10 | 25 | 50 |
| ★★ | 5 | 15 | 30 |
| ★★★ | 3 | 8 | 15 |
| ★★★★ | 1 | 3 | 6 |
| ★★★★★ | Holo med én gang | | |

- Bare den trykte kanten (den hvite kanten og den gule dobbeltstreken ytterst) byttes ut med **sølv**, **gull** eller **holo** (regnbue). Resten av kortet er uendret. En lysstripe glir sakte langs kanten av seg selv, følger fingeren når du drar i kortet og musa på datamaskin.
- **Vipping:** Under Innstillinger kan du la lyset følge telefonen når du vipper den. På Android er det på fra start; på iPhone må du slå det på, og telefonen spør om lov til å bruke bevegelsessensoren.
- **Merker:** 10, 25 og 50 arter, hele kortstokken, sju dager på rad, et merke for hver 5. observasjonsdag (5, 10, 15 … uten slutt; fanen Merker viser dem du har og det neste), fire årstider (vår, sommer, høst og vinter), Tellekorps (en hagefugltelling på minst én time) og Flokk (minst 20 av én art i en telling).
- Nivåer og merker regnes ut fra observasjonene og tellingene hver gang, så de lagres ikke for seg. Sletter du dager, kan et kort miste kanten igjen.
- Når et kort får sølv-, gull- eller holokant, kommer kortet fram over alt annet med lysstråler bak, den nye kanten lyser opp, og nivået står med store bokstaver. Den står til du trykker; da strømmer frøene for kanten fra kortet inn i frøtallet, og så vises kortet i kortstokken. Får flere kort nytt nivå samtidig, for eksempel etter en telling, vises de etter hverandre. Statistikken viser antall glinskort, hvilke kort som er nærmest neste nivå, og alle merkene med fremdrift. I samlingen har glinskortene sølv-, gull- eller holokant. Bonuskortene har bronsekant til de får et høyere nivå.
- Baksiden av et kort viser nivået og hvor mange dager som mangler til neste.

## Min fugleliste

Ringen øverst til høyre åpner **Min fugleliste**, delt i fem faner. Tittelen og fanene står fast øverst mens du ruller, og appen husker hvilken fane du brukte sist (på enheten, `fuglekort:fane`). Piltastene bytter fane.

- **Profil:** navnet ditt, hvor mange fugler du har sett av 100, poeng, merker oppnådd, solsikkefrøene (saldo, kilder og Frøbutikken), glinskortene, hvor mange registreringer som mangler til neste bonus, og lagring/sikkerhetskopi.
- **Statistikk:** sjeldneste funn, fuglen du har sett flest dager, observasjonsdager og registreringer, nye arter siste 12 måneder, fordeling etter sjeldenhet, nye arter per måned og «Sist sett».
- **Telling:** start eller fortsett en hagefugltelling, og tidligere tellinger.
- **Kort:** samlingen (fuglekortene med antall dager i hjørnet) og bonuskortene du har funnet.
- **Merker:** alle merkene, og merkene for hver 5. observasjonsdag.

**Flere brukere senere:** I dag er det én bruker per enhet («meg»). Brukerne ligger i `fuglekort:brukere` (`[{ id: "meg", navn: "Jakob" }]`) og den aktive i `fuglekort:bruker`. Alt som hører til en person, lagres under nøkler fra `brukerNokkel()` og `brukerSamling()`: den første brukeren beholder nøklene og samlingene appen alltid har brukt (`hagefugler-oslo:sett:v1`, `sett` …), mens en ny bruker `u2` får `hagefugler-oslo:sett:v1@u2` på telefonen og `sett_u2` i Claude. Bildevalg, fane og andre innstillinger gjelder enheten. Det som mangler for flere brukere, er bare et sted å legge til og bytte bruker (f.eks. øverst i Profil).

## Lagring av observasjoner

All lagring går gjennom objektet `Store` øverst i skriptet i `src/app.html`:

- **Som Claude-artifact** lagres observasjonene i artifactens database (samlingen `sett`, ett dokument per art, f.eks. `sett/parus-major = { art, date, dager, ts }`), så de følger med på alle enheter der du er logget inn. `dager` er alle dagene fuglen er sett, eldste først, og `date` er den første av dem (feltet er beholdt så eldre versjoner av appen fortsatt kan lese lista).
- Tellingene ligger i samlingen `tellinger`, ett dokument per telling, f.eks. `tellinger/t1790700000000 = { start, slutt, omrade, arter: { "parus-major": 4, "ekorn": 1 }, ts }`. `start` og `slutt` er tidspunkter i millisekunder, og `slutt` er 0 mens tellingen pågår. I den frittstående appen ligger de i `localStorage` under `hagefugler:tellinger:v1`.
- Avkrysninger fra før observasjonsdagene kom (bare `date`) blir automatisk fuglens første observasjonsdag.
- **Som frittstående app** lagres de i nettleserens `localStorage` på enheten. Under «Lagring» i fanen Profil finnes «Kopier sikkerhetskopi» og «Gjenopprett», så du kan flytte listen mellom enheter. Gjenoppretting legger dagene i kopien til dem du har, og tar også imot eldre kopier med én dato per fugl. Sikkerhetskopien har også med de avsluttede tellingene.

Vil du ha synkronisering i den frittstående appen, bytter du ut `connectRemote()` og `push()` i `Store` med kall mot din egen backend, for eksempel Firebase eller Supabase. Resten av appen trenger ingen endringer.

## Hente nye kort fra Fuglekort-builder

1. I **Fuglekort-builder**: endre regnearket, bildene eller baksiden og push. GitHub bygger kortene. Last ned «app» under *Actions → Bygg fuglekort → Artifacts* og pakk den ut. (Eller kjør `python bygg.py --uten-pdf` der, så ligger den i `ut/app`.)
2. Her: `python3 importer_fuglekort.py sti/til/app`
3. Commit og push. GitHub Pages oppdaterer appen, og telefonene henter de nye kortene selv.

Skriptet kopierer kortene, de to forklaringskortene, baksiden, fotosettet og tegneseriesettet (se over), finner SETT-ruta og datolinja, lager `data/cards.json`, miniatyrene og app-ikonene, og kjører `build.py`. Avkrysningene lagres på artens latinske navn (f.eks. `parus-major`), ikke på kortnummeret, så de følger fuglen når kortene får ny rekkefølge. Avkrysninger fra før dette (lagret på kortnummer) flyttes over automatisk ved hjelp av `data/tidligere_nummer.json`.

Miniatyrene i `docs/sprites/` er rutenett med 10 kolonner og én rad per ti kort. Appen regner ut antall rader selv.

## Bruk

- **Hold** på kortet, så løftes det og følger fingeren. **Dra det til kanten** og slipp for neste (venstre) eller forrige (høyre) kort.
- **Sveip fort** for å bla gjennom mange kort. Farten avtar av seg selv, og **et trykk** stopper blaingen.
- **Trykk** på kortet for å snu det og se baksiden. Trykk på bildet for å se det i fullskjerm; sveip der for å se KI, foto og tegneserie. Bildene på kortene velger du i Innstillinger.
- **Zoom:** Selve appen kan ikke zoomes (viewport med `user-scalable=no`, `touch-action: pan-x pan-y` på siden, og to-finger-bevegelser og Safaris gesture-hendelser stoppes). To fingre på kortet øverst i bunken, på et forklaringskort eller på fuglebildet i fullskjerm forstørrer det rundt punktet mellom fingrene (opptil 4 ganger), og det spretter tilbake når en finger slippes. En kopi vises over alt annet, så ingenting under flytter seg. På PC gjør Ctrl + rullehjul (eller knip på styreflaten) det samme; Ctrl +/− er ikke sperret. Forklaringskortene sveipes med appens egen sveip, så to fingre kan zoome.
- **Trykk på SETT** når du ser fuglen. Første gang kommer haken og datoen på kortet. En senere dag legger et nytt trykk til en ny observasjonsdag, og tallet ved SETT (f.eks. «× 7») viser hvor mange dager du har sett den. Et nytt trykk samme dag viser lista over dagene. Det er ingen meldinger nederst på skjermen og ingen angreknapp; en registrering fjernes ved å slette dagen på baksiden. Det som skjer, leses opp for skjermlesere.
- **I dag:** En fugl du har registrert i dag, får en grønn merkelapp «✓ Sett i dag» nederst i hjørnet av bildet. I samlingen og søket viser tallet i hjørnet hvor mange dager du har sett fuglen (gult, eller grønt når du har sett den i dag), og under «Sist sett» står det «I dag». Merkingen forsvinner ved midnatt, også når appen står åpen. «Sjeldneste funn» i fanen Statistikk er fuglen med høyest kortnummer du har sett (kortene går fra den vanligste, 001, til den sjeldneste).
- **Baksiden** av et kort du har sett, viser alle dagene. Der kan du slette en dag (×) eller legge til en dag du glemte. Datoen på forsiden er første gang; endrer du den, flyttes den dagen.
- **Menyen** (☰ øverst til høyre) samler **Søk etter fugl**, **Om kortene** (forklaringskortene: Om kortene og Tegnforklaring) og **Innstillinger**. Øverst ellers: frøtallet (åpner Frøbutikken) og ringen (statistikken).
- **Innstillinger**: Under «Bilder på kortene» velger du **KI-illustrasjoner** (standard, som på de trykte kortene), **Fotografier** fra Artsdatabanken og Artsobservasjoner eller **Tegneseriefugler** (fuglene tegnet i tegneseriestil, for 61 av 100 fugler, og bonuskortene). Kort uten bilde i valgt sett viser illustrasjonen, og i fotovalget kommer kortet Bildekreditering med under **Om kortene**. Piltastene går gjennom alle valgene. Valget gjelder alle kortene, huskes på enheten og påvirker ikke avkrysningene. I fullskjerm kan du se de andre bildene uten å endre kortet.
- **Tilbake** (knappen eller bevegelsen på Android, og sveip fra kanten på iPhone) lukker det som ligger øverst: et spørsmål, fullskjermbildet, en feiring, menyen eller et panel, akkurat som Esc. Først når ingenting er åpent, går tilbake ut av appen. Appen legger til ett steg i nettleserhistorikken mens noe er åpent, og fjerner det igjen når du lukker med en knapp eller et trykk.
- Tastatur: ← → blar, mellomrom snur kortet, S registrerer i dag, / åpner søk, ? viser forklaringskortene, Esc stopper blaing og lukker paneler.
