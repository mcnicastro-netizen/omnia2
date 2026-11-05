# Prossima sessione — programma passi

**Aggiornato**: 5 Novembre 2026 — **D-144** domain .it WHOIS + tre layer dominio/sito/email · docs/HAL **v0.52**  
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
| **Home / Cerca / App** | **D-139** news + **D-141** mappa + **D-142** Scout + **D-143** PWA QR→Area ✅ |
| **Dominio** | **D-144** WHOIS `.it` + tre layer dominio/sito/email ✅ |
| Listino B2C | [`memory/PRICING_B2C.md`](./PRICING_B2C.md) v1.4 |
| API / FE | Railway D-123 · Vercel D-074/D-133 |

---

## Filo prodotto

1. **05-Nov chiuso:** D-144 — checker `.it` WHOIS + tre layer (dominio/sito/email) · caso Nicastro/Aruba/Agesta · Cap.17/HAL v0.52 (PR #108 + docs).
2. **05-Nov:** D-143 PWA QR→Area · nav opaca (PR #104–#106); D-142 Scout; D-141 mappa; D-139 news.
3. **04-Nov sera:** D-140 Vendi + video tour · Scout · safety soft.
4. **Ops:** hard refresh FE; reindex HAL già fatto post-sync se chunk aggiornati.
5. **Riprove E2E** portale a mente fresca (dogfood Privato + install PWA su Android reale).

---

## Link dogfood Privato

- Home: https://cloud.omniarealestateecosystem.it/it/cloud  
- Scarica app / QR: https://cloud.omniarealestateecosystem.it/it/cloud/app  
- Area (atterraggio QR): https://cloud.omniarealestateecosystem.it/it/cloud/area?from=pwa  
- Cerca mappa: https://cloud.omniarealestateecosystem.it/it/cloud/search?view=map  
- Vendi: https://cloud.omniarealestateecosystem.it/it/cloud/account/sell  
- Account prova sera: `provaomniatest@virgilio.it` (listing Mascalucia `provaprova`)

**Regola**: login B2C Privato ≠ sessione agenzia/Founder CRM.
