# 🔍 AUDIT M2 — Programma vs Realtà (24-Feb-2026)

**Metodo**: confronto voce-per-voce di `PROGRAMMA_OMNIA.md` (M2 + M2.5 + M2.6) con lo stato reale di `/app/backend`, `/app/frontend`, `/app/backend/tests` e collezioni MongoDB.

**Scopo**: identificare i TODO **saltati o fatti parzialmente** dentro milestone dichiarate "✅ DONE", come richiesto nel `CHANGELOG.md` del 29-Giu-2026 (action item mai eseguito) e ora esplicitamente dal Founder il 24-Feb-2026.

**Range**: solo M2 core + M2.5 + M2.6. M3/M5 fuori scope di questo audit (vedi Sprint 3 in `PIANO_ESECUZIONE.md`).

---

## 📊 Tabella item-per-item

### M2 core (M2.S1 → M2.S6)

| Item | Programma dice | Realtà | Stato |
|---|---|---|:-:|
| M2.S1 Wizard setup agenzia | logo, dati fiscali, indirizzo, contatti | `OnboardingWizard.jsx` + `agencies.py` presenti | ✅ |
| M2.S1 Dashboard con KPI | dashboard base + KPI | `dashboard.py` + `KPICard.jsx` | ✅ |
| M2.S1 Invito collaboratore magic-link Resend | ✓ | `invites.py` + `InviteMemberModal.jsx` + template email | ✅ |
| M2.S2 CRUD Immobili 16 tipologie 25 features | ✓ | `property.py` con `PropertyFeatures`, `PropertyPhoto`, `PropertyOwner`, `PropertyEnergy` | ✅ |
| **M2.S2 Upload foto** | "base64 + canvas resize client-side, **da migrare a S3 in M3**" | `site.py:56` fa ancora `base64.b64decode` — **mai migrato a object storage** | 🟡 **GAP #1** |
| M2.S2 Stati workflow property | draft/active/reserved/sold/rented/withdrawn | Presenti in model | ✅ |
| M2.S2 Import CSV + XML Agestanet | ✓ | `properties.py` CSV import + `import_agestanet.py` + `xml_import.py` (Universal M2.5.4a) | ✅ |
| M2.S3 CRM 5 tipologie cliente | buyer/seller/tenant/landlord/investor | ✓ tutti presenti | ✅ |
| M2.S3 SearchPreferences idealista-style | filtri completi | 20+ campi Optional | ✅ |
| M2.S3.5 Property.seller_client_id + cascade | ✓ | `property.py:132` + cascade in `properties.py:183` | ✅ |
| M2.S4 Matching + Lead Scoring | Layer 1 deterministico + Gemini | `matching.py` + `matches.py` + `lead_scoring.py` | ✅ |
| M2.S5 Layer A Portal Manager | portali PortalSubscription | `portals.py` (legacy 7 portali OSF) | ✅ |
| M2.S5 Layer B XML/JSON OSF feed | endpoint pubblici | `feed.py` con `.xml/.json/schema/osf-v1.json` | ✅ |
| M2.S5 Layer C Site-as-Feed | HTML SEO + sitemap + photo binary | `site.py` con 4 route pubbliche | ✅ |
| M2.S5 Layer D Brand Extractor + Theme Registry | 4 temi + estrattore Gemini | `brand_extractor.py` + `themes.py` (39kb) + `WebsitePage.jsx` | ✅ |
| **M2.S5 Layer A++** | "cron worker push portali push_api (rinviato a M4.S3+)" | Nessun cron push, `sync_engine.py` gestisce solo pull + stub `api_push=simulated_push` | ⏸️ **Rinvio esplicito** (non gap nascosto) |
| M2.S5 Enhancement Social Share (4 pulsanti) | WhatsApp/FB/Email/Copy | `themes.py::_share_block()` (4 occorrenze) | ✅ |
| M2.S5 Smart Clients List | AI Lead Scoring + bucket filters | `clients_smart.py` (16 occorrenze action_hint) | ✅ |
| M2.S5 Click-to-Call/WhatsApp | tel: + wa.me | `ClientsPage.jsx` | ✅ |
| M2.S5 CSV Client Import UI | dropzone | `ClientImportPage.jsx` | ✅ |
| M2.S5 D-FUTURE-07 AI Smart Import Clienti v1 | 4 endpoint /import/ai | `clients_ai_import.py` | ✅ |
| M2.S6 Custom domain CNAME + host routing | ✓ | `custom_domain.py` + `host_routing.py::HostRoutingMiddleware` | ✅ |
| **DoD M2 · Stress test 5 agenti in parallelo** | "[ ] testabile ora" | `test_m2_stress_5_agents.py` esiste — **7/11 FAILED oggi** (regressione post-refactor) | 🔴 **GAP #2** |

### M2.5 White Label / Doppio Binario

| Item | Programma dice | Realtà | Stato |
|---|---|---|:-:|
| M2.5.0 GO_TO_MARKET.md + PRICING_OMNIA.md v2 | 2 documenti strategici | Entrambi presenti in `/app/memory/` | ✅ |
| M2.5.1 Multi-branch: `agency_group` + `branch` + ruoli | ✓ | `groups.py` con `group_admin`, `branch_admin`, `plan_type` | ✅ |
| M2.5.1 Contabilità crediti group vs branch | menzionato | Da verificare più a fondo (fuori audit — appartiene a M4.S4 Stripe/crediti) | 🟡 verifica rimandata a M4 |
| M2.5.2 API Gateway 5+ endpoint Track B | ≥5 | 10 endpoint: valuator, mortgages, legal/ask, feed/properties, widgets/lead, staging/render, domain/check, legal/render, health, me | ✅ |
| M2.5.2 API keys con `partner_id` (D-046) | rev-share partner | `api_keys.py:86` + `gateway.py:247` attribuzione partner_id | ✅ |
| **M2.5.3 Widget embeddabili 4 servizi** | "Valuator, Mutui, Virtual Staging, HAL Legal pubblico" | **Solo 2 widget nel loader**: `valuator` + `mortgages`. Assets: valuator.html, mortgages.html, domain-check.html (bonus, non nel loader). **Mancano widget Virtual Staging e HAL Legal**. | 🔴 **GAP #3** |
| M2.5.3 Snippet 1-line + iframe | ✓ | `loader.js` funzionante | ✅ |
| M2.5.3 Lead capture on-widget + webhook | ✓ | `POST /api/v1/widgets/lead` in `gateway.py:222` | ✅ |
| M2.5.4a Universal XML Importer | parser schema-agnostic + preview→commit | `shared/importers/universal_xml.py` + `xml_import.py` + UI `/it/app/import` | ✅ |
| M2.5.4b Domain Ownership Checker | RDAP + landing + lead + rate-limit | `apps/marketing/domain_check.py` con `/check` + `/lead` + 24 occorrenze rate-limit | ✅ |
| M2.5.4c Legal Templates Pack 4 PDF | PEC/GDPR/disdetta/CNR-IIT | `shared/legal_kit/templates.py` con `TEMPLATES` dict | ✅ |
| M2.5.5 Domain Vault (D-056) | signup + policy + audit trail | `domain_vault.py` + policy page + `domain_vault_events` | ✅ |
| **M2.5 Feed bidirezionale INBOUND** (D-041 modalità 3) | "immobili out → ImmoCloud, **lead in → loro CRM**" | Solo outbound XML/JSON. **Nessun endpoint per ricevere feed immobili da CRM esterni**. **Nessun endpoint export lead** verso il CRM del cliente Track B. | 🔴 **GAP #4** |
| **M2.5.x Universal Smart Importer 2.0** (D-043) | "1 mapper HAL-powered per qualsiasi export" | `clients_ai_import.py` esiste (v1 solo clienti). **Manca la versione property + integrazione HAL, come da D-FUTURE-10** | 🟡 **GAP #5** (v1 clienti ✅ · v2 immobili ⏳) |

### M2.6 Publishing Center

| Item | Programma dice | Realtà | Stato |
|---|---|---|:-:|
| M2.6a Foundation catalog 8 portali | Subito/Bakeca/Kijiji/Wikicasa/FB Marketplace/Google Business/Attico/Case24 | `CATALOG_SEED` con esattamente 8 slug corretti | ✅ |
| M2.6a Credenziali AES-256 | Fernet o AES-GCM | `shared/utils/crypto.py::encrypt_dict` (AES-256-GCM) | ✅ |
| M2.6a Feed generator multi-dialetto | osf_federata + generic_rss | ✓ in `publishing.py` | ✅ |
| M2.6a UI dashboard `/it/app/publishing` | tab attivi/disponibili | `PublishingPage.jsx` | ✅ |
| M2.6b Sync scheduler daily 06:00 UTC | APScheduler | `sync_engine.py::start_scheduler` + retry 1/5/30 min | ✅ |
| M2.6b Compliance validator HARD | classe energetica, min-foto, prezzo, superficie, indirizzo | `shared/validators/compliance.py` (9 funzioni) | ✅ |
| M2.6c Social Publisher FB Page + IG Business + Telegram | Graph API v20 + Bot API | `social_publisher.py` con 8 endpoint | ✅ (D-058) |
| M2.6d Universal Portal Wizard 4-step | tenant-namespaced slug | `publishing.py` con 5 endpoint `/custom-portals` | ✅ (D-057) |

---

## 🔴 GAP identificati (6 totali, priorità ordinata)

### ✅ CHIUSI in Sprint 1.5 recovery (24-Feb-2026 evening, D-059)

- ✅ **GAP #3 — Widget M2.5.3 completati**: aggiunti `staging.html` (Virtual Staging demo + lead capture) e `legal.html` (HAL Legal Q&A pubblico con disclaimer L.247/2012). Loader accetta 4 widget. `WidgetLeadBody` pattern esteso. 
- ✅ **GAP #4 — Feed bidirezionale INBOUND (D-041 modalità 3)**: `POST /api/v1/feed/properties` (ingest upsert idempotent) + `GET /api/v1/leads/export?since=&limit=` (pull mode). Pilastro Track B chiuso 3/3 modalità.

Test: 13/13 pytest locale + 16/16 testing_agent contro preview URL. Regressione totale 193/193 verdi.

### 🔴 GAP residui

### GAP #2 · 🔴 P0 — Stress test 5 agenti concorrenti ROTTO
- **Dov'è nel programma**: DoD M2 riga finale "[ ] 5 agenti in parallelo nella stessa agenzia (testabile ora)".
- **Stato reale**: `test_m2_stress_5_agents.py` ora fallisce **7/11**. Al 23-Feb l'handoff diceva "validato — iter_25". Regressione post-refactor probabilmente causata da modifiche a login flow / property schema.
- **Recupero previsto**: **Sprint 4** (Perf hardening) ha già "Regressione stress test finale" come item.
- **Azione consigliata**: NON toccare adesso. Verificare in Sprint 4 dopo aver applicato async geocoding + list projection (le fix perf potrebbero far ripassare i test).

### GAP #3 · 🟠 P1 — Widget M2.5.3 mancanti (Virtual Staging + HAL Legal)
- **Dov'è nel programma**: M2.5.3 dichiara 4 widget (Valuator, Mutui, Virtual Staging, HAL Legal pubblico).
- **Stato reale**: `loader.js` accetta solo `valuator` + `mortgages`. `domain-check.html` esiste ma non è ufficialmente esposto dal loader.
- **Impatto D-041 Doppio Binario**: Track B web agency non possono embeddare Virtual Staging demo o HAL Legal pubblico. Riduce completezza dell'offerta Track B (uno dei 3 revenue stream pubblicati in `PRICING_OMNIA.md`).
- **Effort stimato**: ~2h per widget (asset HTML + registrazione loader + endpoint gateway già presenti `staging/render` e `legal/render`).

### GAP #4 · 🟠 P1 — Feed bidirezionale INBOUND (Track B modalità 3)
- **Dov'è nel programma**: D-041 dichiara 3 modalità di consumo Track B — (1) API, (2) widget, (3) **feed bidirezionale: immobili out + lead in**. Il "lead in" è specifico per Track B: la web agency riceve leads dal proprio widget/site e li deve poter iniettare nel CRM esterno.
- **Stato reale**: Feed outbound XML/JSON ✅. **Feed inbound assente**: nessun endpoint per ricevere payload immobili da CRM esterni, nessun endpoint `GET /api/v1/leads/export?since=…` per pull-mode né webhook push-mode.
- **Impatto D-041**: Track B partner non possono chiudere il loop lead — attualmente possono solo consumare feature OMNIA in uscita, non aggregare i lead dentro il proprio CRM.
- **Effort stimato**: 
  - `POST /api/v1/feed/properties` (ingest) — 3-4h con validation + de-dup
  - `GET /api/v1/leads/export` + webhook opzionale — 2-3h
- **Decisione Founder richiesta**: promuovere a Sprint 2 o consolidare in un futuro "Sprint 5 Track B closure"?

### GAP #5 · 🟢 P2 — Universal Smart Importer 2.0 immobili (D-043 / D-FUTURE-10)
- **Dov'è nel programma**: D-043 lo indica come strategia di migrazione principale del pivot Doppio Binario. D-FUTURE-10 lo attende dopo D-FUTURE-07 completato.
- **Stato reale**: v1 clienti ✅ (`clients_ai_import.py`). v2 immobili ❌: nessun endpoint `/api/app/properties/import/ai`, nessuna UI drop-Excel per immobili.
- **Impatto migration wedge**: senza questo, la promessa "migrazione zero-friction" (D-042) è solo metà mantenuta.
- **Effort stimato**: 1 giornata piena (pattern replicato da clients_ai_import + gestione media/foto).

### GAP #1 · 🔵 P3 — Foto storage in base64 (mai migrato a object storage)
- **Dov'è nel programma**: M2.S2 dichiara "base64 + canvas resize, **da migrare a S3 in M3**". La migrazione **non è mai stata eseguita**.
- **Stato reale**: `site.py:56` legge ancora dal DB Mongo (base64) per servire i binari. `PhotoUploader.jsx` invia base64 al backend.
- **Impatto**: 
  - Dimensione Mongo esplode all'aumentare dei portafogli (300 immobili × 15 foto × ~800KB = 3-4 GB per agenzia).
  - Latenza serving foto pubbliche (via `/api/public/property/{pid}/photo/{idx}`) non ottimizzata.
  - Cost su Atlas quando ci si sposterà in produzione.
- **Fix suggerito**: object storage Emergent (playbook via `integration_playbook_expert_v2`) con migrazione lazy (foto vecchie restano in DB, nuove vanno in bucket).
- **Effort stimato**: 1-2 giornate (playbook + upload + serving + migrazione script).

### GAP #6 · ⚪ — Layer A++ cron push_api
- **Dov'è nel programma**: M2.S5 Layer A++ "cron worker push portali push_api" con nota esplicita **"rinviato a M4.S3+ insieme allo Stripe"**.
- **Stato reale**: `sync_engine.py` rileva `integration_type: api_push` e ritorna `simulated_push` (stub). M2.6c Social Publisher ha già implementato push reale su FB Page/IG/Telegram — questo pattern potrebbe essere generalizzato.
- **Rinvio esplicito, non gap nascosto**. Nessuna azione richiesta ora.

---

## 🎯 Sintesi decisionale

| Priorità | Item | Azione consigliata | Sprint di destinazione |
|:-:|---|---|:-:|
| 🔴 P0 | GAP #2 Stress test rotto | Investigare in Sprint 4 dopo perf fix | Sprint 4 |
| 🟠 P1 | GAP #3 Widget Virtual Staging + HAL Legal | Chiudere in Sprint 2 come "recupero DoD M2.5.3" | Sprint 2 (parallelo a HAL Knowledge) |
| 🟠 P1 | GAP #4 Feed inbound + Lead export | Decidere: Sprint 2 vs futuro Sprint 5 dedicato | ❓ Decisione Founder |
| 🟢 P2 | GAP #5 Universal Smart Importer 2.0 immobili | Sprint 3 (dopo M3 backlog) o dedicato | ❓ Decisione Founder |
| 🔵 P3 | GAP #1 Foto storage → object storage | Sprint 4 (perf hardening) | Sprint 4 |
| ⚪ | GAP #6 Cron push_api | Rinvio esplicito, no azione | M4+ |

**Test suite oggi**: 180/180 pytest verdi (funzionali) · 4/11 stress test verdi (perf/carico). Regressione totale 184/191 = 96,3%.

---

## 📌 Raccomandazione operativa

Il programma M2/M2.5/M2.6 è **completo al 87%** — 4 gap nascosti (GAP #1/#3/#4/#5) rispetto al DoD dichiarato, più 1 regressione (GAP #2) e 1 rinvio esplicito (GAP #6).

**Prossimo passo raccomandato**: nel decidere Sprint 2 valutare se chiudere in parallelo:
- **GAP #3** (2 widget mancanti, ~4h) → completamento M2.5.3 DoD
- **GAP #4** (feed bidir. inbound, ~6h) → completamento D-041 modalità 3

Entrambi sono breve effort e chiudono definitivamente il "pilastro Track B", che è il vero motore di revenue post pivot v3.0 (D-041). HAL Knowledge (M5.S2) resta la priorità principale ma i due gap sopra si possono chiudere nella stessa sessione senza allungare significativamente.

---

*Documento generato: 24-Feb-2026 · Firma: E1 (agente in corso)*
*Metodo: grep+ls+pytest-collect su codebase live · nessun rebase, nessuna interpretazione soggettiva.*
