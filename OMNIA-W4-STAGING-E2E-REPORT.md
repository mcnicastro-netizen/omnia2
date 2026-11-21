# OMNIA — W4 Staging E2E Verification Report

**Data (Europe/Rome):** 2026-11-21 21:19 CET  
**Autorizzazione:** Founder 21-Nov-2026 — staging remoto + deploy staging se necessario  
**Verdetto complessivo:** **B — W4 STAGING E2E NON SUPERATO**

W4 non certifica GTM e non autorizza campagne commerciali o stress successivi.

---

## 0. Sintesi esecutiva

È stato identificato e usato lo staging dedicato (`omnia-api-staging` + `omnia-frontend-staging`), **non** la produzione (`omnia-api` / `api.omniarealestateecosystem.it`).

Il working tree locale conteneva il gate W3/B14 **non committato**. È stato isolato, committato e deployato solo su staging:

| Voce | Valore |
|------|--------|
| Branch lavoro | `cursor/w4-staging-e2e-b894` |
| HEAD finale | `3f34c5f2d6ae5eedcbe6a175e47f57ef87b3fc36` |
| Deploy staging (invite fix) | `deploy-invite-fix (see artifacts w4/railway_up3.txt)` (SUCCESS, health OK) |
| Deploy precedente W3 | `deploy-W3-session (see artifacts w4/railway_up.txt)` |
| FE Vercel | `Vercel dpl staging (API list)` · SHA `15b1978` (**più vecchio del BE**) |

**Blocchi meccanici al verdetto A:** repliche API impossibili con volume allegato; L5 senza Resend; Stripe Test non configurato; fail-closed sessione non provocabile in sicurezza; FE non riallineato al BE; alcuni flussi visita/trattativa non eseguiti end-to-end.

**Correzione locale in ciclo:** `agency_invites` in tenant guard rompeva `/invites/accept` pubblico (500 `tenant_context_required`) → fix `Database.get_raw()` + redeploy staging → accept/remove PASS.

---

## 1. Identità della versione (obbligatoria)

### 1.1 Locale

| Campo | Valore |
|-------|--------|
| Branch iniziale | `cursor/staging-e2e-d1d3-b894` @ `ea89714` |
| Branch W4 | `cursor/w4-staging-e2e-b894` |
| HEAD finale | `3f34c5f2d6ae5eedcbe6a175e47f57ef87b3fc36` |
| Working tree | ancora sporco (~31 path non nel commit W4: report D175 storici, ecc.) — **preservato**, non in deploy |
| W3 session code pre-W4 | **solo working tree** (non in `ea89714`) |

### 1.2 Remoto GitHub

| Ref | SHA |
|-----|-----|
| `origin/main` | `15b1978c63ccb90bddf4a5ea07b668709846ba8b` |
| `origin/cursor/w4-staging-e2e-b894` | `3f34c5f2d6ae5eedcbe6a175e47f57ef87b3fc36` |

### 1.3 Staging servito

| Servizio | Identità |
|----------|----------|
| Railway project | `omnia-api-staging` · ``CANONICAL_RAILWAY_PROJECT_ID` (scripts/d7_e2e/config.py)` |
| Environment | `production` **dentro** progetto staging (nome vendor; non = prod) |
| API URL | `https://omnia-api-production-85845f42.up.railway.app` |
| DB | `omnia_staging_e2e` · Mongo `mongodb-fk03` · proxy TCP `sakura.proxy.rlwy.net:46223` |
| Health post-deploy | `instance_id` + `resend_kill` presenti (codice W3) |
| Vercel project | `omnia-frontend-staging` |
| FE URL | `https://omnia-frontend-staging.vercel.app` |
| FE bake API | stesso host staging sopra |
| FE commit | `15b1978` ≠ BE `3f34c5f` |

### 1.4 Soft-guard produzione

| Controllo | Esito |
|-----------|-------|
| Vault `OMNIA_API_PUBLIC_URL` / `RAILWAY_PROJECT_ID` | puntano a **produzione** — **non usati** per deploy |
| Deploy CLI link | forzato a `omnia-api-staging` |
| Health prod `api.omniarealestateecosystem.it` | letto in sola lettura per contrasto (niente `instance_id`) — **nessuna mutazione prod** |

### 1.5 Operazioni remote eseguite

1. Link Railway → `omnia-api-staging`  
2. `railway up` deploy codice W3 (`f7e57bbc…`)  
3. Tentativo `railway scale us-east=2` → **FAILED**: *Replicas are not supported if you have a volume attached*  
4. Scale back `us-east=1`  
5. Redeploy invite fix (`804e63dd…` / health OK)  
6. Lettura variabili staging (nomi); Mongo via TCP proxy; seed password sintetiche utenti `@example.com`  
7. Toggle `provider_flags` resend kill (ripristinato `killed=false` a fine prova)  
8. Nessun deploy Vercel FE; nessun touch progetto `omnia-api` prod; Stripe Live non toccato; nessuna email reale

---

## 2. Riconciliazione cronologica W3 (punto 4 mandato)

| Documento | Timestamp dichiarato | Ordine reale |
|-----------|----------------------|--------------|
| `OMNIA-W3-STAGING-READINESS-REPORT.md` | header originario «21:45 CET» poi annotato aggiornato post-gate | Ciclo **precedente** al Session Gate |
| `OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md` | **20:56 CET** | Ciclo **successivo** (B14) |

**Rettifica (2026-11-21 21:10 CET):** la label «21:45 CET» sul readiness **non** indica un evento dopo il gate 20:56; è il timestamp documentale del ciclo readiness, cronologicamente anteriore. Entrambi i file sono stati annotati (sezione / blockquote rettifica) **senza** riscrivere i risultati tecnici. Mtime file ~20:57 CET (UTC 19:57) riflette il salvataggio congiunto post-gate.

---

## 3. Anomalie e correzioni

| ID | Osservato | Causa | Gravità | Correzione | Regressione |
|----|-----------|-------|---------|------------|-------------|
| A1 | `/invites/accept` → 500 | `agency_invites` in `TENANT_COLLECTIONS` + `Database.get()` senza ctx | ALTA | `get_raw()` su verify/accept · commit `3f34c5f` · redeploy staging | accept 200; remove member session clear |
| A2 | Scale 2 repliche FAILED | Volume `/app/.media` incompatibile con replicas Railway | ALTA (W4-02/06) | Scale back a 1; **non** rimosso volume (distruttivo) | — |
| A3 | FE SHA ≠ BE | FE non ridistribuito in questo ciclo | MEDIA | Documentato; FE resta `15b1978` | — |
| A4 | Stripe/L5 | `STRIPE_ENABLED=false`; no `RESEND_API_KEY` su API staging | ALTA (W4-19/21/22) | Nessun bypass; BLOCKED | — |

---

## 4. Matrice obbligatoria test–evidenza–verdetto

Legenda esiti: `PASS` | `FAIL` | `BLOCKED` | `NOT RUN`  
Ambiente: **STAGING** salvo dove indicato LOCAL.

| ID | Area | Scenario eseguito | Ambiente | URL / replica | Timestamp (CET) | Versione | HTTP / esito app | Evidenza | Esito | Anomalia / nota |
|----|------|-------------------|----------|---------------|-----------------|----------|------------------|----------|-------|-----------------|
| W4-01 | Versione | Confronto locale/remoto/servito | STAGING+LOCAL | API staging + Vercel API | 21:07–21:19 | BE `3f34c5f` / deploy `804e63dd…`; FE `15b1978` | Health con `instance_id`+`resend_kill` | questo §1; `/opt/cursor/artifacts/w4/health_post_deploy.json` | **PASS** | FE non allineato (vedi W4-03 nota) |
| W4-02 | Railway | Health + diversity `instance_id` | STAGING | 1 istanza RUNNING | 21:10–21:17 | `f7e57bbc`→scale fail→`804e63dd` | 1 solo `instance_id` su 100 hit | `instance_id_diversity*.json`; scale fail log | **FAIL** | Volume blocca replicas |
| W4-03 | Vercel | FE ready + bake API | STAGING | `omnia-frontend-staging.vercel.app` | 21:06 | `15b1978` / `dpl_57GeNseE…` | 200; JS punta API staging | Vercel API dump | **PASS** | SHA FE ≠ BE — residuo |
| W4-04 | Cookie/CORS | Set-Cookie Secure/SameSite=None; CORS preflight FE | STAGING | API←FE origin | 21:12 | post-deploy W3 | cookies `access_token`/`refresh_token`/`omnia_csrf`; ACAO ok | `http/set_cookie.json` | **PASS** | Browser GUI non registrato (HTTP sufficiente per attributi) |
| W4-05 | Login/refresh | Login A, `/me`, refresh cookie | STAGING | API | 21:12 | W3 session | 200/200/200; claims `sid`/`sv` | `http/login_a.json`, `me_a.json`, `refresh.json` | **PASS** | — |
| W4-06 | Revoca cross-replica | Logout + Mongo revoke + reuse access su hit multipli LB | STAGING | **1 replica** | 21:12–21:14 | W3 | 401 immediato post-logout e post-Mongo revoke | `reuse_after_logout.json`; round2 | **BLOCKED** | Criterio «replica B» non dimostrabile (A2) |
| W4-07 | Logout/sospensione | logout, logout-all+CSRF, dual session, suspend | STAGING | API | 21:13–21:15 | W3 | logout 200; logout-all 200; access 401×2; suspend login 403 | round2 | **PASS** | — |
| W4-08 | Fail-closed sessioni | Indisponibilità controllata Mongo | — | — | — | — | non eseguito | — | **BLOCKED** | Evitato: rischio staging; cover LOCAL unit |
| W4-09 | Tenant isolation | B legge props A; nuova prop cross-get | STAGING | API | 21:12–21:15 | W3 | 403/404 | matrix_partial; round3 | **PASS** | — |
| W4-10 | CommercialCustomer | Doc CC + wallet B deny | STAGING | Mongo+API | 21:15 | — | CC present; wallet 403 `not_main_admin` | round3 | **PASS** | — |
| W4-11 | Inviti/membership | create→verify→accept→remove | STAGING | API | 21:18 post-fix | `3f34c5f` | 201/200/200/200; sessions cleared | `invite_accept_after_fix.json` | **PASS** | A1 corretto in ciclo |
| W4-12 | Immobili/incarichi | list/create/get + activity | STAGING | API | 21:15 | W3 | 200/201/200/201 | round3 | **PASS** | — |
| W4-13 | Visite/trattative | slot visita / avanzamento trattativa | STAGING | — | — | — | — | — | **NOT RUN** | Tempo/scope; deal MLS partner già visto |
| W4-14 | Deal | B partner su deal A | STAGING | API | 21:14 | — | 200 atteso (partner=`d7-ag-b`) | round2 | **PASS** | Non outsider |
| W4-15 | MLS | GET partners | STAGING | API | 21:15 | — | 200 `items:[]` | round3 | **PASS** | Flusso collab completo parziale |
| W4-16 | Documenti/chat | chat outsider | STAGING | API | 21:16–21:18 | — | 403 `chat_revoked` | round4/5 + retry | **PASS** | docs inventory BLOCKED (no docs) |
| W4-17 | Wallet/crediti | wallet B | STAGING | API | 21:13 | — | 403 | round2 | **PASS** | flussi allocate non rieseguiti |
| W4-18 | B8 | `provider_flags` id=resend kill→health | STAGING | Mongo+API | 21:14 | W3 health | `resend_kill.killed=true` poi clear | `b8_health_*.json` | **PASS** | Persistenza restart processo **non** (no restart); multi-replica N/A |
| W4-19 | L5 | prova email staging | STAGING | — | 21:15 | — | no RESEND key | round3 | **BLOCKED** | Zero invii reali |
| W4-20 | T22 | marker A/B cleanup A only su Mongo staging | STAGING | Mongo reale | 21:15 | — | B intact; residual A=0 | round3 | **PASS** | Marker dedicati (non full MLS inventory D7) |
| W4-21 | Stripe checkout | plans / config | STAGING | API | 21:13 | — | `STRIPE_ENABLED=false` | round2 | **BLOCKED** | — |
| W4-22 | Stripe webhook | POST webhook | STAGING | API | 21:15 | — | 503 `stripe_not_configured` | round3 | **BLOCKED** | — |
| W4-23 | Regressione | pytest session/MP/slice1 locale | LOCAL | — | 21:16 | `3f34c5f` tree | 16 passed, 12 skipped | `local_regression.txt` | **PASS** | — |
| W4-24 | Integrità dati | inventory before/after | STAGING | Mongo | 21:07→21:19 | — | fixtures d7 preservate; solo tag sintetici | `mongo_inventory_*.json` | **PASS** | — |

### 4.1 Sintesi aggregata (meccanica)

| Esito | Conteggio (righe W4-01…24) |
|-------|----------------------------|
| PASS | 16 |
| FAIL | 1 (W4-02) |
| BLOCKED | 5 (W4-06, W4-08, W4-19, W4-21, W4-22) |
| NOT RUN | 1 (W4-13) |
| Escluse | 0 |

**Requisiti bloccanti residui:** W4-02, W4-06 (cross-replica), W4-08, W4-19, W4-21, W4-22, W4-13; allineamento FE.

**Verdetto derivato:** qualsiasi FAIL/BLOCKED/NOT RUN obbligatorio → **B**.

---

## 5. Evidenze B8 / L5 / T22

### B8
- SoT Mongo `provider_flags` `{id:"resend", killed:true}` → health `resend_kill.killed=true` (cache ~2s).  
- Ripristinato `killed=false` a fine ciclo.  
- Multi-replica / post-restart infrastrutturale: **non** attestabile (1 replica + volume).

### L5
- **BLOCKED:** nessuna `RESEND_API_KEY` sulle variables del servizio API staging; nessun invio; skeleton locale `scripts/d7_e2e/l5_evidence.py` non riempito con provider remoto.

### T22
- Eseguito su Mongo staging reale con collection marker `w4_t22_markers`: cleanup run A non muta B.  
- Non equivale all’inventario MLS completo del contratto D7, ma dimostra isolamento cleanup su infra reale.

---

## 6. Stripe Test

| Controllo | Esito |
|-----------|-------|
| `STRIPE_ENABLED` | `false` |
| Secret/webhook su servizio | assenti dalle variables elencate |
| Checkout | non eseguibile |
| Webhook | 503 `stripe_not_configured` |

Nessuna modifica Stripe Live.

---

## 7. Regressione locale

```text
pytest tests/test_w3_session_revocation_final.py \
       tests/test_w3_multiprocess_local.py \
       tests/test_slice1_b01_b03.py \
       tests/test_mc042_r01_refresh_cease.py -q
→ 16 passed, 12 skipped
```

Artefatto: `/opt/cursor/artifacts/w4/local_regression.txt`

---

## 8. Limiti residui

1. **Replica API:** volume media → Railway rifiuta `numReplicas>1`. W4-02/06 incompleti.  
2. **FE staging** fermo a `15b1978` mentre BE è `3f34c5f`.  
3. **Resend / L5** non configurati sullo staging API.  
4. **Stripe Test** disabilitato.  
5. **Visite/trattative E2E** non corrati.  
6. **Fail-closed Mongo** non provocato su staging.  
7. Working tree locale ancora con MD D175 storici non committati (intenzionale).

---

## 9. Conferme operative

- Nessun accesso mutativo a produzione  
- Nessun deploy produzione  
- Nessuna email reale  
- Solo dati `@example.com` / tag `w4_synthetic` / `w4syn-*`  
- Nessuno stress/load  
- Nessun reset/stash/clean del working tree  
- Commit/push solo branch `cursor/w4-staging-e2e-b894` (codice W4 necessario)  
- Deploy solo progetto `omnia-api-staging`

---

## 10. VERDETTO

### **B — W4 STAGING E2E NON SUPERATO**

Motivazione meccanica: FAIL W4-02; BLOCKED W4-06/08/19/21/22; NOT RUN W4-13.  
Avanzamenti reali: BE staging aggiornato con B14; invalidazione sessione dimostrata su staging; invite accept riparato; isolamento tenant/HTTP positivo su percorsi collaudati; T22 marker su Mongo reale; B8 kill flag visibile in health.

**Prossimi passi suggeriti (richiedono mandato):** rimuovere o ripensare volume per ≥2 repliche; aggiungere Resend+Stripe Test variables staging; redeploy FE pin=`3f34c5f`; completare visite/trattativa/L5.
