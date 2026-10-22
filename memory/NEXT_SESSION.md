# Prossima sessione — programma passi

**Aggiornato**: 22 Ottobre 2026 — rotazione core DONE · vault Personal OK oggi · ripresa prodotto su ok Founder  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault scope: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md) — Personal vs Environment.

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

## Filo prodotto (pre-incidente Railway)

1. Simulazioni commerciali Founder/Nicastro (4 percorsi) → clone-from-URL = prodotto vero (≠ Brand Extractor).
2. Demo foto immobili / computerUse: skip Founder (spend / no clone reale) → chiudere docs.
3. HAL + manuale + merge PR (cleanup: solo redundant; rebase/merge il resto). Dogfood già su main.
4. Poi mail Railway → rotazione core FATTA. Residui: YouTrust → `ESIGN_PROVIDER=mock`; Mongo rotate saltato.

**Prossimo lavoro (solo se Founder dice vai):** P0 Clone-from-URL (D-130) con preview reale, **oppure** pilota mandati D-129. Non feature grandi da soli; non re-ruotare secret senza richiesta.

---

## ⏭️ Primo passo tipico (nuovo agent)

1. `bash scripts/check-secrets-presence.sh` + smoke health API
2. Vault: Personal OK oggi; no Start Fresh; no delete My Secrets finché UI Environment non risponde
3. Residui sicurezza solo se Founder chiede: YouTrust key / Mongo rotate / secondo giro post-screenshot
4. Altrimenti ripresa prodotto su ok Founder: Clone P0 (D-130) o pilota mandati D-129

---

## ⚠️ Non dimenticare

| Voce | Nota |
|------|------|
| **YouTrust** | Ticket inviato 22-Ott · finché no key → `ESIGN_PROVIDER=mock` |
| **Mongo rotate** | Saltato — riprendere a outage/UI rotate disponibile |
| **Vault Personal** | Add secrets → Personal; Environment preferibile; UI env può glitchare — **no Start Fresh** |
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
