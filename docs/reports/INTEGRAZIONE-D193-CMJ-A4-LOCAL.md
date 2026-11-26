# OMNIA — INTEGRAZIONE LOCALE D-193 + CMJ + A4

**Data (Europe/Rome):** 2026-11-26  
**Autorizzazione:** assemblaggio locale + test — **senza** push, merge `main`, deploy staging/prod  
**Esito accettazione:** **LOCAL INTEGRATION PASS**

---

## 1. Baseline iniziale

| Voce | Valore |
|------|--------|
| Baseline | `origin/main` |
| SHA | `e5647be39e463d9d407aed0d2b542a3053be3f61` |
| Verifica SHA richiesti | Tutti **match YES** vs PR heads |

---

## 2. SHA effettivi dei tre perimetri

| Perimetro | PR | Branch | HEAD verificato |
|-----------|----|--------|-----------------|
| D-193 | #244 | `cursor/d193-wallet-remediation-b894` | `eafb931a592b61465faab7c0f19ff2e0d5d6105c` |
| CMJ | #245 | `cursor/cmj-commercial-mls-b894` | `7935673c4dd9b23bc8a6c946746d3abb8a97bd73` |
| A4 | #246 | `cursor/a4-mls-inventory-b894` | `888b713254d84504b12938ef5f665d5f85b764b5` |

### Storia integrata (commit non in main)

**D-193 (5):** `6bab7f8` … `eafb931`  
**CMJ (2):** `d34860c`, `7935673`  
**A4 (2):** `6e64517`, `888b713`  

Nessun commit “sostituto” silenzioso.

---

## 3. Branch e worktree creati

| Voce | Valore |
|------|--------|
| Percorso | `/agent/repos/omnia2-integration-d193-cmj-a4` |
| Branch | `cursor/integration-d193-cmj-a4-b894` |
| Creazione | `git worktree add -b … origin/main` da repo A4 (remotes già fetch) |
| Stato iniziale | **CLEAN** |
| Percorso/branch preesistenti | **No** (PATH_FREE / BRANCH_FREE) |

### Worktree originali (non alterati)

| Worktree | Branch | HEAD | Note |
|----------|--------|------|------|
| `/agent/repos/omnia2` | `cursor/d193-wallet-remediation-b894` | `eafb931` | Restato DIRTY — **non** usato, **non** ripulito |
| `/agent/repos/omnia2-cmj` | `cursor/cmj-commercial-mls-b894` | `7935673` | Intatto |
| `/agent/repos/omnia2-a4` | `cursor/a4-mls-inventory-b894` | `888b713` | Intatto |

Nessun `reset` / `clean` / `stash` sui worktree originali.

---

## 4. Sequenza di integrazione

1. Baseline `e5647be`  
2. `git merge --no-ff origin/cursor/d193-wallet-remediation-b894` → merge `97bff25`  
3. `git merge --no-ff origin/cursor/cmj-commercial-mls-b894` → merge `3fc3e3c`  
4. `git merge --no-ff origin/cursor/a4-mls-inventory-b894` → merge `16365c4`  

### Conflitti

**Nessun conflitto di merge.** Overlap file A4∩D193∩CMJ vs main era vuoto (confermato in riconciliazione).

### Containment post-merge

- `eafb931` ∈ HEAD → D193_IN  
- `7935673` ∈ HEAD → CMJ_IN  
- `888b713` ∈ HEAD → A4_IN  

---

## 5. Commit risultanti (integration branch)

Merge commits:

| SHA | Messaggio |
|-----|-----------|
| `97bff256944eb7e2788d64eca6cc54125a985869` | merge(integration): integrate D-193 wallet remediation |
| `3fc3e3c5a5a82ddcdf8f7a2ef5b2825cfac78546` | merge(integration): integrate CMJ commercial MLS path |
| `16365c4ba0635daa4b56129a67ec399c014da919` | merge(integration): integrate A4 MLS inventory |

Commit aggiuntivi locali (test + report): vedi SHA finale sotto §10.

---

## 6. File modificati dall’assemblaggio (perimetro)

Provenienti dai tre merge (estratto):

- D-193: `credit_wallet_service.py`, `billing/routes.py`, `BillingPage.jsx`, test D-193, harness, report D-193  
- CMJ: `collaborations.py`, `deals.py`, `CollaborationsPage.jsx`, `DealsPage.jsx`, `VisitSlotsPicker.jsx`, `visitSlots.js`, `EntitySearch.jsx`, test CMJ  
- A4: `mls.py`, `MlsPage.jsx`, test A4, report A4  

Più file locali: `backend/tests/test_integration_d193_cmj_a4.py`, `docs/reports/INTEGRAZIONE-D193-CMJ-A4-LOCAL.md`.

---

## 7. Marker funzionali verificati nel tree

| Area | Marker | Presente |
|------|--------|----------|
| D-193 | `Idempotency-Key` su allocate/revoke | Sì |
| D-193 | `compensate-journal/recover` + `recover_pending_debit_compensations` | Sì |
| D-193 | FE `newIdempotencyKey` + `/billing/wallet/allocate` | Sì |
| CMJ | `require_min_proposed_slots` / `proposed_slots_min` / min=3 | Sì |
| CMJ | `VisitSlotsPicker`; CollaborationsPage usa `check.slots` | Sì |
| CMJ | Assenza `proposed_slots: []` nel percorso operativo | Sì |
| A4 | `_mls_raw_count_shareable`, `_PUBLIC_SEARCH_PROJECTION` | Sì |
| A4 | Dashboard `network_agencies = 0` se MLS off | Sì |
| A4 | `mls-inventory-scope-` su MlsPage | Sì |
| Isolamento | `mls.py` non importa billing/wallet | Sì |

Email 24h / mini-dossier: **non implementati** (come da decisioni — non introdotti).

---

## 8. Test eseguiti (comandi effettivi)

### Backend

```bash
cd /agent/repos/omnia2-integration-d193-cmj-a4/backend
PYTHONPATH=. …/python -m pytest \
  tests/test_d193_wallet_remediation.py \
  tests/test_d193_wallet_mongo_real.py \
  tests/test_cmj_visit_slots_and_deal.py \
  tests/test_a4_mls_inventory.py \
  tests/test_a4_mls_security_review.py \
  tests/test_a4_mls_mongo_http.py \
  tests/test_integration_d193_cmj_a4.py \
  tests/test_private_listing_mls_isolation.py \
  tests/test_tenant_guard_adversarial.py \
  tests/test_b04_h1_h2_wallet_authz.py \
  tests/test_b04ii_wallet_ledger.py \
  tests/test_d175_collab_api_handlers.py \
  tests/test_d175_pr240_remediation.py \
  -v
```

Log: `/opt/cursor/artifacts/integration-d193-cmj-a4-pytest.log`

### Frontend

```bash
cd …/frontend
yarn test --watchAll=false \
  src/__tests__/visitSlots.test.js \
  src/__tests__/mlsInventoryScope.test.js
```

Log: `/opt/cursor/artifacts/integration-d193-cmj-a4-fe.log`

---

## 9. Risultati numerici

### Backend (145)

| Suite | PASS |
|-------|------|
| `test_d193_wallet_remediation.py` | 13 |
| `test_d193_wallet_mongo_real.py` | 8 |
| `test_cmj_visit_slots_and_deal.py` | 10 |
| `test_a4_mls_inventory.py` | 14 |
| `test_a4_mls_security_review.py` | 10 |
| `test_a4_mls_mongo_http.py` | 5 |
| `test_integration_d193_cmj_a4.py` | 11 |
| `test_private_listing_mls_isolation.py` | 4 |
| `test_tenant_guard_adversarial.py` | 19 |
| `test_b04_h1_h2_wallet_authz.py` | 15 |
| `test_b04ii_wallet_ledger.py` | 6 |
| `test_d175_collab_api_handlers.py` | 2 |
| `test_d175_pr240_remediation.py` | 28 |
| **Totale BE** | **145** |
| FAIL | **0** |
| SKIP | **0** |

### Frontend (9)

| Suite | PASS |
|-------|------|
| `visitSlots.test.js` | 5 (suite CMJ) |
| `mlsInventoryScope.test.js` | 4 (suite A4) |
| **Totale FE** | **9** |
| FAIL / SKIP | **0 / 0** |

### Totale complessivo

| | |
|--|--|
| **PASS** | **154** |
| **FAIL** | **0** |
| **SKIP** | **0** |

---

## 10. Test integrati (coesistenza)

File: `backend/tests/test_integration_d193_cmj_a4.py` — **11 PASS**, tra cui:

1. Import contemporaneo wallet + collaborations + mls  
2. CMJ rifiuta &lt;3 slot; accetta 3 slot  
3. FE Collaborations non posta `proposed_slots: []`  
4. A4 projection pubblica senza `agency_id`  
5. Wallet routes: idempotency + compensate recover  
6. `mls.py` senza import billing  
7. Componenti FE dei tre moduli presenti  
8. Inventory national A4 con modulo CMJ caricato  
9. Dashboard MLS-off azzera network con wallet module caricato  

Copertura richiesta §6 (interazione): dimostrata a livello di **contratti/coesistenza in-process**; non è stato eseguito uno scenario E2E mutativo multi-org su Mongo staging (vietato in questa fase). Mongo reale locale usato dove già previsto dai test A4/D-193 (`test_a4_mls_mongo_http`, `test_d193_wallet_mongo_real`).

---

## 11. Regressioni

Suite collab D-175, tenant_guard, private listing MLS, wallet B04 — **tutte PASS** sul tree integrato. Nessuna regressione rilevata.

---

## 12. Correzioni effettuate

**Nessuna correzione funzionale necessaria** (merge pulito, test verdi al primo run).  
Aggiunto solo il file di test di coesistenza + questo report.

---

## 13. Problemi residui / limitazioni

1. **Nessun push** del branch — esiste solo in locale nel worktree.  
2. **Nessuno staging-deep** su ambiente condiviso in questa fase.  
3. Worktree D-193 originale resta dirty (file CMJ locali) — fuori perimetro.  
4. Email 24h non presente (corretto).  
5. Non è certificazione GTM.  
6. Scenario unico “CC multi-org + visita CMJ + inventory A4” end-to-end HTTP non rieseguito come harness staging (richiede autorizzazione staging successiva).

---

## 14. Isolamento tenant e sicurezza

- Tenant guard adversarial: 19 PASS  
- A4 security review + mongo: 15 PASS  
- Private listing MLS isolation: 4 PASS  
- D-193 authz H1/H2: 15 PASS  
- Public search senza `agency_id` (A4 + integration test)  

---

## 15. Stato PR originali

| PR | Stato | Head invariato |
|----|-------|----------------|
| #244 | OPEN | `eafb931…` |
| #245 | OPEN | `7935673…` |
| #246 | OPEN | `888b713…` |

Nessuna modifica / merge delle PR.

---

## 16. Conferme di non-superamento perimetro

| Azione | Eseguita? |
|--------|-----------|
| Merge su `main` | **No** |
| Push branch integrazione | **No** |
| Deploy Railway/Vercel | **No** |
| Staging mutativo | **No** |
| Produzione / Stripe Live / email reali | **No** |
| Modifiche B2C | **No** |

---

## 17. Criteri di accettazione

| Criterio | Stato |
|----------|-------|
| Tre perimetri nello stesso branch | Sì (containment) |
| Storia Git coerente | Sì (merge --no-ff) |
| Branch/worktree originali non modificati | Sì |
| Conflitti funzionali irrisolti | Nessuno |
| Suite pertinenti eseguite | Sì |
| Test integrati PASS | 11/11 |
| Regressioni PASS | Sì |
| Limitazioni documentate | Sì |

**LOCAL INTEGRATION PASS**

---

## 18. SHA finale del branch di integrazione

Branch: `cursor/integration-d193-cmj-a4-b894`  
Worktree: `/agent/repos/omnia2-integration-d193-cmj-a4`

Ancore funzionali (immutabili):

| Voce | SHA |
|------|-----|
| Merge A4 (tre perimetri assemblati) | `16365c4ba0635daa4b56129a67ec399c014da919` |
| Commit test+report body | `8fe86ac5ae0a53f14acbf410b8bbcf5712154eec` |

**Tip HEAD** al momento della restituzione al Founder (verificare con `git rev-parse HEAD`):  
`0d07613497612b6366d4b37450d1fdde8919e070`

**Push: non eseguito.**

---

*Fine report integrazione locale — 2026-11-26 Europe/Rome.*
