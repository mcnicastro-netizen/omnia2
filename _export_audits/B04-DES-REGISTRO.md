# B04 — Registro decisioni di design (Billing / ANO-008)

**Aggiornato:** 17 novembre 2026 · Europe/Rome  
**Natura:** design solo. **Nessuna implementazione autorizzata.**  
**Vincoli:** B01–B03 chiusi; decisioni B16 approvate non riapribili; B05–B07 esclusi.

---

## Decisioni approvate

| ID | Data | Oggetto | Stato |
| -- | ---- | ------- | ----- |
| B04-DES-01 | 17/11/2026 | Collegamento stabile uno-a-uno CommercialCustomer ↔ Stripe Customer; cambio carta/metodo non crea nuovo Customer né nuova subscription | Approvata |
| B04-DES-02 | 17/11/2026 | Macchina a stati OMNIA (commerciale + operativa) distinta da Stripe; eventi Stripe alimentano, OMNIA decide; idempotenza / fuori ordine / traccia | Approvata |
| B04-DES-03 | 17/11/2026 | Listino versionato + fotografia economica per subscription; no modifica automatica/retroattiva; Founder→Standard 12 mesi; baseline v3.3. Precisazione: repricing su esistenti solo con decisione Founder + comunicazione + decorrenza + accettazione/rifiuto | Approvata |
| B04-DES-04 | 17/11/2026 | Wallet centrale per CommercialCustomer; CreditLot; CreditAllocation per Organization; CreditLedgerEntry permanente; FIFO; Main Admin vs Branch Admin; operazioni atomiche. Vincoli B16 (upgrade/downgrade, no scadenza crediti, insoluto, cessazione, uscita filiale, no transfer cross-P.IVA) | Approvata |

---

## Follow-up programma OMNIA (non ChatGPT ora)

Vedi `B04-OPEN-FOLLOWUPS.md` → **B04-OPEN-01** (approfondimento processo repricing dopo chiusura design B04).

---

## Confini

- Nessun codice, migrazione, Stripe live, deploy.
- Fermarsi a fine design B04.
