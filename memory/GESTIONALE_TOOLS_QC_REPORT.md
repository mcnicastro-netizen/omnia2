# Gestionale Tools QC Report

> **STALE (25-Set-2026)** — run del **18-Set**. Post A-028a…i: Attività ✅, Oggi ✅, cluster ✅, score explain ✅, match harden cap 400×400. Non usare Gaps/Top-5 sotto come coda. SoT: `GESTIONALE_ANALISI_2026-09-24.md` (rev. 25-Set). Rieseguire QC solo con «vai».

**Run**: 2026-09-18T07:42:54.553853+00:00 → 2026-09-18T07:53:49.631355+00:00 (reprobe merged + HAL/lead recover)
**User**: `{'role': 'super_admin', 'agency': 'demo-agency-001', 'email': 'mcnicastro@gmail.com'}`
**Preview healthz**: `{"ok": true, "preview": true, "api_origin": "http://127.0.0.1:43121", "api_ok": true, "api_status": 200, "crm_public_preview": false, "error": null}`
**Counts**: {'PASS': 69, 'GAP': 1, 'FAIL': 1, 'SKIP': 2}

## Verdict

- **PASS 69** / SKIP 2 / FAIL 1 / GAP 1
- Unico FAIL tecnico residuo: **A8 Matches list** agency-wide (perf bomb ~2M pairs sotto stress seed).
- CRM_PUBLIC_PREVIEW=false. Soft vendor: zero burn.

## Policy

- No Resend / Stripe checkout / fal generate / portal sync-now / Nominatim hammer
- CRM_PUBLIC_PREVIEW expected **false**

## Results

| Sec | Tool | Route | Status | HTTP | Detail |
|-----|------|-------|:------:|:----:|--------|
| A | A1 Dashboard KPIs | `/app/dashboard` | **PASS** | 200 | list n=6 |
| A | A1 Dashboard UI | `/it/app/dashboard` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| A | A2 Properties list | `/app/properties` | **PASS** | 200 | keys=['items', 'total', 'page', 'page_size'] total=2204 n=20 |
| A | A3 Property get | `/app/properties/b63a4274-0501-48c4-85fe-6517489d17d3` | **PASS** | 200 | keys=['created_at', 'updated_at', 'id', 'agency_id', 'title', 'description', 'reference_code', 'prop |
| A | A3 Property patch | `/app/properties/b63a4274-0501-48c4-85fe-6517489d17d3` | **PASS** | 200 | {"created_at":"2026-09-18T07:31:10.970232+00:00","updated_at":"2026-09-18T07:42:54.908147+00:00","id |
| A | A3 Fascicolo | `/app/properties/b63a4274-0501-48c4-85fe-6517489d17d3/fascicolo` | **PASS** | 200 | keys=['property', 'checklist', 'progress', 'documents', 'staging_jobs', 'valuation', 'last_analysis' |
| A | A3 HAL improve | `/app/al/improve` | **PASS** | 200 | {'field': 'title', 'lang': 'it', 'tone': 'standard', 'improved': 'Appartamento signorile in zona cen |
| A | A4 Property create | `/app/properties/new` | **PASS** | 201 | id=67ae4b85-7c10-409b-872b-11c0e71f7bab |
| A | A5 Clients list | `/app/clients` | **PASS** | 200 | keys=['items', 'total', 'page', 'page_size'] total=10003 n=20 |
| A | A5 Clients smart | `/app/clients` | **PASS** | 200 | keys=['items', 'total', 'page', 'page_size', 'counts', 'counts_scope', 'scanned', 'properties_matche |
| A | A6 Client get | `/app/clients/38ac1708-bfae-40a4-b4c5-bf4badde2a32` | **PASS** | 200 | keys=['created_at', 'updated_at', 'id', 'agency_id', 'name', 'surname', 'email', 'phone'] |
| A | A6 Client matches | `/app/matches/client/38ac1708-bfae-40a4-b4c5-bf4badde2a32` | **PASS** | 200 | keys=['client', 'items', 'total'] total=2000 n=5 |
| A | A7 Client create | `/app/clients/new` | **PASS** | 201 | id=5ab82bc1-b8b2-408b-a33b-70b3e69e047e |
| A | A9 Attività / follow-up | `/app/activities` | **GAP** |  | Nessuna route UI /app/activities o /app/tasks in App.js — conferma gap review QC |
| B | B1 Publishing UI | `/it/app/publishing` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| B | B2 Portal wizard UI | `/it/app/publishing/wizard` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| B | B3 Social UI | `/it/app/publishing/social` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| B | B4 MLS UI | `/it/app/mls` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| B | B5 Website UI | `/it/app/website` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| B | B6 Import XML UI | `/it/app/import` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| C | C1 Staging UI | `/it/app/staging` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| C | C2 Mutui UI | `/it/app/mutui` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| C | C3 Modulistica UI | `/it/app/modulistica` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| C | C4 Moderation UI | `/it/app/moderation` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| D | D1 HAL Knowledge UI | `/it/app/hal-knowledge` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| D | D4 Analytics UI | `/it/app/analytics` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| E | E1 Group UI | `/it/app/group` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| E | E2 Members UI | `/it/app/members` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| E | E3 API Keys UI | `/it/app/api-keys` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| E | E4 Settings UI | `/it/app/settings` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| E | E5 Billing UI | `/it/app/settings/billing` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| E | E6 Brand Lab UI | `/it/app/brand-lab` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| E | E7 Ops UI | `/it/app/ops` | **PASS** | 200 | ImmoWeb — Gestionale OMNIA |
| LOOP | Mattina agente | `/app/dashboard→clients→matches→properties→publishing→hal` | **PASS** |  | API chain exercised; dashboard still KPI-only (gap A-028a) |
| A | A8 Matches list | `/app/matches` | **FAIL** |  | blocked: agency-wide /app/matches scans ~2M pairs under stress seed and kills API; client-scoped onl |
| A | A8 Matches by client | `/app/matches?client=38ac1708-bfae-40a4-b4c5-bf4badde2a32` | **PASS** | 200 | keys=['client', 'items', 'total'] total=2000 |
| A | A8 Lead score | `/app/matches/lead` | **PASS** | 200 | query client_id+property_id required; 200 score returned |
| B | B1 Publishing connections | `/app/publishing` | **PASS** | 200 | keys=['items', 'total'] total=0 |
| B | B1 Publishing catalog | `/app/publishing` | **PASS** | 200 | keys=['items', 'total'] total=8 |
| B | B3 Social catalog | `/app/publishing/social` | **PASS** | 200 | keys=['items', 'total'] total=3 |
| B | B3 Social channels | `/app/publishing/social` | **PASS** | 200 | keys=['items', 'total'] total=0 |
| B | B4 MLS dashboard | `/app/mls` | **PASS** | 200 | keys=['mls_enabled', 'joined_at', 'province_sigla', 'mine', 'network', 'collaborations'] |
| B | B4 MLS inventory | `/app/mls` | **PASS** | 200 | keys=['scope', 'total', 'items', 'limit', 'skip'] total=2205 |
| B | B5 Website themes | `/app/website` | **PASS** | 200 | keys=['themes', 'default_theme_id'] |
| B | B5 Website theme | `/app/website` | **PASS** | 200 | keys=['agency_id', 'agency_slug', 'saved_theme_config', 'resolved', 'extracted_profile', 'public_url |
| C | C1 Staging styles | `/app/staging` | **PASS** | 200 | keys=['styles', 'room_types', 'modes', 'credit_cost_per_variant'] |
| C | C1 Staging history | `/app/staging` | **PASS** | 200 | keys=['items', 'count'] |
| C | C1 Staging credits | `/app/staging` | **PASS** | 200 | keys=['agency_id', 'balance', 'required', 'credit_cost_per_variant', 'num_variants', 'ok'] |
| C | C1 Staging generate | `/app/staging` | **SKIP** |  | soft: no fal spend |
| C | C2 Mutui compare | `/app/mutui` | **PASS** | 200 | {"eligible":true,"loan_amount":200000.0,"ltv":80.0,"max_ltv":80.0,"duration_years":25,"consap_applie |
| C | C3 Modulistica templates | `/app/modulistica` | **PASS** | 200 | keys=['items', 'total'] total=7 |
| C | C3 Modulistica docs | `/app/modulistica` | **PASS** | 200 | keys=['items', 'total', 'page', 'page_size'] total=14 |
| C | C3 Esign status | `/app/modulistica` | **PASS** | 200 | keys=['provider', 'ready', 'note'] |
| C | C4 Moderation queue | `/app/moderation` | **PASS** | 200 | keys=['items', 'total'] total=46 |
| D | D1 HAL knowledge status | `/app/hal-knowledge` | **PASS** | 200 | keys=['chunks_indexed', 'manual_hal_indexed', 'index', 'model', 'corpus_files'] |
| D | D1 HAL ask publish | `/app/hal-knowledge` | **PASS** | 200 | Ciao collega! Per pubblicare un immobile sui portali, segui questi passi… |
| D | D1 HAL ask MLS | `/app/hal-knowledge` | **PASS** | 200 | Ciao collega! Ecco come funziona l'MLS in OMNIA:  1. Nel menu a sinistra clicca **MLS** (oppure usa  |
| D | D2 HAL Assist sessions | `HAL Assist` | **PASS** | 200 | keys=['items'] |
| D | D2 HAL Assist chat | `HAL Assist` | **PASS** | 200 | {'session_id': '189c3b86-3a18-40a3-9d38-31fb0466ac0f', 'reply': 'Prima di cliccare su "Pubblica", ci |
| D | D3 HAL Legal sessions | `/legal` | **PASS** | 200 |  |
| D | D3 HAL Legal health | `/legal` | **PASS** | 200 | keys=['service', 'model', 'temperature', 'soft_rate_limit_per_hour', 'confidence_threshold', 'sub_ag |
| D | D3 HAL Legal chat | `/legal` | **PASS** | 200 | reply OK (no normative sources — soft disclaimer) |
| D | D4 Analytics overview | `/app/analytics` | **PASS** | 200 | keys=['days_lookback', 'properties', 'leads', 'publishing_recent', 'top_views'] |
| E | E1 Group me | `/app/group` | **PASS** | 404 | keys=['detail'] |
| E | E2 Members | `/app/members` | **PASS** | 200 |  |
| E | E2 Invites | `/app/members` | **PASS** | 200 |  |
| E | E3 API Keys list | `/app/api-keys` | **PASS** | 200 | keys=['items', 'total'] total=1 |
| E | E3 API Key create | `/app/api-keys` | **PASS** | 201 | id=4acf8b91-b5e3-4a66-b4f8-f7d35a89c34e |
| E | E3 API Key revoke | `/app/api-keys/4acf8b91-b5e3-4a66-b4f8-f7d35a89c34e/revoke` | **PASS** | 200 | {"status":"ok","id":"4acf8b91-b5e3-4a66-b4f8-f7d35a89c34e","revoked_at":"2026-09 |
| E | E4 Agency settings | `/app/settings` | **PASS** | 200 | keys=['id', 'name', 'slug', 'city', 'province_sigla', 'mls_enabled', 'mls_joined_at', 'mls_province' |
| E | E5 Billing plans | `/app/settings/billing` | **PASS** | 200 | keys=['plans', 'credit_packages', 'credit_costs', 'trial_days', 'onboarding', 'demo_contact_email',  |
| E | E5 Stripe checkout | `/app/settings/billing` | **SKIP** |  | soft: no Stripe checkout |
| E | E7 Ops overview | `/app/ops` | **PASS** | 200 | keys=['period_days', 'generated_at', 'providers', 'policy', 'alerts', 'totals', 'services', 'tavily' |

## Gaps prodotto (A-028) — storico 18-Set (superato)

- ~~A9: missing Attività~~ → ✅ A-028h (24-Set)
- ~~Dashboard KPI-only~~ → ✅ A-028a
- ~~Match score explain~~ → ✅ A-028b
- ~~Sidebar flat~~ → ✅ A-028c

## Blocchi tecnici — storico 18-Set

- **FAIL** A/A8 Matches list (18-Set): agency-wide ~2M pairs. **Mitigato 24-Set**: scan fast + cap 400×400 + breakdown solo sulla page (`scan_capped`). Non rieseguire stress full senza «vai».

### SKIP (soft / defer)
- C/C1 Staging generate: soft: no fal spend
- E/E5 Stripe checkout: soft: no Stripe checkout

## Burn check

- Resend: non chiamato
- Stripe checkout: SKIP policy
- fal generate: SKIP policy
- Portal sync-now: non chiamato
- Nominatim: solo eventuale geocode implicito su property create (1×) — no hammer

## Top 5 next (solo con «vai») — aggiornato 25-Set

Vedi analisi §8: **R4** Analytics nav · **R5** UI match capped · **R6** QC refresh · **R1** smart `no_match` · **R3** agenda Attività.  
A-028 chiuso. Demo A-025 in pausa.

JSON: `/workspace/memory/reports/gestionale_tools_qc_latest.json`
