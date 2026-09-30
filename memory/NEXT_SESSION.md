# Prossima sessione — programma passi

**Aggiornato**: 30 Settembre 2026 sera · **Domani: invio demo → Nicastroimmobiliare (cliente 1)**  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  

---

## 🎯 Domani (1-Ott) — Demo Nicastroimmobiliare

**Obiettivo Founder:** inviare / aprire la demo all’agenzia **Nicastroimmobiliare** (dogfood cliente-1).

### Checklist operativa

1. Ambiente prova su (`bash scripts/omnia-stack.sh ensure`) + tunnel pubblico stabile  
2. Account **agenzia ufficiale** Nicastroimmobiliare (non `demo-agency-001`) · ruolo `agency_admin`  
3. Lead Founders già fatto / reinvio se serve · URL sito dichiarato sul lead  
4. Prep **assistita** (A-037 non chiude ancora URL→demo automatica):
   - brand extractor sull’URL sito se disponibile  
   - oppure tema OMNIA + logo/colori a mano  
   - pochi immobili reali + HAL (foto/testi)  
5. Inviare link login / accesso demo a Marco-titolare (esperienza cliente, non solo super_admin)  
6. Annotare cosa gratta → backlog / A-037

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

### Dopo la demo Nicastro

1. Firmare restore non-prod (O3b) se non fatto  
2. A-037 (chiudere loop URL→demo + template pack)  
3. Founder decide self-serve ON solo con O6 PASS  
