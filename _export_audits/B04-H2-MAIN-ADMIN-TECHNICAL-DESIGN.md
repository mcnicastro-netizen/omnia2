# B04-H2 — Progettazione tecnica Main Admin commerciale
## Opzione A: `main_admin_user_id` su CommercialCustomer

**Data:** 17 novembre 2026 · Europe/Rome (aggiornato chiusura §14 ~19:30)  
**Baseline codice:** `main` @ `3b425a8e53e29a14fa209f050a58530231bd3fa8`  
**Mandato documenti:** sola lettura / progettazione — **nessun codice, DB, commit, PR implementativa, merge**  
**Opzione:** A — `main_admin_user_id` (senza auto da `owner_id` / `agency_admin` / prima org)  
**§14:** **CHIUSO** — decisioni Founder D01–D12 (vedi `B04-H2-MAIN-ADMIN-DECISIONS-CONFORMITY.md`)

SoT vincolanti: B01-DEC-02, B01 §6.3, B02-DEC-01, B16 interventi straordinari, DES-04, DES-08, H1 (PR #212), decisioni Founder D01–D12.

---

## Riepilogo esecutivo

**Modello:** Opzione A con binding **esplicito e versionato** sul CommercialCustomer (campo + metadati + eventi append-only + transfer 2 fasi). Non un campo opaco isolato.

| Elemento | Valore (decisioni Founder + design) |
|---|---|
| Binding attivo | `commercial_customers.main_admin_user_id: str \| null` |
| Metadati nomina | `main_admin_appointed_at`, `main_admin_appointed_by` (+ reason/origine in eventi) |
| Storia | `commercial_main_admin_events` append-only |
| Guard wallet ordinario | **solo** `user.id == cc.main_admin_user_id` + idoneità; `null` → **deny** |
| Super Admin su allocate/revoke | **D07:** solo **straordinario** motivato + audit; non privilegio ordinario; non nomina implicita |
| Nomina iniziale | **D01:** solo Super Admin Ops — mai self-nominate / owner / agency_admin |
| Sostituzione | propose→accept; attori propose: Main Admin corrente **o** Super Admin; accept solo designato |
| TTL proposta | **D09: 48 ore** |
| Notifica | **D08:** sempre Cabina; email Resend best-effort; email ≠ prerequisito accept |
| Revoca effettiva | runtime deny se non idoneo; clear campo solo atto esplicito Ops |
| Migrazione | nessuna auto-euristica; CC esistenti `null` finché Ops nomina |

**Implementazione codice:** solo dopo mandato Founder esplicito successivo. H3/H4/legacy esclusi.

---

## 1. Modello dati proposto

### 1.1 Estensione `CommercialCustomer` (documento)

```text
commercial_customers:
  ...campi B04-I esistenti...
  main_admin_user_id: string | null     # User.id del Main Admin attivo
  main_admin_appointed_at: ISO8601 | null
  main_admin_appointed_by: string | null  # user_id attore (Main Admin precedente o super_admin)
```

Vincoli:
- Al più un Main Admin attivo → unicità implicita del singolo campo (non array).
- Indice non-unique su `main_admin_user_id` (lookup “quali CC amministra questo user”).
- `null` = **nessun Main Admin** → wallet admin deny-by-default (non “chiunque”).

### 1.2 Eventi di autorità (append-only)

```text
commercial_main_admin_events:
  id, commercial_customer_id, event_type, actor_user_id,
  previous_main_admin_user_id, new_main_admin_user_id,
  reason, request_id, outcome, created_at, meta (no secrets)
```

`event_type` ∈:
`nominate` | `propose_transfer` | `accept_transfer` | `cancel_transfer` |
`revoke` | `clear_on_cessation` | `deny_attempt` | `runtime_block`

### 1.3 Trasferimento in corso (stato temporaneo)

Opzione consigliata: documento di pending transfer **separato** (non mutare ancora `main_admin_user_id`):

```text
commercial_main_admin_transfers:
  id, commercial_customer_id,
  from_user_id, to_user_id,
  status: pending | accepted | cancelled | expired,
  token_hash, expires_at, created_by, created_at, resolved_at
```

Atomicità accettazione: `find_one_and_update` su transfer `pending` + set `main_admin_user_id` nello stesso flusso transazionale/logico.

### 1.4 Cosa non introdurre in questa slice

- Nuovo `users.role = main_admin` globale (confligge con multi-CC futuro e con Membership org).
- Auto-link Representation (non implementata).
- Flag `is_hq` su Organization come surrogate del Main Admin.

---

## 2. Relazioni User / CommercialCustomer / Organization

```text
Person ──< User
              │
              │  (binding commerciale esplicito)
              ▼
         CommercialCustomer  ←── agencies.commercial_customer_id ── Organization(s)
              │
              └── main_admin_user_id ──► User (uno solo)

User ── Membership ──► Organization   (ruoli operativi: agency_admin, branch_admin, …)
```

Regole:
- Main Admin è autorità sul **CC**, non una Membership org.
- La stessa persona può essere Main Admin **e** `agency_admin` di una org: sono poteri distinti (B01-DEC-02). Il guard wallet usa **solo** il binding CC.
- Organization admin (`agency_admin` / `branch_admin`) **non** eredita wallet centrale.
- `owner_id` resta titolarità/creazione org — **mai** fonte del Main Admin.

---

## 3. Regole di nomina e sostituzione

### 3.1 Identificazione (valutazione regole proposte)

| Regola proposta Founder | Valutazione tecnica |
|---|---|
| Un solo Main Admin attivo | OK — campo scalare |
| Deve essere User esistente | OK — check `users.id` |
| Email verificata + account operativo (B03) | OK — riuso `email_verified` + `is_active` |
| Non dedotto da owner / agency_admin / prima org | OK — **obbligatorio** |
| Verifica backend a ogni op wallet | OK — dependency dedicata |

### 3.2 Nomina iniziale (chi ha titolo) — **D01**

**Decisione Founder (vincolante):**

1. **Attore ammesso:** solo `super_admin` (Cabina Ops), tramite endpoint dedicato  
   `POST /ops/commercial-customers/{cc_id}/main-admin` (o equivalente founder_ops).
2. **Payload:** `user_id` del designato (non preso da cookie del designato).
3. **Precondizioni designato:** user esiste, `is_active`, `email_verified`. Multi-CC consentito (**D02**): non rifiutare solo perché già Main Admin altrove.
4. **Precondizione CC:** `main_admin_user_id is null` **oppure** sostituzione/transfer esplicito (non overwrite silenzioso).
5. **Tracciamento:** evento `nominate` + set metadati appointed_*.
6. **Divieto:** nessun endpoint pubblico in cui un `agency_admin` setta `main_admin_user_id` su se stesso o su altri.

Membership **non** richiesta (**D03**). Nessuna auto-nomina in onboarding.

### 3.3 Sostituzione (passaggio di consegne) — decisioni D08/D09/D10

Flusso **a due fasi** (vincolante):

1. **Propose** (`propose_transfer`)
   - Attore: Main Admin corrente **oppure** Super Admin.
   - Target: User esistente, active, email verified.
   - Crea transfer `pending` + token (solo **hash** persistito), **TTL = 48 ore (D09)**.
   - **Notifica Cabina sempre (D08)**; email Resend **best-effort** (esito invio auditato). Fallimento email **non** invalida la proposta.
2. **Accept** (`accept_transfer`) — **D10**
   - Attore: **solo** il `to_user_id` autenticato, con token valido non scaduto/non usato.
   - Atomico: chiude transfer + scrive `main_admin_user_id = to_user_id`.
   - Evento `accept_transfer`. La proposta **non** conferisce privilegi prima dell’accept.
3. **Cancel / Expire**
   - Main Admin corrente o Super Admin cancella; expiry a 48h → non accettabile.
   - `main_admin_user_id` resta invariato fino ad accept riuscito.

**Concorrenza:** un solo transfer `pending` per CC (unique partial index). Secondo propose → 409. Mai due Main Admin attivi.

**Assenza temporanea (D11):** se Main Admin non idoneo ma campo ancora settato → wallet admin **bloccato**; nuova nomina solo Super Admin Ops (no auto-passaggio). Se titolare non idoneo, il transfer ordinario **non** aggirare il blocco senza percorso Ops.

---

## 4. Regole di revoca e sospensione

| Evento | Effetto su binding | Effetto su wallet admin |
|---|---|---|
| User `is_active=false` | campo **non** auto-cancellato | **deny** runtime |
| Email non più verificata / gate B03 fail | idem | **deny** |
| User cancellato / non trovato | raccomandare clear Ops + evento | **deny** |
| Fine Membership su una org | **nessun** effetto automatico sul Main Admin | invariato (potere commerciale ≠ membership) |
| Cambio ruolo org → branch_admin | **nessun** effetto automatico | invariato se binding CC resta |
| Revoca esplicita Ops | `main_admin_user_id = null` + evento `revoke` | deny finché nuova nomina |
| CC `ceased` | **D05:** conservare binding/storia; no clear automatico obbligatorio | deny mutazioni; consultazione limitata DES-07/08 + B16 |
| Sostituzione completata | nuovo user_id | vecchio perde potere immediatamente |

**Niente trasferimenti automatici** di autorità (allineato alla richiesta Founder).

---

## 5. Matrice dei permessi (riconciliata DES-04 / DES-08)

| Operazione | Main Admin (binding CC) | agency_admin (org) | branch_admin | group_admin | super_admin |
|---|---|---|---|---|---|
| Leggere wallet centrale | Sì (a) | **No** | **No** | **No** (b) | Consultazione ops/audit sì |
| Ledger centrale | Sì (a) | No | No | No (b) | Consultazione ops sì |
| Tutte le allocazioni del CC | Sì (a) | No | No | No (b) | Consultazione ops sì |
| Allocare / Revocare / Redistribuire | Sì (a) | No | No | No (b) | Solo straordinario (c) |
| `GET /wallet/organization` propria org | Sì se contesto org ok | Sì | Sì | secondo permessi esistenti | Sì |
| Consumi propria org | idem | Sì | Sì | secondo permessi | Sì |

(a) Binding match + account idoneo + CC ammissibile (**D12**).  
(b) **D06** — no wallet senza nomina Main Admin.  
(c) **D07** — eccezione motivata + audit; non privilegio ordinario; non cambia `main_admin_user_id`.

H1 resta: revoke filtra sempre `commercial_customer_id` del chiamante autorizzato.

---

## 6. Endpoint da modificare / aggiungere

### 6.1 Da modificare (wallet)

| Endpoint | Oggi | Dopo |
|---|---|---|
| `GET /billing/wallet` | exact agency_admin/group_admin/super_admin | Main Admin ordinario; super_admin lettura ops |
| `POST /billing/wallet/allocate` | idem | Main Admin **oppure** Super Admin **straordinario D07** |
| `POST /billing/wallet/revoke` | idem + H1 CC bind | Main Admin + H1 **oppure** Super Admin straordinario D07 |
| `GET /billing/wallet/organization` | org-scoped | **invariato** (branch/agency ok) |

### 6.2 Da aggiungere (Ops / ciclo vita)

| Endpoint | Attore | Scopo |
|---|---|---|
| `POST /ops/.../main-admin` | super_admin | nomina iniziale / revoke / force-set con audit |
| `POST /billing/commercial/main-admin/transfer` | Main Admin o super_admin | propose |
| `POST /billing/commercial/main-admin/transfer/accept` | designato | accept |
| `POST /billing/commercial/main-admin/transfer/cancel` | Main Admin o super_admin | cancel |
| `GET /billing/commercial/main-admin` | Main Admin o super_admin | stato binding (no PII eccessiva) |

Path esatti da allineare alle convenzioni `founder_ops` esistenti in implementazione.

---

## 7. Controlli backend necessari

```text
resolve_cc_for_request(user) → cc_id
load cc
# percorso ordinario:
assert cc.main_admin_user_id == user.id
assert user.is_active and email_verified
assert cc commercial/operational allows the action (DES-07; ceased → no mutate)
# percorso Super Admin mutate (allocate/revoke only):
assert role==super_admin AND extraordinary_reason non-empty AND audit written (D07)
# lettura ops super_admin: consentita con audit accesso
deny 403 main_admin_required | main_admin_unassigned | account_not_eligible | cc_not_operable | forbidden
```

- **Non** fidarsi di `agency_id` / `allocation_id` client come prova di autorità commerciale.
- Preservare H1: revoke con `commercial_customer_id` obbligatorio dal CC del chiamante autorizzato.
- Rimuovere `agency_admin` / `group_admin` da `_WALLET_MAIN_ADMIN` attuale.
- Dependency nuova: `require_commercial_main_admin` (+ helper `require_super_admin_wallet_emergency` per D07).

---

## 8. Audit log necessario

Minimo eventi (senza segreti/token in chiaro):

| Evento | Campi chiave |
|---|---|
| nominate | actor, cc_id, new_user_id, outcome |
| propose_transfer | actor, cc_id, from, to, transfer_id, expiry |
| accept_transfer | actor(=to), cc_id, from, to |
| cancel_transfer / expired | actor/system, transfer_id |
| revoke / clear | actor, cc_id, previous |
| wallet_admin_access | actor, cc_id, route, outcome success\|denied |
| deny_attempt | actor, cc_id, reason_code (`not_main_admin`, `unassigned`, `inactive`, …) |
| runtime_block | user_id, cc_id, reason (inactive/unverified) |

Correlazione: `request_id` se disponibile. Retention: allineare policy audit OMNIA (B02 target `audit_events`; finché assente, collezione dedicata sopra).

---

## 9. Strategia CommercialCustomer esistenti

| Caso | Azione |
|---|---|
| CC con `main_admin_user_id = null` | **Stato atteso post-deploy** — wallet admin deny; Ops nomina |
| Evidenze ambigue (più agency_admin, owner diversi) | **Nessuna auto-scelta** — ticket riconciliazione |
| Un solo candidato “ovvio” | Ancora **no auto**; Ops conferma esplicita |
| CC ceased | null o freeze (§14) |
| Rollback schema | campo nullable → rimuovere guard nuovi e ripristinare? (vedi §13) |

Report read-only pre-migrazione (da autorizzare separatamente):

```js
db.commercial_customers.aggregate([
  {$group:{_id:{has_ma:{$ne:["$main_admin_user_id",null]}}, n:{$sum:1}}}
])
// + join agencies/users per dossier Ops — senza scrivere
```

---

## 10. Piano di migrazione proposto (non eseguito ora)

1. **Auth Founder** all’implementazione (campo + guard + Ops API + transfer).
2. Deploy codice con campo nullable + guard deny-if-null (**breaking** per agency_admin che oggi leggono wallet — **voluto**).
3. Tool Ops: lista CC senza Main Admin + UI nomina.
4. Riconciliazione umana batch (priorità CC con wallet/lots > 0).
5. Nessun job “auto-nominate from owner_id”.
6. Criterio done: 0 CC *attivi con spendable/unallocated > 0* senza Main Admin, oppure eccezioni firmate Founder.

---

## 11. Test (unit / integrazione / sicurezza)

### Unit
- `require_commercial_main_admin` allow/deny matrix.
- nominate solo super_admin; self-nominate agency_admin → 403.
- transfer: propose/accept/cancel/expire/concurrent 409.
- runtime deny se inactive / unverified.
- H1 revoke cross-tenant ancora 404 senza mutazione.

### Integrazione HTTP
1. Main Admin → GET wallet / allocate / revoke 200.
2. agency_admin filiale → 403; dati invariati.
3. branch_admin → 403 centrali; GET organization 200 scoped.
4. Main Admin altro CC → 403.
5. agency_admin → solo organization propria.
6. Manipolazione `commercial_customer_id` / `allocation_id` client → ignore/deny.
7. Regressione B04-I, B04-II, Slice1, H1 suite.

### Sicurezza
- Token transfer non loggato in chiaro; accept senza token → fail.
- super_admin force-set sempre auditato.

---

## 12. Criteri di accettazione

H2 residuo **chiuso** solo se:
1. Esiste binding persistito CC ↔ User Main Admin.
2. Wallet centrale admin ordinario **solo** via binding Main Admin; Super Admin solo via percorso straordinario D07.
3. `agency_admin` / `branch_admin` **non** amministrano il wallet centrale.
4. Nomina/sostituzione/revoca esplicite, auditabili, senza auto-euristiche vietate.
5. CC senza Main Admin → deny (non fallback permissivo).
6. H1 invariato.
7. Test §11 verdi in CI.
8. Decisioni §14 approvate Founder prima del merge implementativo.

---

## 13. Rischi e rollback

| Rischio | Mitigazione |
|---|---|
| Lock-out operativo (CC senza Main Admin) | Ops nominate path + runbook; emergenza D07 solo se motivata |
| Confusione Owner/Main Admin | UI/copy espliciti; mai sync da owner_id |
| Transfer hijack | token hash, TTL, accept solo to_user |
| Regressione agency_admin che usavano /wallet | intenzionale; comunicare breaking |
| Rollback | feature flag `MAIN_ADMIN_WALLET_GUARD` (opzionale) o revert PR; campo nullable innocuo se guard disattivato |

---

## 14. Decisioni Founder — REGISTRO CHIUSO (D01–D12)

§14 **non è più aperto**. Testo vincolante completo in  
`B04-H2-MAIN-ADMIN-DECISIONS-CONFORMITY.md`.

| ID | Sintesi |
|---|---|
| D01 | Nomina iniziale: solo Super Admin Ops |
| D02 | Multi-CC consentito |
| D03 | Membership non obbligatoria; no CRM da nomina |
| D04 | Fine Membership ≠ clear Main Admin |
| D05 | CC ceased: no admin operativa; conserva storia; consultazione limitata |
| D06 | `group_admin` senza nomina = no wallet |
| **D07** | Super Admin allocate/revoke **solo straordinario** motivato + audit |
| **D08** | Cabina sempre + email Resend best-effort |
| **D09** | TTL transfer **48 ore** |
| D10 | Transfer effettivo solo post-accept |
| D11 | Perdita idoneità → blocco; no auto-successione |
| D12 | Deny immediato su endpoint admin; breaking `/wallet` accettato |

---

## Compatibilità H1 / codice attuale (sintesi)

- H1 (`commercial_customer_id` su revoke) **compatibile** e da preservare.
- `_WALLET_MAIN_ADMIN = require_roles_exact(..., agency_admin, ...)` va **sostituito**, non esteso.
- Representation assente → non usarla.
- Audit privacy/domain esistenti non coprono eventi commerciali → collezione dedicata.

---

## Condizione di chiusura di questo aggiornamento documentale

Documenti aggiornati con §14 **chiuso**.  
**Nessuna** modifica codice/DB/commit/PR implementativa/merge.  
**Nessun** H3/H4/legacy.  
Implementazione: **solo** con mandato Founder esplicito successivo (prompt ChatGPT già predisposto).
