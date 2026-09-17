# Inventario migrazione repo — Emergent → Cursor

**Data**: 2026-09-17 10:48 UTC
**Eseguito da**: agente Cursor (controlli automatici, nessun delete)

## Fonti confrontate

| Fonte | URL / path | HEAD | Ultimo push |
|-------|------------|------|-------------|
| Emergent (GitHub pubblico collegato) | https://github.com/mcnicastro-netizen/OMNIA | `790d9fb` | 2026-08-16 |
| Workspace Cursor attuale | `/workspace` (remote tmp Cursor) | `dc27086` | ongoing |

> **Nota**: fonte Emergent = repo GitHub pubblico `mcnicastro-netizen/OMNIA` (tutto il codice del progetto lì; Founder conferma: nessuna variante privata separata).
> Confrontato interamente dall’agente — **nessuno zip richiesto**.

## Verdetto (codice sorgente)

- File solo su Emergent GitHub e **assenti** in Cursor: **0**
- File identici byte-per-byte: **305**
- File presenti in entrambi ma modificati in Cursor: **117**
- File **nuovi solo in Cursor** (lavoro post-import): **124**

### Conclusione

**Cursor è un superinsieme completo del mirror GitHub Emergent `mcnicastro-netizen/OMNIA`.**
Nessun path sorgente Emergent manca qui. Il nuovo repo ufficiale deve nascere da **questo** workspace Cursor (non da un re-clone solo Emergent), altrimenti si perdono Scout, gate, security go-live, MLS Cursor-era, ecc.

## Conteggio (source, esclusi `.venv` / `node_modules` / `.mongo-data` / `.media` / secret env)

| Metrica | N |
|---------|--|:
| File Emergent | 422 |
| File Cursor | 549 |
| Identici | 305 |
| Modificati in Cursor | 117 |
| Solo Cursor | 124 |
| Solo Emergent | 0 |

## Cosa c’è in più solo su Cursor (sintesi)

### Docs / report / manuale (32)

- `memory/DEPLOY_VERCEL.md`
- `memory/GOOGLE_AUTH.md`
- `memory/MANUAL_SYNC.md`
- `memory/NEXT_SESSION.md`
- `memory/PLATFORM_STRESS_REPORT.md`
- `memory/PREPROD_GATE_REPORT.md`
- `memory/PRODUCT_NORTHSTAR_B2C.md`
- `memory/PROGRAMMA_CONCLUSIONE.md`
- `memory/ROADMAP_OPERATIVA_CURSOR.md`
- `memory/SECURITY_CHECKLIST.md`
- `memory/STRESS_REPORT.md`
- `memory/manuale/22-hal-legal.md`
- `memory/manuale/23-video-ab-testing.md`
- `memory/manuale/24-gruppi-sedi.md`
- `memory/manuale/25-privacy-immobili.md`
- `memory/manuale/26-widget-embed.md`
- `memory/manuale/hal/00-api-codice.yaml`
- `memory/manuale/hal/22-hal-legal.yaml`
- `memory/manuale/hal/23-video-ab-testing.yaml`
- `memory/manuale/hal/24-gruppi-sedi.yaml`
- … +12 altri

### Frontend nuovi (28)

- `frontend/.env.example`
- `frontend/preview-server.js`
- `frontend/public/cloud/city-milano.jpg`
- `frontend/public/cloud/city-napoli.jpg`
- `frontend/public/cloud/city-roma.jpg`
- `frontend/public/cloud/city-torino.jpg`
- `frontend/public/cloud/hero.jpg`
- `frontend/public/cloud/intent-mortgage.jpg`
- `frontend/public/cloud/intent-sell.jpg`
- `frontend/public/cloud/intent-value.jpg`
- `frontend/public/cloud/living.jpg`
- `frontend/public/cloud/scout.jpg`
- `frontend/public/robots.txt`
- `frontend/public/sw-push.js`
- `frontend/src/apps/immocloud/components/CloudPageHero.jsx`
- `frontend/src/apps/immocloud/components/VisuraPage.jsx`
- `frontend/src/apps/immoweb/pages/AnalyticsPage.jsx`
- `frontend/src/apps/immoweb/pages/FounderLegalOpsPage.jsx`
- `frontend/src/apps/immoweb/pages/FounderOpsPage.jsx`
- `frontend/src/apps/immoweb/pages/ModulisticaPage.jsx`
- … +8 altri

### Security / privacy / tenant (13)

- `backend/shared/auth/mfa.py`
- `backend/shared/db/tenant_guard.py`
- `backend/shared/db/tenant_middleware.py`
- `backend/shared/monitoring/__init__.py`
- `backend/shared/monitoring/alerts.py`
- `backend/shared/privacy/__init__.py`
- `backend/shared/privacy/consent_log.py`
- `backend/shared/privacy/erasure.py`
- `backend/shared/security/__init__.py`
- `backend/shared/security/circuit.py`
- `backend/shared/security/csrf.py`
- `backend/shared/security/middleware.py`
- `backend/shared/security/rate_limit.py`

### Backend shared altro (8)

- `backend/shared/email/templates/error_alert.it.html`
- `backend/shared/llm/__init__.py`
- `backend/shared/notifications/__init__.py`
- `backend/shared/notifications/center.py`
- `backend/shared/notifications/prefs.py`
- `backend/shared/notifications/web_push.py`
- `backend/shared/openapi_catasto.py`
- `backend/shared/ops_alerts.py`

### Test (8)

- `backend/tests/test_a017_notifications.py`
- `backend/tests/test_a021_notification_prefs.py`
- `backend/tests/test_b2c_boosts.py`
- `backend/tests/test_b2c_media_upload.py`
- `backend/tests/test_private_publisher_contact.py`
- `backend/tests/test_scout_gaps_and_vapid.py`
- `backend/tests/test_scout_hal_and_pulse.py`
- `backend/tests/test_viewer_is_lister.py`

### Scout / ImmobilCloud nuovi (7)

- `backend/apps/immocloud/alert_fanout.py`
- `backend/apps/immocloud/buyer_brief.py`
- `backend/apps/immocloud/favorites.py`
- `backend/apps/immocloud/market_pulse.py`
- `backend/apps/immocloud/price_watch.py`
- `backend/apps/immocloud/push_subscriptions.py`
- `backend/apps/immocloud/visura_b2c.py`

### Altro (6)

- `backend/.env.example`
- `backend/.vapid_local.json`
- `backend/ISTRUZIONI_CHIAVE_GEMINI.txt`
- `backend/emergentintegrations/__init__.py`
- `backend/emergentintegrations/llm/__init__.py`
- `backend/emergentintegrations/llm/chat.py`

### MLS (6)

- `backend/apps/immoweb/mls.py`
- `backend/scripts/load_ladder_mls.py`
- `backend/tests/test_mls_network.py`
- `frontend/src/apps/immoweb/pages/MlsPage.jsx`
- `memory/manuale/27-mls-network.md`
- `memory/manuale/hal/27-mls-network.yaml`

### Modulistica / firma (6)

- `backend/apps/immoweb/modulistica.py`
- `backend/shared/modulistica/__init__.py`
- `backend/shared/modulistica/catalog.py`
- `backend/shared/modulistica/esign.py`
- `backend/shared/modulistica/pdf.py`
- `backend/tests/test_modulistica.py`

### Backend apps altro (5)

- `backend/apps/billing/b2c_boosts.py`
- `backend/apps/core/google_auth.py`
- `backend/apps/core/mfa_routes.py`
- `backend/apps/core/notifications_inbox.py`
- `backend/apps/immoweb/founder_ops.py`

### Script QA / stack (5)

- `backend/scripts/e2e_b2c_privati_hal.py`
- `backend/scripts/preprod_confidence_gate.py`
- `backend/scripts/stress_platform_full.py`
- `backend/scripts/stress_scale_ladder.py`
- `scripts/omnia-stack.sh`

## Modificati rispetto a Emergent (top path)

- `frontend/src`: 37 file
- `backend/apps`: 35 file
- `memory/manuale`: 15 file
- `backend/shared`: 8 file
- `backend/tests`: 3 file
- `.gitignore`: 1 file
- `README.md`: 1 file
- `backend/requirements.txt`: 1 file
- `backend/server.py`: 1 file
- `frontend/public`: 1 file
- `memory/ASPETTI_DA_APPROFONDIRE.md`: 1 file
- `memory/CHANGELOG.md`: 1 file
- `memory/DECISIONS.md`: 1 file
- `memory/GAP.md`: 1 file
- `memory/HANDOFF_NEXT_AGENT.md`: 1 file
- `memory/NEXT_SESSION_TIPS.md`: 1 file
- `memory/OPEN_SOURCE_FINDINGS.md`: 1 file
- `memory/PIANO_ESECUZIONE.md`: 1 file
- `memory/PRICING_B2C.md`: 1 file
- `memory/PRICING_OMNIA.md`: 1 file
- `memory/PROGRAMMA_OMNIA.md`: 1 file
- `memory/ROADMAP.md`: 1 file
- `memory/SPRINT_STATUS.md`: 1 file
- `memory/STRIPE_ONBOARDING.md`: 1 file

## Cosa NON va nel nuovo repo (runtime locale)

- `backend/.env`, `frontend/.env`, `memory/test_credentials.env` (secret)
- `backend/.media/**` (PDF/foto generate in locale)
- `.mongo-data/`, `.venv/`, `node_modules/`

## Checklist prima di dichiarare il nuovo repo “completo”

- [x] Mirror Emergent GitHub accessibile e clonato
- [x] Diff path: 0 file solo-Emergent
- [x] Cursor contiene lavoro post-16-ago (Scout, gate, security, …)
- [x] Tu confermi: versione Emergent = tutto pubblico su quel GitHub (niente ramo/file privati extra)
- [ ] Creazione nuovo repo Cursor (nome da te) **senza** cancellare Emergent
- [ ] Push mirror di questo workspace → nuovo repo
- [ ] Clone fresco + `bash scripts/omnia-stack.sh ensure` OK
- [ ] Solo dopo: lavori gestionale sul nuovo repo
- [ ] Emergent resta backup indefinito finché non lo chiudi tu

## Raccomandazione operativa

1. **Non cancellare** Emergent / GitHub `OMNIA`.
2. Nuovo repo Cursor = copia di **questo** workspace (codice + storia git Cursor).
3. Se hai dubbi su lavoro solo in Emergent UI: esporta ZIP o invita accesso; io rifaccio il confronto.

JSON grezzo: `memory/reports/REPO_MIGRATION_INVENTORY.json`

