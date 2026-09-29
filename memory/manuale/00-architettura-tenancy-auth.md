# Cap. 00 · Architettura tenancy → retention (audit SaaS)

**Ambito**: founder / super_admin.  
**Prompt master**: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27).  
**Numerazione sessione**: continuum in `AUDIT_ARCHITETTURA_NOTE.md`.

---

## Metodo

Un blocco alla volta · niente fix senza «vai» · no P0–P3 prematuri · **listino fermo** finché Backup+Restore non sono disegnati.

---

## Decisioni di dominio (codice ⏳)

### D-094 / D-095 / D-085
Trash ≠ status · media pubblico/privato · quota GB + bak 30g

### D-096
Bak+Restore insieme · restore **agency-first** · listino fermo

### D-097
«Elimina per sempre» = fuori area operativa utente; supporto **MAY** bak valido.  
Trash **può** restare nel backup. Copy prodotto da riallineare.

---

## Cluster aperti

| Cluster | Finding |
|---------|---------|
| Media authorization | P3.1 + P4.1 + M-01 |
| Mongo ⟷ blob | M-02…M-04 · L-05/L-06 · T-02 · **RET-02** |
| Disaster recovery | B-* · R-* · D-096 |
| Cestino vs Backup | BC-* · T-* · **D-097** |
| Retention incompleta | **RET-*** (orphan ∞ · no offboarding) |
| GDPR / privacy | **G-*** (erase ≠ wipe · fascicolo/media · DPA) |
| Costo infra / listino | C-* · B-01 · fermo |

---

## Progresso

| Sessione | Master | Stato |
|----------|--------|--------|
| P1–P12 | §1–§11 (+ anticipi) | acquisiti / D-094…D-097 |
| P13 Retention | §12 | **ACQUISITO** · RET-* |
| P14 GDPR | §13 | Consegnato · G-* |
| — | §14 race… | prossimo tipico |

Dettaglio: `AUDIT_ARCHITETTURA_NOTE.md` · A-035.
