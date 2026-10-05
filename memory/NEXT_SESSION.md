# Prossima sessione — programma passi

**Aggiornato**: 5 Ottobre 2026 · **Track A home live** · layout pixel + Track B dopo  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅ (SoT = github/main; non Origin-tmp / New Project)

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
| **Sito pubblico** | `/api/p/nicastroimmobiliare/` (Track A) |
| **Ruolo** | `agency_admin` |
| **Seed** | `backend/scripts/seed_nicastro_agency.py` (idempotente) |

### Checklist operativa

1. ✅ Ambiente prova su (`bash scripts/omnia-stack.sh ensure`) + tunnel pubblico  
2. ✅ Account **agenzia ufficiale** Nicastroimmobiliare (non `demo-agency-001`) · `agency_admin`  
3. Lead Founders — reinvio se serve · URL sito `https://www.nicastroimmobiliare.it/`  
4. ✅ Prep **assistita** + **Track A**:
   - Classic verde `#3D8B40` + hero default + `mls_enabled`
   - Home: dual search + In evidenza + Ultimi (portafoglio proprio)
   - **CRM operativo**: caricare immobili reali (manuale/CSV/XML); eventuali `_demo_layout` solo QA
   - Seed non rimette fixture CT se `dogfood_skip_fixtures`
5. ✅ Login QA + Brand Studio anteprima `srcDoc` PASS  
6. ⏳ **Prossimo**: raffinare layout pixel vs sito legacy · poi Track B / D-023 (A-037)

### Secrets (pod omnia2, 5 Ott 2026)

Verifica: `bash scripts/check-secrets-presence.sh` (nomi + present/missing, **mai valori**).

| Secret | Stato su questo env omnia2 |
|--------|----------------------------|
| `RESEND_API_KEY` | **PRESENT** |
| `GEMINI_API_KEY` | **PRESENT** |
| `FAL_KEY` | **PRESENT** |

- SoT key = password manager + console provider. Cursor vault = sola copia di iniezione.  
- Regola anti–New Project: `.cursor/rules/anti-new-project.mdc`

### Limiti onesti da non promettere in mail
- Clone automatico pixel-perfect del sito **non** ancora live (A-037 Track B / D-023)  
- Track A = struttura home riconoscibile; polish layout = backlog Founder  
- Self-serve Stripe **OFF** (O6 CONDITIONAL)  

---

## Continuità SoT

| | |
|--|--|
| **Programma** | `docs/audit/OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md` |
| **O6 gate** | `docs/audit/OMNIA_O6_GATE_CHECKLIST.md` — CONDITIONAL PASS |
| **Priorità prodotto** | **A-037** — Track B clone + template pack; raffinamento layout Track A |
| Regola | **Nessun self-serve finché O6 ≠ PASS** |

### Prossimi passi (in ordine)

0. ✅ Track A home + hero + Cap.8/HAL sync  
1. Raffinamento layout (Founder: «ce ne occuperemo dopo»)  
2. Carico immobili/richieste reali Nicastro  
3. Track B / D-023 quando Founder dice via  
4. Firmare restore non-prod (O3b) se non fatto  
5. Founder decide self-serve ON **solo** con O6 PASS  
