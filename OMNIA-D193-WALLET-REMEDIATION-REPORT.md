# OMNIA — D-193 WALLET REMEDIATION REPORT

**Data (Europe/Rome):** 2026-11-25 ~13:40 CET  
**Mandato:** remediation locale + gate Mongo reale / UI / failure recovery / riconciliazione suite  
**Autorizzazione:** `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` — solo locale  
**Esclusi:** commit · push · merge · deploy · Railway/Vercel/Mongo staging-prod · Stripe Live · email  
**Verdetto sintetico (pre-promozione):**

| Gate | Stato |
|------|--------|
| Implementazione locale | **sì** |
| FakeDB locale | **PASS** |
| MongoDB reale locale | **PASS** |
| UI browser locale | **PASS** |
| CI | in corso / da verificare dopo push |
| Deploy staging | **non ancora** |
| Staging-deep | **non verificato** |
| GTM readiness | **NON CERTIFICATO** |

**Ops recovery:** `POST /billing/wallet/compensate-journal/recover` (Super Admin only) espone `recover_pending_debit_compensations`.

---

## 1. Stato git / working tree

| Check | Valore |
|-------|--------|
| Branch | `cursor/d193-wallet-remediation-b894` |
| HEAD | `e5647be39e463d9d407aed0d2b542a3053be3f61` |
| Commit/push/merge/deploy | **nessuno** |
| Working tree | intenzionalmente sporco (M + ??) |

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
| Staging-deep | — | **non verificato** |
| GTM | — | **non certificato** |

---

## 7. Residui aperti

1. Staging-deep E2E (gate successivo Founder).  
2. Transazioni multi-doc non adottate (serve RS anche fuori dal harness).  
3. Journal open failure estremo ancora residuo ops.  
4. Idempotency-Key ancora **opzionale** (legacy).  
5. Cookie `COOKIE_SECURE=true` in `.env` Cloud: UI locale ha usato inject cookie / HTTPS; non è un difetto wallet ma un attrito dev locale.  
6. `computerUse` Cursor non disponibile (quota modello): UI verificata via Chrome headless.

---

## 8. Decisioni Founder strettamente necessarie (prossimi gate)

1. Autorizzare **staging-deep** (`grant → allocate → debit FIFO → revoke` su 2 filiali stessa P.IVA).  
2. (Opzionale) Rendere Idempotency-Key obbligatoria.  
3. (Opzionale) Imporre replica set / txn multi-doc in architettura deploy.

---

## 9. Conferme operative

1. **Modifiche:** compensate+journal, null-key fix, Mongo harness tests, UI+`is_main_admin`, indici journal, report.  
2. **Test:** audit-set 92 PASS; FakeDB D-193 12 PASS; Mongo reale 8 PASS; gate estesa 200 PASS; UI browser PASS.  
3. **Residui:** §7.  
4. **Working tree:** sporco su `cursor/d193-wallet-remediation-b894` @ `e5647be`.  
5. **Conferma:** **nessun** commit, push, merge o deploy.

---

**Fine report aggiornato — D-193 locale + gate Mongo/UI. Non GTM-ready.**
