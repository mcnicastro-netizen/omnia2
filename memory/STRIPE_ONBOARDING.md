# 💳 Stripe — Onboarding & Test Mode

**Stato**: ✅ Account Stripe **test** OMNIA collegato (chiavi in `backend/.env`, gitignored).  
**Modalità attiva OMNIA**: `test` — pagamenti simulati, nessun addebito reale.  
**Catalogo**: creato via `python -m apps.billing.setup_stripe` (idempotente).

### Decisione Founder 15-Sep-2026
- **Live + webhook**: configurare **solo dopo deploy su Vercel** (fine percorso).
- **Non** usare più Emergent come URL webhook / host produzione.
- Chiavi `pk_live` / `sk_live` (se già generate): restano dal Founder in password manager — **mai in chat / mai in git**.
- `whsec` live: si crea in Dashboard → Webhooks → endpoint pubblico post-Vercel  
  Target a regime: `https://api.omniarealestateecosystem.it/api/billing/webhook`  
  (oggi `api.` non up — non creare endpoint “a vuoto”).
- Fino ad allora: lasciare `STRIPE_MODE=test` e chiavi `*_test_*` in `.env` di sviluppo.

---

## Variabili `.env` (non committare)

```
STRIPE_ENABLED=true
STRIPE_MODE=test
STRIPE_PUBLISHABLE_KEY=pk_test_…
STRIPE_SECRET_KEY=sk_test_…
STRIPE_WEBHOOK_SECRET=whsec_…   # test / tunnel locale se serve
```

Webhook storico (dev tunnel Cloudflare — **obsoleto**, non riusare Emergent):  
documentato solo come riferimento; ricrea endpoint se serve di nuovo un tunnel di sviluppo.

Senza webhook, il frontend può comunque attivare il pagamento via polling `GET /api/billing/status/{session_id}` (fallback Stripe retrieve).

---

## Come attivare il **live mode** (DOPO Vercel — non ora)

1. Completa KYC / onboarding Stripe (dati, IBAN, documento) se non già fatto.
2. In Dashboard passa a **Live** e copia le chiavi live.
3. Deploy API su Vercel (+ DNS `api.` se previsto).
4. Crea Webhook endpoint → URL  
   `https://api.omniarealestateecosystem.it/api/billing/webhook`  
   (o URL Vercel API equivalente) → copia `whsec_…`.
5. Env produzione: `pk_live_…`, `sk_live_…`, `whsec_…`, `STRIPE_MODE=live`.
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
