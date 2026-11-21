# OMNIA — W3 Staging Readiness: Global Hardening, Remediation & Local Certification

**Data (Europe/Rome):** 2026-11-21 20:56 CET (aggiornato post session gate)  
**Branch iniziale/finale:** `cursor/staging-e2e-d1d3-b894`  
**HEAD iniziale/finale:** `ea89714dfee65ca592e413db551d1506b573049a` (**nessun commit**)  
**Precedenti:** `OMNIA-W3-TENANT-GUARD-E2E-VERIFICATION.md` · `OMNIA-W3-SECONDARY-ACCESS-PATHS-HARDENING.md` · `OMNIA-W3-RESIDUAL-IDOR-CLOSURE.md`  
**Follow-up obbligatorio (chiuso):** `OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md` — invalidazione immediata access JWT (B14)  
**Vincoli rispettati:** nessun reset/stash/clean · nessun commit/push/merge/deploy · nessun accesso Railway/Vercel/Mongo remoto/Resend/Stripe live · nessuna email reale

---
> **Rettifica cronologica (W4 · 2026-11-21 21:10 CET):** l’header originario «21:45 CET» appartiene al ciclo Staging Readiness (prima del Session Final Gate). Il gate B14 è stato completato alle **20:56 CET** dello stesso giorno; l’annotazione «aggiornato post session gate» su questo file è stata applicata ~20:56–20:57 CET. Nessun risultato del readiness è stato alterato retroattivamente — solo l’ordine temporale è chiarito. Dettaglio: `OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md` § Rettifica cronologica. Inventario mtime remediation: `/opt/cursor/artifacts/w4r/chrono_artifacts_window.json` (readiness locale ~20:38 CET → session ~20:56 CET).


## 1. Baseline e stato del repository

| Voce | Valore |
|------|--------|
| Working tree | Modifiche W3/D-175/PRE-GTM **conservate** + questo ciclo |
| Mongo locale | `mongod` 127.0.0.1:27017 · DB `omnia` |
| API primaria | `http://127.0.0.1:43121` `/api/health` → 200 |
| API secondaria (test MP) | avviata su `:43122` durante suite, terminata a fine test |
| Harness locale | `python -m scripts.w3_staging_harness --mode local` → **PASS** |

### File toccati in questo ciclo (principali)

**Produzione / sicurezza**
- `backend/shared/db/tenant_guard.py` — scrub `agency_id` negli update; `import_jobs`/`publishing_sync_logs` in guard; refuse `estimated_document_count`
- `backend/apps/immocloud/private_listings.py` — filtri owner atomici
- `backend/apps/billing/b2c_listing_publish.py`, `b2c_boosts.py` — filtri owner atomici
- `backend/apps/immoweb/property_privacy.py`, `staging_api.py`, `staging_b2c.py`, `moderation.py`
- `backend/apps/immocloud/listing_safety_gate.py`
- `backend/apps/v1/gateway.py` — ingest update con `agency_id`
- `backend/apps/immoweb/agencies.py` — gate join CC via P.IVA; `remove_member` membership+refresh+filtro atomico
- `backend/apps/billing/routes.py` — checkout subscription Main Admin (`require_roles_exact` + assert)
- `backend/apps/immoweb/groups.py` — `branch_admin` non crea gruppi
- `backend/apps/immoweb/invites.py` — exact roles; invite `agency_admin` solo owner/MA; claim atomico
- `backend/apps/immoweb/mls.py` — actor filters partner/offer respond
- `backend/shared/auth/membership_service.py` — `end_membership_for_organization`
- `backend/shared/billing/commercial_access.py` — cease revoca anche Main Admin senza `agency_ids`

**Test / harness / docs**
- `backend/tests/test_w3_staging_readiness_authz.py` (**nuovo**)
- `backend/tests/test_w3_http_dual_tenant_mongo.py` (**19 scenari HTTP**)
- `backend/tests/test_w3_multiprocess_local.py` (**nuovo**, 4 test)
- `backend/tests/test_tenant_guard_adversarial.py`, `test_slice1_b01_b03.py`
- `scripts/w3_staging_harness/*` (**nuovo**)
- `PRE-GTM-READINESS-MASTER.md`, `docs/pre-gtm/02-security-multitenant.md`
- questo rapporto

---

## 2. Problemi individuati

| ID | Severità | Area | Descrizione |
|----|----------|------|-------------|
| W3-SR1 | ALTA | B2C properties | Update/submit listing con solo `{id}` su path `/api/cloud` (no tenant inject) |
| W3-SR2 | ALTA | Billing B2C | Slot/addon/boost apply con solo `{id}` dopo ownership find |
| W3-SR3 | ALTA | CC join | Creazione agency con P.IVA esistente auto-attacca Organization al CC altrui |
| W3-SR4 | ALTA | Billing | `POST /billing/checkout` accettava `branch_admin` via alias `agency_admin` |
| W3-SR5 | ALTA | Groups | `branch_admin` poteva creare AgencyGroup e promuovere a `group_admin` |
| W3-SR6 | ALTA | Membership | `remove_member` update by id; nessun end membership; nessun revoke refresh |
| W3-SR7 | MEDIA | Tenant guard | `$set.agency_id` poteva riassegnare tenant sotto enforce |
| W3-SR8 | MEDIA | MLS legacy | `mls_partners` / `mls_requests` respond update by id post-gate |
| W3-SR9 | MEDIA | Invites | Accept non-atomico; `branch_admin` poteva invitare; invite `agency_admin` non gated |
| W3-SR10 | MEDIA | Cease CC | Revoca sessioni non includeva Main Admin senza `agency_ids` |
| W3-SR11 | MEDIA | Guard coverage | `import_jobs`, `publishing_sync_logs` fuori `TENANT_COLLECTIONS` |
| W3-SR12 | BASSA | Guard | `estimated_document_count` unscoped sotto enforce |
| W3-SR13 | MEDIA | CRM agency | privacy / staging save / v1 ingest / moderation / safety — filtri non atomici |
| W3-SR14 | BASSA | Test infra | `_run` con `get_event_loop` fragile dopo `asyncio.run` (slice1) |

---

## 3. Cause radice

1. **TOCTOU check-then-mutate:** ownership verificata in `find_one`, mutazione con solo `id` (critico fuori `/api/app` dove non c’è inject).
2. **Alias ruoli D-041:** `require_roles("agency_admin")` espande a `branch_admin` su percorsi commerciali che richiedono Main Admin.
3. **Adesione CC = riuso VAT senza gate:** B16 “1 P.IVA = 1 CC” implementato senza autorizzazione di join.
4. **Revoca incompleta:** unlink `agency_ids` senza Membership SoT né refresh store.
5. **Difesa in profondità incompleta:** inject sul filtro ma non scrub dell’update payload.

---

## 4. Correzioni implementate

| ID | Fix |
|----|-----|
| W3-SR1 | `owner_user_id` + `is_private_listing` su update/submit B2C |
| W3-SR2 | stessi vincoli su slot/addon/boost |
| W3-SR3 | se CC ha org o MA → solo MA / super_admin / owner org esistente (MA vacante) |
| W3-SR4 | `require_roles_exact` + `assert_is_main_admin_of` su checkout |
| W3-SR5 | `require_roles_exact(..., agency_admin)` — **no** `branch_admin` |
| W3-SR6 | filtro `{id, agency_ids}`; `end_membership_for_organization`; `revoke_all_refresh`; demote role se senza org |
| W3-SR7 | `_scrub_update_agency_id` su update_one/many/find_one_and_update |
| W3-SR8 | partner filter `$or` agency_a/b + initiator≠; offer filter `to_agency_id` |
| W3-SR9 | claim `find_one_and_update({id,status:pending})`; exact roles; agency_admin invite solo owner/MA |
| W3-SR10 | cease revoca anche `main_admin_user_id` |
| W3-SR11 | collections aggiunte a `TENANT_COLLECTIONS` |
| W3-SR12 | refuse `estimated_document_count` under enforce |
| W3-SR13 | filtri agency/owner/private su privacy, staging, v1, moderation, safety |
| W3-SR14 | `asyncio.run` in slice1 `_run` |

**Preservato:** modello Deal/MLS partner `$or`, chat contestuale, documenti autorizzati, bump pubblico `property_stat_days`, wallet H4 già Main Admin, job video system-scoped con `_video_job_filter`.

---

## 5. Vulnerabilità residue e motivazione

| Residuo | Motivazione | Blocca staging? |
|---------|-------------|-----------------|
| Access JWT ~15′ valido dopo revoke refresh | **CHIUSO** — `active_session_ids` + `session_epoch` / claims `sid`/`sv` (`OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md`) | No |
| Dual-model `agency_groups` vs CC | Decisione funzionale E (non inventata qui) | No — path branch escalation chiuso |
| Contatori pubblici view/lead by `{id}` | Dopo gate listing pubblica | No |
| `payment_transactions` non in guard | Webhook Stripe senza tenant ctx | No — documentato E |
| `/api/v1` senza middleware enforce | Isolamento via API key `agency_id` + filtro handler (ora atomico su upsert) | No — rafforzare in ciclo dedicato se richiesto |
| Race create agency stessa VAT parallela | **CHIUSO** — unique + omit sparse-null; test concorrente PASS | No |

Nessuna vulnerabilità **locale riproducibile** del perimetro W3 lasciata aperta senza motivazione.

---

## 6. Inventario endpoint / collection (sintesi)

### Tenant-guarded (force `agency_id` + scrub update)
`properties`, `clients`, `activities`, `modulistica_documents`, `virtual_staging_jobs`, `social_*`, `calendar_events`, `credit_*` (agency), `import_jobs`, `publishing_sync_logs`, …

### Actor/owner filters (non in guard)
`deals`, `mls_*` collab/visit/doc/chat, `mls_partners`, `mls_requests`

### Owner B2C
`properties` private listing mutations

### CommercialCustomer scoped
wallet allocate/revoke, checkout subscription, storage CC

### System / public intentional
orphan GC raw, portal counters, property_stat_days bump, provider_flags, health

---

## 7. Risultati test per tipologia

**Comando aggregato (locale):**

```text
cd backend && PYTHONPATH=. pytest \
  tests/test_w3_staging_readiness_authz.py \
  tests/test_w3_http_dual_tenant_mongo.py \
  tests/test_w3_multiprocess_local.py \
  tests/test_w3_residual_idor.py \
  tests/test_w3_secondary_paths.py \
  tests/test_w3_deals_mls_outsider_authz.py \
  tests/test_tenant_guard_adversarial.py \
  tests/test_tenant_guard_inject.py \
  tests/test_d175_deal_collab_chat.py \
  tests/test_d175_pr240_remediation.py \
  tests/test_d175_collab_api_handlers.py \
  tests/test_d175_c5_purchase_authz.py \
  tests/test_b04_h1_h2_wallet_authz.py \
  tests/test_b04_h2_main_admin.py \
  tests/test_authz_storage_paths.py \
  tests/test_owner_delete_video_tour.py \
  tests/test_microtour_video_persist.py \
  tests/test_slice1_b01_b03.py \
  tests/test_mc042_r01_refresh_cease.py -q
→ 214 passed (ciclo staging readiness)
→ 226 passed (post session gate: +session HTTP + MP B14 + P.IVA)
```

Artefatti: `/opt/cursor/artifacts/w3_sr_full_regression.txt` · `/opt/cursor/artifacts/w3_session_full_regression.txt`

| Tipologia | Suite | Esito |
|-----------|-------|-------|
| Unit / FakeDB / static sniff | staging_readiness_authz, tenant_guard_*, residual, secondary, deals/MLS, D-175, B04, storage, video, slice1, cease | PASS |
| Mongo reale + HTTP live `:43121` | `test_w3_http_dual_tenant_mongo.py` **19 scenari** | PASS |
| Multi-processo locale (2 uvicorn + Mongo) | `test_w3_multiprocess_local.py` **4** | PASS |
| Harness preflight locale | `scripts.w3_staging_harness --mode local` | PASS |

**Il numero 214 è regressione aggregata — non 214 test HTTP.**

---

## 8. Risultati MongoDB reale

- Seed/cleanup isolati con prefissi `w3dt-*` / `w3mp-*`
- Dual CommercialCustomer + Main Admin + branch_admin
- Verifica membership ended + refresh deleted su `remove_member` (quando HTTP 200)
- Video job filter wrong-agency → `matched_count == 0`
- Nessun FakeDB sul path HTTP

---

## 9. Risultati HTTP reali (19 scenari)

| # | Scenario | Endpoint | Atteso |
|---|----------|----------|--------|
| 1 | property cross-tenant | `GET /api/app/properties/{pB}` | 403/404 |
| 2 | activity mutate cross | `PATCH/DELETE …/activities/{actB}` | 403/404 |
| 3 | deal outsider | `GET …/deals/{deal}` | 403/404 |
| 4 | public video leak | `GET /api/cloud/videos/{vid}` | 403/404 |
| 5 | unauth wall | `GET …/properties` no token | 401/403 |
| 6 | document outsider | `POST …/document-requests/{id}/access` | 403/404 |
| 7 | chat outsider | `POST …/collab-chat/threads/{id}/messages` | 403/404 |
| 8 | dashboard no agency | `GET …/dashboard/kpis` | 400/403/404 |
| 9 | membership cleared | GET property | 400/401/403/404 |
| 10 | agency spoof activity | `POST …/activities` agency_id=B | crea A o deny |
| 11 | video job Mongo scope | update_one wrong agency | matched 0 |
| 12 | collab outsider | `GET …/collaborations/{id}` | 403/404 |
| 13 | branch_admin create group | `POST /api/app/groups` | 401/403 |
| 14 | branch_admin wallet | `GET/POST /api/billing/wallet*` | 401/403/404 |
| 15 | CC spoof allocate | `POST /api/billing/wallet/allocate` cc=B | 401/403/404/422 |
| 16 | cross-CC property | GET prop B as MA A | 403/404 |
| 17 | remove_member | `DELETE …/agencies/me/members/{id}` | 200⇒ membership ended + refresh 0 |
| 18 | calendar cross | GET calendar event A as B | 403/404/405 |
| 19 | MLS partner outsider | `POST …/mls/partners/{id}/respond` | 403/404 + status pending |

**Non eseguiti remotamente:** Stripe checkout live/test su Railway, cookie domain Vercel, multi-replica LB.

---

## 10. Risultati multi-processo

| Prova | Dimostrato | Non equivalente a |
|-------|------------|-------------------|
| Health su `:43121` e `:43122` | 200 entrambi | Railway replica set |
| Stesso JWT access su entrambi | status coerente | sticky session LB |
| Deny cross-tenant coerente | 403/404 entrambi | — |
| Revoca sessioni Mongo condivisa | jti + `active_session_ids` / epoch | access JWT **rifiutato subito** anche sul processo B (gate B14) |

---

## 11. Ambiente staging atteso

Vedi `scripts/w3_staging_harness/config.py` `EXPECTATIONS`:

| Elemento | Requisito | SoT | Verifica staging |
|----------|-----------|-----|------------------|
| Backend | Railway HTTPS `/api` | Railway URL | health 200 |
| Frontend | Vercel staging | Vercel | SPA + API corretta |
| Mongo | DB staging dedicato | `MONGO_URL`/`DB_NAME` | ping harness |
| JWT | `JWT_SECRET` identico su repliche | Railway env | token cross-instance |
| Repliche | ≥2 API | Railway scale | `instance_id` diversi |
| Email | Resend + kill switch | secrets + `provider_flags` | B8/L5 |
| Stripe | **test mode only** | `sk_test` | webhook staging |
| Dati sintetici | prefisso `w3stg-<run_id>` | harness | cleanup tagged-only |

Valori URL/secret remoti **non inventati** — da leggere dall’ambiente al momento del mandato staging.

---

## 12. Requisiti e configurazioni

Localmente verificati: `MONGO_URL`, `DB_NAME=omnia`, `JWT_SECRET` (da `backend/.env`), API `:43121`, mongod locale.

Staging (non verificati qui): Railway vars, Vercel `REACT_APP_BACKEND_URL`, Stripe webhook endpoint, Resend, replica count.

---

## 13. Harness preparato

Package: `scripts/w3_staging_harness/`

- `preflight.py` — health, mongo ping, unauth wall, **session_revocation** (access+refresh)
- `config.py` — expectations + acceptance
- `__main__.py` — report PASS/FAIL/BLOCKED + entry criteria EC-1…EC-7
- Staging mode **bloccato** senza `OMNIA_STAGING_VERIFY=1`

Esecuzione locale: **PASS** → `/opt/cursor/artifacts/w3_staging_harness_session.json`

---

## 14. Criteri di ingresso staging

| ID | Criterio | Stato locale |
|----|----------|--------------|
| EC-1 | Regressione W3/D-175 verde | **OK** (226 post session gate) |
| EC-2 | Vuln locali riproducibili chiuse | **OK** (incluso B14 access JWT) |
| EC-3 | Ambiente atteso documentato | **OK** |
| EC-4 | Harness + session revocation preflight | **OK** |
| EC-5 | Dati sintetici + cleanup | **OK** |
| EC-6 | Remote-only elencati separati | **OK** |
| EC-7 | B14 multi-process locale | **OK** |

---

## 15. Verifiche che richiedono necessariamente staging

1. Multi-replica Railway + diversity `instance_id`
2. B8 provider kill cross-replica
3. L5 Resend evidence
4. T22 Mongo staging
5. Stripe webhook end-to-end (test mode)
6. Cookie/CORS Vercel↔Railway
7. Attestazione multi-replica Railway della revoca sessioni (già dimostrata localmente cross-process)

---

## 16. Blocchi

**Nessun blocco locale** che impedisca di *iniziare* la verifica staging. Il gap B14 “access JWT ~15′” è stato chiuso nel gate sessioni.

Blocchi **esclusivamente remoti** (non risolvibili qui): deploy/commit autorizzati, secrets staging, scale repliche, attestazioni B8/L5/T22.

---

## 17. Verdetto tecnico e governance

### **A. W3 PRONTO PER VERIFICA STAGING — SESSIONI VERIFICATE**

Tutti i problemi locali risolvibili del perimetro W3 (incluso invalidazione immediata access JWT / B14) sono stati corretti, testati (HTTP + multi-processo) e sottoposti a regressione. Harness aggiornato e PASS. Restano esclusivamente verifiche che richiedono l’ambiente distribuito.

Dettaglio gate: `OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md`.

**Non** si dichiara W3 certificato staging né GTM. La certificazione richiede la verifica sul campo successiva.

### Conferme operative

- Nessun reset/stash/clean  
- Nessun commit/push/merge  
- Nessun deploy  
- Nessun accesso remoto a Railway/Vercel/Mongo/Resend/Stripe live  
- Nessuna email reale  
