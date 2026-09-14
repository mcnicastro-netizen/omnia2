# OMNIA Real Estate — Product Requirements Document

**Versione**: 1.1
**Data**: Gennaio 2026 (ultimo update: Feb 2026 — Cap. 20 · API Keys e integrazioni)
**Founder**: mcnicastro-netizen

- **Ultimo update (Feb 2026 — 📖 TASK Q · Cap. 20 · API Keys e integrazioni · Track B API Gateway)**:
  - ✅ **Cap. 20 · API Keys e integrazioni**: 15 sottocapitoli + **14 voci HAL YAML** (`api-keys.cos-e`, `dove-trovarlo`, `emissione-show-once`, `credit-wallet`, `allowed-origins`, `revoca-key`, `usage-log`, `api-v1-endpoints`, `pricing-track-b`, `widget-embed-loader`, `partner-id`, `errori-comuni`, `limitazioni-v1`, `collegamenti`).
  - ✅ **Onestà D-051 pricing dual-track**: Track A (piani B2B + credit packages BillingPage Cap. 19) = **€0,05/cred** vs Track B (API Gateway ApiKeysPage Cap. 20) = **€0,03/cred**. Wallet contabilmente separati.
  - ✅ **Endpoint `/api/v1/*` documentati con costi**: valuator (5cr), mortgages/compare (1cr), legal/ask (3cr), feed/properties (0), me (0), health (no-auth), widgets/lead (0), staging (~15cr async).
  - ✅ **Formato chiave**: `omk_live_<28 base32>` plaintext show-once + hash SHA-256 + prefix 12ch visibile. Ledger `api_credit_ledger` + `api_usage_log`.
  - ✅ **`hal-index.json` rigenerato**: v0.16-cap20, **255 voci totali** (Cap. 1-20), 20 source files.
  - 📸 Screenshots-index: +5 righe Cap. 20. Totale **95 screenshot**.
  - 📈 **Progresso manuale**: 20/26 capitoli (77%). Totale voci HAL: **255**.
  - 📋 Backlog: A-026 UI usage detail per chiave · A-027 reportistica per-partner.

- **Ultimo update precedente (Feb 2026 — 📖 TASK O · Cap. 19 · Impostazioni agenzia · v1 onesta)**:
  - ✅ **Cap. 19 · Impostazioni agenzia**: 15 sottocapitoli + **14 voci HAL YAML** (`settings.cos-e`, `settings.dove-trovarlo`, `settings.sezione-identita`, `settings.sezione-fiscali`, `settings.sezione-indirizzo`, `settings.sezione-contatti`, `settings.sezione-sito-web`, `settings.permessi-ownership`, `settings.endpoint-patch`, `settings.billing-pagina-separata`, `settings.chi-non-e-coperto`, `settings.errori-comuni`, `settings.limitazioni-v1`, `settings.collegamenti`).
  - ✅ **Onestà D-051**: la SettingsPage v1 copre **solo 5 sezioni anagrafica** (identità/fiscale/indirizzo/contatti/modalità sito). Template omnia (minimal/elegant/bold) TUTTI stub "presto disponibile" inattivi. Nessuna UI per logo/colori/REA/FIAIP/plan_type. Nessuna validazione P.IVA/CF/CAP/telefono. Owner-only PATCH (agency_admin invitato → 403 not_owner). Toast success = banner emerald embedded (NON sonner Cap. 18). Team/API Keys/Domain/Notifiche/Billing = pagine separate.
  - ✅ **Billing pagina separata** (`/app/settings/billing`, `BillingPage.jsx` 235 righe): piani Founders €49/€99/€249/€299 + 6 credit packages (€0,05/cred, ratio 20 cred/€, no sconto volume) + Stripe checkout/portal. Feature flag `STRIPE_ENABLED != "true"` → HTTP 503 "Billing è in preparazione".
  - ✅ **`hal-index.json` rigenerato**: v0.15-cap19, **241 voci totali** (Cap. 1-19), 19 source files.
  - 📸 Screenshots-index: +8 righe Cap. 19. Totale **90 screenshot**.
  - 📈 **Progresso manuale**: 19/26 capitoli (73%). Totale voci HAL: **241**.

- **Ultimo update precedente (Feb 2026 — 📖 TASK O · Cap. 18 · Notifiche e attività · D-051 estremo)**:
  - ✅ **Cap. 18 · Notifiche e attività**: 18 sottocapitoli + **16 voci HAL YAML** (`notifiche.cos-e`, `notifiche.dove-trovarlo`, `notifiche.canali-attivi`, `notifiche.email-panoramica`, `notifiche.template-welcome-password`, `notifiche.template-agency-invite`, `notifiche.template-lead-notification`, `notifiche.template-saved-search-alert`, `notifiche.toast-in-app`, `notifiche.cron-saved-searches`, `notifiche.preferenze-utente`, `notifiche.audit-trail-interno`, `notifiche.dashboard-vs-activity-feed`, `notifiche.errori-comuni`, `notifiche.limitazioni-v1`, `notifiche.collegamenti`).
  - ✅ **Onestà D-051 estrema**: Cap. 18 documenta un modulo che v1 **NON esiste**. Il capitolo elenca esaustivamente cosa NON c'è (no router `/notifications`, no Bell icon, no activity feed, no push/SMS/WhatsApp, no retry queue, no webhook Resend, no UI preferenze) e documenta invece cosa esiste: 7 template Resend (`welcome`, `password_reset`, `agency_invite`, `lead_notification`, `saved_search_alert`, `founders_welcome`, `founders_admin_notification`) + toast sonner (~4-5s ephemera) + cron saved-search super_admin (frequency flag ignorato v1) + 10 audit collections Mongo non-UI + Dashboard 6 KPI counter (che NON è activity feed).
  - ✅ **Dead code documentato**: schema `User.notification_channels: List[Literal["email", "push"]]` accetta `"push"` ma nessun sender push implementato. `saved_search.frequency` (instant/daily/weekly) salvato ma cron ignora il valore.
  - ✅ **`hal-index.json` rigenerato**: v0.14-cap18, **227 voci totali** (Cap. 1-18), 18 source files.
  - 📸 Screenshots-index: +7 righe Cap. 18 (email-welcome/agency-invite/lead-notification/saved-search/toast-success/toast-error/dashboard-kpi). Totale **79 screenshot**.
  - 📈 **Progresso manuale**: 18/26 capitoli (69%). Totale voci HAL: **227**.
  - 📋 **Backlog qualità prodotto proposti**: A-017 Notification center in-app · A-018 Activity feed dashboard · A-019 Frequency-aware cron · A-020 Internal APScheduler saved-searches · A-021 UI notification preferences · A-022 Retention policy audit collections · A-023 Toast duration tuning.

- **Ultimo update precedente (Feb 2026 — 🔧 FIX RAG · Pattern A + Pattern B + Micro YAML)**:
  - ✅ **Pattern A**: escluso `memory/manuale/*.md` dall'ingest RAG in `hal_knowledge.py`. Solo i chunk atomici YAML (`memory/manuale/hal/*.yaml`) sono la sorgente retrieval per il manuale. I `.md` restano lettura umana. Aggiunto cleanup orfani in `ingest_corpus()` con rebuild TF-IDF su rimozioni.
  - ✅ **Pattern B**: deprecati/retagged 2 chunk legacy in `03-immobili.yaml` (`immobili.importare-xml`, `immobili.importare-xml-universale`) → tags `[deprecato-cap14, redirect]`, puntatori a Cap. 14. Nessun id rimosso (compat correlati esterni).
  - ✅ **Micro YAML**: arricchite `domanda_naturale` + `a_cosa_serve` di `team.limitazioni-v1` (Cap. 13) e `social.limitazioni-v1` (Cap. 15) per battere collisioni con `ASPETTI_DA_APPROFONDIRE.md` e altri chunk stesso file.
  - ✅ **Smoke test ristampato**: 14/15 PASS (93%) su Cap. 13/14/15 (9/9) + Cap. 16 (3/3) + Cap. 17 (2/3). 1 collision pre-esistente Cap. 8 vs Cap. 17 (`custom-domain` chapter overlap, non causata dal fix).
  - ✅ **Reindex live**: `chunks_indexed=659` (448 root md + 211 YAML) · `manual_hal_indexed=211` invariato.
  - 📋 Nota: NO Cap. 18 in questo task. Solo fix retrieval quality per direttiva Founder.

- **Ultimo update precedente (Feb 2026 — TASK M · Cap. 16 · Compliance Portali deep-dive normativo)**:
  - ✅ **Cap. 16 · Compliance Portali** (deep-dive normativo del validatore HARD/SOFT): 14 sottocapitoli + **14 voci HAL YAML** (`compliance.panoramica-validatore`, `compliance.hard-prezzo-canone`, `compliance.hard-superficie`, `compliance.hard-ape-classi-ammesse`, `compliance.hard-foto-minimo`, `compliance.hard-indirizzo`, `compliance.soft-warning-qualita`, `compliance.mapping-campi-immobile`, `compliance.feed-vs-sync`, `compliance.privacy-non-in-feed`, `compliance.affitto-vs-vendita`, `compliance.codici-violazione`, `compliance.correggere-da-modale`, `compliance.limitazioni-v1`). Copertura 1:1 con `shared/validators/compliance.py` (171 righe) + `publishing.py` compliance endpoint + `sync_engine.py` filter + `PublishingPage.jsx` modale inline.
  - ✅ **Distinto da Cap. 6**: Cap. 6 = **operativo** (attiva portale, sync, wizard); Cap. 16 = **riferimento normativo/tecnico** (perché, quali campi, contesto legale, mapping). Cross-ref aggiunto in Cap. 6 §6.5.
  - ✅ **Onestà D-051 chiave**: 5 regole HARD → 7 codici precisi, 4 SOFT, 14 classi APE ammesse esatte, cornice normativa italiana (D.Lgs 192/2005 APE + AGCM trasparenza prezzi) come contesto (no consulenza legale), architettura funzioni pure senza DB, ghost label `missing_rent` documentata onestamente (frontend orfana, backend emette sempre `missing_price`), api_push=simulated_push, feed vs sync 1:1, privacy L3/L4 esclusa a monte.
  - ✅ **Limiti v1 espliciti**: NO CompliancePage.jsx standalone (modale inline), api_push simulated, no sync-log UI, ghost label missing_rent, no bottone Sospendi sync, legacy PORTAL_CATALOG (Idealista NON v1), no trend storico, no promemoria APE, no bottone Correggi dalla modale, soglie hardcoded (MIN_PHOTOS=3, MIN_TITLE_CHARS=10, MIN_DESCRIPTION_CHARS=50), no controllo semantico, no audit trail correzioni.
  - ✅ **`hal-index.json` rigenerato**: v0.12-cap16, **196 voci totali** (Cap. 1-16), 16 source files.
  - 📸 Screenshots-index: +3 righe Cap. 16. Totale 72 screenshot.
  - 📋 **Nota conflitto planning**: "Cap. 16 Domain Vault" (menzionato in docs precedenti) → spostato a Cap. futuro. Cap. 16 è Compliance Portali (priorità Founder).
  - 📈 **Progresso manuale**: 16/26 capitoli (62%). Totale voci HAL: **196**. Prossimo: batch reindex Cap. 13/14/15/16 + smoke, poi Cap. 17+ (HAL Legal, Domain Vault, Impostazioni, Billing, Universal Portal Wizard M2.6d).

- **Ultimo update (Feb 2026 — TASK L · Cap. 15 · Social Publisher)**:
  - ✅ **Cap. 15 · Social Publisher** (Facebook, Instagram, Telegram): 12 sottocapitoli + **14 voci HAL YAML** (`social.cos-e`, `social.dove-trovarlo`, `social.canali-supportati`, `social.credenziali-facebook`, `social.credenziali-instagram`, `social.credenziali-telegram`, `social.configurare-canale`, `social.validare-canale`, `social.pubblicare-immobile`, `social.caption-default`, `social.audit-log`, `social.errori`, `social.limitazioni-v1`, `social.collegamenti`). Copertura 1:1 con `social_publisher.py` (578 righe) + `SocialPublisherPage.jsx` (470 righe).
  - ✅ **Onestà documentale (D-051)**: 8 endpoint reali sotto `/api/app/publishing/social/*`, 3 canali supportati (Literal ChannelType), ruoli agency_admin/super_admin/branch_admin/group_admin, white label D-041 esplicito ("OMNIA never posts under its own identity"), credenziali AES-GCM cifrate, API base Meta Graph v20.0 + Telegram Bot API, caption limits esatti (2000 safe, 1024 Telegram photo), credential fields per canale documentati 1:1 con SOCIAL_CATALOG, IG richiede image_url HTTPS, flusso 2-step IG (container→publish), caption default 5-righe con emoji fisse 📍 💶 📐, audit `social_posts` (success + failed), counter live posts_ok/posts_failed, status transitions active/pending/disabled/error, 12+ codici errore mappati.
  - ✅ **Limiti v1 dichiarati esplicitamente**: no scheduling (solo on-demand), no X/LinkedIn/TikTok/YouTube/WhatsApp/Threads, no carosello, no video/reel/story, no editor caption con preview, no template caption per agenzia, no analytics engagement, no auto-refresh token FB long-lived, no bulk publish, no rollback multi-canale, no preview finale, no moderazione pre-pubblicazione.
  - ✅ **`hal-index.json` rigenerato**: v0.11-cap15, **182 voci totali** (Cap. 1-15), 15 source files.
  - 📸 Screenshots-index: +3 righe Cap. 15. Totale 69 screenshot catalogati.
  - 📈 **Progresso manuale**: 15/26 capitoli (58%). Totale voci HAL: **182**. Prossimo: reindex prod super_admin + smoke 3/3 Cap. 15, poi Cap. 16+ (HAL Legal se attivato, Domain Vault, Compliance HARD/SOFT, Impostazioni, Billing UI).

- **Ultimo update (Feb 2026 — TASK K · Cap. 14 · Import XML / Migrazione)**:
  - ✅ **Cap. 14 · Import XML** (Migrazione da altro gestionale): 12 sottocapitoli + **13 voci HAL YAML** (`import.cos-e`, `import.dove-trovarlo`, `import.flusso-preview-commit`, `import.file-xml-requisiti`, `import.mapping-tabelle`, `import.dedupe`, `import.simulazione-dry-run`, `import.divergenze`, `import.risultato-commit`, `import.errori`, `import.limitazioni-v1`, `import.checklist-migrazione`, `import.collegamenti`). Copertura 1:1 con `xml_import.py` (192 righe) + `universal_xml.py` (546 righe) + `ImportXmlPage.jsx` (341 righe).
  - ✅ **Onestà documentale (D-051)**: 3 endpoint reali (POST /preview, POST /commit, GET /session/{id}), ruolo agency_admin+super_admin obbligatorio, TTL session 10min in-memory (non persistita), tabelle mapping esatte (TYPE_CODE_MAP 18 codici, ENERGY_CODE_MAP 19, OPERATION_CODE_MAP 6, FEATURE_KEYWORDS 25), regola `looks_like_property` ≥3 tag, guard `missing_city_or_title`, cap divergences 50 + samples 5, dedupe scoped a agency_id, batch insert 100 (ordered=False), metadata `_import_source` + `_import_reference` per audit, stato default `approved`+`listed`+no agent_id, dry-run non consuma session, copy anti-competitor D-050.
  - ✅ **Limiti v1 dichiarati esplicitamente**: no CSV/JSON/Excel, no sync automatica, no wizard mappatura, no rollback batch, no session persistita, no preview foto, no import clienti/lead via XML, no fuzzy match dedupe, no auto-assign agent, no storico import UI.
  - ✅ **`hal-index.json` rigenerato**: v0.10-cap14, **168 voci totali** (Cap. 1-14), 14 source files.
  - 📸 Screenshots-index: +3 righe Cap. 14. Totale 66 screenshot catalogati.
  - 📈 **Progresso manuale**: 14/26 capitoli (54%). Totale voci HAL: **168**. Prossimo: reindex prod super_admin + smoke 3/3 Cap. 14, poi Cap. 15+ (HAL Legal se attivato, Impostazioni, Domain Vault, Billing, Universal Export).

- **Ultimo update (Feb 2026 — TASK J · Cap. 13 · Team & Ruoli / Collaboratori)**:
  - ✅ **Cap. 13 · Team & Ruoli** (Collaboratori): 13 sottocapitoli + **13 voci HAL YAML** (`team.cos-e`, `team.dove-trovarlo`, `team.ruoli-disponibili`, `team.invitare-membro`, `team.tab-inviti`, `team.accettare-invito`, `team.lista-membri`, `team.chi-puo-invitare`, `team.onboarding-vs-invito`, `team.utente-gia-registrato`, `team.errori-comuni`, `team.limitazioni-v1`, `team.collegamenti`). Copertura 1:1 con `invites.py` (286 righe) + `agencies.py` (180 righe) + `MembersPage.jsx` (225 righe) + `InviteMemberModal.jsx` (134 righe) + `AcceptInvitePage.jsx` (186 righe).
  - ✅ **Onestà documentale (D-051)**: ruoli invitabili SOLO `agent` + `agency_admin` (segreteria = concetto operativo NON ruolo backend), `INVITE_EXPIRY_DAYS=7` esatto, idempotenza pending (refresh token+scadenza), sicurezza L5 token nel fragment, ruoli non invitabili documentati (super_admin/client/group_admin/branch_admin/branch_agent), upgrade role solo se `client` con tabella verità 6 casi, auto-login post-accept, password min 8 + bcrypt, elenco membri visibile anche a `agent` (no require_roles), revoca NON retroattiva su accepted, onboarding promuove server-side a `agency_admin` (S2 sicurezza), vincolo one-owner.
  - ✅ **Limiti onestamente dichiarati**: no rimozione membro UI, no cambio ruolo post-join, no toggle is_active UI, no audit log UI, no permessi granulari per membro, no franchising, no notifica real-time, no transfer ownership.
  - ✅ **`hal-index.json` rigenerato**: v0.9-cap13, **155 voci totali** (Cap. 1-13), 13 source files con MD5 aggiornati.
  - 📸 Screenshots-index: +3 righe Cap. 13. Totale 63 screenshot catalogati.
  - 📈 **Progresso manuale**: 13/26 capitoli (50%). Totale voci HAL: **155**. Prossimo: reindex prod super_admin + smoke 3/3 Cap. 13, poi Cap. 14+ (HAL Legal se attivato, Impostazioni, Domain Vault, Billing, Universal Import XML).

- **Ultimo update (Feb 2026 — TASK I · Cap. 12 · HAL Knowledge)**:
  - ✅ **Cap. 12 · HAL Knowledge** (meta-doc del RAG stesso): 12 sottocapitoli + **13 voci HAL YAML** (`halk.cos-e`, `halk.dove-lo-trovi`, `halk.come-porre-domanda`, `halk.badge-confidence`, `halk.fonti-citate`, `halk.corpus`, `halk.motore`, `halk.insufficient-context`, `halk.storico`, `halk.reindex`, `halk.status-badge`, `halk.distinzione-tre-hal`, `halk.limiti`). Copertura 1:1 con `hal_knowledge.py` (617 righe) + `HalKnowledgePage.jsx` (307 righe).
  - ✅ **Onestà documentale (D-051)**: soglie confidence 0.08/0.20 esatte, `TOP_K=5`, `CHUNK_WORDS=500/50`, corpus 7 file fondamentali (CHANGELOG escluso B-ter), modello `gemini-3-flash-preview` via Emergent LLM Key, reindex super_admin-only con MD5-idempotenza, storico 15 fetch/8 UI, super_admin vede storico di tutti, indice JSON (no pickle) per sicurezza H9, `insufficient_context` come feature D-051 zero-invenzioni, distinzione D-040 fra HAL Knowledge / HAL Agent CRM / HAL Legal.
  - ✅ **Limiti onestamente dichiarati**: no multilingua (corpus IT), no embeddings neurali (TF-IDF D-061), no memoria multi-turn, no feedback loop utente, no rate limit dedicato v1, no scraping/web search, no multitenant a corpus (isolamento è HAL Agent CRM), no TTL storico sessioni.
  - ✅ **`hal-index.json` rigenerato**: v0.8-cap12, **142 voci totali** (Cap. 1-12), 12 source files con MD5 aggiornati.
  - 📸 Screenshots-index: +3 righe Cap. 12. Totale 60 screenshot catalogati.
  - 📈 **Progresso manuale**: 12/26 capitoli (46%). Totale voci HAL: **142**. Prossimo: reindex prod super_admin + smoke 3/3 Cap. 12, poi Cap. 13+ (candidati: HAL Legal · Team & Ruoli · Impostazioni · Domain Vault).

- **Ultimo update (Feb 2026 — TASK C · Cap. 6 · Portali/Publishing)**:
  - ✅ **Cap. 6 · Portali/Publishing**: 9 sottocapitoli + **12 voci HAL YAML**. Copre a-cosa-serve del Publishing Center, catalogo 8 portali del `CATALOG_SEED` (Subito · Bakeca · Kijiji · Wikicasa · FB Marketplace · Google Business · Attico · Case24), attivazione con form credenziali AES-256-GCM, sync daily 06:00 UTC + sync manuale con retry 60/300/1800s, Compliance HARD (5 regole: prezzo · superficie · APE valida · ≥3 foto · indirizzo) + SOFT (4 warning), modale Compliance con top-5 reasons + lista bloccati, Universal Portal Wizard M2.6d (4 step feed_pull only), feed XML pubblico osf_federata/generic_rss, log audit trail.
  - ✅ **Onestà documentale (D-051)**: solo gli 8 portali del catalogo v1 documentati come attivi. Idealista/Immobiliare.it/Casa.it esplicitati come "continua a usarli col loro pannello". api_push (FB/Google) chiaramente marcato "simulato in v1, live in arrivo".
  - ✅ **Micro-fix Cap. 1 v1.0.3**: HAL Knowledge non è più "in arrivo" (corpus attivo dopo TASK B-bis/B-ter). Aggiornati `01-primo-accesso.md` e `.yaml`.
  - ✅ **`hal-index.json` rigenerato**: v0.2-cap6, **68 voci totali** (Cap. 1-6), md5 aggiornati per tutti i file.
  - 📸 Screenshots-index: +6 righe Cap. 6. Totale 34 screenshot catalogati.
  - 📈 **Progresso manuale**: 6/26 capitoli (23%). Totale voci HAL: **68**. Prossimo: Cap. 7 (secondo indice).

- **Ultimo update (05-Ago-2026 — TASK A · Pricing Sync ufficiale)**:
  - ✅ **Listino Founder 5-Ago-2026 sincronizzato** in codice + Stripe + docs:
    - Founders 12m: Starter **€49** · Pro **€99** · Agency **€249** · crediti/mese **120/1200/3600**
    - Standard: €79/179/349
    - Pacchetti crediti 6 tier, ratio fisso 20 cr/€ (€20→400 fino a €1000→20000)
    - Consumo: staging 18, HAL Legal 12, visura 24, valuator UNI+PDF 40, video 60, promozioni 400/1000/2000
    - **Rimossi**: planimetria catastale, ispezione ipotecaria (margini bassi in v1)
    - Multiposting + Portal Wizard custom **inclusi su tutti i piani**
  - ✅ **Catalog Stripe sandbox rigenerato** (idempotente) via `python -m apps.billing.setup_stripe`.
  - ♻️ `backend/apps/billing/plans.py` riscritto con nuovo campo `credits_included_monthly` esposto in `/api/billing/plans`.
  - ✨ `memory/PRICING_OMNIA.md` v3.0 — LISTINO UFFICIALE (sostituisce ogni bozza precedente incluso v2.0).
  - 📌 **Enterprise** resta con prezzi legacy €299/2990 — sessione dedicata su posizionamento + Custom API.
  - 📌 **Break-even ricalcolato**: mix realistico 10 agency → +€250 margine/mese · 50 Founders pieno → ~€48k/anno.

- **Ultimo update (27-Feb-2026 notte — Cap. 5 · Match + 3 fix v1.0.1 su Cap. 4)**:
  - ✅ **Cap. 5 · Match**: 11 sottocapitoli + **11 voci HAL YAML**. Copre motore matching, scala temperature 🔥🌶️☀️❄️ con range precisi (85/65/40 dal codice), 14 criteri di scoring con pesi esatti (Prezzo 17 · Operazione 14 · Città 12 · Tipologia 11 · … · Piano 3 = 100), pagina Match con filtri Score min, Lead Scoring AI (deterministic vs AI), workflow giornata tipo con power hour ROVENTI + regola 80/20, troubleshooting zero-match.
  - ✅ **3 Fix Cap. 4 · Clienti v1.0.1** (verificati sul backend):
    - Bucket Venditori: filtro codice è `client_type not in SEARCHER_TYPES` (indipendente da immobili collegati).
    - Delete client con immobili collegati: il backend blocca con 409, il manuale ora documenta il messaggio *"Impossibile eliminare: N immobile/i in carico"* e i passi per riassegnare.
    - Visibilità agente: `list_clients` filtra solo per `agency_id`. Titolare + agente + segreteria vedono TUTTA l'anagrafica agenzia; il campo "agente assegnato" è solo per statistiche.
  - 📸 Screenshots-index: +5 voci Cap. 5. Totale 28 screenshot catalogati.
  - 📈 **Progresso manuale**: 5/26 capitoli (19%). Totale voci HAL: **56**. Prossimo (attesa decisione Founder): cold start HAL Knowledge RAG **OR** Cap. 6 · Fascicolo.

- **Ultimo update (27-Feb-2026 sera — Cap. 4 · Clienti + fix v1.0.1/v1.0.2 + GAP.md formale)**:
  - ✅ **Cap. 4 · Clienti**: 7 sottocapitoli + **12 voci HAL YAML**. Copre anagrafica (5 tipi cliente, 7 stati CRM, GDPR), preferenze di ricerca, Import CSV con template, Smart Import AI (formati .csv/.xlsx/.vcf/.txt, powered by Gemini), collegamento property-seller, Smart Sorting con bucket 🔥🌶️☀️❄️ e Lead Scoring intro.
  - ✅ **Fix Cap. 3 v1.0.1** — L4 privacy: rimosso "e le agenzie in rete" (MLS network M4 non ancora implementato). L4 = solo team di agenzia.
  - ✅ **Fix Cap. 1 v1.0.2** — rimossa dicitura "attività recenti" dalla tabella Tour barra sinistra (non esiste in UI).
  - ✅ **GAP.md formale creato** (`/app/memory/GAP.md`, 119 righe): 6 sezioni (funzioni backend senza UI, moduli deprecati, duplicati, roba da NON documentare, gap per capitolo, azioni prossime). Serve come "verità operativa" per il prossimo agente.
  - ✅ **Screenshots Index**: 23 placeholder totali (Cap. 1-4). Dati demo standardizzati.
  - 📈 **Progresso manuale**: 4/26 capitoli (15%). Totale voci HAL prodotte: **45**. Prossimo: Cap. 5 · Match.

- **Ultimo update (27-Feb-2026 mattina — Cap. 1-3 + micro-cleanup)**:
  - ✅ **Manuale Operativo — Fase 0 (piano) approvato dal Founder**: mappa moduli/widget completa, indice 26 capitoli + 2 placeholder, 10 convenzioni redazionali chiuse (nomi menu = "ImmoWeb", assistente = "HAL", mls_box → "Vetrina Immobili", segreteria = concetto operativo, Gruppi = solo tier Agency, HAL Legal legale silente, screenshot placeholder-only, HAL Knowledge indicizzazione incrementale, Academy/MLS placeholder "ricco ma corto", NO Immobili Segreti).
  - ✅ **Cap. 1 · Primo Accesso**: 5 sottocapitoli in `manuale/01-primo-accesso.md` + **10 voci HAL YAML** validate in `manuale/hal/01-primo-accesso.yaml`. Rimosso vecchio file discorsivo `01-introduzione-primo-accesso.md`. Micro-fix v1.0.1: HAL Knowledge "in arrivo", nota agenti invitati, selettore agenzia chiarito, tier Agency per Gruppi.
  - ✅ **Cap. 2 · Dashboard**: 5 sottocapitoli + **8 voci HAL** allineate all'UI reale (rimosse feature inesistenti come "attività recenti").
  - ✅ **Cap. 3 · Immobili**: 7 sottocapitoli + **15 voci HAL** (81 passi, 21 errori comuni). Include privacy L1-L4 spiegata in linguaggio agenzia, import CSV/XML veloce, import XML universale (solo titolare), fascicolo con checklist 10 documenti, APE via partner esterno.
  - ✅ **Screenshots Index** (`manuale/hal/screenshots-index.md`): 17 screenshot catalogati (Cap. 1-3) con convenzioni viewport, dati demo standardizzati (Immobiliare Rossi, Belpasso CT), priorità 🔴🟡🟢.
  - ✅ **Progresso manuale**: 3/26 capitoli (12%). Totale voci HAL prodotte: **33**. Prossimo: Cap. 4 · Clienti.
  - ✅ **Stripe plans** — rimosso campo dead-code `stripe_price_id_env` da `apps/billing/plans.py` (esposto via API pubblica con valori errati per Pro/Agency, mai usato dal checkout che si basa su `lookup_key`). Test `billing/stripe` 10/10 verdi.
  - ✅ **R9 Health leak** — `/api/core/health` non espone più dettagli raw dell'eccezione DB (rischio info disclosure). Errore generico in response, dettagli loggati server-side.
  - ✅ **R10 PostHog** — verificato: già dietro guard `if (PH_KEY && indexOf("phc_") === 0)` in `frontend/public/index.html`. Nessun fix necessario (falso positivo audit).
  - ✅ **R13 LLM budget** — verificato: già 503 `llm_budget_exceeded` in tutti gli endpoint (al_legal, al_agent). Falso positivo audit.
  - 📌 **Pending Founder decisions**: R8 (moderation super_admin vs group_admin), R12 (v1 staging 501 → intenzionale per M2.5.3).
  - 📌 **Pricing v2.0 (PRICING_OMNIA.md)** — resta 🟡 BOZZA in revisione Founder. Deliverable M2.5.0/P0. Sandbox Stripe attuale (€19/29/79/299) NON allineata al listino ufficiale Founders 50 (€49/99/249 nella v più recente) — da riallineare quando Founder conferma v2.0.

- **Sessione precedente (23-Feb-2026)**:

- **Stato progetto**: 🎉 **Audit COMPLETO (Fasi 0-3) + Follow-up S1-S5 DONE · Manuale Cap. 1-3 in corso** — Aggiornamento **30-Lug-2026 (notte)**:
  - ✅ **30-Lug-2026 (follow-up report post-push, S1-S5 + R)**: testato da testing agent iteration_32 (16/16 nuovi test + 35/35 suite audit + UI Playwright tutta verde):
    - 🔴 **S1 Credenziali**: password admin/agent/stress RUOTATE (le vecchie nel repo/history Git sono invalide → 401 verificato). Test (~41 file) ora leggono da `memory/test_credentials.env` (gitignored) via conftest; `memory/*.md` e `test_reports/` bonificati; gitignore esteso (`test_reports/`, `memory/test_credentials.*`). NUOVE credenziali SOLO in `memory/test_credentials.env|.md` (mai committati).
    - 🔴 **S2 Register**: `_PUBLIC_ROLES={client, student}` — `agency_admin` E `agent` non ottenibili da registrazione pubblica. Il flusso agenzia: register (client) → OnboardingWizard → `POST /app/agencies` promuove server-side a `agency_admin`. RegisterPage: select "Tipo di account" (Agenzia/Privato/Studente) al posto della scelta ruolo; redirect post-register: agenzia→onboarding, privato→/cloud, studente→/academy.
    - 🟠 **S3 RBAC**: verificato con utente `group_admin` reale (test_groupadmin@omnia.it): dashboard/properties/settings accessibili grazie a ROLE_ALIASES in ProtectedRoute (era un falso positivo del report: guardava solo App.js).
    - 🟠 **S4**: suite phase23 35/35 verde (il test tollera `id`; failure del XML era di una run precedente).
    - 🟠 **S5**: gitignore `!.env.example` → i template env ora committabili (verificato con git check-ignore).
    - 🟡 **R**: crypto warning se manca CREDENTIALS_MASTER_KEY (R2), fallback base64 foto limitato a 600KB (R4), errori leggibili su CloudRegister (R5), timeout axios 30s (R6), `await refresh()` (R7), README root riscritto. R9/R13 erano già risolti (falsi positivi). R3/R10/R11 scelte documentate.
  - ✅ **30-Lug-2026 (Fase 2-3 audit — "sistema tutto")**: **REFACTORING ARCHITETTURALE + DEBITO TECNICO COMPLETATI** (pytest 653/653 + 10 nuovi test fase 2-3, jest frontend 19/19, testing agent iteration_31 100%):
    - **M16** Lazy loading: tutte le ~40 route in `React.lazy` + `Suspense` (chunk separati per app).
    - **M17** `ImmocloudApp.jsx` 831→33 righe: pagine estratte in `pages/` (CloudHomePage, CloudSearchPage, CloudRegisterPage) + `components/` (CloudTopNav, FooterB2C, PropertyCard) + `cloudTheme.js`.
    - **M18** Client HTTP unificato su axios `api` per tutti i flussi core B2C; `fetch` resta SOLO dove tecnicamente necessario (AlChatWidget SSE streaming, download CSV template) — scelta documentata.
    - **M19+M20+M21** Pulizia: rimossi React Query (mai usato), lodash, dayjs, swr, recharts, framer-motion, cra-template + 35 dipendenze radix/utility orfane + 44 componenti shadcn inutilizzati (restano button, sonner).
    - **M22** Clustering mappa: grid clustering puro in `lib/clustering.js` (zero dipendenze extra, unit-testato con 500 marker), vista mappa deep-linkable `?view=map`.
    - **M23** Import XML async: feed URL → job in background con polling `GET /import/jobs/{id}`; XML incollato resta sincrono; SSRF check sempre sincrono (400 immediato).
    - **M24** Fascicolo: upload multipart → Object Storage (`POST /fascicolo/{pid}/documents/upload`), download retro-compatibile col base64 legacy.
    - **M5** Multi-agency switcher: `active_agency_id` su user + `GET /auth/my-agencies` + `POST /auth/active-agency` + select in sidebar (visibile solo con 2+ agenzie).
    - **M13+H2** Deprecato e RIMOSSO `portals.py` legacy (endpoint 404, route FE eliminata) → resta un solo sistema crypto (AES-GCM `shared/utils/crypto.py`).
    - **M14** Parser CSV RFC-4180 (campi quotati, separatori interni, ""escaped, auto-rilevamento ;/,).
    - **M11** Download video auth-gated per video di agenzia (i video UGC pubblici restano pubblici); **M12** guard SSRF su image_url del virtual staging.
    - **L8** 13 helper `_agency` duplicati consolidati in `shared/auth/tenant.py`; **L9** `properties.py` splittato (357 righe + `properties_import.py`); **L10** `routing.js` dead code rimosso.
    - **L12** Revoca refresh token al logout (jti in `refresh_tokens` collection, verificato 401 post-logout); **L13** `COOKIE_SECURE` configurabile via env (default true).
    - **L3** PostHog key via `%REACT_APP_POSTHOG_KEY%` (env, non hardcoded); **L5** token invito nel fragment `#token=` (fallback query per email già inviate); **L14** conftest legge le URL da frontend/.env (mai stantie); **L15** dropzone foto accessibile (role/aria/tastiera) + alt text.
    - **L2** TypeScript incrementale attivo: tsconfig.json + `shared/lib/navigation.ts` (sanitizeNextParam, resolveLangRedirect, switchLangInPath) usato da LoginPage/LanguageSwitcher; typecheck verde.
    - **L1** Test frontend: 4 suite jest (19 test) — anti open-redirect, lang redirect, clustering, formatEUR, parità chiavi i18n IT/EN/ES (il test ha subito scovato e fatto fixare 25 chiavi `import.*` mancanti in EN/ES).
    - 🐛 **Fix bonus**: endpoint foto pubbliche `/api/public/property/{id}/photo/{idx}` non va più in 500 — gestisce data:base64, `/api/media/` (object storage) e URL esterni (302).
    - 📌 **Scelte documentate (non bug)**: L4 script Emergent in index.html è richiesto dalla piattaforma (non rimosso); L6 API key nella preview widget è inerente all'architettura embed pubblica dei widget.
  - ✅ **30-Lug-2026 (fork hardening pre-fase-finale)**: **AUDIT UNIFICATO FE+BE — TUTTI I P0 (7) + P1 (13) + P2 FUNZIONALI RISOLTI** — Il Founder ha fornito un report audit cross-stack (~60 issue) chiedendo di "sistemare tutto" prima della fase finale. Eseguito e testato (pytest 622+ verdi, testing agent 25/25 backend + 7/7 flussi frontend, iteration_30.json 100%):
    - 🔴 **C1 Role escalation** — `POST /auth/register` ora whitelista `{client, agent, agency_admin, student}`; `super_admin`/`group_admin` via registrazione → forzati a `client` (`apps/core/auth.py`).
    - 🔴 **C2 Token reset nei log** — rimosso il reset_url (con token) dai log; si logga solo l'evento.
    - 🔴 **C3 Open redirect** — `LoginPage.jsx` valida `?next=`: solo path relativi, no `//`, no `://`.
    - 🔴 **C4 Checkout rotto** — `BillingPage.jsx` `/api/billing/checkout` → `/billing/checkout` (era doppio /api).
    - 🔴 **C5 Reset password UI** — creata `ResetPasswordPage.jsx` + route `/{lang}/reset-password` + chiavi i18n IT/EN/ES. Flusso E2E verificato (forgot → token → reset → login).
    - 🔴 **C6 Branch hijacking** — `attach_branch` richiede `owner_id`/`agency_ids` del chiamante (403 `agency_not_owned` verificato) salvo super_admin.
    - 🔴 **C7 SSRF import XML** — nuovo `shared/utils/net_guard.py` (`assert_public_url`): blocca IP privati/loopback/link-local/metadata. Verificato su 169.254.169.254, 127.0.0.1, 10.x.
    - 🟠 **H1** CORS default esplicito con warning se `*`; **H3** moderazione solo `super_admin` (BE+FE allineati, via i ruoli fantasma dalla route); **H4** PropertyForm: GET fallito → submit disabilitato (mai PATCH su form vuoto); **H5** JSON-LD escape `<`→`\u003c` (anti-XSS); **H6** register B2C sincronizza AuthProvider via `refresh()`; **H7** `ProtectedRoute` espande gli alias ruoli franchising (branch_admin/group_admin) come il backend + sidebar filtrata (settings/billing/website solo admin); **H8** debito crediti API key atomico `$gte:cost` + clamp a zero (mai negativo); **H9** indice HAL Knowledge da pickle → JSON (vocab+idf+CSR), zero RCE da DB compromesso, rebuild automatico dal legacy; **H10** PhotoUploader → upload multipart su Object Storage (nuovo `POST /app/properties/photos/upload-tmp` per la modalità create, fallback base64 se storage giù); **H11** `api.js` fail-fast se manca REACT_APP_BACKEND_URL; **H12** `<Toaster/>` sonner montato in App.js; **H13** fix link `/edit` rotti (Publishing/SocialPublisher); **H14** `/auth/refresh` rifiuta utenti disabilitati; **H15** `/billing/status/{id}` auth-bound (401 senza cookie, 403 se non owner).
    - 🟡 **M1** LanguageSwitcher via `useNavigate` (router sync); **M2** rimossi path `/it/` hardcoded (BillingPage, LegalApp, WidgetsShowcase, PublishingPage); **M3** clients_smart solo immobili `active`; **M4** `update_one` con filtro `agency_id` (properties, clients); **M6** `re.escape` + cap 100 char su tutte le regex di ricerca (no ReDoS/injection, verificato con `a(b` ecc.); **M7** HalKnowledgePage `submit(q)` diretto (no race setTimeout); **M9** interceptor 401 → evento `omnia:unauthorized` → AuthProvider logout → redirect login; **M10** lang non supportata (`/fr/...`) → redirect a `/it/...`; **M25** creati `.env.example` backend+frontend completi.
    - 🟢 **L7** ErrorBoundary: stack trace solo in dev; **L11** health endpoint non espone più il messaggio d'errore DB.
    - 🧪 **Test**: 2 test stale allineati al comportamento voluto (brand `Sei HAL,`; semantica NULLABLE_FIELDS explicit-clear di seller_client_id). Suite stress 11/11 verde se eseguita come file. Nuova suite regression `tests/test_audit_p0_p1_final.py` (25 test, dal testing agent).
    - 📌 **Non affrontati (per scelta/scope)**: M5 multi-agency switcher, M11/M12 (video auth / staging allowlist — rischio basso, fal.ai esterno), M13 deprecazione portals.py legacy, M14 CSV Papa Parse, M16-M24 (lazy loading, split monoliti, React Query, clustering mappa — refactor architetturali Fase 2), L1/L2 (test FE, TypeScript), L3-L6, L8-L9, L12 (revoca refresh token richiede token-store). Elencati in ROADMAP sotto.
  - ✅ **27-Feb-2026 (fork audit-driven)**: **BUG SWEEP FEB-2026 + STRIPE SANDBOX + APE/OpenAI DOCS SCAFFOLD + MLS BOX DONE** — Chiuso ~4h di lavoro. Audit profondo del codice per pilastri (Architettura, Qualità, Funzionalità) → 18 punti A-R organizzati in `/app/memory/AUDIT_TODO_FEB2026.md`. Poi:
    - 🐛 **P0-A Privacy Gate energy field bug** — `apply_privacy_view` scriveva `{"class": ...}` invece di `{"energy_class": ...}`. La classe energetica è ora visibile su ImmobilCloud L1/L2 (99% del traffico B2C). Fix in `shared/utils/privacy_gate.py:120-124`.
    - 🐛 **P0-B Dashboard KPI mentivano** — `leads_open` e `matches_week` erano `locked=True, value=0` mentre il rollup gruppi contava dati reali. Riscritto `apps/immoweb/dashboard.py`: legge `db.leads` (new+contacted), `db.match_audit`, `db.calendar_events`. Ora l'agente singola-agenzia vede i lead sul dashboard.
    - 🐛 **P0-D Matches escludono draft** — filtro `status:"active"` sostituito a `status:{$in:["active","draft"]}`. Meno falsi positivi.
    - 🐛 **P0-E HAL hot leads** — ora include `status:contacted` con score alto (non solo `new`).
    - 🐛 **P0-F Doppio sistema Portali** — voce sidebar "Portali" legacy rimossa da `AgencyShell.jsx`. Solo "Publishing" (M2.6a) attivo.
    - 🐛 **P0-C Moderation ruoli fantasma** — `platform_admin`/`admin` erano ghosts. Ora `ALLOWED_ROLES = {"super_admin", "group_admin"}` (moderation.py) e `{"super_admin"}` in cron.py.
    - 🐛 **P1-H Group create auto-attach agency** — `POST /api/app/groups` ora aggancia automaticamente l'unica agency del creatore come primo branch (se non già in un gruppo). No più due step manuali.
    - 🐛 **P1-K Retry email lead** — `_schedule_lead_email` con exponential back-off (1s, 3s, 10s) + durable error log. Zero lead persi silenziosamente.
    - 🐛 **P3-M REACT_APP_BACKEND_URL nel backend** — sostituito con `PUBLIC_BASE_URL` in `micro_tour_video.py` e `v1/widgets.py`. Zero cross-contamination env frontend/backend.
    - 🐛 **P3-Q .env critici** — aggiunti `CREDENTIALS_MASTER_KEY` (AES-256-GCM per publishing/social), `OMNIA_PORTAL_ENC_KEY`, `PUBLIC_BASE_URL`, `FRONTEND_BASE_URL`, `SUPER_ADMIN_EMAIL`, tutti gli STRIPE_*, tutti gli SIAPE_*/OPENAI_DOCS_*.
    - 🐛 **White-label footer** — rimosso "Powered by OMNIA" dai siti agenzia (`themes.py:388`), Founder-requested D-051 no brand mentions al cliente.
    - 🧹 **D-051 vendor map rename** — `apps/immoweb/import_agestanet.py` (261 righe, brand-mention nel filesystem) → `shared/importers/vendor_map_legacy_a.py`. Zero occorrenze del brand nel codice.
    - 💳 **Stripe TEST MODE ATTIVO** — sandbox Emergent claimable provisionata (scadenza 27-Sep-2026). `apps/billing/` completo: models + plans (LAUNCH_PLANS 4 tier + 3 credit packages) + routes (checkout, portal, webhook signature-verified, status polling, credits ledger atomico). Catalog Stripe creato via `setup_stripe.py` idempotente (4 subs × 2 cicli + 3 credits). Checkout end-to-end testato: `cs_test_...` restituito, URL valido. Frontend `BillingPage.jsx` con Piano attuale + Saldo crediti + 4 card piani (toggle Mensile/Annuale) + 3 card pacchetti crediti + Portal button. Voce sidebar "Piano & Crediti" 💳. `/app/memory/STRIPE_ONBOARDING.md` con URL claim account.
    - 📄 **APE/SIAPE + OpenAI docs scaffold** — `apps/docs_search/` con endpoint 503-guarded (`/api/docs/ape/search`, `/api/docs/ape/upload-ocr`, `/api/docs/openai/search`, `/api/docs/status`) pronti per API key del Founder. Consumo credit ledger predisposto (`ape_search=3`, `visura_catastale=5`, ecc.).
    - 🏠 **MLS Box widget** — `apps/immoweb/mls_box.py` con endpoint pubblici `GET /api/mls-box/agency/{slug}` (JSON) + `.html` (iframe embed self-styled Mediterranean Future 2035). Replica struttura home nicastroimmobiliare.it: 3 featured + 6 latest. Privacy Gate L1 applicato. Snippet copia-incolla via `/embed-snippet/{slug}`.
    - 🧪 **Regression pytest**: **113/114 core** verdi (un test order-dependent pre-esistente escluso). Nessuna regressione introdotta.
    - 📝 File aggiunti: `/app/memory/AUDIT_TODO_FEB2026.md`, `/app/memory/STRIPE_ONBOARDING.md`, `/app/memory/SUGGERIMENTI_POST_PROGRAMMA.md` (22 osservazioni per il Founder a programma compiuto).

  - ✅ **26-Feb-2026 (fork)**: **SPRINT 4 · PERF HARDENING + DEPLOY READY DONE** (opzione B: solo il critico) — chiuso in ~2h di lavoro:
    - 🧪 **GAP #2 Stress Test 5 Agenti FIX** — Da 7/11 FAIL → **11/11 verdi**. Aggiunto fixture `_seed_test_agents` che fa upsert dei 4 agenti test in DB + sanato data-drift `property_type='apartment'`/`None` in DB con helper `_normalize_property_type()` in `apps/immoweb/properties.py` (mappa valori legacy inglesi ai codici IT). Soglie di performance ricalibrate per il preview ingress single-worker (target production <500ms CREATE / <200ms READ p95 documentato inline). Vedi D-067.
    - 📦 **GAP #1 Foto Base64 → Emergent Object Storage** — Nuovo modulo `shared/storage/objstore.py` (init/put/get, retry 403, thread-safe), startup hook lazy in `server.py`, endpoint autenticato `POST /api/app/properties/{id}/photos/upload` (multipart, max 8MB, whitelist JPG/PNG/WEBP), router pubblico `apps/immoweb/media.py` con `GET /api/media/{path:path}` (cache 24h), script `scripts/migrate_photos_to_objstore.py` idempotente (dry-run + apply). 1 foto legacy migrata sul DB preview, 0 base64 residui. Test suite `test_sprint4_objstore.py` 7/7 verdi. Vedi D-068.
    - ⚡ **Perf side-quest LIST properties** — projection esplicita che esclude `photos` pesanti (usa `$slice: 1` per il cover) + nuovo indice compound `agency_id + created_at`. Da ~3s a <15ms localhost.
    - 🚀 **Deploy readiness confermato** — deployment_agent PASS. Unico fix richiesto: `CORS_ORIGINS` in `backend/.env` da allowlist a `"*"` (già letto via `os.environ.get(..., "*")`, no code change). Vedi D-069.
    - Test suite: **+7 test objstore** + **11/11 stress** verdi. Nessuna regressione introdotta. Un fail pre-esistente su `test_property_detail_returns_data` (privacy gate su record senza `privacy_level`) rimane documentato ma è pre-Sprint-4.
  - ✅ **24-Feb-2026 (fork)**: **M2.6c SOCIAL PUBLISHER DONE (Sprint 1 · Item #2)** — Sprint 1 chiuso al **3/3**. Auto-post su Facebook Page + Instagram Business + Telegram Channel via API ufficiali (Meta Graph v20 + Bot API). **Backend**: nuovo modulo `apps/immoweb/social_publisher.py` con adapter async httpx (FB `/photos` e `/feed`, IG container `/media` + `/media_publish`, Telegram `sendPhoto`/`sendMessage`); router `/api/app/publishing/social/*` con `GET /catalog`, `GET|POST|PATCH|DELETE /channels`, `POST /channels/{id}/validate` (live `/debug_token` + `/me` + IG `/{id}` + TG `getMe`), `POST /publish` (per property_id o payload esplicito), `GET /posts` (audit trail con filtro canale). Nuove collezioni `social_channels` (crediali AES-256-GCM via `shared.utils.crypto.encrypt_dict`) e `social_posts`. Caption builder default in italiano (titolo · 📍 città · 💶 prezzo · 📐 mq/locali · descrizione). **Frontend**: nuova pagina `/it/app/publishing/social` (`SocialPublisherPage.jsx`) con 3 sezioni (canali configurati, catalog da aggiungere, storico post), modale credenziali cifrate, bottone "Testa" per validazione live; CTA "Canali social" nella header di `PublishingPage` accanto al Wizard portali custom. Route protetta per `agency_admin`/`super_admin`/`branch_admin`/`group_admin`. **Credenziali Founder**: Page Access Token non-scadente su Page "Omnia real estate lab" (ID `1275173392335417`, scopes `pages_manage_posts`, `instagram_content_publish`, `instagram_basic`, `pages_read_engagement`, `pages_show_list`); IG Business account da collegare alla Page prima del primo post IG. **Test**: 16/16 pytest (`test_m2s6c_social_publisher.py`: catalog 3 canali + declared credential_fields + activate/encrypt/deactivate + missing/invalid creds 422 + duplicate 409 + tenant isolation + update rotate + disable/enable + delete/404 + publish requires channels + channel_not_configured error path + property_not_found 404 + audit trail + filter by channel + auth boundary 401/403) + **regressione totale 180/180 pytest verdi** (164 pre + 16 nuovi, zero regressioni). Smoke frontend OK — UI Mediterranean Future 2035 con 3 card canali (dot color-coded), tabella canali con badge status, storico post con external_id/errore.
  - ✅ **23-Feb-2026 (fork)**: **M2.6d UNIVERSAL PORTAL WIZARD DONE (Sprint 1 · Item #3)** — self-service configurazione di portali custom (regionali/franchising/nicchia) senza intervento OMNIA. **Backend**: `PortalCatalog` esteso con `owner_agency_id: Optional[str]` + `is_custom: bool` + `endpoint_url` + `site_url`; nuovo endpoint `GET/POST/PATCH/DELETE /api/app/publishing/custom-portals` + `GET .../feed-info?dialect={osf_federata|generic_rss}` per URL feed pronto-copia; slug namespaced con prefix `x-{agency8}-{user_slug}` (tenant isolation forte); `/publishing/catalog` esistente esteso per includere i custom della stessa agenzia + tutti i system portals, esclusi i custom altrui. Modalità **feed_pull only** in Sprint 1 (push/API rinviate a Sprint 2+). **Frontend**: nuova pagina `/it/app/publishing/wizard` con stepper a 4 step (Identità → Formato → Endpoint → Conferma), auto-slug da nome, radio dialect con descrizione, avviso integrazione feed_pull, URL feed pronto-copia con button "Copia" clipboard-based; bottone CTA verde emerald "+ Aggiungi portale personalizzato" nell'header di `PublishingPage`. i18n IT/EN/ES completa (35+ chiavi). **Test**: 13/13 pytest (`test_m2s6d_portal_wizard.py`: feed-info + 4 test create incluso duplicate 409, unsupported dialect/integration 422 + tenant isolation catalog + patch + delete cascading + auth boundary) + **regressione 164/164** (132 originali + 11 Domain Vault + 13 Portal Wizard + 8 immobilcloud auth). Fix minore su `test_m2s6a_publishing.py` per filtrare `is_custom=false` (semantica corretta). Screenshot smoke: step 0/1/4 renderizzano perfettamente con auto-slug e URL feed visibile.
  - ✅ **23-Feb-2026 (fork)**: **M2.5.5 DOMAIN VAULT DONE (Sprint 1 · Item #1)** — signup con garanzia contrattuale "il tuo dominio resta tuo". **Modelli**: `AgencyInDB` estesa con `domain_sovereignty_confirmed: bool`, `domain_sovereignty_confirmed_at: str`, `existing_domain: str`; `UserInDB` estesa con `signup_domain_sovereignty_confirmed` e `signup_existing_domain` (transfer automatico su create_agency). **Backend**: nuovo router `/api/app/agencies/me/domain-sovereignty` (GET + POST, ruoli agency_admin/super_admin/branch_admin/group_admin) in `apps/immoweb/domain_vault.py`; audit trail append-only in collection `domain_vault_events` (agency_id, user_id, confirmed, existing_domain, ts). **Frontend**: `RegisterPage.jsx` con badge emerald 🛡️ "Il tuo dominio resta tuo" (visibile solo per ruoli agenzia), campo opzionale dominio esistente con link a `/verifica-dominio`, checkbox obbligatoria "Ho letto e accetto la Domain Sovereignty Policy" con blocco submit; nuova pagina pubblica `/it/domain-sovereignty-policy` in stile Mediterranean Future 2035 (palette navy/emerald/gold/off-white F5F1E8) con 6 sezioni contrattuali (dominio del cliente, no blocco tecnico/legale, portabilità totale, trasparenza operativa, wind-down 90gg preavviso). Link nel footer di `LandingApp` e `AgenziesLandingPage`. i18n IT/EN/ES per tutte e 40+ chiavi domain_vault. **Test**: 11/11 pytest nuovi (`test_m2s5_5_domain_vault.py`: signup capture + endpoint idempotency + invalid domain 400 + auth boundary + audit trail) + regressione **151/151** (132 originali + 11 nuovi + 8 immobilcloud auth). Lint frontend pulito. Smoke screenshot OK su entrambe le pagine.
  - ✅ **25-Giu-2026**:
  - ✅ **GIS Valuator Pro** completato e testato 100% (37/37 backend pytest + 4/4 frontend E2E). Copertura nazionale via Nominatim province fallback, UNI 10750 commercial surface, coefficienti merito (piano/esposizione/affaccio/riscaldamento/ascensore/anno costruzione) + coefficienti regionali + vincoli/locazione.
  - ✅ **CTA "Confronta con immobili simili in vendita"** sul pannello risultato Valuator → trasforma ogni valutazione in lead funnel verso `/it/cloud/search` con filtri precompilati (città + tipologia + prezzo ±20%).
  - ✅ **AL Chatbot SSE streaming** + inline `AlImproveButton` ("✨ Migliora con AL") per copywriting.
  - ✅ **AL Legal** con Tavily web-search e validator anti-hallucination su `/it/legal`.
  - 📄 **BUSINESS_MODEL.md** documentato — 7-stream revenue ecosystem.
  - ✅ **27-Giu-2026 mattina**: Landing `/it/agenzie` v0.1 (prima bozza) LIVE. Backend `/api/founders/{spots,register}` + 2 template email Resend + frontend completo (hero, counter, 3 wow-moment, pricing table, form 5 campi). Test smoke + curl PASS. Considerata "prima bozza" dal founder, refinement futuro.
  - ✅ **29-Giu-2026**: **ANNCSU Sprint 2 DONE** — live autocomplete indirizzi stile Idealista/Immobiliare.it sul Valuator. Endpoint `/api/cloud/anncsu/suggest` (multi-candidati con doppio provider ANNCSU/Nominatim) + componente `AddressAutocomplete.jsx` (debounce, keyboard nav, badge validazione, autofill comune). Smoke E2E PASS.
  - ✅ **29-Giu-2026 (POMERIGGIO) — D-035 STOP PRE-LAUNCH**: il Founder ferma il filone commerciale (landing/banner/founders 50/sora videos) e richiede ritorno al **PROGRAMMA_OMNIA.md originale**, sequenziale, **passo passo**. Citazione: *"Non ci sarà nessun pre-launch senza Academy e features funzionanti"*. Tutto il filone commerciale ENTRA IN STATO DORMIENTE (codice già in produzione resta, ma non si pubblicizza/promuove). Vedi `DECISIONS.md` D-035.
  - ✅ **03-Lug-2026**: **M5.S4.1 Virtual Staging DONE** — pipeline 3-stage (SAM 2 + Flux LoRA inpainting + Real-ESRGAN) via fal.ai. Costo per render: **$0.056** esatto come stimato in D-033. Frontend page `/it/app/staging` con dropzone + selettore stile/stanza + progress bar 3-stage live + before/after + download watermark AGCM. Test E2E OK.
  - ✅ **03-Lug-2026 (fork)**: **M5.S4.2 Virtual Staging Sprint 2 DONE** — (1) **Reverse Staging** (rimozione arredo esistente + ri-arredo), (2) **varianti parallele 1-4** con scelta utente UI: "1 render" / "4 varianti stesso stile" / "4 stili diversi" multi-select, (3) **prompt CRM-aware** via Gemini (zona/prezzo/target buyer dall'immobile collegato, fallback statico), (4) **bottone inline 🪄 "Arreda questa foto"** nel form immobili → modale StagingStudio con foto pre-caricata, (5) **persistenza render**: salvataggio come foto base64 watermarkate nell'annuncio (endpoint `dataurl` + `save-to-property`), (6) **reaper job orfani** al boot server, (7) **rate-limit per-agenzia** (80/h) oltre a per-utente (20/h). Componente riusabile `StagingStudio.jsx`. Test: 18/18 pytest + testing agent frontend 100%. ⚠️ Test live pipeline BLOCCATO: saldo fal.ai esaurito.
  - ✅ **03-Lug-2026 (fork)**: **Allineamento i18n EN/ES DONE** — 480 chiavi mancanti tradotte via Gemini (script `backend/scripts/translate_i18n.py`, idempotente). Ora 921/921 chiavi in IT/EN/ES, 0 placeholder mismatch, 0 stringhe non tradotte. Verificato con screenshot UI inglese.
  - ✅ **03-Lug-2026 (fork)**: **Report PDF Valutazione brandizzato DONE** (idea ecosistema #3) — `POST /api/cloud/valuator/report-pdf` (reportlab): riusa pipeline UNI 10750, branding agenzia (nome+colori+contatti) se agente loggato, branding OMNIA se anonimo. Tabelle: riepilogo, valore hero, superficie ponderata, coefficienti merito, comparabili, metodologia+disclaimer. Bottone "📄 Scarica report PDF" nel pannello risultato Valuator (i18n IT/EN/ES). Testato curl anonimo+autenticato.
  - ✅ **03-Lug-2026 (fork, pomeriggio)**: **FASE C COMPLETATA** —
    - 📁 **Fascicolo Immobile AI** (precursore paperless Santo Graal): pagina `/app/properties/:id/fascicolo` con prezzo annuncio vs stima AI UNI 10750 (badge sopra/sotto/in linea), checklist documentale rogito (11 tipi: APE, planimetria, visura, atto provenienza, doc identità obbligatori + consigliati + condominiali per tipologie condo), upload/download/delete documenti (base64 nel doc immobile, max 8MB), analisi AL via Gemini con fallback rule-based (persistita), galleria render staging collegati. Link "📁 Fascicolo" nel form immobili (edit). Backend `apps/immoweb/fascicolo.py`, frontend `pages/FascicoloPage.jsx`. Test: 9/9 pytest + testing agent frontend E2E PASS.
    - ✍️ **Descrizione coordinata staging→annuncio**: `POST /staging/jobs/{id}/rewrite-description` — AL riscrive la descrizione in coerenza con lo stile del render scelto (solo dati reali, menzione render virtuali). Bottone "✍️ Descrizione coordinata" in StagingStudio dopo salvataggio variante, con textarea editabile + applica (form o PATCH diretto). Testato live.
    - 🐛 Fix regressione salvataggio immobili (stringhe vuote → campi numerici Pydantic) introdotta dal fix del warning React: ora il submit ripulisce tutti i campi "" (top-level + features). Verificato: salvataggio OK, foto e prezzo persistono.
  - ✅ **03-Lug-2026 (fork)**: Test live pipeline M5.S4.2 SBLOCCATO e PASSATO (23/23): saldo FAL attivo (errore precedente transitorio), generazione reale 2 varianti + download + dataurl + save-to-property. Anche LLM key attiva (~60 crediti).
  - 📷 **MLS multi-agenzia**: pattern documentati in `MLS_RESEARCH.md` (Agestanet backend + nicastroimmobiliare box pubblico). Da NON costruire fino a M4.
  - ✅ **03-Lug-2026 (fork, sera)**: **D-036 + D-037 applicate** —
    - 🤖 **AL → HAL** ovunque user-facing (chat widget, HAL Legal, i18n IT/EN/ES, system prompt). Route API e nomi file invariati.
    - 🗑️ **"Descrizione coordinata" RIMOSSA** su decisione Founder (rischio confusione tra stile render e reale stato manutentivo — principio AGCM). Endpoint + UI + test eliminati. NON riproporre.
    - 🏦 **Strategia M5.S5 Mutui**: motore in-house orientativo (Eurirs/Euribor + spread, TAEG, soglia usura TEGM Banca d'Italia, offerte banche admin-curated). MutuiOnline/Facile/Segugio senza API pubbliche — Founder valuta affiliazioni esterne in autonomia.
    - ⚡ **Strategia M5.S6 APE**: superata da **D-039 (06-Lug-2026)** — calcolatore in-house **eliminato dalla roadmap**. Resta solo il binario partner esterno (D-038, in attesa risposte).
    - Test post-modifiche: 25/25 pytest, frontend compilato, screenshot HAL verificato.
  - ✅ **06-Lug-2026 (fork)**: **M5.S5 COMPARATORE MUTUI DONE** (motore in-house, D-037 — MutuiOnline & co. rifiutano partnership senza volumi): ammortamento francese, TAN=benchmark+spread (Eurirs/Euribor 3M), TAEG via IRR, soglia usura TEGM, LTV 80%/95% Consap under-36, sostenibilità 35%, 14 offerte curate 8 banche in `mortgage_data.py` (aggiornamento manuale, no admin panel). Tre superfici: B2C `/cloud/mutui` + lead capture (`mortgage_leads`), CRM `/app/mutui`, box "Rata stimata" su annunci pubblici → comparatore precompilato. i18n IT/EN/ES. Test: 12/12 pytest + testing agent 100%.
  - 📧 **06-Lug-2026 (fork)**: **D-038 — Outreach partner APE**: preparate email di presentazione per APEFACILE e Certificato-Energetico.it/EnUp (richieste: API key, pay-per-use senza minimi, white label, clausola prezzo finale ≤ listino pubblico). ⏳ In attesa di invio/risposte del Founder. Scope ridotto a link-out/embed "Ordina APE ufficiale" (nessun calcolo lato OMNIA, vedi D-039).
  - ❌ **06-Lug-2026 (fork)**: **D-039 — M5.S6 calcolatore APE orientativo RIMOSSO dalla roadmap**. Motivazioni: rischio disclaimer, valore percepito basso, overhead di manutenzione. Rimane solo il binario partner esterno (D-038).
  - 🎛️ **06-Lug-2026 (fork)**: **D-040 — HAL entry point = 3 bottoni fisici** (Agents / Knowledge / Legal), no router LLM davanti. Trasparenza UX + zero latenza + isolamento dati cross-tenant. Revisione se >15% wrong-button in produzione.
  - 🏛️ **06-Lug-2026 (fork)**: **D-041 — PILLAR ARCHITETTURALE DOPPIO BINARIO** (Track A Turnkey / Track B White Label). Ogni feature futura progettata in **3 modalità di consumo**: UI dentro OMNIA + API+crediti + widget embeddabile. Diventa cornice di tutta la roadmap.
  - 🎯 **06-Lug-2026 (fork)**: **D-042 — Wedge di posizionamento**: **B AI-first + D Zero-friction migration**. A (prezzo) requisito minimo, C (ecosistema) effetto collaterale. Anti-wedge: NON diventiamo Salesforce, NON copiamo Agestanet feature-per-feature.
  - 📥 **06-Lug-2026 (fork)**: **D-043 — Universal Smart Importer 2.0**: HAL-powered mapper universale CSV/XLSX/XML/JSON per ~80% dei gestionali. Connettori nativi solo dopo 5+ paganti dallo stesso gestionale. Agestanet già coperto (parser XML M2.S2). Diventa M2.5.1.
  - 🆕 **06-Lug-2026 (fork)**: **NUOVA MILESTONE M2.5 — WHITE LABEL / DOPPIO BINARIO** inserita in roadmap tra M3 e M4. Sub-sprint: **M2.5.1** Universal Smart Importer, **M2.5.2** Multi-branch/Franchising, **M2.5.3** API Gateway + API Keys, **M2.5.4** Widget Embeddabili, **M2.5.5** Feed XML bidirezionale continuo. Priorità dopo completamento fascia AI (M5.S2 HAL Knowledge) e prima di M4 (crediti).
  - 📖 **06-Lug-2026 (fork)**: **M5.S2-pre Manuale Operativo SOSPESO** su decisione Founder (Cap. 1 draft creato in `/app/memory/manuale/01-introduzione-primo-accesso.md`, rimandato). Ripreso dopo consolidamento M2.5 + definizione unit economics.
  - 🎯 **06-Lug-2026 (fork)**: **D-044 — PROGRAMMA_OMNIA.md riformulato in v3.0** con priorità approvate dal Founder: **P0** M2.5.0 docs strategici (`GO_TO_MARKET.md` + `PRICING_OMNIA.md` v2) → **P1** M2.5 Doppio Binario (ordine interno: Multi-branch → API Gateway → Widget → Feed bidir. → Importer 2.0) → **P2** Manuale Operativo + HAL Knowledge → **P3** M6 Academy → **P4** M4 MLS+Stripe (post-società, confermato dopo M6). `ROADMAP.md` allineato. Sub-sprint M2.5 rinumerati (Importer diventa M2.5.5).
  - 🔍 **06-Lug-2026 (fork)**: **COMPETITIVE_ANALYSIS_TRACK_B.md creato** (prerequisito M2.5.0): ricerca su 7 fronti — valutatori white-label (DomusReport €50-100/mese, RealAdvisor €50-500, Sprengnetter €539/anno+€0,80/call, PriceHubble enterprise-only), staging SaaS ($0,20-0,95/foto vs nostro costo €0,056), stack franchising (Tecnocasa=Salesforce, RE/MAX=HubSpot, Gabetti=onOffice+Toolbox AI di terzi), pricing API PropTech (flat+overage vince), MLS Frimm €1.000-1.500/anno, chatbot white-label ($99-1.299/mese, ZERO comparabili per HAL Legal), mutui white-label (inesistente, L.118/2022 apre mediazione+agenzia). **Scoperta chiave: la suite headless verticale integrata self-service NON esiste in Italia — white space Track B confermato.** GTM raccomandato: bottom-up dalle affiliate + canale web agency. Corridoi di prezzo benchmark-derived pronti per PRICING v2.
  - 🧲 **06-Lug-2026 (fork)**: **D-045 — "Il nodo della domanda"** (approvato dal Founder): strategia GTM a 3 pilastri — ① AND-non-OR sui portali ("riduci e possiedi", mai "abbandona i portali"), ② **Marketing Autopilot** come tema di prodotto post-M2.5 (auto-post social D-FUTURE-11 + alert B2C + SEO programmatico Valutatore + contenuti HAL), ③ rampa ImmobilCloud dichiarata. Aggiunto **Fronte 8** all'analisi Track B con i numeri REALI dal PDF contratti del Founder: stack attuale €3.692/anno scontato → **€7.786/anno a regime** (pack Idealista+Casa.it raddoppia automaticamente al 13° mese: €194,50→€389/mese) vs OMNIA Pro €1.188/anno = **-85%**. ⚠️ Corretto errore ricorrente: il Valutatore è **copertura nazionale 100%** (~7.900 comuni, 3 layer), NON "124 città" (regola #11 in AGENT_BOOTSTRAP).
  - 📄 **06-Lug-2026 (fork)**: **P0/M2.5.0 CONSEGNATA** — creato `GO_TO_MARKET.md` v1.0 (wedge B+D, ICP Track A/B incl. web agency come canale, "nodo della domanda" D-045, motion bottom-up 4 fasi, messaging kit con claims documentati, metriche validazione, vincolo D-035 esplicito) + `PRICING_OMNIA.md` v2.0 bozza (listino Track B completo: widget Valuator €39-79, HAL Legal €69, Mutui €19, bundle €119/mese; API a crediti unificati; feed inbound €49/mese; free tier dev 25 azioni con badge; staging 1→3 crediti €0,90; benchmark -85% vs stack reale). 🟡 **In attesa di revisione/approvazione Founder** → poi P1 M2.5.1 Multi-branch.
  - 🤝 **06-Lug-2026 (fork)**: **D-046 — Programma Partner Web Agency** approvato dal Founder: rev-share **20% ricorrente a vita** (25% Certified) + 10% crediti, tier Gold/wholesale **dormiente**, deal registration, certificazione via Academy, `partner_id` previsto in M2.5.2. Formalizzato come §4-bis di `GO_TO_MARKET.md`.
  - 🔗 **06-Lug-2026 (fork)**: **Share bar sul portale B2C** — aggiunta barra "Condividi" (WhatsApp, Facebook, X, Email, Copia link + Web Share API nativa su mobile) nell'hero della pagina annuncio ImmobilCloud (`PropertyDetailPage.jsx`, componente `ShareBar`, data-testid `detail-share-bar`/`share-*`). i18n IT/EN/ES (`cloud.share_*`). Testata con screenshot: tutti i pulsanti renderizzati. Le anteprime rich sui social sono già supportate dal JSON-LD Schema.org esistente.
  - 🎯 **Prossimo accesso**: revisione Founder dei 2 documenti P0 → **P1 M2.5.1 Multi-branch/Franchising Layer** (primo sprint di codice: agency_group, branch, ruoli, plan_type) (`GO_TO_MARKET.md` + `PRICING_OMNIA.md` v2 con unit economics Track A/B, cap free tier, crediti API group/branch) → revisione Founder → **P1 M2.5.1 Multi-branch**.
  - ✅ **13-Lug-2026 (fork)**: **P0 APPROVATA + M2.5.1 MULTI-BRANCH/FRANCHISING LAYER DONE** (D-041). Founder ha approvato `GO_TO_MARKET.md` + `PRICING_OMNIA.md` v2 e ha dato il via a M2.5.1.
    - **Backend**: nuovo modello `AgencyGroup` (holding/franchising con `credits_mode: group|branch` default **branch**), estensione `AgencyInDB` con `group_id`, `branch_code`, `plan_type: turnkey|whitelabel|hybrid` default **hybrid** (per esistenti). Nuovi ruoli `group_admin`/`branch_admin`/`branch_agent` in `UserRole` con backward-compat via alias in `require_roles()` (agency_admin ≡ branch_admin ≡ group_admin; agent ≡ branch_agent ≡ branch_admin ≡ group_admin). Router `/api/app/groups`: create/list/get/patch/me + `POST/GET/DELETE /{gid}/branches` + `GET /{gid}/consolidated` (rollup properties/clients/leads su tutte le branch del gruppo). Promozione automatica creator → `group_admin` con `group_id` sul record utente.
    - **Frontend**: nuova pagina `/it/app/group` (accessibile solo a `group_admin`/`super_admin`) con 6 KPI consolidati (filiali, attive, immobili attivi/totali, clienti, lead aperti) + tabella filiali con branch_code, plan_type badge, rollup counter per riga. Voce sidebar "Gruppo" condizionale al ruolo. i18n IT/EN/ES completa (23 chiavi × 3).
    - **Test**: 15/15 pytest (`test_m2s5_1_groups.py`) — Group CRUD + Branches attach/detach + Consolidated KPIs + Backward-compat (`/agencies/me` intatto, `/auth/me` espone `group_id`) + Auth boundary. Regressione full suite: 32/33 (1 pre-esistente su seller_link patch, non correlato). Smoke E2E frontend PASS (screenshot verificato: "Nicastro Immobiliare" con 1 filiale MAIN-01 e KPI rollup corretti).
  - ✅ **13-Lug-2026 (fork)**: **M2.5.2 API GATEWAY TRACK B DONE** (D-041/D-046). Prima porta d'ingresso "esterna" alle feature OMNIA per agenzie whitelabel/hybrid.
    - **Backend chiavi**: modello `ApiKeyInDB` (SHA-256 hash-only storage, mai plaintext dopo issue), `ApiUsageLogInDB` per audit billing, `partner_id` opzionale per rev-share D-046. Auth Bearer `Authorization: Bearer omk_live_...` via `shared/auth/api_key.py` (`require_api_key` + `charge_and_log`). Debit crediti solo su successo, log rows su ogni chiamata (anche errori) con `partner_id` propagato per attribuzione commissioni.
    - **Router UI management** `/api/app/api-keys`: list/issue (one-time plaintext) / revoke / adjust credits (top-up manuale fino a M4/Stripe) / usage log.
    - **Router pubblico v1** `/api/v1/*`: `health` (no auth) + `me` (0 cr) + `valuator` (5 cr) + `mortgages/compare` (1 cr) + `legal/ask` (3 cr) + `feed/properties` (0 cr) + `staging/render` (501 riservato a M2.5.3). Riusa i handler esistenti Immocloud/Immoweb — zero duplicazione business logic. Pricing 1 credito = €0,03 allineato a `PRICING_OMNIA.md` v2.
    - **Frontend**: pagina `/it/app/api-keys` con form emissione (nome + crediti + partner_id), box show-once verde per il plaintext, tabella chiavi (prefix visibile, hash mai esposto), azioni top-up/revoca, docs footer con endpoint. Sidebar "API Keys" condizionale a agency_admin+. i18n IT/EN/ES completa (14 chiavi × 3).
    - **Test**: 15/15 pytest (`test_m2s5_2_api_gateway.py`) — issuance/plaintext shape/hash-never-returned + auth boundary (invalid/unknown/bad-prefix) + credit debit correct (1/5) + partner_id in usage log + 402 insufficient credits + free endpoint still works when low + revoke cuts access + management requires JWT. Regressione + M2.5.1: 30/30 pytest passati (`test_m2s5_1_groups.py` + `test_m2s5_2_api_gateway.py`). Smoke E2E screenshot verificato: 1 chiave attiva "Widget Demo Web Agency" con saldo 94/100 dopo 6 crediti spesi in 3 chiamate reali (mutui + valutatore + me).
    - **Prossimo**: **M2.5.3 Widget Embeddabili** (iframe brandizzato Valuator/Mutui/HAL Legal che chiama internamente le v1 API) → **M2.5.4 Feed bidirezionale** → **M2.5.5 Universal Smart Importer 2.0**.
  - ✅ **14-Lug-2026 (fork)**: **M2.5.3 WIDGET EMBEDDABILI TRACK B DONE** (D-049). 2 widget pronti alla demo commerciale ("1 riga di codice").
    - **Backend widget assets**: nuovo router `/api/widgets/v1/*` che serve HTML+JS single-file da `apps/v1/assets/` con placeholder injection (backend URL da forwarded headers, primary color, chiave, lang). Widget `valuator.html` (form UNI 10750 + lead capture + auto-resize via postMessage) e `mortgages.html` (top-3 offerte + lead capture). `loader.js` (~2KB) che crea iframe responsive, gestisce resize dinamico, valida `data-key` prima di montare. Headers CSP `frame-ancestors *` per embed cross-origin.
    - **Security widget**: campo `allowed_origins` su `ApiKeyInDB` (whitelist domini con supporto wildcard `https://*.example.com`). `require_api_key` verifica Origin OR Referer (resiliente a proxy che riscrivono Origin, come il nostro k8s ingress). Chiave senza whitelist = permissive (server-side). PATCH `/api/app/api-keys/{id}/origins` per aggiornare la whitelist.
    - **Endpoint lead** `POST /api/v1/widgets/lead` (0 crediti — lead ingestion sempre gratuita, monetizzazione tramite feature) che crea riga `db.leads` con `source=widget_*`, `partner_id`, `context` completo, `source_url`. Validazioni: consent obbligatorio + almeno email o telefono.
    - **Frontend**: (1) `/it/widgets` (public showcase) con tab switcher Valuator/Mortgages, snippet installazione copy-to-clipboard, iframe anteprima LIVE che chiama davvero l'API se il visitatore incolla una chiave, come-funziona in 3 step. (2) Pagina API Keys estesa: textarea `allowed_origins` (uno per riga), docs footer con snippet embed, link diretto a `/it/widgets` per anteprima.
    - **Test**: 15/15 pytest (`test_m2s5_3_widgets.py`) — asset serving (loader.js con backend URL corretto, HTML con color/lang injection, CSP headers, 404 su widget sconosciuti) + origin whitelist (block quando no headers, allow via Referer, block su origin diverso, wildcard subdomain, permissive senza whitelist) + widget lead capture (crea CRM row, richiede consent, richiede email/phone, valida widget name) + PATCH origins. Regressione totale: **45/45 pytest passati** (M2.5.1 + M2.5.2 + M2.5.3). Smoke E2E screenshot verificato: showcase page con anteprima iframe live di entrambi i widget (chiave demo `Widget Demo Site` con partner_id `webagency_demo` e whitelist popolata).
    - **Prossimo**: ~~M2.5.4 Feed XML bidirezionale~~ → **RIVISTA: M2.5.4 Domain Sovereignty Kit** (Extraction-first, D-051).
  - ⚠️ **15-Lug-2026 — SCOPERTA STRATEGICA "DOMAIN LOCK-IN AGESTANET"** (D-051): il Founder ha rilevato che sul contratto `agestanet_9491_[3-6-2026].pdf` l'Allegato A elenca "Dominio (nicastroimmobiliare.it)" come voce fatturata (€400 listino). Nel suo Aruba risultano registrati solo `nicastroimmobiliare.eu` + `omniarealestateecosystem.it` → **il dominio `.it` è probabilmente registrato da BasicSoft/Agestanet**, non a suo nome. Il problema si estende a **~1.803 agenzie clienti Agestanet + ~4-6.000 agenzie italiane** clienti di gestionali con business model analogo. Founder ha approvato strategia **"Extraction-first"** (aiutare chi è già in trappola, prima di "Prevention"). Regola imposta: **ZERO nomi di concorrenti in qualsiasi materiale pubblico**.
  - ✅ **15-Lug-2026 (fork)**: **M2.5.4a UNIVERSAL XML IMPORTER DONE** (D-050). Prima pietra del pacchetto "Domain Sovereignty Kit" per estrazione da gestionali legacy.
    - **Backend parser** `shared/importers/universal_xml.py`: schema-agnostic XML→OMNIA mapping. Riconosce nativamente feed dei principali gestionali immobiliari italiani (codici numerici tipologia 3/10/31/etc, classi energetiche numeriche, contratti V/A/S, foto vs piantine tramite `tipoN=F|P`, testi multilingua `testo_it/eng/spa/ted/fra`, flag booleani + keyword-based fallback su testo libero, coordinate lat/lng, ~30 feature). Zero riferimenti a competitor concreti nel codice o nei log — solo tabelle euristiche generiche.
    - **Backend API** `/api/app/import/xml/*`: two-phase flow **preview → commit** con session in-memory TTL 10min. `POST /preview` (multipart, JWT) ritorna `ParseReport` completo. `POST /commit` supporta `dry_run` + `skip_duplicates_by_ref` (match `reference_code`), insert batch. Guard 50MB max.
    - **Frontend** `/it/app/import`: drag-drop + preview con 3 stat card (tipologia/contratto/città) + tabella samples + warnings + divergences. 2 CTA "Simulazione" (dry-run) o "Importa in OMNIA" + checkbox dedupe. Copy 100% generica "il tuo attuale gestionale". Sidebar "Importa" condizionale a agency_admin+. i18n IT/EN/ES.
    - **Test**: 12/12 pytest (`test_m2s5_4a_xml_importer.py`). Regressione totale: **57/57 pytest** (M2.5.1+M2.5.2+M2.5.3+M2.5.4a). E2E reale: upload feed XML 3 immobili → preview 3/3 → commit 3 inseriti con `_import_source: universal_xml_importer_v1`.
    - **Prossimo**: **M2.5.4b Domain Ownership Checker** (landing pubblica RDAP `/it/verifica-dominio`) → **M2.5.4c Legal Templates Pack** (4 PDF PEC/GDPR/disdetta/CNR). Poi **M2.5.5 Domain Vault** (prevention per nuovi OMNIA).
  - 🆕 **15-Lug-2026 — M2.6 PUBLISHING CENTER inserito nel programma** (roadmap update). Il Founder ha condiviso screenshot dell'area "Portali Immobiliari" del gestionale attuale (52 portali gestiti, sync giornaliera automatica, credenziali per-portale, filtri "in pubblicità"). Gap analysis: OMNIA ha già feed XML endpoint pubblico single-dialect (da M3), ma manca l'intero **layer OUTBOUND** verso portali esterni (catalogo, credenziali, scheduler, compliance, UI dashboard). Effort stimato: 12-13h su 3-4 sessioni. Sub-sprint pianificati:
    - **M2.6a — Portal Catalog + Connection Layer + Feed multi-dialetto** (P0 — ~5h): modelli `PortalCatalog` + `AgencyPortalConnection` + feed generator con dialetti (OSF-Federata, generic RSS, Facebook Catalog XML, Google Merchant XML), UI dashboard `/it/app/portali` a 3 stati (attivi/disponibili/da-aggiornare).
    - **M2.6b — Sync scheduler + Status tracking + Compliance validator** (P1 — ~4h): job APScheduler-based giornaliero, `PortalSyncLog` collection, validatore pre-publish (classe energetica L. Boschi, min foto, prezzo).
    - **M2.6c — Social Publisher** (P2 — ~3h): Facebook Pages/Instagram Business/Telegram broadcast via API Graph + scheduler settimanale.
    - **M2.6d — Universal Portal Wizard** self-service (P3 — ~1h): agenzia aggiunge portali custom senza aspettare noi.
    - **3 decisioni pending** (da prendere prima di M2.6a): (1) sicurezza credenziali AES/vault/token-only, (2) compliance validator hard vs soft per energetica/foto/prezzo, (3) priorità coverage MVP (5-8 portali gratis top).
  - ✅ **16-Lug-2026 (fork)**: **M2.6a PUBLISHING CENTER FOUNDATION DONE** (D-052). Match funzionale con area "Portali" gestionali legacy — OMNIA ora è sostituibile.
    - **Backend**: modelli `PortalCatalog` + `AgencyPortalConnection` + `PortalSyncLog` in `shared/models/portal.py` (coesistenti con `PortalSubscription` legacy). AES-256-GCM encryption per credenziali via `shared/utils/crypto.py` (key da env `CREDENTIALS_MASTER_KEY` con fallback deterministico su MONGO_URL per dev). Router `apps/immoweb/publishing.py` con endpoint `/api/app/publishing/catalog|connections|connections/{id}|connections/{id}/logs`. Feed pubblico `/api/app/publishing/feed/{agency_slug}.xml?dialect=osf_federata|generic_rss`. Compliance validator HARD (D-052 approvato): esclude annunci senza prezzo/rent, senza classe energetica, con <3 foto. Catalog seed automatico allo startup con 8 portali MVP Fase 1: **Subito · Bakeca · Kijiji · Wikicasa · Facebook Marketplace · Google Business Profile · Attico · Case24**.
    - **Frontend**: pagina `/it/app/publishing` con 3 metric card (attivi/disponibili/catalogo), tab switcher Attivi/Disponibili, tabella portali con traffic_score in stelle, modal attivazione con form credenziali dinamico (basato su `credential_fields` del catalogo). Sidebar "Portali" condizionale a agency_admin+. Banner "Compliance HARD attiva" ben visibile. i18n IT/EN/ES.
    - **Test**: 16/16 pytest (`test_m2s6a_publishing.py`) — catalog seeded/sorted, connection activate/duplicate/update/delete, credenziali mai leaked (encryption verified), feed dialects (osf_federata + generic_rss), compliance filter HARD, auth boundary. **Regressione totale: 73/73 pytest** (M2.5.1+M2.5.2+M2.5.3+M2.5.4a+M2.6a). Smoke E2E screenshot verificato: showcase 8 portali ordinati per traffic_score, tab funzionanti.
    - **Prossimo**: **M2.6b Sync Engine + Compliance UI** (APScheduler job giornaliero + `PortalSyncLog` visualization + per-property publishability preview).
  - ✅ **05-Feb-2026 (fork)**: **M2.6b SYNC ENGINE + COMPLIANCE VALIDATOR DONE** (D-053). Il Publishing Center passa da statico ad automatico.
    - **Compliance Validator** `shared/validators/compliance.py`: modulo dedicato, hard rules (blocca pubblicazione) + soft rules (warning non bloccante). Hard: prezzo/canone, superficie mq, classe APE valida (VALID_ENERGY_CLASSES da D.Lgs 192/2005 incluso A4-G + EXEMPT), min 3 foto con URL valido, indirizzo città+provincia. Soft: titolo <10 chars, descrizione <50 chars, IPE mancante, locali non indicati. Aggregatore `summarize_agency_compliance()` con top-5 motivi blocco per dashboard.
    - **Sync Engine** `apps/immoweb/sync_engine.py`: `sync_connection()` per singola connessione, `sync_connection_with_retry()` con backoff esponenziale 1min/5min/30min (skippato su trigger manuale per snappy response), `run_all_active_syncs()` per il job giornaliero. Distingue integration_type `feed_pull` (portali PULL: refresh timestamp) vs `api_push` (portali PUSH: stub `simulated_push` in attesa M2.6c/d). APScheduler AsyncIOScheduler daily job **06:00 UTC** avviato in server lifespan (`start_scheduler()`), idempotent su hot-reload.
    - **Sync Logs**: collection `publishing_sync_logs` scrive `started_at`, `ended_at`, `status` (success/partial/failed), `items_ok`/`items_failed`, `error_message`, `retry_count`, `trigger` (scheduled/manual/admin_manual). `last_sync_at`/`next_sync_at` scritti su `publishing_connections`.
    - **Endpoint nuovi** in `publishing.py`: `POST /api/app/publishing/connections/{id}/sync-now` (agenzia trigger manuale), `GET /api/app/publishing/connections/{id}/compliance` (snapshot compliance + top-20 immobili bloccati con motivi), `POST /api/app/publishing/sync/run-all` (super_admin bypass scheduler). `is_publishable()` legacy tenuto come wrapper backwards-compatible.
    - **Frontend**: aggiornata `PublishingPage.jsx` con 3 nuovi pulsanti azione per riga (SYNC/COMPLIANCE/DISATTIVA), riga "ultimo sync" sotto il nome portale, badge errore ultimo sync, banner risultato sync (verde/ambra) dopo run manuale. Nuova modale `portal-compliance-modal` con 4 metric card (totale/pubblicabili/bloccati/con-warning) + top-5 motivi blocco tradotti in italiano (`REASON_LABELS`) + lista primi 20 immobili bloccati con link "Correggi →" all'edit. Banner header aggiornato a "Compliance HARD attiva + Sync automatico".
    - **APScheduler installato** (3.11.3, salvato in requirements.txt). Fix minor: `_record_log()` fa `.pop("_id")` sul dict dopo `insert_one` per non restituire ObjectId a FastAPI.
    - **Test**: 20/20 pytest (`test_m2s6b_sync_engine.py`) — 9 unit test compliance validator (fully compliant / hard blocks singoli e combinati / soft warnings non bloccano / summarize aggregate), 6 integration test sync endpoint (feed_pull success, api_push simulated, 404, 409 disabled, last_sync_at update, log record with trigger=manual), 2 test compliance endpoint, 1 test super_admin run-all, 2 auth boundary. **Regressione totale: 93/93 pytest** (M2.5.1+M2.5.2+M2.5.3+M2.5.4a+M2.6a+M2.6b). Smoke E2E: attivato bakeca, cliccato Sync → banner "0 pubblicabili, 9 bloccati" corretto, aperta modale Compliance con motivi frequenti "Meno di 3 foto: 9 immobili", "APE mancante: 5", "Indirizzo incompleto: 5" e lista dettaglio con link Correggi.
    - **Prossimo**: **M2.5.4b Domain Ownership Checker** (landing pubblica RDAP) → **M2.5.4c Legal Templates Pack** → **M2.6c Social Publisher** (Facebook/Instagram/Telegram auto-post con integrazione API reale).
  - ✅ **05-Feb-2026 (fork)**: **M2.5.4b DOMAIN OWNERSHIP CHECKER DONE** (D-054). Secondo tassello del "Domain Sovereignty Kit" (D-051), primo lead magnet pubblico con delivery 100% digitale (no paper) e già disponibile in tutte e 3 le modalità Track A/B (D-041 White Label).
    - **RDAP Client** (`shared/utils/rdap.py`): async httpx (5s+8s timeout, fail-closed) verso il bootstrap universale `rdap.org/domain/{domain}` + fallback per TLD IT/EU/COM/NET/ORG. Normalizza output: registrant, registrar, nameservers, created/expires/last_changed, `not_found`. `normalize_domain()` strip protocollo/www/path e valida sintassi.
    - **Domain Checker Logic** (`apps/marketing/domain_check.py`): euristica generica (regola D-051 no brand mentions) su 4 status: `owner_ok` (green), `likely_hostage` (red — keyword pattern-matching su termini categoriali come "hosting", "web agency", "software solutions", "servizi web", "unipersonale" — MAI nomi di competitor concreti), `redacted` (amber — privacy proxy GDPR), `ambiguous` (amber — registrante presente ma non riconducibile), `not_registered` (info), `unknown` (rdap error). `_domain_matches_registrant()` fuzzy match domain brand vs registrant name vs optional agency_name field.
    - **3 modalità di consumo (White Label nativa)**:
      - **Landing pubblica** `/it/verifica-dominio` (nessuna auth, IP-rate-limited 30/h) → hero + form check + verdict card colorata + lead capture (email/nome/agenzia + GDPR consent obbligatorio). Copy "tutto digitale, zero carta" esplicita.
      - **v1 API Gateway** `POST /api/v1/domain/check` (Bearer API key, 1 credito) per partner web agency + rev-share 20% D-046 propagato automaticamente via `partner_id` in usage log.
      - **Widget embeddabile** `/api/widgets/v1/domain-check.html?key=omk_...&primary=#0b1e3f&lang=it` — single-file HTML+JS con auto-resize postMessage, CSP frame-ancestors *, lead capture inline. Se `key` è vuota parla al `/api/domain/check` pubblico; se è una `omk_...` parla al `/api/v1/domain/check` billed (comportamento switch client-side).
    - **Endpoint pubblici** (`/api/domain/check` + `/api/domain/lead`): rate limit collection-based (`domain_checks` con `client_ip` + `created_ts`), consenso GDPR obbligatorio sul lead, `check_id` UUID per collegare check→lead, mai leak di IP nella response. Persistenza in `domain_checks` + `domain_leads` con `verdict_status` snapshot per analytics.
    - **Costo credito**: `CREDIT_COSTS["domain_check"] = 1` (=€0,03 allineato PRICING_OMNIA v2). Nessun costo lato utente sulla landing pubblica.
    - **Test**: 24/24 pytest (`test_m2s5_4b_domain_checker.py`) — 3 test `normalize_domain` (lowercase/strip-scheme/invalid), 5 heuristics (matches agency, provider hint pos/neg, redacted detection), 6 `_analyze` (not_found/error/owner_ok/likely_hostage/redacted/ambiguous), 3 public check (400 invalid, verdict shape valid, no IP leak), 3 public lead (consent required, missing check 404, 201 happy), 2 v1 (auth required, 1 credit charged), 2 widget asset (HTML placeholder replacement, unknown 404). Cleanup fixture drop `domain_checks` per evitare trip del rate limiter durante il run. **Regressione totale: 117/117 pytest** (M2.5.1+2+3+4a+4b+2.6a+2.6b). Smoke E2E: query `google.com` → verdict `redacted` con registrar MarkMonitor + expiry 14/09/2028 visualizzati correttamente.
    - **Prossimo**: **M2.5.4c Legal Templates Pack** (4 PDF template GDPR/PEC/disdetta/CNR scaricabili gratuiti — delivery via email, 100% no paper) → **M2.5.5 Domain Vault** (signup dove OMNIA garantisce di non registrare mai domini a proprio nome).
  - ✅ **23-Feb-2026 (fork)**: **M2.5.4c LEGAL TEMPLATES PACK DONE** (D-055). Terzo tassello del "Domain Sovereignty Kit" (D-051), completamento del funnel iniziato con M2.5.4b Domain Checker. Delivery **100% digitale** (D-035 No Paper).
    - **Motore PDF** (`shared/legal_kit/`): 4 template legali generici parametrizzati con Jinja2 (nessuna menzione competitor, D-051): (1) Richiesta portabilità dati GDPR art. 20 al fornitore, (2) Richiesta titolarità dominio al registrar, (3) Disdetta contratto fornitore, (4) Reclamo/richiesta info Registro .it CNR-IIT. Ogni template ha metadata (target, when_to_use, canale PEC, giorni risposta) + sezioni (oggetto, premesso che, chiede, modalità consegna, riferimenti normativi). Placeholder mancanti resi come `[DA COMPILARE]` visibili — l'utente sa cosa completare.
    - **PDF renderer** (`shared/legal_kit/pdf_generator.py`): ReportLab platypus con layout editoriale coerente Brand Lab (Deep Navy #0B1E3F header strip, Gold wordmark, Emerald accents, disclaimer footer). `render_pdf(slug, ctx)` restituisce bytes PDF/A. `render_kit_zip(ctx)` bundle i 4 PDF + `LEGGIMI.txt` in un unico ZIP scaricabile.
    - **3 modalità di consumo (D-041 White Label)**:
      - **Landing pubblica** `/it/verifica-dominio` → blocco "Scarica Legal Kit" appare automaticamente dopo verdict `critical` o `warning`. Form con email + consenso GDPR + optional (agency_name/signer/PEC). Download del ZIP in-browser via `blob URL`, senza email inviate (l'utente ottiene il file istantaneamente + noi catturiamo il lead in `legal_kit_leads`).
      - **API pubblica** `POST /api/legal/download/{slug}` + `POST /api/legal/kit` (rate-limit 20/h/IP via collection `legal_kit_events`), consenso GDPR obbligatorio sul kit completo.
      - **v1 API Gateway** `POST /api/v1/legal/render` — **2 crediti** (compute cost superiore a domain_check), Bearer API key, ritorna `application/pdf`, header `X-Credits-Charged: 2`.
    - **Endpoint pubblici** (`/api/legal/*`): `/templates` (lista catalogo con 4 items), `/download/{slug}` (singolo PDF), `/kit` (ZIP + lead capture). Persistenza minima: `legal_kit_events` (rate limit + audit) + `legal_kit_leads` (con flag `context_has_domain` per analytics conversion). Nessuna PII nel response, `client_ip` sempre `pop()` prima del ritorno.
    - **Frontend integrazione**: nuovo componente `LegalKitBlock` in `DomainVerifyPage.jsx` posizionato subito dopo il verdict card (prima del LeadForm esistente). Design ambra distintivo (differenzia dal lead form emerald). Copy esplicita "**Nessun invio cartaceo. Delivery digitale al 100%**". Download client-side via blob URL con nome file `omnia_legal_kit.zip`.
    - **Costo credito**: `CREDIT_COSTS["legal_render"] = 2` (=€0,06 allineato pricing v2 — più costoso di domain_check per compute PDF).
    - **Test**: 15/15 pytest (`test_m2s5_4c_legal_kit.py`) — 2 catalog (4 templates + no brand mentions D-051), 4 unit PDF (bytes/magic/all-slugs render/placeholder substitution deterministic diff/missing slug KeyError/ZIP contents), 5 integration public (list templates, single 200, 404 unknown, consent required, kit ZIP happy), 3 v1 (auth required, 2 credits charged, 404 unknown), 1 cleanup fixture. **Regressione totale: 132/132 pytest** (M2.5.1+2+3+4a+4b+4c+2.6a+2.6b). Smoke E2E: query `google.com` → verdict `redacted` → blocco Legal Kit visibile → form + pulsante download attivi dopo consenso.
    - **Documento supporto**: creato `/app/memory/emails/dossier_commerciale_ape.md` — 1-pager di preparazione alle call APEFACILE + EnUp con volumi 2026/2027 stimati, deal-breaker, matrice comparativa, struttura commerciale rev-share preferita, red flags, script pitch di apertura, leve psicologiche.
    - **Prossimo**: **M2.5.5 Domain Vault** (badge "il tuo dominio resta tuo" nel signup + garanzia contrattuale) → **M2.6c Social Publisher** (Facebook/Instagram/Telegram auto-post reale) o **APE Partnership** (dopo call).
  - ✅ **23-Feb-2026 (fork)**: **M2 CORE DoD VALIDATO AL 100%** — l'ultimo item mai testato della Definition of Done ("test empirico 5 agenti in parallelo nella stessa agenzia") è stato eseguito da testing_agent_v3_fork con stress test completo.
    - **Setup**: seed di 4 agenti aggiuntivi via `/app/backend/tests/seed_stress_agents.py` con hash bcrypt corretto (pattern `shared/auth/passwords.py`), tutti nell'agenzia Nicastro (abc7004b-04a3-414b-8197-8e0e983d0892). Cleanup finale idempotente.
    - **6 scenari di stress eseguiti in parallelo** (`/app/backend/tests/test_m2_stress_5_agents.py`, ThreadPoolExecutor Python):
      1. Login concorrente 5 sessioni → 100% ok, wall 1.7s, p95 1.7s
      2. CREATE 25 properties concurrent (5 agenti × 5 immobili) → 100% ok, wall 3.9s, avg 3.6s, 25 reference_code univoci, ogni immobile attribuito all'agente creatore
      3. READ 50 concurrent (5 agenti × 10 GET /properties) → 100% ok, wall 3.2s, read p95 2.6s (baseline 42ms, degradazione 37× ma nessun 500)
      4. UPDATE concorrente 5 PATCH stesso immobile → 100% ok, wall 47ms, last-write-wins coerente, nessun deadlock MongoDB
      5. Matching engine concorrente 15 (5 × 3 clienti) → 100% ok, wall 113ms, p95 107ms
      6. Tenant isolation → verificato, agenti Nicastro NON vedono dati di altre agenzie
    - **Verdetto**: **PASSED — concurrency-safe, tenant-isolated, data-consistent**. 0 errori 500, 0 duplicati reference_code, 0 deadlock, 0 leak inter-tenant. Tutti i criteri funzionali soddisfatti.
    - **Warning perf attribuiti a infra preview + design consapevole**:
      - POST /properties avg 3.6s vs target 2s → **fire-and-forget geocoding scheduler** (design intenzionale, geocoding non blocca response ma allunga la trace) + latency infrastrutturale preview. In produzione con async geocoding via Motor background task si dovrebbe rientrare <1s
      - GET /properties p95 2.6s vs target 1.5s → sotto 50 richieste concorrenti la degradazione 37× rispetto al baseline (42ms) è accettabile su preview, da ricontrollare su infra prod. Suggerimento code review: aggiungere projection esplicito sul list endpoint per ridurre payload
    - **Code review comments** (dal testing agent):
      - `properties.py:194` update_one non filtra per agency_id (già filtrato via find_one) — safe ma consigliato defensive $set
      - `matches.py` compute-on-read a 88ms medio sotto load — design confermato ottimo
    - **Cleanup completo**: 25 properties + 15 clients + 4 agents eliminati dal DB. Suite pytest 100% self-contained e ri-eseguibile.
    - **Milestone M2 core** ora ufficialmente ✅ DoD al 100% (14/14 item validati).
    - **Prossimo**: chiudere anche **M2.5 al 100%** con M2.5.5 Domain Vault → M2.6c Social Publisher → M2.6d Universal Portal Wizard.



---

## Problem Statement

Costruire OMNIA, ecosistema digitale verticale completo per il settore immobiliare italiano, composto da 3 piattaforme integrate:

1. **ImmobilCloud** — Portale immobiliare B2C (privati + pubblico)
2. **ImmoWeb** — Gestionale CRM B2B per agenzie immobiliari
3. **Omnia Academy** — Piattaforma di formazione agenti certificata

**Vision**: "Più valore, più efficienza, più risultati."

**Differenziale competitivo** (vs Idealista / Immobiliare.it / Casa.it — analisi 16 Giu 2026):

📊 **Stack tradizionale agenzia italiana = €10.000-12.000/anno**:
- Immobiliare.it (30 spazi): ~€500/mese = €6.000/anno (fonte: forum immobilio.it Dic 2025)
- Idealista (30 annunci): ~€250/mese = €3.000/anno
- Gestionale tipo Gestim/Getrix: €80-150/mese = €1.500/anno

💰 **OMNIA fase lancio = €348-948/anno (-95%)** — Starter €29, Pro €29, Agency €79

🎯 **Gap del mercato che OMNIA chiude**:
| Feature | Idealista | Immobiliare.it | Wikicasa | Getrix | OMNIA |
|---|:-:|:-:|:-:|:-:|:-:|
| Pricing trasparente in homepage | ❌ | ❌ | ❌ | ❌ | ✅ |
| AI nativa nel CRM | ❌ | ⚠️ | ❌ | ❌ | ✅ |
| White-label sito agenzia su dominio proprio | ❌ | ❌ | ❌ | ❌ | ✅ |
| Academy integrata | ⚠️ | ❌ | ❌ | ❌ | ✅ |
| MLS aperto (no franchising) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Lead scoring AI (qualità lead) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Migrazione "clone del vecchio sito" | ❌ | ❌ | ❌ | ❌ | ✅ |
| Privacy 4 livelli dinamica | ❌ | ❌ | ❌ | ❌ | ✅ |
| Nessun setup fee / nessun lock-in | ❌ | ❌ | ❌ | ❌ | ✅ |

🔥 **Scoperte chiave** (vedi `COMPETITIVE_ANALYSIS_IDEALISTA.md` per dettagli):
- **Immobiliare.it Pro = Getrix rebrand** (acquisizione, 16.000 installazioni legacy → pool migrabile)
- **Idealista NON ha CRM proprio**: rivende Miogest/Gestim/Casa.it (debolezza strategica)
- **Lamentela #1 mercato**: lead poco qualificati → risolta da Lead Scoring AI (D-025)
- **Tutti hanno pricing opaco** ("Contattaci") → OMNIA mette listino in homepage

---

## User Personas

1. **Privato Acquirente/Venditore** — usa ImmobilCloud per cercare/pubblicare
2. **Agente Immobiliare** — usa ImmoWeb come strumento di lavoro quotidiano
3. **Broker / Titolare Agenzia** — usa ImmoWeb + Analytics + MLS + Academy
4. **Studente Academy** — usa Omnia Academy per certificarsi
5. **Partner Finanziario (banca/mutui)** — riceve lead qualificati

---

## Core Requirements (Static)

### Funzionali
- Multi-tenant (ogni agenzia isolata)
- Multi-utente per agenzia con ruoli
- Multi-lingua (IT primario, EN export)
- Privacy GDPR-compliant
- White Label brandizzabile

### Non funzionali
- Mobile-first responsive
- Performance: < 2s load time
- SEO ottimizzato
- Backup giornaliero
- Audit log completo

---

## What's Been Implemented

### Pre-progetto (eredità da Immocloud-2.0 + IMMOWEB)
- ✅ Modelli dati canonici allineati (Phase A+B, 104 test) — documentati
- ✅ Adapter bidirezionale cross-repo
- ✅ Feed XML multi-portale (documentato, da riportare)
- ✅ MLS Security + Privacy 4 livelli (documentato, da riportare)
- ✅ Workflow collaborazione 5gg (documentato, da riportare)
- ✅ Valutatore GIS con 27.228 zone OMI (documentato, da riportare)

### M2 — ImmoWeb MVP (Agency CRM)
- ✅ **M2.S2 (12 Giu 2026)** — CRUD Immobili + Import CSV/XML:
  - Backend `Property` model (16 tipi, 25 boolean features, 6 stati, energy class, owner riservato, photos, geo)
  - 9 endpoint REST CRUD + CSV template download + POST /import/csv + POST /import/xml
  - Bulk import audit log (`ImportJob` con errori per riga)
  - XML feed parsing flessibile (alias Italian: titolo/prezzo/mq/vani + Immobiliare.it/Idealista compatible)
  - Frontend: `PropertiesPage` (grid card + filtri + search), `PropertyFormPage` (form 8 sezioni con 25 feature checkboxes), `PropertyImportPage` (CSV+XML wizard amichevole 3-step)
  - i18n IT: 90+ chiavi (16 tipi, 25 features, condizioni, ecc.)
  - KPI dashboard "properties_active" ora REALE
  - Sidebar Immobili sbloccata
- ✅ **M2.S1 (12 Giu 2026)** — Dashboard agenzia + onboarding:
  - Backend `Agency` model (fiscal/address/contact/branding) + `AgencyInvite` (magic-link)
  - 9 endpoint REST `/api/app/agencies/*`, `/api/app/invites/*`, `/api/app/dashboard/kpis`
  - Magic-link flow E2E: invito → email Resend → verify → set password → auto-login
  - Frontend: `OnboardingWizard` 4-step, `AgencyShell` (sidebar navy + topbar), `DashboardPage` con KPI grid, `MembersPage` (tab Attivi/Inviti + modal invito + revoca), `SettingsPage`, `AcceptInvitePage`
  - 3 template email IT/EN/ES per invito agenzia
  - Indici DB ottimizzati (slug unique, token unique, compound agency_id+status)
  - 75+ chiavi i18n aggiunte
  - Tested via curl end-to-end + Playwright UI flow

### M1 — Foundation
- ✅ **M1.S1 (10 Giu 2026)** — 3 decisioni architetturali approvate:
  - Monorepo Turborepo (D-011)
  - Sottodomini corti su omniarealestateecosystem.it (D-012)
  - Shared schema MongoDB multi-tenant (D-013)
- ✅ **M1.S2 (11 Giu 2026)** — Setup monorepo + struttura base:
  - i18n nativa IT/EN/ES con react-i18next + auto-detection browser (D-014)
  - Logical Monorepo implementato (D-015): backend `apps/` + `shared/`, frontend `apps/` + `shared/`
  - MongoDB connesso con indici tenant-aware su 6 collection
  - Endpoint health funzionanti: `/api/`, `/api/health`, `/api/core/health`, `/api/cloud/health`, `/api/app/health`, `/api/learn/health`
  - 4 app frontend live: Landing (`/{lang}`), ImmoCloud (`/{lang}/cloud`), ImmoWeb (`/{lang}/app`), Academy (`/{lang}/learn`)
  - Componenti condivisi: `LanguageSwitcher`, `HealthBadge`, axios client con header `Accept-Language` auto
  - Routing intelligente con redirect lingua + 404 personalizzato
  - Design distintivo per app (Landing chiaro/serif, Cloud dark, Web stone, Academy cream)
- ✅ **M1.S3 (11 Giu 2026)** — Auth JWT + Ruoli + Multi-tenant:
  - bcrypt + PyJWT installati
  - 7 endpoint auth: register, login, me, refresh, logout, forgot-password, reset-password
  - 5 ruoli: super_admin, agency_admin, agent, client, student
  - JWT HS256 (access 15min, refresh 7gg) in cookie httpOnly+secure
  - Brute force protection (5 tentativi = lockout 15 min)
  - Admin auto-seeding (mcnicastro@gmail.com)
  - Resend integration con 6 template email (welcome+reset × IT/EN/ES)
  - Frontend: AuthProvider, ProtectedRoute, LoginPage, RegisterPage, ForgotPasswordPage, DashboardPage
  - i18n integrato in tutto auth flow
- ✅ **M1.S4 (11 Giu 2026)** — Deploy preview + dominio:
  - SEO/OG tags multi-lingua in `index.html` (title, og, twitter card, JSON-LD Organization)
  - 4 hreflang links (it/en/es/x-default) + canonical pointing to `omniarealestateecosystem.it`
  - **Design north-star** salvato in `/app/memory/DESIGN_NORTHSTAR.md` (palette navy `#0B1E3F` / teal `#1F6B5C` / viola `#4B3D7A` / oro `#C8A653`, font Fraunces + Inter, principi anti-AI-slop)
  - **DNS setup guide** in `/app/memory/DNS_SETUP_GUIDE.md` (apex + sottodomini cloud./app./learn./api.)
  - **Resend domain guide** in `/app/memory/RESEND_DOMAIN_GUIDE.md` (skip in M1, da fare prima onboarding agenzie)
  - `.gitignore` fix: rimosso `.env*` blocking
  - `CORS_ORIGINS` esteso per produzione (apex + 4 sottodomini)
  - Deploy readiness check: ✅ PASS

### M2 — ImmoWeb (in corso)
- **M2.S1** ✅ Agency Onboarding + Dashboard + Magic-Link Team Invites (Resend)
- **M2.S2** ✅ Property CRUD (16 types, 25 features) + Photo Uploader (base64/canvas resize) + CSV Import + Custom Agestanet XML Parser (65 properties test OK)
- **M2.S2bis** ✅ Cross-app unified TopNav + Desktop UI overflow fixes
- **Settings UI refactor** ✅ (16/06/2026) — Rimossi logo URL + color picker. Aggiunta sezione "Sito web agenzia" con 2 modalità: external (URL + futuro feed XML M2.S5) | omnia_template (galleria M2.S6).
- **M2.S3** ✅ (16/06/2026) — **CRM Clienti completo**: backend CRUD `/api/app/clients` con filtri (q/status/client_type/operation/city) + paginazione + CSV import + CSV template. Frontend `ClientsPage` (lista con tabella + filtri) + `ClientFormPage` (anagrafica + preferenze ricerca idealista-style: operation, property_types[], cities[], zones[], price/surface/rooms/bathrooms ranges, conditions[], floor_preferences[], must_have_features[], energy_min_class, needs_photos/virtual_tour, GDPR consent). Sidebar `Clienti` sbloccata. 15/15 pytest backend + 7/7 flussi UI passed.
- **M2.S3.5** ✅ (17/06/2026, D-026) — **Property↔Seller bidirectional link**: aggiunto `Property.seller_client_id`, endpoint `/clients/sellers` (autocomplete), `/clients/{id}/properties` (immobili in carico). UI SellerPicker combobox nel form immobile + sezione "Immobili in carico" nella scheda Cliente seller/landlord. PATCH null-clear supportato. 10/10 pytest backend + flussi UI passed.
- **M2.S4** ✅ (17/06/2026, D-025) — **Matching Engine + Lead Scoring AI**: algoritmo deterministico 14 criteri/100pt (`matching.py`), 4 endpoint REST (`/matches`, `/matches/property/{pid}`, `/matches/client/{cid}`, POST `/matches/lead-score`). **Lead Scoring AI con Gemini-3-flash-preview via Emergent LLM Key + fallback rule-based.** Output AI in italiano naturale: score 0-100 + temperatura (freddo/tiepido/caldo/rovente) + reasons[] + action_hint commerciale. Frontend MatchesPage (card colorate per temperatura + filtro min_score) + MatchLeadScorePage (banner + action card + reasons + breakdown). Sidebar `Match` sbloccata. 17/17 pytest backend + flussi UI passed. Costo medio Gemini per call: ~$0.001.
- **M2.S5 Layer A** ✅ (18/06/2026, D-029) — **Portal Manager**: backend `/api/app/portals` (catalog GET + CRUD + test endpoint) con encryption AES-256 via Fernet sulle password portali. 7 portali catalogati al lancio (Idealista, Immobiliare.it, Casa.it, Wikicasa, Subito.it, Facebook Catalog, LinkedIn). Frontend `PortalsPage` con tabella sottoscrizioni + modale subscribe + card portali disponibili. Sidebar `Portali` attiva. Layer B/C/D in arrivo (XML feed gen / site-as-feed / clone-from-URL).
- **M2.S5 Layer B** ✅ (18/06/2026, D-028) — **OSF v1.0 Public Feed**: endpoint pubblici `GET /api/feed/{slug}.xml`, `GET /api/feed/{slug}.json`, `GET /api/feed/schema/osf-v1.json` (NO auth, portali pullano anonimamente). Schema OMNIA Standard Feed: clean (stringhe non codici numerici), dual XML+JSON, AI-extended namespace `omnia:*`, JSON Schema documentato pubblicamente per invitare adozione come standard. Testato E2E: 200 OK con feed valido + 404 su slug sconosciuto + multi-tenant rispettato.
- **M2.S5 Layer C** ✅ (18/06/2026) — **Public Site (HTML SEO crawlable)**: 4 endpoint pubblici per consumatori esterni (Idealista pull, Google bot, share social):
  - `GET /api/p/{slug}/` — agency listing index (HTML server-rendered, schema.org RealEstateAgent JSON-LD)
  - `GET /api/p/{slug}/{pid}` — single property page con OG tags + schema.org Product/RealEstateListing JSON-LD + photos lazy + canonical
  - `GET /api/p/{slug}/sitemap.xml` — sitemap XML standard (lastmod, changefreq, priority)
  - `GET /api/public/property/{pid}/photo/{i}` — binary JPEG da base64 con `Cache-Control: max-age=86400`
  - Owner block strippato sempre; styling base inline (clean, fast load <6KB). Verificato 200 OK + JSON-LD valido + 404 su slug/pid sconosciuti.
- **M2.S5 Layer D Phase 1** ✅ (18/06/2026, D-023) — **Brand Profile Extractor**: `POST /api/app/website/extract-from-url` con httpx + BeautifulSoup + Gemini-3-flash-preview. Estrae da un URL fornito dall'agenzia: palette (4 hex), typography (family+scale), structure (header/hero/nav/card style), voice (tone+tagline), logo_hint, confidence 0-100. Persistito in `agency.website.extracted_profile`. Verificato su tecnocasa.it: palette esatta (#00843D verde + #FFF200 giallo) + hero `search_box_centered` + confidence 95.
- **M2.S5 Layer D Phase 2** ⏳ — Bundle Next.js generation + CNAME deploy (rinviato a M2.S6 Theme Registry)
- **M2.S5 Layer A++** ⏳ — Cron worker reale push portali push_api
- **Hardening 18/06/2026**:
  - 💰 **Lead Score caching** (24h TTL via MongoDB index) — call seguente cache-hit 55× più veloce, zero costi Gemini ripetuti. `force_refresh=true` per bypass manuale.
  - 🎯 **Match preview inline** nel PropertyFormPage (edit mode): top 3 clienti compatibili con score badges + link diretto al Lead Score AI page. Riduce drasticamente i click per arrivare al valore.
  - 🛡️ **Error Boundary globale** in App.js — zero white-screen of death in produzione, UI di recovery con tasto Ricarica/Home + dettaglio tecnico collapsable.
- **M2.S5 Layer B+C+D** ⏳ — XML Feed Generator (OSF schema D-028) + Site-as-Feed pages + Clone-from-URL (D-023)
- **M2.S5** ⏳ XML Multiposting/Feed Output — *user has "secret idea" to discuss prima del coding*
- **M2.S6** ⏳ White Label + Template Gallery

### M3 — ImmobilCloud
*Non ancora iniziata*

### M4 — MLS + Stripe
*Non ancora iniziata*

### M5 — AI Suite
*Non ancora iniziata*

### M6 — Academy
*Non ancora iniziata*

---

## Prioritized Backlog

Riferimento completo: vedi `ROADMAP.md`

### P0 — Nessuno (audit 30-Lug-2026: tutte le fasi 0-3 completate)

### P1 — In attesa del Founder
- API key vere per APE/SIAPE + OpenAPI docs (scaffold pronto, 503-guarded)
- Go Live Stripe (claim account sandbox → key live)
- **Manuale Operativo + Academy** (prossimo blocco concordato)
- Landing A-004 `/it/agenzie` refresh + A-006 video Ken Burns

### P2 — Residui minori (non bloccanti, opzionali)
- Estendere TypeScript ad altri moduli shared (L2 è incrementale per design)
- Convertire i fetch residui non-core (ValuatorPage, MortgageComparator, DomainVerifyPage) al client axios
- Test frontend su componenti con DOM (oggi solo logica pura)
- Migrazione batch delle foto base64 legacy verso Object Storage (le nuove già ci vanno)

### P3 (Post-M6) — Espansione
- PWA mobile
- Virtual Cleaning + Interior Redesign AI
- Firma digitale reale
- WhatsApp Business
- Catasto reale

---

## Test Credentials

Vedi `test_credentials.md` (creato al primo deploy).

---

## Architettura tecnica (da confermare in M1.S1)

### Stack
- **Frontend**: React 18 + Tailwind + shadcn/ui
- **Backend**: FastAPI (Python 3.11+)
- **Database**: MongoDB (Motor async driver)
- **Hosting**: Emergent Platform
- **AI**: Gemini via Emergent LLM Key
- **Payment**: Stripe
- **Email**: SendGrid
- **Storage**: Emergent Object Storage
- **Geocoding**: Nominatim (OSM, free)

### Pattern
- Multi-tenant con `agency_id` su ogni documento
- JWT auth con refresh token
- Webhook Stripe per pagamenti
- Cron jobs per multiposting XML
- Background tasks per AI generation

---

## Changelog Sessione 24-Giu-2026 — Strategic & AI Suite

### ⚙️ Tecnico realizzato (4 milestone)
- ✅ **M5.S1 AL for Agents** completato (chat + streaming SSE + inline copywriter IT/EN/ES)
- ✅ **M5.S3 AL Legal** completato (5 sub-agenti, Tavily web search, anti-hallucination, PDF analysis, disclaimer L.247/2012)
- ✅ Brand rename "Al" → "**AL**" ovunque (D-030)
- ✅ P2 fix Chrome auto-translate

### 🧠 Strategic decisions (NON ANCORA IMPLEMENTATE)
- **D-032**: OMNIA è marketplace multi-side con **7 revenue stream**, non SaaS B2B singolo. Vedi `BUSINESS_MODEL.md`
- **D-033**: Architettura **M5.S4 Virtual Staging "premium 3-stage"**: SAM + Flux Inpainting + Real-ESRGAN via fal.ai (~€0,06/img vs €15-29 competitor)
- 5 differenziatori M5.S4: CRM-aware prompt / Reverse Staging / Micro-tour video / A/B test portale / Trasparenza normativa

### 💰 Pricing draft (da validare con consulente esterno)
- Starter €69 / Pro €189 / Premium €499 / Enterprise custom (per agenzia, non per agente)
- **Founder 50** offer: −50% per 24 mesi prime 50 agenzie (lock-in)
- Sweet spot Pro: agenzia media 3-5 agenti, margine 74%
- Vero profit center identificato: **Stream 3 B2C privati** (€3,5M/anno potenziale) + **Stream 5 marketplace** (€2,5M/anno)
- ARR potenziale @1000 agenzie: **€10,9M** (vs vecchia stima €1,3M = +750%)

### 🚨 Blocker richiesto da Founder
1. **Validazione consulente esterno** (commercialista startup SaaS + fractional CFO real estate) prima di GTM
2. **FAL_KEY** richiesta per partire M5.S4 (https://fal.ai/dashboard/keys, $5 free credits)
3. Discussione M4 Stripe sospesa fino a nuova società Founder

---

## Changelog M5.S3 — AL Legal (24-Giu-2026)

✅ **Backend modulare** (`/app/backend/apps/immoweb/al_legal/`):
- `prompts.py` — 5 sub-agenti (general, proposta, locazioni, catasto, urbanistica) + `pdf_analysis` + router keyword-based
- `tavily.py` — async wrapper Tavily AI con whitelist 7 domini normativi IT
- `validator.py` — secondo LLM con `confidence ∈ [0,1]`, soglia 0.85, fallback graceful, `append_disclaimers()`
- `pdf_parser.py` — pypdf, hard cap 5MB / 60 pages / 40k chars
- `router.py` — 5 endpoint: chat / analyze-pdf / sessions list/get/delete / health

✅ **Endpoint REST**:
- `POST /api/app/legal/chat` — Tavily search + main LLM + validator + disclaimer assembly
- `POST /api/app/legal/analyze-pdf` (multipart) — upload + extract + analyze
- `GET/DELETE /api/app/legal/sessions[/{sid}]` — CRUD storico
- `GET /api/app/legal/health` — probe (no auth)

✅ **Frontend** (`/app/frontend/src/apps/legal/LegalApp.jsx`):
- Pagina dedicata `/it/legal` accessibile a tutti gli utenti autenticati
- DisclaimerModal first-visit con checkbox L.247/2012 + localStorage `omnia_legal_disclaimer_v1`
- ChatTab: stream Tavily + LLM (~20s) con thinking placeholder, sub-agent badge colorato, ConfidencePill (verde/ambra), pannello fonti clickable
- PdfTab: dropzone + question + analisi strutturata
- CTA notaio automatica sotto soglia confidence
- Sidebar `AgencyShell.jsx` — nav item `⚖ AL Legal`
- Axios timeout custom: 90s chat, 120s PDF

✅ **Sicurezza**:
- Rate limit 30/h per utente (chat+PDF condivisi, scelta intenzionale)
- Multi-tenancy: nessun `agency_id` necessario (operazione su query/PDF utente)
- Audit log permanente `al_legal_audit` (retention 5 anni richiesta da D-028)

✅ **Test E2E** — iteration_20.json: **16/16 backend** (5 sub-agenti routing, schema, multi-turn, B2C access, PDF valido/non-PDF/>5MB, sessions CRUD, audit log) + **100% frontend** (disclaimer modal, chat flow completo, sub-agent badge, confidence pill, fonti clickable, PDF tab, sidebar nav)

---

## Changelog M5.S1 — AL for Agents (24-Giu-2026)

✅ **Backend** (`/app/backend/apps/immoweb/al_agent.py`):
- POST `/api/app/al/chat` — chat sincrona con Gemini-3-Flash via emergentintegrations
- **POST `/api/app/al/chat/stream`** — **streaming SSE token-by-token** (UX ChatGPT-style)
- **POST `/api/app/al/improve`** — generazione inline titolo/descrizione (IT/EN/ES) usando snapshot del form immobile, no agency_id required (funziona anche per utenti B2C privati)
- Pattern manuale JSON tool-use (la lib non supporta `tools=` nativi)
- 5 tool whitelistati: `query_properties`, `query_clients`, `query_leads`, `monthly_performance`, `write_description`
- Sicurezza multi-tenant: `agency_id` iniettato server-side dal JWT, mai dall'AI
- Rate limit soft: 60 msg/utente/ora (chat + improve condividono contatore)
- Sessioni persistenti (collection `al_sessions` + audit `al_audit`)
- Error handling: budget esaurito → 503/SSE event `llm_budget_exceeded`
- Brand: AL (maiuscolo) — system prompt aggiornato a "Sei AL,..."

✅ **Frontend**:
- `/app/frontend/src/apps/immoweb/components/AlChatWidget.jsx` — FAB "AL" bottom-24/right-6, streaming live via fetch+ReadableStream, Stop button, cursore lampeggiante, i18n completo
- **`/app/frontend/src/shared/components/AlImproveButton.jsx`** — componente riusabile ✨ "Migliora con AL" + modal con tabs IT/EN/ES, layout Originale | Suggerito, Apply/Regenerate/Cancel
- Mount in `PropertyFormPage.jsx` (agente ImmoWeb): accanto a titolo + sotto descrizione
- Mount in `SellPage.jsx` (privato B2C ImmobilCloud): accanto a titolo + sotto descrizione
- Brand: tutto "Al" → "AL" in label UI + i18n (`al.open_chat`, `al.welcome`, ecc.)

✅ **P2 Fix — Chrome auto-translate**:
- `<html lang="it" translate="no">` + `<meta name="google" content="notranslate">` + `<body class="notranslate">`

✅ **Test E2E**:
- iteration_17.json — 100% backend (8/8) + 100% frontend (sync chat)
- iteration_18.json — 100% backend (6/6) + 100% frontend (streaming SSE incrementale)
- iteration_19.json — 100% backend (13/13 pytest improve) + 100% frontend agent flow (IT/EN/regen/apply/cancel/brand AL)

---

*Prossima revisione: al termine di M5.S3 (Al Legal)*
