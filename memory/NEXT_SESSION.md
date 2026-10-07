# Prossima sessione — programma passi

**Aggiornato**: 7 Ottobre 2026 · dogfood Visura OK · D-117 Ops finance · **A-038** in coda post-test  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Chat SoT sessione**: UNICA chat — Stripe sandbox / dogfood / Ops finance

---

## 🟠 Post-test (priorità Founder — non ora)

| ID | Tema | Note |
|--|--|--|
| **A-038** | Fattura Stripe + dati fiscali su ogni incasso | B2C Checkout → Invoice; raccolta CF/P.IVA; FE/SDI = decisione a parte. Dettaglio in `ASPETTI_DA_APPROFONDIRE.md` · **solo con «vai»** |

---

## ✅ Stripe sandbox (Cloud) — chiuso 6 Ott

| Check | Esito |
|--|--|
| Vault inject | `sk_test` / `pk_test` · `STRIPE_ENABLED=true` |
| Catalogo | `python -m apps.billing.setup_stripe` OK |
| API | `GET /api/billing/plans` → `enabled=true` `mode=test` |
| Script | `bash scripts/activate-stripe-sandbox.sh` |
| Docs | HAL `api.cloud-secrets-vault` + `api.stripe-sandbox-cloud` · Cap. 19 §19.10 |

**Regole**: scope secret **Environment** (evitare doppioni Personal); non riusare chat agent avviate con `sk_live_`.

---

## 🎯 Riprendere dogfood E2E (dopo docs)

1. Billing UI `/it/app/settings/billing` (piani + checkout test Stripe)
2. Annuncio privato B2C
3. Nuova agenzia self-serve (se O6 consente) / seed
4. API keys Track B (super_admin)

CRM pubblico (tunnel): vedi `/tmp/omnia-stack/SHARE_URL.txt` / `CRM_LOGIN_URL.txt`

---

## 🎯 Demo Nicastroimmobiliare — ambiente pronto

**Obiettivo Founder:** inviare / aprire la demo all’agenzia **Nicastroimmobiliare** (dogfood cliente-1).

### Accesso titolare (esperienza cliente, non super_admin)

| | |
|--|--|
| **CRM login** | vedi `/tmp/omnia-stack/CRM_LOGIN_URL.txt` (tunnel trycloudflare) |
| **Locale** | http://127.0.0.1:43123/it/login |
| **Email** | `titolare@nicastroimmobiliare.it` |
| **Password** | `NicastroDemo2026!` (override: `NICASTRO_ADMIN_PASSWORD`) |
| **Agenzia** | `nicastro-agency-001` · slug `nicastroimmobiliare` |
| **Ruolo** | `agency_admin` |
| **Seed** | `backend/scripts/seed_nicastro_agency.py` (idempotente) |

### Checklist operativa

1. ✅ Ambiente prova su (`bash scripts/omnia-stack.sh ensure`) + tunnel pubblico  
2. ✅ Account **agenzia ufficiale** Nicastroimmobiliare (non `demo-agency-001`) · `agency_admin`  
3. Lead Founders — reinvio se serve · URL sito `https://www.nicastroimmobiliare.it/`  
4. ✅ Prep **assistita** (A-037 non chiude ancora URL→demo automatica)  
5. ✅ Login QA browser PASS (titolare Nicastro · 4 immobili CT)  
6. ✅ Stripe sandbox Cloud (sk_test) — billing abilitato  
7. ⏳ Annotare cosa gratta → backlog / A-037 · riprendere E2E dogfood

### Limiti onesti da non promettere in mail
- Clone automatico del sito **non** ancora live (A-037)  
- Self-serve Stripe prodotto **OFF** finché O6 ≠ PASS (sandbox Cloud ≠ self-serve pubblico)  
- Dominio/email Basic Soft → percorso verifica-dominio se serve  
- **Secrets**: SoT = password manager + console; Cursor = inject. Inventario: `memory/CLOUD_SECRETS_INVENTORY.md`

---

## Continuità SoT

| | |
|--|--|
| **Programma** | `docs/audit/OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md` |
| **O6 gate** | `docs/audit/OMNIA_O6_GATE_CHECKLIST.md` — CONDITIONAL PASS |
| **Restore** | `docs/ops/RESTORE_MANUAL.md` — run firmata ⏳ non-prod |
| **Priorità prodotto** | **A-037** — demo da sito + template pack / non-proprietario |
| Regola | **Nessun self-serve finché O6 ≠ PASS** |

### Dopo la demo Nicastro / post dogfood

1. Firmare restore non-prod (O3b) se non fatto  
2. A-037 (chiudere loop URL→demo + template pack)  
3. **A-038** — fattura + dati fiscali su ogni incasso (quando Founder dice «vai»)  
4. Founder decide self-serve ON solo con O6 PASS  
