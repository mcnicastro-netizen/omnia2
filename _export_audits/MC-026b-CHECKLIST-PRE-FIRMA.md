# MC-026b — Checklist pre-firma Founder (non firmata)

**Aggiornato:** 18 novembre 2026 · Europe/Rome  
**ID:** MC-026b  
**Stato:** **FIRMATA DAL FOUNDER** 18/11/2026 — `CONFORME CON RISERVE` (vedi §E)  
**Baseline codice:** `main` @ `547f67f` (include PR #216 H2 + PR #218 MC-042 wallet/fail-open)  
**Scopo:** riesame conformità D01–D12 + decisioni 18/11 (MC-042 v2, MC-054…059) **senza** chiusura automatica.

---

## Legenda

| Esito | Significato |
|---|---|
| CONFORME | Evidenza codice allineata alla decisione |
| NON CONFORME | Evidenza di scostamento |
| PARZIALE | Solo una parte allineata |
| NON VERIFICATO | Non riesaminato end-to-end in questo passaggio |
| N/A DECISIONE | Solo funzionale; codice non ancora in scope |

---

## A. D01–D12 (H2 Main Admin) — sintesi

| Tema | Esito | Nota |
|---|---|---|
| D01–D04, D06–D12 (binding, transfer 48h, Cabina, multi-CC, idoneità, D07) | PARZIALE → vedi MC-026a | Codice mergiato (#216); **accettazione Founder ancora aperta** |
| D05 cessazione (storico) | vedi MC-042 v2 sotto | Precisata/restituita da MC-042 v2 |

*(Dettaglio D01–D12: report H2 residuale + conformity — non ripetuto qui.)*

---

## B. MC-042 v2 — cessazione definitiva (18/11 aggiornata)

| Requisito | Tipo | Esito | Nota |
|---|---|---|---|
| Decisione funzionale v2 vigente | Funzionale | CONFORME (doc) | SoT `MC-042-DECISIONE-FOUNDER.md` · D-177 |
| Login/password disattivati | Implementativo | NON CONFORME / NON VERIFICATO | Non parte di #218 |
| Nessun accesso autonomo piattaforma | Implementativo | NON CONFORME | Gate wallet ≠ lockout totale |
| Nessuna consultazione autonoma fatture/documenti | Implementativo | PARZIALE | Nessuna API self-serve (di fatto); manca canale Super Admin |
| Nessun accesso wallet | Implementativo | PARZIALE | Deny wallet su ceased post-#218 |
| Conservazione dati | Implementativo | CONFORME (principio) | No delete su cease documentato |
| Whitelist autonoma chiusura+fatturazione (v1) | Funzionale | **SUPERATA** | Non più requisito |

**MC-042 formalmente chiusa?** **NO.**

---

## C. MC-054…059 — sospensione / riattivazione / deroga

| ID | Esito | Nota |
|---|---|---|
| MC-054 giorno 8: deny wallet read/allocate/revoke/transfer/spend | NON CONFORME (read/allocate/revoke); PARZIALE (spend) | `billing_only` ancora operable per wallet admin read/mutate |
| MC-054 collaboratori / MA solo billing | NON VERIFICATO | |
| MC-055 riattivazione auto saldo pieno Stripe | MANCANTE / NON VERIFICATO | |
| MC-056…059 sistema deroga + email + scadenza | MANCANTE | ≠ D07 emergency wallet |

---

## D. Separazione discrepanze

### Funzionali (decisioni ancora da confermare / firmare)
- MC-040, MC-041, MC-043 — `PENDING_FOUNDER`
- Firma MC-026b stessa
- Firma MC-052 `MASTER STRATO B CHIUSO`

### Implementative (codice vs decisione già approvata)
- MC-042 v2 lockout totale + canale Super Admin
- MC-054 deny wallet/crediti dal giorno 8 (oltre spend)
- MC-055…059 riattivazione/deroga/comms

### Residui accettabili solo se Founder li firma come riserva
- Nessuno auto-accettato da Cursor.

---

## E. Formula firma (solo Founder) — **COMPILATA**

- [x] `CONFORME CON RISERVE`:
  1. MC-042 v2 lockout totale + Super Admin via email — da implementare
  2. MC-054 giorno 8 deny wallet/crediti completo — da implementare (spend già ok)
  3. MC-055…059 riattivazione/deroga/comms — da implementare
- Data / Founder: **18 novembre 2026** · Marco Nicastro

MC-040 / MC-041 / MC-043: decisioni funzionali **prese** lo stesso giorno (pulsante Cabina; job expiry; nomina obbligatoria) — implementazione autorizzata esplicitamente.
