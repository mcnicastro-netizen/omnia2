# OMNIA — AUDIT B16 Billing, Stripe, abbonamenti, crediti e limiti pacchetti

**Fonte:** `bc-7947c9a1` · **Quando:** 2026-11-14 ~01:19 Europe/Rome  
**URL:** https://cursor.com/agents/bc-7947c9a1-3caa-4587-9443-85f55836c277

---

## Prompt commissionato

Perfetto. Procediamo con un audit specifico di **Billing e pacchetti commerciali OMNIA**.
Questo è il prompt da incollare in Cursor. È rigorosamente in sola lettura: Cursor deve analizzare il codice esistente, non correggerlo.
# OMNIA — AUDIT B16
## Billing, Stripe, abbonamenti, crediti e limiti dei pacchetti
**MODALITÀ OBBLIGATORIA: AUDIT ESCLUSIVAMENTE IN SOLA LETTURA.**
Non sei autorizzato a implementare, correggere o modificare nulla.
### 1. Divieti assoluti
Non modificare:
- codice backend o frontend;
- database, documenti o record;
- configurazioni, variabili d'ambiente o indici;
- test o fixture;
- documentazione, decisioni o file di progetto;
- migrazioni o schema.
Non eseguire operazioni che creino, aggiornino o cancellino clienti Stripe, abbonamenti, pagamenti, crediti o altri dati.
Non proporre modifiche come se fossero già state approvate.
Puoi leggere file, seguire chiamate, analizzare modelli, verificare test esistenti e ricostruire il funzionamento effettivo.
### 2. Contesto e decisioni già approvate
OMNIA deve distinguere:
1. **Cliente commerciale:** soggetto identificato dalla partita IVA, che acquista il servizio e possiede l'abbonamento.
2. **Organizzazione operativa:** agenzia o struttura che utilizza OMNIA.
3. **Filiale:** unità operativa appartenente alla medesima entità commerciale.
Decisioni confermate:
- Una partita IVA corrisponde a un solo cliente commerciale OMNIA.
- Organizzazioni e filiali con la stessa partita IVA condividono un solo cliente commerciale e un solo abbonamento.
- Condividono crediti, account e limiti commerciali previsti dal pacchetto.
- L'Admin principale distribuisce gli account disponibili tra le filiali.
- Le filiali mantengono la propria autonomia operativa e organizzativa nei limiti delle autorizzazioni.
- Le filiali non moltiplicano i limiti commerciali.
- Organizzazioni con partita IVA differenti sono clienti commerciali distinti, con abbonamenti e plafond separati.
- La stessa persona può appartenere a più organizzazioni, con ruoli e autorizzazioni distinti.
- Non deve essere introdotto un quarto pacchetto o un nuovo listino.
- Le configurazioni commerciali già approvate devono essere preservate.
### 3. Pacchetti da verificare
Confronta tutte le informazioni nel codice con il listino approvato.
| Pacchetto | Founder mensile | Standard mensile |
| --------- | --------------- | ---------------- |
| Starter   | €49             | €79              |
| Pro       | €99             | €179             |
| Agency    | €299            | €399             |
Verifica anche:
- prezzi annuali e regola 11 mensilità;
- durata e applicazione dello sconto Founder;
- numero massimo di utenti;
- numero massimo di immobili;
- crediti mensili;
- spazio di archiviazione;
- funzionalità incluse;
- add-on, temi e restyling;
- ricariche di crediti;
- upgrade e downgrade;
- eventuali personalizzazioni commerciali già previste.
Non modificare prezzi o condizioni.
### 4. Stripe e cliente commerciale
Ricostruisci il flusso completo:
- creazione del cliente Stripe;
- associazione tra cliente Stripe e OMNIA;
- creazione dell'abbonamento;
- associazione tra subscription e piano;
- checkout;
- pagamento iniziale;
- rinnovi;
- webhook;
- pagamenti falliti;
- sospensione e riattivazione;
- cancellazione e scadenza;
- upgrade e downgrade;
- fatture e storico pagamenti.
Per ogni passaggio indica file, funzioni, modelli e identificativi utilizzati.
Verifica soprattutto se Stripe lavora su `agency_id`, su un cliente commerciale autonomo oppure su un'altra entità.
Non presumere che il modello attuale supporti già il cliente commerciale condiviso.
### 5. Crediti e portafogli
Ricostruisci:
- creazione del wallet;
- associazione del wallet all'entità;
- assegnazione dei crediti mensili;
- rinnovo e azzeramento;
- consumo;
- ricariche;
- eventuali scadenze;
- registrazione dei movimenti;
- gestione dei crediti in caso di upgrade/downgrade;
- comportamento in caso di sospensione o cessazione.
Verifica se i crediti sono associati a `agency_id` oppure a un cliente commerciale condiviso.
Verifica se il sistema consente realmente un unico plafond condiviso tra più organizzazioni.
Individua possibili duplicazioni, perdite di crediti o assegnazioni multiple.
### 6. Account e immobili: limiti dei pacchetti
Verifica come vengono conteggiati:
**Account**
- utenti attivi;
- utenti invitati;
- utenti sospesi;
- trasferimenti tra filiali;
- account appartenenti a più organizzazioni;
- assegnazione e restituzione degli slot.
**Immobili**
- immobili creati;
- immobili archiviati o cancellati;
- immobili presenti in più organizzazioni;
- immobili trasferiti tra filiali;
- eventuali duplicati;
- immobili pubblicati su portali esterni.
Non inventare nuove regole di conteggio. Descrivi quelle attualmente implementate e segnala quelle mancanti o ambigue.
### 7. Operazioni organizzative e conseguenze commerciali
Analizza cosa succede al billing quando:
- viene creata una nuova filiale con la stessa partita IVA;
- viene aggiunta un'organizzazione allo stesso cliente commerciale;
- una filiale viene sospesa;
- una filiale viene chiusa;
- una filiale viene trasferita;
- un'organizzazione esce da un gruppo;
- cambia la partita IVA;
- un cliente commerciale viene sospeso;
- un cliente commerciale termina l'abbonamento.
Indica quali operazioni sono supportate, quali non lo sono e quali potrebbero generare effetti collaterali.
### 8. Coerenza con il modello multi-organizzazione
Verifica in particolare:
- dove viene utilizzato `agency_id`;
- quali modelli e collezioni dipendono da esso;
- se subscription e wallet sono legati direttamente all'agenzia;
- se esiste già un'entità cliente commerciale;
- se esistono riferimenti tra agenzie e filiali;
- se il modello attuale può supportare un cliente commerciale con più organizzazioni;
- quali dipendenze tecniche dovrebbero essere considerate prima di una futura implementazione.
Non progettare ancora una migrazione definitiva e non introdurre nuove entità nel codice.
### 9. Test e casi critici
Esamina i test esistenti e verifica almeno questi scenari:
1. Una società Starter con sede principale e cinque filiali.
2. Una società Pro con più organizzazioni operative.
3. Due società con partite IVA differenti, anche se hanno lo stesso titolare.
4. Trasferimento di un collaboratore da una filiale a un'altra.
5. Creazione di una nuova filiale senza creare un secondo abbonamento.
6. Rinnovo del cliente commerciale con più filiali.
7. Pagamento fallito e conseguenze sulle organizzazioni.
8. Upgrade e downgrade con plafond condiviso.
9. Sospensione di una sola filiale.
10. Chiusura del cliente commerciale.
11. Ricarica crediti e consumo da parte di organizzazioni differenti.
12. Richieste simultanee che potrebbero superare i limiti del pacchetto.
Per ciascuno indica se il caso è coperto da test e se il comportamento effettivo è corretto.
Non eseguire test che richiedano modifiche al database o chiamate reali a Stripe. Se un test comporta effetti collaterali, limitati all'ispezione statica.
### 10. Formato obbligatorio del rapporto
Restituisci un rapporto strutturato con:
**A. Architettura attuale**
- modelli;
- collezioni;
- servizi;
- endpoint;
- webhook;
- flussi Stripe.
**B. Pacchetti commerciali**
- confronto tra listino approvato e codice;
- eventuali discrepanze.
**C. Billing**
- collegamenti effettivi tra cliente, agenzia, subscription e Stripe.
**D. Crediti**
- funzionamento effettivo e possibili criticità.
**E. Limiti**
- conteggio effettivo di account, immobili e storage.
**F. Multi-organizzazione**
- compatibilità con cliente commerciale e filiali.
**G. Rischi**
- classificazione P0, P1, P2, P3;
- conseguenze concrete;
- riferimenti precisi a file e funzioni.
**H. Test**
- coperture esistenti;
- test mancanti;
- scenari non verificabili.
**I. Decisioni già rispettate**
- indica quali decisioni approvate sono già compatibili con il codice.
**J. Decisioni non implementate o incompatibili**
- separa chiaramente problemi tecnici e questioni che richiedono una decisione del Founder.
**K. Ordine raccomandato**
- dipendenze;
- priorità;
- attività preliminari;
- nessuna implementazione automatica.
### 11. Chiusura obbligatoria
Concludi dichiarando esplicitamente:
- se hai modificato file: deve essere NO;
- se hai modificato database: deve essere NO;
- se hai modificato configurazioni o indici: deve essere NO;
- se hai eseguito operazioni reali su Stripe: deve essere NO.
Se non puoi garantire una di queste condizioni, interrompi l'attività e segnalalo.
**Obiettivo: fornire al Founder una fotografia tecnica verificabile del rapporto tra pacchetti commerciali, cliente OMNIA, organizzazioni, filiali, Stripe, crediti e limiti, prima di autorizzare qualsiasi implementazione.**
### **Cosa faremo con il risultato**
Quando Cursor avrà restituito B16, lo confronteremo con:
1. le decisioni commerciali già approvate;
2. il precedente audit B15;
3. il listino ufficiale;
4. l'architettura multi-organizzazione che abbiamo definito.
Non autorizzeremo modifiche finché non avremo capito le incompatibilità e le dipendenze. **L'obiettivo è correggere OMNIA senza cambiare ciò che abbiamo deciso di vendere.**

---

## Report

Marco, audit B16 completato in sola lettura. Fotografia tecnica del billing attuale rispetto al modello “cliente commerciale / organizzazioni / filiali”.

---

# OMNIA — AUDIT B16  
## Billing, Stripe, abbonamenti, crediti e limiti

---

## A. Architettura attuale

### Modelli e collezioni (tutti centrati su `agency_id`)

| Entità | Dove | Chiave |
|---|---|---|
| Piano catalogo | `apps/billing/plans.py` (`LAUNCH_PLANS`, `POST_TRACTION_PLANS`) | tier string |
| Subscription OMNIA | Mongo `subscriptions` (`SubscriptionInDB`) | **`agency_id`** + opz. `stripe_customer_id` / `stripe_subscription_id` |
| Wallet | Mongo `credit_wallets` | **`agency_id`**, `balance` |
| Ledger consumi/topup Stripe | Mongo `credit_ledger` | **`agency_id`** |
| Topup assistiti Ops | Mongo `credit_transactions` | **`agency_id`** (secondo canale, non unificato) |
| Checkout tx | Mongo `payment_transactions` | `session_id`, **`agency_id`** |
| Fatture sync | Mongo `invoices` | `stripe_invoice_id`, **`agency_id`** |
| Storage extra | `agencies.storage_extra_gb` | per agency |
| Group / filiali | `agency_groups` + `agencies.group_id` | `credits_mode` **solo metadato** |
| Cliente commerciale | — | **non esiste** come entità |

### Servizi principali

- `apps/billing/routes.py` — catalogo, checkout, credits, storage, portal, webhook, `debit_credits`
- `apps/billing/setup_stripe.py` — crea Product/Price Stripe da **solo** `LAUNCH_PLANS`
- `apps/immoweb/assisted_billing.py` — `grant_assisted_plan` (Ops, no Stripe)
- `shared/billing/plan_credits.py` — crediti piano da `invoice.paid` (D-167)
- `shared/billing/counters.py` — reminder rinnovo / low credits
- `shared/billing/self_serve.py` — rubinetto `OMNIA_SELF_SERVE_ENABLED` (D-115)
- `shared/storage/quota.py` — quota GB per agency
- B2C parallelo: `b2c_checkout.py` / `b2c_products.py` (fuori listino B2B)

### Endpoint B2B rilevanti

| Metodo | Path | Ruolo |
|---|---|---|
| GET | `/billing/plans` | pubblico |
| GET | `/billing/subscription` | sub + wallet **active agency** |
| POST | `/billing/checkout` | sub Stripe (agency attiva) |
| POST | `/billing/credits/purchase` | topup one-off |
| POST | `/billing/storage/purchase` | addon +100 GB |
| GET | `/billing/status/{session_id}` | poll + fallback apply |
| POST | `/billing/portal` | Stripe Customer Portal |
| POST | `/billing/webhook` | eventi Stripe |

**Assente:** API cliente per storico fatture B2B (le `invoices` esistono in Mongo; UI fatture lato Ops/cabina).

### Flusso Stripe ricostruito

1. **Customer** — non creato esplicitamente in OMNIA. Checkout usa `customer_email=user["email"]` → Stripe crea/associa customer; l’id viene salvato solo **dopo** pagamento in `_apply_session_side_effects` su `subscriptions.stripe_customer_id`.
2. **Associazione OMNIA** — metadata Checkout/Subscription: `agency_id`, `user_id`, `tier`, `billing_cycle`, `kind`. **Nessun** `commercial_customer_id` / VAT.
3. **Price** — `lookup_key = "{tier}_{monthly|yearly}"` da catalogo attivo.
4. **Checkout** — `mode=subscription`; onboarding pending → URL waiting; altrimenti richiede self-serve ON.
5. **Persistenza pre-pay** — `payment_transactions` status `initiated`.
6. **Pagamento / side-effect** — webhook `checkout.session.completed` o poll `/status` → `_apply_session_side_effects` upserta `subscriptions` per `agency_id`; può triggerare auto-Attiva KYC.
7. **Crediti piano** — `invoice.paid` → `grant_plan_credits_from_stripe_invoice` (idempotente su `credit_ledger.ref_id`).
8. **Rinnovo** — Stripe cicla; OMNIA aggiorna periodi su `customer.subscription.updated`; crediti su `invoice.paid`.
9. **Payment failed** — status `past_due` + alert Ops; **non** sospende automaticamente `activation_status` / CRM.
10. **Cancel** — `cancel_at_period_end` aggiornato; **nessun** handler `customer.subscription.deleted`.
11. **Upgrade/downgrade** — delegati al **Customer Portal** Stripe; nessun codice OMNIA di proration o ricalcolo plafond.
12. **Portal** — richiede `subscriptions.stripe_customer_id` già presente.

---

## B. Pacchetti commerciali

### Confronto listino approvato ↔ codice

| Voce | Approvato | Codice (`plans.py`) | Esito |
|---|---|---|---|
| Starter Founder / Standard | €49 / €79 | 49 / 79 | OK |
| Pro | €99 / €179 | 99 / 179 | OK |
| Agency | €299 / €399 | 299 / 399 | OK |
| Annuale = 11× | D-079 | 539, 1089, 3289 / 869, 1969, 4389 | OK |
| max utenti | 3 / 10 / ∞ | `max_agents` 3 / 10 / -1 | OK in catalogo |
| max immobili | 30 / 200 / ∞ | `max_properties` 30 / 200 / -1 | OK in catalogo |
| crediti/mese | 120 / 1200 / 3600 | uguale | OK |
| storage incluso | 30 / 100 / 300 GB | `STORAGE_INCLUDED_GB` + `quota.py` | OK |
| addon storage | +100 GB €15/mese | `STORAGE_ADDONS` | OK |
| ricariche crediti | pacchetti 400…20000 @ €0,05/cr | `CREDIT_PACKAGES` | OK |
| costi consumo | listino PRICING_OMNIA | `CREDIT_COSTS` allineato (micro-tour 30) | OK |
| temi sito D-151 | €99/€199/€199 | `SITE_THEME_PRICES_EUR` | prezzi OK; **checkout Stripe ⏳** (D-151) |
| 4° pacchetto | vietato | solo starter/pro/agency | OK |
| Trial self-serve | no (D-080) | `trial_days=0` | OK |

### Discrepanze rilevanti (non sui prezzi unitari)

1. **Sconto Founders 12 mesi per agenzia** — documentato in `PRICING_OMNIA.md` e commenti; in codice lo switch è **globale** via `PRICING_PHASE` (`launch` vs `post_traction`). Campo `launch_discount_months=0` inutilizzato. **Nessun lock-in per data ingresso agenzia.**
2. **`setup_stripe.py` sincronizza solo `LAUNCH_PLANS`** — prezzi Standard non creati automaticamente da quello script.
3. **`Plan.features`** è lista vuota — feature narrative (multiposting, wizard…) non machine-checked nel piano.
4. FE `RegisterPage.jsx` ha prezzi Founders **hardcoded** (coerenti oggi; rischio drift).

---

## C. Billing — collegamenti effettivi

```
Persona (users) ──owner/member──► Agency (agencies)
                                      │
                                      ├── subscriptions[agency_id] ── stripe_customer_id / stripe_subscription_id
                                      ├── credit_wallets[agency_id]
                                      ├── payment_transactions[agency_id]
                                      └── invoices[agency_id]

AgencyGroup (opzionale) ──group_id──► N agencies
   credits_mode = "group"|"branch"   ※ NON letto da debit/checkout
```

| Domanda | Risposta dal codice |
|---|---|
| Stripe lavora su cosa? | **`agency_id`** (metadata + riga `subscriptions`) |
| Esiste cliente commerciale autonomo? | **No** |
| Una P.IVA / N filiali = 1 subscription? | **No** — ogni agency può avere la propria |
| Checkout riusa customer Stripe esistente? | **No** in create session (solo `customer_email`); portal sì dopo primo salvataggio |
| Abbonamento assistito Ops | `grant_assisted_plan` scrive stessa collection per `agency_id`, `source=assisted_provisioning` |

---

## D. Crediti

### Funzionamento effettivo

- Wallet creato lazy (upsert) al primo grant/topup/debit.
- Accredito mensile/annuale: `invoice.paid` → listino ×1 o ×12 (yearly).
- Ops/KYC: `grant_assisted_plan` con `$inc`; se Stripe già live → `skip_wallet` (D-167).
- Consumo: `debit_credits(agency_id, …)` atomico su balance ≥ amount → 402 se insufficiente.
- Ricariche: checkout `credits_topup` → `$inc` + `credit_ledger`.
- **Nessuna scadenza / azzeramento periodico** dei residui: modello cumulativo (allineato a PRICING “si sommano”).
- Upgrade/downgrade: nessun ricalcolo crediti in OMNIA.
- Sospensione/cessazione: wallet **non** azzerato automaticamente; past_due non blocca debit di per sé.

### Criticità

1. **Plafond condiviso multi-org: assente** — N agency = N wallet.
2. **`credits_mode=group` non implementato** — solo campo su `AgencyGroup`.
3. **Doppio canale ledger** (`credit_ledger` vs `credit_transactions`) — report/audit frammentati.
4. **Rischio doppio accredito assistito + Stripe** mitigato da D-167/clawback 2000, ma path non-Stripe ripetuti possono ancora `$inc`.
5. API Gateway (`shared/auth/api_key.py`) ha **wallet crediti sulla API key**, parallelo al wallet agency — traccia Track B separata.

---

## E. Limiti

### Account

| Regola | Implementata? | Dove |
|---|---|---|
| max_agents su invite | **Sì** | `invites.create_invite`: `members + pending >= max` |
| Conteggio utenti attivi vs sospesi | **Parziale** | `count_documents({agency_ids})` — **non** filtra `is_active` |
| Slot trasferibili tra filiali | **No** | nessun pool commerciale |
| User multi-org conta 1 slot per membership | **Sì di fatto** | contato per `agency_id` dell’invito |
| Assegnazione Admin principale del plafond gruppo | **No** | — |
| Enforce a accept (oltre create invite) | **No** | race: accept non ri-verifica tetto |

### Immobili

| Regola | Implementata? |
|---|---|
| `max_properties` in create | **NO** — `properties.create_property` inserisce senza check |
| Archiviati / cestino nel conteggio | N/A (limite non enforced) |
| Cross-org / trasferimento filiali | Non c’è transfer commerciale; property ha un solo `agency_id` |
| Portali esterni | Multiposting non scala il limite (limite stesso assente) |

### Storage

| Regola | Implementata? |
|---|---|
| Quota GB per agency + extra | **Sì** — `assert_can_upload` |
| Quota condivisa tra filiali | **No** |

UI mostra max agenti/immobili (`BillingPage`, Avvio) ma **immobili non sono hard-gate**.

---

## F. Multi-organizzazione

Compatibilità con il modello approvato (cliente P.IVA + filiali + un abbonamento):

| Capacità richiesta | Stato codice |
|---|---|
| Cliente commerciale = P.IVA | Assente (B15) |
| 1 sub / 1 wallet per P.IVA | Assente — per agency |
| Filiali non moltiplicano limiti | Assente — ogni branch indipendente |
| Admin distribuisce account tra filiali | Assente |
| Autonomia operativa filiale | **Presente** (tenant `agency_id`, group attach/detach) |
| P.IVA diverse = billing separato | **Di fatto sì** (agency separate), ma senza vincolo VAT |
| Stessa persona multi-org | Membership sì; billing/ruoli per-org no (B15) |

**Dipendenze tecniche future (solo elenco, non design):**  
unicità VAT (B15) → entità o chiave commerciale → spostare `subscriptions`/`credit_wallets` (o alias) dalla singola agency → enforce limiti aggregati → wiring `credits_mode` → checkout che riusa un solo Stripe Customer commerciale.

---

## G. Rischi

### P0
1. **Modello billing incompatibile col cliente commerciale condiviso** — oggi N filiali possono generare N checkout/N Stripe customer/N wallet → moltiplicazione listino. File: `routes.create_checkout`, `assisted_billing.grant_assisted_plan`, `plan_credits`.
2. **`max_properties` non enforced** — listino venduto (30/200) non applicato in `properties.create_property`.

### P1
3. **Founders 12 mesi non per-agenzia** — `PRICING_PHASE` globale; lock-in tariffario non realizzabile come documentato.
4. **`setup_stripe` solo Launch** — rischio mismatch Standard vs Stripe.
5. **Checkout senza `customer=` esistente** — possibili customer Stripe duplicati per stessa agency/email.
6. **`past_due` / cancel senza gate CRM** — pagamento fallito non sospende uso; solo alert.
7. **Nessun `subscription.deleted`** — stato OMNIA può restare “active” stale.
8. **Invite seats: pending+members, no re-check su accept; `is_active` ignorato**.
9. **Tema sito D-151 senza checkout** — prezzi in catalogo, vendita non cablata.

### P2
10. `credits_mode` group non collegato.
11. Doppio ledger crediti.
12. Nessuna API storico fatture lato cliente.
13. Upgrade/downgrade solo Portal (comportamento Stripe Dashboard opaco al codice).

### P3
14. Feature flags piano non strutturati in `Plan.features`.
15. Prezzi hardcoded in `RegisterPage.jsx`.

---

## H. Test

| Scenario richiesto | Copertura test | Comportamento codice |
|---|---|---|
| 1. Starter HQ + 5 filiali | **Assente** | Ogni agency billing indipendente |
| 2. Pro multi-org | **Assente** | Idem |
| 3. Due P.IVA stesso titolare | **Assente** (B15: create bloccata da `owner_id`) | Billing per agency se esistessero |
| 4. Transfer collaboratore filiale | **Assente** | Solo pull/add membership; no slot pool |
| 5. Nuova filiale senza 2ª sub | **Assente** | Attach branch non crea sub, ma **non impedisce** 2º checkout |
| 6. Rinnovo cliente multi-filiale | **Assente** | Rinnovo per `stripe_subscription_id` singolo |
| 7. Pagamento fallito → org | Unit counters/alert; **no** test sospensione CRM | Solo `past_due` |
| 8. Upgrade/downgrade plafond condiviso | **Assente** | N/A |
| 9. Sospensione una filiale | **Assente** | `activation_status` filtro cabina; no auto da Stripe |
| 10. Chiusura cliente commerciale | **Assente** | Solo wipe/purge Ops per agency |
| 11. Ricarica + consumo cross-org | **Assente** | Debit solo su `agency_id` attivo |
| 12. Race oltre limiti piano | **Assente** per seats/properties | Invite check non atomico con accept |

**Test utili esistenti (statici/unit):**  
`test_d167_plan_credits`, `test_d169_avvio_seats_credits`, `test_d166_billing_counters`, `test_ops_grant_agency_plan`, `test_storage_quota_d085`, `test_s9_o6_self_serve`, `test_m2s5_1_groups` (solo CRUD `credits_mode`).

Nessun test eseguito che tocchi DB reale o Stripe live in questo audit (solo lettura sorgenti).

---

## I. Decisioni già rispettate (compatibili col codice)

- Tre pacchetti soli; no Enterprise pubblico (D-080).
- Prezzi Founders/Standard e annuale 11× nel catalogo Python (D-079/D-080).
- Crediti unitari €0,05 e pacchetti ricarica.
- Storage 30/100/300 + addon (D-085).
- No trial self-serve; rubinetto O6 (D-115).
- Crediti piano da invoice Stripe listino (D-167).
- Isolamento dati operativo per `agency_id` / filiali group.
- Checkout onboarding pending anche con self-serve OFF (D-157).

---

## J. Decisioni non implementate o incompatibili

### Problemi tecnici (il codice non fa ciò che il listino/modello richiedono)
- Un cliente commerciale / un abbonamento / un plafond per P.IVA.
- Limiti account/immobili aggregati e non moltiplicabili per filiale.
- Distribuzione slot da Admin principale.
- Enforce `max_properties`.
- Lock-in Founders 12 mesi **per ingresso agenzia**.
- Wiring `credits_mode=group`.
- Checkout temi D-151.
- Lifecycle Stripe completo (deleted, sospensione CRM su unpaid).

### Questioni per decisione Founder (prima di implementare)
1. **Entità “cliente commerciale”**: nuova collection vs agency “root” vs group con VAT?
2. **Filiali esistenti con sub/wallet separati**: merge, grandfather, o solo greenfield?
3. **`credits_mode` attuale default `branch`**: allineare al “sempre condiviso stessa P.IVA” o tenere eccezioni franchising multi-P.IVA?
4. **Founders**: meccanismo Stripe (subscription schedule / coupon / price switch) vs solo env globale?
5. **Past_due**: soft warning vs blocco CRM vs solo cabina?
6. **Max immobili**: hard block create vs soft warning (listino dice limiti)?

---

## K. Ordine raccomandato (nessuna implementazione)

**Dipendenze**
```
B15 unicità P.IVA + multi-org persona
    → definizione mapping Cliente commerciale ↔ agencies/filiali  [decisione Founder]
        → single subscription/wallet binding
            → enforce limiti aggregati (agents già parziale; properties da aggiungere)
                → credits_mode effettivo
                    → checkout riusa Stripe Customer commerciale
                        → Founders per-agenzia + sync Stripe Standard
                            → lifecycle past_due/cancel + temi D-151
```

**Priorità**
1. Decisione modello dati commerciale (J) — senza questo ogni patch è prematura.
2. Hard-gate `max_properties` + seats atomici (protezione listino venduto **oggi**, anche a singola agency).
3. Evitare N checkout per stessa P.IVA (gate applicativo) appena esiste unique VAT.
4. Completare lifecycle Stripe e Founders per-agenzia.
5. Plafond condiviso filiali / distribuzione slot.

**Preliminari**
- Inventario agenzie demo con sub/wallet multipli.
- Verifica catalogo Stripe live vs `LAUNCH`/`POST_TRACTION`.
- Non introdurre 4° piano né cambiare prezzi.

---

## Dichiarazione di chiusura (obbligatoria)

| Condizione | Esito |
|---|---|
| File modificati | **NO** |
| Database modificato | **NO** |
| Configurazioni / indici modificati | **NO** |
| Operazioni reali su Stripe | **NO** |

---

**Fermato qui.** B16 è pronto per il confronto con B15, listino ufficiale e modello multi-organizzazione. Nessuna implementazione finché non arriva la frase di autorizzazione esplicita.
