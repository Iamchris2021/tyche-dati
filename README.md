# I luoghi di Overture per Tyche — tutto il mondo

Overture Maps (fondazione di Meta, Microsoft, Amazon, TomTom) pubblica ogni mese
i posti di tutto il mondo, con licenza aperta (CDLA Permissive 2.0). Tyche li usa
**accanto** a OpenStreetMap: OSM porta gli orari, Overture i **telefoni** e i posti
che mancano. Il perché, con i numeri, sta in `src/lib/overture.ts`.

Esempio vero (28 set 2026): seduto da **Panda**, ristorante coreano in Via Gemmellaro
27 a Catania, l'owner cerca «voglio mangiare coreano» e Tyche non lo trova.
Su OpenStreetMap Panda **non esiste**; su Overture sì, con il telefono.

## Cosa c'è qui

| File | Cosa fa |
|---|---|
| `mappa.py` | traduce le ~520 categorie di Overture nei tag di OSM che l'app cerca |
| `gruppi.json` | le 17 **famiglie** di tag (farmacia, ristoranti, casa, …): una ricerca scarica il file della famiglia, non uno per tag. Copia identica in `src/data/overture/` (un test lo controlla) |
| `regioni.json` | la griglia (zone di 2°) e i 6 continenti; copia identica in `src/data/overture/` |
| `prepara.py` | per UNA regione: legge da S3, tiene i posti sicuri e aperti, scrive zone e scaffali, **controlla** che siano sani |
| `radice.py` | riunisce le regioni nella mappa `v3/mappa.json`, l'unico file che l'app legge per sapere dove andare |
| `.github/workflows/mensile.yml` | il 26 di ogni mese: 6 regioni in parallelo, poi la radice, tutto pubblicato su Cloudflare Pages |
| `requirements.txt` | DuckDB |

## Come è fatto (formato v3)

- **Il mondo**: 69 milioni di posti (edizione 2026-09-23.1) — Europa 16,6 M,
  Nord America 13,8 M, Asia 10,3 M, Sud America 4,9 M, Africa e Medio Oriente 1,4 M,
  Oceania 0,9 M.
- **Zone**: la Terra divisa in quadrati di 2°; una zona con più di 800 posti di una
  famiglia si divide in quattro, finché serve. Ogni famiglia ha un piccolo `indice.json`
  con le foglie e i tag **rari** (una cucina coreana non fa scaricare tutti i ristoranti).
- **Scaffali**: Cloudflare Pages gratuito accetta 20.000 file per sito, quindi ogni
  regione riempie da sola i suoi scaffali (`tyche-dati-eu-1`, `-2`, …, sotto i 19.000
  file ciascuno). Circa **10 scaffali** per il mondo intero, tutti gratuiti: richieste e
  banda illimitate.
- **Senza perdite**: nome, telefono intero, via e città si ricompongono identici
  (le città sono scritte una volta per file).
- **Quanto pesa per l'utente** (misurato sull'Italia): la prima ricerca in una zona
  scarica in mediana ~37 KB compressi; ripeterla scarica **0 KB** (i file restano nel
  telefono, cifrati, fino a 200). Il raggio parte da 300 m e si allarga solo se serve.
- **Edizione nel percorso**: ogni mese i file hanno un indirizzo nuovo, quindi il
  telefono può tenerli per sempre senza mai leggere un file vecchio.

Se i controlli di una regione falliscono (edizione a metà, formato cambiato, città
campione senza farmacie, telefoni sotto il 40%) **quella regione non pubblica niente**:
resta online il mese prima, le altre vanno avanti, e GitHub manda una mail.

## I passi dell'owner (una volta sola)

1. **Cloudflare** — crea un account gratuito su cloudflare.com (nessuna carta).
2. **Autorizza il Mac** — nel Terminale, nella cartella del progetto:
   `npx wrangler login` → si apre il browser → «Allow». Da lì la prima pubblicazione
   la faccio io (crea i progetti `tyche-dati` e `tyche-dati-<regione>-<n>`; se il
   nome `tyche-dati` fosse già preso se ne sceglie un altro e si cambia
   `OVERTURE_RADICE` nell'app e `URL_SCAFFALE` in `radice.py`).
3. **GitHub** — crea un account gratuito e un progetto **pubblico** `tyche-dati`
   (i progetti pubblici hanno le macchine più grandi e i minuti gratuiti senza limite;
   qui dentro non c'è niente di segreto); ci va il contenuto di questa cartella.
   Nelle impostazioni del progetto → *Secrets and variables → Actions* aggiungi:
   - `CLOUDFLARE_API_TOKEN` — da Cloudflare: *My Profile → API Tokens → Create
     Token → Create Custom Token*, con un solo permesso: *Account · Cloudflare
     Pages · Edit* (può solo pubblicare questi file, nient'altro);
   - `CLOUDFLARE_ACCOUNT_ID` — da Cloudflare, colonna destra della home dell'account.
4. **(dopo, facoltativo)** un dominio tuo davanti (es. `dati.tyche.app`), così
   l'hosting si cambia senza aggiornare l'app.

## Per accendere Overture nell'app (lo faccio io, dopo i passi sopra)

- [ ] la prima pubblicazione è online e risponde (`…/v3/mappa.json`)
- [ ] `OVERTURE_RADICE` punta al progetto (o al dominio) che è **nostro**
- [ ] `OVERTURE_ACCESO = true` in `src/lib/overture.ts`
- [ ] privacy (5 lingue + PRIVACY.md): i file dei luoghi arrivano da Cloudflare,
      che vede l'indirizzo IP e la zona richiesta, come oggi OpenStreetMap
- [ ] attribuzione «© Overture Maps Foundation» accanto a quella di OpenStreetMap
- [ ] collaudo dell'owner sul telefono

Finché non è acceso, l'app non chiede niente a nessuno: la ricerca dei posti è
esattamente quella di prima (`OVERTURE_ACCESO = false`, con test).

## Prove in locale

```
python prepara.py --regione eu --da-file italia.parquet --out out   # senza S3, senza minimi
python radice.py --out out
```
