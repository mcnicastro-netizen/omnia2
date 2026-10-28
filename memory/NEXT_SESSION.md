# Prossima sessione — programma passi

**Aggiornato**: 28 Ottobre 2026 — D-131…D-134 (auth · Resend · Vercel · Google)  
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
| **Auth area** | **D-131** `/cloud/area` Accedi/Crea account |
| **Google login** | **D-134** `GOOGLE_CLIENT_ID` Web reale |

---

## Filo prodotto

1. Ops 28-Ott chiusi: Area auth · Cerca casa · Resend · Google Sign-In · vault note.
2. **Prossimo (solo se Founder dice vai):** P0 Clone-from-URL (D-130) con preview reale, **oppure** pilota mandati D-129.
3. Residui sicurezza: YouTrust → `ESIGN_PROVIDER=mock`; Mongo rotate saltato.
4. HAL reindex dopo docs Cap.00/01.

---

## ⏭️ Primo passo tipico (nuovo agent)

1. `bash scripts/check-secrets-presence.sh` + smoke health API
2. Vault: Personal OK; no Start Fresh; no delete My Secrets finché UI Environment non risponde
3. Residui sicurezza solo se Founder chiede: YouTrust key / Mongo rotate
4. Altrimenti ripresa prodotto su ok Founder: Clone P0 (D-130) o pilota mandati D-129

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **YouTrust** | Ticket inviato 22-Ott · finché no key → `ESIGN_PROVIDER=mock` |
| **Mongo rotate** | Saltato — riprendere a outage/UI rotate disponibile |
| **Vault Personal** | Add secrets → Personal; Environment preferibile; UI env può glitchare — **no Start Fresh** |
| **No screenshot secret** | Mai foto di Variables Railway con valori in chiaro |
| **SENDER_EMAIL** | Mai `onboarding@resend.dev` in prod (D-132) |
| **Vercel bake** | `REACT_APP_BACKEND_URL` obbligatorio al build (D-133) |
| **D-130** | Vietato promettere clone sito senza preview |
| **D-125 / D-128** | Accesso atti · staging B2C €1,49 |
| **Stripe Live** | Solo dopo KYC |
| **HAL reindex** | Dopo merge docs Cap.00 / YAML |

---

## Stato rapido

| Voce | Esito |
|--|--|
| S1–S10 | ✅ |
| D-124…D-130 | ✅ registrati (clone codice ⏳) |
| D-131 Area auth | ✅ 28-Ott |
| D-132 Resend sender | ✅ live delivered |
| D-133 Vercel API URL | ✅ |
| D-134 Google Sign-In | ✅ live |
| Rotazione Railway core | ✅ 22-Ott |
| YouTrust / Mongo rotate | 🟠 residui |
| A-037 demo da sito | 🟠 |
| Stripe Live | ⏳ |
