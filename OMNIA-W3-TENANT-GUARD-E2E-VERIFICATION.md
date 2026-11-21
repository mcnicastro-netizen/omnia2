# OMNIA — W3 Security Hardening: Tenant Guard End-to-End Verification

**Data (Europe/Rome):** 2026-11-21 19:54+  
**Branch:** `cursor/staging-e2e-d1d3-b894`  
**HEAD:** `ea89714dfee65ca592e413db551d1506b573049a`  
**Mandato:** verifica avversariale completa post-riparazione force-`agency_id`  
**Vincoli rispettati:** nessun reset/stash/clean/commit/push/deploy/remoto

---

## 1. Baseline

| Voce | Valore |
|------|--------|
| Working tree | Modifiche PRE-GTM / D-175 già presenti **conservate** |
| Diff W3 originario | `tenant_guard.py`: force overwrite + `activities` |
| Diff W3 questo ciclo | wrap `replace_one`/`distinct`/`find_one_and_replace`; refuse `bulk_write` under enforce; reject `$lookup`/`$unionWith`/`$graphLookup`/`$out`/`$merge`; expand `TENANT_COLLECTIONS`; fix `Database.tenant_filter`; orphan_gc → `get_raw()` |
| Docs preesistenti | `PRE-GTM-READINESS-MASTER.md`, `docs/pre-gtm/02-security-multitenant.md` allineati al codice dopo questo ciclo |

---

## 2. Inventario accessi MongoDB

Inventario statico su `apps/` + `shared/` (esclusi script/test):

- **~1298** call site di operazioni Mongo tipizzate
- **~92** collection distinte
- Artifact: `/opt/cursor/artifacts/w3_mongo_access_inventory.txt`

### 2.1 Operazioni coperte da `TenantCollection` (dopo fix)

| Op | Inject filtro | Inject doc | Note |
|----|---------------|------------|------|
| find / find_one | sì (force) | — | |
| update_one / update_many | sì | — | |
| delete_one / delete_many | sì | — | |
| find_one_and_update / delete | sì | — | |
| find_one_and_replace | sì | sì | **aggiunto** |
| replace_one | sì | sì | **aggiunto** (prima bypass via `__getattr__`) |
| count_documents / distinct | sì | — | distinct **aggiunto** |
| insert_one / insert_many | — | sì (force) | |
| aggregate | $match forzato | — | stage cross-collection **rifiutati** |
| bulk_write | — | — | **refuse** under enforce |

### 2.2 Bypass strutturali analizzati

| Percorso | Esito |
|----------|-------|
| `TenantCollection.__getattr__` → Motor raw | **RIPARATO** — metodi filter-based non più passthrough |
| `Database.get_raw()` | Intenzionale: deals partner property, orphan GC, jobs. Call site app: `deals.py`, `collaborations.py`, `orphan_gc.py` |
| `Database.tenant_filter(extra)` | **RIPARATO** — `agency_id` context vince su `extra` |
| Middleware agency da query/body | **OK** — solo JWT cookie/Bearer + `optional_agency_id(user)` |
| Enforce solo `/api/app/*` | By design; cloud pubblico non inject |
| Context agency assente + enforce | Inject non forza (filtro invariato) — le route devono usare `arequire_agency` |

### 2.3 Pipeline join

Nessun `$lookup` / `$unionWith` / `$graphLookup` / `$out` / `$merge` negli handler `apps/`+`shared/` (oltre alla denylist nel guard). **Residuo:** se qualcuno li aggiunge su collection guarded, il guard fallisce chiuso.

---

## 3. Risultati per famiglia di operazioni (test avversariali unit/Fake recording)

Suite: `tests/test_tenant_guard_adversarial.py` + `tests/test_tenant_guard_inject.py`

| Famiglia | Manipolazione client | Risultato |
|----------|----------------------|-----------|
| Lettura find/find_one | `agency_id=B` | Forzato ad A |
| Update one/many | `agency_id=B` | Forzato ad A |
| Delete one/many | `agency_id=B` | Forzato ad A |
| Replace / find_one_and_replace | filtro+doc B | Entrambi → A |
| Insert one/many | doc B/C | → A |
| Distinct / count | filtro B | → A |
| Aggregate $match | agency B | → A |
| Aggregate $lookup/… | stage join | `ValueError` fail-closed |
| bulk_write | qualsiasi | `ValueError` under enforce |
| `$or`/`$and` nested agency B | top-level force A | AND incompatibile → zero match |
| `agency_id: {$ne: A}` | overwrite | → A |
| Context assente | agency B nel filtro | non inventa scope |
| `Database.tenant_filter` | extra B | → A |

**Tipo prova:** unit con `RecordingColl` / FakeDB — **non** MongoDB reale.

---

## 4. Collection: guarded vs escluse

### 4.1 Aggiunte a `TENANT_COLLECTIONS` in questo ciclo

| Collection | Motivo |
|------------|--------|
| `activities` | single-agency (già ciclo precedente) |
| `modulistica_documents` | **nome reale**; `modulistica_docs` era alias morto |
| `mandate_opportunities` | funnel single-agency D-129 |
| `social_channels` | agency scoped; update by id senza filtro agency ora difeso |
| `ai_client_import_drafts` | draft per agency |
| `credit_wallets` | wallet per agency (legacy, non CC) |

### 4.2 Esclusioni classificate

| Classe | Collection (esempi) | Protezione dimostrabile |
|--------|---------------------|-------------------------|
| owner/partner-handler | `deals`, `mls_*` | Helper `deal_role` / `require_agency_in_collaboration` + check handler |
| platform/global | `users`, `agencies`, `memberships`, `commercial_*`, `cc_*` | Authz ruolo / Main Admin / ops |
| user-scoped | `notifications`, `favorites`, `b2c_*` | `user_id` / ownership |
| mixed-public-agency | `videos` | Handler misto pubblico/privato — **non** auto-inject |
| handler/job/lead | `import_jobs`, `calendar_events`, `property_stat_days`, `credit_ledger`, lead marketing | Filtri handler o job; **residuo da rafforzare** se esposti su `/api/app` senza agency |

---

## 5. Deals e `mls_*`

**Decisione confermata:** restano **fuori** da `TENANT_COLLECTIONS` (scope `$or` owner/partner).

### 5.1 Contratto authz

1. Load by id (`get_deal` / `get_visit` / `get_collaboration` / `get_thread`) **senza** filtro agency.
2. Gate successivo obbligatorio: `deal_role` / membership owner|partner / `require_agency_in_collaboration` / `require_thread_access`.
3. List endpoint costruiscono `$or` **server-side** da `arequire_agency(user)` — non da payload client.

### 5.2 Test outsider (FakeDB)

`tests/test_w3_deals_mls_outsider_authz.py` + regressioni D-175:

- outsider `agC` → `collaboration_forbidden` / `deal_role is None` / `chat_forbidden`
- list `$or` con aid trusted non matcha deal A/B
- regressioni: `test_d175_deal_collab_chat.py`, `test_d175_pr240_remediation.py`, `test_d175_collab_api_handlers.py`

### 5.3 Residuo deals/MLS

| Residuo | Stato |
|---------|-------|
| Update deal usa `{"id": deal_id}` dopo gate | OK se gate non bypassabile; difesa in profondità assente a livello DB |
| `get_raw().properties` per partner listing | Intenzionale; dipende da check collab precedente |
| Enumerazione id → 403 vs 404 | Leak esistenza deal; non accesso dati |
| Suite HTTP E2E outsider su staging | **Non eseguita** (no remote) |

---

## 6. Vulnerabilità trovate e riparazioni

| ID | Severità | Descrizione | Fix |
|----|----------|-------------|-----|
| W3-B1 | **ALTA** | `replace_one` / `distinct` / `find_one_and_replace` / eventuale `bulk_write` passavano da `__getattr__` senza inject | Wrap espliciti; `bulk_write` refuse under enforce; `__getattr__` blocca i nomi wrapped |
| W3-B2 | **ALTA** | Collection reale `modulistica_documents` **non** in `TENANT_COLLECTIONS` (solo alias `modulistica_docs`) | Aggiunta collection reale |
| W3-B3 | **MEDIA** | `Database.tenant_filter` faceva `base.update(extra)` → client poteva sovrascrivere agency | Force agency dopo extra |
| W3-B4 | **MEDIA** | Aggregate poteva in teoria `$lookup` verso altre collection | Denylist fail-closed (0 usi attuali) |
| W3-B5 | **MEDIA** | `social_channels` / `mandate_opportunities` / `ai_client_import_drafts` / `credit_wallets` senza safety-net guard | Aggiunte a `TENANT_COLLECTIONS` |
| W3-B6 | **BASSA** | orphan_gc via `Database.get()` avrebbe visto solo un tenant sotto enforce | Switch a `get_raw()` |

Riparazione originaria force-`agency_id` (PG-07) **confermata e rafforzata**.

---

## 7. Test eseguiti

| Suite | Tipo | Risultato |
|-------|------|-----------|
| `test_tenant_guard_inject.py` | unit | PASS |
| `test_tenant_guard_adversarial.py` | unit/RecordingColl | PASS |
| `test_w3_deals_mls_outsider_authz.py` | FakeDB | PASS |
| `test_tenant_helpers_onda10.py` | unit | PASS |
| `test_d175_deal_collab_chat.py` | FakeDB | PASS |
| `test_d175_pr240_remediation.py` | FakeDB | PASS |
| `test_d175_collab_api_handlers.py` | FakeDB | PASS |
| `test_d175_c5_purchase_authz.py` + `test_b04_h1_h2_wallet_authz.py` + `test_authz_storage_paths.py` | FakeDB/unit | **55 PASS** |
| **Totale questo ciclo (blocchi sopra)** | | **72 + 55 = 127 PASS** (overlap helpers escluso dal double-count: adversarial block 72) |

Log: `/opt/cursor/artifacts/w3_adversarial_pytest.txt`

### Non eseguibili qui

- MongoDB reale multi-tenant IDOR ladder su HTTP
- Staging dual-agency E2E
- Attacco live su Railway

---

## 8. Rischio residuo

1. **Handler-only collections** (`calendar_events`, `property_stat_days`, `credit_ledger`, lead marketing, `videos`): non in guard; isolamento dipende dai filtri route.
2. **Deals/MLS updates by id** dopo gate: difesa applicativa, non DB-level.
3. **Path non `/api/app`**: enforce off → nessun inject (by design cloud).
4. **Jobs/scripts** con Motor diretto: fuori request path.
5. **Certificazione W3 GTM**: ancora **non** dichiarabile senza ladder HTTP con due agency reali + staging.

---

## 9. Stato W3 aggiornato

| Voce | Stato governance |
|------|------------------|
| Force inject agency_id | **implementato verificato** (unit) |
| Bypass replace/distinct/bulk/aggregate join | **implementato verificato** (unit) |
| Collection single-agency mancanti (modulistica reale, activities, …) | **implementato verificato** (unit wrap) |
| Context solo da JWT/user | **implementato verificato** (source sniff + middleware) |
| Deals/MLS outsider gate | **implementato verificato** (FakeDB + D-175 regressione) |
| IDOR HTTP due agency reali | **fase successiva** / staging |
| W3 “completato / certificato” | **NO** — avanzato, non chiuso |

**Verdetto:** W3 **AVANZATO / hardening verificato in locale**. Non certificazione isolamento multi-tenant end-to-end.
