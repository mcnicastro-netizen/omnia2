# OMNIA — Sprint Status (handoff agenti)
**Ultimo aggiornamento**: Feb 2026 (post-Cap. 11 H-bis · fix onestà 8 banche/9 Consap)  
**Branch di riferimento**: `main`  
**Repo**: https://github.com/mcnicastro-netizen/OMNIA  
**Preview Emergent**: https://omnia-crm-docs.preview.emergentagent.com  
**Founder**: Marco Nicastro · credenziali test in `/app/memory/test_credentials.md` (non in GitHub)
---
## Regole operative (non negoziabili)
1. **Onestà documentale (D-051)**: documentare SOLO ciò che esiste nel codice/UI oggi. Zero invenzioni.
2. **Push GitHub**: l'agente modifica file locali; il **Founder** esegue **Save to GitHub**. Non assumere push automatico.
3. **STOP dopo ogni task**: report + commit message suggerito → attendere **"vai"** esplicito del Founder.
4. **Academy (M6)**: congelata.
5. **MLS network**: 0% — solo placeholder Cap. 27.
6. **Immobili Segreti**: rimosso dal prodotto.
7. **Entità legale**: ditta individuale esistente (no nuova SRL).
8. **Naming**: ImmoWeb (B2B CRM) · ImmobilCloud (B2C) · HAL · segreteria = concetto operativo, non ruolo backend.
---
## Completato in questo sprint (Feb 2026 · post-fork)
| Task | Stato | Note chiave |
|------|:-----:|-------------|
| **A-bis** Pricing B2C | ✅ | `PRICING_B2C.md` v1.0 + `b2c_products.py` stub · checkout Stripe = sprint dopo |
| **A** Pricing B2B sync | ✅ | `PRICING_OMNIA.md` v3.0 + `plans.py` · valuator 6/12 cr |
| **B** HAL cold start | ✅ | `hal-index.json` + `IMPORT_HAL.md` + banner UI |
| **B-bis** HAL YAML ingest | ✅ | Opzione A in `hal_knowledge.py` · 56 voci Cap. 1-5 · live reindex OK |
| **B-ter** HAL corpus cleanup | ✅ | `CHANGELOG.md` **escluso** da `CORPUS_FILES` · feedback loop risolto |
| **C** Manuale Cap. 6 Portali | ✅ | `06-portali-publishing.md` + 12 voci YAML · index **68 voci** |
| **D** Manuale Cap. 7 Fascicolo + micro-fix | ✅ | `07-fascicolo-immobile.md` + 12 voci YAML · index **80 voci** · 4 micro-fix chiusi (Cap. 1 §1.4, CHANGELOG typo, IMPORT_HAL a 80, Cap. 3 cross-ref §3.6/§3.7 + APE partner "in valutazione") |
| **E** Manuale Cap. 8 Sito web | ✅ | `08-sito-web.md` + 12 voci YAML · index **92 voci** · copertura site.py + themes.py + brand_extractor.py + custom_domain.py |
| **F** Manuale Cap. 9 Virtual Staging | ✅ | `09-virtual-staging.md` + 12 voci YAML · index **104 voci** · copertura virtual_staging.py (SAM2+Flux+ESRGAN, 5 stili, 6 stanze, reverse mode, watermark AGCM) |
| **G** Manuale Cap. 10 HAL Agent CRM | ✅ | `10-hal-agent-crm.md` + 13 voci YAML · index **117 voci** · reindex + smoke 3/3 PASS · convenzione naming Fase 0 HAL/al_* |
| **G-bis** Micro-fix retrieval Cap. 9 `staging.crediti-costo` | ✅ | tags 6→14 · +correlato `staging.cos-e` · domanda_naturale doppia · a_cosa_serve arricchito · index v0.6.1-cap10-gbis · retrieval fix validated by testing_agent (top-1 sim 0.379 vs 0.334 fascicolo #2) |
| **H** Manuale Cap. 11 Mutui comparatore | ✅ | `11-mutui-comparatore.md` + 12 voci YAML · index **129 voci** · copertura mutui.py + mortgage_data.py (14 offerte 9 banche, TAEG IRR, Consap under-36, disclaimer 128-sexies TUB) |
| **H-bis** Allineamento D-051 Cap. 11 al codice | ✅ | Fix onestà: 9→**8 banche distinte** (banks_count=8), 11→**9 offerte Consap**, ING interamente fuori Consap. Voce YAML rinominata `mutui.offerte-14-banche-9` → `-banche-8`. Index v0.7.1-cap11-hbis. |
| **I** Manuale Cap. 12 HAL Knowledge | ✅ | `12-hal-knowledge.md` + 13 voci YAML · index **142 voci** · v0.8-cap12 · meta-doc RAG (motore TF-IDF+Gemini, corpus 7 file, soglie confidence 0.08/0.20, distinzione D-040 tre HAL, limiti v1). Copertura `hal_knowledge.py` 617 righe + `HalKnowledgePage.jsx` 307 righe. |
| **J** Manuale Cap. 13 Team & Ruoli (Collaboratori) | ✅ | `13-team-ruoli.md` + 13 voci YAML · index **155 voci** · v0.9-cap13 · magic-link invite 7gg, ruoli `agency_admin`/`agent` (segreteria = concetto operativo), 4 stati invito (pending/accepted/revoked/expired), upgrade role solo se client, token nel fragment (L5). Copertura `invites.py` + `agencies.py` + `MembersPage.jsx` + `InviteMemberModal.jsx` + `AcceptInvitePage.jsx`. |
| **K** Manuale Cap. 14 Import XML (Migrazione) | ✅ | `14-import-xml.md` + 13 voci YAML · index **168 voci** · v0.10-cap14 · flusso Preview→Commit, session TTL 10min in-memory, dedupe per reference_code, dry-run, tabelle mapping (18 tipi + 19 energetiche + 6 contratti + 25 features), zero riferimenti competitor. Copertura `xml_import.py` (192 righe) + `universal_xml.py` (546 righe) + `ImportXmlPage.jsx` (341 righe). |
| **L** Manuale Cap. 15 Social Publisher | ✅ | `15-social-publisher.md` + 14 voci YAML · index **182 voci** · v0.11-cap15 · white label D-041 (post sotto Pagina/Bot dell'agenzia), credenziali AES-GCM cifrate, on-demand push (no scheduling), 3 canali (FB Page/IG Business/Telegram), caption default 5-righe con emoji fisse, audit `social_posts`. Copertura `social_publisher.py` (578 righe) + `SocialPublisherPage.jsx` (470 righe). |
| **M** Manuale Cap. 16 Compliance Portali (deep-dive normativo) | ✅ | `16-compliance-portali.md` + 14 voci YAML · index **196 voci** · v0.12-cap16 · 5 regole HARD → 7 codici, 4 SOFT, 14 classi APE ammesse, ghost label `missing_rent` documentata, feed vs sync, api_push=simulated_push, D.Lgs 192/2005 + AGCM contesto. Copertura `shared/validators/compliance.py` (171 righe) + `publishing.py` compliance endpoint + `sync_engine.py` filter + `PublishingPage.jsx` modale inline. Distinto da Cap. 6 (operativo). |
| **N** Manuale Cap. 17 Domain Vault (sovranità digitale D-054) | ✅ | `17-domain-vault.md` + 15 voci YAML · index **211 voci** · v0.13-cap17 · promessa D-054, 3 componenti (sovereignty confirm + custom domain DNS + RDAP checker pubblico), TXT anti-takeover + CNAME_TARGET, audit trail append-only, help-to-connect NON transfer. Copertura `domain_vault.py` (155 righe) + `custom_domain.py` (454 righe) + `domain_check.py` (359 righe) + `DomainVerifyPage.jsx` + `DomainSovereigntyPolicyPage.jsx`. |
| **N-post** Fix RAG Pattern A + B + Micro YAML | ✅ | Escluso `manuale/*.md` da ingest, deprecato `immobili.importare-xml` (Cap. 3 → Cap. 14), arricchite `domanda_naturale` `team.limitazioni-v1` + `social.limitazioni-v1`. Smoke ristampato **14/15 PASS** (9/9 Cap. 13/14/15 · 3/3 Cap. 16 · 2/3 Cap. 17 · 1 collision Cap.8 vs Cap.17 pre-esistente). |
| **O** Manuale Cap. 18 Notifiche e attività | ✅ | `18-notifiche-attivita.md` + 16 voci YAML · index **227 voci** · v0.14-cap18 · **capitolo D-051 estremo**: 7 template Resend (`welcome`, `password_reset`, `agency_invite`, `lead_notification`, `saved_search_alert`, `founders_welcome`, `founders_admin_notification`) + toast in-app sonner + cron saved-search super_admin (frequency flag ignorato v1) + audit trail 10 collezioni Mongo non-UI + Dashboard 6 KPI counter. Documenta NO modulo dedicato / NO Bell icon / NO activity feed / NO push/SMS/WhatsApp / NO retry queue / NO webhook Resend / NO UI preferenze. `push` in schema utente = dead code. Copertura `shared/email/client.py` (117 righe) + `apps/immoweb/cron.py` + `apps/immocloud/saved_searches.py` + `sonner.jsx`. Backlog A-017 → A-023 (7 voci qualità prodotto proposte). |
| **P** Manuale Cap. 19 Impostazioni agenzia | ✅ | `19-impostazioni-agenzia.md` + 14 voci YAML · index **241 voci** · v0.15-cap19 · 5 sezioni SettingsPage (identità/fiscale/indirizzo/contatti/modalità sito) + PATCH `/agencies/me` owner-only + billing SEPARATO (piani Founders €49/€99/€249/€299 + 6 credit packages €0,05/cred + Stripe checkout/portal + STRIPE_ENABLED flag → 503). **Onestà D-051**: 3 template omnia stub "presto disponibile" inattivi, NO uploader logo/color picker, campi schema-only (logo_url/primary_color/REA/FIAIP/contact.website/country/plan_type), NO validazione P.IVA/CF, NO transfer ownership (owner_id immutabile), NO audit settings, toast embedded (NON sonner). Team/Domini/API Keys/Notifiche = pagine separate. Copertura `SettingsPage.jsx` (358 righe) + `agencies.py` + `AgencyInDB` + `BillingPage.jsx` (235 righe) + `plans.py`. |
| **Q** Manuale Cap. 20 API Keys e integrazioni (Track B / API Gateway) | ✅ | `20-api-keys-integrazioni.md` + 14 voci YAML · index **255 voci** · v0.16-cap20 · **dual-track pricing D-051**: Track B = €0,03/cred vs Track A = €0,05/cred (wallet contabilmente separati). Copertura `ApiKeysPage.jsx` (351 righe) + `apps/immoweb/api_keys.py` (199 righe) + `apps/v1/gateway.py` + `shared/auth/api_key.py` + `shared/models/api_key.py`. Emissione `omk_live_<28ch>` show-once + hash SHA-256. Endpoint `/api/v1/*` con costi: valuator 5cr, mortgages 1cr, legal 3cr, feed 0, me 0, staging ~15cr. Ledger `api_credit_ledger` + `api_usage_log`. **NO** auto-ricarica Stripe (top-up manuale), UI usage detail, reportistica per-partner, rotazione auto, scoping endpoint, rate limit, IP whitelist, webhook. Widget v1: valuator/mortgages/lead-capture. Backlog A-026 UI usage · A-027 report per-partner. |
---
## Manuale operativo — progresso
| Cap | Modulo | Voci HAL | Stato |
|-----|--------|:--------:|:-----:|
| 1 | Primo accesso | 10 | ✅ v1.0.4 (portali v1 aggiornati) |
| 2 | Dashboard | 8 | ✅ |
| 3 | Immobili | 15 | ✅ v1.0.2 (cross-ref Cap. 6/7 + APE partner "in valutazione") |
| 4 | Clienti | 12 | ✅ |
| 5 | Match | 11 | ✅ |
| 6 | Portali / Publishing | 12 | ✅ |
| 7 | Fascicolo Immobile | 12 | ✅ v1.0 (esteso oltre §3.6) |
| 8 | Sito web agenzia | 12 | ✅ v1.0 (site + themes + brand extractor + custom domain) |
| 9 | Virtual Staging | 12 | ✅ v1.0 (pipeline SAM2+Flux+ESRGAN, 5 stili, 6 stanze, reverse mode, watermark AGCM) |
| 10 | HAL Agent CRM | 13 | ✅ v1.0 (chat + 5 tool CRM, streaming SSE, Migliora con HAL 3 langs+3 toni, naming Fase 0) |
| 11 | Mutui comparatore | 12 | ✅ v1.0.1 (H-bis: 8 banche, 9 Consap, ING interamente fuori Consap, disclaimer TUB 128-sexies) |
| 12 | HAL Knowledge | 13 | ✅ v1.0 (motore TF-IDF+Gemini 3 Flash, corpus 7 file + Cap. 1-11, soglie confidence, distinzione D-040 tre HAL, limiti v1) |
| 13 | Team & Ruoli (Collaboratori) | 13 | ✅ v1.0 (magic-link 7gg, ruoli agency_admin/agent, 4 stati invito, upgrade role solo se client, segreteria = concetto operativo) |
| 14 | Import XML (Migrazione) | 13 | ✅ v1.0 (flusso Preview→Commit, session 10min, dedupe reference_code, dry-run, tabelle mapping 18 tipi/19 energetiche/6 contratti/25 features, zero riferimenti competitor) |
| 15 | Social Publisher | 14 | ✅ v1.0 (FB Page/IG Business/Telegram, white label D-041, credenziali AES-GCM, on-demand push, caption default 5-righe, audit social_posts, no scheduling/analytics/carosello v1) |
| 16 | Compliance Portali (deep-dive) | 14 | ✅ v1.0 (5 HARD → 7 codici, 4 SOFT, 14 classi APE, ghost label missing_rent, feed vs sync, D.Lgs 192/2005 + AGCM contesto, distinto da Cap. 6 operativo) |
| 17 | Domain Vault (sovranità digitale) | 15 | ✅ v1.0 (D-054 promise, sovereignty confirm + custom domain DNS + RDAP checker, TXT anti-takeover, audit `domain_vault_events`, help-to-connect NON transfer) |
| 18 | Notifiche e attività (D-051 estremo) | 16 | ✅ v1.0 (7 template Resend + toast sonner + cron saved-search super_admin + 10 audit collections non-UI + Dashboard 6 KPI · NO Bell / NO activity feed / NO push/SMS/WhatsApp / NO retry queue / `push` dead code) |
| 19 | Impostazioni agenzia (v1 onesta) | 14 | ✅ v1.0 (SettingsPage 5 sezioni identità/fiscale/indirizzo/contatti/sito mode · owner-only PATCH · 3 template omnia stub inattivi · NO logo/color/REA/FIAIP UI · billing separato Founders €49/€99/€249 + crediti €0,05 + Stripe) |
| 20 | API Keys e integrazioni (Track B / API Gateway) | 14 | ✅ v1.0 (dual-track pricing €0,03 vs €0,05 · plaintext omk_live_ show-once · endpoint `/api/v1/*` valuator 5cr/mortgages 1cr/legal 3cr/feed 0 · widget embed script · NO auto-ricarica/UI usage detail/rate limit/webhook/rotazione) |
| 21 | Valutatore immobiliare (dual-tier B2C · post B2C-VAL-01) | 12 | ✅ v1.0 (BASE 1×/12mo gratis + UNI €2,99 Stripe + PDF · paywall server-side · upsell CTA · agent pass-through crediti agenzia · fascicolo bypass) |
| 22–26 | — | — | ⏳ |
| 27 | MLS Network | — | 🔒 placeholder |
| 28 | Academy | — | 🔒 frozen |
**Totale**: **21/26 capitoli (81%)** · **267 voci HAL** · **100 screenshot placeholder** in `screenshots-index.md`
**Task recenti chiusi**:
- ✅ **B2C-VAL-01** (16-Ago-2026): gate valutatore dual-tier + Stripe checkout €2,99 + paywall PDF + pytest 10/10 verdi
- ✅ **Cap. 21 Manuale** (16-Ago-2026): 12 voci `valutatore.*` post-merge B2C-VAL-01
**Convenzioni**: `[SCREEN: id]` · aggiornare GAP.md + CHANGELOG · YAML = 1 voce = 1 chunk RAG.
---
## HAL Knowledge — stato tecnico
| Componente | Stato |
|------------|:-----:|
| Motore | TF-IDF + Gemini (`hal_knowledge.py`, D-061) |
| YAML ingest | ✅ attivo |
| Corpus .md | PRD, ROADMAP, DECISIONS, AUDIT_M2, PROGRAMMA, ASPETTI, BUSINESS_MODEL |
| **Escluso** | ~~CHANGELOG.md~~ (B-ter) |
| Index | `hal-index.json` v0.11-cap15 |
| Live B-bis | `manual_hal_indexed: 56` ✅ |
| Post Cap. 10 | 117 voci ✅ reindex + smoke 3/3 PASS |
| Post G-bis | 117 voci ✅ reindex + smoke retrieval fix validato (testing_agent) |
| Post Cap. 11 | 129 voci ✅ reindex + smoke 3/3 PASS |
| Post H-bis | 129 voci ✅ reindex live (id voce rinominato + md5 cambiati) |
| Post Cap. 12 | 142 voci ✅ reindex live + smoke 3/3 PASS (high: 0.293/0.217/0.478) |
| Post Cap. 13 | 155 voci ⏳ reindex live pending (super_admin) |
| Post Cap. 14 | 168 voci ⏳ reindex live pending (super_admin) |
| Post Cap. 15 | 182 voci ✅ reindex live confermato (già indexed al restart backend) |
| Post Cap. 16 | **196 voci** ⏳ reindex live pending (super_admin) |
| Post Cap. 17 | **211 voci** ✅ reindex live confermato (Fix RAG · smoke 14/15 PASS) |
| Post Cap. 18 | **227 voci** ⏳ reindex live pending (super_admin) |
| Post Cap. 19 | **241 voci** ⏳ reindex live pending (super_admin) |
| Post Cap. 20 | **255 voci** ⏳ reindex live pending (super_admin) |
| Post Cap. 21 | **267 voci** ⏳ reindex live pending (batch a fine manuale) |
**Reindex** (super_admin): `POST /api/app/hal/knowledge/reindex?force=true`
**Smoke Cap. 20** (dopo reindex Founder):
1. *Come emetto una nuova API key OMNIA? Posso rileggerla dopo?* → `api-keys.emissione-show-once`
2. *Quanto costa un credito Track B? È diverso dai piani B2B?* → `api-keys.pricing-track-b`
3. *Quali endpoint /api/v1 esistono? Come autentico?* → `api-keys.api-v1-endpoints`

**Smoke Cap. 19** (dopo reindex Founder):
1. *Come cambio il nome della mia agenzia in OMNIA?* → `settings.sezione-identita` (o `settings.cos-e`)
2. *Perché non riesco a modificare le impostazioni? Sono agency_admin invitato.* → `settings.permessi-ownership` (o `settings.errori-comuni`)
3. *Dove attivo un piano OMNIA? Come funzionano i Founders?* → `settings.billing-pagina-separata`

**Smoke Cap. 18** (dopo reindex Founder):
1. *Esiste una pagina Notifiche o una Bell icon in OMNIA?* → `notifiche.cos-e` (o `notifiche.limitazioni-v1`)
2. *Quali email invia OMNIA automaticamente?* → `notifiche.email-panoramica`
3. *C'è un feed attività recenti nella dashboard?* → `notifiche.dashboard-vs-activity-feed`

**Smoke Cap. 16**:
1. *Quali campi devo compilare per passare compliance HARD?* → `compliance.mapping-campi-immobile`
2. *Perché un affitto risulta prezzo mancante?* → `compliance.hard-prezzo-canone` (o `compliance.affitto-vs-vendita`)
3. *Differenza fra violazione HARD e warning SOFT?* → `compliance.soft-warning-qualita` (o `compliance.panoramica-validatore`)
---
## Pricing (Founder approvato)
- **B2B** v3.0: Founders €49/€99/€249 · standard €79/€179/€349 · 1 cr = €0.05
- **B2C** v1.0: rail carta · UNI €2.99 · staging €0.90 · Legal €1.00 · visura/planimetria fase 2
---
## Cap. 6 — onestà codice
- **8 portali** `CATALOG_SEED` (Subito, Bakeca, Kijiji, Wikicasa, FB, Google, Attico, Case24)
- **NON v1**: Idealista, Immobiliare.it, Casa.it
- **feed_pull** = portali scaricano feed · **api_push** = simulated_push v1
- Sync 06:00 UTC · Compliance 5 HARD + 4 SOFT · Wizard M2.6d
---
## Prossimi task (ordine Founder)
| # | Task | Priorità |
|---|------|:--------:|
| 1 | Billing UI listino Founder | 🟡 |
| 2 | B2C Stripe checkout | 🟡 |
| 3 | Screenshot kit (TASK I) | 🟡 |
| 4 | Hard-gate crediti Virtual Staging (pre-check saldo) | 🟢 |
| 5 | Sito Web v2 · scope da definire (P0 Hero+Chi Siamo+Contatti+Footer + extractor esteso) | 🟠 aperta |
| 6 | Cap. 13+ manuale (candidati: HAL Legal · Team & Ruoli · Impostazioni · Domain Vault) | 🟢 |
---
## Micro-fix aperti
_**Fix RAG Pattern A + B + Micro YAML applicato Feb 2026**: escluso `manuale/*.md` da ingest, deprecato `immobili.importare-xml` (Cap. 3 → Cap. 14), arricchite `domanda_naturale` `team.limitazioni-v1` + `social.limitazioni-v1`. Smoke ristampato: **14/15 PASS** (9/9 Cap. 13/14/15 · 3/3 Cap. 16 · 2/3 Cap. 17 · 1 collision Cap.8 vs Cap.17 pre-esistente)._
_G-bis retrieval Cap. 9 applicato (Feb 2026)._
_**Rate limit HAL chat vs improve = SEPARATI CONFERMATO** (60/h ciascuno, no change al_agent.py — decisione Founder Feb 2026)._
_**`chunk_id` in `/ask` sources[]** = fix applicato + test aggiornati + su GitHub `main` (Feb 2026)._

---

## Backlog qualità prodotto

**11 voci tracciate in `ASPETTI_DA_APPROFONDIRE.md` (A-006 → A-016)** — review Founder post-manuale.
- **P1 (4 voci)**: A-006 Tooltip confidence · A-007 Rimozione membro · A-013 Hard-gate crediti Staging · A-014 Billing UI + B2C Stripe live
- **P2 (4 voci)**: A-008 Cambio ruolo · A-009 Bulk-assign agent post-import · A-010 Storico import UI · A-015 Sito Web v2 scope P0
- **P3 (3 voci)**: A-011 Social scheduling · A-012 Social metrics · A-016 Boost tag mutui

Vedi tabella riepilogo in fondo ad `ASPETTI_DA_APPROFONDIRE.md`.
Nessuna implementazione senza *"vai"* esplicito del Founder.

---

## Handoff nuova sessione
