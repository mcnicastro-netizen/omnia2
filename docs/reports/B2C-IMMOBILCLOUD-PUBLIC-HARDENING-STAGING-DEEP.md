# B2C ImmobilCloud — Public Hardening + Staging-Deep

**Data (Europe/Rome):** 2026-11-26 17:10 CET  
**Autore:** Cursor (Cloud Agent) — implementazione autorizzata  
**Repository:** `mcnicastro-netizen/omnia2`  
**Autorizzazione:** `OMNIA — AUTORIZZAZIONE IMPLEMENTAZIONE` (B2C ImmobilCloud public hardening + staging-deep)  
**Perimetro:** hardening B2C + staging · **no** merge `main` · **no** produzione commerciale · **no** Stripe Live · **no** email reali · dati sintetici isolati

---

## 1. Baseline e stato iniziale

| Voce | Valore |
|------|--------|
| Baseline Founder | `main` @ `5fba9f5df0416e81b801d855da5bf79a202a6aaf` |
| Antenato merge #247 | `2dfee7f…` sì (contenuto in baseline) |
| Audit di partenza | `docs/reports/AUDIT-MIRATO-B2C-IMMOBILCLOUD.md` — **NON GTM** |
| Criticità audit | **C1** foto ACL debole · **C2** `agency_id` / `agency.id` pubblici · **C3** `lead_id`/`client_id` in contatto · **S1** agency HTML · **S2** cache foto · **D04** rif. pubblico |
| Decisioni funzionali | **D01–D04** approvate dal Founder (identificativi, foto, contatto opaco, `rif.`) |

Stato iniziale: codice main post-#247 con gap dimostrati sull’audit; inventario ImmobilCloud staging spesso vuoto; nessuna correzione hardening ancora su branch dedicato.

---

## 2. Branch e commit

| Voce | Valore |
|------|--------|
| Branch lavoro | `cursor/b2c-public-hardening-b894` |
| Worktree | `/agent/repos/omnia2-integration-d193-cmj-a4` |
| Commit codice hardening | `95eb8ad25e96b79e5d40689584723b00ecad3f0f` |
| PR | [#248](https://github.com/mcnicastro-netizen/omnia2/pull/248) → base `main` (non mergiata in questo ciclo) |
| Commit report | tip branch (file presente su `cursor/b2c-public-hardening-b894`) |

Operazioni **non** eseguite: merge su `main`, deploy produzione, chiusura/modifica PR estranei.

---

## 3. Difetti riprodotti

| ID | Difetto | Riproduzione pre-fix |
|----|---------|-------------------------|
| C1 | `GET /api/public/property/{pid}/photo/{idx}` usava filtro più debole di `portal_listing_filter` / `brand_site_filter` | Audit + codice `site.py` pre-hardening |
| C2 | Search/detail esponevano `agency.id` e/o `agency_id` | Audit dinamico + `_to_card` / detail publisher |
| C3 | `POST …/contact` restituiva `lead_id` e `client_id` | Codice `portal_contact.py` + test M3S4 |
| S1 | Resolver brand caricava documento agency ampio | `site.py` `_resolve` senza projection stretta |
| S2 | `Cache-Control: public, max-age=86400` su foto | Rischio stale post-ritiro |
| D04 | `reference_code` doveva restare pubblico e coerente | Verifica superfici + privacy gate |

---

## 4. Diagnosi tecnica

### C1 / D02 — Foto
Autorità = backend. Le superfici ImmobilCloud e brand hanno SoT diverse (`portal_listing_filter` vs `brand_site_filter`). Il bug era un filtro foto generico più permissivo, aggirabile con PID+indice. Fix: ACL esplicita per `surface=portal|brand|mls_network` (+ `agency_slug` per brand).

### C2 / D01 — Agency ID
Proiezione pubblica accidentale dal documento Mongo. Fix: `AGENCY_PUBLIC_PROJ` + `public_agency_card()` + `strip_internal_property_fields()`; `_to_card` / detail / HTML brand senza `agency_id` / `agency.id`. Gli ID restano interni a query/authz tenant-scoped.

### C3 / D03 — Contatto
Risposta anonima esponeva ID CRM. Fix: return `{"ok": true}` soltanto; lead/client creati internamente invariati.

### S1 — HTML brand
`_resolve` ora usa projection stretta (campi rendering + `id`/`mls_enabled` solo server-side per query). HTML verificato senza UUID agency né campi riservati iniettati nel seed (`password_hash_should_never_leak`, `stripe_customer_id`).

### S2 — Cache
Header foto portato a `public, max-age=60, must-revalidate`. **Non** esiste invalidazione CDN Railway/Vercel dedicata in-app: documentato come dipendenza infrastrutturale. TTL ridotto mitiga stale; purge CDN = fuori capacità codice.

### D04 — `rif.`
Campo canonico: `reference_code` (codici `OM-L-…` via `ensure_unique_code` / listing code). Esposto in card, detail, brand HTML, form prefill. Se assente → `—` / omesso, senza codice artificiale.

---

## 5. Correzioni effettuate

1. **Photo ACL per superficie** in `serve_property_photo` + helper `portal_photo_filter` / `brand_photo_filter`.
2. **Proiezione agency pubblica** centralizzata; strip ID interni dai payload pubblici.
3. **Contact opaco** `{"ok": true}`.
4. **Brand resolver** projection stretta; temi HTML senza leak ID.
5. **Cache foto** `max-age=60, must-revalidate`.
6. **Privacy gate** conserva `reference_code` su L1/L2 pubblici.
7. **Test** `test_b2c_public_hardening.py` + aggiornamenti M3S4/public/privacy.

---

## 6. File modificati

```
backend/apps/immocloud/portal_common.py
backend/apps/immocloud/portal_contact.py
backend/apps/immocloud/portal_detail.py
backend/apps/immoweb/site.py
backend/apps/immoweb/theme_common.py
backend/apps/immoweb/theme_home.py
backend/apps/immoweb/theme_render.py
backend/shared/db/public_visibility.py
backend/shared/utils/privacy_gate.py
backend/tests/test_b2c_public_hardening.py          (nuovo)
backend/tests/test_immobilcloud_m3s4_contact.py
backend/tests/test_immobilcloud_public.py
backend/tests/test_m3s9_privacy_audit.py
docs/reports/AUDIT-MIRATO-B2C-IMMOBILCLOUD.md
docs/reports/B2C-IMMOBILCLOUD-PUBLIC-HARDENING-STAGING-DEEP.md  (questo)
```

Nessuna modifica FE obbligatoria: `PropertyDetailPage` già usa `prop.reference_code`; contatto già tollera risposta opaca.

---

## 7. Test aggiunti

File: `backend/tests/test_b2c_public_hardening.py`

Copertura (mapping requisiti §5 autorizzazione):

| # | Caso | Test |
|---|------|------|
| 1–8 | Foto portal/brand/bypass | `test_d02_*`, filtri portal vs brand |
| 9–14 | Agency / rif. | `test_d01_*`, `test_d04_*` |
| 15–16 | Contatto opaco | `test_d03_*` + M3S4 aggiornato |
| 27–29 | FE consumers | verifica codice FE + browser staging |

Multi-tenant 22–26: verificati in staging-deep (clienti A/B, cross-slug 404, owner draft escluso; matching D-126 / free tier = **PASS codice** preesistente, non ri-eseguiti end-to-end mutativi oltre seed owner).

---

## 8. Test eseguiti e risultati

### Locale (codice)

| Comando | Esito |
|---------|-------|
| `pytest tests/test_b2c_public_hardening.py tests/test_s4_public_visibility.py tests/test_private_listing_mls_isolation.py -q` | **20 passed** — log `/opt/cursor/artifacts/b2c-local-unit-pass.log` |
| Suite hardening dedicata precedente | **11 passed** — `b2c-hardening-unit*.log` |
| `tests/test_immobilcloud_m3s4_contact.py` (integration su `127.0.0.1:43121` + fixture UUID fissa) | **FAIL/ERROR ambiente** — property seed `3b81db11-…` assente in DB locale; non regressione del fix D01/D03 (asserzioni aggiornate). **NOT VERIFIED** in questo ambiente |

### Staging-deep HTTP (sintetico)

| Harness | Esito |
|---------|-------|
| `/tmp/b2c_staging_deep_v2.py` + recheck city/login/CRM | **48 PASS** su check consolidati (4 check iniziali superati/riscritti: `q=RUN` non matchava title; email seed mixed-case vs login `.lower()`) |
| Log | `/opt/cursor/artifacts/b2c-staging-deep-v2.log`, summary `b2c-staging-deep-summary.json` |
| Evidence HTTP | `/opt/cursor/artifacts/b2c-http-evidence.json` |

Run sintetico: `b2c5cda259f` · DB `omnia_staging_e2e` · cleanup eseguito post-verifica (`session_tag=b2c_harden`).

---

## 9. Regressioni

| Area | Esito |
|------|-------|
| Search/detail pubblici | OK — senza agency ID interni |
| Brand HTML / sitemap | OK |
| Contatto + lead interno | OK |
| Foto ACL | OK |
| Owner listing autopublish su portale | OK (intenzionale D-137) |
| FE staging esistente vs API nuova | OK (rif. + contatto opaco) |
| M3S4 integration locale senza fixture | ambiente — non bloccante sul codice hardening |

---

## 10. Staging e SHA effettivamente distribuito

| Servizio | Dettaglio |
|----------|-----------|
| API pubblica | `https://omnia-api-production-85845f42.up.railway.app` |
| Railway service | `omnia-api` deployment `445a50a2-67f1-44f0-8105-006e6bb607a5` |
| Twin | `omnia-api-w4b` deployment `fe8139b1-91d2-4f13-aa1b-4b545c2bd92a` |
| Codice sorgente deployato | branch `cursor/b2c-public-hardening-b894` @ `95eb8ad…` (railway up da worktree) |
| OpenAPI live | `surface` enum `portal\|brand\|mls_network` presente su photo path |
| FE | `https://omnia-frontend-staging.vercel.app` — **nessun redeploy FE** (nessun diff FE in ciclo) |
| DB | `DB_NAME=omnia_staging_e2e` (label Railway “production” ≠ prod commerciale) |
| Merge main | **non eseguito** |

---

## 11. Evidenze HTTP / API / browser

### HTTP/API (sintesi)

| Check | Esito |
|-------|-------|
| Search `city=Catania` include pub A, pub B, owner published | PASS |
| Search esclude private / pending / owner draft | PASS |
| Nessun `agency_id` / `agency.id` in items | PASS |
| `reference_code` presente (`OM-L-DA259F`, `OM-L-B00001`, `OM-L-OWNPUB`) | PASS |
| Detail pubblico 200; private/pending/draft 404 | PASS |
| Foto portal pubblica 200; private/pending 404 | PASS |
| Foto brand + `agency_slug` corretta 200; cross-agency 404 | PASS |
| `Cache-Control: public, max-age=60, must-revalidate` | PASS |
| Brand index/prop HTML senza org UUID / secret seed | PASS |
| Brand prop mostra `Rif. OM-L-DA259F`; photo URL `surface=brand` | PASS |
| Sitemap include pub, esclude private | PASS |
| Contact `{"ok": true}` senza lead/client id; lead+client in Mongo su agency A | PASS |
| Contact su private → 404 | PASS |
| Post-withdraw foto/detail/brand → 404 | PASS |
| Login agency A (email lower) + `/api/app/clients` vede buyer A; B non vede buyer A | PASS |

### Browser (Playwright headless)

| Step | File | Esito |
|------|------|-------|
| FE search Catania | `b2c-fe-search.png` | PASS — 3 card sintetiche, agency name commerciale, no ID interni |
| FE detail | `b2c-fe-detail.png` | PASS — **RIF. OM-L-DA259F** |
| FE contact submit | `b2c-fe-contact.png` | PASS — “Richiesta inviata!” opaca |
| Brand index | `b2c-brand-index.png` | PASS |
| Brand prop | `b2c-brand-prop.png` | PASS — Rif. in header + griglia + prefill form |
| FE private | `b2c-fe-private.png` | PASS — non scheda pubblica completa |
| Meta | `b2c-browser-evidence.json` | — |

Nota: computerUse GUI agent non disponibile (quota modello); evidenza browser via Playwright. Registrazione video GUI non prodotta.

---

## 12. Isolamento multi-tenant

| Check | Esito |
|-------|-------|
| Agenzia A ≠ B su search (entrambe pubbliche visibili anon, dati CRM separati) | PASS |
| Brand slug B non serve prop di A | PASS (404) |
| Client/lead contatto solo su `agency_id` A | PASS |
| `/api/app/clients` come admin A vede buyer; admin B `items=[]` | PASS |
| Owner draft non in portale; owner published sì (D-137) | PASS |
| Proprietario / free tier / matching D-126 mutativo completo | **PASS codice** preesistente · staging mutativo deep matching **parziale** (seed owner published only) |

---

## 13. Verifica foto e cache

| Scenario | Esito |
|----------|-------|
| Pubblico approved portal | 200 |
| Private / pending / draft / withdrawn | 404 |
| Brand corretto | 200 |
| Brand cross-tenant | 404 |
| Default surface senza bypass private | 404 |
| Cache header mitigato | `max-age=60, must-revalidate` |
| Purge CDN esplicita | **NOT VERIFIED / N/A codice** — dipendenza infra; documentata |

Foto 1×1 JPEG sintetica: ACL HTTP verificata; rendering FE può apparire “bianco” (payload minimo) — non confondere con bypass.

---

## 14. Verifica HTML brand

| Check | Esito |
|-------|-------|
| Index/prop 200 con nome commerciale | PASS |
| Assenza `agency_id` / UUID org nel HTML | PASS |
| Assenza campi riservati seed (`SECRET_HASH_FAKE`, `cus_FAKE`) | PASS |
| `Rif. OM-L-…` in scheda e form | PASS |
| Projection resolver stretta | PASS codice + HTML |

---

## 15. Verifica contatti e lead

| Check | Esito |
|-------|-------|
| Risposta `{"ok": true}` | PASS |
| Nessun `lead_id` / `client_id` | PASS |
| Lead+client creati su agency corretta | PASS |
| Non creati su agency B | PASS |
| Immobile non pubblico → 404 | PASS |
| FE conferma opaca | PASS browser |
| Rate limit / GDPR codice | **PASS codice** (invariati); load-test rate limit staging **NOT VERIFIED** in questo ciclo |

---

## 16. Verifica riferimento `rif.`

| Superficie | Esito |
|------------|-------|
| API search `reference_code` | PASS |
| API detail | PASS (`OM-L-DA259F`) |
| FE detail cella RIF. | PASS browser |
| Brand HTML + prefill “rif. OM-L-…” | PASS |
| Campo canonico | `reference_code` (non UUID property, non agency id) |
| Assenza valore | UI `—` / omesso — nessun codice artificiale introdotto |

---

## 17. Limiti e NOT VERIFIED

1. **Merge `main` / prod** — fuori perimetro (corretto).
2. **M3S4 integration locale** — fixture property assente → ERROR ambiente.
3. **Purge CDN** — non implementabile nel codice attuale.
4. **Rate-limit stress** e **email delivery** — non eseguiti (email reali vietate; Resend circuit già noisy in health).
5. **Matching privato D-126 end-to-end mutativo** oltre presenza owner listing — non rieseguito in toto in questo ciclo.
6. **Redeploy Vercel FE** — non necessario (nessun diff FE); SHA FE staging preesistente.
7. **computerUse / video demo GUI** — non disponibile (quota); sostituito da Playwright screenshot.
8. **Label Railway “production”** — ambiente staging tecnico `omnia_staging_e2e`, non prod commerciale.

---

## 18. Rischi residui

| Rischio | Livello | Nota |
|---------|---------|------|
| Cache/CDN stale ≤60s post-ritiro | basso | mitigato; purge manuale infra se serve |
| FE search card non sempre mostra `rif.` in griglia | basso | detail/brand sì; eventuale UX FE fuori scope se richiesto |
| Foto data-URI minime poco leggibili in UI | informativo | ACL HTTP ok |
| Deploy API da branch non-main | operativo | Founder deve decidere merge #248 |
| Twin `omnia-api-w4b` allineato | basso | deployato in ciclo |

---

## 19. Giudizio GTM aggiornato

| Ambito | Giudizio |
|--------|----------|
| Audit pre-ciclo | **NON GTM** |
| Hardening D01–D04 codice | **PASS** (implementato + unit) |
| Regressione automatica mirata | **PASS** (20 unit locali pertinenti) |
| Staging-deep sintetico HTTP | **PASS** |
| Staging browser (Playwright) | **PASS** |
| Isolamento tenant CRM contatto | **PASS** |
| GTM commerciale globale ImmobilCloud | **NON dichiarato** — Founder sign-off richiesto; restano limiti §17 |

**Sintesi onesta:** il perimetro autorizzato (hardening pubblico + staging-deep sintetico) è **tecnicamente verificato**. Non è una dichiarazione GTM di prodotto completo.

---

## 20. Prossimo passo tecnico

1. Founder review PR **#248** (`cursor/b2c-public-hardening-b894`).
2. Se approvato: merge su `main` (autorizzazione separata) + eventuale redeploy FE solo se si aggiungono ritocchi UX `rif.` in search card.
3. Opzionale: re-seed fixture M3S4 locale / CI per ripristinare integration contact.
4. Opzionale: runbook purge cache CDN se TTL 60s insufficiente operativamente.
5. **Stop** — in attesa valutazione Founder. Nessun merge eseguito da questo agent.

---

## Appendice — mapping accettazione

| Criterio §8 | Stato |
|-------------|-------|
| Correzioni locali | PASS |
| Regressioni automatiche | PASS (suite mirata) |
| Isolamento multi-tenant | PASS staging |
| Foto authz | PASS |
| Contatto opaco | PASS |
| `rif.` pubblico | PASS |
| HTML brand | PASS |
| Staging-deep sintetico | PASS |
| Errori bloccanti hardening | nessuno residuo riproducibile nel perimetro |

Fine report.
