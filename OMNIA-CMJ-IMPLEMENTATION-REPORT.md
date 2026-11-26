# OMNIA — CMJ — IMPLEMENTATION REPORT

**Gate:** CMJ — Percorso commerciale MLS operativo  
**Autorizzazione:** `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE CMJ`  
**Ambito:** solo locale (FE/BE/test/browser/docs). **Niente** commit · push · merge · deploy · staging remoto · Stripe Live · email reali.  
**PR #244:** resta OPEN / non mergiata / non integrata.  
**Data (Europe/Rome):** 2026-11-25 ~16:35 CET  

---

## 1. Branch e SHA iniziale

| Voce | Valore |
|------|--------|
| Branch | `cursor/d193-wallet-remediation-b894` |
| Upstream | `origin/cursor/d193-wallet-remediation-b894` |
| HEAD iniziale (e finale non commitato) | `eafb931a592b61465faab7c0f19ff2e0d5d6105c` |
| Messaggio tip | `docs(d193): tip SHA for report/harness HEAD` |
| Commit / push in questo ciclo | **NON eseguiti** (vietati dall’autorizzazione) |

---

## 2. Stato iniziale del working tree

All’avvio del mandato CMJ (prima delle modifiche prodotto):

- Tracked clean rispetto a `eafb931` salvo lavoro D-193 già su branch remoto.
- Untracked preesistente preservato: `OMNIA-NEXT-CRITICAL-FUNCTIONAL-GATE.md` (analisi gate).
- Nessun reset / clean / stash / force push.

---

## 3. Dipendenze dalla PR #244

| Domanda | Esito |
|---------|-------|
| Il codice CMJ dipende da modifiche runtime in #244? | **No.** #244 = wallet D-193 + docs/harness. |
| #244 contiene solo docs/harness o anche runtime necessario a CMJ? | Runtime wallet billing; **non** collab/visite/Deal UI. |
| Base disponibile sul branch corrente | `eafb931` include tip docs D-193 + codice prodotto main tip; CMJ agisce su `collaborations` / `deals` / FE immoweb. |
| Conflitti / rischio D-193 | Modifiche CMJ non toccano `credit_wallet_service` / billing wallet. Coesistenza locale OK. |
| Si può implementare/testare CMJ senza integrare #244? | **Sì.** Verificato: test FakeDB + API locale + browser locale senza merge. |

**Decisione operativa:** nessuna merge/cherry-pick/rebase di #244.

---

## 4. Problemi riprodotti (pre-fix)

| ID | Problema | Evidenza |
|----|----------|----------|
| CMJ-01 | `DealsPage` richiedeva input testuali `property_id` / `client_id` (UUID) | Ispezione `pages/DealsPage.jsx` |
| CMJ-02 | FE inviava `proposed_slots: []`; BE accettava liste vuote/corte | `CollaborationsPage.jsx` + `VisitCreate` senza min |
| CMJ-03 | Liste collab: `Immobile {property_id}` | `CollaborationsPage.jsx` |
| CMJ-04 | Nessuna CTA visita→Deal con precompilazione robusta / label | Link parziale senza `property_label`; GET property partner = 404 |
| CMJ-05 | Continuità percorso frammentata in UI | Flusso API già presente; UI incompleta |

---

## 5. Correzioni implementate

### Backend

- `backend/apps/immoweb/collaborations.py`
  - `MIN_VISIT_PROPOSED_SLOTS = 3`
  - `normalize_proposed_slots` / `require_min_proposed_slots` (vuoti, &lt;3, duplicati)
  - Enrichment batch collab/visite (`property_label`, counterpart agency, `next_action`) — **no N+1**
  - `update_visit`: `agreed_slot` obbligatorio se esistono proposte; deve essere in lista
- `backend/apps/immoweb/deals.py`
  - Idempotenza CMJ-04: stesso `visit_id` + `agency_id` + `client_id` → ritorna Deal esistente (non chiuso)

### Frontend

- Nuovo `components/EntitySearch.jsx` (estratto da Activities; riuso condiviso)
- Nuovo `components/visitSlots.js` + `VisitSlotsPicker.jsx`
- `ActivitiesPage.jsx` → importa EntitySearch condiviso
- `pages/DealsPage.jsx` → ricerca immobile/cliente; niente UUID; banner da visita; `property_label` iniziale
- `pages/CollaborationsPage.jsx` → form ≥3 slot; label leggibili; agree con select; CTA «Apri Deal da visita»; revoke invariato

### Test

- Nuovo `backend/tests/test_cmj_visit_slots_and_deal.py`
- Aggiornati VisitCreate/agree in `test_d175_collab_api_handlers.py`, `test_d175_pr240_remediation.py`
- Nuovo `frontend/src/__tests__/visitSlots.test.js`

---

## 6. File modificati / creati (working tree finale, non commitati)

**Modificati**

- `backend/apps/immoweb/collaborations.py`
- `backend/apps/immoweb/deals.py`
- `backend/tests/test_d175_collab_api_handlers.py`
- `backend/tests/test_d175_pr240_remediation.py`
- `frontend/src/apps/immoweb/ActivitiesPage.jsx`
- `frontend/src/apps/immoweb/pages/CollaborationsPage.jsx`
- `frontend/src/apps/immoweb/pages/DealsPage.jsx`
- `OMNIA-NEXT-CRITICAL-FUNCTIONAL-GATE.md` (aggiornato esito CMJ locale)

**Creati**

- `backend/tests/test_cmj_visit_slots_and_deal.py`
- `frontend/src/apps/immoweb/components/EntitySearch.jsx`
- `frontend/src/apps/immoweb/components/VisitSlotsPicker.jsx`
- `frontend/src/apps/immoweb/components/visitSlots.js`
- `frontend/src/__tests__/visitSlots.test.js`
- `OMNIA-CMJ-IMPLEMENTATION-REPORT.md` (questo file)

**Preservati / non toccati di proposito**

- Tutto il codice D-193 / wallet / billing di #244
- Nessuna modifica Railway/Vercel/prod

---

## 7. Test aggiunti e comandi eseguiti

### Backend (FakeDB)

```bash
cd backend && python -m pytest \
  tests/test_cmj_visit_slots_and_deal.py \
  tests/test_d175_collab_api_handlers.py \
  tests/test_d175_pr240_remediation.py -q
```

**Risultato:** `40 passed`

Copertura CMJ mirata:

- reject 0 / 1 / 2 slot
- reject duplicati / blank→too few
- accept 3 slot + agree validation
- label enrichment lista collab
- visita→Deal + idempotenza
- client foreign deny
- revoke → deny nuova visita

### Frontend

```bash
cd frontend && CI=true npm test -- --watchAll=false --testPathPattern=visitSlots
```

**Risultato:** `5 passed` (suite visitSlots)

### API E2E locale (due agenzie sintetiche)

Script HTTP su `127.0.0.1:43121` con:

- Owner: `demo.admin@omniaecosystem.it` / `demo-agency-001`
- Partner: `titolare@nicastroimmobiliare.it` / `nicastro-agency-001`

Prep locale Mongo (solo DB locale): `email_verified`, `mls_enabled`, `mls_shared` su seed demo.

**Risultato:** `22/22 PASS` — log `/opt/cursor/artifacts/cmj-api-e2e.log` · summary `cmj-api-e2e-summary.json`

Passi: collab → accept → labels → reject 0/2 slot → visit 3 → agree → complete → mini-dossier → search cliente → Deal → idempotenza → proposta → risposta partner → chat → revoke → deny → search immobile owner.

### Browser E2E locale (Chromium via Playwright)

Preview `http://127.0.0.1:43123` dopo `omnia-stack.sh rebuild`.

Run finale `cmj-browser-e2e3`: **8/8 PASS**

- UI agree visita (select slot + Concorda)
- UI complete
- CTA Deal da visita (banner, immobile locked, no UUID)
- ricerca/selezione cliente «Sara»
- Deal creato con titoli leggibili
- Owner: ricerca immobile «Prati» + cliente «Giulia» senza UUID

Log: `/opt/cursor/artifacts/cmj-browser-e2e3.log`  
Screenshot: `cmj-b3-01` … `cmj-b3-06`, `cmj-02-collab-list`, `cmj-03-visit-slots-form`  
Demo video: `/opt/cursor/artifacts/cmj-browser-demo.mp4` (slideshow da screenshot browser reali; export video Playwright fallito per tooling ffmpeg cache)

---

## 8. Conteggio effettivi

| Suite | Passati | Falliti |
|-------|---------|---------|
| Backend CMJ + D-175 collab/pr240 | 40 | 0 |
| Frontend visitSlots (+ listingFlag regressione) | 13 | 0 |
| API E2E locale CMJ | 22 | 0 |
| Browser UI E2E3 | 8 | 0 |

---

## 9. Criteri oggettivi di PASS (locale)

| # | Criterio | Stato |
|---|----------|-------|
| 1 | Nessun UUID digitato per creare Deal | **PASS** (EntitySearch) |
| 2 | Ricerca/selezione immobile e cliente | **PASS** (browser + API) |
| 3 | Visita FE ≥3 slot | **PASS** (UI + unit) |
| 4 | Backend rifiuta &lt;3 | **PASS** (unit + API) |
| 5 | Label collab leggibili | **PASS** |
| 6 | Visita→Deal mantiene contesto | **PASS** |
| 7 | Proposta/risposta | **PASS** (API E2E) |
| 8 | Chat solo con condizioni | **PASS** (API; UI chat non ri-collaudata in E2E3 oltre CTA) |
| 9 | Revoca blocca nuove ops | **PASS** (API) |
| 10 | Test automatici verdi | **PASS** |
| 11 | E2E browser locale | **PASS** (Playwright Chrome) |
| 12 | Documentazione con evidenze | **PASS** (questo report) |

---

## 10. Regressioni

- Suite D-175 collab handlers + PR240 remediation: **verdi** dopo allineamento VisitCreate a ≥3 slot.
- Nessuna regressione dimostrata su D-193/wallet (non modificato).
- W3/W4 non riaperti; solo regressione mirata collab/deal.

---

## 11. Limiti e rischi residui

1. **Staging CMJ non eseguito** — richiede autorizzazione successiva.
2. **Partner non può cercare immobili owner via `/app/properties?q=`** — corretto per tenant; Deal da visita/collab usa `property_id` + `property_label` precompilati. Ricerca libera cross-tenant MLS inventory non aggiunta (fuori scope minimo).
3. **GET `/app/properties/{id}` partner = 404** — label via `initialLabel` / enrichment lista; OK UX.
4. **Mini-dossier 24h email** — non verificato (email reali vietate); feedback API sì.
5. **Commit/PR CMJ** — non creati per vincolo autorizzazione; working tree sporco sul branch D-193.
6. **computerUse Cursor** — non disponibile (quota modello); browser via Playwright headless.
7. Export video Playwright nativo fallito; demo mp4 = slideshow screenshot reali.

---

## 12. Stato finale del working tree

```
M  backend/apps/immoweb/collaborations.py
M  backend/apps/immoweb/deals.py
M  backend/tests/test_d175_collab_api_handlers.py
M  backend/tests/test_d175_pr240_remediation.py
M  frontend/src/apps/immoweb/ActivitiesPage.jsx
M  frontend/src/apps/immoweb/pages/CollaborationsPage.jsx
M  frontend/src/apps/immoweb/pages/DealsPage.jsx
?? OMNIA-NEXT-CRITICAL-FUNCTIONAL-GATE.md
?? OMNIA-CMJ-IMPLEMENTATION-REPORT.md
?? backend/tests/test_cmj_visit_slots_and_deal.py
?? frontend/src/__tests__/visitSlots.test.js
?? frontend/src/apps/immoweb/components/EntitySearch.jsx
?? frontend/src/apps/immoweb/components/VisitSlotsPicker.jsx
?? frontend/src/apps/immoweb/components/visitSlots.js
```

HEAD resta `eafb931` (nessun commit).

---

## 13. Gate CMJ locale — verdetto

# **PASS locale**

Implementato e verificato in ambiente locale isolato.  
**Non** dichiarato staging-verificato.  
**Non** certificato GTM / Product Acceptance dogfood.

### Attività che richiedono autorizzazione successiva

1. Commit/push su branch dedicato CMJ (o cherry-pick pulito fuori da #244) + PR.
2. Staging-deep CMJ (API + FE + browser su staging).
3. Eventuale estensione ricerca MLS inventory per partner (se Founder la vuole oltre la precompilazione visita).
4. Merge #244 / D-193 — **separato**, solo se Founder lo chiede.

---

*Fine report CMJ.*


---

## 14. Promozione Git (in corso → completata al push)

| Voce | Valore |
|------|--------|
| Base | `origin/main` @ `e5647be` |
| Branch dedicato | `cursor/cmj-commercial-mls-b894` |
| Worktree | `/agent/repos/omnia2-cmj` (originale D-193 intatto) |
| PR #244 | OPEN, non modificata |
| Diff | solo file CMJ (nessun wallet/D-193) |
| Test isolati | backend 40 · FE visitSlots 5 · API E2E 16/16 · FE build OK |

Dettaglio completo in `OMNIA-CMJ-PROMOTION-STAGING-REPORT.md`.
