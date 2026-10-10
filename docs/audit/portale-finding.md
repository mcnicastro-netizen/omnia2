# Audit Portale — registro finding `P-###`

**Aggiornato**: 2026-10-09 · D-118 residuo codice **CHIUSO** · P-021 opz. · P-026 MITIGATO  
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
| P-024 | P3 | D | Env/docs citano `gemini-2.0-flash` deprecato; product HAL OK | **CHIUSO** |
| P-025 | P2 | D/E | `b2c_purchases` paid senza `amount_eur` (Ops finance cieco su importo) | **CHIUSO** |
| P-026 | P3 | D | Vault `STRIPE_WEBHOOK_SECRET` ≠ secret endpoint auto-sync tunnel | **MITIGATO** |
| P-027 | P1 | E | Telemetry gap: eventi portale senza sink Ops (register/mutui/inquiry/digest/Visura fail) | **CHIUSO** |
| P-028 | P2 | E | `ops_alerts.acked` senza API/UI di ack (“da vedere” permanente) | **CHIUSO** |
| P-029 | P2 | E | Backup health `MISSING` in Cloud (nessuna cartella `.backups`) | **CHIUSO** |
| P-030 | P3 | E | Moderazione (e Legal) fuori nav Shell — solo URL / link interno Ops | **CHIUSO** |
| P-031 | P0 | F | Regressione inventory: demo props `visibility=null` → search total=0 (P-001) | **CHIUSO** |
| P-032 | P3 | F | Route solo `/cloud/valutatore`; `/cloud/valuator` shell vuota | **CHIUSO** |
| P-033 | P2 | G | Search lista card L3/L4 anche se detail anon = 404 | **CHIUSO** |
| P-034 | P2 | G | Sito brand `/api/p/{slug}` ignora visibility/listing/privacy/moderation | **CHIUSO S4** — `brand_site_filter` = surface pubblica condivisa; delta intenzionali in `public_visibility.py` |
| P-035 | P2 | G | Ops `saved_searches_active` query `active` ≠ schema `is_active` | **CHIUSO** |
| P-036 | P3 | G | HAL Legal CRM non addebita listino 12 crediti | **SUPERSEDED D-119** (incluso piano) |
| P-037 | P1 | H | Informativa privacy senza sub-responsabili / transfer extra-UE / no-train | **CHIUSO** |
| P-038 | P2 | H | DSAR B2C: export 404 + rettifica anagrafica assente | **CHIUSO** |
| P-039 | P2 | H | `marketing_consent` dedicato assente (privacy lo cita) | **CHIUSO** |
| P-040 | P2 | H | Nessun age gate 18+ su register B2C | **CHIUSO** |
| P-041 | P2 | H | No TTL Mongo su `al_legal_audit` / `consent_events` / ledger `b2c_purchases` | **CHIUSO** |
| P-042 | P2 | H | Email PII in chiaro in `api.log` | **CHIUSO** |
| P-043 | P2 | H | Staging: watermark OK ma disclosure pubblica scheda debole | **CHIUSO** |
| P-044 | P2 | H | Valuator lead (`valuation_leads`) senza `gdpr_consent` | **CHIUSO** |
| P-045 | P3 | H | Valuator senza CTA “contesta stima” (human oversight) | **WONTFIX** |
| P-046 | P1 | I | Backup giornaliero senza collection B2C (`b2c_*`, consent, favorites, …) | **CHIUSO** |
| P-047 | P2 | I | Restore manual non menziona dati portale B2C/UGC | **CHIUSO** |
| P-048 | P2 | I | Delete annuncio privato = hard delete (no cestino) | **CHIUSO** |
| P-049 | P1 | I | B2C `/billing/b2c/status` senza Stripe retrieve se webhook manca | **CHIUSO** |
| P-050 | P2 | I | Rate limit assente su register B2C e Visura checkout | **CHIUSO** |
| P-051 | P1 | I | `COOKIE_SECURE=false` Cloud → CSRF middleware no-op su HTTPS tunnel | **CHIUSO** |
| P-052 | P3 | I | Nessun handler UX globale API down / network error | **CHIUSO** |
| P-053 | P3 | I | Alert `stripe_webhook` senza dedup/cooldown | **CHIUSO** |
| P-054 | P2 | J | i18n incompleta Visura/checkout/Legal EN-ES/Sell staging ES | **CHIUSO** |
| P-055 | P2 | J | SEO scheda: title/OG generici (non per-property) | **CHIUSO** |
| P-056 | P3 | J | Tunnel/demo `index,follow` — manca noindex non-prod | **CHIUSO** |
| P-057 | P2 | J | UGC approve/reject senza notifica owner | **CHIUSO** |
| P-058 | P3 | J | Nessun runbook ops tunnel morto / webhook | **CHIUSO** |

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

## P-024 — dettaglio (CHIUSO · vai Founder)

- Raw Generative Language su `gemini-2.0-flash` → 404 “no longer available”
- Product: `POST /api/app/hal/knowledge/ask` 200 con `GEMINI_API_KEY`
- Azione: allineare `.env.example` / commenti al default `shared/llm` (flash-latest / 3.5) — P3

## P-025 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `mark_uni_purchase_paid(amount_eur=…)` · webhook legge `session.amount_total/100` · fallback catalogo · backfill overview
- **Verifica**: `b2c_revenue_eur` > 0 con paid · `tests/test_ops_portal_gaps.py`

## P-026 — dettaglio (MITIGATO · vai Founder)

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

## P-032 — dettaglio (CHIUSO · vai Founder)

- Nav/SoT: `/:lang/cloud/valutatore` (`ImmocloudApp.jsx`)
- Nessuna route `valuator` (EN) → SPA 200 con area contenuto vuota (nav+footer restano)
- **Fix** (solo con «vai»): alias route `valuator` → stessa `ValuatorPage` oppure redirect

## P-033 — dettaglio (CHIUSO · vai Founder)

- `_base_filter()` in `public_portal.py` (search) **non** filtra `privacy_level`
- L3/L4 restano in card search; `GET /cloud/property/{id}` anon → 404 (gate OK)
- **Evidenza**: `demo-prop-roma-01` L3 · in_search Roma=True · anon detail 404
- **Fix** (solo con «vai»): escludere L3/L4 da search anon, oppure mostrare card “richiede accesso”

## P-034 — dettaglio (CHIUSO S4 · 10-Ott — supersede WONTFIX 9-Ott)

- Prima: brand SSR solo `agency_id` + `status=active` (WONTFIX 9-Ott)
- **S4** (sequenza coerenza, vai Founder): surface pubblica condivisa
  `active` + `visibility=public` + moderation OK — SoT `public_visibility.py`
- Delta intenzionali restano: opt-out ImmobilCloud e L3/L4 ammessi sul brand
- Spec: `OMNIA_S4_VISIBILITA_PUBBLICA.md`

## P-035 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `founder_ops.py` conta `{"is_active": True}`
- **Verifica**: `test_p035_p036_legal_ops.py` · overview = mongo count

## P-036 — dettaglio (SUPERSEDED · D-119)

- **Fix originale**: CRM debit 12 crediti — in tensione con D-075
- **10-Ott-2026 D-119**: Founder conferma Legal CRM **incluso**; gate = `agency_included` / 0 crediti; B2C €1 e API Track B invariati
- Response/audit: `payment_rail=agency_included`, `credits_charged=0`
- **Verifica**: `test_d119_agency_legal_included_no_debit` · `test_legal_agency_included_no_debit`

## P-037 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `legal_privacy_body` IT/EN/ES — sub-responsabili, transfer extra-UE, no-train AI, diritti export
- Nota: testo prodotto aggiornato; revisione legale esterna resta consigliata

## P-038 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `GET /auth/me/export` · `PATCH /auth/me` (nome + marketing) · UI SecuritySettingsPanel (salva + scarica JSON)

## P-039 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `marketing_consent` su register + opt-in/out in profilo · `consent_events`

## P-040 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `age_confirmed` obbligatorio register (API 400 + checkbox FE)

## P-041 — dettaglio (CHIUSO · vai Founder)

- **Fix**: campo BSON `expire_at` + indici TTL su consent (10y), al_legal_audit (5y), b2c_purchases (90d pending / 7y paid)

## P-042 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `shared/privacy/log_redact.py` + install in `server.py` → email → `[REDACTED_EMAIL]`

## P-043 — dettaglio (CHIUSO · vai Founder)

- **Fix**: photo pubblica espone `is_virtual_staging` · badge scheda «Render virtuale…»

## P-044 — dettaglio (CHIUSO · vai Founder)

- **Fix**: `gdpr_consent` obbligatorio se name+email sul valuator (400) · log consent

## P-045 — dettaglio (WONTFIX · Founder)

- Nessun bottone «contesta stima» — by design (disclaimer stima sufficiente)

## P-046 — dettaglio (CHIUSO · vai Founder)

- `backup_job._COLLECTIONS`: agencies/users/properties/CRM… — **mancano** `b2c_purchases`, `b2c_visura_orders`/`visura_orders`, `consent_events`, `favorites`, `saved_searches`, `al_legal_audit`, `listing_inquiries`
- Media locali sì; ledger B2C no → restore non riporta pagamenti/consensi portale
- **Fix** (solo «vai»): estendere `_COLLECTIONS` + verificare MANIFEST

## P-047 — dettaglio (CHIUSO · vai Founder)

- `docs/ops/RESTORE_MANUAL.md` perimetro agency-first; zero menzione `b2c_*` / UGC
- **Fix**: aggiornare runbook allineato a P-046

## P-048 — dettaglio (CHIUSO · vai Founder)

- `private_listings.py` DELETE → `properties.delete_one` (hard)
- CRM ha cestino soft-delete; B2C no
- **Fix**: soft-delete `withdrawn`/`deleted_at` + retention, oppure conferma UI “irreversibile”

## P-049 — dettaglio (CHIUSO · vai Founder)

- `GET /billing/b2c/status/{session_id}` legge solo Mongo
- Agency `/billing/.../status` fa `Session.retrieve` Stripe
- Se webhook muore, poll B2C resta `pending` anche se Stripe paid
- **Fix**: retrieve Stripe + `mark_uni_purchase_paid` idempotente sul poll

## P-050 — dettaglio (CHIUSO · vai Founder)

- Inquiry 20/h OK (live 429); Legal 30/h OK
- `cloud_auth.register` e Visura checkout: **nessun** `enforce_ip_rate_limit`
- **Fix**: rate limit IP (es. register 10/h, visura checkout 20/h)

## P-051 — dettaglio (CHIUSO · vai Founder)

- Runtime/disk: `COOKIE_SECURE=false` → `csrf_enabled()=False` → middleware no-op
- Live tunnel: PATCH `/auth/me` **senza** `X-CSRF-Token` → **200**
- Su trycloudflare HTTPS andrebbe `COOKIE_SECURE=true` + SameSite=None + CSRF enforce
- **Fix**: `omnia-stack` / sync-public-base imposta `COOKIE_SECURE=true` quando tunnel HTTPS; restart API

## P-052 — dettaglio (CHIUSO · vai Founder)

- `api.js` gestisce 401+refresh; network/5xx/timeout senza UX globale
- ErrorBoundary copre solo crash React
- **Fix**: interceptor → evento `omnia:api-unreachable` + banner cloud

## P-053 — dettaglio (CHIUSO · vai Founder)

- Webhook signature fail → `record_alert(kind=stripe_webhook)` ogni volta, no dedup
- **Fix**: cooldown / upsert per kind+day


## P-054 — dettaglio (CHIUSO · vai Founder)

- Visura UI hardcode IT; nav label senza `t()`
- Checkout success/cancel: chiavi solo fallback IT in `t()`, non nei JSON locale
- Legal: gap EN/ES; Sell `staging_*` assenti in ES
- **Fix**: portare stringhe in `locales/{it,en,es}.json` + parity test

## P-055 — dettaglio (CHIUSO · vai Founder)

- Live tunnel: `/it/cloud/property/demo-prop-roma-01` → title/OG = home generica ImmobilCloud
- `PropertyDetailPage` senza Helmet/`document.title` per-annuncio
- **Fix**: SSR/meta per title, description, og:image foto principale

## P-056 — dettaglio (CHIUSO · vai Founder)

- Preview/tunnel: `meta robots=index, follow`; `robots.txt` Allow /
- Rischio indicizzazione ambienti effimeri trycloudflare
- **Fix**: noindex se host tunnel / `OMNIA_ENV!=prod`

## P-057 — dettaglio (CHIUSO · vai Founder)

- Moderazione approve/reject aggiorna stato + notes; fanout saved-search su approve
- Nessuna `create_notification` / email all’owner UGC
- **Fix**: inbox (+ email) su approve/reject

## P-058 — dettaglio (CHIUSO · vai Founder)

- Automazione: `sync-stripe-webhook-url.py` + omnia-stack
- Manca runbook `docs/ops` “tunnel morto → nuovo URL → webhook → COOKIE_SECURE”
- **Fix**: doc ops breve collegata a P-026/P-051


## Chiusura residuo D-118 (vai Founder 9-Ott)

| ID | Fix |
|--|--|
| P-051 | `sync-public-base-url` → `COOKIE_SECURE=true` su tunnel HTTPS · CSRF enforce |
| P-049 | `b2c_status` Stripe `Session.retrieve` + `apply_b2c_purchase_side_effects` |
| P-046/047 | `backup_job._COLLECTIONS` B2C + `RESTORE_MANUAL.md` |
| P-050 | rate limit `cloud_register` 10/h · `cloud_visura_checkout` 20/h |
| P-033 | `_base_filter` esclude `privacy_level` L3/L4 |
| P-048 | soft-delete UGC (`deleted_at` + withdrawn) |
| P-054 | i18n Visura/checkout/Legal EN-ES/Sell staging ES |
| P-055 | SSR/meta per-property + `document.title` |
| P-057 | notify inbox owner su approve/reject |
| P-052 | evento `omnia:api-unreachable` + banner cloud |
| P-053 | `record_alert` dedupe 24h per `stripe_webhook` |
| P-032 | route alias `/cloud/valuator` |
| P-024 | `.env.example` → `gemini-3.5-flash` |
| P-056 | `noindex` su trycloudflare |
| P-058 | `docs/ops/TUNNEL_RUNBOOK.md` |
| P-026 | WARN sync whsec + runbook · vault Save resta Founder |
| P-021 | APERTO(opz.) — `GOOGLE_CLIENT_ID` assente in vault |

## P-012…P-017 — fix breve

| ID | Fix |
|--|--|
| P-012 | Valuator → `/${lang}/login?next=…`; checkout URLs con lang |
| P-013 | TopNav sell → `account/sell` se B2C loggato |
| P-014 | Register rispetta `?next=` same-origin |
| P-015 | sid in sessionStorage; link success senza query; Visura legge storage |
| P-016 | checkbox GDPR obbligatorio su lead mutui |
| P-017 | menu mobile `cloud-nav-menu` |
