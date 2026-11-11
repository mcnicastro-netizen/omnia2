# Cap. 00 · Architettura tenancy → jobs (audit SaaS)

**Ambito**: founder / super_admin.  
**Prompt master**: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27).  
**Numerazione sessione**: continuum in `AUDIT_ARCHITETTURA_NOTE.md`.

---

## Metodo

Un blocco alla volta · niente fix senza «vai» · no P0–P3 prematuri · **listino fermo** finché Backup+Restore non sono disegnati.

---

## Decisioni di dominio (codice ⏳)

| ID | Sintesi |
|----|---------|
| **D-094** | Trash ≠ status · filtro uniforme dominio (pre-GTM) · default non-trashed |
| **D-095** | Media pubblici vs privati · cleanup blob |
| **D-096** | Bak+Restore insieme · restore agency-first |
| **D-097** | Elimina per sempre ≠ irrecuperabile assoluto · trash in bak OK |
| **D-098** | Orphan → path a delete (WHEN col bak) · agency close V1 controllata |
| **D-099** | Founders GDPR assistito · fascicolo AuthZ **prima** del bak |
| **D-100** | Invite: utente esistente → link agency; **mai** overwrite password (**fix-needed** · **trasversale**) |
| **D-101** | Job automatici: **single-instance** ora (non lock multi-pod); worker poi |
| **D-102** | Purge + orphan cleanup: **automatizzare ora** nel ciclo APScheduler |
| **D-103** | No worker dedicato ora; eventuale anti-dup minimo stesso-giorno |
| **D-104** | **GTM-01 ACQUISITO** · in coda · **vincolo hard** pre-~5000 email |
| **D-105** | Bak health minimo Founder Ops (OK/PARTIAL/FAILED + alert + last_run) |
| **D-106** | `active_agency_id` = SoT; no fallback `agency_ids[0]`; missing = errore |
| **D-107** | Errori API: `code` stabile BE + i18n FE; feedback se altera significato azione |
| **D-108** | Scheduling: un solo owner di esecuzione (cron = trigger/fallback) |
| **D-109** | Pricing SoT = `GET /billing/plans`; landing allineata o nascosta; legacy esplicito |
| **D-110** | Demo mode esplicito; `localStorage` ≠ entitlement authority |
| **D-111** | Cestino = stato non operativo (freeze); storico preservato |
| **D-112** | Seed demo idempotente e deterministico |
| **D-113** | Restore manuale testabile pre-GTM (non piattaforma DR) |
| **D-114** | Sostenibilità bak/media = priorità pre-attivazione; O0 = numeri+design vincolante |
| **D-115** | Programma O0…O6 approvato · **no self-serve finché O6 ≠ PASS** |
| **D-118** | **Audit Portale ImmobilCloud** · A–J GREEN + residuo codice CHIUSO · **MERGED su main** (PR #12 · 9-Ott-2026) · fascicolo `OMNIA_PORTALE_AUDIT_FASCICOLO.md` · residui P-021/P-026 |
| **D-116** | OpenAPI Catasto sandbox: **una sola API key** (`OPENAPI_API_KEY` + fallback `ADMIN_EMAIL`) |
| **D-145** | Primo cliente reale = **Nicastro Immobiliare** · seed demo **OFF** su Railway · retire `demo-agency-001` via Ops |
| **D-146** | **Vetrina www** istituzionale: Chi siamo · Perché OMNIA · Il vero lavoro · Prezzi · **no Cerca casa** in nav/CTA finale |
| **D-148** | **Paperless in Perché OMNIA** (4° tratto = documenti digitali): Fascicolo · modulistica PDF · kit dominio — **no** firma/PEC inventate; D-129 resta sulle 3 prove economiche |
| **D-147** | Kling micro-tour gestionale **30 crediti / €1,50** (SoT `CREDIT_COSTS`; Ken Burns B2C gratis) · gate pre-prod margini Visura/APE |

**SoT continuità:** `docs/audit/OMNIA_AUDIT_STATE.md` · `memory/NEXT_SESSION.md` · fascicolo D-118  

### Vetrina www (`LandingApp` · D-146 · 06-Nov-2026)

- **URL**: `https://omniarealestateecosystem.it/it` (Vercel FE · `frontend/src/apps/landing/LandingApp.jsx`).
- **Ruolo**: pitch Lab + Ecosystem (non è ImmobilCloud). Entry B2C ricerca casa = sotto-dominio/path cloud, non TopNav vetrina.
- **Nav**: Chi siamo (`#chi-siamo`) · Le tre anime (`#offerta`) · Perché OMNIA (`#perche`) · Prezzi (`#prezzi`) · Registrati. Sticky TopNav **fuori** dal wrapper `overflow-x-hidden` (altrimenti sticky spezzato → scroll “a metà”).
- **Ordine sezioni**: …anime → Perché OMNIA (tratti) → Il vero lavoro (`#vero-lavoro`, diagramma) → Prezzi → CTA «validazione» (solo Inizia ora).
- **Perché OMNIA (D-148)**: 4 tratti — ecosistema · mestiere · domain sovereignty · **documenti digitali (non cartacei)**. Listino Founders solo in `#prezzi`. Claim paperless = solo pezzi reali (Fascicolo, modulistica PDF, kit dominio); vietato firma live / PEC OMNIA / «100% paperless».
- **Box anime**: cloud→`/it/cloud` · crm→`/it/register` · academy→`/it/learn`.
- **Deploy**: `bash scripts/vercel-deploy.sh` (D-074).
- **HAL**: `api.www-vetrina-landing`.

**Sequenza priorità (D-099):** fascicolo → orphan → Bak+Restore → retention → costi.  
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

### D-153…D-161 — Cabina + registrazione gestionale (10–11-Nov-2026)

- **D-153**: Founder Ops ≠ CRM Nicastro (`active_agency_id` scollegato).
- **D-154/D-155**: Cabina `/app/ops` + kill-switch, impersonation, listino B2B, GDPR erase/offboard.
- **D-156/D-157** (storico): piano → KYC+Stripe → Attiva. *API=password superato da D-161.*
- **D-158**: Logo opzionale se sito/dominio; upload con preview blob.
- **D-159**: Register B2B richiede password (min 8).
- **D-160 / D-162 / D-163**: Niente mail a register; dopo KYC+pay Gemini confronta allegati → auto-Attiva + `agency_activated`, altrimenti `agency_pending` Ops.
- **D-164**: Stripe period su `items` + waiting poll `/billing/status` (senza webhook apply fallisce → niente auto-Attiva).
- **D-165**: CTA email Attiva = `enter_url` (login `?from=app&next=/…/dashboard`), non deep-link freddo (anti-403).
- **D-161**: **Password register = login definitivo**; Attiva → `agency_activated`; API keys solo da Impostazioni; forgot-password se non ricorda.
- **Cabina scheda**: checklist 3 passi (documenti → pagamento → attiva).
- **A-038** (aperta): Stripe sandbox ≠ FE italiana.
- SoT: `DECISIONS.md` · Cap.01 §1.2.0 · A-038 · `RIPRENDI_2026-11-11.md`.

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