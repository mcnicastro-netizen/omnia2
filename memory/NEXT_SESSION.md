# Prossima sessione — programma passi

**Aggiornato**: 20 Ottobre 2026 — **YouTrust sandbox reiniettata** (+ D-129/mandati in main)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch**: `main`

**YouTrust / Yousign**: vault Environment `YOUSIGN_API_KEY` + `ESIGN_PROVIDER=yousign` · smoke OTP **OK** 20-Ott · **scadenza key 25/10/2026** — rinnovare in console prima di quella data.

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| **Posizionamento** | **D-129** — Portale · Academy · Mandati (prove misurabili; no appiattimento) |
| **Ultimo ship** | Coda **Opportunità mandati** + `GET …/proof` · D-125…D-128 invariati |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) **v1.4** |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 |
| **Vercel FE** | [`docs/ops/VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) — D-074 |
| **Stripe** | [`memory/STRIPE_ONBOARDING.md`](./STRIPE_ONBOARDING.md) — Test webhook |

---

## ⏭️ Primo passo tipico (prove, non pitch)

1. **Pilota mandati** su `demo-agency-001`: annuncio privato approvato → match richiesta → UI `/app/mandate-opportunities` → avanzare funnel → leggere `/proof`
2. **Portale**: verificare KPI «Contatti portale (7gg)» + `pillars.portal` in proof
3. **Academy**: non claimare; solo sblocco M6 quando Founder riapre
4. Smoke B2C invariato: staging €1,49 · boost · slot · Stripe Test
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
