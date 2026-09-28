#!/usr/bin/env python3
"""Henter inn kortene fra Fuglekort-fabrikken (repoet Fuglekort-).

Bruk:
    python3 importer_fuglekort.py STI/TIL/app

der STI/TIL/app er mappen `ut/app` fra `python bygg.py` i Fuglekort-, eller den utpakkede
«app»-nedlastingen fra Actions → Bygg fuglekort. Mappen skal ha kort.json, kort/, bilder/ og bakside.webp.

Skriptet
  1. kopierer kortbildene (001–NNN), de to forklaringskortene (000a, 000b) og baksiden til docs/cards/
  2. finner SETT-ruta og datolinja på kortene, så avkrysningen havner riktig
  3. lager data/cards.json (navn, sjeldenhet og korttekst til søket)
  4. lager miniatyrene i docs/sprites/ og app-ikonene i docs/icons/ (fra baksiden)
  5. kjører build.py
"""
import json, shutil, statistics, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROT = Path(__file__).resolve().parent
DOCS = ROT / "docs"
W, H = 750, 1050


def finn_sett(fil):
    """SETT-ruta (mørkegrønn ramme) og streken etter «Dato:», som andeler av kortet."""
    a = np.asarray(Image.open(fil).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gronn = (g > r + 25) & (g > b) & (r < 90) & (g < 140)
    ys, xs = np.nonzero(gronn[895:988, 35:135])
    boks = [xs.min() + 35, ys.min() + 895, xs.max() + 35, ys.max() + 895]
    mork = a.sum(axis=2) < 560
    del2 = mork[930:995, 395:710]
    rad = int(np.argmax(del2.sum(axis=1)))
    xs2 = np.nonzero(del2[rad])[0]
    linje = [xs2.min() + 395, rad + 930, xs2.max() + 395]
    return boks, linje


def ikon(bakside, storrelse, maskable=False):
    """Kvadratisk utsnitt av baksiden rundt fuglen. Maskable-varianten får luft rundt (Android-sikker sone)."""
    im = Image.open(bakside).convert("RGBA")
    bak = Image.new("RGBA", im.size, im.getpixel((W // 2, 8))[:3] + (255,))
    bak.alpha_composite(im)
    side = H - 335                      # under ordet «Hagefugler», ned til bunnen
    kvadrat = bak.crop((18, 335, 18 + side, 335 + side)).convert("RGB")
    if maskable:
        flate = Image.new("RGB", (side, side), im.getpixel((W // 2, 8))[:3])
        liten = kvadrat.resize((int(side * 0.8), int(side * 0.8)), Image.LANCZOS)
        flate.paste(liten, ((side - liten.width) // 2, (side - liten.height) // 2))
        kvadrat = flate
    return kvadrat.resize((storrelse, storrelse), Image.LANCZOS)


def main(app):
    kilde = json.loads((app / "kort.json").read_text(encoding="utf-8"))
    kort_inn = kilde["kort"]
    (DOCS / "cards").mkdir(parents=True, exist_ok=True)
    for f in (DOCS / "cards").glob("*.webp"):
        f.unlink()

    # 1. bilder
    for k in kort_inn:
        shutil.copy(app / k["kortbilde"], DOCS / "cards" / f"{k['nr']:03d}.webp")
    hjelp = []
    for f in kilde.get("forklaringskort", []):
        shutil.copy(app / f["kortbilde"], DOCS / "cards" / f"{f['id']}.webp")
        hjelp.append({"id": f["id"], "navn": f.get("navn") or f.get("tittel"), "bilde": f"cards/{f['id']}.webp"})
    bakside = app / (kilde.get("bakside") or "bakside.webp")
    shutil.copy(bakside, DOCS / "cards" / "bakside.webp")

    # 2. SETT-ruta: lik på alle kort, så bruk medianen (tåler et kort med grønt nær ruta)
    funn = [finn_sett(DOCS / "cards" / f"{k['nr']:03d}.webp") for k in kort_inn]
    med = lambda liste, i: statistics.median(x[i] for x in liste)
    bx0, by0, bx1, by1 = (med([f[0] for f in funn], i) for i in range(4))
    lx0, ly, lx1 = (med([f[1] for f in funn], i) for i in range(3))
    sett = {"boks": [round(float(bx0) / W, 4), round(float(by0) / H, 4), round(float(bx1 - bx0) / W, 4), round(float(by1 - by0) / H, 4)],
            "linje": [round(float(lx0) / W, 4), round(float(ly) / H, 4), round(float(lx1 - lx0) / W, 4)]}

    # 3. data
    kort = [{
        "nr": k["nr"], "id": f"{k['nr']:03d}", "navn": k["norsk"], "latin": k["latin"],
        "stjerner": k["stjerner"], "status": k["stjernetekst"],
        "kjennetegn": k["kjennetegn"], "nar": k["naar"], "mat": k["mat"], "fakta": k["funfact"],
        "vingespenn": k["vingespenn"], "vekt": k["vekt"], "utbredelse": k["land"],
        "rodliste": (k.get("rodliste") or {}).get("navn", ""),
        "bilde": f"cards/{k['nr']:03d}.webp", "sett": sett,
    } for k in kort_inn]
    data = {"tittel": "Hagefugler Oslo", "antall": len(kort), "bakside": "cards/bakside.webp", "hjelp": hjelp,
            "sjeldenhet": {"1": "Vanlig", "2": "Regelmessig", "3": "Uvanlig", "4": "Sjelden", "5": "Svært sjelden"},
            "kort": kort}
    (ROT / "data" / "cards.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    # 4. miniatyrer (10 kolonner) og ikoner
    kol, rader = 10, (len(kort_inn) + 9) // 10
    ark_kort = Image.new("RGBA", (kol * 150, rader * 210), (0, 0, 0, 0))
    ark_foto = Image.new("RGB", (kol * 128, rader * 128), (220, 226, 220))
    for i, k in enumerate(kort_inn):
        x, y = i % kol, i // kol
        ark_kort.paste(Image.open(app / k["kortbilde"]).convert("RGBA").resize((150, 210), Image.LANCZOS), (x * 150, y * 210))
        foto = Image.open(app / k["bilde"]).convert("RGB")
        s = min(foto.size)
        foto = foto.crop(((foto.width - s) // 2, (foto.height - s) // 2, (foto.width + s) // 2, (foto.height + s) // 2))
        ark_foto.paste(foto.resize((128, 128), Image.LANCZOS), (x * 128, y * 128))
    (DOCS / "sprites").mkdir(exist_ok=True)
    ark_kort.save(DOCS / "sprites" / "cards.webp", "WEBP", quality=76, method=4)
    ark_foto.save(DOCS / "sprites" / "photos.webp", "WEBP", quality=78, method=4)
    (DOCS / "icons").mkdir(exist_ok=True)
    ikon(bakside, 192).save(DOCS / "icons" / "icon-192.png")
    ikon(bakside, 512).save(DOCS / "icons" / "icon-512.png")
    ikon(bakside, 512, maskable=True).save(DOCS / "icons" / "icon-512-maskable.png")
    ikon(bakside, 180).save(DOCS / "icons" / "apple-touch-icon.png")

    print(f"Hentet {len(kort)} kort, {len(hjelp)} forklaringskort og baksiden fra {app}")
    print(f"SETT-rute {sett['boks']}, datolinje {sett['linje']}")
    subprocess.run([sys.executable, str(ROT / "build.py")], check=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "kort.json").exists():
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve())
