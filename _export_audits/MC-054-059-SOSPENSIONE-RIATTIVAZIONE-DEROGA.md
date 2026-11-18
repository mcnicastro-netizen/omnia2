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

## Stato tecnico vs codice (`main` @ `547f67f`) — sola evidenza

| ID | Decisione | Codice attuale | Esito |
|---|---|---|---|
| MC-054 grace 1–7 | Piena operatività | `commercial_status=grace` → `operational_status=full` | **PARZIALE / MODELLO** — macchina notifiche Main Admin non riesaminata qui |
| MC-054 giorno 8 wallet/crediti | Deny consultazione + allocate/revoke/transfer/spend | `suspended` → `billing_only`; `cc_is_wallet_operable` **non** nega `billing_only`; spend sì (`_spend_blocked` include suspended); allocate/read **ancora possibili** | **NON CONFORME** su read/allocate/revoke; **PARZIALE** su spend |
| MC-054 collaboratori bloccati / MA solo billing | Entitlements DES-07 | Non verificato end-to-end in questo allineamento doc | **NON VERIFICATO** |
| MC-055 riattivazione auto saldo pieno | Stripe → auto | Non dichiarato implementato come regola prodotto in #218 | **MANCANTE / NON VERIFICATO** |
| MC-055 no riattivazione parziale | — | Non verificato | **NON VERIFICATO** |
| MC-056…059 deroga | Sistema completo | Assente come prodotto (D07 emergency wallet ≠ deroga riattivazione) | **MANCANTE** |

**D07** (Super Admin mutate wallet straordinarie) **non** è MC-056: non sostituisce deroga di riattivazione con debito.

---

## Fuori scope di questo documento

- Implementazione codice.
- Modifica Stripe/webhook.
- Merge PR #217.
- Firma MC-026b.
