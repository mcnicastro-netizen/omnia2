# Prossima sessione — programma passi

**Aggiornato**: 3 Novembre 2026 — **D-136** Virtual Staging professionale (fedeltà) + dogfood B2C  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault scope: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md) — Personal vs Environment.  
**Email**: [`memory/RESEND_DOMAIN_GUIDE.md`](./RESEND_DOMAIN_GUIDE.md) — D-132 mittente `info@omniarealestateecosystem.it` live.  
**Google**: [`memory/GOOGLE_AUTH.md`](./GOOGLE_AUTH.md) — D-134 Client ID Web live.  
**Staging ops**: [`docs/STAGING_PROFESSIONAL_D136.md`](../docs/STAGING_PROFESSIONAL_D136.md).

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
| **Vendi B2C** | **D-135** CSRF · HAL · **D-136** staging fedeltà |

---

## Filo prodotto

1. **03-Nov chiuso (codice):** D-136 pipeline professionale (flag) + room detect + hard gate + blocco promote · FE stili/modi · cap dogfood (`CAP=0`, esente `@virgilio.it`) · PR #71–#74 su `main` · Railway+Vercel live.
2. **03-Nov docs/HAL:** Cap.9 MD+YAML · voci `staging.fedelta-architettonica` + `staging.b2c-vendi` · `hal-index` v0.45 · reindex prod.
3. **Prossimo (Founder domani):** dogfood visivo account `@virgilio.it` — soggiorno → **Sostituisci arredi** → **Luxury** → deve restare soggiorno (no porte/armadi inventati). Poi decidere shadow `OMNIA_STAGING_PIPELINE=professional`.
4. **Non fare finché Founder non dice vai:** flip default `professional` · merge PR #70 (wait-ux) — **superseded**/conflitto, UX già in FE D-136.
5. Residui sicurezza: YouTrust → `ESIGN_PROVIDER=mock`; Mongo rotate saltato.

---

## Link dogfood Privato (Founder)

- Area: https://cloud.omniarealestateecosystem.it/it/cloud/area  
- Register sell: https://cloud.omniarealestateecosystem.it/it/cloud/register?intent=sell  
- Vendi: https://cloud.omniarealestateecosystem.it/it/cloud/account/sell  

**Regola**: sessione gestionale/Founder ≠ account Privato. Per Vendi usa B2C (`@virgilio.it` OK). Hard refresh dopo deploy.
