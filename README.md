# Hagefugler Oslo

Kortstokk med 100 fuglekort fra Oslo. Du kan sveipe for å bla, snu kortene, søke på navn eller kjennetegn, krysse av fuglene du har sett med dato og se statistikk.

Appen ligger på **https://jakob-byte-2d.github.io/hagefugler-oslo/** når GitHub Pages er slått på (se under).

## Innhold

```
hagefugler-oslo/
├── data/cards.json          Navn, sjeldenhet og teksten fra kortene (til søket) + posisjonen til SETT-ruta og datolinja
├── src/app.html             Selve appen (HTML, CSS og JavaScript i én fil)
├── src/sw.template.js       Mal for offline-støtte (service worker)
├── build.py                 Bygger docs/index.html og artifact.html fra src + data
├── artifact.html            Versjonen som ligger publisert hos Claude
└── docs/                    Ferdig app – det er denne mappen GitHub Pages viser
    ├── index.html
    ├── manifest.webmanifest  Gjør at appen kan legges på hjemskjermen (PWA)
    ├── sw.js                 Gjør at appen virker uten nett etter første besøk
    ├── icons/                App-ikoner
    ├── cards/001–100.webp    Kortbildene (750 × 1050 px, avrundede hjørner)
    └── sprites/              Små miniatyrer til søk og samlingen
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

Da starter den i fullskjerm med eget ikon, og kortene virker uten nett. Etter endringer: kjør `python3 build.py`, øk `CACHE` i `src/sw.template.js`, og push.

**I App Store og Google Play.** Pakk `docs/` med [Capacitor](https://capacitorjs.com):

```
npm init -y
npm i @capacitor/core @capacitor/cli @capacitor/ios @capacitor/android
npx cap init "Hagefugler Oslo" no.hagefugler.oslo --web-dir docs
npx cap add ios && npx cap add android
npx cap open ios        # eller: npx cap open android
```

## Lagring av avkrysninger

All lagring går gjennom objektet `Store` øverst i skriptet i `src/app.html`:

- **Som Claude-artifact** lagres avkrysningene i artifactens database (samlingen `sett`, ett dokument per kort, f.eks. `sett/024 = { nr, date, ts }`), så de følger med på alle enheter der du er logget inn.
- **Som frittstående app** lagres de i nettleserens `localStorage` på enheten. Under «Lagring» i statistikkmenyen finnes «Kopier sikkerhetskopi» og «Gjenopprett», så du kan flytte listen mellom enheter.

Vil du ha synkronisering i den frittstående appen, bytter du ut `connectRemote()` og `push()` i `Store` med kall mot din egen backend, for eksempel Firebase eller Supabase. Resten av appen trenger ingen endringer.

## Endre eller legge til kort

1. Rediger `data/cards.json`. Legger du til et kort, legg bildet i `docs/cards/` og fyll inn `sett.boks` (x, y, bredde, høyde) og `sett.linje` (x, y, bredde) som andeler av kortets bredde og høyde.
2. Kjør `python3 build.py`.
3. Øk `CACHE`-versjonen i `src/sw.template.js` hvis appen allerede er installert, så telefonene henter de nye filene.

Miniatyrene i `docs/sprites/` er rutenett med 10 kolonner og én rad per ti kort. Appen regner ut antall rader selv, så nye kort trenger bare nye miniatyrer.

## Bruk

- **Hold** på kortet, så løftes det og følger fingeren. **Dra det til kanten** og slipp for neste (venstre) eller forrige (høyre) kort.
- **Sveip fort** for å bla gjennom mange kort. Farten avtar av seg selv, og **et trykk** stopper blaingen.
- **Trykk** på kortet for å snu det og se baksiden.
- Tastatur: ← → blar, mellomrom snur kortet, S krysser av, / åpner søk, Esc stopper blaing og lukker paneler.
