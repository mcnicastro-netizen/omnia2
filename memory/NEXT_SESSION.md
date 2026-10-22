# Prossima sessione — programma passi

**Aggiornato**: 22 Ottobre 2026 — **P0 Railway security: rotazione credenziali**  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch docs**: `main`

**🔴 P0 sicurezza**: mail Railway 22-Ott — possibile leak Variables. Runbook: [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md).  
Ruotare prima di ogni altra feature. Build Railway possono essere bloccate (status.railway.com).

**YouTrust / Yousign**: ruotare `YOUSIGN_API_KEY` **ora** (incidente + scadenza ~25/10).

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| **Posizionamento** | **D-129** — Portale · Academy · Mandati |
| **P0 sito** | **D-130 / D-023** — Clone-from-URL (pari gravità VS) · A-037 = rampa demo |
| Listino B2B | [`memory/PRICING_OMNIA.md`](./PRICING_OMNIA.md) — **no SKU solo sito** |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) **v1.4** |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 |
| **Vercel FE** | [`docs/ops/VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) — D-074 |
| **Stripe** | [`memory/STRIPE_ONBOARDING.md`](./STRIPE_ONBOARDING.md) — Test webhook |

---

## ⏭️ Primo passo tipico

1. **Rotazione Railway** (P0): revoca key provider → Variables `omnia-api` → vault Cursor omnia2 → smoke health/webhook
2. Solo dopo: Clone P0 (D-130) / A-037 / pilota mandati / Stripe Live

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **Railway leak** | Rotare Stripe/Gemini/fal/Resend/OpenAPI/YouTrust/JWT/Mongo/RAILWAY_TOKEN |
| **D-130** | Vietato promettere «cloniamo il sito» finché preview clone non esiste |
| **D-023** | Decisione clone ancora valida; codice incompleto (solo Brand Extractor) |
| **YouTrust key** | Ruotare ora (incidente Railway + scadenza ~25/10) |
| **D-125** | Accesso atti = progetto comunale · no wallet |
| **D-128** | Staging B2C €1,49 |
| **HAL reindex** | Dopo merge Cap.8 / YAML sito |
| **Stripe Live** | Solo dopo KYC |
| **Pre-demo probe** | `python scripts/pre_demo_probe.py` |

---

## Stato rapido

| Voce | Esito |
|--|--|
| S1–S10 | ✅ |
| D-124…D-129 | ✅ registrati |
| D-130 clone P0 + no solo-sito | ✅ decisione · codice ⏳ |
| A-037 demo da sito | 🟠 aperta (sotto D-130) |
| YouTrust sandbox vault | ⚠️ key fino al 25/10 |
| Link box APE/planimetria/atti | ⏳ |
| Stripe Live | ⏳ |
