# Prossima sessione — programma passi

**Aggiornato**: 21 Novembre 2026 (~00:05 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**Puntatore primario**: [`HANDOFF_PRE_GTM_ORDINI.md`](./HANDOFF_PRE_GTM_ORDINI.md) · **D-191**

---

## Dove siamo

| Item | Stato |
|------|-------|
| PR #240 Deal / chat / mini-dossier | **MERGED** in `main` (`f0d4b26`) · tip docs `759d628` |
| Primo E2E gestionale dogfood | `D175-E2E-DEEP` · SHA `9aec192` · CLEAN · **fatto** |
| E2E INTEGRALE PRE-GTM | SHA `759d628` · CONTINUITY · dossier Founder · **fatto** |
| Riconciliazione DEEP↔INTEGRALE | `_export_audits/RICONCILIAZIONE-PRIMO-E2E-VS-E2E-20-NOVEMBRE.md` · **fatto** |
| Programma stabilizzazione 8 aree | `_export_audits/OMNIA-PROGRAMMA-STABILIZZAZIONE-PRE-GTM.md` · **fatto** |
| Implementazione fix / H4 / nuovo E2E | **NON autorizzata** |

### Verità da non confondere
- **0 SUPERATO ≠ gestionale rotto.** = criteri più ampi + UI 0 click + gap billing/AI.  
- **Nessuna regressione CRM/MLS confermata** DEEP→INTEGRALE.  
- **A-007** = difetto lista legacy (priorità #1 quando si autorizza il codice).  
- **LLM/HAL** = priorità critica trasversale (piano accettazione autonomo).

---

## Prossimo passo (sceglie il Founder)

1. **S1** — Diagnosi/fix A-007 (fondamenta)  
2. **S3** — Diagnosi LLM/HAL (`llm_busy`, resilience, eval)  
3. Altro solo con mandato scritto

Finché non arriva il “vai”: **STOP. Nessun codice prodotto.**

## Non fare

- Audit generale da zero / E2E mutativo spontaneo  
- Aprire H4 / Stripe LIVE / sealed  
- Contare PARZIALI come % rottura  
- “Sistemare” AI cambiando modello senza diagnosi  
- Dichiarare GTM-ready  
- Ripartire da “merge PR #240” (già in main)
