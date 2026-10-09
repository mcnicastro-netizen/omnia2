# Audit Portale — registro finding `P-###`

**Aggiornato**: 2026-10-09 · Onda H GREEN · P-037…P-045 aperti  
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
| P-031 | P0 | F | Regressione inventory: demo props `visibility=null` → search total=0 (P-001) | **CHIUSO** |
| P-032 | P3 | F | Route solo `/cloud/valutatore`; `/cloud/valuator` shell vuota | **APERTO** |
| P-033 | P2 | G | Search lista card L3/L4 anche se detail anon = 404 | **APERTO** (dopo) |
| P-034 | P2 | G | Sito brand `/api/p/{slug}` ignora visibility/listing/privacy/moderation | **WONTFIX** (by design) |
| P-035 | P2 | G | Ops `saved_searches_active` query `active` ≠ schema `is_active` | **CHIUSO** |
| P-036 | P3 | G | HAL Legal CRM non addebita listino 12 crediti | **CHIUSO** |
| P-037 | P1 | H | Informativa privacy senza sub-responsabili / transfer extra-UE / no-train | **APERTO** |
| P-038 | P2 | H | DSAR B2C: export 404 + rettifica anagrafica assente | **APERTO** |
| P-039 | P2 | H | `marketing_consent` dedicato assente (privacy lo cita) | **APERTO** |
| P-040 | P2 | H | Nessun age gate 18+ su register B2C | **APERTO** |
| P-041 | P2 | H | No TTL Mongo su `al_legal_audit` / `consent_events` / ledger `b2c_purchases` | **APERTO** |
| P-042 | P2 | H | Email PII in chiaro in `api.log` | **APERTO** |
| P-043 | P2 | H | Staging: watermark OK ma disclosure pubblica scheda debole | **APERTO** |
| P-044 | P2 | H | Valuator lead (`valuation_leads`) senza `gdpr_consent` | **APERTO** |
| P-045 | P3 | H | Valuator senza CTA “contesta stima” (human oversight) | **APERTO** |

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

## P-031 — dettaglio (CHIUSO · vai Founder 9-Ott)

- **Fix**: re-seed `seed_demo_gestionale.py` + `seed_nicastro_agency.py` · `omnia-stack ensure` ora richiama seed se `GET /cloud/search` total=0
- **Verifica**: QC `match_base_filter=8` · search `total=8` · favorite 201 · contact 200
- Artefatti: `/opt/cursor/artifacts/p031-seed.log` · `p031-qc.log` · `p031-property-cta.log`

## P-032 — dettaglio (APERTO · Onda F)

- Nav/SoT: `/:lang/cloud/valutatore` (`ImmocloudApp.jsx`)
- Nessuna route `valuator` (EN) → SPA 200 con area contenuto vuota (nav+footer restano)
- **Fix** (solo con «vai»): alias route `valuator` → stessa `ValuatorPage` oppure redirect

## P-033 — dettaglio (APERTO · Onda G)

- `_base_filter()` in `public_portal.py` (search) **non** filtra `privacy_level`
- L3/L4 restano in card search; `GET /cloud/property/{id}` anon → 404 (gate OK)
- **Evidenza**: `demo-prop-roma-01` L3 · in_search Roma=True · anon detail 404
- **Fix** (solo con «vai»): escludere L3/L4 da search anon, oppure mostrare card “richiede accesso”

## P-034 — dettaglio (WONTFIX · Founder 9-Ott)

- Brand SSR filtra solo `agency_id` + `status=active` — vetrina CRM distinta da ImmobilCloud
- Decisione Founder: **no** allineare ai flags cloud

## P-035 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `founder_ops.py` conta `{"is_active": True}`
- **Verifica**: `test_p035_p036_legal_ops.py` · overview = mongo count

## P-036 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `_ensure_legal_payment` — B2C Stripe €1 invariato; CRM con `active_agency_id` → `debit_credits(..., 12, reason=hal_legal_query)` su chat + analyze-pdf
- Response/audit: `payment_rail`, `credits_charged`
- **402** `insufficient_credits` se wallet < 12
- **Verifica**: pytest debit 100→88 · insufficient 402

## P-037 — dettaglio (APERTO · Onda H)

- `cloud.legal_privacy_body` (it.json): titolare + categorie + diritti email — **nessun** elenco Stripe/Resend/OpenAPI/Gemini/Tavily/fal/Kling
- Zero menzione trasferimenti extra-UE / SCC; zero claim «non usiamo dati per training»
- **Fix** (solo «vai» + preferibilmente legale): riscrivere informativa; allineare en/es

## P-038 — dettaglio (APERTO · Onda H)

- `GET /auth/me/export` → 404; erase OK (`POST /auth/me/erase` + UI)
- Nessuna UI B2C per rettifica nome/email (solo notification prefs)
- **Fix**: endpoint export JSON + form rettifica, oppure process documentato con SLA su privacy@

## P-039 — dettaglio (APERTO · Onda H)

- Privacy cita base «consenso (es. marketing/alert)» ma register non ha `marketing_consent`
- Alert = intent `get_alerts` / prefs — non opt-in marketing distinto

## P-040 — dettaglio (APERTO · Onda H)

- `CloudRegisterPage` / `cloud_auth.py`: nessun checkbox 18+ / DOB

## P-041 — dettaglio (APERTO · Onda H)

- Nessun indice TTL su `al_legal_audit`, `consent_events`, `b2c_purchases`
- UNI entitlement ha TTL feature 24h in codice (OK parziale)

## P-042 — dettaglio (APERTO · Onda H)

- Tail `/tmp/omnia-stack/api.log`: email in chiaro (register/contact/reset paths)
- **Fix**: redact PII in logger / structured logging

## P-043 — dettaglio (APERTO · Onda H)

- Watermark server «Render virtuale OMNIA» presente
- Scheda pubblica `PropertyDetailPage` senza label chiara «immagine generata / non reale»

## P-044 — dettaglio (APERTO · Onda H)

- `valuator.py` → `valuation_leads` con name/email **senza** campo/gate `gdpr_consent`

## P-045 — dettaglio (APERTO · Onda H)

- Valuator: disclaimer stima OK; nessun CTA «contesta / segnala errore»

## P-012…P-017 — fix breve

| ID | Fix |
|--|--|
| P-012 | Valuator → `/${lang}/login?next=…`; checkout URLs con lang |
| P-013 | TopNav sell → `account/sell` se B2C loggato |
| P-014 | Register rispetta `?next=` same-origin |
| P-015 | sid in sessionStorage; link success senza query; Visura legge storage |
| P-016 | checkbox GDPR obbligatorio su lead mutui |
| P-017 | menu mobile `cloud-nav-menu` |
