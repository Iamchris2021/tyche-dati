"""
Tyche · la mappa degli scaffali (formato v3)
--------------------------------------------
Riunisce i `regione-<id>.json` scritti da `prepara.py` in `radice/v3/mappa.json`,
l'unico file che l'app legge per sapere dove sta una zona:

  { v: 3,
    s: { "eu-1": { url: "https://tyche-dati-eu-1.pages.dev/", r: "2026-09-23.1" }, … },
    regioni: { eu: [ { id: "eu-1", da: [i, j], a: [i, j] }, … ], … } }

SE UNA REGIONE QUEL MESE È FALLITA (i suoi controlli non passavano, o S3 non
rispondeva), il suo `regione-<id>.json` manca: si riprende la sua parte dalla
mappa ANCORA ONLINE, che punta agli scaffali del mese prima — ancora lì, perché
per quella regione non si è pubblicato niente. Nessuna zona resta scoperta.

Uso:  python radice.py --out out [--online https://tyche-dati.pages.dev/v3/mappa.json]
"""
from __future__ import annotations

import argparse, glob, json, os, shutil, sys, urllib.request

QUI = os.path.dirname(os.path.abspath(__file__))
REG = json.load(open(os.path.join(QUI, "regioni.json")))
URL_SCAFFALE = "https://tyche-dati-{id}.pages.dev/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(QUI, "out"))
    ap.add_argument("--online", default="https://tyche-dati.pages.dev/v3/mappa.json")
    a = ap.parse_args()
    mappa = {"v": 3, "s": {}, "regioni": {}}
    fatte = set()
    for f in sorted(glob.glob(os.path.join(a.out, "regione-*.json"))):
        d = json.load(open(f))
        fatte.add(d["regione"])
        mappa["regioni"][d["regione"]] = [{"id": sc["id"], "da": sc["da"], "a": sc["a"]} for sc in d["scaffali"]]
        for sc in d["scaffali"]:
            mappa["s"][sc["id"]] = {"url": URL_SCAFFALE.format(id=sc["id"]), "r": d["r"]}
    mancanti = [r["id"] for r in REG["regioni"] if r["id"] not in fatte]
    if mancanti:
        try:
            with urllib.request.urlopen(a.online, timeout=60) as r:
                vecchia = json.load(r)
        except Exception as e:  # prima pubblicazione, o radice irraggiungibile
            vecchia = {"s": {}, "regioni": {}}
            print(f"mappa online non leggibile ({e}): le regioni {mancanti} restano senza scaffali questo mese")
        for reg in mancanti:
            if reg in vecchia.get("regioni", {}):
                mappa["regioni"][reg] = vecchia["regioni"][reg]
                for sc in vecchia["regioni"][reg]:
                    if sc["id"] in vecchia["s"]:
                        mappa["s"][sc["id"]] = vecchia["s"][sc["id"]]
                print(f"{reg}: questo mese non è stata rifatta — resta quella del mese prima")
    if not mappa["regioni"]:
        sys.exit("nessuna regione: niente da pubblicare")
    base = os.path.join(a.out, "radice")
    os.makedirs(os.path.join(base, "v3"), exist_ok=True)
    with open(os.path.join(base, "v3", "mappa.json"), "w") as fh:
        json.dump(mappa, fh, separators=(",", ":"))
    with open(os.path.join(base, "404.html"), "w") as fh:
        fh.write("not found")
    # la licenza CDLA Permissive 2.0 (art. 2.1): chi condivide i dati ne mette accanto il testo
    shutil.copy(os.path.join(QUI, "LICENZA-DATI.txt"), os.path.join(base, "LICENZA-DATI.txt"))
    with open(os.path.join(base, "_headers"), "w") as fh:
        # la mappa cambia una volta al mese: un'ora di cache basta e avanza
        fh.write("/v3/mappa.json\n  Cache-Control: public, max-age=3600\n  Access-Control-Allow-Origin: *\n")
    print(json.dumps({r: len(v) for r, v in mappa["regioni"].items()}), "scaffali:", len(mappa["s"]))


if __name__ == "__main__":
    main()
