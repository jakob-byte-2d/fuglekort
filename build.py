#!/usr/bin/env python3
"""Bygger Fuglekort fra src/app.html + data/cards.json.

Lager to utgaver av samme side:
  docs/index.html     – frittstående app (PWA): full HTML med manifest og offline-støtte
  artifact.html       – fragmentet som publiseres som Claude-artifact

Kjør:  python3 build.py
"""
import json, re, pathlib

ROOT = pathlib.Path(__file__).parent
src = (ROOT / "src" / "app.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "data" / "cards.json").read_text(encoding="utf-8"))

# Inline the card data (</ is escaped so the JSON can never close the <script> tag)
payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
fragment = src.replace("__CARDS_JSON__", payload)

# 1) Claude artifact: the fragment as-is (the platform adds <html>/<head>/<body>)
(ROOT / "artifact.html").write_text(fragment, encoding="utf-8")

# 2) Standalone app: full document, title moved into <head>, manifest + service worker
title_m = re.search(r"<title>.*?</title>\s*", fragment, re.S)
title = title_m.group(0).strip() if title_m else "<title>Fuglekort</title>"
body = fragment.replace(title_m.group(0), "", 1) if title_m else fragment
head = f"""<!doctype html>
<html lang="nb">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
{title}
<meta name="description" content="100 fuglekort med hagefugler i Norge som en kortstokk. Bla, søk og kryss av fuglene du har sett.">
<meta name="theme-color" content="#0f4a36">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Fuglekort">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
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
(ROOT / "docs" / "index.html").write_text(head + body + tail, encoding="utf-8")

# Service worker precache list follows the card data, so new cards are cached automatically
assets = ["./", "index.html", "manifest.webmanifest", "sprites/photos.webp", "sprites/cards.webp", "sprites/titler.webp",
          "icons/icon-192.png", "icons/icon-512.png", "icons/icon-512-maskable.png", "icons/apple-touch-icon.png"]
assets += [data.get("bakside", "cards/bakside.webp")] + [h["bilde"] for h in data.get("hjelp", [])] + [c["bilde"] for c in data["kort"]]
# alle bildesettene lagres på telefonen, så man kan bytte i innstillingene også uten nett
if data.get("hjelpFoto"):
    assets += ["sprites/cards-foto.webp", "sprites/photos-foto.webp"]
    assets += [h["bilde"] for h in data["hjelpFoto"] if h["bilde"] not in assets]
    assets += [c["bildeFoto"] for c in data["kort"] if c.get("bildeFoto")]
if data.get("tegneserie"):
    assets += ["sprites/cards-tegneserie.webp", "sprites/photos-tegneserie.webp"]
    assets += [c["bildeTegneserie"] for c in data["kort"] if c.get("bildeTegneserie")]
# de store fuglebildene til fullskjermvisningen (alle tre bildesettene) lastes ned sammen med appen
if data.get("storeBilder"):
    for c in data["kort"]:
        assets.append(f"pictures/{c['id']}.webp")
        if c.get("bildeFoto"):
            assets.append(f"pictures-foto/{c['id']}.webp")
        if c.get("bildeTegneserie"):
            assets.append(f"pictures-tegneserie/{c['id']}.webp")
# The cache name follows the content, so phones fetch new cards automatically after every change
import hashlib
h = hashlib.sha1((ROOT / "docs" / "index.html").read_bytes())
for f in assets:
    fp = ROOT / "docs" / f
    if fp.is_file():
        h.update(fp.read_bytes())
sw = (ROOT / "src" / "sw.template.js").read_text(encoding="utf-8").replace("__ASSETS__", json.dumps(assets, indent=2))
sw = re.sub(r"const CACHE = '[^']*';", f"const CACHE = 'fuglekort-{h.hexdigest()[:10]}';", sw)
(ROOT / "docs" / "sw.js").write_text(sw, encoding="utf-8")

print(f"Bygget {len(data['kort'])} kort → docs/index.html og artifact.html")
