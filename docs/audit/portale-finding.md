# Audit Portale — registro finding `P-###`

**Aggiornato**: 2026-10-08 · Onda B analisi (P-009…P-017 aperti)  
**Regola**: nessun fix senza «vai» Founder (D-118)

| ID | Sev | Onda | Titolo | Stato |
|--|--|--|--|--|
| P-001 | P0 | A | Search/schede vuote: seed `visibility` null + Nicastro trashed | CHIUSO |
| P-002 | P2 | A | Tunnel trycloudflare stale ma `tunnel_ok=true` | CHIUSO |
| P-003 | P2 | A | Register intents solo sell/rent_out/get_alerts (no buy) | CHIUSO |
| P-004 | P3 | A | `GET /api/ready` 404 | CHIUSO |
| P-005 | P1 | A | Footer B2C senza Privacy/Cookie/Termini | CHIUSO |
| P-006 | P3 | A | check-secrets shell ≠ uvicorn env | CHIUSO |
| P-007 | P2 | A | HAL Legal assente da CloudTopNav | CHIUSO |
| P-008 | P2 | A | Register email esistente → 409 (no auto-login) | CHIUSO |
| P-009 | P0 | B | Media `omnia/private/…` pubblici via `GET /api/media` | APERTO |
| P-010 | P1 | B | HAL Legal B2C senza gate pagamento (SKU €1) | APERTO |
| P-011 | P2 | B | `b2c_staging_render` paid senza consume path | APERTO |
| P-012 | P2 | B | Valuator `/it/cloud/login` morto + lang hardcode | APERTO |
| P-013 | P2 | B | TopNav Vendi → sempre register se loggato | APERTO |
| P-014 | P2 | B | Register ignora `?next=` | APERTO |
| P-015 | P2 | B | `session_id` Stripe in query URL | APERTO |
| P-016 | P3 | B | Mutui lead `gdpr_consent:true` hardcoded | APERTO |
| P-017 | P3 | B | CloudTopNav senza menu mobile | APERTO |

## P-001 — dettaglio

- **File**: `backend/apps/immocloud/public_portal.py` → `_base_filter()`
- **Sintomo**: `GET /cloud/search` → `total=0`; `GET /cloud/property/demo-prop-roma-01` → 404
- **Causa**: nessun documento soddisfa contemporaneamente `visibility=public`, not trashed, active, listed, mod∉pending/rejected
- **Impatto**: dogfood “cerca casa” inutilizzabile; inquiry/preferiti su scheda pubblica bloccati
- **Fix (vai 2026-10-08)**:
  1. `seed_demo_gestionale.py` + `seed_nicastro_agency.py`: `visibility:"public"` su ogni prop listata; upsert property con `$unset deleted_at/deleted_by`
  2. Re-seed → `match_base_filter=8`
  3. QC: `backend/scripts/qc_public_portal_inventory.py` (exit 1 se inventory=0)
- **Verifica**: `GET /api/cloud/search` → `total=8`; schede `demo-prop-roma-01` e `nicastro-prop-ct-01` → 200; FE proxy `43123` total=8

## P-002 — dettaglio

- **File**: `scripts/omnia-stack.sh` → `adopt_or_start_tunnel` / `ensure`
- **Fix**: non adottare URL trycloudflare senza `tunnel_alive`; se process up ma URL morto → kill + restart; `tunnel_ok=true` solo dopo probe live

## P-003 — dettaglio

- **File**: `backend/apps/immocloud/cloud_auth.py` (`Intent`) + `CloudRegisterPage.jsx` + i18n
- **Fix**: aggiunto intent `buy` (BE + FE + it/en/es)

## P-004 — dettaglio

- **File**: `backend/server.py`
- **Fix**: `GET /api/ready` alias di `/api/health/readiness`

## P-005 — dettaglio

- **File**: `FooterB2C.jsx`, `LegalDocPage.jsx`, route App.js `/:lang/{privacy,cookie,termini}`
- **Fix**: link footer + pagine statiche informativa/cookie/termini (i18n)

## P-006 — dettaglio

- **File**: `scripts/check-secrets-presence.sh`
- **Fix**: carica `backend/.env` per chiavi unset (parity con uvicorn dotenv); vault/process vince sul file

## P-007 — dettaglio

- **File**: `CloudTopNav.jsx`
- **Fix**: link `HAL Legal` → `/:lang/legal`

## P-008 — dettaglio

- **File**: `CloudRegisterPage.jsx`
- **Fix**: su 409 `email_already_registered` messaggio chiaro + link a `/:lang/login` (API resta 409; no auto-login)

## P-009 — dettaglio (Onda B)

- **File**: `backend/apps/immoweb/media.py` — `_PRIVATE_PREFIXES` copre solo `fascicolo`/`modulistica`, **non** `omnia/private/`
- **Evidenza**: listing privato con photo URL `/api/media/omnia/private/{uid}/photos/{id}.jpg` → `GET` anon **200** JPEG (~338 KB)
- **Impatto**: foto annunci privati B2C accessibili a chi conosce/guess URL (UUID riduce brute-force ma nessun AuthZ)
- **Fix proposto**: trattare `omnia/private/` come path protetto (404 pubblico) + endpoint autenticato owner-only; o signed URL TTL

## P-010 — dettaglio (Onda B)

- **File**: `al_legal/router.py` `POST /chat` / `analyze-pdf`; catalog `b2c_hal_legal_query` in `b2c_products.py`; webhook marca paid ma Legal non consulta `b2c_purchases`
- **Sintomo**: qualsiasi utente autenticato usa HAL Legal gratis (solo soft RL 30/h)
- **Fix proposto**: gate 402 se manca purchase paid non consumato; decremento/consume a chiamata

## P-011 — dettaglio (Onda B)

- **File**: `b2c_checkout.apply_b2c_purchase_side_effects` — staging/legal → solo `mark_uni_purchase_paid`
- **Fix proposto**: consume path in Sell staging job o documentare come “ledger-only WIP” e nascondere CTA se non pronto

## P-012 — dettaglio (Onda B)

- **File**: `ValuatorPage.jsx` → `/it/cloud/login` (route assente in ImmocloudApp; SPA shell 200 vuota/catch)
- **Fix proposto**: `/${lang}/login?next=…`; rimuovere hardcode `/it/` su checkout success/cancel

## P-013 — dettaglio (Onda B)

- **File**: `CloudTopNav.jsx` link sell sempre `register?intent=sell`
- **Fix proposto**: se `user.account_type===b2c` → `/${lang}/cloud/account/sell`

## P-014 — dettaglio (Onda B)

- **File**: `CloudRegisterPage.jsx` legge solo `intent`; Visura passa `?next=`
- **Fix proposto**: dopo register/login navigare a `next` se same-origin path

## P-015 — dettaglio (Onda B)

- **File**: `VisuraPage.jsx`, `CheckoutSuccessPage.jsx` — `session_id` in query
- **Impatto**: leak via Referer/history/screenshot; mitigato da bind `user_id` server-side
- **Fix proposto**: short-lived server token o storage session-only post-redirect

## P-016 — dettaglio (Onda B)

- **File**: `MortgageComparator.jsx` lead POST `gdpr_consent: true` fisso
- **Fix proposto**: checkbox obbligatorio legato al payload

## P-017 — dettaglio (Onda B)

- **File**: `CloudTopNav.jsx` — `nav` `hidden md:flex`, nessun hamburger
- **Fix proposto**: menu mobile accessibile con stessi link
