# Prossima sessione — programma passi

**Aggiornato**: 7 Ottobre 2026 · **Dogfood E2E PASS** · Stripe sandbox Cloud OK  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Chat SoT sessione**: UNICA chat — Stripe + dogfood (`bc-7412138c-…`)

---

## ✅ Dogfood E2E (7 Ott) — chiuso PASS

| Step | Esito |
|--|--|
| Billing UI Nicastro + checkout Stripe test | PASS (`cs_test` · Sandbox) |
| Annuncio privato B2C | PASS (IN REVISIONE) |
| Nuova agenzia (register → onboarding) | PASS (`agency_admin`) |
| API keys Track B (Founder) | PASS (`omk_live_` prefix) |

### Dogfood strumenti privato B2C (7 Ott pomeriggio)

| Strumento | Esito | Nota onesta |
|--|--|--|
| Boost Vetrina | PASS → Stripe test | Checkout ok; effetto post-pagamento non chiuso (webhook) |
| Virtual staging | PASS → Stripe test | Serve ≥1 foto |
| Valutatore gratis | PASS | Serve email verificata; 1/anno |
| Valutatore UNI €2,99 | PASS → Stripe test | |
| Visura €4,90 | BLOCCATA | Manca secret provider catasto (OpenAPI.it) |
| HAL Legal | PARZIALE | Chat apre ma risposta timeout (Tavily assente); €1 catalogo non in UI |
| Mutui | PASS | Gratis · offerte banche ok |

Report strumenti: `/opt/cursor/artifacts/dogfood-b2c-tools-report.json` (solo agent VM).

CRM pubblico (tunnel): vedi `/tmp/omnia-stack/CRM_LOGIN_URL.txt` (quick tunnel si rinnova).  
Report E2E: `/opt/cursor/artifacts/dogfood-e2e-report.json` (solo su agent VM).

**Onesto**: O6 self-serve *pagamento* resta OFF — creazione account agenzia ≠ checkout pubblico.

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
7. ✅ Dogfood E2E UI PASS (billing → B2C privato → nuova agenzia → API keys)

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

### Dopo la demo Nicastro

1. Firmare restore non-prod (O3b) se non fatto  
2. Annotare friction dogfood → backlog  
3. A-037 / template pack
