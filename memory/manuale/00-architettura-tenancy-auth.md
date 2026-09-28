# Cap. 00 · Architettura tenancy → backup/restore (audit SaaS)

**Ambito**: founder / super_admin.  
**Prompt master**: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27).  
**Numerazione sessione**: continuum in `AUDIT_ARCHITETTURA_NOTE.md`.

---

## Metodo

Un blocco alla volta · niente fix senza «vai» · no P0–P3 prematuri · **listino fermo** finché Backup+Restore non sono disegnati.

---

## Decisioni di dominio (codice ⏳)

### D-094 / D-095 / D-085
- Trash ≠ status · media pubblico/privato · quota GB + bak 30g  
- Promessa D-085 «ripristino via supporto» = **oggi senza tool** (P11)

---

## Cluster aperti

| Cluster | Finding |
|---------|---------|
| Media authorization | P3.1 + P4.1 + M-01 |
| Mongo ⟷ blob | M-02…M-04 · L-05/L-06 |
| Proiezioni/jobs vs D-094 | E-* · J-01…J-04 |
| Disaster recovery incompleto | B-* · **R-*** (no restore) |
| Costo infra massimo | C-* · B-01 ~31× · €/GB non confermato |
| Orchestrazione job | rimandata post design bak+restore |

---

## Progresso

| Sessione | Master | Stato |
|----------|--------|--------|
| P1–P9 | §1–§8 (+§15 Jobs) | acquisiti |
| P10 Backup | §9 | **ACQUISITO** · pesante, incompleto, no restore |
| P11 Restore | §10 | Consegnato · **NO** ripristino fedele da ieri |
| — | §11+ | prossimo su feedback Founder |

Dettaglio: `AUDIT_ARCHITETTURA_NOTE.md` · A-035 · HAL `api.backup-archivio` / `api.restore-disaster`.
