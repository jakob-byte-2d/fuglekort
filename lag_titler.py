#!/usr/bin/env python3
"""Lager ikonarket for titlene (Egg … Fuglekonge) til Profil og feiringen.

    python3 lag_titler.py

Leser de 13 ikonene i kilder/titler/ (01_egg.jpg … 13_fuglekonge_med_krone.jpg, kvadratiske, i rekkefølgen
til titlene) og lagrer dem side om side i docs/sprites/titler.webp, 320 × 320 px hver. Appen viser ett ikon
om gangen med background-position. Kjør build.py etterpå, så ikonarket kommer med i hurtiglageret.
"""
import sys
from pathlib import Path
from PIL import Image

ROT = Path(__file__).resolve().parent
KILDE = ROT / "kilder" / "titler"
UT = ROT / "docs" / "sprites" / "titler.webp"
ANTALL, SIDE = 13, 320

filer = sorted(f for f in KILDE.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
if len(filer) != ANTALL:
    sys.exit(f"Fant {len(filer)} ikoner i {KILDE}, ventet {ANTALL} (ett per tittel).")
ark = Image.new("RGB", (SIDE * ANTALL, SIDE), "white")
for k, f in enumerate(filer):
    im = Image.open(f).convert("RGBA")
    bak = Image.new("RGBA", im.size, (255, 255, 255, 255))   # gjennomsiktige ikoner får hvit bakgrunn
    bak.alpha_composite(im)
    s = min(bak.size)
    bak = bak.crop(((bak.width - s) // 2, (bak.height - s) // 2, (bak.width + s) // 2, (bak.height + s) // 2))
    ark.paste(bak.convert("RGB").resize((SIDE, SIDE), Image.LANCZOS), (k * SIDE, 0))
UT.parent.mkdir(parents=True, exist_ok=True)
ark.save(UT, "WEBP", quality=84, method=6)
print(f"Laget {UT.relative_to(ROT)} med {ANTALL} ikoner ({UT.stat().st_size // 1024} kB): " + ", ".join(f.stem for f in filer))
