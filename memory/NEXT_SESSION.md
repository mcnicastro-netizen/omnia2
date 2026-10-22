# Prossima sessione — programma passi

**Aggiornato**: 22 Ottobre 2026 — rotazione Railway **core DONE** · nuovo agent  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (secret aggiornati — **nuovo agent obbligatorio**)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.

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
| **Vercel FE** | [`docs/ops/VERCEL_DEPLOY.md`](./VERCEL_DEPLOY.md) — D-074 |
| **Stripe** | [`memory/STRIPE_ONBOARDING.md`](./STRIPE_ONBOARDING.md) |

---

## ⏭️ Primo passo tipico (nuovo agent)

1. `bash scripts/check-secrets-presence.sh` + smoke health API
2. Residui sicurezza solo se Founder chiede: YouTrust key / Mongo rotate / secondo giro Stripe+Resend+OpenAPI (no screenshot valori)
3. Altrimenti ripresa prodotto: Clone P0 (D-130) o pilota mandati D-129

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **YouTrust** | Ticket inviato 22-Ott · finché no key → `ESIGN_PROVIDER=mock` |
| **Mongo rotate** | Saltato — riprendere a outage/UI rotate disponibile |
| **No screenshot secret** | Mai foto di Variables Railway con valori in chiaro |
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
| Rotazione Railway core | ✅ 22-Ott |
| YouTrust / Mongo rotate | 🟠 residui |
| A-037 demo da sito | 🟠 |
| Stripe Live | ⏳ |
