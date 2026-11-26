# OMNIA — A4 PROMOZIONE E STAGING-DEEP

**Autorizzazione:** `OMNIA — AUTORIZZAZIONE PROMOZIONE A4 E STAGING-DEEP`  
**Data (Europe/Rome):** 2026-11-26  
**Worktree:** `/agent/repos/omnia2-a4`  
**Branch:** `cursor/a4-mls-inventory-b894`  
**PR:** https://github.com/mcnicastro-netizen/omnia2/pull/246  

---

## 1. Stato iniziale e integrità worktree

| Voce | Valore |
|------|--------|
| Branch A4 | `cursor/a4-mls-inventory-b894` |
| HEAD pre-commit | `e5647be39e463d9d407aed0d2b542a3053be3f61` (= `origin/main` al fetch) |
| Modifiche A4 presenti | `mls.py`, `MlsPage.jsx`, 3 test BE, 1 test FE, 2 report locali |
| Altri file estranei | Nessuno nel worktree A4 |
| Worktree D-193 `/agent/repos/omnia2` | `cursor/d193-wallet-remediation-b894` @ `eafb931` — **non modificato** |
| Worktree CMJ `/agent/repos/omnia2-cmj` | `cursor/cmj-commercial-mls-b894` @ `7935673` — **non modificato** |
| PR #244 | OPEN `eafb931a592b61465faab7c0f19ff2e0d5d6105c` — non alterata |
| PR #245 | OPEN `7935673c4dd9b23bc8a6c946746d3abb8a97bd73` — non alterata |
| Operazioni distruttive | Nessuna (`reset`/`clean`/`stash` non usati) |

---

## 2. Base e SHA

| Voce | SHA |
|------|-----|
| Base `main` al momento promozione | `e5647be39e463d9d407aed0d2b542a3053be3f61` |
| Commit A4 promosso | `6e6451721a58f7c4075dfa0a8109802aac517a26` |
| Messaggio | `A4: fix MLS inventory cross-tenant scopes and harden raw surfaces` |

---

## 3. Modifiche effettuate (perimetro A4)

- `backend/apps/immoweb/mls.py` — inventory raw + shareable helpers; dashboard network zero se MLS off; public search projection senza `agency_id`
- `frontend/src/apps/immoweb/pages/MlsPage.jsx` — `data-testid` scope tabs
- `backend/tests/test_a4_mls_inventory.py`
- `backend/tests/test_a4_mls_security_review.py`
- `backend/tests/test_a4_mls_mongo_http.py`
- `frontend/src/__tests__/mlsInventoryScope.test.js`
- `docs/reports/A4-MLS-INVENTORY-IMPLEMENTATION.md`
- `docs/reports/A4-MLS-SECURITY-DEEP-REVIEW.md`
- `docs/reports/A4-PROMOTION-STAGING-DEEP.md` (questo file)

---

## 4. Commit e PR A4

| Voce | Valore |
|------|--------|
| Branch remoto | `origin/cursor/a4-mls-inventory-b894` |
| PR | **#246** OPEN → base `main` |
| URL | https://github.com/mcnicastro-netizen/omnia2/pull/246 |
| Merge | **Non eseguito** (come da mandato) |

---

## 5. Risultati CI (versione promossa)

| Run | Trigger | Conclusion |
|-----|---------|------------|
| https://github.com/mcnicastro-netizen/omnia2/actions/runs/45823375915 | push `6e64517` | **success** |
| https://github.com/mcnicastro-netizen/omnia2/actions/runs/45823401698 | pull_request #246 | **success** |

Check osservato: `Backend billing / B04 unit` (workflow CI del repo) — conclusion `success`.

---

## 6. Servizi staging e SHA/codice effettivamente servito

### API Railway — progetto `omnia-api-staging` (`<RAILWAY_STAGING_PROJECT_ID>`)

| Servizio | URL | Deploy id | Image tag |
|----------|-----|-----------|-----------|
| `omnia-api` | https://omnia-api-production-85845f42.up.railway.app | `5bbb3116-e93a-4bfb-a35c-e2581ad12f04` | stesso id |
| `omnia-api-w4b` | https://omnia-api-w4b-production.up.railway.app | `37a34b7b-3a52-4a5c-b5d7-03b76e90e193` | stesso id |

Environment Railway nome: `production` (naming storico; **non** produzione commerciale — topologia W4).

**Nota SHA Railway:** `railway up` carica il filesystem del worktree (file upload). La meta deploy **non** espone il git SHA. Verifica codice servito = **marker comportamentali A4** (sotto) + instance_id post-deploy.

Post-deploy health `omnia-api`: `instance_id=8f8123621a82:2`, status ok.

Marker comportamentali che dimostrano codice A4 live (pre-A4 fallirebbero):

1. Inventory `scope=national` restituisce listing shareable di **altra** agenzia.
2. Dashboard con `mls_enabled=false` → `network.*.listings/agencies = 0` (no leak raw).
3. Inventory MLS-off → HTTP **403** `mls_not_enabled`.
4. Public search senza `agency_id` / owner PII.

### Frontend Vercel — `omnia-frontend-staging`

| Voce | Valore |
|------|--------|
| URL | https://omnia-frontend-staging.vercel.app |
| Deployment | `dpl_F6AdFHFkgH2JYnVCeohe8vCKc5MQ` |
| Alias | production staging FE |
| `main.js` live | `main.4d38954f.js` |
| Chunk MLS live | `2225.8625ce19.chunk.js` |
| API embedded | `https://omnia-api-production-85845f42.up.railway.app` (verificato nel bundle) |
| Marker A4 FE | stringa `mls-inventory-scope-` + path `/app/mls/inventory` nel chunk |

---

## 7. Configurazione e isolamento ambiente

| Check | Esito |
|-------|-------|
| Progetto Railway = `omnia-api-staging` (canonical D7) | Sì |
| DB app | `omnia_staging_e2e` |
| Mongo host marker | `sakura.proxy.rlwy.net` (proxy staging) |
| Non localhost / non prod DB | Sì |
| Stripe Live | Non usato |
| Email reali | Solo `*@example.com` |
| Seed taggati | `a4_run_id` / cleanup post-test |
| Produzione `api.omniarealestateecosystem.it` | Non target del deploy A4 |

---

## 8. Test eseguiti (comandi e risultati)

### Gate locale (riconfermato pre-promozione)

```text
cd /agent/repos/omnia2-a4/backend
PYTHONPATH=. …/python -m pytest \
  tests/test_a4_mls_inventory.py \
  tests/test_a4_mls_security_review.py \
  tests/test_a4_mls_mongo_http.py \
  tests/test_pre_demo_8.py \
  tests/test_private_listing_mls_isolation.py \
  tests/test_tenant_guard_adversarial.py \
  tests/test_agency_home_mls_cases.py -v
→ 61 passed

cd frontend && yarn test --watchAll=false src/__tests__/mlsInventoryScope.test.js
→ 4 passed

Import sanity: from apps.immoweb import mls → OK
```

### Staging API deep (`/tmp/a4_staging_deep.py`)

```text
→ 21/21 PASS
Artefatto: /opt/cursor/artifacts/a4-staging-deep-summary.json
Log: /opt/cursor/artifacts/a4-staging-deep-run.log
```

Casi: health; public search shareable/exclude/no reserved; inventory anon 401; national/local/mine; dashboard on/off; CRM list/get isolation; agency B mine; FE route; bundle API; marker A4 servito.

### Staging FE deep (Playwright — computerUse non disponibile per quota modello)

```text
python3 /tmp/a4_staging_fe_browser.py
→ 6/6 PASS
Artefatto: /opt/cursor/artifacts/a4-staging-browser-summary.json
Video: /opt/cursor/artifacts/a4-fe-staging-demo.mp4
Screenshot: a4-fe-after-login / mls-hub / inventory-national / inventory-mine
```

Evidenza UI: tab **MLS Italia** mostra `A4FE Partner …`; tab **Il mio MLS** mostra solo `A4FE Own …`.

### Cleanup

Seed API e FE rimossi (`properties/users/agencies` con tag A4). `remaining_a4_props=0`.

---

## 9. Evidenze API / FE / security

### API

- National vede partner shareable, non private/noshare/B2C/trash.
- Local filtra provincia CT (esclude RM).
- Mine solo propri.
- MLS off: inventory 403; dashboard network azzerato.
- CRM GET foreign → 404; list senza foreign.

### Frontend

- Pagina `/it/app/mls` carica.
- Scope tabs presenti (`data-testid`).
- Coerenza API↔UI su mine vs national (screenshot + video).
- Bundle punta API staging Railway.

### Security staging

- Nessun campo riservato in public search.
- Nessun bypass tenant su CRM.
- Nessuna scrittura prod.
- Contatori rete non esposti a agenzia MLS-off.

---

## 10. Difetti trovati in promozione

Nessun difetto A4 bloccante sullo staging dopo deploy.  
Gate locale già includeva SEC-1 (dashboard MLS-off) corretto in security review precedente.

**Blocco operativo minore:** subagent `computerUse` non avviabile (quota modello third-party). FE deep eseguito con Playwright + Chromium; evidenze video/screenshot comunque prodotte.

---

## 11. Riserve e limiti

| ID | Problema | Impatto | Evidenza | Rischio | Decisione Founder? |
|----|----------|---------|----------|---------|---------------------|
| R1 | Railway file-upload senza git SHA in meta | Tracciabilità SHA↔container indiretta | Deploy id + marker comportamentali | Basso se si accettano marker | No — accettabile come CMJ/D-193 |
| R2 | National inventory staging mostra anche listing storici CMJ/W4/D7 shareable | Rumore visuale, non leak | Screenshot national | Nessuno su isolamento A4 (fixture A4 pulite) | No |
| R3 | computerUse non disponibile | FE deep via Playwright invece di Computer Use | Log Task error | Basso | No |
| R4 | CI repo = workflow billing unit (non suite A4 completa in GHA) | Coverage CI stretta | `gh run view` | Medio-basso; copertura A4 è locale+staging | Opzionale: allargare CI |

**Non certificato da questo ciclo:** GTM, intero gestionale, portale B2C ImmobilCloud, chiusura PR #244/#245, merge `main`, produzione.

---

## 12. Verdetto finale (gate separati)

| Gate | Esito |
|------|-------|
| **A4 locale** | **PASS** (61 BE + 4 FE riconfermati) |
| **CI sulla versione promossa** | **PASS** (runs 45823375915 / 45823401698 success) |
| **Deploy staging** | **PASS** (Railway entrambi i servizi + Vercel `dpl_F6AdFHFkgH2JYnVCeohe8vCKc5MQ`) |
| **API staging-deep** | **PASS** (21/21) |
| **Frontend staging-deep** | **PASS** (6/6 Playwright + evidenze UI) |
| **Security staging-deep** | **PASS** (MLS-off zero network; public no reserved; CRM isolation) |
| **A4 complessivo** | **PASS** |

Riserve R1–R4 documentate; nessuna richiede fermata Founder per chiudere il percorso A4.

---

## 13. Conferma PR #244 / #245 e worktree

- PR #244 D-193: OPEN, head `eafb931…` invariato; worktree non toccato.  
- PR #245 CMJ: OPEN, head `7935673…` invariato; worktree non toccato.  
- Nessun merge A4 su `main`.

---

## 14. Conferma produzione / Stripe Live

- Nessun deploy su progetto Railway produzione commerciale.  
- Nessun uso Stripe Live.  
- Nessuna email a utenti reali.  
- DB usato: solo `omnia_staging_e2e`.

---

*Fine report A4 promotion + staging-deep — 2026-11-26 Europe/Rome.*
