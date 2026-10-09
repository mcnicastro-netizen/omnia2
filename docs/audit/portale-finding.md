# Audit Portale — registro finding `P-###`

**Aggiornato**: 2026-10-09 · Onda F bottoni · P-031/P-032 aperti  
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
| P-018 | P1 | C | Vault Cloud incompleto vs runtime (Stripe/OPENAPI solo `.env`) | MITIGATO |
| P-019 | P2 | C | `FRONTEND_*` / `OMNIA_PUBLIC_URL` = localhost:43122 | CHIUSO |
| P-020 | P3 | C | `check-secrets` non copre `OPENAPI_*` / Stripe dogfood | CHIUSO |
| P-021 | P3 | C | `GOOGLE_CLIENT_ID` absent — login Google OFF | APERTO (opz.) |
| P-022 | P0 | D | Stripe **live** in Cloud (`sk_live`/`pk_live`, plans `mode=live`) | **CHIUSO** |
| P-023 | P1 | D | OpenAPI key OK ma product `openapi_visure_enabled=false` (manca email / D-116) | **CHIUSO** |
| P-024 | P3 | D | Env/docs citano `gemini-2.0-flash` deprecato; product HAL OK | APERTO |
| P-025 | P2 | D/E | `b2c_purchases` paid senza `amount_eur` (Ops finance cieco su importo) | **CHIUSO** |
| P-026 | P3 | D | Vault `STRIPE_WEBHOOK_SECRET` ≠ secret endpoint auto-sync tunnel | **APERTO** |
| P-027 | P1 | E | Telemetry gap: eventi portale senza sink Ops (register/mutui/inquiry/digest/Visura fail) | **CHIUSO** |
| P-028 | P2 | E | `ops_alerts.acked` senza API/UI di ack (“da vedere” permanente) | **CHIUSO** |
| P-029 | P2 | E | Backup health `MISSING` in Cloud (nessuna cartella `.backups`) | **CHIUSO** |
| P-030 | P3 | E | Moderazione (e Legal) fuori nav Shell — solo URL / link interno Ops | **CHIUSO** |
| P-031 | **P0** | F | Regressione inventory: demo props `visibility=null` → search total=0 (P-001) | **APERTO** |
| P-032 | P3 | F | Route solo `/cloud/valutatore`; `/cloud/valuator` shell vuota | **APERTO** |

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

## P-018 — dettaglio (MITIGATO · automazione + azione vault una tantum)

- **Boot auto**: `stripe-vault-materialize.py` upsert anche `OPENAPI_*`; `sync-stripe-webhook-url.py` crea/aggiorna endpoint test → `{tunnel}/api/billing/webhook`
- **Founder (una tantum)**: Cursor ha richiesto Save Secrets env omnia2 (Stripe sk/pk/whsec + OPENAPI_*). Dopo Save, ogni nuovo agent li riceve e materializza da solo.
- Finché vault incompleto, runtime continua a usare `.env` disk (warm) + WARN in check-secrets

## P-019 — dettaglio (CHIUSO)

- **Fix**: `scripts/sync-public-base-url.py` da `omnia-stack` quando tunnel healthy → upsert `FRONTEND_*` / `OMNIA_PUBLIC_URL`; restart API se CHANGED
- **Runtime**: `shared/public_base.get_public_base_url()` preferisce `SHARE_URL` tunnel su localhost env (email/alert)
- **Verifica**: base = trycloudflare corrente; `test_public_base_url.py` 2 passed

## P-020 — dettaglio (CHIUSO)

- `check-secrets-presence.sh`: JWT required; Stripe/OpenAPI dogfood condizionali; FRONTEND tunnel vs localhost; WARN nomi vault mancanti

## P-021 — dettaglio (APERTO opz.)

- `GOOGLE_CLIENT_ID` absent → Google Sign-In OFF (fail-soft). Opzionale dogfood.

## P-022 — dettaglio (CHIUSO · Onda D ripresa)

- **Chiusura**: vault Environment = `sk_test_` / `pk_test_`; plans `mode=test` `enabled=true`
- **Verifica**: checkout B2C `b2c_hal_legal_query` €1 → session `cs_test_…` · webhook signed → `b2c_purchases.status=paid`
- Log: `/opt/cursor/artifacts/onda-d-live-stripe-openapi.log`

## P-023 — dettaglio (CHIUSO · Onda D ripresa)

- **Chiusura**: merge D-116 (PR #10) su branch audit — `auth_mode=oauth_single_key` (key + `ADMIN_EMAIL`)
- **Verifica**: ping Catasto sandbox 200 · create Visura · PDF 58054 byte · catalog `openapi_enabled=true`
- **Follow-up Founder**: merge PR #10 su `main` se non già fatto (questa ripresa lo usa sul branch audit)

## P-024 — dettaglio (APERTO · Onda D)

- Raw Generative Language su `gemini-2.0-flash` → 404 “no longer available”
- Product: `POST /api/app/hal/knowledge/ask` 200 con `GEMINI_API_KEY`
- Azione: allineare `.env.example` / commenti al default `shared/llm` (flash-latest / 3.5) — P3

## P-025 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `mark_uni_purchase_paid(amount_eur=…)` · webhook legge `session.amount_total/100` · fallback catalogo · backfill overview
- **Verifica**: `b2c_revenue_eur` > 0 con paid · `tests/test_ops_portal_gaps.py`

## P-026 — dettaglio (APERTO · Onda D)

- **Evidenza**: `sync-stripe-webhook-url.py` CREATED endpoint → nuovo `whsec` in `.env`; vault process resta sul whsec precedente (hash diversi, stessa len)
- Run audit: API avviata con whsec `.env` allineato all’endpoint tunnel
- **Azione Founder**: aggiornare vault `STRIPE_WEBHOOK_SECRET` al secret dell’endpoint “OMNIA Cloud Agent portal (auto-sync)” (o disabilitare endpoint orfani)

## P-027 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `ops/overview.portal` (register, mutui, inquiry UGC, digest runs, visura fail/orders, UGC pending, invoices count, paid) · card UI · `record_alert(kind=openapi_visura)` su fulfill fail
- **Verifica**: overview live + pytest · A-038 resta post-test

## P-028 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `POST /api/app/ops/alerts/{id}/ack` · `POST /api/app/ops/alerts/ack-all` · bottoni «Visto» / «Segna tutti visti»
- **Verifica**: ack-all → `unacked=0`

## P-029 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `POST /api/app/ops/backup/run` · bottone «Esegui ora» se status ≠ OK
- **Verifica**: run → `backup.status=OK` · day corrente

## P-030 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `AgencyShell` super_admin — voci Ops Legal + Moderazione · link in card portale Ops

## P-031 — dettaglio (APERTO · Onda F)

- **Evidenza**: `qc_public_portal_inventory.py` → `match_base_filter=0`; `GET /api/cloud/search` `total=0`
- Mongo: 8 props `is_listed_on_immobilcloud=true` ma **`visibility=null`** (0 `visibility=public`)
- Seed script ha già `"visibility":"public"` + upsert `$set` — **non rieseguito** su questo boot / DB stale
- **Impatto**: search/schede/property CTA Onda F non dogfoodabili; portale vuoto come P-001
- **Fix** (solo con «vai»): `python backend/scripts/seed_demo_gestionale.py` (o ensure-seed in boot Cloud) + QC `match_base_filter>0`

## P-032 — dettaglio (APERTO · Onda F)

- Nav/SoT: `/:lang/cloud/valutatore` (`ImmocloudApp.jsx`)
- Nessuna route `valuator` (EN) → SPA 200 con area contenuto vuota (nav+footer restano)
- **Fix** (solo con «vai»): alias route `valuator` → stessa `ValuatorPage` oppure redirect

## P-012…P-017 — fix breve

| ID | Fix |
|--|--|
| P-012 | Valuator → `/${lang}/login?next=…`; checkout URLs con lang |
| P-013 | TopNav sell → `account/sell` se B2C loggato |
| P-014 | Register rispetta `?next=` same-origin |
| P-015 | sid in sessionStorage; link success senza query; Visura legge storage |
| P-016 | checkbox GDPR obbligatorio su lead mutui |
| P-017 | menu mobile `cloud-nav-menu` |
