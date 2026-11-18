# MC-054…059 — Sospensione, riattivazione, deroga Super Admin

**Data:** 18 novembre 2026 · Europe/Rome  
**Stato:** **DECISIONI FUNZIONALI APPROVATE DAL FOUNDER**  
**Implementazione codice:** autorizzata 18/11 (`OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE`) · branch `cursor/mc042-v2-suspend-deroga-e393`  
**Distinzione:** **non** confondere con **MC-042** (cessazione definitiva).  
**Registro:** D-178…D-182 · inventario master MC-054…059

---

## MC-054 — Cliente sospeso per mancato pagamento

### Grace (giorni 1–7)
- Piena operatività.
- Notifiche al Main Admin secondo regole già approvate.

### Dal giorno 8 (sospensione) — **opzione B Founder 18/11**
- Accesso operativo dei collaboratori **bloccato** (login/session deny).
- Main Admin **resta autenticabile** ma **limitato** a: pagamento, metodo di pagamento, fatture, recupero (billing allowlist).
- Consultazione del **wallet** bloccata (anche con `operational_status=billing_only`).
- Consultazione dei **crediti** bloccata.
- Assegnazione crediti bloccata.
- Revoca e trasferimento crediti bloccati.
- Spesa crediti bloccata.

---

## MC-055 — Riattivazione automatica

- Saldo **integrale** del dovuto confermato da Stripe → riattivazione **automatica**.
- Nessuna approvazione manuale ordinaria del Super Admin.
- Ripristino delle funzioni operative previste.
- Conservazione di crediti, assegnazioni e storico.
- Pagamento **parziale** → **nessuna** riattivazione.
- Riattivazione ordinaria **solo** a saldo completo.

---

## MC-056 — Deroga eccezionale Super Admin

Il Super Admin può autorizzare riattivazione eccezionale anche con debito residuo.

**Obbligatori:**
- Motivazione.
- Identificazione operatore.
- Identificazione CommercialCustomer.
- Importo ancora dovuto.
- Data e ora operazione.
- Durata della deroga.
- Data e ora di scadenza.
- Esito operazione.
- Registrazione permanente in audit log.

Nessuna deroga anonima o non tracciata.

---

## MC-057 — Durata della deroga

- Durata **caso per caso** (nessuna durata fissa generale).
- Ogni deroga ha **scadenza obbligatoria**.
- Alla scadenza:
  - se debito saldato → riattivazione definitiva dopo conferma Stripe;
  - se debito non saldato e nessuna nuova deroga valida → **sospensione automatica**.
- Proroga = **nuova** deroga motivata e tracciata.

---

## MC-058 — Comunicazioni automatiche (deroga)

**Alla concessione** — email al cliente con: conferma riattivazione, importo dovuto, durata, scadenza, avviso di nuova sospensione automatica se non saldo.

**48h prima della scadenza** — promemoria automatico al Super Admin.

**Alla scadenza senza saldo** — sospensione automatica + email cliente + notifica Super Admin + audit log.

---

## MC-059 — Deroghe indipendenti

- Ogni deroga è indipendente per CommercialCustomer.
- Durate/scadenze possono differire tra clienti.
- Una deroga **non** modifica stato/scadenze/debiti/deroghe di altri clienti.

---

## Stato tecnico vs codice (`main` @ `6a12932`, post #220) — evidenza verifica 18/11

Fonte: `_export_audits/VERIFICA-POST-MERGE-217-220-2026-11-18.md`.  
Tabella precedente @ `547f67f` (**NON CONFORME** wallet `billing_only`) è **superata** da #220.

| ID | Decisione | Codice attuale | Esito |
|---|---|---|---|
| MC-054 grace 1–7 | Piena operatività | `grace` → `operational_status=full` | **MODELLO OK** — notifiche grace non riesaminate E2E |
| MC-054 giorno 8 wallet/crediti | Deny read+allocate+revoke+transfer+spend | `cc_is_wallet_operable` nega `suspended`/`billing_only`; assert + `_spend_blocked` | **CONFORME** (unit) |
| MC-054 collaboratori / MA billing-only (opz. B) | Collab off; MA solo recovery | `enforce_commercial_access` + allowlist path | **CONFORME** unit · **NON VERIFICATO** E2E FE |
| MC-054 job giorno 8 | past_due ≥8g → suspended | `apply_day8_suspensions` + scheduler | **PRESENTE** |
| MC-055 riattivazione auto saldo pieno | Solo a saldo integrale | `invoice.paid` → `reactivate_cc_on_full_payment` + `list_outstanding_invoices_for_cc` (locale + Stripe open); skip se insoluti | **CONFORME** (fix post-verifica 18/11 · Founder «fix») |
| MC-055 no riattivazione parziale | — | Altro invoice `open` → `skipped: outstanding_balance` | **CONFORME** (unit) |
| MC-056…059 deroga | Sistema completo | Grant Ops + expire + reminder 48h + email best-effort + per-CC | **PRESENTE** (≠ D07) |

**D07** (Super Admin mutate wallet straordinarie) **non** è MC-056.

---

## Fuori scope di questo documento

- Fix codice MC-055 saldo (richiede autorizzazione Founder dedicata).
- Stripe live / produzione.
- Scelta primo slice Strato C.
