# OMNIA — W3 Secondary Access Paths Hardening

**Data (Europe/Rome):** 2026-11-21 20:08+  
**Branch:** `cursor/staging-e2e-d1d3-b894`  
**HEAD:** `ea89714dfee65ca592e413db551d1506b573049a`  
**Precedente:** `OMNIA-W3-TENANT-GUARD-E2E-VERIFICATION.md`  
**Vincoli:** nessun reset/stash/clean/commit/push/deploy/remoto

---

## 1. Baseline

| Voce | Valore |
|------|--------|
| Working tree | Modifiche W3/D-175/PRE-GTM **conservate** |
| Mongo locale | `mongod` 127.0.0.1:27017 · DB `omnia` |
| API locale | `http://127.0.0.1:43121` health 200 |
| Obiettivo ciclo | Chiudere superfici handler-only, `get_raw`, Deal/MLS TOCTOU, context assente, dual-tenant HTTP locale |

---

## 2. Inventario route / collection handler-only

### 2.1 `calendar_events`

| Voce | Dettaglio |
|------|-----------|
| Route | Solo `GET /api/app/dashboard/kpis` e `/today` (read) |
| Write | Nessuna route di scrittura trovata |
| Context | Era `optional_agency_id` → **ora `require_agency`** (fail closed) |
| Guard | **Aggiunto** a `TENANT_COLLECTIONS` |
| Esito | Letture sempre scoped; senza agency → 400 |

### 2.2 `property_stat_days`

| Voce | Dettaglio |
|------|-----------|
| Accesso | `bump_daily_stat` (portal public) + `GET …/private-listings/{pid}/stats` |
| Chiave | `property_id` + `day` (non agency-first) |
| Authz stats | Ownership `owner_user_id` su listing privato prima della lettura |
| Guard | **Non** in `TENANT_COLLECTIONS` (bump pubblico /api/cloud) |
| Fix | Stamp opzionale `agency_id` su insert; residuo documentato |

### 2.3 `credit_ledger`

| Voce | Dettaglio |
|------|-----------|
| Accesso | Solo servizi billing (`credit_wallet_service`, `plan_credits`) — insert con `agency_id` |
| Route client diretta | Nessuna |
| Guard | **Aggiunto** a `TENANT_COLLECTIONS` |
| Classe | Handler/service — ora con safety-net |

### 2.4 Lead marketing (`valuation_leads`, `mortgage_leads`, `domain_leads`, `legal_kit_leads`)

| Voce | Dettaglio |
|------|-----------|
| Natura | Lead pubblici / marketing / privacy export |
| Isolamento tenant CRM | Non applicabile come CRM agency-scoped |
| Classe | platform/marketing — **residuo accettato** (non tenant CRM) |

### 2.5 `videos` (mixed public / agency)

| Voce | Dettaglio |
|------|-----------|
| Vulnerabilità | (1) `video_status` con agency opzionale → query solo `{id}` leak cross-tenant; (2) `video_status_public` fallback `{id, status:ready}` leak agency video; (3) `by-property` senza verifica listing pubblico |
| Fix | `arequire_agency` + `$or` scoped; public solo UGC null **o** agency video se property pubblica; by-property richiede listing pubblico |
| Guard | Resta fuori `TENANT_COLLECTIONS` (mixed) |
| Test HTTP Mongo | `GET /api/cloud/videos/{agencyVid}` → 404 su video privato |

### 2.6 Altri ex-handler-only ora guarded

`match_audit`, `calendar_events`, `credit_ledger` (+ precedenti: activities, modulistica_documents, social_channels, …).

---

## 3. Inventario `get_raw()`

| File:funzione | Collection | Motivo | Classe | Note |
|---------------|------------|--------|--------|------|
| `server.py:global_health` | ping | health | **A** | Non esposto a dati tenant |
| `provider_flags.py` | provider_flags | ops kill SoT | **A** | Globale |
| `orphan_gc.py` | multi | GC blob cross-tenant | **A** | Switch a raw (ciclo precedente) |
| `tenant_middleware.py` | users | load user per JWT | **A** | Pre-inject |
| `consent_log.py` | consent | audit privacy | **A** | |
| `deals.py:create_deal` | properties | partner legge listing owner post-collab | **B** | Commento + gate collab/MLS |
| `collaborations.py:create` | properties, agencies | richiesta collab su listing altrui | **B** | `assert_mls_listing_shareable` + self partner |
| Test harness | FakeDB | mock | n/a | |

**C/D riparati in questo ciclo:** nessuno nuovo C/D oltre hardening commenti + già B. Nessun raw ingiustificato rimosso.

---

## 4. Deal / MLS — difesa in profondità

| Operazione | Prima | Dopo |
|------------|-------|------|
| Deal update/proposal/send/partner | `update_one({"id"})` dopo gate | `deal_actor_filter` / `deal_owner_filter` / `deal_partner_filter` + `matched_count==0` → 403 |
| Visit update | `{"id"}` | `visit_actor_filter` |
| Collab accept/reject/revoke | `{"id"}` | `collaboration_actor_filter` (+ owner_agency_id dove serve) |
| Payload role spoof | non c’è campo role client | invariato — ruolo da `deal_role(deal, aid)` |
| Race TOCTOU | check poi update bare id | update filtrato atomicamente sullo scope actor |

Helper nuovi in `shared/mls_collab/service.py`.

---

## 5. Tenant context assente

| Comportamento | Stato |
|---------------|-------|
| Enforce + no `agency_id` su guarded coll | **`TenantContextRequired`** (fail closed) — non lascia più passare filtri client |
| Dashboard | `require_agency` al posto di optional |
| Video status agency | `arequire_agency` |
| Middleware | Continua a derivare agency solo da JWT → user DB (`optional_agency_id`) — no query/body |

---

## 6. Vulnerabilità e riparazioni

| ID | Severità | Descrizione | Fix |
|----|----------|-------------|-----|
| W3-S1 | **ALTA** | Video status senza agency = IDOR by id | require agency + $or scoped |
| W3-S2 | **ALTA** | Public video fallback any ready | Solo UGC null o listing pubblico |
| W3-S3 | **MEDIA** | Public by-property senza check listing | Require public listing |
| W3-S4 | **MEDIA** | Guard senza context lasciava filtro invariato | `TenantContextRequired` |
| W3-S5 | **MEDIA** | Dashboard optional agency | `require_agency` |
| W3-S6 | **MEDIA** | Deal/MLS update by id post-gate | Filtri actor atomici |
| W3-S7 | **BASSA** | Handler-only calendar/ledger/match_audit | Aggiunti a `TENANT_COLLECTIONS` |
| W3-S8 | **BASSA** | social_channels update solo by id | Filtro `agency_id` esplicito |

---

## 7. Test

| Suite | Tipo | Risultato |
|-------|------|-----------|
| `test_tenant_guard_*` + secondary + outsider | unit / FakeDB | PASS |
| `test_d175_deal_collab*` / pr240 / collab handlers | FakeDB | PASS |
| purchase/wallet/storage authz | FakeDB/unit | PASS |
| **`test_w3_http_dual_tenant_mongo.py`** | **HTTP + Mongo reale + API live** | **5 PASS** |
| **Totale blocco regressione** | misto | **132 PASS** |

Log: `/opt/cursor/artifacts/w3_secondary_full_regression.txt`

### Distinzione prove

| Layer | Cosa dimostra | Cosa non dimostra |
|-------|---------------|-------------------|
| Unit / RecordingColl | Inject / fail-closed / denylist | Isolamento HTTP |
| FakeDB | Filtri Deal outsider | Persistenza Mongo |
| **HTTP dual-tenant Mongo** | Property/activity/deal/video cross-tenant su stack locale | Staging multi-replica / load |

---

## 8. Rischi residui

1. **`property_stat_days`** ancora keyed by property_id; lettura agency-side non esposta, ma bump pubblico resta intenzionale.
2. **Marketing leads** non sono tenant CRM.
3. **`videos` mixed** — mutazioni background (`update_one({"id"})` in job generate) restano by id; path request-scoped riparati.
4. **Document request / chat update** alcuni ancora `{"id"}` dopo gate — pattern simile a Deal; rafforzabili in ciclo successivo.
5. **Staging** dual-agency + membership revocata + concurrent agency switch **non** eseguiti (no remote).
6. W3 **non certificato** GTM.

---

## 9. Stato W3 aggiornato

| Voce | Governance |
|------|------------|
| Tenant guard force + bypass wrap | implementato verificato |
| Handler-only prioritari | implementato verificato (locale) |
| get_raw inventory | implementato verificato (classi A/B) |
| Deal/MLS DB-scoped mutations | implementato verificato (FakeDB + HTTP parziale) |
| Dual-tenant HTTP Mongo locale | **implementato verificato** (5 scenari) |
| Staging / certificazione | **fase successiva** |
| W3 certificato | **NO** |

**Verdetto:** W3 **AVANZATO — secondary paths hardened**; evidenza HTTP locale presente; **non** certificazione staging.
