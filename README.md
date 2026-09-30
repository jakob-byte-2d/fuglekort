# Hagefugler

Kortstokk med 100 fuglekort med hagefugler i Norge. Du kan sveipe for å bla, snu kortene, søke på navn eller kjennetegn, registrere hvilke dager du har sett hver fugl, telle fugler til Hagefugltellingen, samle glinskort og merker og se statistikk. Knappen **?** viser de to forklaringskortene.

Kortene lages i repoet **Fuglekort-** (Fuglekort-fabrikken). Dette repoet er appen som viser dem.

Appen ligger på **https://jakob-byte-2d.github.io/hagefugler/** når GitHub Pages er slått på (se under).

## Innhold

```
hagefugler/
├── data/cards.json          Navn, sjeldenhet og teksten fra kortene (til søket) + posisjonen til SETT-ruta og datolinja
├── src/app.html             Selve appen (HTML, CSS og JavaScript i én fil)
├── src/sw.template.js       Mal for offline-støtte (service worker)
├── build.py                 Bygger docs/index.html og artifact.html fra src + data
├── importer_fuglekort.py    Henter kort, forklaringskort og bakside fra Fuglekort-
├── artifact.html            Versjonen som ligger publisert hos Claude
└── docs/                    Ferdig app – det er denne mappen GitHub Pages viser
    ├── index.html
    ├── manifest.webmanifest  Gjør at appen kan legges på hjemskjermen (PWA)
    ├── sw.js                 Gjør at appen virker uten nett etter første besøk
    ├── icons/                App-ikoner, laget av fuglen på baksiden
    ├── cards/                Kortbildene 001–100 med KI-illustrasjoner, bonuskortene b01–b05, forklaringskortene 000a og 000b,
    │                         bildekrediteringen for bonuskortene (b00) og bakside.webp
    ├── cards-foto/           Kortene som har fotografi fra Artsdatabanken, og kortet Bildekreditering (000c)
    └── sprites/              Små miniatyrer til søk og samlingen (cards/photos og cards-foto/photos-foto)
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
npx cap init "Hagefugler" no.hagefugler.app --web-dir docs
npx cap add ios && npx cap add android
npx cap open ios        # eller: npx cap open android
```

## Fotografier eller KI-illustrasjoner

Fuglekort- lager to sett kort til appen: KI-illustrasjonene (`kort/`) og fotografiene fra mappen
`bilder_artsdatabanken` (`kort_foto/`, med fotokreditering). Importen kopierer bare kortene som faktisk har
fotografi til `docs/cards-foto/`; de andre er like KI-kortene og gjenbrukes. I `data/cards.json` har disse kortene
`bildeFoto`, `fotograf` og `lisens`, og `hjelpFoto` er forklaringskortene med Bildekreditering. Begge settene
lagres på telefonen, så man kan bytte også uten nett. Finnes ikke fotosettet, skjules tannhjulet.

## Hagefugltelling

Under statistikken (ringen øverst til høyre) finnes **Start telling**. Skriv gjerne inn området, og trykk Start.

- **Mens du teller** går klokka i en linje under toppen. Under kortstokken står telleren for kortet du ser på: − og + (eller skriv inn tallet) for det høyeste antallet du har sett **samtidig**. Kort med antall får et gult merke i hjørnet. På tastatur: + og −.
- **Telleliste** viser alle artene med hver sin teller: **Ekorn** øverst (det står i skjemaet på Fuglevennen.no; når ekornkortet er funnet, telles det på kortet), så de vanligste hagefuglene først, og til slutt bonusdyrene du har funnet. Du kan søke etter en art. Trykker du på navnet, kommer du til kortet. Tellinger fra før bonuskortene, der ekorn ble lagret som `ekorn`, flyttes over på ekornkortet (`sciurus-vulgaris`) når de leses.
- **Avslutt** viser tallene i alfabetisk rekkefølge, som skjemaet på Fuglevennen.no. Har tellingen vart under én time, står det en påminnelse om at Fuglevennen anbefaler minst én time. Du kan fortsette eller avslutte og lagre. Da får alle fuglene i tellingen en observasjonsdag (datoen tellingen startet). Du angrer i meldingen nederst.
- **Tidligere tellinger** ligger under Hagefugltelling i statistikken. Der kan du kopiere tallene som tekst, dele dem, åpne Fuglevennen.no eller slette tellingen.
- Tellingen lagres fortløpende, så den fortsetter der du slapp hvis appen lukkes.

## Bonuskort (andre dyr)

Fem bonuskort med de vanligste ville pattedyrene i hager: b01 ekorn, b02 rådyr, b03 hare, b04 elg og b05 rødrev
(rangert etter Hagefugltellingen 2024–2026). De lages i Fuglekort- (arket Bonuskort) og kommer med i importen fra
feltet `bonus` i `kort.json`. I `data/cards.json` har de `bonus: true`, `id` som `b01` og `lengde` i stedet for `vingespenn`.

**De er en belønning og en overraskelse.** Et bonuskort finnes ikke i appen før det er fortjent:

- Et bonuskort ved 5, 10, 20, 40 og 60 registreringer av fugler (`BONUS_GRENSER` i `src/app.html`), i rekkefølgen b01, b02 … En registrering er én observasjonsdag for én fugl, også de som kommer fra en hagefugltelling. Bonusdyrene teller ikke.
- Før det er fortjent, vises det ingen steder: ikke i kortstokken, scrubberen, søket, samlingen, «Sist sett», glinskortene, telleliste (ekorn står der som en vanlig rad, siden det er med i skjemaet) eller under **?**. `#b03` i adressen virker først når kortet er funnet. Kortet «Bildekreditering bonuskort» (b00) kommer under **?** når alle er funnet.
- Hint uten å si hva: statistikken har delen «Bonus» med et kort med spørsmålstegn og hvor mange registreringer som mangler, og meldingen nederst sier «To registreringer til en bonus!» og «Én registrering til en bonus!».
- **Når et bonuskort er fortjent**, faller et kort med baksiden opp inn på skjermen og vugger, med et lysende spørsmålstegn. Trykk, så snur det seg: blader virvler ut, et stempel sier BONUSKORT, og det står hvilke kort det er stokket inn blant. Trykk igjen, så viser kortstokken hvor det havnet, og kortet lyser opp. Ingenting skjer av seg selv; hvert steg venter på et trykk. Avsløringen vises én gang (i Claude lagres det i samlingen `bonusvist`); bonuskort fortjent før denne versjonen avsløres første gang appen åpnes.
- Kortet stokkes inn blant fuglekortene med like mange stjerner, et sted mellom to av dem. Plassen er fast (regnes ut fra artsnavnet), så den er lik hver gang og på alle enheter. Ekorn (★★) havner blant kortene 018–032, rådyr (★★★) blant 033–048, og hare, elg og rødrev (★★★★) blant 049–068.
- Et **BONUS-merke** ligger nederst til høyre på kortet, over det trykte kortnummeret. Overskriften viser «Bonuskort» uten nummer, og samlingen viser «Bonus» på kortene som ikke er sett.
- Angrer du registreringen som ga et bonuskort, eller sletter dager så du kommer under grensen, forsvinner kortet igjen, og det avsløres på nytt når det er fortjent.
- Bonuskortene får observasjonsdager og glinskant som fuglene, men teller ikke med i fuglelista: ringen, «av 100 fugler sett», poengene, sjeldenhetsstolpene og merkene gjelder bare fuglene.
- De har KI-illustrasjoner og fotografier som fuglene: KI-kortene i `docs/cards/`, kortene med fotografi i `docs/cards-foto/` (med `bildeFoto`, `fotograf` og `lisens` i `cards.json`). Med fotografier står fotografen og lisensen også nederst på baksiden av kortet.

## Solsikkefrø

Man tjener solsikkefrø og bruker dem til å låse opp kort. Alle tallene står samlet i `FRO` øverst i frødelen av `src/app.html`.

- **Åpne kort:** 001–025 er åpne fra start. 026–100 er grå kort: på sin plass i kortstokken, men bare navnet, stjernene, prisen og en lås vises. Bildet og teksten er skjult, også i samlingen, søket (grå kort finnes bare på navn), «Sist sett» og tellelista.
- **Tjene frø:** registrering (én observasjonsdag) 100 × stjerner, første gang man ser en art 1 000 × stjerner, sølv-/gull-/holokant 2 000 / 5 000 / 15 000, bonuskort 10 000, og merkene: 10 arter 2 500, 25 arter 5 000, 50 arter 15 000, hele kortstokken 50 000, sju på rad 5 000, 30 dager 7 500, fire årstider 10 000, Tellekorps 7 500, Flokk 7 500. Meldingen nederst viser f.eks. «+300 frø», og frøtallet øverst teller opp.
- **Grå kort:** Man kan registrere en fugl med grått kort, men får en advarsel hver gang og bare halvparten av frøene (registrering, første gang og nivåer). De frøene er låst til kortet («1 100 frø venter på kortet») og frigjøres når kortet låses opp. Registreringer på grå kort teller fullt mot bonuskort og merker. Glinskant vises først når kortet er åpnet.
- **Priser:** `pris = 3 000 × 1,035^(kortnr − 26) × stjernefaktor` (★★ 1,35 · ★★★ 1,8 · ★★★★ 2,4 · ★★★★★ 3,2), i hele frø uten avrunding (desimalene kuttes). Alle prisene er forskjellige og stiger bakover i kortstokken (appen sjekker det ved oppstart). Fra 026 Svartmeis 4 050 til 100 Lappugle 122 421, rundt 3 millioner til sammen.
- **Kjøpe:** Trykk på et grått kort («Lås opp Nøtteskrike for 7 359 frø?»), eller åpne Frøbutikken fra frøtallet øverst. Opplåsingen har sin egen hendelse: fargene fyller kortet nedenfra og frø drysser; den står til man trykker.
- **Statistikk:** delen «Solsikkefrø» viser saldo, tjent i alt, brukt, frø som venter på grå kort, åpne kort og hva frøene kom fra. Merkene viser hvor mange frø de gir. Innstillinger (tannhjulet) ligger nå øverst i statistikken, for å gi plass til frøtallet.
- **Lagring:** Saldoen regnes ut hver gang: tjent (fra observasjonene, nivåene, merkene og bonuskortene) minus brukt. Bare kjøpene lagres, i samlingen `kjop` (`kjop/garrulus-glandarius = { pris, dato, ts }`); i Claude deles de, på telefonen ligger de i `localStorage` (`hagefugler:kjop:v1`), og de er med i sikkerhetskopien. Frø fra dager før kjøpsdatoen gir halv verdi; dager fra og med kjøpsdatoen full verdi. Angrer man en registrering, går saldoen ned av seg selv; kjøpte kort beholdes også om saldoen havner under null.
- **Tempo:** En simulering med fem registreringer om dagen gir omtrent 38 åpne kort etter en uke, 46 etter en måned, 56 etter tre måneder, 65 etter et halvt år og 78 etter ett år.

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
- **Merker:** 10, 25 og 50 arter, hele kortstokken, sju dager på rad, 30 observasjonsdager, fire årstider (vår, sommer, høst og vinter), Tellekorps (en hagefugltelling på minst én time) og Flokk (minst 20 av én art i en telling).
- Nivåer og merker regnes ut fra observasjonene og tellingene hver gang, så de lagres ikke for seg. Sletter du dager, kan et kort miste kanten igjen.
- Når et kort får sølv-, gull- eller holokant, kommer kortet fram over alt annet med lysstråler bak, den nye kanten lyser opp, og nivået står med store bokstaver. Den står til du trykker. Får flere kort nytt nivå samtidig, for eksempel etter en telling, vises de etter hverandre. Nye merker står i meldingen nederst. Statistikken viser antall glinskort, hvilke kort som er nærmest neste nivå, og alle merkene med fremdrift. I samlingen har glinskortene sølv-, gull- eller holokant.
- Baksiden av et kort viser nivået og hvor mange dager som mangler til neste.

## Lagring av observasjoner

All lagring går gjennom objektet `Store` øverst i skriptet i `src/app.html`:

- **Som Claude-artifact** lagres observasjonene i artifactens database (samlingen `sett`, ett dokument per art, f.eks. `sett/parus-major = { art, date, dager, ts }`), så de følger med på alle enheter der du er logget inn. `dager` er alle dagene fuglen er sett, eldste først, og `date` er den første av dem (feltet er beholdt så eldre versjoner av appen fortsatt kan lese lista).
- Tellingene ligger i samlingen `tellinger`, ett dokument per telling, f.eks. `tellinger/t1790700000000 = { start, slutt, omrade, arter: { "parus-major": 4, "ekorn": 1 }, ts }`. `start` og `slutt` er tidspunkter i millisekunder, og `slutt` er 0 mens tellingen pågår. I den frittstående appen ligger de i `localStorage` under `hagefugler:tellinger:v1`.
- Avkrysninger fra før observasjonsdagene kom (bare `date`) blir automatisk fuglens første observasjonsdag.
- **Som frittstående app** lagres de i nettleserens `localStorage` på enheten. Under «Lagring» i statistikkmenyen finnes «Kopier sikkerhetskopi» og «Gjenopprett», så du kan flytte listen mellom enheter. Gjenoppretting legger dagene i kopien til dem du har, og tar også imot eldre kopier med én dato per fugl. Sikkerhetskopien har også med de avsluttede tellingene.

Vil du ha synkronisering i den frittstående appen, bytter du ut `connectRemote()` og `push()` i `Store` med kall mot din egen backend, for eksempel Firebase eller Supabase. Resten av appen trenger ingen endringer.

## Hente nye kort fra Fuglekort-

1. I **Fuglekort-**: endre regnearket, bildene eller baksiden og push. GitHub bygger kortene. Last ned «app» under *Actions → Bygg fuglekort → Artifacts* og pakk den ut. (Eller kjør `python bygg.py --uten-pdf` der, så ligger den i `ut/app`.)
2. Her: `python3 importer_fuglekort.py sti/til/app`
3. Commit og push. GitHub Pages oppdaterer appen, og telefonene henter de nye kortene selv.

Skriptet kopierer kortene, de to forklaringskortene, baksiden og fotosettet (se under), finner SETT-ruta og datolinja, lager `data/cards.json`, miniatyrene og app-ikonene, og kjører `build.py`. Avkrysningene lagres på artens latinske navn (f.eks. `parus-major`), ikke på kortnummeret, så de følger fuglen når kortene får ny rekkefølge. Avkrysninger fra før dette (lagret på kortnummer) flyttes over automatisk ved hjelp av `data/tidligere_nummer.json`.

Miniatyrene i `docs/sprites/` er rutenett med 10 kolonner og én rad per ti kort. Appen regner ut antall rader selv.

## Bruk

- **Hold** på kortet, så løftes det og følger fingeren. **Dra det til kanten** og slipp for neste (venstre) eller forrige (høyre) kort.
- **Sveip fort** for å bla gjennom mange kort. Farten avtar av seg selv, og **et trykk** stopper blaingen.
- **Trykk** på kortet for å snu det og se baksiden.
- **Trykk på SETT** når du ser fuglen. Første gang kommer haken og datoen på kortet. En senere dag legger et nytt trykk til en ny observasjonsdag, og tallet ved SETT (f.eks. «× 7») viser hvor mange dager du har sett den. Et nytt trykk samme dag viser lista over dagene. Du angrer i meldingen nederst.
- **Baksiden** av et kort du har sett, viser alle dagene. Der kan du slette en dag (×) eller legge til en dag du glemte. Datoen på forsiden er første gang; endrer du den, flyttes den dagen.
- **?** øverst viser forklaringskortene (Om kortene og Tegnforklaring).
- **Tannhjulet** åpner Innstillinger. Under «Bilder på kortene» velger du **KI-illustrasjoner** (standard, som på de trykte kortene) eller **Fotografier** fra Artsdatabanken og Artsobservasjoner. Arter uten fotografi viser illustrasjonen, og i fotovalget kommer kortet Bildekreditering med under **?**. Valget huskes på enheten og påvirker ikke avkrysningene.
- Tastatur: ← → blar, mellomrom snur kortet, S registrerer i dag, / åpner søk, ? viser forklaringskortene, Esc stopper blaing og lukker paneler.
