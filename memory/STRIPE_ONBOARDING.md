# 💳 Stripe — Onboarding & Test Mode

**Stato**: ✅ Configurato in **test mode** con sandbox Emergent claimable.
**Scadenza sandbox**: 2026-09-27 (rinnovabile).
**Modalità**: `test` — pagamenti simulati, nessun addebito reale.

---

## Come attivare il **live mode** (quando pronto)

1. Vai al link di onboarding ricevuto dalla piattaforma:

   👉 **https://dashboard.stripe.com/onboard_sandbox/YWNjdF8xVHlYbEg1ZlRlVlZXZERmLDE3ODU5NDAxNzMv100yvn5ZYge**

2. Completa il modulo KYC di Stripe (dati personali, IBAN, documento d'identità).

3. Al termine, Stripe attiverà il tuo account.

4. Al primo re-deploy della piattaforma le chiavi TEST verranno **automaticamente** sostituite con le chiavi LIVE. Nessuna modifica di codice richiesta.

---

## Modalità fiscale selezionata

Al momento il checkout è in modalità **DIY (Stripe processa solo il pagamento, no gestione IVA)**.

Modalità disponibili quando andrai in live:
- **Stripe Managed Payments** (in ~80 paesi Italia inclusa): Stripe gestisce IVA, dichiarazioni, frodi, dispute — commissione ~3.5% invece del 1.9%. Ti raccomando questa modalità per lanciare senza pensieri.
- **Stripe Tax calculates only**: Stripe calcola IVA al checkout, tu presenti dichiarazioni. Commissione +0.5%.
- **DIY** (attuale): tu ti occupi di IVA e dichiarazioni. Solo pagamento.

Per switchare basta chiedermi "attiva Stripe Managed Payments" quando pronto.

---

## Test dei checkout (subito)

Con **modalità test attiva ora**, puoi testare l'intero flusso:

1. Login CRM come `mcnicastro@gmail.com`
2. Vai a **Settings → Billing** (quando la UI è pronta) oppure chiama direttamente:
   ```bash
   curl -X POST https://<preview>/api/billing/checkout \
     -H "Content-Type: application/json" \
     -H "Cookie: <auth-cookie>" \
     -d '{"plan_tier":"pro","billing_cycle":"monthly"}'
   ```
3. Vai all'URL restituito → carta di test:
   - **Numero**: `4242 4242 4242 4242`
   - **Scadenza**: qualsiasi futura
   - **CVC**: qualsiasi 3 cifre
4. Al completamento il webhook aggiorna il DB e attiva l'abbonamento

---

## Catalogo Stripe creato (idempotente)

| Prodotto | Lookup Key | Prezzo |
|---|---|---|
| Starter | `starter_monthly` / `starter_yearly` | €19/mese · €190/anno |
| Pro | `pro_monthly` / `pro_yearly` | €29/mese · €290/anno |
| Agency | `agency_monthly` / `agency_yearly` | €79/mese · €790/anno |
| Enterprise | `enterprise_monthly` / `enterprise_yearly` | €299/mese · €2990/anno |
| Pacchetto crediti 50 | `pkg_50` | €9 one-off |
| Pacchetto crediti 200 | `pkg_200` | €29 one-off |
| Pacchetto crediti 1000 | `pkg_1000` | €119 one-off |

Per aggiungere/modificare piani: modifica `apps/billing/plans.py` e rilancia `python -m apps.billing.setup_stripe`.

---

## Endpoint disponibili

| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/api/billing/plans` | Catalog pubblico |
| GET | `/api/billing/subscription` | Sub attuale dell'agenzia (auth) |
| POST | `/api/billing/checkout` | Crea Checkout Session subscription (auth) |
| POST | `/api/billing/credits/purchase` | Crea Checkout Session one-off crediti (auth) |
| POST | `/api/billing/portal` | Customer Portal self-service (auth) |
| GET | `/api/billing/status/{session_id}` | Polling stato sessione (pubblico, safe) |
| POST | `/api/billing/webhook` | Webhook Stripe (signature-verified) |

---

## Sicurezza

- ✅ Signature verification su webhook con `STRIPE_WEBHOOK_SECRET`
- ✅ Session insert PRIMA del redirect (`payment_transactions` collection)
- ✅ Webhook idempotente (guard `payment_status != paid`)
- ✅ Side-effect (grant crediti / attiva sub) sono re-applicabili senza duplicati
- ✅ Amounts server-side only (frontend invia solo `lookup_key`)
