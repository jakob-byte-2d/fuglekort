#!/usr/bin/env python3
"""Henter inn kortene fra kortfabrikken (repoet Fuglekort-builder).

Bruk:
    python3 importer_fuglekort.py STI/TIL/app

der STI/TIL/app er mappen `ut/app` fra `python bygg.py` i Fuglekort-builder, eller den utpakkede
«app»-nedlastingen fra Actions → Bygg fuglekort. Mappen skal ha kort.json, kort/, bilder/ og bakside.webp
(og kort_tegneserie/ og bilder_tegneserie/ når Fuglekort-builder har tegneseriesettet).

Skriptet
  1. kopierer kortbildene (001–NNN), bonuskortene (b01–b05, andre dyr), de to forklaringskortene (000a, 000b)
     og baksiden til docs/cards/, og kortene med fotografi (også bonuskortene og bildekrediteringen deres, b00)
     til docs/cards-foto/, og kortene med tegneseriebilde til docs/cards-tegneserie/ (bonuskortene i
     tegneseriestil fra kilder/bonus_tegneserie/, laget med lag_bonus_tegneserie.py, når kort.json ikke har dem)
  2. finner SETT-ruta og datolinja på kortene, så avkrysningen havner riktig
  3. lager data/cards.json (navn, sjeldenhet og korttekst til søket)
  4. lager miniatyrene i docs/sprites/ og app-ikonene i docs/icons/ (fra baksiden)
  5. lagrer de store fuglebildene (800 × 800) til fullskjermvisningen i docs/pictures/, docs/pictures-foto/
     og docs/pictures-tegneserie/
  6. kjører build.py
"""
import json, re, shutil, statistics, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROT = Path(__file__).resolve().parent
DOCS = ROT / "docs"
BONUS_TS = ROT / "kilder" / "bonus_tegneserie"     # bonuskortene i tegneseriestil (lag_bonus_tegneserie.py)
W, H = 750, 1050


def nokkel(latin):
    """Fast nøkkel for en art, f.eks. «parus-major». Avkrysningene lagres på denne, så de følger fuglen når kortene får ny rekkefølge."""
    return re.sub(r"[^a-z]+", "-", latin.lower()).strip("-")


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
    # under ordet øverst («Fuglekort», tidligere «Hagefugler»), ned til bunnen: finn nederste mørke rad i ordet
    mork = (np.asarray(bak.convert("RGB")).astype(int).sum(2) < 250).any(1)
    topp = max(y for y in range(200, 430) if mork[y]) + 9
    side = H - topp
    x0 = (W - side) // 2
    kvadrat = bak.crop((x0, topp, x0 + side, topp + side)).convert("RGB")
    if maskable:
        flate = Image.new("RGB", (side, side), im.getpixel((W // 2, 8))[:3])
        liten = kvadrat.resize((int(side * 0.8), int(side * 0.8)), Image.LANCZOS)
        flate.paste(liten, ((side - liten.width) // 2, (side - liten.height) // 2))
        kvadrat = flate
    return kvadrat.resize((storrelse, storrelse), Image.LANCZOS)


def foto_felt(k, kid=None):
    """Kortbildet med fotografi og hvem som tok det, for kort som har fotografi (kid: «001», «b01» …)."""
    fs = k.get("fotosett") or {}
    if not fs.get("foto"):
        return {}
    return {"bildeFoto": f"cards-foto/{kid or format(k['nr'], '03d')}.webp",
            "fotograf": fs["foto"]["fotograf"], "lisens": fs["foto"]["lisens"]}


def tegneserie_felt(k):
    """Kortbildet i tegneseriestil, for fuglekort som har det (resten viser KI-kortet i det valget)."""
    return {"bildeTegneserie": f"cards-tegneserie/{k['nr']:03d}.webp"} if k.get("tegneserie") else {}


def bonus_tegneserie(app, k):
    """(kortbilde, kvadratisk bilde) for et bonuskort i tegneseriestil: fra kort.json hvis Fuglekort-builder har det,
    ellers fra kilder/bonus_tegneserie/. None når det mangler (appen viser da KI-kortet)."""
    ts = k.get("tegneserie")
    if ts:
        return app / ts["kortbilde"], app / ts["bilde"]
    kort, bilde = BONUS_TS / "kort" / f"{k['nr_tekst']}.webp", BONUS_TS / "bilder" / f"{k['nr_tekst']}.webp"
    return (kort, bilde) if kort.exists() and bilde.exists() else None


def lagre_stort(fil, maal):
    """Stort, kvadratisk fuglebilde (800 × 800) til fullskjermvisningen, litt hardere komprimert enn kilden."""
    im = Image.open(fil).convert("RGB")
    if im.size != (800, 800):
        s = min(im.size)
        im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2)).resize((800, 800), Image.LANCZOS)
    im.save(maal, "WEBP", quality=80, method=6)


def kvadrat(fil):
    """Kvadratisk utsnitt fra midten, 128 × 128, til miniatyrene i søket."""
    foto = Image.open(fil).convert("RGB")
    s = min(foto.size)
    foto = foto.crop(((foto.width - s) // 2, (foto.height - s) // 2, (foto.width + s) // 2, (foto.height + s) // 2))
    return foto.resize((128, 128), Image.LANCZOS)


def main(app):
    kilde = json.loads((app / "kort.json").read_text(encoding="utf-8"))
    kort_inn = kilde["kort"]
    bonus = kilde.get("bonus") or {}          # bonuskortene (andre dyr): legges etter fuglekortene i kortstokken
    bonus_inn = bonus.get("kort", [])
    for mappe in ("cards", "cards-foto", "cards-tegneserie"):
        (DOCS / mappe).mkdir(parents=True, exist_ok=True)
        for f in (DOCS / mappe).glob("*.webp"):
            f.unlink()
    fotosett = kilde.get("fotosett")   # kortene med fotografier (valget «Fotografier» i innstillingene)
    # tegneseriefuglene (valget «Tegneseriefugler»): bare fuglekort, og bare de som har et tegneseriebilde
    tegneserie = kilde.get("tegneserie") if any(k.get("tegneserie") for k in kort_inn) else None

    # 1. bilder
    for k in kort_inn:
        shutil.copy(app / k["kortbilde"], DOCS / "cards" / f"{k['nr']:03d}.webp")
    hjelp = []
    for f in kilde.get("forklaringskort", []):
        shutil.copy(app / f["kortbilde"], DOCS / "cards" / f"{f['id']}.webp")
        hjelp.append({"id": f["id"], "navn": f.get("navn") or f.get("tittel"), "bilde": f"cards/{f['id']}.webp"})
    # bonuskortene: KI-kortene i cards/, kortene med fotografi i cards-foto/ (som fuglene);
    # bildekrediteringen deres (b00) står sist under ? når man har valgt fotografier
    for k in bonus_inn:
        shutil.copy(app / k["kortbilde"], DOCS / "cards" / f"{k['nr_tekst']}.webp")
        fs = k.get("fotosett")
        if fs and fs.get("foto"):
            shutil.copy(app / fs["kortbilde"], DOCS / "cards-foto" / f"{k['nr_tekst']}.webp")
    hjelp_bonus, hjelp_bonus_foto = [], []
    for f in bonus.get("forklaringskort", []):                  # (eldre kort.json: b00 lå her)
        shutil.copy(app / f["kortbilde"], DOCS / "cards" / f"{f['id']}.webp")
        hjelp_bonus.append({"id": f["id"], "navn": f.get("navn") or f.get("tittel"), "bilde": f"cards/{f['id']}.webp"})
    for f in (bonus.get("fotosett") or {}).get("forklaringskort", []):
        shutil.copy(app / f["kortbilde"], DOCS / "cards-foto" / f"{f['id']}.webp")
        hjelp_bonus_foto.append({"id": f["id"], "navn": f.get("navn") or f.get("tittel"), "bilde": f"cards-foto/{f['id']}.webp"})
    bakside = app / (kilde.get("bakside") or "bakside.webp")
    shutil.copy(bakside, DOCS / "cards" / "bakside.webp")
    # fotosettet: bare kort som faktisk har fotografi kopieres; resten er like KI-kortene og gjenbrukes
    hjelp_foto = []
    if fotosett:
        for k in kort_inn:
            fs = k.get("fotosett")
            if fs and fs.get("foto"):
                shutil.copy(app / fs["kortbilde"], DOCS / "cards-foto" / f"{k['nr']:03d}.webp")
        vanlige = {h["id"]: h for h in hjelp}
        for f in fotosett.get("forklaringskort", []):
            if f["id"] in vanlige and f.get("navn") == vanlige[f["id"]]["navn"]:
                hjelp_foto.append(vanlige[f["id"]])        # samme forklaringskort som i KI-settet
            else:                                           # f.eks. kortet Bildekreditering
                shutil.copy(app / f["kortbilde"], DOCS / "cards-foto" / f"{f['id']}.webp")
                hjelp_foto.append({"id": f["id"], "navn": f.get("navn") or f.get("tittel"), "bilde": f"cards-foto/{f['id']}.webp"})

    # tegneseriesettet: samme forklaringskort som KI-settet og ingen bildekreditering
    if tegneserie:
        for k in kort_inn:
            if k.get("tegneserie"):
                shutil.copy(app / k["tegneserie"]["kortbilde"], DOCS / "cards-tegneserie" / f"{k['nr']:03d}.webp")
        for k in bonus_inn:
            b = bonus_tegneserie(app, k)
            if b:
                shutil.copy(b[0], DOCS / "cards-tegneserie" / f"{k['nr_tekst']}.webp")

    # 2. SETT-ruta: lik på alle kort, så bruk medianen (tåler et kort med grønt nær ruta)
    funn = [finn_sett(DOCS / "cards" / f"{k['nr']:03d}.webp") for k in kort_inn]
    med = lambda liste, i: statistics.median(x[i] for x in liste)
    bx0, by0, bx1, by1 = (med([f[0] for f in funn], i) for i in range(4))
    lx0, ly, lx1 = (med([f[1] for f in funn], i) for i in range(3))
    sett = {"boks": [round(float(bx0) / W, 4), round(float(by0) / H, 4), round(float(bx1 - bx0) / W, 4), round(float(by1 - by0) / H, 4)],
            "linje": [round(float(lx0) / W, 4), round(float(ly) / H, 4), round(float(lx1 - lx0) / W, 4)]}

    # 3. data
    kort = [{
        "nr": k["nr"], "id": f"{k['nr']:03d}", "key": nokkel(k["latin"]), "navn": k["norsk"], "latin": k["latin"],
        "stjerner": k["stjerner"], "status": k["stjernetekst"],
        "kjennetegn": k["kjennetegn"], "nar": k["naar"], "mat": k["mat"], "fakta": k["funfact"],
        "vingespenn": k["vingespenn"], "vekt": k["vekt"], "utbredelse": k["land"],
        "rodliste": (k.get("rodliste") or {}).get("navn", ""),
        "bilde": f"cards/{k['nr']:03d}.webp", "sett": sett,
        **foto_felt(k),
        **tegneserie_felt(k),
    } for k in kort_inn]
    # bonuskortene (andre dyr): samme felt, men «lengde» i stedet for vingespenn
    kort += [{
        "nr": k["nr"], "id": k["nr_tekst"], "bonus": True, "key": nokkel(k["latin"]), "navn": k["norsk"], "latin": k["latin"],
        "stjerner": k["stjerner"], "status": k["stjernetekst"],
        "kjennetegn": k["kjennetegn"], "nar": k["naar"], "mat": k["mat"], "fakta": k["funfact"],
        "lengde": k["lengde"], "vekt": k["vekt"], "utbredelse": k["land"],
        "rodliste": (k.get("rodliste") or {}).get("navn", ""),
        "bilde": f"cards/{k['nr_tekst']}.webp", "sett": sett,
        **foto_felt(k, k["nr_tekst"]),
        **({"bildeTegneserie": f"cards-tegneserie/{k['nr_tekst']}.webp"} if tegneserie and bonus_tegneserie(app, k) else {}),
        # eldre kort.json uten fotosett: kortet selv var fotografiet
        **({"fotograf": k["foto"]["fotograf"], "lisens": k["foto"]["lisens"]} if k.get("foto") else {}),
    } for k in bonus_inn]
    hjelp += hjelp_bonus
    hjelp_foto += hjelp_bonus + hjelp_bonus_foto
    data = {"tittel": "Fuglekort", "antall": len(kort_inn), "bonus": len(bonus_inn), "bakside": "cards/bakside.webp", "hjelp": hjelp,
            "sjeldenhet": {"1": "Vanlig", "2": "Regelmessig", "3": "Uvanlig", "4": "Sjelden", "5": "Svært sjelden"},
            "kort": kort}
    if fotosett:
        data["hjelpFoto"] = hjelp_foto
    if tegneserie:
        data["tegneserie"] = True
    assert len({k["key"] for k in kort}) == len(kort), "to kort har samme latinske navn"
    tidligere = ROT / "data" / "tidligere_nummer.json"
    if tidligere.exists():   # gamle avkrysninger lagret på kortnummer flyttes over på arten
        data["tidligereNr"] = json.loads(tidligere.read_text(encoding="utf-8"))["nummer"]
    (ROT / "data" / "cards.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    # 4. miniatyrer (10 kolonner) og ikoner – bonuskortene kommer etter fuglekortene, som i kortstokken
    kort_inn = kort_inn + bonus_inn
    kol, rader = 10, (len(kort_inn) + 9) // 10
    ark_kort = Image.new("RGBA", (kol * 150, rader * 210), (0, 0, 0, 0))
    ark_foto = Image.new("RGB", (kol * 128, rader * 128), (220, 226, 220))
    for i, k in enumerate(kort_inn):
        x, y = i % kol, i // kol
        ark_kort.paste(Image.open(app / k["kortbilde"]).convert("RGBA").resize((150, 210), Image.LANCZOS), (x * 150, y * 210))
        ark_foto.paste(kvadrat(app / k["bilde"]), (x * 128, y * 128))
    (DOCS / "sprites").mkdir(exist_ok=True)
    ark_kort.save(DOCS / "sprites" / "cards.webp", "WEBP", quality=76, method=4)
    ark_foto.save(DOCS / "sprites" / "photos.webp", "WEBP", quality=78, method=4)

    def miniatyrsett(navn, bilder):
        """Miniatyrer for et annet bildesett: KI-miniatyrene, med kortene som har eget bilde byttet ut.
        bilder(k) gir (kortbilde, bilde) som filstier for kort som har det, ellers None."""
        kort_ark, foto_ark = ark_kort.copy(), ark_foto.copy()
        for i, k in enumerate(kort_inn):
            b = bilder(k)
            if not b:
                continue
            x, y = i % kol, i // kol
            kort_ark.paste(Image.open(b[0]).convert("RGBA").resize((150, 210), Image.LANCZOS), (x * 150, y * 210))
            foto_ark.paste(kvadrat(b[1]), (x * 128, y * 128))
        kort_ark.save(DOCS / "sprites" / f"cards-{navn}.webp", "WEBP", quality=76, method=4)
        foto_ark.save(DOCS / "sprites" / f"photos-{navn}.webp", "WEBP", quality=78, method=4)

    for f in ("cards-foto.webp", "photos-foto.webp", "cards-tegneserie.webp", "photos-tegneserie.webp"):
        (DOCS / "sprites" / f).unlink(missing_ok=True)
    # fotosettet (KI-bildet der fotografi mangler)
    if fotosett:
        miniatyrsett("foto", lambda k: (app / k["fotosett"]["kortbilde"], app / k["fotosett"]["bilde"])
                     if (k.get("fotosett") or {}).get("foto") else None)
    # tegneseriesettet (KI-bildet der tegneseriebilde mangler)
    if tegneserie:
        er_bonus = lambda k: any(k is b for b in bonus_inn)
        miniatyrsett("tegneserie", lambda k: bonus_tegneserie(app, k) if er_bonus(k) else
                     (app / k["tegneserie"]["kortbilde"], app / k["tegneserie"]["bilde"]) if k.get("tegneserie") else None)
    # 5. store fuglebilder til fullskjermvisningen (trykk på bildet på kortet): ett per kort og bildesett
    for mappe in ("pictures", "pictures-foto", "pictures-tegneserie"):
        (DOCS / mappe).mkdir(exist_ok=True)
        for f in (DOCS / mappe).glob("*.webp"):
            f.unlink()
    store = {"pictures": 0, "pictures-foto": 0, "pictures-tegneserie": 0}
    for k in kort_inn:
        bonus = any(k is b for b in bonus_inn)
        kid = k["nr_tekst"] if bonus else f"{k['nr']:03d}"
        kilder = {"pictures": app / k["bilde"]}
        if (k.get("fotosett") or {}).get("foto"):
            kilder["pictures-foto"] = app / k["fotosett"]["bilde"]
        if tegneserie:
            b = bonus_tegneserie(app, k) if bonus else ((app / k["tegneserie"]["kortbilde"], app / k["tegneserie"]["bilde"]) if k.get("tegneserie") else None)
            if b:
                kilder["pictures-tegneserie"] = b[1]
        for mappe, fil in kilder.items():
            lagre_stort(fil, DOCS / mappe / f"{kid}.webp")
            store[mappe] += 1
    data["storeBilder"] = True
    (ROT / "data" / "cards.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

    (DOCS / "icons").mkdir(exist_ok=True)
    ikon(bakside, 192).save(DOCS / "icons" / "icon-192.png")
    ikon(bakside, 512).save(DOCS / "icons" / "icon-512.png")
    ikon(bakside, 512, maskable=True).save(DOCS / "icons" / "icon-512-maskable.png")
    ikon(bakside, 180).save(DOCS / "icons" / "apple-touch-icon.png")

    print(f"Hentet {len(kort) - len(bonus_inn)} fuglekort, {len(bonus_inn)} bonuskort, {len(hjelp)} forklaringskort "
          f"og baksiden fra {app}")
    if fotosett:
        print(f"Fotosett: {sum(1 for k in kort if k.get('bildeFoto'))} kort med fotografi, "
              f"{len(hjelp_foto)} forklaringskort (resten viser KI-bildet)")
    if tegneserie:
        print(f"Tegneseriesett: {sum(1 for k in kort if k.get('bildeTegneserie') and not k.get('bonus'))} fuglekort og "
              f"{sum(1 for k in kort if k.get('bildeTegneserie') and k.get('bonus'))} bonuskort med tegneseriebilde "
              f"(resten viser KI-bildet)")
    print(f"Store bilder til fullskjerm: {store['pictures']} KI, {store['pictures-foto']} foto, "
          f"{store['pictures-tegneserie']} tegneserie")
    print(f"SETT-rute {sett['boks']}, datolinje {sett['linje']}")
    subprocess.run([sys.executable, str(ROT / "build.py")], check=True)


if __name__ == "__main__":
    if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "kort.json").exists():
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve())
