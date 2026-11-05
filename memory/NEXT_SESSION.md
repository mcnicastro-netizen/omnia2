# Prossima sessione — programma passi

**Aggiornato**: 5 Novembre 2026 — **D-139** news box portale attivato (+ D-140 già live)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md).  
**Staging ops**: [`docs/STAGING_PROFESSIONAL_D136.md`](../docs/STAGING_PROFESSIONAL_D136.md).

**Prompt nuovo agent**: [`docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md`](../docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md).

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) |
| **Vendi B2C** | **D-135** + **D-136** staging + **D-137/b** safety + **D-138** inbox + **D-140** video/layout ✅ |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) v1.4 |
| API / FE | Railway D-123 · Vercel D-074/D-133 |

---

## Filo prodotto

1. **05-Nov:** D-139 news box RSS **live** — `GET /api/cloud/news` + box home/account (`OMNIA_PORTAL_NEWS` default on).
2. **04-Nov sera chiuso:** D-140 live (PR #84–#90) · Vendi ordine + video tour · Scout · safety soft rescan · docs/HAL v0.47.
3. **Ops:** hard refresh FE se cache chunk; reindex HAL post-merge docs se non già fatto in sessione.
4. **Riprove E2E** portale a mente fresca (dogfood Privato).

---

## Link dogfood Privato

- Vendi: https://cloud.omniarealestateecosystem.it/it/cloud/account/sell  
- Area: https://cloud.omniarealestateecosystem.it/it/cloud/area  
- Account prova sera: `provaomniatest@virgilio.it` (listing Mascalucia `provaprova`)

**Regola**: login B2C Privato ≠ sessione agenzia/Founder CRM.
