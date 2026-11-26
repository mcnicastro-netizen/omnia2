# STAGING-DEEP INTEGRATO — D-193 + CMJ + A4

**Data (Europe/Rome):** 2026-11-26 16:10 CET  
**Autore:** Cursor (Cloud Agent)  
**Autorizzazione:** Founder — promozione integrazione + staging-deep mutativo  
**Ambito:** solo staging · no merge `main` · no produzione commerciale · no Stripe Live · no email reali

---

## 0. Giudizio finale

**STAGING-DEEP PASS** (motivato).

Tutti i criteri essenziali del mandato risultano **PASS**:
- branch e deploy identificati e coerenti;
- API e frontend servono la stessa versione integrata;
- D-193, CMJ, A4 operativi su staging con scritture/letture reali;
- scenario integrato multi-organizzazione superato;
- isolamento CommercialCustomer A↔B dimostrato (HTTP + UI);
- RBAC wallet e MLS-off verificati;
- browser su FE distribuito: 10/10;
- harness HTTP/DB: 38/38;
- nessun dato di produzione commerciale coinvolto;
- nessun difetto bloccante residuo nel perimetro.

Residui non bloccanti: vedi §12.

---

## 1. Identità versione

| Voce | Valore |
|------|--------|
| Branch | `cursor/integration-d193-cmj-a4-b894` |
| Worktree | `/agent/repos/omnia2-integration-d193-cmj-a4` |
| **SHA iniziale (promosso)** | `9b695b1d6597565ea3d4c3d06948daf9b0155ad1` |
| **SHA finale (post-report)** | 2ffa6e3aded411764c06de2dd94b280ee781f016 |
| Baseline merge | D-193 + CMJ + A4 su baseline prevista (no-ff) |
| PR integrazione | [#247](https://github.com/mcnicastro-netizen/omnia2/pull/247) OPEN |
| PR sorgente **non toccate** | #244 D-193 (`eafb931…`) · #245 CMJ (`7935673…`) · #246 A4 (`888b713…`) |

### Verifica pre-promozione
- HEAD effettivo = SHA atteso `9b695b1…` **PASS**
- Working tree clean al momento del push **PASS**
- Report integrazione locale + test `test_integration_d193_cmj_a4.py` presenti **PASS**
- Tre perimetri presenti sul branch **PASS**

---

## 2. Push e PR

- Push del solo branch `cursor/integration-d193-cmj-a4-b894` eseguito.
- Nessuna modifica ai branch sorgente D-193 / CMJ / A4.
- Nessun merge su `main`.
- PR #244 / #245 / #246 lasciate intatte (OPEN, OID invariati al momento del report).

---

## 3. Deploy staging

| Servizio | Ambiente | ID deploy / nota |
|----------|----------|------------------|
| API Railway `omnia-api` (etichetta tecnica Railway «production» ≠ produzione commerciale) | staging OMNIA | `bedcc260-1bfc-459a-9831-938c44675b3f` |
| API Railway `omnia-api-w4b` (allineato) | staging | `e17a19e2-fc52-4d12-8593-b8c65f48315c` |
| Frontend Vercel `omnia-frontend-staging` | staging | `dpl_B7sFuATM39qHszqwjBTvL5CBiWRs` |
| API URL | | `https://omnia-api-production-85845f42.up.railway.app` |
| FE URL | | `https://omnia-frontend-staging.vercel.app` |
| Database | | `omnia_staging_e2e` (Mongo staging; URI solo da secret Railway / file locale non versionato) |

**Nota sicurezza:** etichetta Railway `production` = environment tecnico del progetto staging. Non è l’ambiente commerciale di produzione. Nessun Stripe Live, nessuna email reale, nessun DB produzione.

---

## 4. Prova codice effettivamente servito

Post-deploy OpenAPI live:
- header/schema **Idempotency-Key** su allocate wallet → **PASS**
- path `/api/billing/wallet/compensate-journal/recover` → **PASS**
- path `/api/app/mls/inventory` → **PASS**
- path `/api/app/visits` e `/api/app/deals` → **PASS**

Frontend staging (chunk JS): marker wallet/allocate, `proposed_slots`, `mls-inventory-scope` presenti sul deploy Vercel precedente alla sessione browser.

Railway non espone git SHA nel payload upload; la prova operativa è OpenAPI + comportamento funzionale allineato al tip `9b695b1`.

---

## 5. Sessione test

| Campo | Valore |
|-------|--------|
| Prefisso/session | `inte89dde76` (`session_tag=int_synth`) |
| Dati | sintetici isolati; cleanup eseguito a fine sessione browser |
| Fixture preesistenti | non modificate / non cancellate |

---

## 6. Risultati numerici

| Suite | PASS | TOTAL | FAIL |
|-------|------|-------|------|
| Staging-deep HTTP+DB+servizi (`int_staging_deep_full.py`) | **38** | **38** | **0** |
| Browser Playwright FE staging | **10** | **10** | **0** |
| **Complessivo sessione** | **48** | **48** | **0** |

Log: `/opt/cursor/artifacts/int-staging-deep-run4.log`, `int-browser-run3.log`, summary JSON `int-staging-deep-summary.json`, `int-browser-summary.json`.

---

## 7. D-193 — CommercialCustomer / wallet

### Setup
- CommercialCustomer **A** con organizzazioni A1 + A2 (+ org MLS-off nel seed).
- CommercialCustomer **B** separato con org B1.
- Main Admin A, Branch Admin A1, Main Admin B (ruoli distinti).

### Verifiche (tutte PASS)
| Check | Esito |
|-------|-------|
| Grant lotto centrale A (100) | PASS |
| Wallet doc `cc_credit_wallets` | PASS |
| Allocate service idempotente | PASS |
| HTTP wallet Main Admin | PASS |
| Org wallet Branch (spendable/allocazioni) | PASS |
| Branch **non** può allocate (403) | PASS |
| B **non** legge wallet A (403 `not_main_admin`) | PASS |
| Allocate HTTP + Idempotency-Key duplicata → stesso allocation id | PASS |
| Revoca allocazione | PASS |
| Redistribuzione (re-allocate post-revoke) | PASS |
| Debit organizzazione | PASS |
| Recover compensate journal | PASS |

Isolamento: utente B non legge/modifica wallet A (HTTP ripetuto anche post-CMJ/A4).

---

## 8. CMJ — collaborazioni / visite / Deal

| Check | Esito |
|-------|--------|
| Collab partner B su listing A shareable | PASS (201) |
| Accept owner → active | PASS |
| Visit con 1 slot → 400 `proposed_slots_min` | PASS |
| Visit con 3 slot | PASS |
| Agree slot + status `agreed` | PASS |
| Visit `completed` | PASS |
| Deal create (con `visit_id` + client owner) | PASS |
| Deal idempotente (stesso visit/client/agency) | PASS |

Frontend: pagina Collaborazioni mostra collab attiva, 3 slot, visita completed, azioni Deal/feedback (screenshot).

**Non implementato (fuori perimetro):** email a 24h / altre feature non approvate.

---

## 9. A4 — inventario MLS

| Check | Esito |
|-------|--------|
| Public search HTTP | PASS |
| Include shareable A + B | PASS |
| Esclude private / non-share / trash | PASS |
| Nessun `agency_id` in proiezione pubblica | PASS |
| Inventory national (vede share B, non private) | PASS |
| Inventory mine (solo A) | PASS |
| MLS-off → inventory 403 | PASS |
| MLS-off → dashboard network zero | PASS |
| CRM foreign property denied (404) | PASS |
| Coesistenza post wallet+CMJ | PASS |

---

## 10. Scenario integrato multi-modulo

Eseguito sullo stesso ambiente/seed:
1. A usa wallet centrale (grant/alloc/revoke/redistribute/debit) → **PASS**
2. Filiale A1 usa crediti assegnati (org wallet spendable + debit) → **PASS**
3. Due org (A1↔B1) collaborazione MLS → **PASS**
4. Visita concordata (≥3 slot) e completata → **PASS**
5. Deal creato + idempotenza → **PASS**
6. Inventario MLS ancora conforme post-operazioni → **PASS**
7. B non accede ai dati wallet di A → **PASS**

Nessuna regressione crociata osservata tra moduli.

---

## 11. Frontend / browser

FE: `https://omnia-frontend-staging.vercel.app`  
Route billing corretta: `/it/app/settings/billing` (non `/it/app/billing`).

| Check | Esito |
|-------|--------|
| Login Main Admin A | PASS |
| Pagina Piano & Crediti + controlli Alloca/Revoca | PASS (alloc UI usata; toast «Allocati 1 crediti») |
| Collaborazioni | PASS |
| Deals | PASS |
| MLS hub / inventario | PASS |
| Login org MLS-off → MLS UI | PASS |
| Login B → billing | PASS |
| Console errori hard (sessione primaria) | PASS |
| Nessun 5xx API inatteso | PASS |

### Screenshot / video
- `/opt/cursor/artifacts/int-browser-billing.png`
- `/opt/cursor/artifacts/int-browser-collaborations.png`
- `/opt/cursor/artifacts/int-browser-deals.png`
- `/opt/cursor/artifacts/int-browser-mls.png`
- `/opt/cursor/artifacts/int-browser-mls-off.png`
- `/opt/cursor/artifacts/int-browser-billing-b.png`
- `/opt/cursor/artifacts/int-browser-staging-demo.webm`

---

## 12. Difetti, correzioni, residui

### Difetti di prodotto nel perimetro
**Nessuno bloccante** riscontrato dopo le correzioni dell’harness di verifica.

### Correzioni durante la sessione
Solo sul **runner di test** (non sul codice prodotto):
- field names grant/allocate (`amount`/`origin`);
- collection names (`cc_credit_wallets`, `mls_collaborations`, `mls_visits`);
- client Deal sotto agency opener;
- visita `agreed`→`completed` prima del Deal con `visit_id` per idempotenza CMJ-04;
- loop Motor unico per evitare «Event loop is closed»;
- route FE billing → `/settings/billing`.

Nessun commit di fix prodotto necessario: comportamento staging allineato al tip `9b695b1`.

### Residui accettati (non bloccanti)
1. Shell HTTP `GET /it/app/billing` risponde 200 (SPA) ma la route applicativa è `/it/app/settings/billing` — verificato in browser.
2. Utenti seed atterrano su `/it/app/avvio` (onboarding incompleto) ma le pagine operative restano raggiungibili.
3. Upload Railway senza git SHA embedded — prova via OpenAPI + comportamento.
4. Durante switch utente (clear cookie) rumore 401 refresh/CORS — escluso dal gate console della sessione primaria.

### Regressioni
Nessuna regressione bloccante rispetto ai tre perimetri.

### Problemi residui
Nessuno nel perimetro autorizzato che impedisca il PASS.

---

## 13. Sicurezza e isolamento

| Controllo | Stato |
|-----------|--------|
| Isolamento wallet A↔B | PASS |
| Branch non allocate | PASS |
| Public MLS senza `agency_id` | PASS |
| MLS-off deny inventory + dashboard zero | PASS |
| CRM cross-tenant deny | PASS |
| Dati solo staging sintetici | PASS |
| No Stripe Live / no email reali / no DB prod commerciale | PASS |
| Secret non in report/repo/log | PASS |

---

## 14. Criteri PASS — checklist

- [x] Branch e deploy identificati  
- [x] API e frontend coerenti  
- [x] D-193 operativo  
- [x] CMJ operativo  
- [x] A4 operativo  
- [x] Scenario integrato multi-org  
- [x] Isolamento CommercialCustomer  
- [x] RBAC / sicurezza  
- [x] Browser  
- [x] Nessuna regressione bloccante  
- [x] Evidenze conservate  
- [x] Nessun dato produzione  

**Giudizio: STAGING-DEEP PASS.**

---

## 15. Limiti rispettati

- Nessun merge su `main`
- Nessun merge PR #244 / #245 / #246
- Nessun deploy produzione commerciale
- Nessuna modifica Stripe Live
- Nessuna email reale
- Nessuna modifica perimetro B2C

**Stato:** fermo in attesa del Founder.
