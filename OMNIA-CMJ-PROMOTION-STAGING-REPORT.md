# OMNIA — CMJ — PROMOZIONE GIT E STAGING-DEEP

**Autorizzazione:** `OMNIA — AUTORIZZAZIONE PROMOZIONE CMJ E STAGING-DEEP`  
**Data (Europe/Rome):** 2026-11-26  
**PR #244:** resta OPEN / non modificata / non mergiata  

---

## A. Grafo Git e isolamento

| Voce | Valore verificato |
|------|-------------------|
| Working tree originale | `cursor/d193-wallet-remediation-b894` @ `eafb931` + CMJ uncommitted (preservato) |
| `origin/main` | `e5647be39e463d9d407aed0d2b542a3053be3f61` (Merge #243) |
| Merge-base `eafb931` ↔ `origin/main` | `e5647be` |
| Commit D-193 non in main | `6bab7f8` … `eafb931` (wallet/docs) — **esclusi** dal branch CMJ |
| Overlap path D-193 ∩ CMJ | **nessuno** |
| Branch CMJ | `cursor/cmj-commercial-mls-b894` basato su `origin/main` |
| Worktree | `/agent/repos/omnia2-cmj` |
| Trasferimento payload | sha256 match 14/14 file CMJ esportati |

### File CMJ inclusi (diff vs main)

```
backend/apps/immoweb/collaborations.py
backend/apps/immoweb/deals.py
backend/tests/test_cmj_visit_slots_and_deal.py
backend/tests/test_d175_collab_api_handlers.py
backend/tests/test_d175_pr240_remediation.py
frontend/src/apps/immoweb/ActivitiesPage.jsx
frontend/src/apps/immoweb/components/EntitySearch.jsx
frontend/src/apps/immoweb/components/VisitSlotsPicker.jsx
frontend/src/apps/immoweb/components/visitSlots.js
frontend/src/apps/immoweb/pages/CollaborationsPage.jsx
frontend/src/apps/immoweb/pages/DealsPage.jsx
frontend/src/__tests__/visitSlots.test.js
OMNIA-CMJ-IMPLEMENTATION-REPORT.md
OMNIA-NEXT-CRITICAL-FUNCTIONAL-GATE.md
OMNIA-CMJ-PROMOTION-STAGING-REPORT.md
```

Nessun file `wallet` / `billing` / `BillingPage` / `D-193` nel diff.

### PR #244

- URL: https://github.com/mcnicastro-netizen/omnia2/pull/244  
- State: **OPEN** · head `cursor/d193-wallet-remediation-b894` @ `eafb931`  
- Non modificata in questo ciclo  

---

## B. Regressione locale sulla base isolata

| Suite | Risultato | Artifact |
|-------|-----------|----------|
| pytest CMJ + D-175 collab + PR240 | **40 passed** | `/opt/cursor/artifacts/cmj-isolated-backend.log` |
| FE `visitSlots` | **5 passed** | `/opt/cursor/artifacts/cmj-isolated-fe.log` |
| API E2E dual-agency (API da worktree) | **16/16 PASS** | `/opt/cursor/artifacts/cmj-isolated-api-e2e.log` |
| `yarn build` frontend | **OK** | `/opt/cursor/artifacts/cmj-isolated-fe-build.log` |

Dipendenza runtime D-193: **non richiesta**.

---

## C. Commit / push / PR

| Voce | Valore |
|------|--------|
| Commit SHA | `d34860c246eacca9a2d8d3f7cee97cfe9af23585` |
| Branch remoto | `origin/cursor/cmj-commercial-mls-b894` |
| PR | https://github.com/mcnicastro-netizen/omnia2/pull/245 |
| Base PR | `main` |
| CI | **SUCCESS** (Backend billing / B04 unit ×2) |
| Merge | **NON eseguito** |

---

## D. Staging-deep

| Voce | Valore |
|------|--------|
| API staging | Railway service `omnia-api` · URL `https://omnia-api-production-85845f42.up.railway.app` |
| Deploy API | `4a77bafe-1537-49c8-9016-aa8a34969b71` SUCCESS · 2026-11-26 12:16 Europe/Rome |
| DB | `omnia_staging_e2e` (synthetic only; cleanup post-run) |
| FE staging | Vercel `omnia-frontend-staging` · alias `https://omnia-frontend-staging.vercel.app` |
| FE deploy CMJ (API corretta) | `dpl_HnhAiruV8vvwqCk3aLhJwE1kRTnJ` · bundle `main.66a23d06.js` con `REACT_APP_BACKEND_URL=https://omnia-api-production-85845f42.up.railway.app` |
| Prod / Stripe Live / email reale | **non toccati** |

### D1. API E2E staging (synthetic dual-agency)

| Esito | Artifact |
|-------|----------|
| **27/27 PASS** | `/opt/cursor/artifacts/cmj-staging-e2e.log` |

Criteri coperti: create/accept collab, labels titolo, reject 0/1/2 slot, visit ≥3, agree/complete, mini-dossier API, client search, open Deal + idempotenza, proposal/partner-respond, chat, deny post-revoke, owner property search, cleanup.  
`mini_dossier_email_24h`: **SKIP_VERIFIED_POLICY** (no real email; auth forbids real send).

Nota seed: documenti sintetici devono rispettare schema list (`client_type`/`updated_at`; property `status=active`). Seed incompleto → ResponseValidationError 500 su list (non gap CMJ prodotto).

### D2. FE browser staging

| Esito | Artifact |
|-------|----------|
| **13/13 PASS** | `/opt/cursor/artifacts/cmj-staging-browser-summary.json` · log `cmj-staging-browser.log` |
| Screenshot | `cmj-stg-01` … `cmj-stg-09` |
| Demo | `/opt/cursor/artifacts/cmj-staging-browser-demo.mp4` |

Criteri UI: label titolo (no UUID grezzo), VisitSlotsPicker ≥3 input, agree, CTA visita→Deal, niente placeholder `property_id`, banner/prefill da visita, EntitySearch cliente/immobile, Deal in lista.

### D3. Incidente FE deploy (risolto)

Primo deploy Vercel prebuilt aveva bakato `http://127.0.0.1:43121` perché l’ambiente Cloud Agent esponeva `REACT_APP_BACKEND_URL=http://127.0.0.1:43121` (override CRA su `.env.production.local`).  
Risolto: rebuild esplicito con URL Railway + redeploy `dpl_HnhAiruV8vvwqCk3aLhJwE1kRTnJ`. Verificato nel bundle live.

---

## E. Verdetti

| Gate | Stato | Note |
|------|-------|------|
| **PROMOZIONE CMJ** | **PASS** | Branch isolato da `main`, PR #245 OPEN, CI green, #244 intatta, no merge |
| **STAGING-DEEP CMJ** | **PASS** | API 27/27 + FE browser 13/13 su staging; email 24h = residuo accettato (policy) |

### Residui accettati

1. Delivery email mini-dossier 24h non esercitata su staging (policy no real send).  
2. Ambient `REACT_APP_BACKEND_URL=localhost` sul Cloud Agent — rischio deploy FE prebuilt; mitigazione documentata.

### Non fatto (fuori scope autorizzazione)

- Merge PR #245 / #244  
- Deploy produzione  
- Stripe Live  

---

*Chiusura ciclo promozione + staging-deep CMJ — 2026-11-26 Europe/Rome.*
