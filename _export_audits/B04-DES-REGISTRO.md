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
| B04-DES-03 | 17/11/2026 | Listino versionato + snapshot termini; no modifica automatica/retroattiva; Founder→Standard 12 mesi; baseline v3.3. Repricing esistenti solo con decisione Founder + comunicazione + decorrenza + accettazione/rifiuto | Approvata |
| B04-DES-04 | 17/11/2026 | Wallet centrale per CommercialCustomer; CreditLot; CreditAllocation; CreditLedgerEntry; FIFO; permessi; atomicità. Vincoli B16 | Approvata |
| B04-DES-05 | 17/11/2026 | Limiti utenti/immobili aggregati sul CommercialCustomer (P.IVA); hard-block backend atomico; no plafond per filiale; no aggiramento via nuova Organization stessa P.IVA | Approvata |
| B04-DES-05b | 17/11/2026 | Conteggio immobili = portafoglio operativo (`draft`/`active`/`reserved` sì; `sold`/`rented`/`withdrawn`/cestino no); MLS 0 slot; 1 ownership = 1 slot; restore/reopen richiedono slot; storage indipendente; no status `archived` implicito | Approvata |
| B04-DES-06 | 17/11/2026 | Ciclo subscription / allowance / rinnovi / upgrade / downgrade / insoluto+grazia / idempotenza / cessazione-disdetta (P01–P07 + P07-X1…X3). **CHIUSO** sul piano funzionale | Approvata / chiusa |

---

## B04-DES-06 — Sintesi punti (P01–P07)

| Punto | Tema | Stato |
| ----- | ---- | ----- |
| P01 | Periodicità allowance | Approvato |
| P02 | Rinnovo ordinario | Approvato |
| P03 | Upgrade | Approvato |
| P04 | Downgrade | Approvato |
| P05 | Insoluto e grazia | Approvato |
| P06 | Idempotenza e riconciliazione | Approvato |
| P07 | Cessazione e disdetta | Approvato (+ X1…X3) |

> Nota programma: il dump narrativo integrale P01–P06 vive nella sessione ChatGPT Founder; qui restano ID, chiusura e precisazioni X vincolanti. Se serve archivio verbatim in `_export_audits/`, il Founder lo chiede esplicitamente.

### P07 — Cessazione e disdetta (base)

1. La richiesta di disdetta non interrompe immediatamente il servizio.
2. Il cliente rimane operativo fino alla fine del periodo già pagato (salvo regole X3 se in insoluto).
3. Alla scadenza si applicano le regole di cessazione B16.
4. Crediti residui: non rimborsati, non liquidati, non trasferiti.
5. Dopo cessazione effettiva non maturano nuove allowance.
6. Data richiesta disdetta ≠ data cessazione effettiva.

### P07-X1 — Crediti residui dopo cessazione effettiva

- Restano nel ledger permanente (DES-04).
- Diventano non spendibili / inesigibili operativamente.
- Vietato azzerare silenziosamente lotti o cancellare lo storico.

### P07-X2 — Ambito CommercialCustomer

- Disdetta e cessazione agiscono sulla P.IVA / tutte le Organization collegate.
- Nessuna filiale resta operativa sui diritti del piano dopo cessazione effettiva.

### P07-X3 — Regola temporale disdetta × insoluto/grazia (17/11/2026)

Approvata integralmente dal Founder:

- **Pagamenti regolari:** cessazione alla fine dell'ultimo periodo pagato.
- **Insoluto durante la grazia:** se il pagamento viene recuperato → cessazione alla fine del periodo di servizio regolarizzato; se non recuperato → cessazione alla fine dei **7 giorni di grazia**.
- **Nessuna sospensione ordinaria al giorno 8** se la disdetta è già stata richiesta durante la grazia e non c’è stato recupero.
- **Fatture insolute:** il debito resta dovuto anche dopo la cessazione.
- **Disdetta dopo la sospensione:** non riavvia né prolunga la grazia.
- **Crediti residui:** come X1 (storico permanente, non spendibili, no rimborso/liquidazione/transfer).

---

## Follow-up programma OMNIA (non ChatGPT ora)

Vedi `B04-OPEN-FOLLOWUPS.md` → **B04-OPEN-01** (repricing dopo chiusura design B04).

---

## Confini

- Nessun codice, migrazione, Stripe live, deploy.
- DES-01…06 chiuse sul design; prossimo tema B04 solo su richiesta Founder.
- Fermarsi a fine design B04 complessivo prima di qualsiasi implementazione.
