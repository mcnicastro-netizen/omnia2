# B04-H2 residuo Main Admin — DECISIONE RICHIESTA (STOP implementazione)

**Data:** 17 novembre 2026 · Europe/Rome  
**Commit di partenza (`main`):** `3b425a8e53e29a14fa209f050a58530231bd3fa8`  
**Mandato:** completamento residuo H2 (Main Admin vs agency_admin di filiale)  
**Esito:** **STOP** — le strutture esistenti non consentono di identificare il Main Admin in modo autorevole senza una decisione strutturale.  
**Nessuna modifica funzionale al wallet implementata in questo branch.** H3/H4/legacy/B04-III non avviati. Nessun merge.

---

## 1. Problema

Dopo PR #212, `require_roles_exact` esclude `branch_admin` dagli endpoint wallet admin, ma un utente con ruolo letterale `agency_admin` su **qualsiasi** Organization del CommercialCustomer (anche una filiale) può ancora:

- `GET /billing/wallet`
- `POST /billing/wallet/allocate`
- `POST /billing/wallet/revoke`

Questo viola DES-04 / DES-08: solo il **Main Admin del CommercialCustomer** amministra il wallet centrale.

---

## 2. Analisi obbligatoria (codice effettivo)

### 2.1 Come è identificato oggi il “Main Admin”?

**Non lo è.** Nel codice implementato non esiste:

- ruolo DB `main_admin`
- campo `commercial_customers.main_admin_user_id` (o equivalente)
- membership commerciale verso il CommercialCustomer
- entità `Representation` implementata

Il commento di route “Main Admin” è **etichetta documentale**: il guard effettivo è solo `require_roles_exact("super_admin", "agency_admin", "group_admin")` + `require_agency(user)` → `resolve_cc_id_for_agency`.

### 2.2 Amministratori Organization

| Concetto | Implementazione |
|---|---|
| Ruolo utente | `users.role` ∈ {agency_admin, branch_admin, group_admin, agent, …} |
| Membership operativa | `memberships` con `operational_role` ∈ {agency_admin, agent, branch_admin, branch_agent, group_admin} — **solo verso Organization** |
| Owner agenzia | `agencies.owner_id` = user che ha creato l’agenzia |
| Contesto tenant | `active_agency_id` / membership attiva |

`agency_admin` = Admin **dell’Organization**, non Main Admin commerciale (B01-AC09, B02 §5.3).

### 2.3 Relazione CommercialCustomer ↔ Main Admin

`CommercialCustomerInDB` (`backend/shared/models/commercial_customer.py`): P.IVA, stati, Stripe — **nessun riferimento a utente Main Admin**.

### 2.4 Campi/relazioni già esistenti — perché non bastano

| Candidato | Perché non usarlo come Main Admin senza nuova decisione |
|---|---|
| `users.role == agency_admin` | È Admin di Organization; presente anche sulle filiali. È esattamente il bug. |
| `agencies.owner_id` | B01 §6.3: **«owner_id non deve essere convertito automaticamente in Main Admin»**. Owner ≠ Main Admin (B01-DEC-02). |
| Prima agency del CC / agency “HQ” | Non esiste flag `is_commercial_primary` / `is_hq` autorevole sul modello. |
| `group_admin` | B01-AC09: Main Admin distinto anche da `group_admin`. Group ≠ CommercialCustomer. |
| Membership attiva | Solo ruoli operativi org; nessun ruolo commerciale. |
| Representation | Prevista in design B01/B02, **non implementata** nel backend. |

### 2.5 Endpoint wallet e controlli attuali

| Endpoint | Guard oggi | Scope dati |
|---|---|---|
| `GET /billing/wallet` | exact: super_admin, agency_admin, group_admin | wallet **centrale** del CC risolto da agency attiva |
| `POST /billing/wallet/allocate` | idem | mutazione centrale |
| `POST /billing/wallet/revoke` | idem + H1 bind CC | mutazione centrale |
| `GET /billing/wallet/organization` | require_roles (include branch_admin) | solo `require_agency(user)` |

Il controllo è backend; manca il criterio **“è Main Admin di questo CC?”**.

### 2.6 Sicurezza lato server

Sì, il controllo **deve** essere backend. H1 (bind CC su revoke) va preservato. Ma senza un’identità Main Admin persistita, qualsiasi euristica (owner, prima org, solo agency_admin) o è vietata dal design o è ambigua.

---

## 3. Conclusione tecnica

**Non è possibile completare il residuo H2 in modo corretto usando solo relazioni già implementate**, senza violare B01-DEC-02 / B01 §6.3 / B01-AC09 / DES-08.

Completare H2 richiede una **decisione Founder** su come ancorare Main Admin al CommercialCustomer nel modello dati (o su quale euristica temporanea — se ammessa — usare in attesa del modello pieno).

Per mandato §4: **mi fermo. Non introduco autonomamente ruolo/campo/relazione nuova.**

---

## 4. Opzioni proposte (per decisione Founder / ChatGPT)

### Opzione A — Campo autorevole sul CommercialCustomer (consigliata per chiudere H2 in modo pulito)

- Aggiungere es. `commercial_customers.main_admin_user_id` (o lista `main_admin_user_ids`).
- Bootstrap: regola Founder esplicita (es. al create agency iniziale del CC, o assegnazione Ops/Super Admin).
- Guard wallet: `user.id == cc.main_admin_user_id` **oppure** `super_admin` (ops).
- `agency_admin` di filiale → negato sul wallet centrale; resta `GET /wallet/organization`.

**Impatto:** piccolo schema + seed/migrazione dati (assegnazione Main Admin per CC esistenti).  
**Compatibilità:** non confonde owner e Main Admin. Allinea DES-08.  
**Rischio:** CC senza Main Admin assegnato → wallet admin bloccato finché assegnato (corretto deny-by-default).

### Opzione B — Capability / Membership commerciale verso CC

- Nuova relazione “CommercialMembership” o capability `commercial_main_admin` legata al CC (design B02 pieno).
- Più corretta a lungo termine, più invasiva (B02 non ancora interamente implementato).

**Impatto:** alto. Fuori da “completamento H2 minimo”.

### Opzione C — Euristica temporanea vietata dal design attuale

Es. “owner della prima organization del CC” o “solo agency_admin se org.owner_id == user”.  
**Non raccomandata** senza deroga Founder esplicita a B01 §6.3.

### Opzione D — Fermare H2 residuo e aprire slice identità dedicata

Rinviare wallet Main Admin fino a slice B01/B02 “Main Admin binding”.

---

## 5. Cosa NON è stato fatto

- Nessun cambio a `revoke` / allocate / routes wallet (resto su #212).
- Nessun H3/H4/legacy/B04-III.
- Nessuna migrazione operativa.
- Nessun merge.

---

## 6. Domanda secca al Founder

Quale opzione autorizzi per chiudere il residuo H2?

- **A** — campo `main_admin_user_id` su CommercialCustomer (+ regola di assegnazione)  
- **B** — modello capability/membership commerciale (scope più ampio)  
- **C** — euristica temporanea (specificare quale, in deroga a B01 §6.3)  
- **D** — rinvio a slice identità dedicata  

Dopo la scelta, Cursor implementa solo quello, con test del mandato H2 residuo, PR dedicata, **senza merge** finché non lo chiedi.
