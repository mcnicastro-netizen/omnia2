# Prossima sessione — programma passi

**Aggiornato**: 4 Novembre 2026 — **D-138** Idealista+ inbox + Esci B2C; probe API; **D-139** news backlog  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md) · probe 04-Nov: Tavily 401 · Yousign sandbox 401 (`mock`).  
**Staging ops**: [`docs/STAGING_PROFESSIONAL_D136.md`](../docs/STAGING_PROFESSIONAL_D136.md).  
**Claude Code marketplace (29-Ott)**: Founder check Windows `svc-telemetry` → **OK** (non impattato).

**Prompt nuovo agent**: [`docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md`](../docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md).

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) |
| **Vendi B2C** | **D-135** + **D-136** staging ✅ + **D-138** inbox/visite/Esci ✅ |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) v1.4 |
| API / FE | Railway D-123 · Vercel D-074/D-133 |

---

## Filo prodotto

1. **04-Nov chiuso:** D-136 dogfood staging+Stripe; D-138 inbox Idealista+ + Esci B2C; docs/HAL v0.46; merge #82+#83.
2. **Backlog Founder (unica soluzione dopo pausa):** D-139 news box RSS; riprove flussi end-to-end portale.
3. **Ops:** rinnovare `TAVILY_API_KEY` se serve HAL Legal search; YouTrust resta mock finché key prod.
4. **Opzionale staging:** shadow `professional` su Railway / ripristino cap anteprime / UX stili REJECT.

---

## Link dogfood Privato

- Vendi: https://cloud.omniarealestateecosystem.it/it/cloud/account/sell  
- Area: https://cloud.omniarealestateecosystem.it/it/cloud/area  

**Regola**: login B2C Privato ≠ sessione agenzia/Founder CRM.
