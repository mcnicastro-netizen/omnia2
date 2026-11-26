# OMNIA — D-193 Wallet Deep Audit (READ-ONLY)

**Data (Europe/Rome):** 2026-11-25 ~12:40 CET  
**Mandato:** POST-W4 / D-193 — audit read-only wallet centrale CommercialCustomer  
**Verdetto sintetico:** **implementato e verificato a livello unit/FakeDB · non certificato staging-deep · residui tecnici e di copertura documentati**  
**Ambito:** nessun mutamento codice/DB/staging; nessun nuovo E2E mutativo; nessun commit/push.

---

## 0. Executive (Founder)

Il wallet **multi-filiale sotto la stessa P.IVA** (1 CommercialCustomer → N Organization → 1 `cc_credit_wallets`) è **presente nel codice** e coperto da una **suite unitaria ampia (91 PASS** in questo audit su test mirati). Le decisioni B04-DES-04 / H1–H3 / MC-042 / R-03 / D-175 C4 strutturali risultano **allineate** sul percorso service+API.

**Non** si può dichiarare «affidabile GTM / wallet deep chiuso» perché:

1. **Nessuna prova staging-deep** allocate → spend FIFO → revoke → saldi su filiali reali (residuo D-193 esplicito).  
2. **UI gestionale** non espone allocate/revoke sul wallet centrale (API sì; FE Billing mostra saldo/acquisto, non redistribuzione filiali).  
3. **Difetto tecnico noto** in `debit_for_organization`: compensate su fallimento ripristina allocation ma **non** il `remaining_qty` del lot (commento in codice).  
4. Staging API **non** espone SHA commit nel meta Railway dell’ultimo deploy (25-Nov = `redeploy` env); allineamento codice↔immagine **non dimostrabile al millimetro** in questo giro RO.

---

## 1. Riconciliazione git / ambienti

| Check | Evidenza | Verdetto |
|-------|----------|----------|
| `origin/main` == `e5647be` | `git rev-parse origin/main` → `e5647be39e463d9d407aed0d2b542a3053be3f61` | **verificato** |
| `e5647be` è merge #243 | parents `3619381` + `dfc7ba4`; messaggio Merge PR #243 | **verificato** |
| #243 contenuto | docs D-193 / report W4; **non** tocca `credit_wallet_service.py` | **verificato** |
| Ultima modifica wallet su main | tip wallet = `622b920` (R-03); `0` commit successivi sul file fino a main | **verificato** |
| Working tree locale | branch `cursor/w4-l5-stripe-final-b894` @ `dfc7ba4` (parent di merge); status pulito al momento check | **osservato** |
| Staging API A/B health | A/B `status=ok`, `db=ok` (RO curl) | **verificato** |
| Staging deploy SHA == `e5647be` | meta ultimo SUCCESS `reason=redeploy` 25-Nov 11:04Z; **nessun** `commitHash` in meta | **non verificabile** (infra) |
| Staging vs codice wallet | wallet in main da prima di W4; #243 docs-only; immagine tipica post-W4 + redeploy env | **plausibile, non attestato SHA** |
| FE staging | HTTP 200 su progetto staging Vercel | **smoke only** |

**Conclusione §1:** SoT git per docs D-193 = `e5647be`. Codice wallet su main = tip `622b920` (stabile). Staging operativo sì; **corrispondenza bit-a-bit immagine↔commit non certificabile** senza SHA Railway.

---

## 2. Modello dati effettivo (da codice)

SoT: `backend/shared/billing/credit_wallet_service.py` (header B04-DES-04 / B04-II).

```
CommercialCustomer (1 × P.IVA)
  └── cc_credit_wallets × 1
        ├── credit_lots[]          (acquisto/grant; original/remaining/unallocated)
        ├── credit_allocations[]   (qty verso organization_id / filiale)
        └── cc_credit_ledger[]     (grant|allocate|revoke|consume|compensate|…)
Organization / agencies.commercial_customer_id → link obbligatorio per allocate (MC-045 H3)
Legacy mirror: credit_wallets / credit_ledger (agency-scoped, `cc_mirror`)
```

| Collection | Ruolo |
|------------|--------|
| `cc_credit_wallets` | Saldi cached `balance_total` / `balance_unallocated` |
| `credit_lots` | Lotti centrali; `idempotency_key` unique sparse |
| `credit_allocations` | Assegnazioni a filiale; `remaining_qty`, `revoked_at` |
| `cc_credit_ledger` | Tracciabilità; `idempotency_key` unique sparse |
| `commercial_customers` | `main_admin_user_id`, status operable (MC-042) |

**Unicità wallet per CC:** `ensure_wallet` + indice unique (connection.py ~225–252).  
**Nessuna funzione** `transfer` crediti CC↔CC. Movimento intra-P.IVA = allocate / revoke.

---

## 3. Superficie API / servizi

### 3.1 Service (`credit_wallet_service.py`)

| Funzione | Operazione |
|----------|------------|
| `ensure_wallet` | Crea/get wallet CC |
| `grant_lot` | Accredito lotto (+ opz. auto-allocate) |
| `allocate_credits` | Assegna a Organization (FIFO lotti; R-03 claim atomico `unallocated_qty`) |
| `revoke_allocation` | Revoca → torna unallocated (H1 bind CC) |
| `debit_for_organization` | Consumo FIFO allocazioni/lotti |
| `org_spendable_balance` | Saldo spendibile filiale |
| `wallet_summary` | Lettura aggregata |
| `assert_organization_linked_to_cc` | Anti cross-P.IVA |
| `grant_for_agency` | Bridge piano/assistito → `grant_lot` |

### 3.2 HTTP (`backend/apps/billing/routes.py`)

| Route | Auth effettiva |
|-------|----------------|
| `GET /billing/wallet` | `_WALLET_AUTH` + `_authorize_wallet_admin` → Main Admin (o SA read) |
| `GET /billing/wallet/organization` | `require_roles` (include branch) · sola **lettura** propria agency |
| `POST /billing/wallet/allocate` | Main Admin (o SA + `extraordinary_reason`) |
| `POST /billing/wallet/revoke` | idem + H1 `commercial_customer_id` risolto server-side |
| Helper `debit_credits` | usata da call-site (es. staging/virtual staging), non route pubblica “spend” generica |

### 3.3 Acquisto → wallet centrale

| Path | Comportamento |
|------|----------------|
| `checkout_fulfillment.fulfill_credits_topup` | `grant_lot(..., allocate_to_organization_id=None)` — **no auto-allocate** |
| `plan_credits` / assisted | `grant_for_agency` (può auto-allocare all’agency) |
| Stripe webhook | adiacente; side-effect crediti via fulfillment (W4 deep wallet **non** rieseguito) |

### 3.4 FE

| Area | Stato |
|------|-------|
| `BillingPage.jsx` | saldo `sub.wallet`, ricarica/acquisto (H4/self-serve gates) |
| UI allocate/revoke multi-filiale | **non trovata** sotto `frontend/src` (nessun client di `/billing/wallet/allocate\|revoke`) |
| Main Admin transfer | `MainAdminTransferPage.jsx` = handover ruolo, **non** crediti |

---

## 4. Matrice requisito → implementazione → test → evidenza → verdetto

Legenda verdetto riga:  
`IV` = implementato verificato (unit) · `IPV` = implementato parzialmente verificato · `NV` = non verificato staging · `GAP` = mancante / difetto · `FUORI` = fuori scope deciso

| # | Requisito (B16 / B04-DES-04 / D-175) | Implementazione | Test che lo dimostrano | Evidenza | Verdetto |
|---|-------------------------------------|-----------------|------------------------|----------|----------|
| R1 | Wallet unico centrale per P.IVA (1 CC) | `ensure_wallet`; unique CC | `test_d175_c4_structure` (1 wallet/CC); indici DB | codice + 91 suite | **IV** |
| R2 | Acquisto crediti sul wallet centrale | `grant_lot`; checkout no auto-alloc | C6 fulfillment FakeDB; grant idempotent B04-II | codice | **IV** (unit) / **NV** staging deep |
| R3 | Assegnazione a filiali | `allocate_credits` + POST allocate | B04-II; MC-045 H3; R-03 concurrency | codice + unit | **IV** |
| R4 | Revoca da filiali | `revoke_allocation` + POST revoke | B04-II revoke; H1 suite | codice + unit | **IV** |
| R5 | Redistribuzione disponibilità | solo via centrale (revoke→allocate); no transfer diretto org↔org | implicito architettura | design | **IV** (by design) |
| R6 | Consumo + registrazione | `debit_for_organization` + ledger `consume` + mirror legacy | B04-II FIFO/insufficient/suspended | codice + unit | **IV** |
| R7 | FIFO allocazione/consumo più vecchia | sort `created_at` lots/allocs | `test_fifo_debit_across_two_lots` | unit | **IV** |
| R8 | Conservazione crediti residui (revoke→pool) | revoke restore `unallocated_qty` | `test_revoke_returns_to_unallocated` | unit | **IV** |
| R9 | Divieto trasferimento tra P.IVA | `assert_organization_linked_to_cc` → `cross_vat_transfer_forbidden` | `test_allocate_rejects_cross_vat`; MC-045 other-CC | unit | **IV** |
| R10 | Main Admin vs Branch Admin | MA binding `assert_is_main_admin_of`; branch legge solo org | H2 authz; D-175 C4 matrix `commercial_wallet=False` per org admin | unit + dogfood C4 | **IPV** (§5.2) |
| R11 | Atomicità / concorrenza | `find_one_and_update` claim; **no** multi-doc txn | R-03 allocate concurrency; H1 concurrent revoke | unit | **IPV** (§5.1) |
| R12 | Idempotenza | lot/ledger keys; checkout `checkout:{session}` | `test_grant_lot_idempotent` | unit | **IPV** (HTTP allocate/revoke senza key client) |
| R13 | Audit / tracciabilità | `cc_credit_ledger` entry types | append su grant/alloc/revoke/consume | codice | **IV** struttura / **NV** staging export |
| R14 | Operabilità cease/suspend | MC-042 gates service+route | `test_mc042_cc_non_operable_wallet` | unit | **IV** |
| R15 | Multi-P.IVA network affiliati | 1 CC per affiliato (D-189) | C4 docs: **non** E2E network | decisionale | **FUORI** C4 / non deep qui |
| R16 | UI redistribuzione filiali | — | — | grep FE negativo | **GAP** prodotto |
| R17 | Staging E2E multi-filiale saldi | — | — | D-193 residuo | **NV** |
| R18 | Compensate debit ripristina lot | commento L749: lot non restored | nessun test compensate mid-flight | codice | **GAP** tecnico |

---

## 5. Difetti / rischi (riproducibili o documentati)

### 5.1 Compensate incompleto su debit (codice)

File: `backend/shared/billing/credit_wallet_service.py` ~743–760.

Su `HTTPException` a metà debit, si `$inc` di nuovo `credit_allocations.remaining_qty` e si scrive ledger `compensate`, ma **non** si ripristina `credit_lots.remaining_qty` («Note: lot restore would need lot_id…»).

**Rischio:** in race/failure path, `balance_total` (da lots) e allocazioni possono **divergere** fino a intervento ops.  
**Classificazione:** difetto codice · severità media · **non** coperto da test dedicato trovato.

### 5.2 `_WALLET_AUTH` include `branch_admin` / `agent`

File: `backend/apps/billing/routes.py` — dependency ampia; autorità reale in `_authorize_wallet_admin` / Main Admin.

**Rischio:** difesa a strati (OK se Main Admin check sempre eseguito); i test H2 che usano allow-list **più stretta** di `_WALLET_AUTH` non dimostrano da soli l’esclusione FastAPI di `branch_admin` sulla dependency live.  
**Mitigazione attuale:** `assert_is_main_admin_of` su mutate/read centrale.  
**Classificazione:** rischio authz-documentale · non bypass dimostrato nei test H1/H2 sul percorso Main Admin.

### 5.3 Idempotenza HTTP allocate/revoke

Service accetta `idempotency_key` su allocate; **route** POST allocate/revoke **non** espongono/passano key client.

**Rischio:** doppio click / retry client → doppia allocate se non gestito a FE.  
**Classificazione:** gap API/contratto · test unit sulla key di service esistono solo se passata.

### 5.4 Dual mirror legacy

`credit_wallets` / `credit_ledger` aggiornati come mirror. Percorsi che ancora debitano **solo** legacy (se esistenti) potrebbero desincronizzare.

**Classificazione:** rischio migrazione · `debit_for_organization` è il path CC; legacy helper segnalato come bridge.

### 5.5 FE senza allocate/revoke

Operazioni multi-filiale dipendono da API/manuale/script. Per GTM «gestione crediti multi-filiale» **manca il percorso utente**.

**Classificazione:** gap prodotto/FE · non gap del ledger service.

### 5.6 Staging deep assente

Nessun artefatto in questo audit di: 2 filiali, grant centrale, allocate A/B, debit FIFO, revoke, assert saldi su staging Mongo.

**Classificazione:** gap test/infra (residuo D-193).

### 5.7 Allineamento immagine staging

Ultimo deploy SUCCESS = redeploy senza commit hash esposto.

**Classificazione:** gap infrastruttura osservabilità.

---

## 6. Cosa dimostrano i test (eseguiti in questo audit)

Comando (locale, FakeDB — **non** staging):

```text
pytest tests/test_b04ii_wallet_ledger.py \
       tests/test_b04_h1_h2_wallet_authz.py \
       tests/test_mc042_cc_non_operable_wallet.py \
       tests/test_mc045_h3_allocate_link.py \
       tests/test_r03_allocate_concurrency.py \
       tests/test_d175_c4_structure.py \
       tests/test_d175_c6_fulfillment.py
→ 91 passed (log: /opt/cursor/artifacts/w4r/wallet_deep_unit_tests.log)
```

| Suite | Dimostra | Non dimostra |
|-------|----------|--------------|
| B04-II ledger | grant idempotent, FIFO debit, revoke, cross-VAT, suspended, insufficient | Mongo reale, staging, FE |
| B04 H1/H2 | revoke tenant bind, Main Admin exact vs alias | bypass se dependency live diversa |
| MC-042 | deny cease/suspend/unlinked | deroga E2E staging |
| MC-045 H3 | allocate solo org linkate; no partial su shortfall | — |
| R-03 | no overallocation concorrente | — |
| D-175 C4 | 1 wallet/CC; org admin senza wallet authority | C5–C8 purchase live |
| D-175 C6 | fulfillment grant path FakeDB | webhook staging wallet deep |

---

## 7. Percorsi alternativi / incoerenze API

| Percorso | Nota |
|----------|------|
| `grant_lot` con `allocate_to_organization_id` | Auto-allocate; H3 check **prima** del grant | OK se linkato |
| `grant_for_agency` (piano/assistito) | Può accreditare **e** allocare subito all’agency | Diverso da checkout topup (no auto-alloc) — **incoerenza di prodotto intenzionale?** da chiarire in mandato funzionale, non riaperta qui |
| Org wallet GET vs central GET | Branch legge org; centrale solo MA | Coerente |
| Founder bridge | Legge legacy balances; **non** mutate wallet CC | Nessun bypass grant trovato in founder_ops |
| Checkout B2B self-serve | 503 `self_serve_blocked` (D-193) | Gate O6; non è bug wallet ledger |

---

## 8. Separazione stati (onesta)

| Voce | Stato |
|------|-------|
| Modello CC/wallet/lotti/alloc/ledger | **implementato verificato** (unit) |
| Anti cross-P.IVA | **implementato verificato** |
| FIFO + revoke + concurrency allocate | **implementato verificato** |
| Main Admin mutate / Branch read | **implementato · verificato unit · caveats auth dependency** |
| Acquisto → grant centrale | **implementato · unit/C6 · staging deep non rifatto** |
| UI allocate/revoke multi-filiale | **mancante (FE)** |
| Staging E2E wallet deep | **non verificato** |
| Compensate lot restore | **difetto tecnico documentato** |
| Network multi-P.IVA affiliati | **fuori scope C4 / non in questo audit** |
| GTM-ready wallet | **non dichiarabile** |

---

## 9. Sequenza minima per chiudere i gap (solo proposta operativa — no implementazione)

Ordine suggerito **dopo** nuovo mandato Founder (questo audit non autorizza codice):

1. **Osservabilità staging:** esporre/annotare SHA deploy API (o `GET` version build) per riconciliare immagine↔`main`.  
2. **E2E staging read+write controllato (sintetico):** 1 CC, 2 org, grant → allocate A/B → debit FIFO → revoke → assert saldi/ledger (tag cleanup).  
3. **Fix compensate debit** (ripristino lot) + test mid-flight failure.  
4. **Contratto HTTP idempotency** su allocate/revoke (header/body key).  
5. **FE (o Cabina Ops)** allocate/revoke/saldi per filiale — altrimenti certificare solo «API-complete».  
6. Solo allora rivalutare residuo D-193 «wallet deep» → chiuso / accettato con limiti.

---

## 10. Risposta alla domanda Founder

> «Il wallet è davvero affidabile a livello multi-filiale e multi-P.IVA?»

- **Stessa P.IVA, multi-filiale (modello C4):** a livello **codice + unit test** il disegno è **coerente e difeso** (centrale, allocate/revoke, FIFO, anti cross-VAT, MA vs branch).  
- **Non ancora «certificato affidabile» per GTM:** manca **verifica staging-deep**, manca **UI redistribuzione**, resta un **bug di compensate**, e multi-P.IVA *network* è **fuori** dal collaudo C4.  
- **Multi-P.IVA:** il divieto di trasferimento tra CC è **implementato e unit-tested**; affidabilità operativa multi-CC non è stata esercitata in E2E in questo audit.

---

## 11. Riferimenti file (indice)

| Area | Path |
|------|------|
| Service | `backend/shared/billing/credit_wallet_service.py` |
| Authz MA | `backend/shared/billing/main_admin_service.py` |
| Routes | `backend/apps/billing/routes.py` (`/wallet*`) |
| Checkout grant | `backend/shared/billing/checkout_fulfillment.py` |
| Dipendenze ruoli | `backend/shared/auth/dependencies.py` |
| Dogfood C4 | `docs/dogfood/C4-STRUCTURE.md`, `C4-FOUNDER-PROCEDURE.md` |
| Test | `backend/tests/test_b04ii_wallet_ledger.py`, `test_b04_h1_h2_wallet_authz.py`, `test_mc042_cc_non_operable_wallet.py`, `test_mc045_h3_allocate_link.py`, `test_r03_allocate_concurrency.py`, `test_d175_c4_structure.py`, `test_d175_c6_fulfillment.py` |
| Log unit | `/opt/cursor/artifacts/w4r/wallet_deep_unit_tests.log` |

---

**Fine audit READ-ONLY.** Nessuna modifica a staging/DB; file report creato su richiesta mandato. Nessun commit eseguito.

---

## Addendum remediation locale (2026-11-25)

Le evidenze di questo audit restano valide come fotografia pre-fix. La remediation locale autorizzata è documentata in `OMNIA-D193-WALLET-REMEDIATION-REPORT.md` e aggiorna lo stato di:

- compensate debit (lot + alloc) → **corretto localmente (FakeDB)**;
- idempotenza allocate/revoke → **introdotta localmente**;
- UI Main Admin allocate/revoke → **implementata localmente**;
- gate `_WALLET_ADMIN_AUTH` → **indurito (no branch/agent)**.

**Non** aggiorna lo stato staging-deep / GTM: restano **non verificati / non certificati**.
