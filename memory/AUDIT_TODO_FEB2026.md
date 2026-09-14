# 📋 AUDIT TODO — Febbraio 2026 (fork post-Sprint 4)

**Compilato**: 26-Feb-2026 · **Autore**: agente E1 fork post-Sprint4
**Stato**: 📝 memorizzato · da attendere approvazione Founder prima dell'implementazione

---

## 🔴 P0 — Bug silenziosi in produzione (~1-2h totali)

### A. Privacy Gate — classe energetica invisibile su B2C
**File**: `/app/backend/shared/utils/privacy_gate.py:120-123`
**Bug**: `apply_privacy_view` sotto L4 riscrive `energy = {"class": energy.get("class")}`
ma nel modello `PropertyEnergy` la chiave è `energy_class`, non `class`.
**Effetto**: viewer L1/L2 (99% del traffico portale) non vede la classe energetica.
**Contraddizione**: il Compliance Validator M2.6b esige la classe energetica come rule HARD (L. Boschi).

### B. Dashboard singola-agenzia mente sui KPI
**File**: `/app/backend/apps/immoweb/dashboard.py:51-63`
**Bug**: `leads_open` e `matches_week` sono `locked=True, value=0` benché i dati esistano.
Il rollup consolidato `groups.py:238-345` legge invece `db.leads` reali con `count_documents({"status": "new"})`.
**Effetto**: l'agente singola-filiale non vede i lead sul dashboard. Solo il `group_admin` li vede sul consolidato.

### D. Matching engine include immobili `draft`
**File**: `/app/backend/apps/immoweb/matches.py:71, 148`
**Bug**: filtro `status: {"$in": ["active", "draft"]}` propaga anche le bozze.
**Effetto**: falsi positivi nei match → l'agente propone al cliente immobili non pubblicati.

### E. HAL sotto-conta gli hot leads
**File**: `/app/backend/apps/immoweb/al_agent.py:164`
**Bug**: `hot_leads` filtra `status: "new" AND score >= 70`.
Lead in status `contacted` con score alto (già chiamati ma bollenti) sono esclusi.
**Effetto**: HAL sotto-riporta la pipeline calda.

### F. Doppio sistema Portali attivo
**File**: `/app/backend/apps/immoweb/portals.py` (legacy M2.S5 Layer A, Fernet) coesiste con
`/app/backend/apps/immoweb/publishing.py` (M2.6a, AES-256-GCM, seed 8 portali).
Il frontend espone entrambe le rotte (`/it/app/portals` + `/it/app/publishing`) nella sidebar.
**Effetto**: due sistemi, dati non sincronizzati. UX rotta.

---

## 🟡 P1 — Coerenza ruoli e UX (~1h)

### C. Ruoli fantasma nella moderazione
**File**: `/app/backend/apps/immoweb/moderation.py:24`, `/app/backend/apps/immoweb/cron.py:14`
**Bug**: `ALLOWED_ROLES = {"super_admin", "platform_admin", "admin"}` — ma nel `Literal UserRole`
esistono solo `super_admin`, `agency_admin`, `agent`, `client`, `student`, `group_admin`,
`branch_admin`, `branch_agent`. `platform_admin` e `admin` sono ruoli fantasma.
**Effetto**: di fatto solo `super_admin` può moderare. Da decidere: creare ruolo moderatore reale
o rimuovere alias fantasma. Il `group_admin` (holding) non può moderare i private listings.

### H. Group creation non aggancia agency del creatore
**File**: `/app/backend/apps/immoweb/groups.py:77-121`
**Bug**: il `create_group` promuove l'utente a `group_admin` ma **non aggancia automaticamente**
l'agency esistente del creatore come primo branch. Deve fare a mano `POST /branches`.
**Effetto**: onboarding a due step non necessari, il gruppo appena creato ha 0 branch.

### K. Lead email notification senza retry
**File**: `/app/backend/apps/immocloud/public_portal.py:707-718`
**Bug**: `_schedule_lead_email` è fire-and-forget. Fallimento Resend = log-only.
**Effetto**: lead perso silenziosamente.

### I. Ambiguità ruolo `agency_admin` vs `branch_admin`
**File**: `/app/backend/shared/models/user.py:8-18`
**Situazione**: commenti dicono "legacy alias — same as branch_admin", ma `agency_admin`
è ancora il default assegnato ai nuovi signup B2B. Decidere se alias reale o sostituzione.

### J. `moderation._ensure_admin` bypassa `require_roles()`
**File**: `/app/backend/apps/immoweb/moderation.py:27-29`
Il check custom `if user["role"] not in ALLOWED_ROLES` non usa il sistema alias franchising
di `shared/auth/dependencies.require_roles()`. Coerenza rotta con il resto del CRM.

### L. Filtro difensivo mancante su UPDATE
**File**: `/app/backend/apps/immoweb/properties.py:242`
`update_one({"id": prop_id})` senza `agency_id` (già filtrato in `find_one` prima → safe,
ma difensivamente debole — segnalato nel Sprint 4 testing report).

---

## 🟢 P2 — Debito tecnico (~2-3h)

### 1. Helper `_agency`/`_public`/`_strip` duplicati in 19 file
Consolidare in `/app/backend/shared/auth/tenant.py`:
- `require_agency_id(user) -> str`
- `strip_id(doc) -> dict`

File coinvolti (grep verified):
`properties.py`, `clients.py`, `matches.py`, `brand_extractor.py`, `publishing.py`,
`social_publisher.py`, `portals.py`, `custom_domain.py`, `api_keys.py`, `xml_import.py`,
`fascicolo.py`, `themes.py`, `analytics_ab.py`, `clients_ai_import.py`, `clients_smart.py`,
`al_agent.py`, `micro_tour_video.py`, `property_privacy.py`, `agencies.py`.

### 2. `import_agestanet.py` viola D-051
Il file `/app/backend/apps/immoweb/import_agestanet.py` (261 righe) è brand-mention nel filesystem.
Regola D-051: **zero brand mentions in codice, UI, log, PDF, email, commenti**.
La logica generica va migrata sotto `shared/importers/universal_xml.py` (che già esiste).

### 3. Split `properties.py` (717 righe)
Suggerito split:
- `apps/immoweb/properties_crud.py` (list/create/read/update/delete)
- `apps/immoweb/properties_photos.py` (upload Object Storage)
- `apps/immoweb/properties_import.py` (CSV template + CSV import + XML generic legacy)

### 4. Coerenza cartelle frontend
Consolidare `/app/frontend/src/apps/immoweb/*.jsx` (18 file legacy) e
`/app/frontend/src/apps/immoweb/pages/*.jsx` (11 file più recenti) in un'unica convenzione.
**Proposta**: tutte le pagine sotto `pages/`, componenti in `components/`.

### 5. File-fossili
- `apps/immoweb/cron.py` — 22 righe, quasi vuoto
- `apps/marketing/founders.py` — Founders 50 landing, congelato da D-035

---

## ⚙️ Piano di lavoro consigliato

**Blocco 1 (P0)**: A + B + D + E + F → 4 bug funzionali silenziosi + doppio menu portali.
Rischio basso, ROI alto (bug visibili all'utente finale). ~1-2h.

**Blocco 2 (P1)**: C + H + K + J → coerenza ruoli e UX onboarding gruppi.
Richiede una micro-decisione del Founder su C (creare ruolo moderator dedicato o rimuovere gli alias).

**Blocco 3 (P2)**: refactor pulizia debito.
Fare SOLO se il Founder dà il via — nessun impatto funzionale, ma costa tempo.

---

---

## 🏗️ P3 — Architettura & Env (~1.5h)

### M. Backend legge `REACT_APP_BACKEND_URL` (var frontend)
**File**: `apps/immoweb/micro_tour_video.py:95,294,464`, `apps/v1/widgets.py:32`
**Bug**: il backend fa `os.environ.get("REACT_APP_BACKEND_URL")` per costruire URL assoluti dei
video/asset. È una var **frontend** (prefix `REACT_APP_`) che il backend non dovrebbe leggere.
Rende il container backend dipendente da env destinata al frontend.
**Effetto**: rottura in caso di split container/deployment separati.
**Rimedio**: rinominare in `PUBLIC_BASE_URL` (già esiste come alternativa in `widgets.py:32`)
e aggiungerla al `.env` backend.

### N. Fallback hardcoded a preview URL obsoleto
**File**: ~30 test files in `/app/backend/tests/`
**Bug**: `BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com")`
L'URL preview di fallback è di una vecchia session. Ora il preview è
`f8c52ffb-5b20-4d8b-8b44-4bf33a3b19dd.preview.emergentagent.com`.
**Effetto**: se qualcuno lancia pytest senza `.env` caricato → chiama URL sbagliato, test rotti in silenzio.
**Rimedio**: `pytest.ini` che fa `env-file backend/.env` + rimuovere fallback hardcoded.

### O. 11 file frontend duplicano lettura `REACT_APP_BACKEND_URL`
**File**:
`apps/immocloud/ImmocloudApp.jsx`, `.../PropertyDetailPage.jsx`, `.../AddressAutocomplete.jsx`,
`.../ValuatorPage.jsx`, `apps/immoweb/WebsitePage.jsx`, `.../ModerationPage.jsx`,
`.../PublishingCenter.jsx`, `apps/landing/DomainVerifyPage.jsx`, `.../AgenziesLandingPage.jsx`,
`pages/WidgetsShowcasePage.jsx`, `shared/components/MortgageComparator.jsx`.
Ciascuno ridefinisce `const BACKEND_URL = process.env.REACT_APP_BACKEND_URL` e costruisce
`` `${BACKEND_URL}/api/xxx` `` a mano, quando `/app/frontend/src/shared/lib/api.js` centralizza
già `baseURL`, `Accept-Language`, cookies auth.
**Rimedio**: migrare tutti ad `import { api }` da `shared/lib/api.js`.

### P. Due sistemi crypto paralleli
**File**: `apps/immoweb/portals.py:40` (`OMNIA_PORTAL_ENC_KEY` → Fernet)
+ `shared/utils/crypto.py:17` (`CREDENTIALS_MASTER_KEY` → AES-256-GCM)
**Effetto**: convivono due sistemi di cifratura credenziali con chiavi env separate.
Legato al doppio sistema Portali (F). Da consolidare in AES-256-GCM (già la scelta più recente in M2.6a).

### Q. ENV VARS usate ma NON documentate in `.env`
Grep verified — usate in codice, assenti in `backend/.env`:
- `CREDENTIALS_MASTER_KEY` (⚠️ usato per cifrare credenziali portali e social — se manca fallback deterministico!)
- `FRONTEND_BASE_URL`, `PUBLIC_BASE_URL` (usati per costruire URL assoluti)
- `OMNIA_CUSTOM_DOMAIN_CNAME_TARGET`, `OMNIA_LOGO_URL`, `OMNIA_PORTAL_ENC_KEY`, `OMNIA_PUBLIC_URL`
- `RUN_STAGING_LIVE` (feature flag test)
- `SUPER_ADMIN_EMAIL`
**Rimedio**: aggiungere placeholder al `.env.example` (creare se non esiste) + rimuovere fallback
deterministici pericolosi (in particolare `CREDENTIALS_MASTER_KEY` — se un attacker conosce
`MONGO_URL` può derivare la master key dei portali cifrati).

### R. URL hardcoded fallback `omniarealestateecosystem.it`
Presente in `public_portal.py:734`, `saved_searches.py:265`, `brand_extractor.py:76`,
`feed.py:27-28`, `custom_domain.py:47,54,212`.
Non è un segreto ma se il dominio cambia (o l'agenzia usa il proprio) devi toccare 10 file.
**Rimedio**: unica costante `settings.APP_DOMAIN` da env.

---

## 🧪 Testing plan

Post-fix ogni blocco:
1. `pytest tests/test_matches.py tests/test_m3s9_privacy_audit.py` (P0 A+D)
2. Curl dashboard KPIs con user agente reale (P0 B)
3. Curl HAL Agents `monthly_performance` tool (P0 E)
4. Smoke UI su `/it/app/publishing` dopo dedup portals (P0 F)
5. Regressione stress test 5 agenti + Sprint 4 objstore
6. Testing agent v3 fork per validazione end-to-end frontend
