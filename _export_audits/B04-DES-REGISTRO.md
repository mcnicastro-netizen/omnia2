# B04 — Registro decisioni di design (Billing / ANO-008)

**Aggiornato:** 17 novembre 2026 · Europe/Rome  
**Natura:** design solo. **Nessuna implementazione autorizzata.**  
**Stato:** **DESIGN B04 CHIUSO** (DES-01…10).  
**SoT completo:** `_export_audits/B04-ANO-008-DESIGN-BILLING.md`

**Vincoli:** B01–B03 chiusi; decisioni B16 approvate non riapribili; B05–B07 esclusi.

---

## Decisioni approvate

| ID | Data | Oggetto | Stato |
| -- | ---- | ------- | ----- |
| B04-DES-01 | 17/11/2026 | CommercialCustomer ↔ Stripe Customer 1:1 stabile; cambio metodo non crea nuovo Customer | Approvata |
| B04-DES-02 | 17/11/2026 | State machine OMNIA distinta da Stripe; idempotenza / fuori ordine | Approvata |
| B04-DES-03 | 17/11/2026 | Catalogo versionato + snapshot; Founder 12m; baseline v3.3; repricing solo governance Founder | Approvata |
| B04-DES-04 | 17/11/2026 | Wallet / Lot / Allocation / Ledger; FIFO; permessi; atomicità; vincoli B16 | Approvata |
| B04-DES-05 | 17/11/2026 | Limiti utenti/immobili aggregati su P.IVA; hard-block atomico backend | Approvata |
| B04-DES-05b | 17/11/2026 | Conteggio portafoglio operativo; MLS 0; 1 ownership=1 slot; no `archived` implicito | Approvata |
| B04-DES-06 | 17/11/2026 | Allowance/cicli/upgrade/downgrade/grazia/idempotenza/cessazione (P01–P07 + X1…X3) | Approvata |
| B04-DES-07 | 17/11/2026 | Entitlements operativi per stato (pre-attivazione→cessazione) | Approvata |
| B04-DES-08 | 17/11/2026 | Area Amministrazione e fatturazione B2B (Main vs Branch Admin) | Approvata |
| MC-042 / D-176 | 18/11/2026 | Precisa consultazione CC non operativo: sola lettura chiusura+fatturazione; no wallet operativo (non riapre DES) | Approvata funzionale; codice non autorizzato |
| B04-DES-09 | 17/11/2026 | Mapping eventi Stripe → azioni OMNIA (principi, non auto-state) | Approvata |
| B04-DES-10 | 17/11/2026 | Casi limite multi-Organization; P.IVA invariabile; no transfer silenzioso | Approvata |

---

## Follow-up programma OMNIA (non design B04)

Vedi `B04-OPEN-FOLLOWUPS.md` → **B04-OPEN-01** (repricing).

---

## Confini

- Nessun codice, migrazione, Stripe live, deploy da questo registro.
- Implementazione solo con autorizzazione Founder esplicita + slice.
