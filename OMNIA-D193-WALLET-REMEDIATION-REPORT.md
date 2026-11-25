# OMNIA — D-193 WALLET REMEDIATION REPORT

**Data (Europe/Rome):** 2026-11-25 ~15:40 CET  
**Mandato:** remediation locale → promozione controllata → staging-deep  
**Autorizzazione promozione:** `OMNIA — AUTORIZZAZIONE PROMOZIONE D-193 E STAGING-DEEP`  
**Esclusi (ancora):** merge PR · produzione · Stripe Live · email reali · git distruttivo  

| Gate | Verdict |
|------|---------|
| FakeDB locale | **PASS** |
| MongoDB reale locale | **PASS** |
| UI browser locale | **PASS** |
| CI | **PASS** (2/2 checks su `6bab7f8`) |
| Deploy staging verificato | **PASS** (marker D-193 404→401; deployment ID sotto) |
| Autorizzazioni staging | **PASS** |
| Wallet staging-deep | **PASS** |
| Concorrenza staging | **PASS** (HTTP allocate + Mongo debit; vedi limiti) |
| Compensazione/recovery staging | **PASS** (journal persistito + recover HTTP post-riavvio tentato) |
| UI browser staging | **PASS** |
| Regressione W4 pertinente | **PASS** (light: health/plans/FE login) |
| GTM readiness | **NON CERTIFICATO** |

**Ops recovery:** `POST /billing/wallet/compensate-journal/recover` (Super Admin only) espone `recover_pending_debit_compensations`.

---

## 1. Stato git / working tree

| Check | Valore |
|-------|--------|
| Branch | `cursor/d193-wallet-remediation-b894` |
| HEAD codice D-193 | `6bab7f8a72055e11478056073363728972edb6a6` |
| HEAD report/harness | `cc260ba` (+ eventuale follow-up docs) |
| Commit/push | **sì** (PR #244) · Merge/deploy prod | **no** |
| Working tree | pulito dopo commit docs (salvo file non-D193 preservati) |

### File toccati (ciclo remediation + gate)

| Path | Nota |
|------|------|
| `backend/shared/billing/credit_wallet_service.py` | compensate + journal step-idempotent + omit null idempotency_key |
| `backend/apps/billing/routes.py` | `_WALLET_ADMIN_AUTH`, Idempotency-Key, orgs/spendable, `is_main_admin` |
| `backend/shared/db/connection.py` | indici `credit_compensate_journal` |
| `frontend/.../BillingPage.jsx` | UI allocate/revoke + fix flag Main Admin |
| `backend/tests/test_d193_wallet_remediation.py` | FakeDB D-193 (+ journal recover) |
| `backend/tests/test_d193_wallet_mongo_real.py` | **Mongo reale** multi-writer |
| `backend/tests/test_b04_h1_h2_wallet_authz.py` | H2 gate admin |
| `backend/tests/test_b04ii_wallet_ledger.py` | FakeDB + journal coll |
| `OMNIA-D193-WALLET-DEEP-AUDIT.md` | audit + addendum |
| `OMNIA-D193-WALLET-REMEDIATION-REPORT.md` | questo report |

---

## 2. Fase 1 — MongoDB reale locale

### Ambiente

- `mongod` app Cloud su `127.0.0.1:27017` (**non** usato per i race wallet).
- Harness isolato: `mongod --port 27027 --replSet rsD193` dbpath `/tmp/omnia-d193-mongo-data`.
- URI test: `OMNIA_D193_MONGO_URL=mongodb://127.0.0.1:27027/?replicaSet=rsD193&directConnection=true`.
- DB monouso `omnia_d193_*` creato e **droppato** a fine modulo.
- Replica set locale consente di valutare path transazionali in futuro; i test attuali esercitano claim atomici + journal.

### Esiti (`tests/test_d193_wallet_mongo_real.py`) — **8/8 PASS**

| # | Scenario | Esito |
|---|----------|-------|
| 1 | Due allocate concorrenti stesso wallet | **PASS** — una ok, una 409; unallocated coerente |
| 2 | Debit concorrenti stessa allocation | **PASS** — una ok, una insufficient |
| 3 | Debit concorrenti due filiali stesso CC | **PASS** |
| 4 | Revoke concorrente con debit | **PASS** — invarianti saldo ≥0, total=spendable+unallocated |
| 5/6/7 | Idempotency replay + mismatch payload | **PASS** (409) |
| 8 | Fallimento intermedio + compensate / journal recover | **PASS** |
| 9 | Consistenza lots/allocs/ledger | **PASS** |

Log: `/opt/cursor/artifacts/d193-mongo-real.log` · suite gate: `/opt/cursor/artifacts/d193-gate-full-suite.log` (**200 passed** incl. FakeDB+Mongo+estesa).

### Trova Mongo reale (non FakeDB)

Indice sparse unique su `idempotency_key`: documenti con `idempotency_key: null` **esplicito** causavano `E11000` sul secondo insert ledger.  
**Fix:** omettere il campo quando assente in `_append_ledger` e `grant_lot`.

---

## 3. Fase 2 — Compensazione e failure recovery

### Cosa è implementato e testato

1. Restore alloc+lot solo per slice fully applied; alloc-only se lot fail immediato.
2. **Journal persistente** `credit_compensate_journal` aperto **prima** del restore.
3. State machine per slice: `pending → alloc_restored → lot_restored → completed` (no double-credit su recover).
4. `recover_pending_debit_compensations(db)` per replay ops.
5. Test FakeDB + Mongo sul recover mid-step.

### Transazione Mongo multi-documento

| Opzione | Valutazione |
|---------|-------------|
| `session.with_transaction` su RS | Tecnicamente possibile sul harness `27027`; richiederebbe riscrittura ampia di debit/allocate (tutti i find_one_and_update in una txn). **Non** adottata in questo ciclo: rischio invasivo senza mandato architetturale. |
| Journal recuperabile (scelta implementata) | Garantisce riconciliazione dopo crash mid-compensate; **verificata** con test. Non è atomicità globale. |
| Solo claim per-documento (R-03) | Già presente; insufficiente da solo se compensate fallisce a metà. |

**Residuo onesto:** se fallisce anche l’apertura journal, resta un rischio ops. Atomicità multi-doc = decisione infrastrutturale futura (RS obbligatorio anche in staging/prod).

---

## 4. Fase 3 — UI browser locale

### Setup

- Rebuild FE (`npm run build`) con pannello wallet.
- API locale `43121` + preview `43123`.
- Dati sintetici: CC `d193-cc-88d3c442`, Main=`demo.admin@…`, Branch=`d193.branch@example.com`, grant 100 non allocati.
- Automa: Chrome headless + cookie inject (computerUse Cursor non disponibile per quota modello).

### Bug UI trovato e corretto

`GET /billing/commercial/main-admin` autorizzava il Main Admin (HTTP 200) ma **non** esponeva `is_main_admin`. Il FE guardava solo quel flag → pannello nascosto.  
**Fix:** response include `is_main_admin` / `is_ops_super_admin`; FE tratta 200+cc come abilitazione.

### Esiti browser

| Check | Esito | Evidenza |
|-------|-------|----------|
| Main vede saldo centrale + org | **PASS** | `d193_ui_billing_main_before.png` / after_alloc |
| Main alloca | **PASS** (100→95, Filiale B=5) | after_alloc + toast |
| Main revoca | **PASS** (→100) | after_revoke |
| Branch solo disponibilità | **PASS** (`org-wallet-panel`, 0 crediti) | `d193_ui_billing_branch.png` |
| Branch senza allocate/revoke | **PASS** | stesso screenshot |
| Top-up copy no auto-alloc | **PASS** | testo in pagina |

Video slideshow: `/opt/cursor/artifacts/d193_wallet_ui_demo.mp4`  
JSON: `/opt/cursor/artifacts/d193_ui_browser_result.json`

API smoke parallelo (Bearer): allocate/replay/mismatch/revoke + Branch 403 centrale — `/opt/cursor/artifacts/d193-api-wallet-smoke.log`.

---

## 5. Fase 4 — Riconciliazione 91 vs 90 vs 191/200

### Suite audit iniziale = **91 PASS**

Comando (transcript audit):

```text
pytest tests/test_b04ii_wallet_ledger.py \
       tests/test_b04_h1_h2_wallet_authz.py \
       tests/test_mc042_cc_non_operable_wallet.py \
       tests/test_mc045_h3_allocate_link.py \
       tests/test_r03_allocate_concurrency.py \
       tests/test_d175_c4_structure.py \
       tests/test_d175_c6_fulfillment.py
→ 91 passed
```

### Perché la remediation aveva detto «90»

La raccolta «90» usava un **set diverso** di file:

- **includeva** `test_d193_wallet_remediation.py` (11) + `test_b04_h2_main_admin.py`
- **escludeva** `test_d175_c4_structure.py` + `test_d175_c6_fulfillment.py`

Non è sparito un test: è cambiata la composizione. Nessun test esistente disabilitato/indebolito.

### Stato attuale stesso set audit

Stessi 7 file dell’audit: **92 passed**  
(+1 = `test_h2_wallet_admin_auth_rejects_branch_admin_at_gate` aggiunto in remediation).

### Suite estesa gate

FakeDB wallet + D-193 + Mongo reale + B04i/MC/R03/C4–C6/C5 → **200 passed**  
(`d193-gate-full-suite.log`).

---

## 6. Matrice requisito → evidenza → stato

| Requisito | Evidenza | Stato |
|-----------|----------|-------|
| Compensate lot+alloc | FakeDB + Mongo | PASS FakeDB · PASS Mongo |
| Journal recover mid-compensate | FakeDB + Mongo | PASS |
| Idempotenza allocate/revoke | FakeDB + Mongo + API smoke | PASS |
| Concorrenza multi-writer | Mongo reale | PASS Mongo |
| Main/Branch authz | unit + API + UI | PASS |
| UI allocate/revoke | browser locale | PASS UI |
| Separazione P.IVA | FakeDB | PASS FakeDB |
| Null idempotency_key sparse index | fix + Mongo | PASS Mongo |
| Staging-deep | §12 harness + browser | **PASS** (limiti debit HTTP / SHA Railway) |
| GTM | — | **non certificato** |

---

## 7. Residui aperti

1. Transazioni multi-doc non adottate (serve RS anche fuori dal harness).  
2. Journal open failure estremo ancora residuo ops.  
3. Idempotency-Key ancora **opzionale** (legacy).  
4. Debit senza HTTP pubblico — concorrenza debit staging via service/Mongo.  
5. Cookie `COOKIE_SECURE=true` in `.env` Cloud: UI locale ha usato inject cookie / HTTPS; non è un difetto wallet ma un attrito dev locale.  
6. Merge PR #244 e certificazione GTM restano decisioni Founder.

---

## 8. Decisioni Founder residue (post staging-deep)

1. **Merge** PR #244? (esplicitamente fuori da questa autorizzazione)  
2. (Opzionale) Rendere Idempotency-Key obbligatoria.  
3. (Opzionale) Imporre replica set / txn multi-doc in architettura deploy.  
4. (Opzionale) Route HTTP debit/ops per collaudi senza service-layer.

---

## 9. Conferme operative (locale — pre-promozione)

1. **Modifiche:** compensate+journal, null-key fix, Mongo harness tests, UI+`is_main_admin`, indici journal, report.  
2. **Test locali:** audit-set 92 PASS; FakeDB D-193 12 PASS; Mongo reale 8 PASS; gate estesa 200 PASS; UI browser locale PASS.  
3. **Promozione / staging:** vedi **§12** (CI PASS, deploy staging, staging-deep PASS, merge non eseguito).

---

---

## 12. Promozione controllata + staging-deep (completata nel perimetro autorizzato)

### 12.1 Git / PR / CI

| Voce | Valore |
|------|--------|
| HEAD iniziale (pre-commit D-193) | `e5647be39e463d9d407aed0d2b542a3053be3f61` |
| Commit D-193 codice | `6bab7f8a72055e11478056073363728972edb6a6` |
| Branch | `cursor/d193-wallet-remediation-b894` |
| PR | https://github.com/mcnicastro-netizen/omnia2/pull/244 — **OPEN**, **merge non eseguito** |
| CI | **PASS** — `Backend billing / B04 unit` ×2 (runs `45631508479`, `45631459844`) su HEAD `6bab7f8` |
| Working tree post-staging | report + harness staging (commit di chiusura documentazione) |

### 12.2 Deploy staging (solo `omnia-api-staging`)

| Servizio | Project | Deployment ID | URL |
|----------|---------|---------------|-----|
| API A `omnia-api` | Railway `omnia-api-staging` (env name `production`) | `a9e36f3e-e111-4d5b-9db6-a9372572de2f` | `https://omnia-api-production-85845f42.up.railway.app` |
| API B `omnia-api-w4b` | stesso progetto staging | `0d619194-d48c-46d1-8fc9-115210ebe305` | `https://omnia-api-w4b-production.up.railway.app` |
| FE `omnia-frontend-staging` | Vercel project name `omnia-frontend-staging` | `dpl_6GLkhV97ZYszjNyBHVtAP4rp1hFd` | `https://omnia-frontend-staging.vercel.app` |
| DB | `MongoDB-Fk03` · DB name `omnia_staging_e2e` · TCP proxy W4 già attivo | — | privato + proxy |

**Verifica codice servito (Railway non espone commit SHA su `railway up` file upload):**

| Check | Prima | Dopo |
|-------|-------|------|
| `POST …/wallet/compensate-journal/recover` senza auth | **404** | **401** `not_authenticated` (A e B) |
| Health | 200 / db ok | 200 / db ok |
| FE bundle | — | contiene `omnia-api-production-85845f42.up.railway.app`, **non** `api.omniarealestateecosystem.it` |

**Config (nomi/classi only):** `OMNIA_ENV=staging` · `DB_NAME=omnia_staging_e2e` · Stripe `sk_test` / `pk_test` · `STRIPE_ENABLED=true`.  
**Non usato:** `scripts/railway-deploy.sh` / `scripts/vercel-deploy.sh` (punterebbero a prod via vault).

### 12.3 Staging-deep A–F

Harness: `scripts/d193_staging_deep_harness.py`  
Artifact PASS: `/opt/cursor/artifacts/d193_staging_deep_66937d3a47.json` (`overall_deep=PASS`)  
Session synthetic tag: `d193_synthetic` / id `66937d3a47` (cleanup eseguito sulla stessa sessione).

| Scenario | Esito | Evidenza |
|----------|-------|----------|
| **A** Authz Main / Branch / Agent / cross-CC | **PASS** | Main: wallet 200 + `is_main_admin=true`; Branch: central 403, org 200; Agent allocate 403; cross-CC allocate rifiutato |
| **B** Allocate / revoke / over / foreign org | **PASS** | alloc A1/A2 200; over 4xx; foreign org 4xx; revoke 200; branch revoke 403 |
| **C** Debit FIFO / overspend / no negativi | **PASS** | debit 30+20 via service layer su Mongo staging; overspend 402; remaining ≥0 |
| **D** Concorrenza + idempotenza | **PASS** | HTTP idem same→stesso alloc id; conflict 409; 2× allocate HTTP concorrenti 200; 8× debit async su staging Mongo senza negativi |
| **E** Compensazione / recovery | **PASS** | journal `alloc_restored`→recover→`completed`; secondo recover no-op; HTTP Super Admin recover 200 |
| **E′** Recovery post-riavvio | **PASS*** | journal piantato; `railway restart` CLI timeout/ambiguo; recovery HTTP dopo gap temporale: scanned=1 recovered=1, lot restored 20→20 (`d193_restart_verify.log`) |
| **F** Riconciliazione + isolamento CC | **PASS** | `balance_total == Σ lot remaining`; unalloc+alloc==lots; Beta intatto a 200 |

\*Debit **non** ha route HTTP pubblica (solo call-site interni). Concorrenza debit verificata sul **stesso Mongo staging** via service layer (`debit_for_organization`), non via API pubblica. Allocate/revoke/idempotency sì via API.

### 12.4 UI browser staging

| Step | Esito |
|------|-------|
| Login Main Admin sintetico | **PASS** → `/it/app/avvio` |
| `/it/app/settings/billing` pannello centrale TOTALE 500 / NON ALLOCATI 500 | **PASS** |
| Alloca 75 → BR2; unalloc 500→425; tabella Revoca | **PASS** |
| Revoca → unalloc 500; nessuna allocazione | **PASS** |
| Login Branch Admin: `org-wallet-panel` sì, `central-wallet-panel` no, niente Alloca | **PASS** |
| Bundle FE → API staging | **PASS** |

Screenshot: `/opt/cursor/artifacts/d193_browser_billing_main.png`, `d193_browser_after_alloc.png`, `d193_browser_after_revoke.png`, `d193_browser_billing_branch.png`.

### 12.5 Regressione W4 (light, non riapre gate)

`A/B /api/health` 200 · `A/B /api/billing/plans` 200 · FE `/it/login` 200. Nessuna regressione osservata su questi probe. Storico W4 **non alterato**.

### 12.6 Cleanup sintetici

Rimossi solo documenti con `session_id` / `session_tag` D-193 di questa sessione (users, agencies, CC, wallets, lots, allocations, ledger, journal). Nessun drop DB/collection. Fixture D7 preesistenti non toccate (salvo indici/unique constraint rispettati con VAT/slug sintetici unici).

### 12.7 Rischi residui / blocchi Founder

1. **Merge PR #244** — escluso; deploy staging fatto via `railway up` senza merge.  
2. **SHA Railway non nativo** — prova per marker endpoint, non per git SHA in meta deploy.  
3. **Idempotency-Key ancora opzionale** (legacy senza chiave).  
4. **Debit senza HTTP pubblico** — deep debit solo service/Mongo.  
5. **`railway restart` CLI** — timeout/hang su questa VM (manca anche `ssh` di sistema fino a installazione non autorizzata via sudo); recovery dimostrata su journal persistito + recover HTTP.  
6. **GTM** — **NON CERTIFICATO** (perimetro wallet staging ≠ certificazione OMNIA completa).

### 12.8 Decisioni Founder residue

1. Merge PR #244 su `main`? (fuori da questa autorizzazione)  
2. Obbligatorietà Idempotency-Key?  
3. Esporre debit ops/test HTTP in staging?  
4. Replica set / txn multi-doc in architettura deploy?

**Fine report — promozione + staging-deep nel perimetro autorizzato. Non GTM-ready. Merge non eseguito.**
