# Cap. 00 · Architettura tenancy, auth, media, jobs, storage (audit SaaS)

**Ambito**: founder / super_admin.  
**Prompt master**: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27).  
**Numerazione sessione**: continuum in `AUDIT_ARCHITETTURA_NOTE.md` (non forzare allineamento artificialmente).

---

## Metodo

Un blocco alla volta · niente fix senza «vai» implementazione · no P0–P3 prematuri · aggiornare le note.

---

## Decisioni di dominio (codice ⏳)

### D-094
- `status` = commerciale · `trashed` = lifecycle  
- Trashed → escluso da feed/sync/pubblicazioni **senza** forzare `withdrawn`  
- Cliente Trash → Richieste **archiviate** (storico), non distrutte; restore non riapre  

### D-095
- Media **pubblici** vs **privati** · no “UUID = secret”  
- Cleanup blob indipendente da S3/R2 · idempotente  

### D-085 (già prodotto)
- Quota storage GB per piano + addon €15/100 GB · meter + blocco 413  

---

## Cluster aperti (sintesi)

| Cluster | Finding |
|---------|---------|
| Media authorization | P3.1 + P4.1 + M-01 |
| Mongo ⟷ blob | M-02…M-04 · L-05/L-06 |
| Proiezioni/jobs vs D-094 | E-* · J-01…J-04 |
| AuthZ E2E | P4 cluster |
| Attività | domanda aperta |
| Costo infra / margine | C-* (P9) · bak full-copy · Agency ∞ |
| Trusted path tenant context | domanda aperta P8 |
| APScheduler in-process | area da verificare (deploy/affidabilità) — **non** finding |

---

## Progresso

| Sessione | Master | Stato |
|----------|--------|--------|
| P1–P5 | §1–§5 | acquisiti / finding aperti |
| P6 Proiezioni | fuori | **ACQUISITO** · E-* |
| P7 Media | §7 | **ACQUISITO** · D-095 · M-* |
| P8 Jobs | §15 | **ACQUISITO** · J-* · decisioni purge/trusted aperte |
| P9 Storage/costi | §8 | Consegnato · C-* |
| — | §6 Cestino | da blocco dedicato |
| — | §9 Backup | **prossimo naturale** |

Dettaglio: `AUDIT_ARCHITETTURA_NOTE.md` · A-035 · HAL `api.*` correlati.
