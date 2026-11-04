# Prossima sessione — programma passi

**Aggiornato**: 4 Novembre 2026 — **D-136** dogfood B2C chiuso (fedeltà + Stripe €1,49)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md).  
**Staging ops**: [`docs/STAGING_PROFESSIONAL_D136.md`](../docs/STAGING_PROFESSIONAL_D136.md).  
**Claude Code marketplace (29-Ott)**: Founder check Windows `svc-telemetry` → **OK** (non impattato).

**Prompt nuovo agent**: [`docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md`](../docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md).

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) |
| **Vendi B2C** | **D-135** + **D-136** staging fedeltà + Stripe €1,49 dogfood ✅ |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) v1.4 |
| API / FE | Railway D-123 · Vercel D-074/D-133 |

---

## Filo prodotto

1. **04-Nov chiuso:** dogfood Founder `@virgilio.it` — soggiorno → Sostituisci arredi → gate PASS (resta soggiorno) · multi-stile mostra solo ACCEPT · **Stripe €1,49 OK**.
2. **Docs/HAL sync:** Cap.9 + voci HAL · `hal-index` v0.46 · reindex prod.
3. **Prossimo (solo se Founder dice vai):**
   - shadow `OMNIA_STAGING_PIPELINE=professional` su Railway
   - oppure ripristinare `OMNIA_B2C_STAGING_PREVIEW_DAILY_CAP=3` (fine dogfood)
   - oppure UX: miniature stili REJECT in grigio «scartato»
4. Residui sicurezza: YouTrust → `ESIGN_PROVIDER=mock`; Mongo rotate saltato.

---

## Link dogfood Privato

- Vendi: https://cloud.omniarealestateecosystem.it/it/cloud/account/sell  
- Area: https://cloud.omniarealestateecosystem.it/it/cloud/area  

**Regola**: login B2C Privato ≠ sessione agenzia/Founder CRM.
