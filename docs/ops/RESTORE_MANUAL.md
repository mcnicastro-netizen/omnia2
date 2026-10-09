# Procedura restore manuale (D-113) — non-prod

**Stato:** procedura documentata · test ripetibile su ambiente non-prod  
**Non è:** DR piattaforma · restore self-service · garanzia commerciale  
**Correlato:** D-096 · D-105 · O0 design · O3b

## Premessa onesta (CT-03)

| Livello | Significato |
|---------|-------------|
| Bak presente | cartella `BACKUP_ROOT/YYYY-MM-DD` esiste |
| Bak verificato | `MANIFEST.json` con `status: OK` (o PARTIAL noto) |
| Restore disponibile | questa procedura è eseguibile |
| Restore testato | almeno una run firmata sotto (esito verificabile) |

Bak ≠ restore testato. Non promettere “restore garantito” in marketing finché non ci sono tempi/limiti operativi firmati.

## Perimetro V1 (agency-first + portale B2C)

**In scope agency:** una singola agency (es. `demo-agency-001`) — immobili, clienti, richieste, attività, media referenziati, membership utenti correlati.

**In scope portale B2C (P-046 / P-047):** collection presenti nel backup giornaliero:
`b2c_purchases`, `b2c_visura_orders`, `consent_events`, `favorites`, `saved_searches`, `al_legal_audit`, `listing_inquiries` (+ `users` B2C / `properties` UGC già in dump properties).

**Fuori scope V1:** restore multi-tenant atomico, RPO/RTO commerciali, self-serve.

## Prerequisiti

1. Accesso SSH/shell all’host non-prod  
2. `BACKUP_ROOT` (default `/workspace/backend/.backups`) con almeno un giorno valido  
3. Mongo non-prod raggiungibile (`MONGO_URL` / DB name da `.env`)  
4. `LOCAL_STORAGE_ROOT` (default `/workspace/backend/.media`)  
5. Founder Ops mostra ultimo bak (`GET /api/app/ops/overview` → `backup.status`)

## Scelta del recovery point

```bash
ls -1 "$BACKUP_ROOT" | sort
# apri MANIFEST del giorno scelto
python -c "import json; print(json.load(open('$BACKUP_ROOT/YYYY-MM-DD/MANIFEST.json'))['status'])"
```

Usa solo giorni con `status` **OK** (o PARTIAL se le collection target sono integre).

## Procedura (agency `AGENCY_ID`)

Sostituisci `AGENCY_ID` e `DAY`.

### 1. Freeze operativo (non-prod)

Ferma scritture applicative sul tenant (mantieni API in sola lettura o ferma il processo app se sandbox dedicata).

### 2. Estrai documenti Mongo dal dump JSONL

```bash
DAY=YYYY-MM-DD
AGENCY_ID=demo-agency-001
SRC="$BACKUP_ROOT/$DAY"

# Esempio: properties dell'agency → file staging
python3 <<'PY'
import json, os, sys
day, aid = os.environ["DAY"], os.environ["AGENCY_ID"]
src = os.path.join(os.environ["BACKUP_ROOT"], day)
out = f"/tmp/restore_{aid}"
os.makedirs(out, exist_ok=True)
agency_colls = (
    "agencies","users","properties","clients","client_requests","activities",
    "leads","subscriptions","credit_wallets","publishing_connections",
)
# Portale B2C: di solito restore **globale** (non filtrato per agency) — copia intera collection
b2c_colls = (
    "b2c_purchases","b2c_visura_orders","consent_events","favorites",
    "saved_searches","al_legal_audit","listing_inquiries",
)
for coll in agency_colls + b2c_colls:
    path = os.path.join(src, f"{coll}.jsonl")
    if not os.path.isfile(path):
        print("MISSING", coll); continue
    kept = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            if coll in b2c_colls:
                kept.append(doc)  # dump intero
            elif coll == "agencies" and doc.get("id") == aid:
                kept.append(doc)
            elif coll == "users" and (
                aid in (doc.get("agency_ids") or []) or doc.get("account_type") == "b2c"
            ):
                # users B2C: includi tutti i b2c se restore portale; altrimenti solo membership agency
                kept.append(doc)
            elif doc.get("agency_id") == aid:
                kept.append(doc)
            elif coll == "properties" and doc.get("is_private_listing") and doc.get("owner_user_id"):
                kept.append(doc)  # UGC privati
    with open(os.path.join(out, f"{coll}.jsonl"), "w", encoding="utf-8") as w:
        for d in kept:
            w.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(coll, len(kept))
PY
```

### 2b. Verifica MANIFEST include B2C

```bash
python3 -c "import json; m=json.load(open('$BACKUP_ROOT/$DAY/MANIFEST.json')); print(sorted((m.get('collections') or {}).keys()))"
# attesi tra gli altri: b2c_purchases, consent_events, favorites, …
```

### 3. Ripristina in Mongo (replace per agency)

Su non-prod: per ogni collection, `delete_many` filtrato per agency poi `insert_many` dai JSONL staging.  
**Non** eseguire su produzione senza runbook dedicato e approvazione Founder.

### 4. Media

Copia selettiva da `$SRC/media/` i path referenziati dalle properties/fascicolo dell’agency (o, in sandbox, l’intero tree se piccolo).

```bash
# sandbox piccola: copia tree (pesante — solo non-prod piccolo)
rsync -a "$SRC/media/" "$LOCAL_STORAGE_ROOT/"
```

### 5. Verifica esito (criterio D-096)

Checklist pass/fail:

- [ ] `agencies` documento `AGENCY_ID` presente  
- [ ] conteggio `properties` / `clients` / `client_requests` / `activities` coerente col dump  
- [ ] almeno 1 immobile con foto raggiungibile via URL media  
- [ ] login utente membership agency ok  
- [ ] nessun documento di **altra** agency modificato (spot-check)  
- [ ] (portale) `b2c_purchases` / `consent_events` / `favorites` presenti se erano nel bak  
- [ ] (portale) login B2C + preferiti / ordini Visura coerenti col dump

### 6. Firma run

| Campo | Valore |
|-------|--------|
| Data run | |
| Ambiente | non-prod |
| Day bak | |
| Agency | |
| Esecutore | |
| Esito | PASS / FAIL |
| Note limiti | tempi, gap collection, media orphan |

## Limiti interni (dichiarati)

- Restore = **manuale**, non automatizzato in app  
- Collection assenti dal MANIFEST → gap accettato finché O0 V1 incrementale non le include tutte  
- Tempi: dipendono da volume media; non c’è RTO commerciale  
- PARTIAL bak: valutare collection per collection prima di restore

## Relazione O3a / D-105

Se Founder Ops mostra `backup.status` FAILED/MISSING → **non** avviare restore; correggere bak prima.
