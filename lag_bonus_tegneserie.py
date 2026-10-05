#!/usr/bin/env python3
"""Lager bonuskortene i tegneseriestil (valget «Tegneseriefugler» i appen) med kortmalen i Fuglekort-builder.

Bruk:
    python3 lag_bonus_tegneserie.py STI/TIL/Fuglekort-builder
    python3 importer_fuglekort.py STI/TIL/app        (tar dem med inn i appen)

Fuglekort-builder endres ikke. Skriptet bygger i en midlertidig kopi der tegneseriebildene i kilder/bonus_tegneserie/
(b01_ekorn.jpg … b05_rodrev.jpg, stående 533 × 631 som bildefeltet på kortet) står i stedet for KI-bildene
til bonuskortene, og kjører «bygg.py --bonus bare». Kortene havner i kilder/bonus_tegneserie/kort/ og de
stående bildene (fullskjerm og miniatyrer) i kilder/bonus_tegneserie/bilder/. Teksten på kortene kommer fra
regnearket i Fuglekort-builder, så kjør skriptet på nytt hvis bonuskortene endres der.
"""
import shutil, subprocess, sys, tempfile
from pathlib import Path

ROT = Path(__file__).resolve().parent
KILDE = ROT / "kilder" / "bonus_tegneserie"


def main(fuglekort):
    bilder = sorted(KILDE.glob("b[0-9][0-9]_*.jpg"))
    if not bilder:
        sys.exit(f"Fant ingen tegneseriebilder (b01_ekorn.jpg …) i {KILDE}")
    with tempfile.TemporaryDirectory() as tmp:
        kopi = Path(tmp) / "Fuglekort"
        shutil.copytree(fuglekort, kopi, ignore=shutil.ignore_patterns(".git", "ut", "__pycache__"))
        for b in bilder:
            maal = kopi / "bilder" / b.name
            if not maal.exists():
                sys.exit(f"Fuglekort-builder har ikke {b.name} i bilder/ (KI-bildet til bonuskortet med samme navn).")
            shutil.copy(b, maal)
        subprocess.run([sys.executable, "bygg.py", "--bonus", "bare", "--uten-pdf"], cwd=kopi, check=True)
        app = kopi / "ut" / "app" / "bonus"
        for mappe in ("kort", "bilder"):
            (KILDE / mappe).mkdir(exist_ok=True)
            for f in (KILDE / mappe).glob("*.webp"):
                f.unlink()
            for b in bilder:
                nr = b.name[:3]
                shutil.copy(app / mappe / f"{nr}.webp", KILDE / mappe / f"{nr}.webp")
    print(f"Laget {len(bilder)} bonuskort i tegneseriestil i {KILDE.relative_to(ROT)}/kort/. "
          "Kjør importer_fuglekort.py for å ta dem med i appen.")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not (Path(sys.argv[1]) / "bygg.py").exists():
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve())
