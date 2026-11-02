# Prossima sessione — programma passi

**Aggiornato**: 02 Novembre 2026 — **D-135** dogfood B2C Vendi (CSRF · HAL · account)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault scope: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md) — Personal vs Environment.  
**Email**: [`memory/RESEND_DOMAIN_GUIDE.md`](./RESEND_DOMAIN_GUIDE.md) — D-132 mittente `info@omniarealestateecosystem.it` live.  
**Google**: [`memory/GOOGLE_AUTH.md`](./GOOGLE_AUTH.md) — D-134 Client ID Web live.

**Prompt primo messaggio nuovo agent**: vedi [`docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md`](../docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md).

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) — S1–S10 ✅ |
| **Posizionamento** | **D-129** — Portale · Academy · Mandati |
| **P0 sito** | **D-130 / D-023** — Clone-from-URL · A-037 rampa demo |
| **Sicurezza** | Rotazione Railway 22-Ott (residui sotto) |
| Listino B2B | [`memory/PRICING_OMNIA.md`](./PRICING_OMNIA.md) — no SKU solo sito |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) **v1.4** |
| **API Railway** | [`docs/ops/RAILWAY_DEPLOY.md`](../docs/ops/RAILWAY_DEPLOY.md) — D-123 |
| **Vercel FE** | [`docs/ops/VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) — D-074 / **D-133** bake API URL |
| **Stripe** | [`memory/STRIPE_ONBOARDING.md`](./STRIPE_ONBOARDING.md) |
| **Auth area** | **D-131** `/cloud/area` · **D-135** account solo B2C |
| **Google login** | **D-134** `GOOGLE_CLIENT_ID` Web reale |
| **Vendi B2C** | **D-135** CSRF · HAL improve · moderazione pending |

---

## Filo prodotto

1. **02-Nov chiuso:** dogfood Privato Vendi live (città, HAL, salva, sessione CSRF, nav account). Founder pubblica da account B2C (anonima se sessione CRM).
2. **Prossimo (solo se Founder dice vai):** moderazione Founder degli annunci `pending` · oppure P0 Clone-from-URL (D-130) · oppure pilota mandati D-129.
3. Residui sicurezza: YouTrust → `ESIGN_PROVIDER=mock`; Mongo rotate saltato.
4. HAL reindex dopo docs Cap.00/01/10/18 (D-135).

---

## Link dogfood Privato (Founder)

- Area: https://cloud.omniarealestateecosystem.it/it/cloud/area  
- Register sell: https://cloud.omniarealestateecosystem.it/it/cloud/register?intent=sell  
- Vendi: https://cloud.omniarealestateecosystem.it/it/cloud/account/sell  

**Regola**: sessione gestionale/Founder ≠ account Privato. Per Vendi usa B2C (finestra anonima OK).
