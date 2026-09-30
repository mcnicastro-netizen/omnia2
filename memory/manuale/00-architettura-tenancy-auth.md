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
| **D-100** | Invite: utente esistente → link agency; **mai** overwrite password (**fix-needed**) |
| **D-101** | Job automatici: **single-instance** ora (non lock multi-pod); worker poi |
| **D-102** | Purge + orphan cleanup: **automatizzare ora** nel ciclo APScheduler |
| **D-103** | No worker dedicato ora; eventuale anti-dup minimo stesso-giorno |
| **D-104** | **GTM-01 ACQUISITO** · in coda · **vincolo hard** pre-~5000 email |
| **D-105** | Bak health minimo Founder Ops (OK/PARTIAL/FAILED + alert + last_run) |
| **D-106** | `active_agency_id` = SoT sessione; `agency_ids` = membership |

**SoT continuità:** `docs/audit/OMNIA_AUDIT_STATE.md`  
**Sequenza priorità (D-099):** fascicolo → orphan → Bak+Restore → retention → costi.  
**Niente codice** senza «vai».

---

## Cluster aperti

| Cluster | Finding |
|---------|---------|
| Media / fascicolo AuthZ | P3.1 + M-01 + **G-02** → D-095/D-099 |
| Orphan / retention | RET-* · D-098 · **D-102** |
| Disaster recovery | B-* · R-* · D-096 |
| GDPR | G-* · D-099 (Founders assistito) |
| Race | **RC-*** · invite → **D-100** |
| Jobs | **J-*** · **JA-*** · **D-101**…**D-103** |
| Osservabilità | **O-*** · **D-105** |
| API / Frontend | **AF-*** |
| GTM / Demo | **GTM-01 ACQUISITO** · **D-104** · in coda · pre-~5000 email |
| Costo / listino | C-* · B-01 · fermo |

---

## Progresso

| Sessione | Master | Stato |
|----------|--------|--------|
| P1–P17 | §1–§16 | acquisiti · D-094…D-105 |
| P18 API/FE | §17 | Consegnato · AF-* |
| — | §18 Error handling… | prossimo tipico |
| GTM-01 | post-audit | 🟠 **ACQUISITO** · in coda |

Dettaglio: `docs/audit/OMNIA_AUDIT_STATE.md` · `AUDIT_ARCHITETTURA_NOTE.md` · A-035 · A-036.