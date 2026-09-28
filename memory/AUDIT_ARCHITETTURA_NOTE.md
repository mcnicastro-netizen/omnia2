# Audit architettura SaaS — note Founder

> Progresso blocco-per-blocco.  
> **Prompt master vincolante**: `memory/AUDIT_PROMPT_MASTER.md` (indice §1–§27).  
> **Niente codice** senza «vai» di implementazione.  
> **⏸ SESSIONE IN PAUSA** — riprendere **solo** al prossimo «vai» Founder.

**Ultimo aggiornamento**: 28-Set-2026 · prompt master salvato · **stop fino a «vai»**

---

## Stato vs prompt master

| Master § | Tema | Stato sessione |
|----------|------|----------------|
| §1 | Comprendi il sistema | 🟢 fatto (P1) |
| §2 | Modello concettuale | 🟢 approvato (P2) |
| §3 | Multi-tenancy | 🟠 acquisito · finding aperti |
| §4 | AuthN/AuthZ | 🟠 acquisito · finding aperti |
| §5 | Lifecycle | 🟠 + **D-094** |
| §6 | Cestino | 🟡 parziale in P5 · **da fare come blocco dedicato** |
| §7 | Media e file | 🟠 + **D-095** · M-* |
| §8 | Storage e costi | ⬜ **prossimo naturale** |
| §9–§14 | Backup → GDPR | ⬜ |
| §15 | Job asincroni | 🟠 anticipato come “P8” · J-* |
| §16–§27 | Osservabilità → report | ⬜ |

**Fuori indice ma utili**: finding **E-*** (proiezioni esterne / enforcement D-094) — tenere nel corpus.

Decisioni dominio (codice ⏳): **D-094**, **D-095**.

---

## Cluster già emersi (no P0–P3 finché Founder non apre §23)

1. **Media authorization** = P3.1 + P4.1 + M-01 → D-095  
2. **Mongo ⟷ blob lifecycle** = M-02…M-04 + L-05/L-06 → D-095  
3. **Proiezioni/jobs vs D-094** = E-* · J-01…J-04  
4. **AuthZ non uniforme** login→risorsa (P4)  
5. **Attività**: appartenenza aperta (non = Richieste)

---

## Alla ripresa («vai»)

1. Rileggi `AUDIT_PROMPT_MASTER.md`.  
2. Continua dal **prossimo blocco master non chiuso** (salvo diversa indicazione Founder): tipicamente **§6 Cestino** (approfondimento) oppure **§8 Storage e costi**.  
3. Aggiorna queste note senza contraddire i verdetti già acquisiti.  
4. **Non** produrre il report finale A–K (§25) finché non richiesti i punti 23–25.

Dettaglio finding: sezioni storiche sotto / file git history; sintesi in Cap.00 e A-035.
