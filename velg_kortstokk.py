#!/usr/bin/env python3
"""Velger fuglene i kortstokken til Hagefugler: fuglene som er registrert i hager.

Bruk:
    python3 velg_kortstokk.py STI/TIL/Fuglekort-builder/data/fuglekort_data.xlsx

Regelen: arter som i snitt er sett på minst 0,1 % av fôringsplassene i Hagefugltellingen 2024, 2025 og 2026
(arket «Sjeldenhetsvurdering» i regnearket til Fuglekort-builder, som bare leses). Det gir 60 av de 100 fuglekortene.
Resultatet skrives til data/kortstokk.json. build.py tar bare med disse i kortstokken; de andre fuglekortene merkes
«ute» (se README, «Kortstokken»). Dyrekortene er ikke med i regelen og er med som før.
"""
import json, sys
from pathlib import Path
import openpyxl

ROT = Path(__file__).resolve().parent
GRENSE = 0.001            # andel av fôringsplassene (0,1 %), snitt av de tre årene


def main(xlsx):
    kort = {c["id"]: c for c in json.loads((ROT / "data" / "cards.json").read_text(encoding="utf-8"))["kort"] if not c.get("bonus")}
    ark = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)["Sjeldenhetsvurdering"]
    rader = list(ark.iter_rows(values_only=True))
    hode = list(rader[3])
    i_nr, i_art = hode.index("Kortnr"), hode.index("Art")
    i_aar = [hode.index(f"Hagefugltellingen {a}") for a in (2024, 2025, 2026)]
    inne, ute = [], []
    for r in rader[4:]:
        if not r[i_nr]:
            continue
        kid = str(r[i_nr])[:3]
        c = kort.get(kid)
        if not c:
            sys.exit(f"fant ikke kort {kid} ({r[i_art]}) i data/cards.json")
        andel = sum(float(r[i] or 0) for i in i_aar) / len(i_aar)
        (inne if andel >= GRENSE else ute).append({"id": kid, "key": c["key"], "navn": c["navn"], "andel": round(andel, 5)})
    ut = {
        "tittel": "Hagefugler",
        "regel": "Fugler som i snitt er sett på minst 0,1 % av fôringsplassene i Hagefugltellingen 2024–2026 "
                 "(BirdLife Norge/Fuglevennen), fra arket Sjeldenhetsvurdering i Fuglekort-builder.",
        "antall": len(inne),
        "arter": inne,
        "ute": ute,
    }
    (ROT / "data" / "kortstokk.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(inne)} fugler i kortstokken, {len(ute)} ute → data/kortstokk.json")
    print("  ute:", ", ".join(f"{x['id']} {x['navn']}" for x in ute))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
