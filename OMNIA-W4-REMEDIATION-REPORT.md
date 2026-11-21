# OMNIA — W4 REMEDIATION REPORT

**Data (Europe/Rome):** 2026-11-21 22:05 CET  
**Autorizzazione:** Founder — ciclo remediation W4, solo staging, perimetro W4 già concesso  
**Branch:** `cursor/w4-staging-e2e-b894`  
**HEAD tip docs remediation:** `4bb9ffa` (su `5a8adaf`)  
**API staging (primaria):** deploy `804e63dd…` · codice tip `3f34c5f`  
**API staging (seconda istanza):** servizio `omnia-api-w4b` · deploy `8b8c79d5…` · `Dockerfile.railway`  
**FE staging:** Vercel `dpl_BKEU47VmocASEGrMUNGQjFoNV99c` · commit `5a8adaf` · API host bundle `<STAGING_API_A_HOST>`  
**Verdetto complessivo:** **B — W4 STAGING E2E NON SUPERATO**

---

## 1. Stato iniziale (rilevato di nuovo, non assunto)

| Voce | Valore rilevato |
|------|-----------------|
| Branch | `cursor/w4-staging-e2e-b894` |
| HEAD | `5a8adaf930dd197f932de4860bd8fa3d909e8460` |
| Working tree | Preservato (molti MD D-175 untracked + docs pre-gtm) — **nessun reset/stash/clean** |
| PR #242 | OPEN · CI Backend billing SUCCESS (2 check) |
| API staging | `omnia-api` Online · health OK · instance `8147372f9cd8:2` |
| FE staging pre-ciclo | commit `15b1978` (drift vs BE) |
| Volume | Collegato a `omnia-api` → `numReplicas>1` non supportato |
| Resend su Railway staging | **assente** (`RESEND_API_KEY` non presente) |
| Stripe Test secrets su Railway | **assenti** (solo `STRIPE_ENABLED`) |
| Credenziali demo seed | non valide su staging; usati utenti sintetici D7 dopo reset hash password (solo record `d7-*`) |

---

## 2. Rettifica cronologica (evidenze, non supposizioni)

### Contraddizione segnalata

Il fascicolo W4 precedente affermava, in sostanza, che il ciclo “21:45 CET” (readiness) **precedesse** il Session Gate “20:56 CET” — impossibile nella stessa data/fuso.

### Evidenze originali

| Evidenza | Timestamp (Europe/Rome) | Fonte |
|----------|-------------------------|--------|
| Harness readiness locale | **20:38:43 CET** | mtime `/opt/cursor/artifacts/w3_staging_harness_local.json` · `generated_at_utc=19:38:42Z` |
| Harness session gate | **20:56:30 CET** | `generated_at_utc` in `w3_staging_harness_session.json` = `2026-11-21T19:56:30.272362+00:00` |
| Report Session Final Gate (file) | **20:58:08 CET** | mtime artefatto `OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md` |
| Probe HTTP W4 | **21:13–21:19 CET** | mtime `/opt/cursor/artifacts/w4/http/*` |
| Report W4 (file) | **21:21:35 CET** | mtime `OMNIA-W4-STAGING-E2E-REPORT.md` |
| Commit git `f45819c` (W3 ship) | **21:09:34 CET** | `git log` `2026-11-21T20:09:34+00:00` |

### Sequenza corretta

1. **~20:38 CET** — ciclo Staging Readiness (locale)  
2. **~20:56 CET** — Session Final Gate B14 (locale)  
3. **~21:09 CET** — commit `f45819c` (codice+report W3)  
4. **~21:13–21:19 CET** — primo ciclo W4 staging remoto  

### Su «21:45 CET»

- Nel blob git `f45819c` l’header readiness è già **20:56 CET** con nota di rettifica che *cita* un header originario «21:45 CET».
- **Non** esiste un blob git recuperabile con header letterale `21:45 CET` in questo workspace.
- Nessuna evidenza artefatto attesta un’esecuzione alle 21:45 CET **prima** delle 20:56.
- Conclusione: l’etichetta «21:45» non è attestata come tempo di esecuzione; la sequenza operativa reale è **20:38 → 20:56 → 21:13+**. La frase «il ciclo 21:45 precede 20:56» è **falsa** e va considerata errore documentale.

Inventario JSON: `/opt/cursor/artifacts/w4r/chrono_evidence.json`, `chrono_artifacts_window.json`.

---

## 3. Interventi effettuati

### 3.1 A2 — multi-istanza (W4-02 / W4-06)

- Analisi volume: primario ha `RAILWAY_VOLUME_*`; backend media usa storage locale/volume; sessioni SoT = Mongo (stateless rispetto al volume per auth).
- Creato servizio `omnia-api-w4b` senza volume; env copiate (JWT/Mongo/DB condivisi); `LOCAL_STORAGE_ROOT=/tmp`.
- Primi deploy fallivano: `railway up` costruiva il **Dockerfile Cloud Agent** → container `STOPPED`.
- Fix: `serviceInstanceUpdate` GraphQL con `dockerfilePath=Dockerfile.railway` + healthcheck; redeploy SUCCESS.
- Domain pubblico attivo; health A≠B.
- Prova revoke cross-instance **PASS** (`w4r/cross_instance_revoke.json`).

### 3.2 A3 — FE↔BE (W4-01/03/04)

- CI PR #242 verde.
- Build FE con `REACT_APP_BACKEND_URL` staging; bundle contiene host staging API (0 hit su `api.omniarealestateecosystem.it`).
- Deploy Vercel progetto `omnia-frontend-staging` → `dpl_BKEU47VmocASEGrMUNGQjFoNV99c`, commit `5a8adaf`, alias `omnia-frontend-staging.vercel.app` 200.
- Meta: `w4r/fe_deploy_meta.json`.

### 3.3 A4 — B8 / L5 (W4-18 / W4-19)

- Kill flag Mongo `provider_flags.id=resend` impostato → health A e B `killed=true` (cache TTL 2s) → clear → entrambi `killed=false`.
- **L5 NON eseguito:** su Railway staging mancano `RESEND_API_KEY` (e correlati). Nessun invio, nessuna chiave inventata.
- Evidenza: `w4r/w4_18_b8_kill.json`, `w4r/resend_stripe_presence.json`.

### 3.4 W4-08 fail-closed Mongo

- Istanze isolate locali: mongod effimero + uvicorn con JWT staging, **Mongo Railway non toccato**.
- Login OK → kill mongod → `GET /api/auth/me` → **401** `session_store_unavailable` (~30s) → restore mongod → 200.
- Evidenza: `w4r/w4_08_failclosed.json`.

### 3.5 W4-13 visite / trattative

Flusso E2E sintetico D7:

1. Collab B→A su `d7-prop-complete` → accept  
2. Visit con **3** `proposed_slots` → agree → complete  
3. Deal open + advance `proposal_prepared` → `proposal_sent`  
4. Isolamento: agency inactive 403 su patch visit / get deal; list visits non vede la visita  

IDs: collab `d994e7a5-…`, visit `b5fd5ff4-…`, deal advance `3091955b-…`  
Evidenza: `w4r/w4_13_visits_deals.json`, `w4r/w4_13_deal_advance2.json`.

### 3.6 Stripe (W4-21 / W4-22)

- Railway: presente solo `STRIPE_ENABLED`; assenti `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_MODE`.
- `POST /api/billing/webhook` senza firma → **503** (disabilitato) — **non** è prova di idempotenza.
- Locale ha chiavi Test in `backend/.env` ma **non** sono state propagate su Railway (fuori da “inventare/copiare senza mandato esplicito di config staging”).

### 3.7 Altro

- Reset password hash **solo** utenti sintetici `d7.admin.*@example.com` (nessuna cancellazione dati).
- Enable `mls_enabled` su `d7-ag-active`/`d7-ag-b`; upsert client sintetici `d7-client-w4r-*`.
- Riesecuzione probe indipendenti: 10/10 PASS (`w4r/independent_reverify.json`).

---

## 4. Problemi risolti in questo ciclo

| ID | Problema | Esito |
|----|----------|-------|
| W4-02 / W4-06 | Nessuna prova multi-istanza | **PASS** (servizio w4b + revoke cross-instance) |
| W4-01/03/04 FE drift | FE `15b1978` vs BE | **PASS** (FE `5a8adaf` + API staging host) |
| W4-08 | Fail-closed Mongo non dimostrato | **PASS** (istanza isolata) |
| W4-13 | Visite/trattative NOT RUN | **PASS** (E2E sintetico) |
| W4-18 (parziale) | Kill B8 + propagazione | **PASS** controllo kill + A/B; L5 separato |
| Cronologia | 21:45 vs 20:56 | **Rettificata** su evidenze |
| Deploy w4b | Dockerfile sbagliato | **Risolto** pin `Dockerfile.railway` |

---

## 5. Problemi non risolti e cause

| ID | Stato | Causa precisa | Prossima azione più breve |
|----|-------|---------------|---------------------------|
| W4-19 L5 | **BLOCKED** | Su servizio Railway `omnia-api` **mancano** `RESEND_API_KEY` (+ `SENDER_EMAIL` / from). Config assente, non “invalida”. | Founder: impostare variabili Resend **Test** solo su progetto staging → ripetere L5 zero-send |
| W4-21 / W4-22 | **BLOCKED** | Mancano `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_MODE` su Railway staging; webhook risponde 503 | Founder: Stripe **Test** vars + webhook secret staging → rieseguire checkout/idempotenza |
| W4-18 restart | parziale | Persistenza kill dopo *restart container* non rieseguita (evitato restart distruttivo non necessario) | Opzionale: `railway service restart` primario + w4b con flag killed=true |
| Multi-replica nativa su un solo servizio | non fatta | Volume media blocca `numReplicas` | Migrazione object storage (doc topologia) — decisione Founder |
| Merge PR #242 | non fatto | Fuori autorizzazione | Solo su mandato esplicito |

---

## 6. Modifiche locali e remote

### Locali (repo)

- Report/docs: questo file, aggiornamenti W4/PRE-GTM/topologia, rettifica cronologica.
- Nessuna modifica prodotto runtime oltre a quanto già in branch (`3f34c5f`+).
- Working tree D-175 **conservato**.

### Remote staging

| Azione | Dettaglio |
|--------|-----------|
| Servizio nuovo | `omnia-api-w4b` |
| Deploy API w4b | `8b8c79d5…` Dockerfile.railway |
| Domain | `<STAGING_API_B_HOST>` |
| FE Vercel | `dpl_BKEU47VmocASEGrMUNGQjFoNV99c` |
| Mongo | update password hash D7; mls_enabled; clients sintetici; provider_flags resend toggle (ripristinato killed=false) |
| Produzione | **non toccata** |

---

## 7. CI

PR #242: check `Backend billing / B04 unit` → SUCCESS (×2). Nessun deploy effettuato con CI rossa.

---

## 8. Test e regressioni

| Suite | Esito | Artefatto |
|-------|-------|-----------|
| Cross-instance revoke | PASS | `w4r/cross_instance_revoke.json` |
| FE deploy smoke | PASS | `w4r/fe_deploy_meta.json` |
| W4-08 fail-closed | PASS | `w4r/w4_08_failclosed.json` |
| W4-13 visits/deals | PASS | `w4r/w4_13_visits_deals.json` |
| B8 kill A/B | PASS | `w4r/w4_18_b8_kill.json` |
| Reverify indipendente | 10/10 | `w4r/independent_reverify.json` |
| L5 / Stripe E2E | BLOCKED | presence JSON |

---

## 9. Matrice aggiornata (sintesi)

Vedi `OMNIA-W4-STAGING-E2E-REPORT.md` § matrice completa.

**Aggregato remediation (obbligatori W4-01…24):**

| Esito | Conteggio (indicativo post-ciclo) |
|-------|-----------------------------------|
| PASS | 20 |
| FAIL | 0 |
| BLOCKED | 3 (W4-19, W4-21, W4-22) |
| NOT RUN | 1 (W4-18 sotto-voce restart container — documentato; kill/propagation PASS) |

Requisito bloccante residuo al verdetto A: **L5 + Stripe Test** (credenziali staging assenti).

---

## 10. Prerequisiti ancora necessari (Founder)

Variabili da configurare **solo** su Railway progetto `omnia-api-staging`, servizio `omnia-api` (e mirror su `omnia-api-w4b` se si ripete L5 multi-istanza), **senza** valori in chat:

1. `RESEND_API_KEY`  
2. `SENDER_EMAIL` (o equivalente from già usato dal codice)  
3. `STRIPE_SECRET_KEY` (Test)  
4. `STRIPE_PUBLISHABLE_KEY` (Test)  
5. `STRIPE_WEBHOOK_SECRET` (Test, endpoint staging)  
6. `STRIPE_MODE=test` (se richiesto dal codice)

Poi: rieseguire L5 zero-send + suite Stripe idempotenza.

---

## 11. Prossima azione concreta (più breve)

1. Founder inserisce le 6 variabili Test sopra nel progetto staging.  
2. Agent ripete **solo** W4-19 + W4-21/22 su staging.  
3. Se PASS → riesame verdetto A; altrimenti resta B con evidenze aggiornate.

---

## 12. Verdetto

**B — W4 STAGING E2E NON SUPERATO**

Motivo: requisiti obbligatori ancora BLOCKED (L5 email, Stripe Test).  
Non si forza A. I blocchi infrastrutturali risolvibili (repliche via secondo servizio, FE align, fail-closed isolato, visite/deal) sono chiusi con evidenze.
