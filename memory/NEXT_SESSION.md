# Prossima sessione — programma passi

**Aggiornato**: 8 Ottobre 2026 · Audit Portale D-118 · vault + HAL sync  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Chat SoT vault / Onda D**: **controllo secrets omnia** (inject fresco)  
**Chat storica audit A–C**: chiusa / non reiniettare secret qui

---

## 🎯 Audit Portale — in corso (D-118)

**Programma**: [`docs/audit/OMNIA_PORTALE_AUDIT_PROGRAM.md`](../docs/audit/OMNIA_PORTALE_AUDIT_PROGRAM.md)  
**Finding**: [`docs/audit/portale-finding.md`](../docs/audit/portale-finding.md)  
**Matrice C**: [`docs/audit/portale-matrici/2026-10-08-onda-c.md`](../docs/audit/portale-matrici/2026-10-08-onda-c.md)  
**Secrets**: [`memory/CLOUD_SECRETS_INVENTORY.md`](CLOUD_SECRETS_INVENTORY.md)

| Giorno | Onda | Stato |
|--|--|--|
| 8 Ott | **A** funzionamento | ✅ CHIUSA · P-001…P-008 |
| 8 Ott | **B** codice solo portale | ✅ CHIUSA · P-009…P-017 |
| 8 Ott | **C** secrets | ✅ boot auto · vault Save fatto · correggere **sk_live→sk_test** |
| succ. | **D** prova live provider | ⏭ su chat *controllo secrets* · Visura **SKIP** (Catasto provider sospeso) |
| poi | E→J | pianificate |

### Prima di Onda D (Founder, su chat secrets)
1. Vault: sostituire Stripe **live** con **test** (`sk_test_` / `pk_test_` / `whsec` test)  
2. Aggiungere `OPENAPI_EMAIL` se serve OAuth (Visura resta SKIP finché Catasto sospeso)  
3. `JWT_SECRET` reale (no `change-me-…`)  
4. Nuovo agent se hai appena corretto i secret · `bash scripts/check-secrets-presence.sh` → class=sk_test  
5. «vai» Onda D (senza Visura PDF)

---

## ✅ Boot auto Cloud (8 Ott) — già in repo

| Script | Ruolo |
|--|--|
| `stripe-vault-materialize.py` | vault → `.env` (+ OPENAPI_*) · prefer sk_test_ |
| `sync-public-base-url.py` | FRONTEND_* / OMNIA_PUBLIC_URL = trycloudflare |
| `sync-stripe-webhook-url.py` | webhook test → `{tunnel}/api/billing/webhook` |
| `shared/public_base.py` | email/alert preferiscono SHARE_URL |
| `check-secrets-presence.sh` | dogfood Stripe/OpenAPI + WARN vault |

---

## ✅ Stripe sandbox (regola Cloud)

Solo `sk_test_` / `pk_test_` · `STRIPE_ENABLED=true` · `STRIPE_MODE` opzionale (auto).  
`bash scripts/activate-stripe-sandbox.sh` · HAL `api.stripe-sandbox-cloud`.

---

## ⚠ Visura / OpenAPI Catasto

**8 Ott 2026 Founder**: servizio **Catasto sospeso dal provider** OpenAPI.it.  
Dogfood Visura = SKIP. HAL: `api.visura-openapi-catasto`.

---

## HAL / manuale

Aggiornati Cap. 00 HAL (`api.cloud-secrets-vault`, `api.visura-openapi-catasto`, `api.portale-audit-program`) + Cap. 19 §19.10.  
Reindex: `POST /api/app/hal/knowledge/reindex?force=true` (super_admin) dopo merge.
