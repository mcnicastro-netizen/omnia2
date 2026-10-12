# Prossima sessione — programma passi

**Aggiornato**: 12 Ottobre 2026 — **go-live D-123 + D-074** (API `api.` + Vercel FE + DNS)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main`

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 · `OMNIA_API_PUBLIC_URL` |
| **Vercel FE** | [`docs/ops/VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) — D-074 · `omnia-frontend` live |
| **DNS** | [`memory/DNS_SETUP_GUIDE.md`](./DNS_SETUP_GUIDE.md) — apex/www/app/cloud → Vercel · `api` → Railway |
| **Stripe** | [`memory/STRIPE_ONBOARDING.md`](./STRIPE_ONBOARDING.md) — Test → `api.…/billing/webhook` |

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **Vault Environment omnia2** | `RAILWAY_TOKEN` · `RAILWAY_PROJECT_ID` · `OMNIA_API_PUBLIC_URL=`OMNIA_API_PUBLIC_URL`` (solo URL) · `VERCEL_PROJECT_ID=`VERCEL_PROJECT_ID` (vault)` |
| **Stripe webhook Test** | URL ``OMNIA_API_PUBLIC_URL` + `/api/billing/webhook`` · `whsec` su Variables Railway |
| **Non toccare** | MX/TXT Resend · CNAME `api` Railway |
| **Stripe Live** | Solo dopo KYC + chiavi live (non ora) |
| **Pre-demo probe** | `python scripts/pre_demo_probe.py` prima di ogni invio demo |

---

## Prossimo passo tipico

1. Smoke Founder su domini pubblici (login demo)  
2. (Opz.) collegare Git → Vercel per redeploy automatici  
3. Quando pronto: Stripe **Live** webhook (non Test)  
4. Cluster residui prodotto (D-038 / S3.1, ecc.)

---

## Stato rapido

| Voce | Esito |
|--|--|
| S1–S10 | ✅ |
| **D-123 Railway API + DNS `api.`** | ✅ smoke health 200 |
| **Stripe webhook Test → `api.`** | ✅ |
| **D-074 Vercel + DNS FE** | ✅ apex/www/app/cloud 200 |
| **D-122 pre-demo ≥8** | ✅ |
| Stripe Live | ⏳ |
| D-038 / S3.1 | ⏳ |
