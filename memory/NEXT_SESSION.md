# Prossima sessione — programma passi

**Aggiornato**: 15 Ottobre 2026 — webhook Stripe Emergent eliminati; ripresa programma D-124  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main`

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| **Ultimo ship** | **D-124** — home ecosistema · Valutatore UNI · promo documenti SellPage |
| **Stripe Test** | Solo Railway `/api/billing/webhook` + Cloud auto-sync · **no Emergent** |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 · `OMNIA_API_PUBLIC_URL` |
| **Vercel FE** | [`docs/ops/VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) — D-074 · `omnia-frontend` live |
| **DNS** | [`memory/DNS_SETUP_GUIDE.md`](./DNS_SETUP_GUIDE.md) — apex/www/app/cloud → Vercel · `api` → Railway |
| **Stripe** | [`memory/STRIPE_ONBOARDING.md`](./STRIPE_ONBOARDING.md) — Test → `api.…/billing/webhook` |

---

## ⏭️ Primo passo tipico (oggi)

1. **Collegare i 3 box** SellPage (`SellDocPromoRail`) alle pagine servizio:
   - Attestato APE
   - Planimetria catastale
   - Accesso agli atti  
2. Smoke Founder su `/it/` + `/it/cloud/account/sell` + `/it/cloud/valutatore`
3. (Opz.) redeploy Vercel FE dopo merge main
4. Quando pronto: Stripe **Live** webhook (non Test)

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
| Link box APE/planimetria/atti | ⏳ sessione successiva |
| Stripe Live | ⏳ |
| D-038 / S3.1 | ⏳ |
