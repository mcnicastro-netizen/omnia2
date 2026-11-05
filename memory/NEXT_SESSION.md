# Prossima sessione — programma passi

**Aggiornato**: 5 Novembre 2026 — D-141 Kling 30 cr · gate **pre-produzione margini**  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (esiste; UI Dashboard può glitchare — non Start Fresh)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md).  
**Staging ops**: [`docs/STAGING_PROFESSIONAL_D136.md`](../docs/STAGING_PROFESSIONAL_D136.md).

**Prompt nuovo agent**: [`docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md`](../docs/ops/NEW_AGENT_PROMPT_POST_RAILWAY_ROTATION.md).

---

## ⛔ Prima di andare in produzione (obbligatorio)

Founder 05-Nov-2026: **controllare i margini prima del go-live**, non dopo.

1. Riaprire [`PRICING_OMNIA.md`](./PRICING_OMNIA.md) § «Controllo perdite» + [`PRICING_B2C.md`](./PRICING_B2C.md).
2. Allineare **codice** (`CREDIT_COSTS` / checkout B2C) ↔ listino: niente SKU sotto COGS (lezione Kling @ 10 cr).
3. **Visura** e **APE**: verificare fee partner (OpenAPI / fatture) ≤ prezzo listino; se fee > prezzo → alzare prezzo o sospendere SKU.
4. Smoke Founder Ops `/app/ops` (COGS vs crediti scalati) su ambiente staging/prod controllato.
5. Solo dopo OK Founder su questa checklist → dichiarare go-live commerciale.

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) |
| **Vendi B2C** | **D-135** + **D-136** staging + **D-137/b** safety + **D-138** inbox + **D-140** video/layout ✅ |
| Listino B2B | [`memory/PRICING_OMNIA.md`](./PRICING_OMNIA.md) **v3.2** (Kling 30 cr · D-141) |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) v1.4 |
| API / FE | Railway D-123 · Vercel D-074/D-133 |

---

## Filo prodotto

1. **05-Nov:** D-141 Kling 30 cr live; **gate pre-prod margini** (Visura/APE fee) ancora da chiudere con fatture.
2. **04-Nov sera chiuso:** D-140 · Vendi + video tour · Scout · safety soft · docs/HAL v0.47.
3. **Backlog Founder:** D-139 news box RSS; riprove E2E portale a mente fresca.
4. **Ops:** hard refresh FE; reindex HAL post-merge docs se serve.

---

## Link dogfood Privato

- Vendi: https://cloud.omniarealestateecosystem.it/it/cloud/account/sell  
- Area: https://cloud.omniarealestateecosystem.it/it/cloud/area  
- Account prova sera: `provaomniatest@virgilio.it` (listing Mascalucia `provaprova`)

**Regola**: login B2C Privato ≠ sessione agenzia/Founder CRM.
