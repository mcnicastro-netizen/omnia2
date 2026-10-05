# Prossima sessione — programma passi

**Aggiornato**: 5 Ottobre 2026 · **Demo Nicastroimmobiliare PRONTA (cliente 1)**  
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
| **Ruolo** | `agency_admin` |
| **Seed** | `backend/scripts/seed_nicastro_agency.py` (idempotente) |

### Checklist operativa

1. ✅ Ambiente prova su (`bash scripts/omnia-stack.sh ensure`) + tunnel pubblico  
2. ✅ Account **agenzia ufficiale** Nicastroimmobiliare (non `demo-agency-001`) · `agency_admin`  
3. Lead Founders — reinvio se serve · URL sito `https://www.nicastroimmobiliare.it/`  
4. ✅ Prep **assistita** (A-037 non chiude ancora URL→demo automatica):
   - palette/logo da crawl sito (`#BC4F08` / `#3DB04B` + logo AgestaWeb)
   - tema Classic + 4 immobili CT + 3 clienti  
5. ✅ Login QA browser PASS (titolare Nicastro · 4 immobili CT) — invio link a Marco-titolare  
6. ⏳ Annotare cosa gratta → backlog / A-037

### Secrets (pod omnia2, 5 Ott 2026)

Verifica: `bash scripts/check-secrets-presence.sh` (nomi + present/missing, **mai valori**).

| Secret | Stato su questo env omnia2 |
|--------|----------------------------|
| `RESEND_API_KEY` | **PRESENT** (mail demo/prod non in mock per assenza chiave) |
| `GEMINI_API_KEY` | **PRESENT** |
| `FAL_KEY` | **PRESENT** |

- SoT key = password manager + console provider. Cursor vault = sola copia di iniezione.  
- Inventario nomi: `memory/CLOUD_SECRETS_INVENTORY.md`. Policy: `memory/INTEGRITY_AND_SECRETS.md`.  
- Se un *altro* agent mostra solo `GITHUB_TOKEN` → environment sbagliato (New Project / Origin-tmp), non chiavi cancellate. **Non** usare New Project per OMNIA.
- Regola anti–New Project committata in `.cursor/rules/anti-new-project.mdc` (Always Apply). Founder non deve incollarla in Settings. Su `cursor.com/agents` aprire **sempre** omnia2, mai Start from scratch / New Project.

### Limiti onesti da non promettere in mail
- Clone automatico del sito **non** ancora live (A-037)  
- Self-serve Stripe **OFF** (O6 CONDITIONAL)  
- Dominio/email Basic Soft → percorso verifica-dominio se serve  

---

## Continuità SoT

| | |
|--|--|
| **Programma** | `docs/audit/OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md` |
| **O6 gate** | `docs/audit/OMNIA_O6_GATE_CHECKLIST.md` — CONDITIONAL PASS |
| **Restore** | `docs/ops/RESTORE_MANUAL.md` — run firmata ⏳ non-prod |
| **Priorità prodotto** | **A-037** — demo da sito + template pack / non-proprietario |
| Regola | **Nessun self-serve finché O6 ≠ PASS** |

### Prossimi passi (in ordine)

0. ✅ HAL + manuale sync D-116 (Cap. 00/08/12/18 + `hal-index` v0.27)  
1. Reinoltro demo / link login **titolare** (esperienza cliente, non solo super_admin)  
2. Annotare friction → backlog / A-037  
3. Firmare restore non-prod (O3b) se non fatto  
4. Founder decide self-serve ON **solo** con O6 PASS  
