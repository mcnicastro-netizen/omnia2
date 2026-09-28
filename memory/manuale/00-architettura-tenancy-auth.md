# Cap. 00 · Architettura tenancy, auth, media, jobs (audit SaaS)

**Ambito**: founder / super_admin.  
**Prompt master**: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27).  
**Stato**: ⏸ audit in pausa fino a «vai» Founder.

---

## Metodo

Un blocco alla volta · niente fix senza «vai» implementazione · no P0–P3 prematuri · aggiornare `AUDIT_ARCHITETTURA_NOTE.md`.

---

## Decisioni di dominio (codice ⏳)

### D-094
- `status` = commerciale · `trashed` = lifecycle  
- Trashed → escluso da feed/sync/pubblicazioni **senza** forzare `withdrawn`  
- Cliente Trash → Richieste **archiviate** (storico), non distrutte; restore non riapre  

### D-095
- Media **pubblici** vs **privati** · no “UUID = secret”  
- Cleanup blob indipendente da S3/R2 · idempotente  

---

## Cluster aperti (sintesi)

| Cluster | Finding |
|---------|---------|
| Media authorization | P3.1 + P4.1 + M-01 |
| Mongo ⟷ blob | M-02…M-04 · L-05/L-06 |
| Proiezioni/jobs vs D-094 | E-* · J-01…J-04 |
| AuthZ E2E | P4 cluster |
| Attività | domanda aperta |

---

## Progresso master

§1–§5 sostanzialmente fatti · §7 + pezzi §15 fatti · **§6 Cestino** e **§8 Storage/costi** tra i prossimi · resto ⬜.

Dettaglio: `AUDIT_ARCHITETTURA_NOTE.md` · A-035.
