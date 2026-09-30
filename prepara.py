"""
Tyche · prepara i file dei luoghi di Overture per l'app — formato v3, il MONDO
------------------------------------------------------------------------------
Vedi `src/lib/overture.ts` e `README.md` per il perché. Per UNA regione di
`regioni.json` alla volta (il lavoro mensile le fa in parallelo, e un guasto in
Asia non ferma l'Europa):
  1. l'ultima edizione di Overture (catalogo STAC), o quella data;
  2. legge da S3 SOLO i posti del riquadro della regione; dentro DuckDB li
     traduce nei tag OSM (`mappa.py`) e nelle FAMIGLIE (`gruppi.json`),
     scartando i chiusi e i poco sicuri, e li riceve ordinati per famiglia e
     zona — una zona alla volta, memoria bassa anche per venti milioni di posti;
  3. scrive le zone in una cartella di appoggio, contando i file di ognuna;
  4. riempie gli SCAFFALI (`<regione>-1`, `-2`, …: un sito Cloudflare Pages
     ciascuno, sotto i 20.000 file) in ordine di zona, e scrive in
     `regione-<id>.json` quali zone stanno in quale scaffale — `radice.py` li
     riunisce nella mappa che l'app legge;
  5. CONTROLLA che il risultato sia sano (minimi e città campione): se non lo
     è esce con errore e NON si pubblica niente per quella regione.

PERCHÉ LE FAMIGLIE E GLI SCAFFALI (29 set 2026): con un file per tag e per zona
il solo riquadro dell'Italia faceva 17.069 file — il mondo ne avrebbe fatti
centinaia di migliaia, e Cloudflare Pages ne accetta 20.000 per sito. Con 17
famiglie i file sono una frazione, e gli scaffali crescono da soli.

FORMATO v3 di una zona (senza perdite — owner: «se abbrevi gli indirizzi e i
contatti come fai a completarli?»):
  { v: 3, r: edizione, o: [lat·1e5, lng·1e5],  ← l'angolo della zona
    t: ["amenity=pharmacy", …],                ← i tag del file
    c: ["Catania", …],                         ← le città, UNA volta per file
    p: [[nome, dlat, dlng, tel, via, città, [tag]], …] }
  Il telefono è intero (solo senza spazi); l'indirizzo si ricompone identico.

Uso:  python prepara.py --regione eu [--release 2026-09-23.1] [--out out]
      python prepara.py --regione eu --da-file italia.parquet     (prove locali)
"""
from __future__ import annotations

import argparse, json, math, os, re, shutil, sys, time, urllib.request
from collections import defaultdict
from functools import lru_cache

import phonenumbers

QUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, QUI)
from mappa import TAX_A_OSM, BASIC_A_OSM, R  # noqa: E402

REG = json.load(open(os.path.join(QUI, "regioni.json")))
GRU = json.load(open(os.path.join(QUI, "gruppi.json")))
GRIGLIA = REG["griglia"]      # lo stesso file lo legge l'app
MAX_PER_FILE = 800            # oltre, la zona si divide in quattro
PROFONDITA_MAX = 10
FIDUCIA_MIN = 0.40            # sotto, Overture stesso non è sicuro che il posto esista
FILE_PER_SCAFFALE = 19000     # Cloudflare Pages ne accetta 20.000 per sito
AMMUCCHIATI_MIN = 8           # posti diversi sullo STESSO punto: da qui si guarda se il punto è vero (vedi leggi)
# LA REVISIONE DEI NOSTRI FILE (30 set 2026). I file hanno l'edizione di Overture nel
# percorso, e i telefoni li tengono PER SEMPRE: un indirizzo non cambia mai contenuto.
# Ma se ripubblichiamo la STESSA edizione con una correzione nostra (telefoni in
# +39…, punti di ripiego tolti, categorie nuove…) l'indirizzo resterebbe uguale e i
# telefoni continuerebbero a leggere la versione vecchia. Perciò il percorso porta anche
# questo numero: SI ALZA a ogni modifica che cambia il contenuto dei file.
#   1 = primo mondo (29 set) · 2 = telefoni +39, zone negative, ripiego, pesi negli indici,
#   categorie nuove (dialisi, cambio valuta, stadi, monumenti, spiagge, ripetizioni…)
REVISIONE = 2
# i MINIMI per regione: circa il 40% di quanti posti c'erano nell'edizione 2026-09-23.1 (misurati
# su tutto il mondo: eu 16,6 M · na 13,8 M · as 10,3 M · sa 4,9 M · af 1,4 M · oc 0,9 M). Sotto,
# l'edizione è a metà o il formato è cambiato: non si pubblica.
MIN_POSTI = {"eu": 6_000_000, "na": 5_000_000, "sa": 1_800_000, "af": 500_000, "oc": 350_000, "as": 4_000_000}


def gruppo_di(tag: str) -> str:
    return GRU["per_tag"].get(tag) or GRU["per_chiave"].get(tag.split("=")[0]) or GRU["altro"]


def ultima_release() -> str:
    with urllib.request.urlopen("https://stac.overturemaps.org/catalog.json", timeout=60) as r:
        cat = json.load(r)
    if not cat.get("latest"):
        sys.exit("catalogo STAC senza «latest»: controllare https://stac.overturemaps.org/catalog.json")
    return cat["latest"]


def regione_di_zona(i: int, j: int) -> str | None:
    lat, lng = (i + 0.5) * GRIGLIA, (j + 0.5) * GRIGLIA
    for r in REG["regioni"]:
        if r["s"] <= lat < r["n"] and r["o"] <= lng < r["e"]:
            return r["id"]
    return None


@lru_cache(maxsize=1_000_000)
def telefono(t, nazione):
    """Il numero nella forma internazionale completa (+39095201101), quella che il
    telefono compone giusta da qualunque paese. In Overture (Italia, set 2026) solo
    metà dei numeri l'aveva: un quarto era «39095201101» — senza «+», toccato dal
    telefono compone un numero locale sbagliato — e un quarto locale («095…»,
    «333…»), che non funziona da una SIM estera. Si legge col paese del posto; se
    così non è un numero valido si riprova col «+» davanti («39…» era già il
    prefisso) — ma solo se porta nello stesso paese. Senza paese non si indovina
    (con un «+» davanti «095537435» sarebbe del Myanmar). Se nessuna lettura è
    valida resta com'era: meglio un numero da controllare che nessun numero."""
    t = (t or "").strip()
    if not t:
        return ""
    cifre = re.sub(r"\D", "", t)
    prove = [(t, nazione)] if (nazione or t.startswith("+")) else []
    if nazione and not t.startswith("+"):
        # se comincia col prefisso del paese, quella è la lettura da provare PRIMA:
        # «3905020002» di un posto di Pisa è valido anche come cellulare 390…, ma è
        # il fisso +39 050 20002 (misurato su un campione: tutti fissi, Pisa, Milano,
        # Torino, Pescara…)
        piu = ("+" + cifre, None)
        prefisso = str(phonenumbers.country_code_for_region(nazione) or "")
        prove.insert(0 if prefisso and cifre.startswith(prefisso) else 1, piu)
        if nazione == "IT" and cifre.startswith("39"):
            # l'Italia è l'unico paese che TIENE lo 0 del prefisso di zona anche col +39:
            # molti numeri arrivano «39 583 981165» invece di +39 0583 981165. Ultimo
            # tentativo, e solo qui (su un campione: 30 su 30 col prefisso della città
            # giusta — Capannori 0583, Jesolo 0421, Gela 0933, Lipari 090…)
            prove.append(("+390" + cifre[2:], None))
    for prova, paese in prove:
        try:
            n = phonenumbers.parse(prova, paese)
        except phonenumbers.NumberParseException:
            continue
        # il «+» aggiunto vale solo se porta nello STESSO paese del posto: «17865491032»
        # di un posto italiano non diventa un numero di Miami
        if phonenumbers.is_valid_number(n) and (paese or t.startswith("+") or phonenumbers.region_code_for_number(n) == nazione):
            return phonenumbers.format_number(n, phonenumbers.PhoneNumberFormat.E164)
    return ("+" if t.startswith("+") else "") + cifre


def leggi(con, regione: dict, release: str, da_file: str | None):
    """Righe (gruppo, i, j, nome, lat, lng, tel, via, paese, nazione, tag), ordinate: lo
    stesso posto con più tag della stessa famiglia arriva in righe vicine."""
    tutti_i_tag = {t for v in list(TAX_A_OSM.values()) + list(BASIC_A_OSM.values()) for t in v} | {R}
    con.execute("CREATE OR REPLACE TABLE mappa(tax VARCHAR, tag VARCHAR)")
    con.executemany("INSERT INTO mappa VALUES (?, ?)", [(t, tag) for t, tags in TAX_A_OSM.items() for tag in tags])
    con.execute("CREATE OR REPLACE TABLE mappa_bc(bc VARCHAR, tag VARCHAR)")
    con.executemany("INSERT INTO mappa_bc VALUES (?, ?)", [(b, tag) for b, tags in BASIC_A_OSM.items() for tag in tags])
    con.execute("CREATE OR REPLACE TABLE gruppi(tag VARCHAR, gruppo VARCHAR)")
    con.executemany("INSERT INTO gruppi VALUES (?, ?)", [(t, gruppo_di(t)) for t in tutti_i_tag])
    o, s, e, n = regione["o"], regione["s"], regione["e"], regione["n"]
    if da_file:
        sorgente = f"(SELECT nome, tax, bc, conf, stato, tel, via, paese, NULL::VARCHAR AS nazione, lat, lng FROM read_parquet('{da_file}'))"
    else:
        sorgente = f"""(SELECT names.primary AS nome, taxonomy.primary AS tax, basic_category AS bc, confidence AS conf,
                  operating_status AS stato, phones[1] AS tel, addresses[1].freeform AS via, addresses[1].locality AS paese,
                  addresses[1].country AS nazione, ST_Y(geometry) AS lat, ST_X(geometry) AS lng
           FROM read_parquet('s3://overturemaps-us-west-2/release/{release}/theme=places/type=place/*', hive_partitioning=1)
           WHERE bbox.xmin BETWEEN {o} AND {e} AND bbox.ymin BETWEEN {s} AND {n})"""
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE base AS
        SELECT * FROM {sorgente} p
        WHERE p.nome IS NOT NULL AND trim(p.nome) <> ''
          AND p.conf >= {FIDUCIA_MIN} AND coalesce(p.stato, 'open') <> 'permanently_closed'
    """)
    # I PUNTI DI RIPIEGO (29 set 2026). Quando Overture sa solo la città o il CAP, mette il
    # posto nel punto centrale: a Città del Messico, sul centro, ristoranti di Tolcayuca
    # (Hidalgo); a Catania 135 posti diversi sullo stesso punto; ad Arezzo 216 con
    # indirizzo «AREZZO 57». Nell'app sarebbero «a 0 m» da chi sta in centro. Un punto
    # con tanti posti è VERO se quasi tutti hanno la stessa via (un palazzo di uffici,
    # una galleria: Via Morimondo 26 a Milano, 113 posti); è di ripiego se le vie sono
    # diverse o sono solo il nome della città. I posti dei punti di ripiego non si
    # scrivono: accanto c'è OSM, e un posto nel posto sbagliato è peggio di nessuno.
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE ripiego AS
        WITH s AS (
            SELECT lat, lng, trim(nome) AS nome,
                   nullif(regexp_replace(lower(coalesce(via, '')), '[^\\p{{L}}]', '', 'g'), '') AS st,
                   nullif(regexp_replace(lower(coalesce(paese, '')), '[^\\p{{L}}]', '', 'g'), '') AS pa
            FROM base),
        per_via AS (
            SELECT lat, lng, CASE WHEN st IS NULL OR st = pa THEN NULL ELSE st END AS st, count(DISTINCT nome) AS k
            FROM s GROUP BY ALL),
        punti AS (
            SELECT lat, lng, sum(k) AS tot, coalesce(max(k) FILTER (WHERE st IS NOT NULL), 0) AS top
            FROM per_via GROUP BY lat, lng)
        SELECT lat, lng, tot FROM punti WHERE tot >= {AMMUCCHIATI_MIN} AND top < tot * 0.5
    """)
    con.execute(f"""
        CREATE OR REPLACE TEMP VIEW posti AS
        SELECT g.gruppo, floor(p.lat / {GRIGLIA})::INT AS i, floor(p.lng / {GRIGLIA})::INT AS j,
               trim(p.nome) AS nome, p.lat, p.lng, p.tel, p.via, p.paese, p.nazione, t.tag
        FROM base p
        CROSS JOIN LATERAL (
            SELECT m.tag FROM mappa m WHERE m.tax = p.tax
            UNION ALL SELECT '{R}' WHERE p.tax LIKE '%\\_restaurant' ESCAPE '\\' AND NOT EXISTS (SELECT 1 FROM mappa m2 WHERE m2.tax = p.tax)
            UNION ALL SELECT b.tag FROM mappa_bc b WHERE p.tax IS NULL AND b.bc = p.bc
        ) t
        JOIN gruppi g ON g.tag = t.tag
        WHERE NOT EXISTS (SELECT 1 FROM ripiego r WHERE r.lat = p.lat AND r.lng = p.lng)
    """)
    punti, tolti = con.execute("SELECT count(*), coalesce(sum(tot), 0) FROM ripiego").fetchone()
    print(f"[{regione['id']}] punti di ripiego: {punti} ({tolti} posti senza la posizione vera, non scritti)")
    return con.execute("SELECT * FROM posti ORDER BY gruppo, i, j, nome, lat, lng")


NOME_ZONA = re.compile(r"^(-?\d+)_(-?\d+)((?:-[0-3])*)$")


def confini(nome):
    """A sud dell'equatore e a ovest di Greenwich i numeri sono negativi
    («-12_-24-1»): il trattino del segno non è quello dei quadranti."""
    m = NOME_ZONA.match(nome)
    i, j = int(m[1]), int(m[2])
    quadri = [q for q in m[3].split("-") if q]
    s, o, lato = i * GRIGLIA, j * GRIGLIA, GRIGLIA
    for q in map(int, quadri):
        lato /= 2
        if q in (1, 3): o += lato
        if q in (2, 3): s += lato
    return s, o, lato


def quadrante(nome, lat, lng):
    s, o, lato = confini(nome)
    meta = lato / 2
    return (1 if lng >= o + meta else 0) + (2 if lat >= s + meta else 0)


tag_per_foglia: dict[tuple[str, str], list[str]] = {}  # (cartella della famiglia, foglia) → i suoi tag


def scrivi_zona(cartella, nome, posti, release, profondita, foglie):
    """posti: [nome, lat, lng, tel, via, paese, set(tag)]"""
    if len(posti) > MAX_PER_FILE and profondita < PROFONDITA_MAX:
        figli = defaultdict(list)
        for p in posti:
            figli[quadrante(nome, p[1], p[2])].append(p)
        for q, sotto in figli.items():
            scrivi_zona(cartella, f"{nome}-{q}", sotto, release, profondita + 1, foglie)
        return
    s, o, _ = confini(nome)
    o5 = [round(s * 1e5), round(o * 1e5)]
    tag = sorted({t for p in posti for t in p[6]})
    tag_per_foglia[(cartella, nome)] = tag
    ti = {t: k for k, t in enumerate(tag)}
    citta, ci, righe = [], {}, []
    for nome_p, lat, lng, tel, via, paese, tags in posti:
        paese, via = (paese or "").strip(), (via or "").strip()
        if paese and paese.lower() in via.lower():
            paese = ""  # già dentro l'indirizzo: non si ripete
        c = -1
        if paese:
            if paese not in ci:
                ci[paese] = len(citta)
                citta.append(paese)
            c = ci[paese]
        # 300: solo contro la spazzatura (testi con link e numeri dentro); i nomi veri lunghi
        # («Noleggio BICICLETTE … Aeroporto di Lampedusa») restano interi
        righe.append([nome_p[:300], round(lat * 1e5) - o5[0], round(lng * 1e5) - o5[1], tel, via[:300], c, sorted(ti[t] for t in tags)])
    with open(os.path.join(cartella, f"{nome}.json"), "w") as f:
        json.dump({"v": 3, "r": release, "o": o5, "t": tag, "c": citta, "p": righe}, f, ensure_ascii=False, separators=(",", ":"))
    foglie.append(nome)


def distanza(a, b, c, d):
    p = math.radians
    x = math.sin(p(c - a) / 2) ** 2 + math.cos(p(a)) * math.cos(p(c)) * math.sin(p(d - b) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regione", required=True, choices=[r["id"] for r in REG["regioni"]])
    ap.add_argument("--release")
    ap.add_argument("--da-file")
    ap.add_argument("--nazione", help="paese (IT, FR…) per i numeri dei posti senza paese: serve solo con --da-file")
    ap.add_argument("--out", default=os.path.join(QUI, "out"))
    a = ap.parse_args()
    reg = next(r for r in REG["regioni"] if r["id"] == a.regione)
    release = a.release or ("locale" if a.da_file else ultima_release())
    if not a.da_file:
        release = f"{release}-r{REVISIONE}"  # per il percorso e per la mappa; S3 si legge con l'edizione nuda
    import duckdb
    con = duckdb.connect()
    con.execute("SET enable_progress_bar=false; INSTALL spatial; LOAD spatial; SET threads=8;")
    if not a.da_file:
        con.execute("INSTALL httpfs; LOAD httpfs; SET s3_region='us-west-2'; SET http_timeout=120; SET http_retries=8;")
    t0 = time.time()
    appoggio = os.path.join(a.out, f"_appoggio-{a.regione}")
    shutil.rmtree(appoggio, ignore_errors=True)
    cur = leggi(con, reg, release.split("-r")[0], a.da_file)

    campioni = REG["campioni"].get(a.regione, [])
    farmacie = defaultdict(int)
    n_posti, con_tel = 0, 0
    file_per_zona = defaultdict(int)          # (i, j) → quanti file
    foglie_per = defaultdict(list)            # (gruppo, i, j) → nomi delle foglie
    stato = {"g": None, "z": None, "buf": {}}

    def chiudi_zona():
        g, z, buf = stato["g"], stato["z"], stato["buf"]
        if g is None or z is None or not buf:
            return
        cart = os.path.join(appoggio, g)
        os.makedirs(cart, exist_ok=True)
        foglie = []
        scrivi_zona(cart, f"{z[0]}_{z[1]}", list(buf.values()), release, 0, foglie)
        foglie_per[(g, z[0], z[1])] = foglie
        file_per_zona[z] += len(foglie)

    while True:
        blocco = cur.fetchmany(50_000)
        if not blocco:
            break
        for g, i, j, nome, lat, lng, tel, via, paese, nazione, tag in blocco:
            if regione_di_zona(i, j) != a.regione:
                continue  # il centro della zona sta in un'altra regione: la scrive lei
            if (g, (i, j)) != (stato["g"], stato["z"]):
                chiudi_zona()
                stato.update(g=g, z=(i, j), buf={})
            chiave = (nome, round(lat, 5), round(lng, 5))
            p = stato["buf"].get(chiave)
            if p is None:
                tel = telefono(tel, nazione or a.nazione)
                p = stato["buf"][chiave] = [nome, lat, lng, tel, via, paese, set()]
                n_posti += 1
                if tel:
                    con_tel += 1
            p[6].add(tag)
            if tag == "amenity=pharmacy":
                for nome_c, clat, clng, _m in campioni:
                    if abs(lat - clat) < 0.05 and abs(lng - clng) < 0.07 and distanza(clat, clng, lat, lng) <= 3000:
                        farmacie[nome_c] += 1
    chiudi_zona()

    # GLI SCAFFALI: zone in ordine, ciascuno fino a FILE_PER_SCAFFALE (tenendo posto agli indici)
    gruppi = sorted({g for g, _i, _j in foglie_per})
    scaffali, corrente, pieni = [], None, 0
    for z in sorted(file_per_zona):
        if corrente is None or pieni + file_per_zona[z] > FILE_PER_SCAFFALE - len(gruppi) - 5:
            corrente = {"id": f"{a.regione}-{len(scaffali) + 1}", "da": list(z), "a": list(z), "zone": []}
            scaffali.append(corrente)
            pieni = 0
        corrente["zone"].append(z)
        corrente["a"] = list(z)
        pieni += file_per_zona[z]
    n_file = 0
    for sc in scaffali:
        base = os.path.join(a.out, sc["id"])
        shutil.rmtree(base, ignore_errors=True)
        radice = os.path.join(base, "v3", release)
        zone = set(sc["zone"])
        for g in gruppi:
            foglie = []
            for (gg, i, j), ff in foglie_per.items():
                if gg == g and (i, j) in zone:
                    foglie += ff
            if not foglie:
                continue
            cart = os.path.join(radice, g)
            os.makedirs(cart, exist_ok=True)
            for f in foglie:
                os.replace(os.path.join(appoggio, g, f"{f}.json"), os.path.join(cart, f"{f}.json"))
            foglie = sorted(foglie)
            # I MESTIERI RARI: per ognuno, in quali file sta. «coreano» fuori città
            # scaricava tutti i ristoranti di 25 km per trovarne due; così solo i
            # file che ne hanno uno. I tag diffusi (in più di metà dei file) non
            # servono: si prendono tutti comunque.
            dove = defaultdict(list)
            for k, f in enumerate(foglie):
                for t in tag_per_foglia.get((os.path.join(appoggio, g), f), []):
                    dove[t].append(k)
            rari = {t: ks for t, ks in dove.items() if len(ks) <= len(foglie) * 0.9}
            # «b»: il peso di ogni file, nello stesso ordine di «z». Serve ai «Luoghi offline»
            # dell'app: prima di scaricare una città dice quanti MB sono (owner, 29 set 2026)
            pesi = [os.path.getsize(os.path.join(cart, f"{f}.json")) for f in foglie]
            with open(os.path.join(cart, "indice.json"), "w") as fh:
                json.dump({"v": 3, "r": release, "z": foglie, "k": rari, "b": pesi}, fh, separators=(",", ":"))
            n_file += len(foglie) + 1
        with open(os.path.join(base, "404.html"), "w") as fh:
            fh.write("not found")
        # la licenza CDLA Permissive 2.0 (art. 2.1): chi condivide i dati ne mette accanto il testo
        shutil.copy(os.path.join(QUI, "LICENZA-DATI.txt"), os.path.join(base, "LICENZA-DATI.txt"))
        with open(os.path.join(base, "_headers"), "w") as fh:
            # il percorso ha l'edizione dentro: lo stesso indirizzo non cambia mai → il telefono lo tiene
            fh.write("/v3/*\n  Cache-Control: public, max-age=31536000, immutable\n  Access-Control-Allow-Origin: *\n")
        sc["file"] = sum(file_per_zona[z] for z in sc["zone"])
        del sc["zone"]
    shutil.rmtree(appoggio, ignore_errors=True)
    print(f"[{a.regione}] edizione {release} · {n_posti} posti · {n_file} file in {len(scaffali)} scaffali · telefono {con_tel / max(1, n_posti):.0%} · {time.time() - t0:.0f}s")

    problemi = []
    if not a.da_file and n_posti < MIN_POSTI[a.regione]:
        problemi.append(f"solo {n_posti} posti (minimo {MIN_POSTI[a.regione]})")
    if n_posti and con_tel / n_posti < 0.4:
        problemi.append(f"telefono solo nel {con_tel / n_posti:.0%}")
    for nome_c, _lat, _lng, minimo in ([] if a.da_file else campioni):
        if farmacie[nome_c] < minimo:
            problemi.append(f"{nome_c}: {farmacie[nome_c]} farmacie entro 3 km (minimo {minimo})")
    if problemi:
        print(f"[{a.regione}] CONTROLLI NON SUPERATI — non si pubblica niente:\n  " + "\n  ".join(problemi))
        sys.exit(2)
    with open(os.path.join(a.out, f"regione-{a.regione}.json"), "w") as fh:
        json.dump({"v": 3, "regione": a.regione, "r": release, "posti": n_posti, "scaffali": scaffali}, fh, indent=1)


if __name__ == "__main__":
    main()
