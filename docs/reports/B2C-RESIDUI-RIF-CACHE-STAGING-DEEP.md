# B2C ImmobilCloud — Chiusura residui D04 (rif. card) + D02 (cache foto)

**Data (Europe/Rome):** 2026-11-26 17:30 CET  
**Autore:** Cursor (Cloud Agent)  
**Branch:** `cursor/b2c-public-hardening-b894`  
**PR:** [#248](https://github.com/mcnicastro-netizen/omnia2/pull/248) → `main` (**non mergiata**)  
**Worktree:** `/agent/repos/omnia2-integration-d193-cmj-a4`  
**Contesto:** prosecuzione autorizzata — chiudere solo i due residui del report hardening; non ripetere D01–D03 già chiusi.

---

## 0. Sintesi

| Obiettivo | Esito |
|-----------|-------|
| **D04** — `rif.` sistematico sulle card search | **PASS** (codice + unit FE/BE + staging API + browser) |
| **D02** — cache foto senza riuso post-revoca | **PASS** (`Cache-Control: private, no-store` + staging revoke 200→404) |
| Merge `main` / prod commerciale | **non eseguito** |
| Purge CDN | **NOT VERIFIED / N/A** — non dichiarata |

---

## 1. Diagnosi iniziale

### D04 — rif. nelle card
- API `_to_card` esponeva già `reference_code`.
- FE `PropertyDetailPage` mostrava già il rif. in scheda.
- **Gap:** `PropertyCard.jsx` non renderizzava `reference_code` → search senza “Rif. …” nonostante payload corretto.

### D02 — cache foto
- Header precedente: `public, max-age=60, must-revalidate`.
- Con `max-age>0` una risposta “fresca” può essere riusata da cache condivisa/browser **senza** nuova verifica ACL dopo ritiro.
- `must-revalidate` non elimina la finestra di freschezza.

---

## 2. File modificati

```
frontend/src/apps/immocloud/components/PropertyCard.jsx
frontend/src/apps/immocloud/lib/cardReference.js          (nuovo)
frontend/src/__tests__/cardReference.test.js              (nuovo)
backend/apps/immoweb/site.py
backend/tests/test_b2c_public_hardening.py
backend/tests/test_b2c_photo_cache_revocation.py          (nuovo)
docs/reports/B2C-RESIDUI-RIF-CACHE-STAGING-DEEP.md        (questo)
docs/reports/B2C-IMMOBILCLOUD-PUBLIC-HARDENING-STAGING-DEEP.md  (sezione chiusura residui)
```

---

## 3. Soluzione adottata e motivazioni

### D04
- Helper puro `cardReferenceCode` / `cardReferenceLabel` (solo `reference_code` valorizzato; nessun fallback UUID/`agency_id`).
- `PropertyCard` mostra `· Rif. {code}` nella riga città/zona quando presente; se assente non mostra nulla.
- Coerenza con detail (`cloud.info_ref`) e brand (già `Rif.` in HTML).

### D02
- `_PHOTO_CACHE_HEADERS = { "Cache-Control": "private, no-store", "Pragma": "no-cache" }` su tutte le risposte binarie e sul 302 esterno dell’endpoint foto.
- Motivazione: impedisce cache condivisa e riuso browser senza revalidation obbligatoria verso origin (e quindi senza nuova ACL `portal|brand|mls_network`).
- Superfici restano separate (filtri invariati).
- **Non** si dichiara purge CDN.

---

## 4. Test aggiunti

| Suite | Cosa |
|-------|------|
| `frontend/src/__tests__/cardReference.test.js` | con rif. / senza / multipli distinti / no fallback ID |
| `test_b2c_public_hardening.py::test_d04_to_card_reference_code_mapping_for_fe` | mapping API card |
| `test_b2c_photo_cache_revocation.py` | authz + no-store per superficie + revoke 200→404 + cross-agency + redirect headers |

---

## 5. Comandi e risultati (locali)

| Comando | Esito |
|---------|-------|
| `pytest tests/test_b2c_public_hardening.py tests/test_b2c_photo_cache_revocation.py tests/test_s4_public_visibility.py -q` | **27 passed**, 0 fail, 0 skip |
| `CI=true npm test -- --watchAll=false --testPathPattern=cardReference` | **5 passed**, 0 fail |

Log: `/opt/cursor/artifacts/b2c-residui-backend-unit.log`, `b2c-residui-fe-unit.log`

---

## 6. Staging — ambiente e deploy

| Voce | Valore |
|------|--------|
| API | `API staging Railway (servizio omnia-api di questo ciclo)` |
| DB | `omnia_staging_e2e` |
| Railway `omnia-api` | deploy `3ac52960-35f2-4ef7-bf4a-c2fb4c60cd53` |
| Railway `omnia-api-w4b` | deploy `9696daae-d7a4-4794-be0b-601d161bd06b` |
| FE staging | `https://omnia-frontend-staging.vercel.app` |
| Vercel deploy (bundle con card rif.) | `dpl_HZV2eSxc16HjLVWaVzA4YkMJYdQA` |
| Commit codice residui | `3ab19495b8f51e2c55e9e0606fec9947e09c9558` |
| Nota FE | Build con `REACT_APP_BACKEND_URL` = API Railway di questo ciclo (non host API commerciale da vault) |

---

## 7. Evidenze staging HTTP

Run sintetico: `b2cr483bd1d9` · tag `b2c_residui` · **cleanup verificato** (0 doc residui).

| Check | Esito |
|-------|-------|
| Foto autorizzata 200 | PASS |
| Header `private, no-store` (portal) | PASS |
| Header `private, no-store` (brand) | PASS |
| Nessun `public` / `max-age=60` | PASS |
| Private / pending / suspended → 404 | PASS |
| Trashed (`deleted_at`) → 404 | PASS (dopo correzione campo SoT; seed errato `trashed_at` superato) |
| Prima revoca 200, dopo withdraw 404 | PASS |
| Header pre-revoca già `no-store` | PASS |
| Cross-agency brand 404 | PASS |
| Search con `reference_code` distinti | PASS |
| Search senza rif. → nessun codice artificiale | PASS |
| Nessun `agency_id` in card search | PASS |

Summary: `/opt/cursor/artifacts/b2c-residui-staging-summary.json` — **21 PASS** consolidati (1 superseded seed).

### Comportamento osservato post-revoca
1. `GET …/photo/0?surface=portal` → **200** + `Cache-Control: private, no-store`.
2. Mongo: `status=withdrawn`.
3. Stessa URL (anche con header client `Cache-Control: max-age=9999`) → **404**.
4. Interpretazione: origin ricalcola ACL; con `no-store` non c’è finestra `max-age` che legittimi riuso di una 200 precedente da cache HTTP conforme.

---

## 8. Evidenze browser

| Step | File | Esito |
|------|------|-------|
| Search Catania — rif. sulle card | `b2c-residui-fe-search-rif.png` | **PASS** — `Rif. OM-L-3BD1D9`, `OM-L-SECOND1`, `OM-L-BONLY1`; card **noref** senza “Rif.” |
| Detail | `b2c-residui-fe-detail-rif.png` | PASS |
| Meta | `b2c-residui-browser.json` | — |

Nota: computerUse GUI non usato; Playwright headless.

---

## 9. Limiti / NOT VERIFIED

| Voce | Stato |
|------|-------|
| Purge CDN Railway/Vercel esplicita | **NOT VERIFIED / N/A** |
| Cache intermediaria non conforme a RFC (proxy aggressivo che ignora `no-store`) | **NOT VERIFIED** (fuori controllo app) |
| Video demo GUI computerUse | **NOT VERIFIED** (quota) |
| Merge PR #248 / main | non eseguito |
| Deploy progetto Vercel `omnia-frontend` (sito commerciale) | **non toccato** |

---

## 10. SHA / CI / PR

| Voce | Valore |
|------|--------|
| Branch HEAD al momento del codice residui | `3ab1949…` |
| Report tip | (commit successivo con questa documentazione) |
| CI su push branch | atteso (subscription attiva) |
| PR #248 | aperta, base `main`, **no merge** |

---

## 11. Residui ancora aperti

**Nessuno** tra i due obiettivi autorizzati (D04 card + D02 cache foto), entro i limiti §9.

---

## 12. Giudizio

I due residui sono **chiusi e dimostrati** (local unit + staging HTTP + browser).  
GTM commerciale globale ImmobilCloud resta soggetto a firma Founder / merge — fuori perimetro.

Fine report.
