# Cap. 00 · Architettura tenancy → jobs (audit SaaS)

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
| **D-099** | Founders GDPR assistito · fascicolo AuthZ **prima** del bak |
| **D-100** | Invite: utente esistente → link agency; **mai** overwrite password |

**Sequenza priorità (D-099):** fascicolo → orphan → Bak+Restore → retention → costi.

---

## Cluster aperti

| Cluster | Finding |
|---------|---------|
| Media / fascicolo AuthZ | P3.1 + M-01 + **G-02** → D-095/D-099 |
| Orphan / retention | RET-* · D-098 |
| Disaster recovery | B-* · R-* · D-096 |
| GDPR | G-* · D-099 (Founders assistito) |
| Race | **RC-*** · invite → **D-100** |
| Jobs | **J-*** · **JA-*** · single-instance Founder |
| Costo / listino | C-* · B-01 · fermo |

---

## Progresso

| Sessione | Master | Stato |
|----------|--------|--------|
| P1–P14 | §1–§13 (+ anticipi) | acquisiti · D-094…D-099 |
| P15 Race | §14 | **ACQUISITO** · RC-* · D-100 |
| P16 Jobs deepen | §15 | Consegnato · JA-* |
| — | §16 Osservabilità… | prossimo tipico |

Dettaglio: `AUDIT_ARCHITETTURA_NOTE.md` · A-035.
