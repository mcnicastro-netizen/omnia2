# OMNIA — W3 Residual IDOR Closure & HTTP E2E Expansion

**Data (Europe/Rome):** 2026-11-21 20:20+  
**Branch iniziale/finale:** `cursor/staging-e2e-d1d3-b894`  
**HEAD iniziale/finale:** `ea89714dfee65ca592e413db551d1506b573049a` (nessun commit)  
**Precedenti:** `OMNIA-W3-TENANT-GUARD-E2E-VERIFICATION.md` · `OMNIA-W3-SECONDARY-ACCESS-PATHS-HARDENING.md`  
**Vincoli:** nessun reset/stash/clean/commit/push/deploy/remoto · no email reali · no Railway/Vercel

---

## 1. Baseline e stato repository

| Voce | Valore |
|------|--------|
| Working tree | Modifiche W3/D-175/PRE-GTM **conservate** (+ questo ciclo) |
| Mongo locale | `mongod` 127.0.0.1:27017 · DB `omnia` |
| API locale | `http://127.0.0.1:43121` `/api/health` → 200 |
| Commit/push/deploy | **Nessuno** |

### File toccati in questo ciclo (principali)

- `backend/shared/mls_collab/service.py` — filtri document/chat/feedback
- `backend/apps/immoweb/collaborations.py` — mutazioni atomiche docs/chat/feedback
- `backend/apps/immoweb/micro_tour_video.py` — `_video_job_filter` + job scoped
- `backend/apps/immoweb/social_publisher.py` — update channel con `agency_id`
- `backend/tests/test_b04ii_wallet_ledger.py` — FakeColl array-contains (allineamento Mongo)
- `backend/tests/test_w3_residual_idor.py` — **nuovo**
- `backend/tests/test_w3_http_dual_tenant_mongo.py` — **ampliato** (12 scenari HTTP)

---

## 2. Inventario percorsi esaminati (documenti / chat)

| Endpoint / op | Authz pre-mutazione | Filtro DB prima | Filtro DB dopo | Classe |
|---------------|---------------------|-----------------|----------------|--------|
| `POST …/document-requests/{id}/respond` approve/fulfill/reject | owner only | `{id}` | `document_request_owner_filter` | **C→B** |
| stesso + revoke | owner\|requester | `{id}` | `document_request_actor_filter` | **C→B** |
| `POST …/access` (consult log) | actor | `{id}` | actor filter | **C→B** |
| `GET …/download` access_log push | actor | `{id}` | actor filter | **C→B** |
| `POST …/visit-feedback/{id}/contest` | `to_agency_id` | `{id}` | `visit_feedback_rated_agency_filter` | **C→B** |
| `POST …/visit-feedback/{id}/resolve` | super_admin only | `{id}` | invariato (ops) | **A/B** |
| `POST …/collab-chat/threads/{id}/messages` thread touch | `require_thread_access` | `{id}` | `chat_thread_actor_filter` (`agency_ids` contains) | **C→B** |
| modulistica update | `arequire_agency` | `{id, agency_id}` già | invariato | **B** |

---

## 3. Video job / background

| Job / helper | Scope | Prima | Dopo | Classe |
|--------------|-------|-------|------|--------|
| `_generate_ken_burns` | system async, tenant/UGC | `update_one({id})` | `_video_job_filter(id, agency_id, property_id)` | **C→B** |
| `_generate_kling_video` | system async, agency | `{id}` | stesso + `agency_id` dalla creazione | **C→B** |
| `hydrate_ready_video` / `_mark_video_expired` | system heal | `{id}` | filtro da campi del doc già caricato | **C→B** |
| `soft_delete_owner_ken_burns` | UGC owner | `id $in` | + `property_id` + `agency_id: null` + mode | **C→B** |

Distinzione esplicita: i job **non** richiedono HTTP tenant context; conservano lo scope della creazione (agency_id può essere `None` per UGC).

---

## 4. `property_stat_days`

| Controllo | Evidenza |
|-----------|----------|
| Bump pubblico | Solo da `portal_detail` / `portal_contact` dopo load property con `_base_filter()` (listing pubblico) |
| Lettura privata | `GET …/private-listings/{pid}/stats` richiede `owner_user_id == user.id` + `is_private_listing` **prima** di `get_listing_stats` |
| Cross-tenant via stats API | Nessun endpoint agency che esponga stats by arbitrary property_id senza ownership |
| Tenant guard | **Non** aggiunto (bump pubblico legittimo su `/api/cloud`) |
| Verdetto residuo | **Sicuro per disegno attuale** — keyed by `property_id`; esposizione gated a ownership o listing pubblico |

---

## 5. Ricerca sistematica mutazioni per `id`

Inventario statico: `/opt/cursor/artifacts/w3_id_only_mutation_inventory.txt`

| Collection prioritaria | Residuo id-first (heuristica) | Classificazione |
|------------------------|-------------------------------|-----------------|
| deals / mls_visits / mls_collaborations / mls_document_requests / mls_chat_threads | **0** | riparati |
| mls_visit_feedback | 1 (`resolve` super_admin) | **A** |
| videos | update_many soft-delete (ora + property/agency) | **B** |
| modulistica_documents | `{id, agency_id}` | **B** (falso positivo heuristica) |
| social_channels | `{id, agency_id}` | **B** |
| properties/users/agencies/commercial_* | molti | **A/B/C** fuori residual docs/chat/video — documentati come residuo globale |

---

## 6. HTTP E2E dual-tenant (Mongo reale + API live)

**File:** `backend/tests/test_w3_http_dual_tenant_mongo.py`  
**Tipo:** HTTP reale contro `127.0.0.1:43121` + seed/cleanup su Mongo `omnia`  
**Non FakeDB.** JWT creati con `create_access_token` + cookie/Bearer.

### Harness

- Due agency `w3dt-*-agA/B` con slug unici, utenti admin, property private, deal A↔B, video agency, activities, collab attiva, document_request fulfilled, chat thread, calendar_event.
- Cleanup: `delete_many` solo sugli id del run.
- Nessun mock HTTP; nessun FakeDB nel path di test.

### Scenari eseguiti (12)

| # | Test | Endpoint HTTP | Asserzione |
|---|------|---------------|------------|
| 1 | property cross-tenant | `GET /api/app/properties/{pB}` | 403/404 |
| 2 | activity mutate cross | `PATCH/DELETE /api/app/activities/{actB}` | 403/404 |
| 3 | deal outsider C | `GET /api/app/deals/{dealAB}` | 403/404 |
| 4 | public video leak | `GET /api/cloud/videos/{vidA}` | 403/404 |
| 5 | unauth wall | `GET /api/app/properties/{pA}` no token | 401/403 |
| 6 | document outsider | `POST /api/app/document-requests/{dr}/access` | 403/404 |
| 7 | chat outsider | `POST /api/app/collab-chat/threads/{t}/messages` | 403/404 |
| 8 | dashboard no agency | `GET /api/app/dashboard/kpis` | 400/403/404 |
| 9 | membership revoked | clear `agency_ids` then GET property | 400/401/403/404 |
| 10 | agency spoof payload | `POST /api/app/activities` con `agency_id=B` | crea A o deny; mai B |
| 11 | video job scope Mongo | `update_one` wrong agency filter | matched_count 0 |
| 12 | collab outsider | `GET /api/app/collaborations/{id}` | 403/404 |

**Non eseguiti in questo ciclo (dichiarati non coperti):** race timing reale multi-thread; token expiry clock; staging remoto; Package C / T3–T4.

---

## 7. Vulnerabilità e riparazioni

| ID | Severità | Impatto | Fix |
|----|----------|---------|-----|
| W3-R1 | ALTA | Doc respond/revoke TOCTOU by id | owner/actor filters |
| W3-R2 | ALTA | Access/download log by id | actor filter |
| W3-R3 | MEDIA | Chat thread update by id | `agency_ids` containment |
| W3-R4 | MEDIA | Feedback contest by id | `to_agency_id` filter |
| W3-R5 | MEDIA | Video job retarget by id | `_video_job_filter` |
| W3-R6 | BASSA | social_channels validate/publish by id | + `agency_id` |

---

## 8. Test eseguiti

```text
cd backend && PYTHONPATH=. pytest \
  tests/test_w3_residual_idor.py \
  tests/test_w3_http_dual_tenant_mongo.py \
  tests/test_w3_secondary_paths.py \
  tests/test_w3_deals_mls_outsider_authz.py \
  tests/test_tenant_guard_adversarial.py \
  tests/test_tenant_guard_inject.py \
  tests/test_d175_deal_collab_chat.py \
  tests/test_d175_pr240_remediation.py \
  tests/test_d175_collab_api_handlers.py \
  tests/test_d175_c5_purchase_authz.py \
  tests/test_b04_h1_h2_wallet_authz.py \
  tests/test_authz_storage_paths.py \
  tests/test_owner_delete_video_tour.py \
  tests/test_microtour_video_persist.py -q
→ 152 passed
```

Artefatto: `/opt/cursor/artifacts/w3_residual_full_regression.txt`

| Tipologia | Cosa |
|-----------|------|
| Unit / FakeDB | residual filters, guard, D-175 collab |
| Mongo reale + HTTP | 12 dual-tenant scenarios |
| Video unit | persist / owner delete |

Il numero **152** è regressione aggregata — **non** 152 test HTTP.

---

## 9. Rischi residui

1. `properties` / `users` / billing CC: molte mutazioni id-only post-gate (fuori residual docs/chat/video).
2. Feedback `resolve` super_admin resta by id (accettabile ops).
3. Race multi-worker reale non strumentata.
4. Staging / membership revoke end-to-end cookie refresh **non** eseguiti remotamente.
5. W3 **non certificato** staging/GTM.

---

## 10. Staging ancora necessario

- Dual-agency su Railway multi-replica
- Revoca membership + invalidazione sessione reale
- Load/stress (W5) e capacity (W6) — fuori questo ciclo
- Attestazione B8/L5/T22 (W9) remota

---

## 11. Verdetto governance

**W3 localmente verificato (residual IDOR docs/chat/video chiusi + HTTP Mongo ampliato) — avanzato, non certificato staging/GTM.**

Motivazione: riparazioni request-scoped dimostrate; 12 scenari HTTP su Mongo reale verdi; residui globali e staging esplicitamente aperti.
