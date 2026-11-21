# OMNIA D-175 — Harness E2E T3/T4 (`scripts/d7_e2e`)

**Versione:** 1.0.0  
**Autorizzazione creazione:** Founder A+B (implementazione senza esecuzione)  
**Esecuzione:** richiede pacchetto **C** + flag `--confirm-staging-run`

## Perché esiste

La forense `D175-D7-FORENSIC-PROVENANCE-T3-T4.md` ha dimostrato che:

| Artefatto storico | Verdetto |
|-------------------|----------|
| A5 `d7_t3_api.json` | Provenienza verificata da `/tmp/d7_t3_t4_run.py` `run_t3` |
| A6 `d7_t4_api.json` | **Non** prodotto da A10; harness inline; **non SoT** |
| A9 seed | Email `@example.invalid` (API le rifiuta) |
| A10 | Classificatore T3 incompleto; T4 FAIL poi path patch; overwrite JSON |

Questo package è la **nuova baseline versionabile**. Non riproduce A6 bit-a-bit. Non modifica A5/A6/A7/A9/A10.

## Ambiente

Solo staging autorizzato (vedi `config.py`):

- FE / BE / DB / pin: valori di default in `config.py` (sovrascritti da `OMNIA_D7_*`)
- Railway project name atteso: `omnia-api-staging`
- Hostname BE contiene il segmento vendor `omnia-api-production-…` **dentro** il progetto staging (vedi forense / D1–D3)

## Prerequisiti runtime (quando C sarà autorizzato)

- `RAILWAY_API_TOKEN` (lettura variabili progetto staging)
- Opzionale `VERCEL_TOKEN` (gate P6 pin FE; senza → BLOCKED su P6, non PASS)
- `OMNIA_D7_MONGO_PROXY_HOST` / `PORT` se il proxy TCP differisce
- Python con dipendenze backend (`pymongo`, hashing auth)

## Comandi (non eseguire senza C)

```bash
cd /path/to/omnia2
PYTHONPATH=. python -m scripts.d7_e2e precheck --confirm-staging-run
PYTHONPATH=. python -m scripts.d7_e2e run --confirm-staging-run
PYTHONPATH=. python -m scripts.d7_e2e run --confirm-staging-run --cleanup-after
PYTHONPATH=. python -m scripts.d7_e2e cleanup --confirm-staging-run --run-id <RUN_ID>
```

Senza `--confirm-staging-run` il processo esce con codice 2.

## Artefatti immutabili

```text
artifacts/d7/<run_id>/
  MANIFEST.json
  precheck.json
  seed_meta.json
  secrets/fixtures_secrets.json   # mode 0600 — non committare
  t3_api.json
  t3_classification.json
  t4_api.json
  t4_classification.json
  console.log
  sha256sums.txt
  cleanup.json                    # se --cleanup-after
```

`run_id` = `UTC_YYYYMMDDThhmmssZ_<hex8>`.  
Se la directory esiste già → **errore** (no overwrite).

## Controlli T3 (tutti obbligatori per PASS)

Vedi `t3.py`: login B/A, collab create/accept, visit create/**complete**, mini-dossier, deal, chat open/post, **list da B**, isolamento altro tenant (solo 401/403), revoke, proposal-after-revoke (4xx).  
Qualsiasi **5xx** o status fuori allowlist → **FAIL**. Step saltato → **FAIL**.

## Controlli T4 (tutti obbligatori per PASS)

Vedi `t4.py`: CC/Main Admin binding, GET main-admin, branch login/me, **branch deny** su main-admin, create invite, no email-send signal, token da DB staging, accept, membership, isolamento non-membro.  
Token assente → **BLOCKED** (non PASS).

## Cleanup

Solo documenti con `d7_run_id == <run_id>`.  
**Non** cancella per solo `d7_tag` legacy.  
`run_id` troppo corto → refuse.

## Secrets

- Scritti sotto `artifacts/d7/<run_id>/secrets/` con **0600**
- Non usare `/tmp/d7_fixtures_secrets.json` (rimosso in A; era 0644)
- Aggiungere `artifacts/d7/**/secrets/` a `.gitignore` se non già coperto

## Limiti

- Non verifica UI browser
- Non attiva Stripe / Resend
- Non tocca produzione
- Precheck P6 richiede `VERCEL_TOKEN` per PASS completo

## Mapping forense → codice

| Problema | Mitigazione in questo harness |
|----------|-------------------------------|
| A6 ≠ A10 | Un solo package versionato; vietato overwrite |
| Classificatore T3 debole | Step visita/chat B/revoke/proposal nel PASS |
| Isolation 500 soft | `is_5xx` → FAIL; allowlist stretta |
| Email `.invalid` | Solo `@example.com` |
| Secrets 644 `/tmp` | 0600 sotto artifacts run |
| Path invite | `/api/app/agencies/me/invites`, `/api/app/invites/accept` |
| Main admin path | `/api/billing/commercial/main-admin` |
