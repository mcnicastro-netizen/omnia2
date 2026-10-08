# Inventario Secrets Cloud Agent — OMNIA (solo NOMI)

**Politica SoT (obbligatoria)**: `memory/INTEGRITY_AND_SECRETS.md`  
→ Codice = github/main. API key = password manager + console provider. Cursor = solo *copia* di iniezione.

**Perché esiste questo file**: i Secrets Cursor sono **per environment**.  
Un **New Project** / repo Origin-tmp apre un vault **vuoto** → in UI vedi solo `GITHUB_TOKEN` (iniettato dalla piattaforma).  
**I valori non sono cancellati** dalle console: resta perso solo il collegamento a *questo* vault. Non vanno mai in git né in chat.

**Regola Founder**: per OMNIA avvia sempre l’agent su `github.com/mcnicastro-netizen/omnia2`.  
Non usare New Project per continuare lavoro prodotto.

---

## Dove reiniettare

Dashboard Cursor → **Cloud Agents** → Environments → env **omnia2** → **Secrets**  
(preferire scope **Environment**; evitare doppioni con My Secrets / Personal sullo stesso nome)

Nomi obbligatori (env var, niente italiano/spazi):
`STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_ENABLED=true` (+ opzionale `STRIPE_WEBHOOK_SECRET`).

**Audit Portale Onda C (8 Ott 2026)**: il vault env omnia2 aveva iniettato solo  
`FAL_KEY`, `GEMINI_API_KEY`, `RESEND_API_KEY`, `STRIPE_ENABLED` — **mancavano** Stripe sk/pk/whsec e tutta la famiglia OpenAPI (erano solo su `backend/.env` disk).  
Reiniettare i nomi sotto «Elenco» + sezione OpenAPI; poi nuovo agent boot. Dettaglio: `docs/audit/portale-matrici/2026-10-08-onda-c.md`.

Dopo il Save, **riavvia un nuovo agent** sullo stesso environment (i secret non compaiono magicamente nel pod già aperto).

**Trappola fixata (Ott 2026)**: `backend/.env` template ha `STRIPE_ENABLED=false`. Prima `load_dotenv(override=True)` **cancellava** il vault. Ora `shared/env_bootstrap.py` + `scripts/stripe-vault-materialize.py` fanno vincere i secret iniettati; con `sk_test_…` la sandbox si auto-abilita.

**Hardening**: wipe Stripe da `.env` a ogni boot (niente live stale su warm disk); preferisci qualsiasi valore `sk_test_`/`pk_test_` presente nel process env anche se lo slot canonico ha ancora `sk_live_`; **non** reimportare `STRIPE_*` da `.env` nel process. Attivazione one-shot: `bash scripts/activate-stripe-sandbox.sh`.

---

## Elenco (nomi solo) — dove recuperare il valore

| Nome secret | Obbligatorio? | Dove ritrovare il valore | A cosa serve |
|-------------|---------------|--------------------------|--------------|
| `RESEND_API_KEY` | **Sì** (mail demo/prod) | [Resend](https://resend.com/api-keys) → API Keys | Email transazionali |
| `GEMINI_API_KEY` | **Sì** (HAL/AI) | Google AI Studio / Google Cloud | LLM HAL, brand extract, coach |
| `FAL_KEY` | Consigliato | [fal.ai](https://fal.ai/dashboard/keys) | Staging / video |
| `TAVILY_API_KEY` | Opzionale | Tavily dashboard | AL Legal search |
| `STRIPE_SECRET_KEY` | **Sì** se billing ON | Stripe Dashboard → API keys (**test** in Cloud) | Pagamenti B2B/B2C |
| `STRIPE_PUBLISHABLE_KEY` | **Sì** se billing ON | Stripe | Plans API / Stripe.js |
| `STRIPE_WEBHOOK_SECRET` | **Sì** se webhook | Stripe → Webhooks (endpoint = tunnel + `/api/billing/webhook`) | Eventi Stripe |
| `STRIPE_ENABLED` | **Sì** `=true` sandbox | Vault / env | Gate billing |
| `OPENAPI_ENABLED` | **Sì** Visura PDF | `true` | Feature flag; host default sandbox finché `OPENAPI_MODE≠live` |
| `OPENAPI_API_KEY` | **Sì** Visura sandbox | Console OpenAPI.it (Sandbox) | OAuth; **basta questa key** + enabled (D-116); email = `OPENAPI_EMAIL` o `ADMIN_EMAIL` |
| `OPENAPI_EMAIL` | Solo se ≠ ADMIN | Console OpenAPI.it | Opzionale in sandbox se `ADMIN_EMAIL` = account console |
| `OPENAPI_TOKEN` | Opz. alt. a email+key | Console OpenAPI.it | Bearer statico |
| `OPENAPI_CATASTO_BASE` | Consigliato sandbox | es. `https://test.catasto.openapi.it` | Host Catasto |
| `OPENAPI_OAUTH_BASE` | Consigliato sandbox | es. `https://test.oauth.openapi.com` | Host OAuth |
| `GOOGLE_CLIENT_ID` | Opzionale | Google Cloud Console → OAuth | Login Google |
| `JWT_SECRET` | Consigliato (prod) | Genera nuovo se perso (`openssl rand -hex 32`) | Sessioni; se cambi, tutti i login scadono |
| `FRONTEND_BASE_URL` | Dogfood tunnel | URL pubblico preview/tunnel (non `127.0.0.1`) | Link in email alert/lead |
| `FRONTEND_URL` | Dogfood tunnel | idem | Welcome / reset password |
| `OMNIA_PUBLIC_URL` | Consigliato | idem | Asset/link email |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Bootstrap | Non secret “API”: seed Founder; già in `.env.example` per Cloud | Utente super_admin (+ fallback OAuth OpenAPI D-116) |
| `DEMO_ADMIN_PASSWORD` | Bootstrap | `.env.example` | Demo agency_admin |
| `GITHUB_TOKEN` | Auto | Lo mette Cursor — **non** è il vault OMNIA | Push git |

Alias legacy accettati dal backend (se li avevi): `GOOGLE_API_KEY`, `EMERGENT_LLM_KEY` (mirror Gemini).

---

## Cosa NON fare

- Non committare valori in `backend/.env`, script, PR, chat  
- Non copiare secret da un environment all’altro **in chiaro in chat**  
- Non considerare “perso” un secret solo perché il **pod nuovo** non lo vede  

---

## Checklist rapida dopo un env nuovo

1. [ ] Conferma environment = **omnia2** (non `tmp-…`)  
2. [ ] Secrets UI ha almeno `RESEND_API_KEY` + `GEMINI_API_KEY`  
3. [ ] + billing: `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` / `STRIPE_ENABLED` / `STRIPE_WEBHOOK_SECRET`  
4. [ ] + Visura: `OPENAPI_ENABLED` + `OPENAPI_EMAIL` + `OPENAPI_API_KEY` (+ base sandbox)  
5. [ ] Nuovo agent boot → `bash scripts/check-secrets-presence.sh` OK  
6. [ ] Mail non più in `[EMAIL MOCK]` · plans `enabled=true` `mode=test`  

---

## Stato verificato — 6 Ott 2026

Env omnia2, questa chat: `sk_test` / `pk_test` iniettati, `STRIPE_ENABLED=true`.  
`/api/billing/plans` → `enabled=true`, `mode=test`. Sandbox OK.  
Scripts env proposti per Save: `cloud-agent-install.sh` + `cloud-agent-start.sh`.

## Stato verificato — 8 Ott 2026 (Onda C)

| Check | Esito |
|--|--|
| Vault inject list | solo 4 nomi → **Save Secrets richiesto** (UI) |
| Boot auto | `stripe-vault-materialize` (+OPENAPI) · `sync-public-base-url` · `sync-stripe-webhook-url` |
| `/api/billing/plans` | `enabled=true` `mode=test` |
| Visura catalog | `openapi_enabled=true` `stripe_enabled=true` |
| FE build | same-origin `/api` (no localhost bake) |
| `FRONTEND_*` | sync → trycloudflare · `get_public_base_url()` |

## Stato verificato — 8 Ott 2026 sera (chat «controllo secrets»)

Founder ha salvato i secret Environment su omnia2. Nuovo agent vede Stripe + OpenAPI inject.

| Alert | Azione |
|--|--|
| Stripe inject **`sk_live` / `pk_live`** | **Sostituire** subito con `sk_test_` / `pk_test_` (+ webhook `whsec` **test**) |
| `STRIPE_MODE` | non obbligatorio in vault |
| `OPENAPI_EMAIL` | aggiungere (OAuth con API key) |
| OpenAPI.it **Catasto sospeso dal provider** | Visura dogfood = **SKIP** finché riattivano; non è bug OMNIA |
| `JWT_SECRET` | evitare placeholder `change-me-…` — mettere valore reale in vault |
| SoT sessione vault | chat **controllo secrets** (inject fresco); questa linea audit resta storica |

---

## ID `bld-…` (Environment Builds) — 7 Ott 2026

Esempio UI chat: `bld-20261007-349ad6c9-7db4-471c-af4e-2ea4fea82e8e`.

| Domanda | Risposta |
|--|--|
| È un secret? | **No** |
| Devo salvarlo nel password manager? | **No** — Cursor lo tiene in Dashboard → Environments → Builds |
| A cosa serve? | Snapshot install dell’env omnia2 (SUCCEEDED = build sano) |
| Quando annotarlo? | Solo pin/debug/supporto di *quel* snapshot |
| Sostituisce le API key? | **No** — vault invariato |

HAL: `api.cloud-environment-builds`.
