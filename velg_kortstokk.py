#!/usr/bin/env python3
"""Velger fuglene i kortstokken til Hagefugler: de som det er mest sannsynlig å se i en hage.

Bruk:
    python3 velg_kortstokk.py STI/TIL/Fuglekort-builder/data/fuglekort_data.xlsx [ANTALL]

Regelen: de ANTALL fuglene (73 hvis ikke annet er oppgitt) det er lettest å se i en hage i boligstrøk, etter samme mål
som stjernene og kortnumrene i Fuglekort-builder (arket «Sjeldenhetsvurdering», som bare leses): det høyeste av
  vinter: snittet av andelen fôringsplasser som så arten i Hagefugltellingen 2024–2026 × hagetilknytning, og
  sommer: sommeranslaget fra Artsobservasjoner × hagetilknytning² × «lander i hagen».
Kortnumrene følger det samme målet, så 73 gir kort 001–073 (skriptet sier fra hvis det ikke stemmer).
Resultatet skrives til data/kortstokk.json. build.py tar bare med disse i kortstokken; de andre fuglekortene merkes
«ute» (se README, «Kortstokken»). Dyrekortene er ikke med i regelen og er med som før.
"""
import json, sys
from pathlib import Path
import openpyxl

ROT = Path(__file__).resolve().parent


def main(xlsx, antall=73):
    kort = {c["id"]: c for c in json.loads((ROT / "data" / "cards.json").read_text(encoding="utf-8"))["kort"] if not c.get("bonus")}
    ark = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)["Sjeldenhetsvurdering"]
    rader = list(ark.iter_rows(values_only=True))
    hode = list(rader[3])
    kol = lambda navn: hode.index(navn)
    i_nr, i_art = kol("Kortnr"), kol("Art")
    i_aar = [kol(f"Hagefugltellingen {a}") for a in (2024, 2025, 2026)]
    i_sommer, i_tilkn, i_lander = kol("Sommeranslag"), kol("Hagetilknytning"), kol("Lander i hagen")
    tall = lambda x: float(x or 0)
    alle = []
    for r in rader[4:]:
        if not r[i_nr]:
            continue
        kid = str(r[i_nr])[:3]
        c = kort.get(kid)
        if not c:
            sys.exit(f"fant ikke kort {kid} ({r[i_art]}) i data/cards.json")
        t = tall(r[i_tilkn])
        vinter = sum(tall(r[i]) for i in i_aar) / len(i_aar) * t
        sommer = tall(r[i_sommer]) * t * t * tall(r[i_lander])
        alle.append({"id": kid, "key": c["key"], "navn": c["navn"], "hage": round(max(vinter, sommer), 5)})
    alle.sort(key=lambda x: (-x["hage"], x["id"]))
    inne = sorted(alle[:antall], key=lambda x: x["id"])
    ute = sorted(alle[antall:], key=lambda x: x["id"])
    ut = {
        "tittel": "Hagefugler",
        "regel": f"De {antall} fuglene det er lettest å se i en hage i boligstrøk: det høyeste av andelen fôringsplasser "
                 "i Hagefugltellingen 2024–2026 × hagetilknytning og sommeranslaget fra Artsobservasjoner × hagetilknytning² "
                 "× «lander i hagen» (arket Sjeldenhetsvurdering i Fuglekort-builder). «hage» er dette tallet.",
        "antall": len(inne),
        "arter": inne,
        "ute": ute,
    }
    (ROT / "data" / "kortstokk.json").write_text(json.dumps(ut, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    nr = [x["id"] for x in inne]
    print(f"{len(inne)} fugler i kortstokken, {len(ute)} ute → data/kortstokk.json")
    if nr != [f"{i:03d}" for i in range(1, len(inne) + 1)]:
        print("  NB: ikke de samme som kort 001–%03d:" % len(inne), ", ".join(nr))
    print(f"  sist inne: {alle[antall - 1]['id']} {alle[antall - 1]['navn']} ({alle[antall - 1]['hage'] * 100:.2f} %)"
          + (f", første ute: {alle[antall]['id']} {alle[antall]['navn']} ({alle[antall]['hage'] * 100:.2f} %)" if len(alle) > antall else ""))


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) == 3 else 73)
