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
| `TAVILY_API_KEY` | Consigliato (HAL Legal) | [Tavily](https://tavily.com/) → API Keys | Ricerca fonti normative HAL Legal |
| `OPENAPI_EMAIL` | Per Visura sandbox | [console.openapi.com](https://console.openapi.com) → Autenticazione → email account | OAuth Catasto |
| `OPENAPI_API_KEY` | Per Visura sandbox | Stessa console → API Key **Sandbox** | OAuth Catasto (con EMAIL) |
| `OPENAPI_TOKEN` | Alternativa a EMAIL+KEY | Bearer già mintato (raro) | Skip OAuth |
| `OPENAPI_ENABLED` | `true` se Visura ON | Impostare `true` (anche in `.env`) | Abilita client catasto |
| `STRIPE_SECRET_KEY` | Solo se billing ON | Stripe Dashboard → API keys (test/live) | Pagamenti |
| `STRIPE_PUBLISHABLE_KEY` | Solo se billing ON | Stripe | Frontend Stripe |
| `STRIPE_WEBHOOK_SECRET` | Per effetti post-pagamento | Stripe → Developers → Webhooks → endpoint → Signing secret | Conferma pagamenti → boost/PDF/visura |
| `GOOGLE_CLIENT_ID` | Opzionale | Google Cloud Console → OAuth | Login Google |
| `JWT_SECRET` | Consigliato (prod) | Genera nuovo se perso (`openssl rand -hex 32`) | Sessioni; se cambi, tutti i login scadono |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Bootstrap | Non secret “API”: seed Founder; già in `.env.example` per Cloud | Utente super_admin |
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
3. [ ] Nuovo agent boot → `echo $RESEND_API_KEY | wc -c` > 0 (solo length)  
4. [ ] Mail non più in `[EMAIL MOCK]`  

---

## Stato verificato — 6 Ott 2026

Env omnia2, questa chat: `sk_test` / `pk_test` iniettati, `STRIPE_ENABLED=true`.  
`/api/billing/plans` → `enabled=true`, `mode=test`. Sandbox OK.  
Scripts env proposti per Save: `cloud-agent-install.sh` + `cloud-agent-start.sh`.
