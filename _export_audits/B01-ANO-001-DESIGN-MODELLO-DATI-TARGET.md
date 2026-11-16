# OMNIA — B01 / ANO-001
## Progettazione del modello dati target

**Versione:** 1.0 — Design  
**Data:** 16 novembre 2026  
**Baseline tecnica:** `main` @ `2fea64a`  
**Perimetro:** identità, cliente commerciale, organizzazioni e appartenenze.  
**Stato:** progettazione autorizzata; nessuna implementazione.

Riferimenti: `CHIUSURA-VERIFICA-STATICA-BLOCCHI-0-7.md`, `FASE-2-BACKLOG-PIANIFICAZIONE-RISANAMENTO.md`.

---

# 1. Obiettivo di B01

B01 deve definire un modello dati capace di rappresentare correttamente cinque concetti distinti:

1. Persona.
2. Account utente.
3. Organizzazione.
4. Cliente commerciale OMNIA identificato dalla P.IVA.
5. Appartenenza operativa e rappresentanza.

L'architettura attuale utilizza prevalentemente `agency_id` come identificatore tenant e commerciale di fatto. Questo non è sufficiente per il modello Founder.

Il nuovo modello deve permettere di separare:

- identità della persona;
- credenziali e account;
- organizzazione nella quale si opera;
- soggetto commerciale che paga OMNIA;
- relazioni organizzative e autorizzazioni.

B01 definisce la struttura concettuale e le regole di integrità. Non definisce ancora l'implementazione delle autorizzazioni, delle sessioni, degli inviti o del billing.

---

# 2. Vincoli Founder da rispettare

Le seguenti condizioni sono requisiti già approvati, non nuove proposte.

| ID      | Requisito                                                                                         |
| ------- | ------------------------------------------------------------------------------------------------- |
| B01-R01 | Una P.IVA identifica un cliente commerciale OMNIA                                                 |
| B01-R02 | Più organizzazioni con la stessa P.IVA appartengono allo stesso cliente commerciale               |
| B01-R03 | P.IVA differenti identificano clienti commerciali distinti                                        |
| B01-R04 | Una persona può rappresentare organizzazioni appartenenti a clienti commerciali diversi           |
| B01-R05 | Un collaboratore operativo appartiene a una sola organizzazione alla volta                        |
| B01-R06 | Ogni organizzazione ha un proprio Admin                                                           |
| B01-R07 | La gerarchia organizzativa deve supportare livelli annidati senza limite funzionale prefissato    |
| B01-R08 | Le organizzazioni conservano autonomia operativa e identità MLS                                   |
| B01-R09 | L'appartenenza non equivale alla rappresentanza                                                   |
| B01-R10 | L'accesso tra organizzazioni richiede autorizzazioni esplicite, selettive, revocabili e tracciate |
| B01-R11 | Limiti utenti e immobili sono aggregati per cliente commerciale P.IVA                             |
| B01-R12 | Gruppo/franchising non equivale a cliente commerciale                                             |

---

# 3. Modello dati target

## 3.1 Entità principali

### A. Person

Rappresenta la persona fisica.

Responsabilità:

- identità anagrafica;
- identificativo stabile;
- collegamento agli account;
- collegamento alle relazioni di rappresentanza.

Non deve essere utilizzata come tenant commerciale.

Campi concettuali:

| Campo         | Significato            |
| ------------- | ---------------------- |
| person_id     | Identificativo stabile |
| identity_data | Dati identificativi    |
| created_at    | Creazione              |
| updated_at    | Ultimo aggiornamento   |
| status        | Stato della persona    |

Nota: la separazione tra Person e User è una proposta architetturale da mantenere distinta dall'attuale struttura tecnica. Non si assume che ogni account debba necessariamente generare subito una nuova entità Person senza una regola di riconciliazione.

### B. User

Rappresenta l'account OMNIA e il soggetto autenticabile.

Responsabilità:

- email e credenziali;
- autenticazione;
- stato account;
- collegamento alla persona;
- preferenze e configurazioni dell'account.

Campi concettuali:

| Campo          | Significato               |
| -------------- | ------------------------- |
| user_id        | Identificativo account    |
| person_id      | Collegamento alla persona |
| email          | Email account             |
| auth_data      | Dati di autenticazione    |
| account_status | Stato account             |
| created_at     | Creazione                 |
| updated_at     | Aggiornamento             |

`User` non deve diventare il contenitore delle appartenenze commerciali.

Il ruolo globale attuale non deve essere assunto come fonte definitiva dei poteri operativi per organizzazione.

### C. CommercialCustomer

È l'entità centrale del modello commerciale OMNIA.

Identifica il soggetto contrattuale e commerciale tramite P.IVA.

Campi concettuali:

| Campo                  | Significato                    |
| ---------------------- | ------------------------------ |
| commercial_customer_id | Identificativo interno stabile |
| country_code           | Paese di registrazione         |
| vat_number_normalized  | P.IVA normalizzata             |
| legal_name             | Ragione sociale                |
| fiscal_data            | Dati fiscali                   |
| customer_status        | Stato commerciale              |
| created_at             | Creazione                      |
| updated_at             | Ultimo aggiornamento           |

Vincolo fondamentale:

`UNIQUE(country_code, vat_number_normalized)`

Il vincolo riguarda `CommercialCustomer`, non le organizzazioni.

La stessa P.IVA può quindi comparire nei dati fiscali di più organizzazioni, ma tutte devono puntare allo stesso cliente commerciale.

La normalizzazione e la validazione della P.IVA devono essere definite in modo coerente e non basarsi soltanto sulla validazione frontend.

La gestione dei casi esteri e delle eccezioni fiscali richiede una specifica di dominio separata prima dell'implementazione.

### D. Organization

Rappresenta una singola organizzazione operativa all'interno di OMNIA.

Responsabilità:

- dati identificativi e operativi;
- appartenenza commerciale;
- gerarchia organizzativa;
- configurazione autonoma;
- identità MLS;
- amministrazione locale.

Campi concettuali:

| Campo                  | Significato                               |
| ---------------------- | ----------------------------------------- |
| organization_id        | Identificativo stabile                    |
| commercial_customer_id | Cliente commerciale di appartenenza       |
| parent_organization_id | Organizzazione superiore, nullable        |
| legal_data             | Dati legali e fiscali dell'organizzazione |
| operational_data       | Dati operativi                            |
| mls_identity           | Identità MLS autonoma                     |
| organization_status    | Stato organizzazione                      |
| created_at             | Creazione                                 |
| updated_at             | Ultimo aggiornamento                      |

Vincoli:

- ogni organizzazione appartiene a un cliente commerciale;
- una stessa organizzazione non può appartenere contemporaneamente a due clienti commerciali;
- `parent_organization_id` consente gerarchia annidata;
- non devono essere imposti limiti arbitrari al numero di livelli;
- la gerarchia non deve sostituire la relazione commerciale con il cliente P.IVA.

La possibilità di cambiare cliente commerciale di un'organizzazione non viene trattata come una semplice modifica del campo: deve essere governata da un processo controllato, con effetti commerciali e storici da definire nelle fasi dipendenti.

### E. Membership

Rappresenta l'appartenenza operativa di un account a un'organizzazione.

Campi concettuali:

| Campo             | Significato                         |
| ----------------- | ----------------------------------- |
| membership_id     | Identificativo stabile              |
| user_id           | Account                             |
| organization_id   | Organizzazione                      |
| operational_role  | Ruolo operativo nell'organizzazione |
| membership_status | Stato appartenenza                  |
| valid_from        | Inizio validità                     |
| valid_to          | Fine validità                       |
| created_at        | Creazione                           |
| ended_at          | Chiusura                            |

Regola fondamentale:

Un collaboratore può avere una sola appartenenza operativa attiva alla volta.

Le appartenenze terminate devono rimanere storicizzate e non essere eliminate fisicamente con un semplice `$pull`.

La gestione dettagliata dei ruoli, dei poteri e delle autorizzazioni è rinviata a B02.

### F. Representation

Rappresenta la relazione mediante la quale una persona o un account è autorizzato a rappresentare un'organizzazione o un cliente commerciale.

È distinta dalla Membership.

Campi concettuali:

| Campo                  | Significato                                      |
| ---------------------- | ------------------------------------------------ |
| representation_id      | Identificativo                                   |
| person_id              | Persona rappresentante                           |
| commercial_customer_id | Cliente commerciale rappresentato, se pertinente |
| organization_id        | Organizzazione rappresentata, se pertinente      |
| representation_type    | Tipo di rappresentanza                           |
| authority_scope        | Ambito della rappresentanza                      |
| valid_from             | Inizio                                           |
| valid_to               | Fine                                             |
| status                 | Stato                                            |

La stessa persona può avere relazioni di rappresentanza con organizzazioni diverse, anche appartenenti a clienti commerciali diversi, senza diventare automaticamente collaboratore operativo di tutte.

La rappresentanza deve essere documentabile e verificabile.

I poteri effettivi, le deleghe e i controlli di autorizzazione saranno specificati in B02. Non si attribuiscono automaticamente privilegi amministrativi in virtù della sola rappresentanza.

### G. OrganizationGroup

Il gruppo/franchising rimane un concetto separato.

Non deve essere utilizzato come sostituto di `CommercialCustomer`.

Può rappresentare una rete o un gruppo operativo/commerciale secondo le funzioni già previste, ma non determina automaticamente:

- appartenenza allo stesso cliente P.IVA;
- condivisione della subscription;
- condivisione del wallet;
- accesso ai dati CRM;
- delega amministrativa.

---

# 4. Relazioni target

Schema concettuale:

```
PERSON
  |
  | 1:N
  |
USER
  |
  | 1:N storico
  |
MEMBERSHIP
  |
  | N:1
  |
ORGANIZATION
  |
  | N:1
  |
COMMERCIAL_CUSTOMER
  |
  | 1:N
  |
ORGANIZATIONS
```

Relazioni aggiuntive:

```
PERSON
  |
  | 1:N
  |
REPRESENTATION
  |
  +----> COMMERCIAL_CUSTOMER
  |
  +----> ORGANIZATION

ORGANIZATION
  |
  | parent_organization_id
  |
ORGANIZATION
```

Relazioni commerciali future:

```
COMMERCIAL_CUSTOMER
  |
  +---- SUBSCRIPTION
  |
  +---- CENTRAL_CREDIT_WALLET
  |
  +---- AGGREGATED_LIMITS
```

Queste ultime sono indicate per rendere esplicito il punto di aggancio del modello commerciale. Non fanno parte dell'implementazione B01 e saranno trattate nella progettazione billing.

---

# 5. Regole di integrità del modello

| ID      | Regola                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------- |
| B01-I01 | Un cliente commerciale è identificato univocamente dalla P.IVA normalizzata nel relativo contesto nazionale |
| B01-I02 | Una organizzazione ha un solo cliente commerciale attivo                                                    |
| B01-I03 | Un cliente commerciale può avere più organizzazioni                                                         |
| B01-I04 | Organizzazioni con la stessa P.IVA devono convergere sullo stesso cliente commerciale                       |
| B01-I05 | Organizzazioni con P.IVA differenti non condividono automaticamente il cliente                              |
| B01-I06 | Una membership operativa attiva per account al massimo                                                      |
| B01-I07 | Le membership terminate rimangono storicizzate                                                              |
| B01-I08 | La rappresentanza non crea automaticamente membership                                                       |
| B01-I09 | Il cambio di organizzazione non cancella la storia precedente                                               |
| B01-I10 | La gerarchia organizzativa non sostituisce il legame al cliente commerciale                                 |
| B01-I11 | L'identità MLS resta autonoma per organizzazione                                                            |
| B01-I12 | Nessuna relazione di gruppo produce automaticamente accesso cross-tenant                                    |

---

# 6. Mapping dallo stato attuale al modello target

La baseline attuale utilizza principalmente:

- `users`;
- `agencies`;
- `agency_groups`;
- `users.agency_ids[]`;
- `users.active_agency_id`;
- `agencies.owner_id`;
- `agencies.group_id`;
- `agencies.fiscal.vat_number`.

Il mapping concettuale è il seguente.

| Stato attuale                                     | Destinazione target                          | Nota                                                 |
| ------------------------------------------------- | -------------------------------------------- | ---------------------------------------------------- |
| `users`                                           | User                                         | Conservare identità account e ID                     |
| Dati anagrafici eventualmente presenti in `users` | Person                                       | Richiede regole di separazione e riconciliazione     |
| `agencies`                                        | Organization                                 | Conservare ID e riferimenti storici ove possibile    |
| `agencies.fiscal.vat_number`                      | CommercialCustomer                           | Non trasferire automaticamente senza riconciliazione |
| `users.agency_ids[]`                              | Membership                                   | Ricostruire appartenenze attive                      |
| `users.active_agency_id`                          | Contesto organizzativo attivo                | Non sostituisce la membership                        |
| `agencies.owner_id`                               | Membership amministrativa e/o Representation | Non assumere equivalenza automatica                  |
| `agencies.group_id`                               | OrganizationGroup                            | Non convertire in cliente commerciale                |
| Storico `$pull` assente                           | Membership history                           | Non ricostruibile se mai registrato                  |
| `users.role`                                      | Identità/ruolo legacy da riconciliare        | Non è la futura fonte completa dei permessi          |

## 6.1 Regola per la P.IVA

Non creare un cliente commerciale per ogni agency.

Procedura concettuale di mapping:

1. acquisire la P.IVA presente nei dati fiscali;
2. normalizzarla;
3. raggruppare le organizzazioni per identificativo fiscale valido;
4. individuare quelle con la stessa P.IVA;
5. collegarle al medesimo cliente commerciale;
6. sottoporre a riconciliazione umana i casi ambigui, mancanti o discordanti.

La stessa P.IVA in più organizzazioni non è un duplicato da eliminare: è il caso previsto dal modello.

La P.IVA mancante non deve essere inventata o ricostruita per deduzione.

## 6.2 Regola per le appartenenze

`users.agency_ids[]` consente attualmente più appartenenze.

La conversione in Membership dovrà distinguere:

- appartenenza operativa attiva;
- appartenenza terminata;
- invito pendente;
- rappresentanza;
- eventuale appartenenza storica non documentata.

Non assumere che tutte le agency presenti nell'array rappresentino membership simultaneamente valide.

I conflitti dovranno essere identificati e sottoposti a riconciliazione.

## 6.3 Regola per owner

`agencies.owner_id` non deve essere convertito automaticamente in Main Admin.

Occorre distinguere:

- titolarità o proprietà dell'agenzia;
- Admin operativo dell'organizzazione;
- rappresentante del cliente commerciale;
- Main Admin commerciale.

Sono relazioni diverse.

## 6.4 Compatibilità con gli identificativi legacy

La proposta è conservare, ove possibile, gli ID attuali di `agencies` come riferimenti compatibili per le nuove Organization.

Non è ancora una decisione di migrazione.

Prima di scegliere una strategia definitiva occorrerà verificare tutte le dipendenze applicative da `agency_id`, comprese quelle MLS, documentali e commerciali.

Non si propone una rinominazione massiva immediata.

---

# 7. Rischi progettuali

| ID         | Rischio                                | Gravità    | Mitigazione progettuale                       |
| ---------- | -------------------------------------- | ---------- | --------------------------------------------- |
| B01-RSK-01 | P.IVA assente o errata                 | Critica    | Riconciliazione documentata e umana           |
| B01-RSK-02 | Duplicazione cliente commerciale       | Critica    | Unicità sulla nuova entità                    |
| B01-RSK-03 | Fusione impropria di organizzazioni    | Critica    | Separare cliente commerciale e organizzazione |
| B01-RSK-04 | Confusione tra owner e Main Admin      | Alta       | Relazioni distinte                            |
| B01-RSK-05 | Perdita storico membership             | Alta       | Ledger/storico append-only                    |
| B01-RSK-06 | Multi-membership incompatibile         | Alta       | Vincolo di appartenenza attiva unica          |
| B01-RSK-07 | Confusione rappresentanza/appartenenza | Alta       | Entità separate                               |
| B01-RSK-08 | Uso di group come customer             | Alta       | Separazione dei domini                        |
| B01-RSK-09 | Rottura dipendenze `agency_id`         | Alta       | Mapping e compatibilità controllata           |
| B01-RSK-10 | Gerarchie cicliche                     | Media/Alta | Vincolo anti-ciclo                            |
| B01-RSK-11 | P.IVA estera o non standard            | Media      | Regole fiscali per paese                      |
| B01-RSK-12 | Cambio P.IVA non storicizzato          | Alta       | Relazione commerciale versionata              |

## 7.1 Rischi non risolvibili con il solo design

- storico appartenenze mai registrato;
- P.IVA non presenti nei dati;
- identità commerciali ambigue;
- collegamenti Stripe multipli non riconciliati;
- eventuali relazioni di rappresentanza non documentate.

Il modello target può impedire nuovi errori, ma non può ricostruire automaticamente informazioni storiche inesistenti.

---

# 8. Criteri di accettazione B01

B01 potrà essere considerato progettualmente completo quando tutti i criteri seguenti saranno verificabili nella specifica approvata.

| ID       | Criterio             | Condizione di accettazione                                  |
| -------- | -------------------- | ----------------------------------------------------------- |
| B01-AC01 | Separazione entità   | Person, User, Organization e CommercialCustomer distinti    |
| B01-AC02 | Unicità P.IVA        | Un cliente commerciale univoco per P.IVA normalizzata       |
| B01-AC03 | Multi-organizzazione | Più organizzazioni possono appartenere allo stesso cliente  |
| B01-AC04 | Clienti distinti     | P.IVA diverse non vengono fuse                              |
| B01-AC05 | Membership           | Un solo rapporto operativo attivo per collaboratore         |
| B01-AC06 | Storico              | Le appartenenze terminate non vengono eliminate             |
| B01-AC07 | Rappresentanza       | Separata dall'appartenenza operativa                        |
| B01-AC08 | Admin organizzativo  | Ogni organizzazione ha un Admin identificabile              |
| B01-AC09 | Main Admin           | Concetto commerciale distinto da Branch Admin e group_admin |
| B01-AC10 | Gerarchia            | Supporto di livelli organizzativi annidati                  |
| B01-AC11 | Gruppi               | Group/franchising non equivale a cliente commerciale        |
| B01-AC12 | Autonomia MLS        | Ogni organizzazione mantiene la propria identità MLS        |
| B01-AC13 | Compatibilità        | Mapping dei riferimenti legacy documentato                  |
| B01-AC14 | Integrità            | Relazioni e vincoli descritti senza ambiguità               |
| B01-AC15 | Dati incerti         | Nessuna attribuzione automatica di dati mancanti o ambigui  |

Il superamento di questi criteri riguarda la qualità della progettazione, non l'implementazione.

---

# 9. Dipendenze verso B02–B07

Questa sezione identifica soltanto le dipendenze. Non apre né progetta i blocchi successivi.

**Nota di correzione rispetto alla bozza ChatGPT:** numerazione allineata al backlog FASE 2 (`B04` = billing / ANO-008; `B05` = MLS / ANO-006; `B06` = documenti / ANO-007; `B07` = migrazione / ANO-009).

| Blocco | Area                             | Dipendenza da B01                                                                                        |
| ------ | -------------------------------- | -------------------------------------------------------------------------------------------------------- |
| B02    | Autorizzazioni e audit           | Utilizza Organization, Membership, Representation e separazione Main/Branch Admin                        |
| B03    | Sessioni, registrazione e inviti | Deve rispettare identità account, appartenenza unica e ciclo di vita Membership                          |
| B04    | Billing                          | Deve utilizzare CommercialCustomer come riferimento per subscription, wallet e limiti aggregati          |
| B05    | MLS                              | Deve utilizzare Organization come identità autonoma e non confondere cliente commerciale con agenzia MLS |
| B06    | Documenti e fascicoli            | Deve restare ancorato a Organization e a Membership/Representation per autorizzazioni                    |
| B07    | Migrazione                       | Deve applicare il mapping legacy verso le entità target, con riconciliazione umana                       |

Il collaudo integrato successivo ai risanamenti non è un item del backlog B01–B07 e non va confuso con la fotografia statica già chiusa.

## 9.1 Dipendenze critiche

- B02 non può assumere che `users.role` globale rappresenti già il ruolo per membership.
- B03 non può consentire che l'accettazione di un invito produca una seconda appartenenza operativa attiva.
- B04 non può continuare a considerare ogni agency un cliente commerciale autonomo.
- B05 non può utilizzare il cliente commerciale come sostituto dell'identità MLS dell'organizzazione.
- B06 non può autorizzare condivisioni documentali senza provenienza Membership/Representation.
- B07 non può attribuire P.IVA mancanti o ricostruire membership storiche non registrate.

---

# 10. Questioni da non considerare automaticamente risolte

Il design non decide automaticamente:

1. se Person e User debbano essere sempre due record separati in ogni caso;
2. come trattare account legacy privi di dati anagrafici sufficienti;
3. quale processo documentale validi la rappresentanza;
4. quale regola applicare ai casi di P.IVA estera o variazione fiscale;
5. come gestire una modifica della P.IVA di un'organizzazione senza perdere la storia commerciale;
6. come rappresentare le organizzazioni senza P.IVA;
7. come migrare i rapporti owner/Admin già esistenti;
8. come gestire eventuali collaboratori attualmente presenti in più agency.

Questi punti richiedono specifica o riconciliazione prima di un'eventuale implementazione. Non devono essere risolti con assunzioni implicite.

---

# 11. Confini di B01

B01 comprende esclusivamente la progettazione di:

- identità e account;
- cliente commerciale;
- organizzazione;
- gerarchia;
- appartenenza;
- rappresentanza;
- mapping concettuale;
- vincoli di integrità.

B01 non comprende:

- progettazione dettagliata RBAC e capability;
- implementazione delle deleghe;
- sessioni e revoche;
- flussi di invito;
- modello billing e wallet;
- modello completo MLS;
- migrazione dati;
- modifiche al codice o al database;
- test mutativi;
- PR o deploy.

---

# 12. Conclusione B01

La progettazione proposta separa i cinque concetti che nell'architettura attuale risultano sovrapposti: persona, account, organizzazione, cliente commerciale e appartenenza.

Il punto architetturale centrale è `CommercialCustomer`, identificato dalla P.IVA e distinto dalle singole organizzazioni.

Le organizzazioni rimangono autonome sul piano operativo e MLS, pur condividendo il rapporto commerciale quando appartengono alla stessa P.IVA.

La membership operativa viene separata dalla rappresentanza e storicizzata.

**Stato finale:**

- Design B01 prodotto.
- Nessun codice scritto.
- Nessuna modifica repository (salvo eventuale export documentale in `_export_audits/`).
- Nessuna migrazione.
- Nessuna PR di prodotto.
- Nessun test mutativo.
- B02 non aperto.
- B03–B07 non aperti.

---

## Punto di attenzione prima di considerare B01 chiuso

Tre aspetti progettuali non considerati automaticamente risolti:

1. **Person vs User:** separazione architetturalmente utile; serve regola di identità per account legacy.
2. **Owner vs Main Admin:** non intercambiabili; il modello li mantiene separati.
3. **Membership vs Representation:** essenziale per rappresentanza multipla senza violare l'appartenenza operativa unica.

Sono punti da validare nel design B01, non autorizzazioni a intervenire sul codice.
