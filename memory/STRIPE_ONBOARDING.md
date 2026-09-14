# 💳 Stripe — Onboarding & Test Mode

**Stato**: ✅ Account Stripe **test** OMNIA collegato (chiavi in `backend/.env`, gitignored).
**Modalità**: `test` — pagamenti simulati, nessun addebito reale.
**Catalogo**: creato via `python -m apps.billing.setup_stripe` (idempotente).

---

## Variabili `.env` (non committare)

```
STRIPE_ENABLED=true
STRIPE_MODE=test
STRIPE_PUBLISHABLE_KEY=pk_test_…
STRIPE_SECRET_KEY=sk_test_…
STRIPE_WEBHOOK_SECRET=whsec_…
```

Webhook attuale (dev tunnel):  
`https://icons-rid-pontiac-messages.trycloudflare.com/api/billing/webhook`  
Se il tunnel Cloudflare cambia URL, ricrea l’endpoint in Stripe Dashboard (o via API) e aggiorna `STRIPE_WEBHOOK_SECRET`.

Senza webhook, il frontend può comunque attivare il pagamento via polling `GET /api/billing/status/{session_id}` (fallback Stripe retrieve).

---

## Come attivare il **live mode** (quando pronto)

1. Completa KYC / onboarding Stripe (dati, IBAN, documento).
2. In Dashboard passa a **Live** e copia le chiavi live.
3. Sostituisci in `.env`: `pk_live_…`, `sk_live_…`, webhook live `whsec_…`, `STRIPE_MODE=live`.
4. Rilancia `python -m apps.billing.setup_stripe` sul catalogo live.
5. Punta il webhook live all’URL pubblico di produzione `/api/billing/webhook`.

---

## Modalità fiscale

Checkout attuale: **DIY** (Stripe processa il pagamento, IVA gestita da OMNIA).

Opzioni future: Stripe Managed Payments · Stripe Tax · DIY.

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
| Starter | `starter_monthly` / `starter_yearly` | €49/mese · €490/anno |
| Pro | `pro_monthly` / `pro_yearly` | €99/mese · €990/anno |
| Agency | `agency_monthly` / `agency_yearly` | €249/mese · €2490/anno |
| Enterprise | `enterprise_monthly` / `enterprise_yearly` | €299/mese · €2990/anno |
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
