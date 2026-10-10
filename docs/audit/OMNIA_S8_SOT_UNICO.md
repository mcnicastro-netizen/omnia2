# S8 — SoT unico (C9 / C10)

**Data:** 10 Ottobre 2026  
**Stato:** ✅ DECISO + CODICE (docs)  
**Chiude:** C9 (SoT in conflitto temporale) · C10 (falsa chiusura CHIUSO/PASS/GREEN)

---

## Regola (vincolante)

| Ruolo | Documento |
|-------|-----------|
| **Freccia / sequenza** | `docs/audit/OMNIA_COERENZA_SISTEMA.md` |
| **Cancello self-serve** | `docs/audit/OMNIA_O6_GATE_CHECKLIST.md` |
| **Puntatore sessione** | `memory/NEXT_SESSION.md` |
| Scala verità | DECISO → CODICE → LIVE → FIRMATO |

Qualsiasi altro doc che dica “prossimo passo / Next / vai” **non** è SoT freccia se contraddice i tre sopra.

---

## Registro documenti

### LIVE (consultare)

| Doc | Uso |
|-----|-----|
| `OMNIA_COERENZA_SISTEMA.md` | Freccia S1–S10 · contraddizioni C* |
| `OMNIA_O6_GATE_CHECKLIST.md` | Gate commerciale self-serve |
| `memory/NEXT_SESSION.md` | Cosa fare al prossimo «vai» |
| `OMNIA_S1`…`S7_*.md` + `docs/ops/runs/*` | Artefatti step chiusi |
| `OMNIA_PORTALE_AUDIT_FASCICOLO.md` | Audit portale D-118 (storico utile) |
| `memory/DECISIONS.md` | Decisioni product (non freccia sessione) |
| `memory/PRICING_*.md` | Listino (fermo; S3.1 firma meter aperta) |

### FROZEN (non guidano più la sessione)

Banner in testa al file → rimanda a coerenza + NEXT.

| Doc | Perché frozen |
|-----|----------------|
| `OMNIA_AUDIT_STATE.md` | Diceva «Next: O3b / A-037» — superato da S1–S7 |
| `OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md` | Onde O0–O6 storiche; freccia = S* in coerenza |
| `memory/HANDOFF_NEXT_AGENT.md` | Handoff feb/set — non punta S8/S9 |
| `memory/HANDOFF_SUMMARY.md` | Idem (pre-launch freeze D-035 storico) |

Non cancellati: restano memoria. **Non** usarli per decidere il prossimo step.

---

## Allineamenti fatti in S8

1. C6 → runtime S2 ✅ (non più “bak ×30 as-is”)  
2. O6 riga O3b → run firmata S1 ✅ (non più ⏳)  
3. C9/C10 mitigati da questo registro + banner  
4. NEXT → **S9**  
5. “Fuori sequenza” ancorato a **S9 / O6**, non a S7  

---

## Aperto (esplicito, non nascosto)

| Voce | Nota |
|------|------|
| **S3.1** | Firma Founder meter storage |
| **D-038** | APE ordine — accordo commerciale |
| **D-075 vs P-036** | HAL Legal incluso vs 12 crediti |
| **S9** | Firma Founder → `OMNIA_SELF_SERVE_ENABLED=true` |
| **C5** | Trash non ovunque (fuori freccia S1–S10 finché non ripriorizzato) |
