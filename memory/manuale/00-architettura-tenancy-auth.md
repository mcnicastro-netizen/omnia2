# Cap. 00 · Architettura tenancy → jobs (audit SaaS)

**Ambito**: founder / super_admin.  
**Prompt master**: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27).  
**Numerazione sessione**: continuum in `AUDIT_ARCHITETTURA_NOTE.md`.

---

## Metodo

Un blocco alla volta · niente fix senza «vai» · no P0–P3 prematuri · **listino fermo** finché Backup+Restore non sono disegnati.

---

## Decisioni di dominio (stato 09-Nov-2026)

| ID | Sintesi | Stato codice |
|----|---------|--------------|
| **D-094** | Trash ≠ status · filtro uniforme dominio · default non-trashed | ⏳ dominio pieno pre-GTM |
| **D-095** | Media pubblici vs privati · cleanup blob | ✅ AuthZ fascicolo + blob delete + trash→blob |
| **D-096** | Bak+Restore insieme · restore agency-first | ✅ scope B2C+media · dry-run agency-first (#145) |
| **D-097** | Elimina per sempre ≠ irrecuperabile assoluto · trash in bak OK | ✅ policy |
| **D-098** | Orphan → path a delete · agency close V1 | ✅ orphan GC APScheduler (#144) · close V1 ⏳ |
| **D-099** | Founders GDPR assistito · fascicolo AuthZ prima del bak | ✅ export/erase + DSAR + DPA stub (#146) |
| **D-100** | Invite: utente esistente → link agency; mai overwrite password | ⏳ fix-needed trasversale |
| **D-101** | Job automatici: **single-instance** ora | ✅ ops single-replica |
| **D-102** | Purge + orphan cleanup in APScheduler | ✅ (#144) |
| **D-103** | No worker dedicato ora | ✅ |
| **D-104** | **GTM-01 ACQUISITO** · vincolo hard pre-~5000 email | ⏳ coda |
| **D-105** | Bak health minimo Founder Ops | ⏳ |
| **D-106** | `active_agency_id` = SoT; no `agency_ids[0]` | ✅ path toccati + helper `require_agency_id` |
| **D-107** | Errori API: `code` stabile BE + i18n FE | ⏳ |
| **D-108** | Scheduling: un solo owner di esecuzione | ✅ |
| **D-109** | Pricing SoT = `GET /billing/plans` | ✅ |
| **D-110** | Demo mode esplicito; `localStorage` ≠ entitlement | ✅ |
| **D-111** | Cestino = stato non operativo (freeze) | ✅ |
| **D-112** | Seed demo idempotente | ✅ · demo OFF prod (D-145) |
| **D-113** | Restore manuale testabile pre-GTM | ✅ dry-run agency-first |
| **D-114** | Sostenibilità bak/media pre-attivazione | ⏳ numeri+design |
| **D-115** | Programma O0…O6 · no self-serve finché O6 ≠ PASS | ⏳ |
| **D-118** | Audit Portale ImmobilCloud · MERGED (#12) | ✅ |
| **D-116** | OpenAPI Catasto sandbox: una sola API key | ✅ |
| **D-145** | Primo cliente = Nicastro · seed demo OFF Railway | ✅ |
| **D-146** | Vetrina www · no Cerca casa in nav/CTA | ✅ |
| **D-147** | Kling 30 cr / €1,50 | ✅ |
| **D-148** | Paperless in Perché OMNIA (4° tratto) | ✅ |
| **D-149** | Migrazione sito casi 1–2 MLS on/off + clone capture | ✅ (#136) · restyling coda |
| **D-150** | Template pack unico neo+restyling · matrice MLS | ✅ |
| **D-151** | Listino template €99/€199 · gallery 8 | ✅ gallery (#137) · Stripe entitlement ⏳ |

**SoT continuità:** `docs/audit/OMNIA_AUDIT_STATE.md` · `memory/NEXT_SESSION.md` · `memory/PROGRAMMA_VERSO_8.md` · fascicolo D-118  

### Vetrina www (`LandingApp` · D-146 · 06-Nov-2026)

- **URL**: `https://omniarealestateecosystem.it/it` (Vercel FE · `frontend/src/apps/landing/LandingApp.jsx`).
- **Ruolo**: pitch Lab + Ecosystem (non è ImmobilCloud). Entry B2C ricerca casa = sotto-dominio/path cloud, non TopNav vetrina.
- **Nav**: Chi siamo (`#chi-siamo`) · Le tre anime (`#offerta`) · Perché OMNIA (`#perche`) · Prezzi (`#prezzi`) · Registrati. Sticky TopNav **fuori** dal wrapper `overflow-x-hidden` (altrimenti sticky spezzato → scroll “a metà”).
- **Ordine sezioni**: …anime → Perché OMNIA (tratti) → Il vero lavoro (`#vero-lavoro`, diagramma) → Prezzi → CTA «validazione» (solo Inizia ora).
- **Perché OMNIA (D-148)**: 4 tratti — ecosistema · mestiere · domain sovereignty · **documenti digitali (non cartacei)**. Listino Founders solo in `#prezzi`. Claim paperless = solo pezzi reali (Fascicolo, modulistica PDF, kit dominio); vietato firma live / PEC OMNIA / «100% paperless».
- **Box anime**: cloud→`/it/cloud` · crm→`/it/register` · academy→`/it/learn`.
- **Deploy**: `bash scripts/vercel-deploy.sh` (D-074).
- **HAL**: `api.www-vetrina-landing`.

**Sequenza D-099 (09-Nov):** fascicolo AuthZ ✅ · orphan GC ✅ · Bak+Restore ✅ · GDPR Founders ✅ · retention/costi residui.  
**Filo verso-8:** Manut/SaaS = 8 · Storia ~7,8 (manca dogfood Nicastro Onda 1).  
**Niente codice** senza «vai».

### Cloud Agent — ID `bld-…` (7-Ott-2026)

Nella UI chat può comparire un ID tipo `bld-20261007-…`: è lo **snapshot Environment Build** (install già fatto), **non** un secret.  
Cursor lo tiene in Dashboard → Environments → Builds. **Non serve** salvarlo nel password manager; annotalo solo se vuoi pin/debug di quello snapshot. I secret restano nel vault (`CLOUD_SECRETS_INVENTORY.md`). HAL: `api.cloud-environment-builds`.

### D-123 / D-074 — Go-live produzione (12-Ott-2026)

**API pubblica**: `OMNIA_API_PUBLIC_URL` (`GET /api/health` → ok/db=ok).  
Alias Railway: `https://omnia-api-production-2cec.up.railway.app`. Progetto `omnia-api`.  
**FE Vercel**: progetto `omnia-frontend` · alias `https://omnia-frontend-kappa.vercel.app` · domini `omniarealestateecosystem.it` / `www` / `app` / `cloud`.  
**Stripe Test webhook**: ``OMNIA_API_PUBLIC_URL` + `/api/billing/webhook`` (descrizione `OMNIA Railway API (sandbox)`) · `whsec` su Variables Railway.  
DNS SoT: `memory/DNS_SETUP_GUIDE.md`. Runbook: `docs/ops/RAILWAY_DEPLOY.md` · `docs/ops/VERCEL_DEPLOY.md` · `memory/STRIPE_ONBOARDING.md`.  
HAL: `api.railway-api-deploy` · `api.vercel-fe-deploy` · `api.stripe-sandbox-cloud` · `api.cloud-secrets-vault`.

### D-131 / D-132 / D-133 / D-134 — Ops live (28-Ott-2026)

- **D-131 Auth area**: hub B2C `/cloud/area` (Accedi / Crea account); 409 `email_already_registered` su duplicati. Recovery password unica (`forgot-password`) per tutti i ruoli.
- **D-132 Resend**: `SENDER_EMAIL=OMNIA <info@omniarealestateecosystem.it>` (non `EMAIL_FROM` / non sandbox `onboarding@resend.dev`). Auto-heal in `shared/email/client.py`. Guide: `RESEND_DOMAIN_GUIDE.md`.
- **D-133 Vercel bake**: build FE **deve** impostare `REACT_APP_BACKEND_URL` da `OMNIA_API_PUBLIC_URL` (`vercel-deploy.sh`) — altrimenti Academy→Cerca casa crasha.
- **D-134 Google Sign-In**: `GOOGLE_CLIENT_ID` = OAuth **Web** reale (`…apps.googleusercontent.com`) su Railway + vault Environment. Placeholder → `401: invalid_client`. Guide: `GOOGLE_AUTH.md`. P-021 chiuso.

### D-135 — Dogfood B2C Vendi (02-Nov-2026)

- **CSRF cross-site** (`cloud.*` / `www.*` → `api.*`): `/api/auth/refresh` **esente**; header `X-CSRF-Token` + mirror `sessionStorage` FE; CORS `expose_headers`. Sintomo tipico: logout ~1 min / `csrf_failed` sul salva.
- **HAL improve**: pin `gemini-3.5-flash` (+ timeout/fallback); i18n `al_improve.err_*`.
- **Nav account**: «Il mio account» **solo** `account_type=b2c`; sessione agenzia/Founder → «Area riservata» + banner. Vendi = account Privato (finestra anonima OK).
- HAL YAML Cap.00/01/10/18 · reindex prod ~973 chunks · SoT `DECISIONS` D-135.

### Incident Railway Variables (22-Ott-2026)

Mail Railway: possibile leak Variables. OMNIA `omnia-api` → rotazione credenziali.  
Runbook: `docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`.  
**Core DONE** Founder 22-Ott (Stripe, Gemini, fal, Resend, OpenAPI, JWT, RAILWAY_TOKEN + deploy; health ok).  
Residui: YouTrust (ticket / `ESIGN_PROVIDER=mock`) · Mongo rotate · no screenshot valori.  
HAL: `api.railway-security-rotation`. Prompt nuovo agent: `docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md`.

### D-118 — stato (aggiornato 9-Ott-2026 sera)

**Analisi + residuo codice chiusi**: A–J GREEN · fascicolo aggiornato · PR #12.  
**Fix**: Ops/G/H + resilienza P-033/046…058 (CSRF, Stripe fallback, backup B2C, RL, soft-delete, i18n, SEO, notify…).  
**Residui**: P-021 Google opz. · P-026 vault whsec MITIGATO.  
**Stato repo**: MERGED su `main` (PR #12 · `361bd98`).  
SoT: `OMNIA_PORTALE_AUDIT_FASCICOLO.md` · `portale-finding.md` · `NEXT_SESSION.md`.  
HAL: `api.portale-audit-program` · `api.founder-ops-portale` · `api.visura-openapi-catasto`.

---

## Cluster aperti

| Cluster | Finding |
|---------|---------|
| Media / fascicolo AuthZ | P3.1 + M-01 + **G-02** → D-095/D-099 |
| Orphan / retention | RET-* · D-098 · **D-102** |
| Disaster recovery | B-* · R-* · D-096 |
| GDPR | G-* · D-099 (Founders assistito) |
| Race | **RC-*** · invite → **D-100** |
| Jobs | **J-*** · **JA-*** · **D-101**…**D-103** |
| Osservabilità | **O-*** · **D-105** |
| API / Frontend | **AF-*** |
| Coerenza prodotto | **CT-*** · **D-109** · **D-110** · P21 CHIUSO |
| Casi limite | **EC-*** · **D-111** · **D-112** · P22 CHIUSO |
| Debito architetturale | **AD-*** · **D-113** · P23 CHIUSO |
| Non lista infinita | **NI-*** · P24 CHIUSO · SoT ripago §25bis |
| Report finale | P25 A–K · ⏳ |
| GTM / Demo | **GTM-01 ACQUISITO** · **D-104** · in coda · pre-~5000 email |
| Portale B2C audit | **D-118** · CHIUSO · MERGED `main` · P-021/P-026 residui |
| Costo / listino | C-* · B-01 · fermo |

---

## Progresso

| Sessione | Master | Stato |
|----------|--------|--------|
| P1–P24 | §1–§24 | chiusi · D-094…D-114 · classificazione + D-114 bak/media |
| P25 Report finale | §25 | Consegnato · A–K · ⏳ analisi |
| D-118 Portale | A–J | ✅ GREEN + residuo codice CHIUSO · MERGED `main` |
| — | §23 Priorità | ⬜ CLOSED fino al «vai» |
| GTM-01 | post-audit | 🟠 **ACQUISITO** · in coda · smoke ~20 |

Dettaglio: `docs/audit/OMNIA_AUDIT_STATE.md` · `AUDIT_ARCHITETTURA_NOTE.md` · A-035 · A-036.