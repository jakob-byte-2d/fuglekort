#!/usr/bin/env python3
"""Bygger Hagefugler fra src/app.html + data/cards.json (og data/kortstokk.json: fuglene i kortstokken).

Lager docs/index.html: den frittstående appen (PWA) med manifest og offline-støtte, publisert med GitHub Pages på
jakob-byte-2d.github.io/fuglekort/. (Claude-versjonen, artifact.html, bygges ikke lenger fra oktober 2026.)

Med --play MAPPE lages Play-versjonen (Google Play, TWA) i MAPPE i stedet, f.eks. ../fuglekort_nettside/app, som
GitHub Pages serverer på https://fuglekort.no/app/. Den har eget manifest (id, start_url og scope = /app/), egen
service worker (hurtigbufferen hagefugler-play-…), appversjonen play-<versjon>-<hash> (versjonen i data/play.json)
og bare filene appen bruker. docs/ må være bygget først, for bildene kopieres derfra.

Kjør:  python3 build.py
       python3 build.py --play ../fuglekort_nettside/app
"""
import argparse, hashlib, json, re, pathlib, shutil

ROOT = pathlib.Path(__file__).parent
ap = argparse.ArgumentParser(description="Bygger Hagefugler (docs/) eller Play-versjonen (--play MAPPE).")
ap.add_argument("--play", metavar="MAPPE", help="lag Play-versjonen i MAPPE (served at https://fuglekort.no/app/)")
arg = ap.parse_args()
PLAY = json.loads((ROOT / "data" / "play.json").read_text(encoding="utf-8")) if arg.play else None
UT = pathlib.Path(arg.play).resolve() if arg.play else ROOT / "docs"
MERKE = ".play-bygg"                                     # the Play folder is emptied first, only if it is ours
if PLAY:
    if UT.exists() and any(UT.iterdir()) and not (UT / MERKE).exists():
        raise SystemExit(f"{UT} finnes og er ikke en Play-bygging (mangler {MERKE}). Velg en tom mappe.")
    if UT.exists():
        shutil.rmtree(UT)
    UT.mkdir(parents=True)
    (UT / MERKE).write_text("Laget av build.py --play i repoet fuglekort. Alt her lages på nytt ved hver bygging.\n", encoding="utf-8")
src = (ROOT / "src" / "app.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "data" / "cards.json").read_text(encoding="utf-8"))
# baksider to buy in Frøbutikken (see README): kept apart from cards.json, which importer_fuglekort.py writes anew
bak = ROOT / "data" / "baksider.json"
if bak.is_file():
    data["baksider"] = json.loads(bak.read_text(encoding="utf-8"))
# the deck: the birds registered in gardens (data/kortstokk.json, from velg_kortstokk.py). The other bird cards stay
# in the data, marked «ute»: out of the deck, the search and the counts, but the seeds already earned for them stay
stokk = ROOT / "data" / "kortstokk.json"
if stokk.is_file():
    ks = json.loads(stokk.read_text(encoding="utf-8"))
    inne = {a["key"] for a in ks["arter"]}
    for c in data["kort"]:
        if not c.get("bonus") and c["key"] not in inne:
            c["ute"] = True
    data["tittel"] = ks.get("tittel") or data.get("tittel")
i_stokken = [c for c in data["kort"] if not c.get("ute")]
NB = sum(1 for c in i_stokken if not c.get("bonus"))

# Inline the card data (</ is escaped so the JSON can never close the <script> tag)
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
fragment = src.replace("__CARDS_JSON__", payload)
# the version sent with the statistics (Deling): follows the code and the card data; Play: play-<versjon>-<hash>
VERSJON = hashlib.sha1((src + payload).encode("utf-8")).hexdigest()[:10]
if PLAY:
    VERSJON = f"play-{PLAY['versjon']}-{VERSJON}"
fragment = fragment.replace("__VERSJON__", VERSJON)
# the fonts on the same server (no calls to Google Fonts): fonts/fonter.css inline, the woff2 files next to the app
FONTER = (ROOT / "fonts" / "fonter.css").read_text(encoding="utf-8").strip()
FONTFILER = sorted(p.name for p in (ROOT / "fonts").iterdir() if p.suffix in (".woff2", ".woff", ".txt"))

# The standalone app: full document, title moved into <head>, manifest + service worker
title_m = re.search(r"<title>.*?</title>\s*", fragment, re.S)
title = title_m.group(0).strip() if title_m else "<title>Hagefugler</title>"
body = fragment.replace(title_m.group(0), "", 1) if title_m else fragment
head = f"""<!doctype html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
{title}
<meta name="description" content="{NB} hagefugler i Norge som en kortstokk. Bla, søk og kryss av fuglene du har sett.">
<meta name="theme-color" content="#0f4a36">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Hagefugler">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<style>
{FONTER}
</style>
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
"""
tail = """
<script>
if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
  addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
}
</script>
</body>
</html>
"""
(UT / "index.html").write_text(head + body + tail, encoding="utf-8")
(UT / "fonts").mkdir(exist_ok=True)
for f in FONTFILER:
    shutil.copyfile(ROOT / "fonts" / f, UT / "fonts" / f)

# Service worker precache list follows the card data, so new cards are cached automatically
assets = ["./", "index.html", "manifest.webmanifest", "sprites/photos.webp", "sprites/cards.webp", "sprites/titler.webp",
          "icons/icon-192.png", "icons/icon-512.png", "icons/icon-512-maskable.png", "icons/apple-touch-icon.png"]
assets += [f"fonts/{f}" for f in FONTFILER if f.endswith((".woff2", ".woff"))]
assets += [data.get("bakside", "cards/bakside.webp")] + [h["bilde"] for h in data.get("hjelp", [])] + [c["bilde"] for c in i_stokken]
assets += [b["bilde"] for b in data.get("baksider", []) if b.get("bilde") and b["bilde"] not in assets]
# alle bildesettene lagres på telefonen, så man kan bytte i innstillingene også uten nett
if data.get("hjelpFoto"):
    assets += ["sprites/cards-foto.webp", "sprites/photos-foto.webp"]
    assets += [h["bilde"] for h in data["hjelpFoto"] if h["bilde"] not in assets]
    assets += [c["bildeFoto"] for c in i_stokken if c.get("bildeFoto")]
if data.get("tegneserie"):
    assets += ["sprites/cards-tegneserie.webp", "sprites/photos-tegneserie.webp"]
    assets += [c["bildeTegneserie"] for c in i_stokken if c.get("bildeTegneserie")]
# de store fuglebildene til fullskjermvisningen (alle tre bildesettene) lastes ned sammen med appen
if data.get("storeBilder"):
    for c in i_stokken:
        assets.append(f"pictures/{c['id']}.webp")
        if c.get("bildeFoto"):
            assets.append(f"pictures-foto/{c['id']}.webp")
        if c.get("bildeTegneserie"):
            assets.append(f"pictures-tegneserie/{c['id']}.webp")
# Play: the files the app uses, copied from docs/ (built first), and its own manifest with /app/ as id, start and scope
if PLAY:
    mangler = []
    for f in dict.fromkeys(assets):
        if f in ("./", "index.html", "manifest.webmanifest") or f.startswith("fonts/"):
            continue
        kilde = ROOT / "docs" / f
        if not kilde.is_file():
            mangler.append(f); continue
        (UT / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(kilde, UT / f)
    if mangler:
        raise SystemExit("Mangler i docs/ (bygg docs først): " + ", ".join(mangler[:10]))
    manifest = json.loads((ROOT / "docs" / "manifest.webmanifest").read_text(encoding="utf-8"))
    manifest.update({"name": PLAY.get("navn", "Hagefugler"), "short_name": PLAY.get("navn", "Hagefugler"),
                     "id": "/app/", "start_url": "/app/", "scope": "/app/"})
    (UT / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
# The cache name follows the content, so phones fetch new cards automatically after every change
h = hashlib.sha1((UT / "index.html").read_bytes())
for f in assets:
    fp = UT / f
    if fp.is_file():
        h.update(fp.read_bytes())
sw = (ROOT / "src" / "sw.template.js").read_text(encoding="utf-8").replace("__ASSETS__", json.dumps(assets, indent=2))
sw = re.sub(r"const CACHE = '[^']*';", f"const CACHE = '{'hagefugler-play' if PLAY else 'hagefugler'}-{h.hexdigest()[:10]}';", sw)
(UT / "sw.js").write_text(sw, encoding="utf-8")

if PLAY:
    n = sum(1 for p in UT.rglob("*") if p.is_file()); mb = sum(p.stat().st_size for p in UT.rglob("*") if p.is_file()) / 1e6
    print(f"Bygget Play-versjonen {VERSJON}: {NB} fuglekort i kortstokken, {n} filer ({mb:.1f} MB) → {UT}")
else:
    print(f"Bygget {NB} fuglekort i kortstokken ({len(data['kort'])} kort i alt) → docs/index.html")
