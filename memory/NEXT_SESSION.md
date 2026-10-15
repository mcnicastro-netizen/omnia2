# Prossima sessione — programma passi

**Aggiornato**: 15 Ottobre 2026 — Planimetria B2C €12 live (OpenAPI + Stripe)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main` (dopo merge PR planimetria)

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| **Ultimo ship** | Planimetria B2C €12 · OpenAPI `elaborato_planimetrico` · SellPage link |
| **Stripe Test** | Railway `/api/billing/webhook` + Cloud auto-sync · no Emergent |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 |
| **Pricing B2C** | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) — planimetria €12 |

---

## ⏭️ Primo passo tipico

1. Collegare box residui SellPage: **APE** · **Accesso agli atti**
2. Verificare costo vivo OpenAPI esatto (€6,90+IVA?) in console partner
3. Smoke Founder: carta Test `4242…` su `/it/cloud/planimetria`
4. (Opz.) merge PR #41 prune Emergent + redeploy Vercel FE
5. Quando pronto: Stripe **Live**

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **Vault Environment omnia2** | `RAILWAY_TOKEN` · `RAILWAY_PROJECT_ID` · `OMNIA_API_PUBLIC_URL` · `VERCEL_PROJECT_ID` · `OPENAPI_*` |
| **Stripe webhook Test** | URL `OMNIA_API_PUBLIC_URL` + `/api/billing/webhook` |
| **Non toccare** | MX/TXT Resend · CNAME `api` Railway |
| **Stripe Live** | Solo dopo KYC + chiavi live |
| **Pre-demo probe** | `python scripts/pre_demo_probe.py` prima di ogni invio demo |

---

## Stato rapido

| Voce | Esito |
|--|--|
| S1–S10 | ✅ |
| D-124 home + valutatore | ✅ |
| Planimetria B2C €12 | ✅ (questo PR) |
| Box APE / Accesso atti | ⏳ |
| Stripe Live | ⏳ |
