# 💳 Stripe — Onboarding & Test Mode

**Stato**: ✅ Account Stripe **test** OMNIA collegato.  
**Modalità attiva OMNIA**: `test` — pagamenti simulati, nessun addebito reale.  
**Catalogo**: creato via `python -m apps.billing.setup_stripe` (idempotente).  
**Webhook sandbox → `api.omnia…`**: ✅ (12-Ott-2026) — vedi sotto.

### Decisione Founder 15-Sep-2026 (+ update 12-Ott-2026)
- **Live + webhook live**: solo dopo FE Vercel + DNS `api.` a regime.
- **Non** usare Emergent come URL webhook / host (`…emergentagent.com/api/stripe/webhook` = morto; path errato oltre tutto).
- Path webhook OMNIA (sempre): `/api/billing/webhook` (mai `/api/stripe/webhook`).
- Chiavi `pk_live` / `sk_live`: password manager — **mai in chat / mai in git**.
- Fino al live: `sk_test_` / `pk_test_` + webhook **Test**.

### Webhook Test → Railway (12-Ott-2026)

| Campo | Valore |
|-------|--------|
| Destinazione | `OMNIA Railway API (sandbox)` (`we_1UPksi5fTeVVWdDf21htElsf`) |
| Descrizione | `OMNIA Railway API (sandbox)` |
| URL | `https://omnia-api-production-2cec.up.railway.app/api/billing/webhook` |
| Secret | Variable Railway `STRIPE_WEBHOOK_SECRET` = `whsec_…` di **questa** destinazione |
| Smoke | `stripe trigger checkout.session.completed` → consegna **200 OK** |

**Due destinazioni Test possibili:**
1. **Railway** (stabile) — descrizione `OMNIA Railway API (sandbox)` — **non** toccare da `sync-stripe-webhook-url.py`.
2. **Cloud tunnel** (efimero) — descrizione esatta `OMNIA Cloud Agent portal (auto-sync)` — aggiornata dal boot Cloud verso `*.trycloudflare.com`.

Ogni destinazione ha il **suo** `whsec_`. Railway Variables ≠ vault Cloud se gli endpoint sono due.

DNS `api.` live (12-Ott-2026): URL aggiornato a ``OMNIA_API_PUBLIC_URL` + `/api/billing/webhook`` + `whsec_` su Variable Railway.

### Cleanup Emergent (15-Ott-2026)

Stripe ha segnalato 404 su endpoint legacy:
- `https://omnia-real-estate-1.preview.emergentagent.com/api/stripe/webhook`
- (gemello) `https://omnia-crm-docs.preview.emergentagent.com/api/stripe/webhook`

**Azione**: eliminati dalla Dashboard Test. Path sbagliato (`/api/stripe/webhook`) + host Emergent morto.  
`scripts/sync-stripe-webhook-url.py` ora **prune** automatico di URL `emergentagent.com` o path `/api/stripe/webhook` a ogni sync Cloud.

---

## Variabili `.env` / vault (non committare)

```
STRIPE_ENABLED=true
STRIPE_MODE=test
STRIPE_PUBLISHABLE_KEY=pk_test_…
STRIPE_SECRET_KEY=sk_test_…
STRIPE_WEBHOOK_SECRET=whsec_…   # matching dell'endpoint che riceve (Railway o tunnel)
```

Senza webhook, il frontend può comunque attivare il pagamento via polling `GET /api/billing/status/{session_id}` (fallback Stripe retrieve).

---

## Come attivare il **live mode** (DOPO Vercel — non ora)

1. Completa KYC / onboarding Stripe (dati, IBAN, documento) se non già fatto.
2. In Dashboard passa a **Live** e copia le chiavi live.
3. API già su Railway + DNS `api.` (+ FE Vercel).
4. Crea Webhook endpoint **Live** → URL  
   ``OMNIA_API_PUBLIC_URL` + `/api/billing/webhook`` → copia `whsec_…`.
5. Env produzione Railway: `pk_live_…`, `sk_live_…`, `whsec_…` (e spegni test-only dove serve).
6. Rilancia `python -m apps.billing.setup_stripe` sul catalogo live.
7. Solo allora «vai» su **A-014** se serve UI/listino residuo.

---

## Modalità fiscale

Checkout attuale: **DIY** (Stripe processa il pagamento, IVA gestita da OMNIA).

Opzioni future: Stripe Managed Payments · Stripe Tax · DIY.

---

## Onboarding commerciale

**Demo guidata → abbonamento** (D-080). Nessun trial Stripe self-serve.

---

## Test dei checkout

1. Login come admin di agenzia (es. `demo.admin@omniaecosystem.it`)
2. **Impostazioni → Piano & Crediti**, oppure:
   ```bash
   curl -X POST http://127.0.0.1:43121/api/billing/checkout \
     -H "Content-Type: application/json" -b cookies.txt \
     -d '{"plan_tier":"starter","billing_cycle":"monthly"}'
   ```
3. Carta test: `4242 4242 4242 4242` · scadenza futura · CVC qualsiasi
4. Webhook o polling status aggiornano abbonamento / crediti

---

## Catalogo Stripe (listino Founders — 5 Ago 2026)

| Prodotto | Lookup Key | Prezzo |
|---|---|---|
| Starter | `starter_monthly` / `starter_yearly` | €49/mese · €539/anno (−1 mese) |
| Pro | `pro_monthly` / `pro_yearly` | €99/mese · €1.089/anno |
| Agency | `agency_monthly` / `agency_yearly` | €299/mese · €3.289/anno |
| Crediti 400 | `pkg_400` | €20 |
| Crediti 1000 | `pkg_1000` | €50 |
| Crediti 2000 | `pkg_2000` | €100 |
| Crediti 5000 | `pkg_5000` | €250 |
| Crediti 10000 | `pkg_10000` | €500 |
| Crediti 20000 | `pkg_20000` | €1000 |

Ratio crediti: **€0,05 / credito** (20 crediti / €).

Per modificare piani: `apps/billing/plans.py` → `python -m apps.billing.setup_stripe`.

---

## Endpoint

| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/api/billing/plans` | Catalog pubblico (+ `publishable_key`) |
| GET | `/api/billing/subscription` | Sub attuale agenzia |
| POST | `/api/billing/checkout` | Checkout subscription |
| POST | `/api/billing/credits/purchase` | Checkout one-off crediti |
| POST | `/api/billing/portal` | Customer Portal |
| GET | `/api/billing/status/{session_id}` | Polling stato (auth) |
| POST | `/api/billing/webhook` | Webhook Stripe (signature-verified) |

---

## Sicurezza

- Signature verification webhook con `STRIPE_WEBHOOK_SECRET`
- Session insert PRIMA del redirect (`payment_transactions`)
- Webhook idempotente (`payment_status != paid`)
- Importi solo server-side (FE manda `plan_tier` / `package_key`)
