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

Dashboard Cursor → **Cloud Agents** → **Environments** → (questo env o meglio env omnia2) → **Secrets**

Dopo il Save, **riavvia un nuovo agent** sullo stesso environment (i secret non compaiono magicamente nel pod già aperto).

---

## Elenco (nomi solo) — dove recuperare il valore

| Nome secret | Obbligatorio? | Dove ritrovare il valore | A cosa serve |
|-------------|---------------|--------------------------|--------------|
| `RESEND_API_KEY` | **Sì** (mail demo/prod) | [Resend](https://resend.com/api-keys) → API Keys | Email transazionali |
| `GEMINI_API_KEY` | **Sì** (HAL/AI) | Google AI Studio / Google Cloud | LLM HAL, brand extract, coach |
| `FAL_KEY` | Consigliato | [fal.ai](https://fal.ai/dashboard/keys) | Staging / video |
| `TAVILY_API_KEY` | Opzionale | Tavily dashboard | AL Legal search |
| `STRIPE_SECRET_KEY` | Solo se billing ON | Stripe Dashboard → API keys (test/live) | Pagamenti |
| `STRIPE_PUBLISHABLE_KEY` | Solo se billing ON | Stripe | Frontend Stripe |
| `STRIPE_WEBHOOK_SECRET` | Solo se webhook | Stripe → Webhooks | Eventi Stripe |
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

**Stato 5 Ott 2026 (env omnia2, questo pod):** checklist 1–3 OK. `RESEND_API_KEY`, `GEMINI_API_KEY`, `FAL_KEY` presenti. Verifica: `bash scripts/check-secrets-presence.sh`. Valori mai in git/chat.  
