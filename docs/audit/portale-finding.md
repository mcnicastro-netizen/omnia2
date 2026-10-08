# Audit Portale — registro finding `P-###`

**Aggiornato**: 2026-10-08 · Onda C analisi secrets · P-018…P-021 aperti  
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
| P-009 | P0 | B | Media `omnia/private/…` pubblici via `GET /api/media` | CHIUSO |
| P-010 | P1 | B | HAL Legal B2C senza gate pagamento (SKU €1) | CHIUSO |
| P-011 | P2 | B | `b2c_staging_render` paid senza consume path | CHIUSO |
| P-012 | P2 | B | Valuator `/it/cloud/login` morto + lang hardcode | CHIUSO |
| P-013 | P2 | B | TopNav Vendi → sempre register se loggato | CHIUSO |
| P-014 | P2 | B | Register ignora `?next=` | CHIUSO |
| P-015 | P2 | B | `session_id` Stripe in query URL | CHIUSO (mitigato) |
| P-016 | P3 | B | Mutui lead `gdpr_consent:true` hardcoded | CHIUSO |
| P-017 | P3 | B | CloudTopNav senza menu mobile | CHIUSO |
| P-018 | P1 | C | Vault Cloud incompleto vs runtime (Stripe/OPENAPI solo `.env`) | APERTO |
| P-019 | P2 | C | `FRONTEND_*` / `OMNIA_PUBLIC_URL` = localhost:43122 | APERTO |
| P-020 | P3 | C | `check-secrets` non copre `OPENAPI_*` / Stripe dogfood | APERTO |
| P-021 | P3 | C | `GOOGLE_CLIENT_ID` absent — login Google OFF | APERTO |

## P-009 — dettaglio (CHIUSO)

- **Fix**: `media.py` — path `omnia/private/{user_id}/…` richiede sessione owner o `super_admin`; anon → 404
- **Verifica**: anon GET → 404; `test_b2c_media_upload` 4 passed (owner 200 + anon 404)
- Portale pubblico continua via `/api/public/property/{pid}/photo/{idx}`

## P-010 — dettaglio (CHIUSO)

- **Fix**: `consume_hal_legal_query` + gate in `al_legal` chat/analyze-pdf per clienti B2C; CRM agents skip
- **FE**: paywall + checkout `b2c_hal_legal_query` in `LegalApp.jsx`
- **Verifica**: B2C register → `POST /app/legal/chat` → **402** `legal_payment_required`

## P-011 — dettaglio (CHIUSO)

- **Fix**: `listing_id` obbligatorio su `b2c_staging_render` · `consume_b2c_staging_render` · webhook `fulfill_paid_staging_render` (job `payment_rail=b2c_stripe`, no debit crediti) · `POST/GET /cloud/me/properties/{pid}/staging` · SellPage resume post-`staging=ok` · auto-save foto watermarked sull’annuncio · success_url Stripe con `&session_id=` se già query
- **Verifica**: `test_b2c_staging.py` (catalog + consume + fulfill idempotent); checkout senza `listing_id` → 400

## P-018 — dettaglio (APERTO)

- `CLOUD_AGENT_ALL_SECRET_NAMES` = solo `FAL_KEY,GEMINI_API_KEY,RESEND_API_KEY,STRIPE_ENABLED`
- Runtime oggi OK perché `.env` disk ha `STRIPE_SECRET_KEY` (`sk_test`), `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, famiglia `OPENAPI_*`, `TAVILY_API_KEY`
- **Rischio**: boot su vault-only / env nuovo → billing 503 + Visura `openapi_not_configured`
- **Azione Founder**: reiniettare nomi in lista C.3 (`portale-matrici/2026-10-08-onda-c.md`)

## P-019 — dettaglio (APERTO)

- `FRONTEND_BASE_URL` / `FRONTEND_URL` / `OMNIA_PUBLIC_URL` = `http://127.0.0.1:43122`
- Preview/tunnel = `43123` / trycloudflare → link in email dogfood puntano a localhost
- Fix tipico: allineare a URL tunnel corrente (o rewrite in stack start) — serve «vai»

## P-020 — dettaglio (APERTO)

- `scripts/check-secrets-presence.sh`: REQUIRED solo Resend+Gemini; Stripe optional; **zero** `OPENAPI_*`
- Gap di diagnostica, non di runtime (se `.env` completo)

## P-021 — dettaglio (APERTO)

- `GOOGLE_CLIENT_ID` absent → Google Sign-In disabilitato (fail-soft). Opzionale dogfood.

## P-012…P-017 — fix breve

| ID | Fix |
|--|--|
| P-012 | Valuator → `/${lang}/login?next=…`; checkout URLs con lang |
| P-013 | TopNav sell → `account/sell` se B2C loggato |
| P-014 | Register rispetta `?next=` same-origin |
| P-015 | sid in sessionStorage; link success senza query; Visura legge storage |
| P-016 | checkbox GDPR obbligatorio su lead mutui |
| P-017 | menu mobile `cloud-nav-menu` |
