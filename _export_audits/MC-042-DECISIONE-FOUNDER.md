# MC-042 — Decisione Founder (consultazione CC non operativo)

**Data:** 18 novembre 2026 · Europe/Rome  
**ID inventario:** MC-042  
**Stato:** **DECISIONE FUNZIONALE APPROVATA DAL FOUNDER — 18/11/2026**  
**Implementazione codice:** **NON AUTORIZZATA** da questa decisione  
**SoT piano:** `MASTER-CHIUSURA-POST-AUDIT-PIANO.md`

---

## Testo vincolante (Founder)

Per un CommercialCustomer **non operativo** è consentita esclusivamente la consultazione in **sola lettura** di:

- documenti di **chiusura**;
- documenti di **fatturazione**.

Sono **vietati**:

- consultazione **operativa** del wallet;
- assegnazione di crediti;
- revoca di crediti;
- trasferimento di crediti;
- spesa di crediti.

Identità, nomine, ledger e storico restano **conservati**.  
La conservazione dei dati **non** comporta il diritto di consultarli operativamente.

---

## Coerenza con decisioni già chiuse

| Riferimento | Rapporto |
|---|---|
| **D05** | MC-042 **precisa** «consultazione limitata» (D05 / B16 / DES-07/08): whitelist = chiusura + fatturazione, read-only. Non riapre D05. |
| **DES-07 / DES-08** | Area amm./fatturazione e entitlements per stato: allineati al principio «no operativa wallet su CC non operativo». |
| **D01–D04, D06–D12** | Non modificati. |
| **D12** | Deny su mutate resta; MC-042 aggiunge il confine sulla **read operativa wallet**. |

---

## Distinzione obbligatoria

| Tipo | Stato |
|---|---|
| Decisione funzionale Founder | **APPROVATA** 18/11/2026 |
| Implementazione / enforcement in codice | **NON fatta** · richiede mandato esplicito successivo |
| Verifica conformità MC-026b | Deve segnalare lo scostamento codice↔decisione (vedi sotto) |

---

## Scostamento tecnico noto (sola evidenza, nessun fix)

Baseline `main` @ `c3baebc` (PR #216):

- `cc_allows_wallet_admin_read()` restituisce sempre `True` («consultazione limitata» non ristretta).
- `GET /billing/wallet` con `for_mutation=False` non applica un deny su CC non operativo e restituisce `wallet_summary` completo.
- Le **mutate** allocate/revoke restano bloccate da `cc_allows_wallet_mutation` su CC ceased / non operabile (coerente con il divieto di mutate in MC-042).

**Conclusione evidenza:** decisione funzionale OK; enforcement whitelist chiusura/fatturazione e deny read operativa wallet **ancora da implementare** (fuori da questo aggiornamento documentale).
