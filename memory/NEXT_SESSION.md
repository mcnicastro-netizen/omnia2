# Prossima sessione — programma passi

**Aggiornato**: 7 Ottobre 2026 · **Pausa** dopo dogfood B2C + secret sandbox in-pod  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch lavoro**: `cursor/e2e-dogfood-results-cc7d` · PR #6  
**Chat SoT**: questa chat (stesso thread — non aprire decine di new chat per secret sandbox)

---

## ▶️ Da dove ricominciamo (ordine)

1. **Webhook Stripe → questo tunnel**  
   - URL attuale: `/tmp/omnia-stack/SHARE_URL.txt` + path `/api/billing/webhook`  
   - Secret: `STRIPE_WEBHOOK_SECRET` (`whsec_…`) — incolla in chat (demo) o Environment Secrets  
   - Evento: `checkout.session.completed`  
   - Smoke: paga Boost o HAL €1 → vedi entitlement / PDF / boost attivo

2. **Dogfood chiusura strumenti B2C** (con OpenAPI + Tavily già in questo pod)  
   - Visura €4,90 end-to-end (checkout → webhook → PDF)  
   - HAL Legal: paga €1 → domanda con fonti Tavily  
   - Conferma label nav **Account** (fix già shippato)

3. **Persistenza secret (quando hai 2 minuti, non bloccante)**  
   - Copiare in Environment Secrets omnia2: `OPENAPI_*`, `TAVILY_API_KEY`, `STRIPE_WEBHOOK_SECRET`  
   - Così un reboot agent non richiede re-incolla

4. **Solo dopo**: restore firmato O3b → poi self-serve O6 / A-037 come da programma

---

## ✅ Stato chiuso in questa sessione (7 Ott)

| Area | Esito |
|--|--|
| Dogfood E2E (billing → B2C annuncio → nuova agenzia → API keys) | PASS |
| Stripe sandbox Cloud (`sk_test`) | PASS |
| Paywall HAL Legal €1 B2C (API 402 + CTA UI) | SHIPPATO |
| Fix UI `CLOUD.NAV_ACCOUNT` → «Account» | SHIPPATO |
| OpenAPI Catasto sandbox (OAuth + `openapi_enabled=true`) | OK **in questo pod** (chiave demo in `.env` locale) |
| Tavily `tvly-dev-` (search 200) | OK **in questo pod** |
| Webhook Stripe post-pay (boost/PDF/visura/HAL) | ⏳ **prossimo** |
| O6 self-serve pagamento pubblico | OFF (invariato) |

### Tabella strumenti B2C (aggiornata)

| Strumento | Esito | Nota |
|--|--|--|
| Boost Vetrina | PASS checkout | Effetto post-pay → webhook |
| Virtual staging | PASS checkout | Serve ≥1 foto |
| Valutatore gratis | PASS | Email verificata; 1/anno |
| Valutatore UNI €2,99 | PASS checkout | PDF → webhook |
| Visura €4,90 | Provider ON (pod) | E2E PDF dopo webhook |
| HAL Legal | Paywall ON + Tavily ON (pod) | E2E domanda dopo pay+webhook |
| Mutui | PASS | Gratis |

CRM pubblico: `/tmp/omnia-stack/CRM_LOGIN_URL.txt` (tunnel trycloudflare si rinnova).

---

## 🎯 Demo Nicastroimmobiliare — ambiente pronto

| | |
|--|--|
| **CRM login** | `/tmp/omnia-stack/CRM_LOGIN_URL.txt` |
| **Locale** | http://127.0.0.1:43123/it/login |
| **Email** | `titolare@nicastroimmobiliare.it` |
| **Password** | `NicastroDemo2026!` (override: `NICASTRO_ADMIN_PASSWORD`) |
| **Agenzia** | `nicastro-agency-001` · slug `nicastroimmobiliare` |

### Limiti onesti
- Clone automatico sito **non** live (A-037)  
- Self-serve Stripe prodotto **OFF** finché O6 ≠ PASS  
- Secret sandbox in-pod **non** sopravvivono a wipe/reboot senza Environment Secrets  
- Inventario nomi: `memory/CLOUD_SECRETS_INVENTORY.md`

---

## Continuità SoT

| | |
|--|--|
| **Programma** | `docs/audit/OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md` |
| **O6 gate** | `docs/audit/OMNIA_O6_GATE_CHECKLIST.md` — CONDITIONAL PASS |
| **Restore** | `docs/ops/RESTORE_MANUAL.md` — run firmata ⏳ |
| **Priorità prodotto** | **A-037** dopo chiusura dogfood webhook |
| **Manuale sync** | Cap. 19 §19.10.6–7 · Cap. 22 v1.1 · HAL `api.stripe-webhook-b2c` / `api.openapi-catasto-sandbox` / `api.tavily-hal-legal` / `legal.paywall-b2c` |
| Regola | **Nessun self-serve finché O6 ≠ PASS** · **no push `main` senza ok Founder** |
