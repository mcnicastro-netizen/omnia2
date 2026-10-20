# Prossima sessione — programma passi

**Aggiornato**: 20 Ottobre 2026 — **D-130 clone P0** + YouTrust sandbox (scadenza key **25/10/2026**)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Branch docs**: `main` (D-130 merged)

**YouTrust / Yousign**: vault Environment `YOUSIGN_API_KEY` + `ESIGN_PROVIDER=yousign` · smoke OTP OK 20-Ott · **scadenza key 25/10/2026** — rinnovare in console prima di quella data.

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

1. **Clone P0 (D-130)**: progettare/implementare pipeline URL → crawl → preview visitabile (home+lista+scheda) — non raffinare i 4 temi
2. **A-037 rampa**: chiudere almeno URL → demo vestita (tema + brand) se clone full slitta
3. Pilota mandati D-129 invariato su `demo-agency-001`
4. Smoke B2C: staging €1,49 · boost · slot · Stripe Test
5. Quando pronto: Stripe **Live** webhook (non Test)

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **D-130** | Vietato promettere «cloniamo il sito» finché preview clone non esiste |
| **D-023** | Decisione clone ancora valida; codice incompleto (solo Brand Extractor) |
| **YouTrust key** | Scadenza sandbox **25/10/2026** — rinnovare o firma torna mock |
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
