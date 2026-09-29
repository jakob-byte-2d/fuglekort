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
    ├── cards/                Kortbildene 001–100 med KI-illustrasjoner, forklaringskortene 000a og 000b, og bakside.webp
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
- **Telleliste** viser alle artene med hver sin teller, de vanligste hagefuglene først og **Ekorn** øverst (det står i skjemaet på Fuglevennen.no). Du kan søke etter en art. Trykker du på navnet, kommer du til kortet.
- **Avslutt** viser tallene i alfabetisk rekkefølge, som skjemaet på Fuglevennen.no. Har tellingen vart under én time, står det en påminnelse om at Fuglevennen anbefaler minst én time. Du kan fortsette eller avslutte og lagre. Da får alle fuglene i tellingen en observasjonsdag (datoen tellingen startet). Du angrer i meldingen nederst.
- **Tidligere tellinger** ligger under Hagefugltelling i statistikken. Der kan du kopiere tallene som tekst, dele dem, åpne Fuglevennen.no eller slette tellingen.
- Tellingen lagres fortløpende, så den fortsetter der du slapp hvis appen lukkes.

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
- Når et kort får sølv-, gull- eller holokant, kommer kortet fram over alt annet med lysstråler bak, den nye kanten lyser opp, og nivået står med store bokstaver. Trykk for å fortsette (det lukker seg selv etter noen sekunder). Får flere kort nytt nivå samtidig, for eksempel etter en telling, vises de etter hverandre. Nye merker står i meldingen nederst. Statistikken viser antall glinskort, hvilke kort som er nærmest neste nivå, og alle merkene med fremdrift. I samlingen har glinskortene sølv-, gull- eller holokant.
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
