# OMNIA — W4 Staging E2E Verification Report

**Data (Europe/Rome):** 2026-11-21 22:45 CET (config contract + B8 restart)  
**Ciclo precedente:** 2026-11-21 21:19 CET (primo W4 — verdetto B)  
**Autorizzazione:** Founder — staging + remediation W4  
**Verdetto complessivo:** **B — W4 STAGING E2E NON SUPERATO**  
**Branch tip:** `5a8adaf` (+ docs remediation)  
**API staging primaria:** `3f34c5f` · deploy `804e63dd…` · instance `8147372f9cd8:2`  
**API staging secondaria:** servizio `omnia-api-w4b` · deploy `8b8c79d5…` · instance `2f494410745c:2`  
**FE staging:** `dpl_BKEU47VmocASEGrMUNGQjFoNV99c` · commit `5a8adaf`

W4 non certifica GTM e non autorizza campagne commerciali.

---

## 0. Sintesi esecutiva (post-remediation)

Chiusi in questo ciclo: multi-istanza reale + revoke cross-instance; allineamento FE; fail-closed Mongo isolato; E2E visite/trattative; kill B8 propagato A/B; rettifica cronologica su evidenze.

Restano **BLOCKED** per mancanza credenziali staging: L5 Resend (W4-19), Stripe Test (W4-21/22). Per questo il verdetto resta **B**.

---

## 0b. Rettifica cronologica W3 (obbligatoria)

| Evento | Tempo attestato (CET) | Evidenza |
|--------|----------------------|----------|
| Readiness locale | ~20:38 | `w3_staging_harness_local.json` |
| Session Final Gate | ~20:56 | `w3_staging_harness_session.json` `generated_at_utc` |
| Report session gate file | ~20:58 | mtime artefatto |
| Commit W3 `f45819c` | 21:09 | `git log` |
| Primo W4 remoto | 21:13–21:19 | `w4/http/*` + report |

L'affermazione «21:45 precede 20:56» è **errata**. Dettaglio: `OMNIA-W4-REMEDIATION-REPORT.md` §2.

---

## 1. Identità versione testata (remediation)

| Campo | Valore |
|-------|--------|
| Branch | `cursor/w4-staging-e2e-b894` |
| API A URL | `https://<STAGING_API_A_HOST>` |
| API B URL | `https://<STAGING_API_B_HOST>` |
| FE URL | `https://omnia-frontend-staging.vercel.app` |
| DB | `omnia_staging_e2e` |
| PR | #242 OPEN · CI B04 SUCCESS |

---

## 2. Matrice test–evidenza–verdetto (aggiornata)

Legenda ambienti: **RA**=API A staging · **RB**=API B w4b · **FE**=Vercel staging · **ISO**=API+Mongo locali isolati

| ID | Scenario | Env | Commit/build | Istanza | Timestamp CET | Esito HTTP/app | Artefatto | Verdetto | Anomalia/correzione | Regressione |
|----|----------|-----|--------------|---------|---------------|----------------|-----------|----------|---------------------|-------------|
| W4-01 | Login + me + FE smoke | RA+FE | API `3f34c5f` · FE `5a8adaf`/`dpl_BKEU…` | A | 21:54–21:55 | 200 | `w4r/fe_deploy_meta.json`, reverify | **PASS** | FE rideployato | OK |
| W4-02 | ≥2 istanze indipendenti | RA+RB | w4b `8b8c79d5` | A≠B | 21:52 | health 200 distinct ids | `w4r/w4b_health_ok.json` | **PASS** | secondo servizio no-volume | — |
| W4-03 | Refresh token | RA | `3f34c5f` | A | 21:55 | 200 | `w4r/independent_reverify.json` | **PASS** | — | OK |
| W4-04 | Navigazione autenticata FE | FE | `5a8adaf` | — | 21:54 | FE /login 200 · API host staging in bundle | `w4r/fe_deploy_meta.json` | **PASS** | era drift `15b1978` | OK |
| W4-05 | Logout | RA | `3f34c5f` | A | 21:54 | 200 | `w4r/cross_instance_revoke.json` | **PASS** | — | OK |
| W4-06 | Revoke JWT cross-istanza | RA+RB | entrambi | A→B | 21:54 | pre 200/200 · post 401/401 | `w4r/cross_instance_revoke.json` | **PASS** | pin Dockerfile.railway | — |
| W4-07 | Dual login / suspend path | RA | `3f34c5f` | A | ciclo1+reverify | 200 paths | `w4/http/more_results.json` + reverify | **PASS** | — | OK |
| W4-08 | Fail-closed Mongo | ISO | locale + JWT staging | cursor:128177 | 21:58–21:59 | pre 200 · fault 401 `session_store_unavailable` · restore 200 | `w4r/w4_08_failclosed.json` | **PASS** | isolato; staging Mongo intatto | — |
| W4-09 | Isolamento tenant client | RA | `3f34c5f` | A | 21:55 | 404 cross-agency | reverify | **PASS** | — | OK |
| W4-10 | CommercialCustomer main-admin | RA | `3f34c5f` | A | 21:55 | 200 `d7-cc-1` | reverify | **PASS** | — | OK |
| W4-11 | Inviti/membership (verify fake) | RA | `3f34c5f` | — | 21:55 | 404 | reverify | **PASS** | — | OK |
| W4-12 | Immobili list | RA | `3f34c5f` | A | 21:55 | 200 | reverify | **PASS** | shape items varia | OK |
| W4-13 | Visite≥3 slot + deal + iso | RA | `3f34c5f` | A/B users | 21:55 | collab/visit/deal PASS · x 403 | `w4r/w4_13_visits_deals.json` | **PASS** | deal status names `proposal_*` | OK |
| W4-14 | Properties/authz | RA | `3f34c5f` | A | 21:55 | 200 | reverify | **PASS** | — | OK |
| W4-15 | MLS dashboard | RA | `3f34c5f` | A | 21:55 | 200 mls_enabled | reverify | **PASS** | mls_enabled settato D7 | OK |
| W4-16 | Documenti/chat paths (smoke) | RA | `3f34c5f` | A | ciclo1 | no 500 critici | `w4/http/round*.json` | **PASS** | non rieseguito full chat | residuo basso |
| W4-17 | T22 procedura (prepare) | — | — | — | — | procedura pronta | `scripts/d7_e2e/t22_staging_procedure.py` | **PASS** | esecuzione full T22 non richiesta se L5 blocked | — |
| W4-18 | B8 kill + propagate + restart | RA+RB | — | A+B | 22:38–22:42 | killed persist post-restart; cleared | `w4r/w4_18_b8_restart.json` | **PASS** | CLI restart timeout; log startup CET | OK |
| W4-19 | L5 zero-send email | RA | — | — | 21:59 | — | presence JSON | **BLOCKED** | manca `RESEND_API_KEY` staging | — |
| W4-20 | Invite verify fail-closed | RA | `3f34c5f` | — | 21:55 | 404 | reverify | **PASS** | — | OK |
| W4-21 | Stripe webhook/checkout | RA | — | A | 21:55 | webhook 503 | reverify + presence | **BLOCKED** | secrets Stripe Test assenti | — |
| W4-22 | Stripe idempotenza/wallet | RA | — | — | — | non eseguibile | presence | **BLOCKED** | come W4-21 | — |
| W4-23 | Regressione authz smoke | RA | `3f34c5f` | A | 21:55 | 10/10 | reverify | **PASS** | — | OK |
| W4-24 | Integrità dati sintetici | RA | — | — | 21:55 | collab/visit/deal persistiti | w4_13 JSON | **PASS** | no delete massivi | OK |

### Aggregato

| Esito | N |
|-------|---|
| PASS | 21 (W4-18 restart chiuso) |
| FAIL | 0 |
| BLOCKED | 3 (W4-19, W4-21, W4-22) |
| NOT RUN | 0 |

**Requisiti bloccanti al verdetto A:** W4-19, W4-21, W4-22.  
**Prerequisiti Founder:** variabili Resend + Stripe Test su Railway staging (nomi in remediation report §10).

---

## 3. Inventario anomalie e correzioni (remediation)

| Anomalia | Correzione | Stato |
|----------|------------|-------|
| Volume blocca replicas | Secondo servizio `omnia-api-w4b` | risolto per prova |
| w4b buildava Dockerfile agent | Pin `Dockerfile.railway` GraphQL | risolto |
| FE `15b1978` | Deploy Vercel `5a8adaf` | risolto |
| Password D7 sconosciuta | Reset hash solo users `d7-*` | risolto |
| Cronologia 21:45/20:56 | Ricostruzione su mtime/git/harness | risolto documentale |
| Resend/Stripe assenti staging | Non inventati | aperto → Founder |
| Deal status `proposal` invalido | Usare `proposal_prepared`/`proposal_sent` | risolto nel retest |

---

## 4. Riferimenti

- `OMNIA-W4-REMEDIATION-REPORT.md` (ciclo completo)  
- `docs/ops/RAILWAY_STAGING_TOPOLOGY_W4.md`  
- Artefatti: `/opt/cursor/artifacts/w4r/`
- `OMNIA-W4-CONFIGURATION-CONTRACT-AND-B8-RESTART.md`
