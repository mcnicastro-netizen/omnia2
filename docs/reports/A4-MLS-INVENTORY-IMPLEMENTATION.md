# OMNIA — A4 MLS INVENTORY — IMPLEMENTAZIONE LOCALE

**Autorizzazione:** `OMNIA — AUTORIZZAZIONE IMPLEMENTAZIONE A4 INVENTARIO MLS`  
**Data (Europe/Rome):** 2026-11-26  
**Giudizio conclusivo:** **PASS** (verifica locale)  
**Fuori scope (rispettato):** commit · push · PR · merge · deploy · staging · produzione · email reale · Stripe Live

---

## 1. Identificazione repository / branch / HEAD / stato iniziale

| Voce | Valore |
|------|--------|
| Repo | `github.com/mcnicastro-netizen/omnia2` |
| Worktree A4 | `/agent/repos/omnia2-a4` |
| Branch A4 | `cursor/a4-mls-inventory-b894` |
| Base | `origin/main` @ `e5647be39e463d9d407aed0d2b542a3053be3f61` (Merge #243) |
| HEAD A4 (nessun commit) | `e5647be39e463d9d407aed0d2b542a3053be3f61` |
| Working tree A4 | modifiche locali non committate (vedi §14) |

### Stato iniziale altri worktree (preservati)

| Worktree | Branch | HEAD | Note |
|----------|--------|------|------|
| `/agent/repos/omnia2` | `cursor/d193-wallet-remediation-b894` | `eafb931…` | Dirty CMJ uncommitted — **non toccato** |
| `/agent/repos/omnia2-cmj` | `cursor/cmj-commercial-mls-b894` | `7935673…` | Solo `??` audit/nvmrc — **non toccato** |

### PR (sola lettura)

| PR | State | head | Modificata? |
|----|-------|------|-------------|
| #244 D-193 | OPEN | `eafb931…` | **No** |
| #245 CMJ | OPEN | `7935673…` | **No** |

---

## 2. Isolamento worktree A4 rispetto a CMJ

- Creato con `git worktree add -b cursor/a4-mls-inventory-b894 /agent/repos/omnia2-a4 origin/main`.
- Nessun merge/cherry-pick da #244 o #245.
- Nessun `reset` / `clean` / `stash` sui worktree esistenti.
- CMJ HEAD invariato a `7935673`; D-193 HEAD invariato a `eafb931`.

---

## 3. Riproduzione del difetto

Sotto enforce `/api/app/*`, `tenant_guard._inject_filter` forza `agency_id` al caller:

```
BEFORE {'agency_id': {'$ne': 'agB'}, 'visibility': {'$ne': 'private'}}
AFTER  {'agency_id': 'agB', 'visibility': {'$ne': 'private'}}
DEFECT True
```

Prova automatizzata: `test_inject_collapses_ne_filter_defect_reproduction` (**PASS**).

Conseguenza su `my_mls_inventory` pre-fix: `scope=local|national` impostava `agency_id: {$ne: aid}` su `Database.get().properties`, poi l’inject lo riscriveva in `agency_id: aid` → solo inventario proprio (o vuoto rispetto all’intent rete).

---

## 4. Diagnosi tecnica (file / riferimenti)

| Elemento | Path | Ruolo |
|----------|------|-------|
| Handler | `backend/apps/immoweb/mls.py` `my_mls_inventory` | Query inventory |
| Dashboard network | stesso file `mls_dashboard` | Contatori local/national |
| Public search | stesso file `public_network_search` | Ricerca rete pubblica |
| Tenant inject | `backend/shared/db/tenant_guard.py` `_inject_filter` L93–111 | Causa root |
| `Database.get` / `get_raw` | `backend/shared/db/connection.py` | Proxy vs raw |
| Shareable filters | `mls.py` `_shareable_listing_filters` | visibility / mls_shared / B2C |
| FE | `frontend/src/apps/immoweb/pages/MlsPage.jsx` | `scope` → `/app/mls/inventory?scope=` |

**Punto minimo di intervento:** non disabilitare il tenant guard globale; usare `Database.get_raw().properties` **solo** nelle query MLS che richiedono lettura cross-tenant, mantenendo `_shareable_listing_filters` + scope espliciti + gate `mls_enabled` sull’inventory.

---

## 5. Inventario endpoint MLS esaminati

| Endpoint | DB | Cross-tenant properties? | Classificazione |
|----------|-----|--------------------------|-----------------|
| `GET /app/mls/inventory` | era `get()` → **fix raw** | Sì (local/national) | **DIFETTO CONFERMATO → CORRETTO** |
| `GET /app/mls/dashboard` (contatori network) | era `get()` su props network → **fix raw** | Sì | **DIFETTO CONFERMATO → CORRETTO** |
| `GET /app/mls/search/public` | era `get()` → **fix raw** | Sì (rete intera) | **DIFETTO CONFERMATO → CORRETTO** (senza auth: `TenantContextRequired`; con auth: collapse a own) |
| `GET /app/mls/dashboard` (mine shared/exclusive) | `get()` + `agency_id=aid` | No | **CORRETTO** / **NON APPLICABILE** |
| `POST /app/mls/offers` | `get()` own property | No | **NON APPLICABILE** |
| `GET /app/mls/offers` | `mls_requests` (non tenant coll) | N/A | **CORRETTO** |
| `GET/POST partners` | `mls_partners` / agencies | N/A properties | **CORRETTO** |
| `POST join/leave` | agencies | N/A | **CORRETTO** |
| `POST /seed` | super_admin bypass | N/A A4 | **NON APPLICABILE** |
| `GET /app/properties` CRM | tenant | No | **CORRETTO** (non modificato) |
| `GET /app/properties/{id}` CRM | tenant | No | **CORRETTO** (404 cross-tenant invariato) |
| Site `/p/{slug}` network props | `get()` ma path **non** `/api/app` → enforce off | Cross-tenant senza inject | **CORRETTO / NON APPLICABILE** al bug inject |

---

## 6. Modifiche implementate (file)

| File | Cambio |
|------|--------|
| `backend/apps/immoweb/mls.py` | `_require_mls_enabled`, `_mls_properties_raw`; inventory usa raw + gate; dashboard network counts via raw; public search via raw |
| `frontend/src/apps/immoweb/pages/MlsPage.jsx` | `data-testid` scope tabs (`mls-inventory-scope-*`) |
| `backend/tests/test_a4_mls_inventory.py` | **nuovo** — 14 test A4 |
| `frontend/src/__tests__/mlsInventoryScope.test.js` | **nuovo** — 4 test FE statici |
| `docs/reports/A4-MLS-INVENTORY-IMPLEMENTATION.md` | questo report |

Nessuna modifica a collaborations/deals/EntitySearch/properties CRM handlers.

---

## 7. Motivazione scelte di sicurezza

1. **Raw confinato:** helper `_mls_properties_raw()` usato solo da inventory / dashboard network / public search — non da CRM.  
2. **Filtri shareable sempre applicati:** `visibility ∈ {public,mls_only}`, `mls_shared ≠ false`, esclusione B2C/`_private_listings`, `with_not_trashed`.  
3. **Scope esplicito:** `mine` → `agency_id=aid`; `local` → `$ne` + `province_sigla`; `national` → `$ne`.  
4. **Gate `mls_enabled`:** inventory risponde `403 mls_not_enabled` se l’agenzia non ha aderito (allineato a requisito auth A4; FE già nasconde UI se `!dash.mls_enabled`).  
5. **Nessun bypass globale** di `Database.get()` / middleware `/api/app/*`.  
6. **Nessuna clonazione** documenti immobiliari; si restituisce projection MLS ristretta.  
7. **CRM invariato:** test regressione inject + `get_property` 404 partner.

---

## 8. Test aggiunti

### Backend `tests/test_a4_mls_inventory.py` (14)

| Test | Copertura |
|------|-----------|
| `test_inject_collapses_ne_filter_defect_reproduction` | Root cause |
| `test_mine_inventory_own_shareable` | Own MLS |
| `test_national_sees_other_shareable_not_private_or_noshare` | B shareable sì; private / mls_shared=false / B2C no; filtro `$ne` |
| `test_local_filters_province` | CT vs RM |
| `test_mls_disabled_denied` | 403 |
| `test_pagination_no_duplicates` | skip/limit |
| `test_empty_results_ok` | total=0 |
| `test_agency_b_mine_no_contamination` | Isolamento B |
| `test_two_agencies_national_distinct` | Risultati separati |
| `test_dashboard_network_counts_use_raw` | Contatori |
| `test_public_search_returns_network` | Public raw |
| `test_crm_list_stays_tenant_scoped` | CRM inject |
| `test_crm_get_foreign_404` | CRM GET |
| `test_scope_literal_contract` | Literal mine/local/national |

### Frontend `mlsInventoryScope.test.js` (4)

Path API `/app/mls/inventory?scope=`, scope tabs, card, no EntitySearch/CRM fallback.

---

## 9. Comandi eseguiti e risultati

```text
# A4 nuovi
pytest tests/test_a4_mls_inventory.py -v
→ 14 passed

# Regressione correlata
pytest tests/test_a4_mls_inventory.py tests/test_pre_demo_8.py \
  tests/test_private_listing_mls_isolation.py \
  tests/test_tenant_guard_adversarial.py \
  tests/test_agency_home_mls_cases.py -v
→ 46 passed

# FE
yarn test --watchAll=false src/__tests__/mlsInventoryScope.test.js
→ 4 passed (1 suite)
```

Artifact log: `/opt/cursor/artifacts/a4-mls-inventory-pytest.log`, `a4-mls-regression-pytest.log`, `a4-mls-fe-test.log`.

---

## 10. Test falliti / non eseguiti / bloccati

| Voce | Stato |
|------|-------|
| Staging E2E inventory | **Non eseguito** (fuori autorizzazione) |
| Mongo reale isolato HTTP dual-tenant | **Non eseguito** in questo ciclo (FakeDB sufficiente per A4; W3 mongo suite non richiesta) |
| Test falliti residui | **Nessuno** nelle suite eseguite |

---

## 11. Regressione CRM / tenant isolation

- `test_tenant_guard_adversarial` **19/19 PASS** (incluso overwrite `$ne`).  
- `test_crm_get_foreign_404` / `test_crm_list_stays_tenant_scoped` **PASS**.  
- Nessuna modifica a `properties.py` list/get.

---

## 12. Verifica frontend

- `MlsPage` continua a chiamare solo `/app/mls/inventory?scope=${scope}` (non CRM).  
- Scope `mine|local|national` con testid.  
- UI inventory solo se `dash.mls_enabled` (preesistente).  
- Nessuna nuova feature UI oltre testid.

---

## 13. Limiti residui / rischi non risolti

1. **Staging non verificato** — A4 chiuso solo in locale.  
2. **Site `/p/{slug}` network** — non toccato; enforce off sul path pubblico (classificato CORRETTO); se in futuro venisse montato sotto `/api/app` andrebbe rivisto.  
3. **Gate `mls_enabled` su inventory** — comportamento più stretto del tip `main` precedente (prima l’API non negava); coerente con auth A4 e con FE. Dashboard resta consultabile anche se disabled (restituisce `mls_enabled: false`).  
4. Residui audit post-CMJ **A3 typeahead** / **B2 email 24h** — fuori perimetro, non toccati.  
5. Working tree A4 **non commitato** (per mandato).

---

## 14. Stato finale working tree / branch

```
branch: cursor/a4-mls-inventory-b894
HEAD:   e5647be39e463d9d407aed0d2b542a3053be3f61  (== origin/main tip)
 M backend/apps/immoweb/mls.py
 M frontend/src/apps/immoweb/pages/MlsPage.jsx
?? backend/tests/test_a4_mls_inventory.py
?? frontend/src/__tests__/mlsInventoryScope.test.js
?? docs/reports/A4-MLS-INVENTORY-IMPLEMENTATION.md
```

Nessun commit sul branch A4.

---

## 15. Conferma PR #244 / #245

**Non modificate.** State OPEN; head invariati (`eafb931` / `7935673`).

---

## 16. Conferma assenza commit / push / merge / deploy / staging-prod

| Azione | Eseguita? |
|--------|----------|
| Commit | **No** |
| Push | **No** |
| Apertura/modifica PR | **No** |
| Merge | **No** |
| Deploy | **No** |
| Scritture staging/produzione | **No** |
| Email reale / Stripe Live | **No** |

---

## Giudizio

**A4 locale: PASS**

Evidenze: difetto riprodotto; fix raw confinato; 14/14 A4 + 46/46 regressione correlata + 4/4 FE; CRM isolation invariata; CMJ/D-193/PR intatti.  
**Non** dichiarare A4 verificato in staging senza nuova autorizzazione.

---

---

## Appendice — Security deep review (stesso giorno)

Vedi rapporto complementare: `docs/reports/A4-MLS-SECURITY-DEEP-REVIEW.md`.

Esito: **PASS** locale — dashboard non espone più contatori rete se `mls_enabled=false`; public search documentato come no-auth dual-box con filtri shareable; helper raw con merge shareable obbligatorio; prova Mongo dedicata 5/5 PASS. Staging ancora non eseguito.

*Fine report A4 — 2026-11-26 Europe/Rome.*
