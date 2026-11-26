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
| Overlap path D-193 ∩ CMJ | **nessuno** (`git diff --name-only origin/main..eafb931` vs path CMJ) |
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

Dipendenza runtime D-193: **non richiesta** (test FakeDB + API locale su main+CMJ).

---

## C. Commit / push / PR

*(compilato dopo push)*

| Voce | Valore |
|------|--------|
| Commit SHA | _TBD_ |
| Branch remoto | `origin/cursor/cmj-commercial-mls-b894` |
| PR URL | _TBD_ |
| Base PR | `main` |
| Merge | **NON eseguito** |

---

## D. Staging-deep

*(compilato dopo deploy)*

| Voce | Valore |
|------|--------|
| Servizi staging | _TBD_ |
| SHA/deploy effettivamente servito | _TBD_ |
| E2E staging | _TBD_ |

---

## E. Verdetti

| Gate | Stato |
|------|-------|
| **PROMOZIONE CMJ** | _in corso → aggiornato post-PR_ |
| **STAGING-DEEP CMJ** | _pending_ |

---

*Aggiornamento incrementale durante il ciclo.*
