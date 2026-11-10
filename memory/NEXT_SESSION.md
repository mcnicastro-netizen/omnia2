# Prossima sessione — programma passi

**Aggiornato**: 10 Novembre 2026, sera (~17:15 Europe/Rome) — chiusura giornata dogfood registrazione  
**Ripresa dettagliata**: [`RIPRENDI_2026-11-11.md`](./RIPRENDI_2026-11-11.md)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Environment**: omnia2 (SoT GitHub — mai New Project / Origin-tmp)

**Sicurezza Railway**: runbook [`docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md`](../docs/ops/RAILWAY_SECURITY_ROTATION_2026-10-22.md) · stato 🟡 core done.  
Smoke: `GET $OMNIA_API_PUBLIC_URL/api/health` → ok/db=ok.  
Vault: [`memory/CLOUD_SECRETS_INVENTORY.md`](./CLOUD_SECRETS_INVENTORY.md).

---

## 🎯 SoT freccia

| Ruolo | Doc |
|-------|-----|
| Freccia | [`docs/audit/OMNIA_COERENZA_SISTEMA.md`](../docs/audit/OMNIA_COERENZA_SISTEMA.md) |
| **Verso-8** | [`PROGRAMMA_VERSO_8.md`](./PROGRAMMA_VERSO_8.md) |
| **Registrazione B2B** | **D-157** + **D-158** (logo vs sito, resume login) |
| **Cabina Ops** | **D-154** / **D-155** |
| **Primo cliente** | Nicastro — tenant `nicastro-immobiliare` **pending** in prod (sera 10-Nov) |

---

## Domani 11-Nov — ripresa riposata

1. Leggere [`RIPRENDI_2026-11-11.md`](./RIPRENDI_2026-11-11.md).
2. Decidere: **continuare** `nicastro-immobiliare` pending **oppure** offboard e rifare register con D-158.
3. Completare fino a **login CRM** (KYC + pagamento + Attiva → API key).
4. Solo dopo: grant/crediti se serve, import, marathon tool.

---

## Login utili

| Chi | Come |
|-----|------|
| Founder Ops | `ADMIN_EMAIL` vault → `/it/app/ops` |
| Nicastro pending | `info@nicastroimmobiliare.it` → **Password dimenticata?** / email resume finché non arriva API key |
| Post-Attiva | email `agency_credentials` (API key = password) |

URL: `https://omniarealestateecosystem.it/it` · API health su `OMNIA_API_PUBLIC_URL`.

---

## Debito noto (non urgente stanotte)

- `STORAGE_BACKEND=local` su Railway (upload non durevoli al redeploy).
- Reindex HAL corpus dopo merge docs (Cap.01 YAML aggiornato).
- Margini listino pre go-live commerciale (gate Founder invariato).
