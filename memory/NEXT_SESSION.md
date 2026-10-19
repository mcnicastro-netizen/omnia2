# Prossima sessione — programma passi

**Aggiornato**: 19 Ottobre 2026 — **D-125/D-128 + listino B2C v1.4 + privati/boost**  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch merge**: `cursor/private-listings-audit-8e9b` → `cursor/staging-quality-v2-8e9b` → `main` (Founder «mergera»)

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| **Ultimo ship** | **D-125** Accesso atti · **D-126** match privati · **D-127** boost densità · **D-128** staging €1,49 Nano Banana |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) **v1.4** |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 |
| **Vercel FE** | [`docs/ops/VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) — D-074 |
| **Stripe** | [`memory/STRIPE_ONBOARDING.md`](./STRIPE_ONBOARDING.md) — Test webhook |

---

## ⏭️ Primo passo tipico

1. **HAL reindex** post-merge: `POST /api/app/hal/knowledge/reindex?force=true` (super_admin)
2. Collegare i 3 box SellPage alle pagine servizio (APE / planimetria / atti) — atti resta «Presto disponibile» finché partner D-125
3. Merge/cablaggio Nano Banana da `cursor/staging-agent-specialized-8e9b` se non già in main
4. Smoke Founder: Sell staging €1,49 · boost · slot dal 3° · messaggi di attesa
5. Quando pronto: Stripe **Live** webhook (non Test)

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **D-125** | Accesso atti = progetto comunale · no wallet |
| **D-128** | Staging B2C €1,49 (ex citazione errata «D-125») |
| **HAL reindex** | Obbligatorio dopo merge Cap.9/18 |
| **Stripe Live** | Solo dopo KYC |
| **Pre-demo probe** | `python scripts/pre_demo_probe.py` |

---

## Stato rapido

| Voce | Esito |
|--|--|
| S1–S10 | ✅ |
| D-124 home + valuator + Sell promo | ✅ |
| D-125 Accesso atti (decisione) | ✅ registrata · prodotto ⏳ partner |
| D-126 match privati → CRM | ✅ |
| D-127 boost + densità 50% | ✅ |
| D-128 staging €1,49 Nano Banana | ✅ listino SoT · pipeline branch staging-agent |
| PRICING_B2C v1.4 | ✅ |
| Link box APE/planimetria/atti | ⏳ |
| Stripe Live | ⏳ |
