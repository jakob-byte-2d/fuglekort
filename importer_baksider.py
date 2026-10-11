#!/usr/bin/env python3
"""Henter inn baksider som kan kjøpes i Frøbutikken.

Bruk:
    python3 importer_baksider.py STI/TIL/baksider.zip      (eller en mappe med PNG/JPG/WebP)

Skriptet
  1. leser bildene (filnavn som «Fuglekort_04_Botanisk_744x1039_300dpi.png»: nummer og navn tas fra navnet)
  2. hopper over bilder som er den baksiden kortstokken har fra før (docs/cards/bakside.webp), så den ikke kan kjøpes
  3. lagrer resten som docs/cards/bakside-<id>.webp i kortstørrelse (750 × 1050)
  4. skriver data/baksider.json med navn og pris (prisene står i PRISER under; en bakside som alt står i fila,
     beholder prisen sin), og kjører build.py
"""
import io, json, re, subprocess, sys, unicodedata, zipfile
from pathlib import Path
import numpy as np
from PIL import Image

ROT = Path(__file__).resolve().parent
KORT = ROT / "docs" / "cards"
JSON = ROT / "data" / "baksider.json"
W, H = 750, 1050
# relativt høye priser: de enkleste først, perlemor dyrest
PRISER = {
    "nordisk-minimal": 37000, "typografisk": 37000, "nordisk-tresnitt": 44000, "japansk-ro": 44000, "botanisk": 52000,
    "klassisk-samlekort": 58000, "klassisk-spillekort": 58000, "art-deco": 64000, "perlemor": 86000,
}
STANDARDPRIS = 52000
LIK = 50          # gjennomsnittlig fargeforskjell (0–255) under dette regnes som samme bilde som baksiden i dag


def slug(tekst):
    t = unicodedata.normalize("NFKD", tekst.lower().replace("æ", "ae").replace("ø", "o").replace("å", "a"))
    return re.sub(r"[^a-z0-9]+", "-", t.encode("ascii", "ignore").decode()).strip("-")


def navn_av(fil):
    """«Fuglekort_04_Botanisk_744x1039_300dpi.png» → (4, «Botanisk»)"""
    stamme = Path(fil).stem
    m = re.match(r"(?:Fuglekort_)?(\d+)_(.+?)(?:_\d+x\d+.*)?$", stamme)
    nr, navn = (int(m.group(1)), m.group(2)) if m else (999, stamme)
    navn = navn.replace("_", " ").strip()
    return nr, navn[:1].upper() + navn[1:]


def bilder(kilde):
    kilde = Path(kilde)
    if kilde.suffix.lower() == ".zip":
        with zipfile.ZipFile(kilde) as z:
            for n in sorted(z.namelist()):
                if n.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and not n.startswith("__MACOSX"):
                    yield n, Image.open(io.BytesIO(z.read(n))).convert("RGB")
    else:
        for f in sorted(kilde.iterdir()):
            if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                yield f.name, Image.open(f).convert("RGB")


def lik(a, b):
    sm = lambda im: np.asarray(im.resize((93, 130), Image.LANCZOS)).astype(float)
    return float(np.abs(sm(a) - sm(b)).mean())


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    standard = Image.open(KORT / "bakside.webp").convert("RGB")
    gamle = {b["id"]: b for b in json.loads(JSON.read_text(encoding="utf-8"))} if JSON.is_file() else {}
    ut = []
    for fil, im in bilder(sys.argv[1]):
        nr, navn = navn_av(fil)
        avstand = lik(im, standard)
        if avstand < LIK:
            print(f"  hopper over {fil}: samme som baksiden i dag (forskjell {avstand:.0f})")
            continue
        bid = slug(navn)
        im.resize((W, H), Image.LANCZOS).save(KORT / f"bakside-{bid}.webp", "WEBP", quality=86, method=6)
        pris = gamle.get(bid, {}).get("pris", PRISER.get(bid, STANDARDPRIS))
        ut.append({"id": bid, "navn": navn, "bilde": f"cards/bakside-{bid}.webp", "pris": pris, "nr": nr})
    ut.sort(key=lambda b: (b["pris"], b["nr"]))
    JSON.write_text(json.dumps([{k: v for k, v in b.items() if k != "nr"} for b in ut], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for b in ut:
        print(f"  {b['navn']:22} {b['pris']:>7} frø  {b['bilde']}")
    print(f"{len(ut)} baksider i {JSON.relative_to(ROT)}")
    subprocess.run([sys.executable, str(ROT / "build.py")], check=True)


if __name__ == "__main__":
    main()
