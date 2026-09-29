# Cap. 00 · Architettura tenancy → GDPR (audit SaaS)

**Ambito**: founder / super_admin.  
**Prompt master**: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27).  
**Numerazione sessione**: continuum in `AUDIT_ARCHITETTURA_NOTE.md`.

---

## Metodo

Un blocco alla volta · niente fix senza «vai» · no P0–P3 prematuri · **listino fermo** finché Backup+Restore non sono disegnati.

---

## Decisioni di dominio (codice ⏳)

| ID | Sintesi |
|----|---------|
| **D-094** | Trash ≠ status · Cliente Trash → Richieste archiviate |
| **D-095** | Media pubblici vs privati · cleanup blob |
| **D-096** | Bak+Restore insieme · restore agency-first |
| **D-097** | Elimina per sempre ≠ irrecuperabile assoluto · trash in bak OK |
| **D-098** | Orphan → path a delete (WHEN col bak) · agency close V1 controllata |

---

## Cluster aperti

| Cluster | Finding |
|---------|---------|
| Media authorization | P3.1 + P4.1 + M-01 · **G-02** |
| Mongo ⟷ blob / orphan | M-* · RET-02 · **D-098** |
| Disaster recovery | B-* · R-* · D-096 |
| Cestino vs Backup | BC-* · D-097 |
| Retention | RET-* |
| GDPR / privacy | **G-01…G-12** |
| Costo / listino | C-* · B-01 · fermo |

---

## Progresso

| Sessione | Master | Stato |
|----------|--------|--------|
| P1–P13 | §1–§12 (+ anticipi) | acquisiti · D-094…D-098 |
| P14 GDPR | §13 | **ACQUISITO** · G-* |
| P15 race | §14 | Consegnato · RC-* |
| — | §15 job / §16+ | prossimo tipico |

Dettaglio: `AUDIT_ARCHITETTURA_NOTE.md` · A-035.
