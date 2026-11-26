# OMNIA — NEXT CRITICAL FUNCTIONAL GATE

**Tipo:** analisi gate + aggiornamento post **promozione + staging-deep CMJ**  
**Data analisi (Europe/Rome):** 2026-11-25 ~16:15 CET  
**Data update CMJ locale:** 2026-11-25 ~16:35 CET  
**Data update promozione/staging:** 2026-11-26 Europe/Rome  
**Branch CMJ:** `cursor/cmj-commercial-mls-b894` @ `d34860c` · PR [#245](https://github.com/mcnicastro-netizen/omnia2/pull/245) OPEN  
**Esclusi:** merge PR #244 / #245 · deploy produzione · Stripe Live · email reale  
**SoT implementazione:** `OMNIA-CMJ-IMPLEMENTATION-REPORT.md`  
**SoT promozione/staging:** `OMNIA-CMJ-PROMOTION-STAGING-REPORT.md`

---

## 0. Sintesi esecutiva

| Voce | Valore |
|------|--------|
| **Gate prioritario** | **CMJ — Percorso commerciale MLS operativo** |
| **Stato CMJ locale** | **PASS** — EntitySearch Deal, visite ≥3 slot FE+BE, label, CTA visita→Deal |
| **PROMOZIONE CMJ** | **PASS** — branch isolato da `main`, PR #245, CI green, #244 intatta |
| **STAGING-DEEP CMJ** | **PASS** — API staging 27/27 · FE browser staging 13/13 |
| **Residui accettati** | Email mini-dossier 24h non esercitata (policy); ambient `REACT_APP_BACKEND_URL=localhost` su Cloud Agent (mitigato in deploy) |
| **Ciclo successivo (Founder)** | Review/merge #245 (se vuole); #244 resta indipendente |
| **Non riaprire** | D-193/#244 merge senza mandato · H4/self-serve · TOOL-08 · prod |

---

## 1. Ricostruzione dello stato reale

### 1.1 Classificazione usata

| Classe | Significato |
|--------|-------------|
| **D** | Decisione Founder approvata |
| **R** | Requisito ancora aperto / non deciso |
| **I** | Implementato in codice |
| **VL** | Verificato localmente (unit/FakeDB/browser locale) |
| **VS** | Verificato su staging (HTTP/FE attestato) |
| **NV** | Non verificato (o solo dichiarato) |
| **PD** | Problema dimostrato |
| **RI** | Rischio soltanto ipotizzato |

### 1.2 Evidenze consultate (SoT)

| Fonte | Classe rilevante |
|-------|------------------|
| `memory/DECISIONS.md` (D-175 ruoli, D-186…D-193) | D |
| `memory/PRODUCT_ACCEPTANCE_MATRIX.md` | D + I; dogfood prod ⬜ |
| `OMNIA-W4-STAGING-E2E-REPORT.md` | VS — verdetto **A con residui** |
| `OMNIA-D193-WALLET-REMEDIATION-REPORT.md` §12 | VS wallet deep PASS; merge escluso |
| `OMNIA-D175-ROADMAP-RESIDUI-GTM.md` (21-Nov) | inventario residui pre-W4/D-193 |
| `OMNIA-D175-D7-T1-T4-E2E-REPORT.md` | VS T3 collab/deal/chat PASS |
| `docs/ops/D175-PR240-DEFINITIVE-REMEDIATION-REPORT.md` | I+VL FIX-01…09 |
| Codice `DealsPage.jsx` / `CollaborationsPage.jsx` / `deals.py` | I (ispezione) |

### 1.3 Cosa è chiuso (non riaprire senza regressione dimostrata)

| Area | Stato | Evidenza |
|------|-------|----------|
| Auth/sessione multi-istanza, fail-closed | **VS** | W4-01…08, W4-18 |
| Tenant isolation | **VS** | W3 + W4-09/23 |
| Main Admin / filiali / inviti (API) | **VS** | D7 T4 · W4-10/11 |
| Lista immobili date mancanti (A-007) + gateway key (A-006) | **I + VL**; staging selettivo preparato | D-191 · S1 report |
| Deal/collab API (accept, visit, dossier, deal, chat, revoke→deny) | **VS** | D7 T3: `proposal_after_revoke` → **400** `collaboration_not_active` |
| Wallet centrale allocate/revoke/debit/recovery | **VS** | D-193 staging-deep (PR #244 OPEN, merge fuori scope) |
| Resend L5 + Stripe Test webhook | **VS** | W4-19/21/22 · D-193 |
| H4 sealed / self-serve checkout B2B | **D intenzionale OFF** | W4 residuo O6 · `503 self_serve_blocked` |

**Nota su A-001 (roadmap 21-Nov):** il roadmap lo classificava ancora come 404 vs deny. Evidenza **successiva** D7 T3 e unit `test_fix04_*` mostrano deny esplicito `collaboration_not_active`. Classificazione aggiornata: **non** è il prossimo blocco operativo quotidiano (residuo di messaging storico, non gap prodotto attuale).

### 1.4 Cosa resta aperto (rilevante GTM / operatività)

| Item | Classe | Impatto quotidiano agenzia |
|------|--------|----------------------------|
| Dogfood Product Acceptance J1–J9 su Nicastro prod | **NV** (Founder) | Alto — ma è collaudo Founder, non gate Cursor di codice |
| H4 sealed / self-serve | **R** finché Founder non autorizza | Alto commerciale; **non** sblocca CRM quotidiano se crediti già assegnabili ops |
| TOOL-08 / `llm_busy` HAL | **PD** parziale (E2E storico) | Medio reputazione AI; CRM base resta usabile |
| Catalog/SoT drift DF-F05/F10/F11 | Docs | Basso operativo |
| **UI percorso Collab→Visita→Deal** | **I + VS** (locale + staging API/FE browser PASS) | Operativo su staging; merge #245 = decisione Founder |

---

## 2. Valutazione dei sette flussi (priorità rischio)

Scala: impatto quotidiano × rischio dati/trattativa × distanza implementazione↔verifica UX.

| # | Flusso | Giudizio sintetico | Priorità relativa |
|---|--------|--------------------|-------------------|
| 1 | Org / filiali / authz | Solido su staging (W3/W4/D7 T4). Residui fixture A-003 = collaudi, non prodotto Nicastro. | Bassa |
| 2 | Immobili / incarichi / docs | Lista/API hardenati (S1). Fascicolo/modulistica esistono. Gap dogfood prod. | Media |
| 3 | Clienti / richieste / matching | Flussi P0 con CTA e typeahead (J4/J7). Unit match presenti. Meno “muro UUID”. | Media |
| 4 | Visite + collaborazione MLS | **API VS**; **FE debole** (visite con `proposed_slots: []`, etichette = id). | **Alta** |
| 5 | Trattative / Deal | **API VS**; **FE = form UUID** (property/client/visit/collab). Blocca chiusura commerciale quotidiana. | **Massima** |
| 6 | Billing / crediti / sospensione | Wallet deep chiuso D-193. Self-serve OFF voluto. Sospensione/lifecycle = verifiche medie. | Bassa (post-D-193) per CRM day-to-day |
| 7 | Notifiche / comunicazioni / documenti | L5 staging PASS (kill). Email reale fuori scope. Chat collab API OK; UI chat legata a collab. | Media-bassa |

**Conclusione sezione 2:** il rischio più alto per “agenzia reale ogni giorno” non è l’assenza di endpoint, ma l’**inutilizzabilità del percorso commerciale MLS in UI** nonostante backend verificato. Un agente non può chiudere una trattativa collaborativa senza copiare UUID: viola i gate S/C/R/A/F della Product Acceptance Matrix (relazione e azione evidenti).

---

## 3. Gate prioritario scelto

### Nome

**CMJ — Commercial MLS Journey Operability**  
*(Percorso commerciale MLS operativo: Collaborazione → Visita → Mini-dossier → Deal → Proposta / risposta partner / Chat)*

### Motivazione (perché prima degli altri)

1. **Impatto quotidiano:** è il ciclo che produce (o perde) una trattativa tra agenzie — cuore differenziante OMNIA rispetto a un CRUD immobili.  
2. **Rischio dati:** form a UUID → alto rischio di Deal collegato a immobile/cliente sbagliato (corruzione relazione CRM).  
3. **Blocco commerciale:** senza UI usabile, la collaborazione MLS resta “demo API”, non lavoro di agenzia.  
4. **Dipendenze:** non dipende da H4, Stripe Live, merge #244, né da D-193. Backend e auth già pronti.  
5. **Copertura test:** unit/API forti; **browser E2E del journey assente** (D7 T3: “UI Deal/chat non eseguita”).  
6. **Distanza I↔verifica:** implementazione dichiarata ≠ comportamento operativo FE (contrastare con Attività, che ha già `EntitySearch`).

### Cosa non è

- Non è riaprire D-193 / PR #244.  
- Non è “mettere più test a caso”.  
- Non è H4 sealed (serve decisione Founder distinta).  
- Non è solo fix A-001 (già deny 400 attestato).

---

## 4. Approfondimento CMJ

### 4.1 Comportamento atteso (decisioni Founder / SoT)

| Aspetto | Atteso | Fonte |
|---------|--------|-------|
| Collaborazione MLS accept/revoke | Stati e deny mutazioni Deal post-revoca | PR #240 · FIX-04 · D7 T3 |
| Visite con slot | Proposta/gestione slot; complete → feedback | `collaborations.py` VisitCreate |
| Mini-dossier post-visita | Feedback strutturato | D7 T3 |
| Deal | Open → proposal_prepared → proposal_sent → partner respond | `deals.py` · W4-13 |
| Chat contestuale | Isolata alla collab | FIX-09 · D7 T3 |
| UX | Prima / azione / passo successivo evidenti; relazioni cliente↔immobile senza UUID | `PRODUCT_ACCEPTANCE_MATRIX` gate S/C/R/A/F |

### 4.2 Implementazione effettiva

| Layer | Stato | Note |
|-------|-------|------|
| BE `collaborations.py` | **I** | visite, feedback, document-requests, chat, respond/revoke |
| BE `deals.py` | **I** | proposals, send, partner-respond, `_assert_deal_collab_still_active` |
| FE `CollaborationsPage.jsx` | **I incompleto** | `requestVisit` invia `proposed_slots: []`; mostra `Immobile {property_id}` |
| FE `DealsPage.jsx` | **I incompleto** | input testo obbligatori `property_id` / `client_id` (placeholder UUID); visit/collab opzionali come stringhe |
| FE `ActivitiesPage.jsx` | **I migliore** | `EntitySearch` typeahead client/property — **pattern da riusare**, non presente in Deal |
| Route | `app/collaborations`, `app/deals` | `App.js` |

### 4.3 Endpoint principali

| Metodo | Path | Ruolo CMJ |
|--------|------|-----------|
| GET/POST | `/api/app/collaborations` (+ `/respond`) | ciclo collab |
| GET/POST/PATCH | `/api/app/visits` | visite |
| POST | `/api/app/visit-feedback` | mini-dossier |
| GET/POST | `/api/app/deals` | open deal |
| POST | `/api/app/deals/{id}/proposals` | prepara proposta |
| POST | `/api/app/deals/{id}/send-proposal` | invia |
| POST | `/api/app/deals/{id}/partner-respond` | partner |
| Chat | thread/messaggi collab | comunicazione |

### 4.4 Modelli / collection

`collaborations`, `visits`, `visit_feedback`, `document_requests`, `deals` (proposals embedded), chat threads/messages, `properties`, `clients`, `agencies`.

### 4.5 Autorizzazioni / isolamento

| Controllo | Stato |
|-----------|-------|
| Ruoli agency_admin/agent su Deal | **I** |
| Owner vs partner transitions | **I** (`allowed_transitions`) |
| Deny post-revoke | **VS** D7 T3 + unit FIX-04 |
| Chat isolation cross-agency | **VS** D7 T3 403 |
| Outsider MLS authz | unit `test_w3_deals_mls_outsider_authz.py` **VL** |

### 4.6 Test esistenti (attestati, non rieseguiti qui)

| Suite | Cosa copre |
|-------|------------|
| `test_d175_pr240_remediation.py` | FIX collab/deal incl. `collaboration_not_active` |
| `test_d175_deal_collab_chat.py` | chat/deal |
| `test_d175_collab_api_handlers.py` | handler |
| `test_w3_deals_mls_outsider_authz.py` | outsider |
| D7 T3 / W4-13 | HTTP staging sintetico |

**Non coperto:** browser E2E “agente apre Deal scegliendo cliente/immobile per nome”; UI slot visita; regressione typeahead; continuità visita completata → Deal precompilato con etichette.

### 4.7 Difetti dimostrabili (solo ispezione codice + rapporti — nessuna mutate)

| ID | Difetto | Riproduzione (read-only) | Causa tecnica |
|----|---------|--------------------------|---------------|
| **CMJ-01** | Apertura Deal richiede UUID grezzi | Aprire `/it/app/deals`: form `placeholder="Immobile (property_id)"` / `client_id` | FE senza typeahead; non riusa `EntitySearch` di Attività |
| **CMJ-02** | Richiesta visita senza slot | `CollaborationsPage.requestVisit` → `proposed_slots: []` | UI non espone date/orari; API accetta lista vuota |
| **CMJ-03** | Etichette collab = id | Lista collab: testo `Immobile {c.property_id}` | Manca resolve titolo/cliente in FE |
| **CMJ-04** | Journey UI non attestato | D7 T3 §6.6: copertura UI non eseguita | Gap di verifica, non di endpoint |

**Non dichiarato come bug runtime nuovo** senza riesecuzione HTTP in questo mandato.

### 4.8 Flusso E2E concreto (lavoro reale agenzia)

> Agenzia A condivide immobile MLS con Agenzia B. B propone visita con 2–3 slot. A conferma uno slot. B completa visita e lascia mini-dossier. A apre Deal collegato a cliente acquirente (cercato per nome) + visita + collab. A prepara e invia proposta. B accetta/contropropone in UI. Chat resta nel contesto. Se A revoca collab, nuove proposte sono negate con messaggio chiaro.

Questo è il percorso da certificare (API già quasi lì; UI no).

### 4.9 Dipendenze tecniche

- Pattern `EntitySearch` già in `ActivitiesPage.jsx` (estrarre/condividere).  
- API clients/properties search (`q=`) già usate.  
- Staging: stessi host W4 (`omnia-api-staging`, FE staging) — **senza** toccare #244.  
- Fixture sintetiche dual-tenant (stile D7), non dati Nicastro prod.

---

## 5. Proposta operativa ciclo successivo (prompt-ready)

### 5.1 Nome e obiettivo

**Gate CMJ — Percorso commerciale MLS operativo**  
Obiettivo: rendere usabile e verificabile end-to-end (API + browser staging) il ciclo Collaborazione → Visita con slot → Mini-dossier → Deal → Proposta/risposta partner, senza UUID manuali.

### 5.2 Motivazione priorità

Vedi §3. Riduce il rischio operativo #1 residuo post D-193/W4: **trattativa collaborativa non eseguibile da utente reale**.

### 5.3 File / componenti previsti (stima perimetro)

| Area | Path probabili |
|------|----------------|
| FE Deal | `frontend/src/apps/immoweb/pages/DealsPage.jsx` |
| FE Collab/Visite | `frontend/src/apps/immoweb/pages/CollaborationsPage.jsx` |
| FE shared search | estrarre `EntitySearch` da `ActivitiesPage.jsx` → componente condiviso |
| BE (solo se gap) | `collaborations.py` / `deals.py` — **solo se** emerge difetto runtime; default = FE |
| Test | nuovi test FE + eventuale estensione API; **non** indebolire FIX-04 |
| Report | nuovo `OMNIA-CMJ-*-REPORT.md` (ciclo implementazione) |

### 5.4 Difetti dimostrati e rischi da verificare

- Dimostrati: CMJ-01…04 (§4.7).  
- Da verificare in implementazione: validazione BE su `proposed_slots` vuoti (oggi accettati); prefill Deal da query params con resolve label; partner UI su secondo utente.

### 5.5 Correzioni tecniche previste

1. Typeahead immobile + cliente su form Deal (riuso EntitySearch).  
2. UI slot visita (almeno 1–3 datetime) prima di POST `/visits`.  
3. Resolve titoli/nomi in liste collab/visite/deal.  
4. CTA continuità: da visita `completed` → “Apri Deal” con `visit_id`/`property_id`/`collaboration_id` precompilati **e** label.  
5. Test regressione FE + smoke API deny post-revoke invariato.  
6. Staging browser dual-login A/B sul percorso §4.8.

### 5.6 Test di regressione necessari

- Unit esistenti PR #240 / W3 outsider — devono restare PASS.  
- Nuovi: EntitySearch su Deal; reject UI senza cliente/immobile selezionato; visit con slot non vuoto (FE).  
- Opzionale BE: policy su `proposed_slots` min length (solo se Founder conferma — altrimenti FE-only).

### 5.7 Verifiche E2E locali

- Due agenzie sintetiche locali o FakeDB+HTTP: collab → visit+slot → feedback → deal (pick typeahead) → proposal → partner respond.  
- Screenshot/video walkthrough.

### 5.8 Verifiche staging necessarie

- Solo `omnia-api-staging` + FE staging (come W4).  
- Dati sintetici `cmj-*` / `@example.com`.  
- Nessuna email reale; Stripe non richiesto.  
- Cleanup solo documenti di sessione.

### 5.9 Dipendenze e autorizzazioni mancanti

| Serve | Perché |
|-------|--------|
| `OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE` con scope **CMJ FE (+ BE solo se difetto runtime)** | Regola D-175 / ruoli governance |
| Autorizzazione staging (come D-193) se si vuole deploy+browser deep | Deploy non incluso in sola implementazione locale |
| **Non** serve: merge #244, H4, Stripe Live, decisione funzionale nuova sul modello Deal |

**Domanda Founder (solo se in implementazione si vuole vincolo BE):**  
«Le visite MLS devono rifiutare `proposed_slots` vuoti a livello API (fail-closed), o basta obbligo UI?»  
Motivo: oggi l’API accetta lista vuota — non c’è decisione esplicita in DECISIONS.md sul minimo slot.

### 5.10 Criteri PASS/FAIL oggettivi

| Criterio | PASS | FAIL |
|----------|------|------|
| Aprire Deal | Selezione cliente+immobile per nome (typeahead), zero UUID digitati | Form richiede UUID |
| Visita | ≥3 slot datetime FE+BE; BE reject &lt;3 | `proposed_slots: []` dall’UI |
| Continuità | Da visita completed → Deal con campi precompilati + label | Solo link con id grezzi |
| Partner | Accetta/rifiuta/controproposta in UI su Deal inviato | Solo API |
| Regressione | FIX-04 / D7 deny post-revoke invariati | 2xx su proposal post-revoke |
| Staging browser (se autorizzato) | Percorso §4.8 dual-tenant con evidenze | Solo unit locale |
| Fuori scope | Nessuna modifica #244/D-193/prod | Touch non autorizzati |

---

## 6. Confronto con alternative scartate

| Alternativa | Perché non prima |
|-------------|------------------|
| H4 / self-serve | Decisione Founder; non sblocca CRM day-to-day se crediti assegnabili |
| TOOL-08 HAL | Reputazione AI; non blocca trattativa |
| Solo ri-E2E S1 A-006/A-007 | Verifica utile ma codice già in main; minore impatto “usabilità quotidiana” vs CMJ |
| Fixture A-003 | Qualità collaudi, non UX Nicastro |
| Deep matching | UI già più matura; meno differenziante MLS |
| Riaprire D-193 / merge #244 | Esplicitamente fuori perimetro |

---

## 7. Chiusura — risposta Founder

| Domanda | Risposta |
|---------|----------|
| **Gate prioritario** | **CMJ — Percorso commerciale MLS operativo** |
| **CMJ locale** | **PASS** — `OMNIA-CMJ-IMPLEMENTATION-REPORT.md` |
| **PROMOZIONE CMJ** | **PASS** — PR #245 @ `d34860c`, CI green |
| **STAGING-DEEP CMJ** | **PASS** — `OMNIA-CMJ-PROMOTION-STAGING-REPORT.md` |
| **Già funzionante (locale + staging)** | EntitySearch Deal; visite ≥3 slot FE+BE; label; CTA visita→Deal; proposal/chat/revoke |
| **Cosa manca ancora** | Merge #245 (decisione Founder); email 24h reale = fuori policy staging |
| **Autorizzazioni** | Implementazione + promozione + staging-deep **eseguite**; **non** merge #244/#245 |

PR #244 resta OPEN / intatta.

---

*Fine `OMNIA-NEXT-CRITICAL-FUNCTIONAL-GATE.md`*
