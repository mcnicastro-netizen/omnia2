# OMNIA — A4 MLS SECURITY DEEP REVIEW

**Collegato a:** `docs/reports/A4-MLS-INVENTORY-IMPLEMENTATION.md`  
**Autorizzazione:** revisione/hardening A4 (no staging / no commit / no push)  
**Data (Europe/Rome):** 2026-11-26  
**Worktree:** `/agent/repos/omnia2-a4` · branch `cursor/a4-mls-inventory-b894`  
**HEAD base:** `e5647be39e463d9d407aed0d2b542a3053be3f61` (nessun commit)  
**Giudizio:** **PASS** (superfici cross-tenant verificate e protette in locale; staging non in scope)

---

## 0. Vincoli rispettati

| Vincolo | Stato |
|---------|-------|
| Solo worktree A4 | Sì |
| PR #244 / #245 non toccate | Sì |
| Nessun commit / push / merge / deploy / staging | Sì |
| CMJ / D-193 non riaperti | Sì |
| Modifiche A4 preesistenti preservate | Sì |

---

## 1. Analisi dashboard (`GET /app/mls/dashboard`)

### Pre-hardening (difetto confermato)

Dopo il fix A4 inventory, i contatori `network.local_listings` / `national_listings` usavano `_mls_properties_raw()` **sempre**, anche con `mls_enabled=false`. Un’agenzia non aderente otteneva aggregati cross-tenant (quanti annunci rete locale/Italia) senza essere nel network.

Query raw coinvolte (pre-fix):

- `count` shareable + `agency_id ≠ self` (+ province per local)
- `agencies.count({mls_enabled: true, id ≠ self})`

Auth: `require_roles(agency_admin|agent|super_admin)` + agency context. **Nessun** gate `mls_enabled` sui contatori network.

### Correzione

Se `mls_enabled` è falso:

- **non** si invocano count raw cross-tenant;
- `network.local_listings = national_listings = agencies = 0`;
- i contatori **mine** restano su tenant DB (solo propri);
- collaborations (partner/offerte tipicamente scoped all’agency) restano.

Se `mls_enabled` è vero: count via `_mls_raw_count_shareable(...)`.

### Test

- `test_dashboard_mls_enabled_exposes_network_counts` — PASS  
- `test_dashboard_mls_disabled_zeros_network_no_raw_leak` — PASS (assert anche `raw_count == 0`)  
- `test_mongo_dashboard_disabled_zeros_network` — PASS (Mongo reale)

---

## 2. Analisi ricerca pubblica (`GET /app/mls/search/public`)

### Contratto effettivo (non dedotto dal nome)

| Aspetto | Evidenza |
|---------|----------|
| Autenticazione | **Nessuna** — nessun `Depends(get_current_user)` |
| Ruolo / mls_enabled caller | **Non richiesti** (visitatori anonimi dual-box / embed) |
| TenantContext | Path `/api/app/*` → enforce on; senza agency → raw obbligatorio |
| Visibilità | Solo `_mls_shareable_query` (public\|mls_only, mls_shared≠false, not B2C, not trashed) |
| Projection risposta | Solo campi pubblici (`id,title,city,province_sigla,price,operation,property_type,sqm,cover_url`) — **senza** `agency_id` / PII owner |
| Paginazione | `limit` 1–100, `skip` ≥0 |

Coerenza: allineato a smoke `test_mls_network.py`, stress platform anon, dual-box sito. **Non** è un bug che un’agenzia MLS-off (o anon) veda listing **shareable** pubblici — è il contratto dual-box. I privati / non condivisi / B2C / cestinati restano esclusi.

Hardening A4: passaggio a `_mls_raw_count_shareable` / `_mls_raw_find_shareable` + `_PUBLIC_SEARCH_PROJECTION` + strip difensivo `agency_id`.

### Test

- unauthenticated / MLS-off auth / MLS-on / exclude private+trashed / no reserved fields — PASS  
- `test_mongo_public_search` — PASS  

---

## 3. Audit helper raw

| Helper | Ruolo |
|--------|-------|
| `_mls_shareable_query(extra)` | Merge obbligatorio filtri shareable + not_trashed |
| `_mls_raw_count_shareable` | Count raw solo su query shareable |
| `_mls_raw_find_shareable` | Find raw + projection |
| `_mls_properties_raw` | Accesso collezione; docstring: non usare da CRM |

Call site: **solo** `mls.py` (inventory, dashboard network, public search).  
Test statico `test_raw_helper_not_referenced_outside_mls_module` — PASS.

CRM non usa questi helper; `get_property` cross-tenant resta 404 (FakeDB + Mongo).

---

## 4. Difetti e correzioni in questo ciclo

| ID | Difetto | Correzione |
|----|---------|------------|
| SEC-1 | Dashboard esponeva contatori rete via raw con MLS off | Zero network + no raw call se disabled |
| SEC-2 | Helper raw invocabile senza merge shareable esplicito | `_mls_shareable_query` / count/find wrappers |
| SEC-3 | Public search usava projection inventory (incl. agency_id in find) | Projection pubblica dedicata; risposta senza agency_id |

---

## 5. Nuovi test

| File | N | Esito |
|------|---|-------|
| `tests/test_a4_mls_security_review.py` | 10 | 10 PASS |
| `tests/test_a4_mls_mongo_http.py` | 5 | 5 PASS (mongod locale `127.0.0.1:27017`, DB `omnia_a4_sec_*` droppato) |

Copertura richiesta (§4 prompt): dashboard on/off, public anon / MLS-off / MLS-on, private+noshare+trashed, no campi riservati, isolamento due agenzie, raw non in CRM — **tutti coperti**.

---

## 6. Verifica MongoDB integrata

**Eseguita.** Ambiente: `mongod` locale già in ascolto su `127.0.0.1:27017` (dbpath `/workspace/.mongo-data`).  
DB dedicato effimero, seed due agenzie + listing, handler reali con `TenantAwareDatabase`, cleanup `drop_database`.  
Non staging, non produzione, non credenziali remote.

---

## 7. Regressione

| Suite | Esito |
|-------|-------|
| 14 test A4 originari | **14 PASS** |
| 10 security review | **10 PASS** |
| 5 mongo HTTP | **5 PASS** |
| pre_demo_8 + private_listing + tenant_guard + agency_home_mls | **PASS** (totale combinato **61 PASS**) |
| FE `mlsInventoryScope` | **4 PASS** |
| Falliti / bloccati | **0** |
| Staging | **Non eseguito** (fuori autorizzazione) |

---

## 8. File toccati in questo ciclo (oltre A4 precedente)

- `backend/apps/immoweb/mls.py` — hardening dashboard + helpers + public projection  
- `backend/tests/test_a4_mls_security_review.py` — nuovo  
- `backend/tests/test_a4_mls_mongo_http.py` — nuovo  
- `docs/reports/A4-MLS-SECURITY-DEEP-REVIEW.md` — questo report  

---

## 9. Rischi residui

1. **Staging non verificato** — promozione richiede autorizzazione separata.  
2. Public search espone **intenzionalmente** volumi/listing shareable anonimi (dual-box); non è un leak CRM.  
3. Collaborations counts su dashboard disabled restano agency-scoped (non listing rete); accettabile.  
4. Site `/p/{slug}` network non rivisto in questo ciclo (enforce off su path non-`/api/app`).

---

## 10. Conferme finali

| Voce | Valore |
|------|--------|
| Commit / push | **No** |
| PR #244 / #245 | OPEN, head invariati (non modificate) |
| Staging / prod write | **No** |

---

## Giudizio finale

**PASS** — superfici cross-tenant A4 (inventory, dashboard network, public search, helper raw) verificate in locale con FakeDB + Mongo dedicato; difetto dashboard MLS-off corretto; CRM isolation confermata.  

**Non** equivale a PASS staging.

---

*Fine A4 security deep review — 2026-11-26 Europe/Rome.*
