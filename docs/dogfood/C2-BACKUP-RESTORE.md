# D-175 · C2 — Backup / restore Dogfood

**Autorizzazione:** `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` — ciclo **C2**  
**Fuori scope:** C3 permanente, C4–C8, Stripe/Resend, merge senza Founder.

## Procedura ripetibile

```bash
# 1) Bootstrap Mongo isolato :27018 + ruoli (auth)
python3 scripts/dogfood_mongo_bootstrap.py

# 2) Drill completo: seed → dump → media → manifest → restore probe → verify
python3 scripts/dogfood_c2_drill.py
```

## Destinazioni

| Ruolo | DB | Note |
|---|---|---|
| Source | `omnia_df_c2_src` | prefisso `omnia_df_` |
| Restore | `omnia_df_probe_c2` | solo `omnia_df_probe*` |
| Vietati | `omnia`, `omnia_df_perm*` | fail-closed |

### Endpoint Mongo (fail-closed)

Dump/restore/bootstrap/drill accettano **solo** host:porta autorizzati:

- default: `127.0.0.1` / `localhost` / `::1` su porta `OMNIA_DF_MONGO_PORT` (default **27018**)
- override: `OMNIA_DOGFOOD_MONGO_ENDPOINTS=127.0.0.1:27018,localhost:27018`

Il nome DB `omnia_df_probe_*` **non** basta: un URI verso un altro server (anche senza DB nel path) viene rifiutato.

**Hard-deny assoluto (non overridable):**

- porta **27017** (mongod condiviso Cloud) — anche se `OMNIA_DF_MONGO_PORT=27017` o elencata in `OMNIA_DOGFOOD_MONGO_ENDPOINTS`
- host non-loopback
- `dogfood_mongo_bootstrap.py` rifiuta `--port 27017` **prima** di qualsiasi `stop_port` / `mongod`
- il drill chiama `assert_dogfood_mongo_endpoint` **prima** di `MongoClient` / `drop_database`

### Media mancanti

Se la directory media sorgente non esiste → backup **FAIL** (`ok: false`).  
Opt-out esplicito documentato: `OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA=1` (non usare in drill certificato).

## Ruoli Mongo

Vedi `dogfood/C2_MONGO_ROLE_MATRIX.json` (e artifact `D175-C2-MONGO-ROLE-MATRIX.json`).  
Credenziali solo in `dogfood/secrets/` (gitignored).

### Criterio PASS certificato (drill)

`report["ok"]` è true **solo se** tutti questi sono veri:

1. bootstrap Mongo isolato riuscito (`boot.ok`) — altrimenti il drill **si interrompe**
2. autenticazione admin obbligatoria (nessun fallback senza credenziali)
3. restore + media + deny su `omnia` / permanente
4. `role_checks.verified` — ogni check deve essere `PASS_ALLOWED` oppure `DENIED` con `pass: true`; qualsiasi `NOT VERIFIED` o report malformato → FAIL complessivo

## Manifest

`MANIFEST.json` include backup_id, git_sha, collections, media inventory SHA, dump tree SHA.  
Mai password/URI con credenziali.

## Permanent

Nessuna operazione sulla base permanente (C3).
