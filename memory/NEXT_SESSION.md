# Prossima sessione — programma passi

**Aggiornato**: 15 Ottobre 2026 — **D-125** Accesso atti (no wallet; box spento)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main`

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| **Ultimo ship** | **D-124** — home ecosistema · Valutatore UNI · promo documenti SellPage |
| **D-125** | Accesso atti = copia progetto comunale · no wallet · attesa partner a consumo |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 · `OMNIA_API_PUBLIC_URL` |
| **Vercel FE** | [`docs/ops/VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) — D-074 · `omnia-frontend` live |
| **DNS** | [`memory/DNS_SETUP_GUIDE.md`](./DNS_SETUP_GUIDE.md) — apex/www/app/cloud → Vercel · `api` → Railway |
| **Stripe** | [`memory/STRIPE_ONBOARDING.md`](./STRIPE_ONBOARDING.md) — Test → `api.…/billing/webhook` |

---

## ⏭️ Primo passo tipico

1. **Founder**: inviare email Pratiche.it + PraticheCasa — accordo a consumo senza wallet; poi ship SKU Accesso atti
2. Collegare box residui SellPage: **APE** · **Planimetria** (Accesso atti resta «Presto disponibile» finché D-125 ha partner)
3. Smoke Founder su `/it/` + `/it/cloud/account/sell` + `/it/cloud/valutatore`
4. (Opz.) redeploy Vercel FE dopo merge main
5. Quando pronto: Stripe **Live** webhook (non Test)

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **Vault Environment omnia2** | `RAILWAY_TOKEN` · `RAILWAY_PROJECT_ID` · `OMNIA_API_PUBLIC_URL` · `VERCEL_PROJECT_ID` |
| **Stripe webhook Test** | URL `OMNIA_API_PUBLIC_URL` + `/api/billing/webhook` · `whsec` su Variables Railway |
| **Non toccare** | MX/TXT Resend · CNAME `api` Railway |
| **Stripe Live** | Solo dopo KYC + chiavi live (non ora) |
| **Pre-demo probe** | `python scripts/pre_demo_probe.py` prima di ogni invio demo |
| **HAL reindex** | Post-merge: `POST /api/app/hal/knowledge/reindex?force=true` (super_admin) se non già fatto |

---

## Stato rapido

| Voce | Esito |
|--|--|
| S1–S10 | ✅ |
| **D-123 Railway API + DNS `api.`** | ✅ |
| **D-074 Vercel + DNS FE** | ✅ |
| **D-122 pre-demo ≥8** | ✅ |
| **D-124 home + valutatore + Sell promo** | ✅ merge PR #40 |
| Link box APE / planimetria | ⏳ |
| Accesso atti (D-125) | ⏳ partner a consumo (no wallet) · box spento |
| Stripe Live | ⏳ |
| D-038 / S3.1 | ⏳ |
