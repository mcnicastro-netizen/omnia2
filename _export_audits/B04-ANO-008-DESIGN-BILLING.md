# OMNIA — B04 DESIGN HANDOFF
## Billing / ANO-008 — Documento decisionale per Cursor

**Data:** 17 novembre 2026  
**Stato:** DESIGN B04 CHIUSO  
**Approvazione:** Founder  
**Perimetro:** progettazione funzionale e tecnica del billing OMNIA  
**Implementazione:** NON AUTORIZZATA da questo documento

Fonte: sessione design ChatGPT + Founder, consegnata a Cursor il 17 novembre 2026 (Europe/Rome).

---

# 1. Mandato e stato

Il design B04 è concluso. Questo documento consolida le decisioni Founder B04-DES-01…10 e i vincoli B01, B02, B03 e B16.

Cursor dovrà utilizzare questo handoff come specifica decisionale per la futura implementazione, senza reinterpretare o riaprire le decisioni approvate.

**Importante:** la chiusura del design non dimostra che le funzionalità siano implementate, né che repository, database, Stripe o produzione siano conformi.

Non si autorizzano con questo documento:

- modifiche al codice;
- modifiche al database;
- migrazioni;
- modifiche Stripe;
- deploy o interventi in produzione;
- apertura automatica di B05–B07.

Qualsiasi implementazione richiederà una successiva autorizzazione esplicita del Founder, con scope e slice definiti.

# 2. Principio commerciale non negoziabile

**Una P.IVA = un CommercialCustomer = un contratto/abbonamento = un wallet centrale.**

Conseguenze:

- più Organization possono appartenere allo stesso CommercialCustomer;
- le filiali con la stessa P.IVA condividono un unico rapporto commerciale, una subscription e un wallet centrale;
- una P.IVA diversa identifica un CommercialCustomer distinto, con contratto e wallet propri;
- nessuna duplicazione di abbonamento o wallet per singola Organization;
- le variazioni organizzative non modificano automaticamente il cliente commerciale.

Le normali operazioni organizzative sono gestite dagli Admin autorizzati, secondo B02 e i rispettivi poteri. Non è previsto un workflow ordinario del Super Admin per gestire le filiali.

Il Super Admin interviene soltanto in casi eccezionali, motivati e tracciati.

# 3. Registro decisioni B04

## B04-DES-01 — Collegamento CommercialCustomer / Stripe Customer

**APPROVATA**

- Ogni CommercialCustomer ha un solo Stripe Customer stabile.
- Checkout e operazioni successive riutilizzano il Customer esistente.
- Il collegamento è univoco e riconciliabile.
- Customer legacy o duplicati non vengono associati automaticamente per semplice somiglianza.
- Cambio carta, IBAN o metodo di pagamento non crea un nuovo Stripe Customer, un nuovo CommercialCustomer o un nuovo contratto.
- Il metodo di pagamento viene aggiornato sul Customer esistente.

## B04-DES-02 — Macchina a stati OMNIA

**APPROVATA**

- Stripe fornisce eventi e dati economici.
- OMNIA determina autonomamente stato commerciale e stato operativo.
- Stato Stripe, stato commerciale OMNIA e stato operativo OMNIA sono concetti distinti.
- Nessun evento Stripe modifica indiscriminatamente tutti gli stati OMNIA.
- Eventi duplicati e fuori ordine devono essere gestiti in modo idempotente e tracciabile.
- Le transizioni rispettano B16, inclusi grazia, sospensione, disdetta e cessazione.

I campi temporali ipotizzati durante il design non sono stati approvati singolarmente come schema obbligatorio. La loro definizione tecnica dovrà rispettare le decisioni funzionali.

## B04-DES-03 — Catalogo, condizioni commerciali e Founder

**APPROVATA**

- Catalogo OMNIA versionato: una versione pubblicata non viene sovrascritta.
- Ogni subscription conserva uno snapshot delle condizioni commerciali accettate.
- Le nuove versioni si applicano alle nuove sottoscrizioni dalla relativa data di efficacia.
- Nessuna modifica automatica o retroattiva delle condizioni degli abbonamenti attivi per il solo aggiornamento del catalogo.
- Founder dura 12 mesi dalla prima subscription pagata e attivata (`first_paid_activated_at`).
- Il periodo Founder è unico per CommercialCustomer e non riparte con un upgrade.
- Alla scadenza si applicano le condizioni Standard.
- Upgrade e downgrade rispettano B16 e DES-06.

Listino di riferimento: `PRICING_OMNIA.md` v3.3 del 9 novembre 2026:

- Starter Founder €49 / Standard €79;
- Pro Founder €99 / Standard €179;
- Agency Founder €299 / Standard €399;
- annuale pari a 11 mensilità;
- storage add-on 100 GB a €15/mese;
- credito €0,05;
- tre piani pubblici;
- nessun piano Enterprise pubblico;
- nessuna prova gratuita self-service;
- multiposting e Portal Wizard Custom inclusi.

Precisazione Founder: un eventuale repricing degli abbonamenti attivi per ragioni economiche o commerciali gravi richiede una decisione Founder esplicita e separata, comunicazione ai clienti, decorrenza definita e processo di accettazione/rifiuto. Sono vietate modifiche silenziose o retroattive.

## B04-DES-04 — Wallet centrale e ledger

**APPROVATA**

Componenti logiche:

- CreditWallet;
- CreditLot;
- CreditAllocation;
- CreditLedgerEntry.

Regole:

- un wallet centrale per CommercialCustomer;
- i lotti conservano provenienza, quantità originaria e residua;
- Main Admin assegna, revoca e redistribuisce crediti alle Organization;
- Branch Admin vede soltanto assegnazioni e consumi della propria Organization;
- FIFO sui lotti più vecchi;
- ledger permanente e tracciabile;
- correzioni tramite movimenti compensativi, senza alterare lo storico;
- assegnazione, revoca e consumo atomici;
- prevenzione di doppio consumo, over-allocation e incoerenze.

Vincoli B16:

- upgrade conserva i residui e riconosce la nuova allowance;
- downgrade conserva i residui e applica l'allowance inferiore dal ciclo successivo;
- crediti inclusi e acquistati non scadono;
- insoluto e sospensione conservano i crediti, ma ne bloccano la spendibilità;
- cessazione senza rimborso, liquidazione o trasferimento;
- uscita di una filiale: crediti assegnati non consumati restituiti al wallet centrale precedente;
- nessun trasferimento tra P.IVA diverse.

## B04-DES-05 — Limiti aggregati

**APPROVATA**

Limiti utenti e immobili applicati al CommercialCustomer, non alle singole Organization.

Utenti:

- inviti pendenti conteggiati;
- account sospesi esclusi;
- riattivazione subordinata alla disponibilità di uno slot;
- superamento del limite blocca nuove creazioni/attivazioni;
- nessuna cancellazione automatica degli utenti esistenti.

Immobili:

- limite aggregato per P.IVA;
- creazione e riattivazione bloccate quando il plafond è esaurito;
- nessuna cancellazione o archiviazione automatica.

Backend autorità definitiva. Verifica e operazione devono essere atomiche, con protezione dalle operazioni concorrenti tra Organization.

## B04-DES-05b — Conteggio immobili

**APPROVATA**

Si conta il portafoglio operativo, non tutto lo storico.

SoT:

- una Property ha un solo `agency_id`;
- MLS è visibilità, non ownership;
- status commerciali: `draft`, `active`, `reserved`, `sold`, `rented`, `withdrawn`;
- cestino/soft delete identificato da `deleted_at`;
- non esiste uno status `archived` approvato.

Conteggio:

- `draft`: SÌ;
- `active`: SÌ;
- `reserved`: SÌ;
- `sold`: NO;
- `rented`: NO;
- `withdrawn`: NO;
- `deleted_at` valorizzato: NO;
- sola visibilità MLS di scheda altrui: NO;
- seconda Property distinta per lo stesso bene in altra filiale: SÌ, secondo slot.

Ulteriori regole:

- restore dal cestino richiede uno slot;
- riapertura commerciale da `sold`, `rented` o `withdrawn` a uno status operativo richiede uno slot;
- `sold` e `rented` sono conclusivi e lo storico va preservato;
- se il bene torna sul mercato, la preferenza approvata è riaprire lo stesso documento, consumando un nuovo slot;
- una futura operazione di trasferimento tra filiali dovrà essere un move di ownership, non una copia silenziosa;
- media e documenti continuano a consumare storage anche quando la Property non occupa uno slot;
- nessuna cancellazione automatica;
- nessuno status `archived` senza decisione Founder separata.

## B04-DES-06 — Maturazione crediti e cessazione

**APPROVATA — P01…P07 e precisazioni X1/X2/X3**

P01 — Periodicità allowance:

- allowance mensile a ogni periodo di servizio, anche con pagamento annuale;
- nessun accredito anticipato dei dodici mesi;
- ogni maturazione genera un lotto nel wallet centrale.

P02 — Rinnovo:

- una sola allowance per ogni nuovo periodo mensile;
- residui conservati;
- nessun azzeramento o sovrascrittura dei lotti.

P03 — Upgrade:

- all'efficacia upgrade, una sola nuova allowance del piano superiore;
- residui precedenti conservati;
- nessun riavvio del periodo Founder.

P04 — Downgrade:

- nessuna riduzione immediata dei residui;
- piano inferiore dal periodo successivo;
- tutti i crediti già maturati restano conservati.

P05 — Insoluto e grazia:

- grazia di sette giorni dal primo pagamento ricorrente fallito;
- retry successivi non riavviano il conteggio;
- piena operatività durante i sette giorni;
- allowance maturate normalmente;
- dal giorno 8 sospensione secondo B16;
- recupero pagamento riattiva automaticamente;
- nessun secondo accredito per allowance già maturata.

P06 — Idempotenza e riconciliazione:

- un solo accredito per CommercialCustomer e periodo;
- webhook duplicati non producono doppi lotti;
- eventi fuori ordine non alterano retroattivamente il saldo;
- rielaborazione senza duplicazione;
- ogni accredito riconciliabile con subscription, periodo, piano e origine;
- correzioni tramite movimenti compensativi.

P07 — Disdetta e cessazione:

- richiesta registrata subito;
- servizio pienamente operativo fino alla fine del periodo già pagato;
- cessazione successiva secondo le regole B16;
- nessun rimborso automatico dei crediti residui;
- dopo cessazione non maturano nuove allowance;
- data richiesta distinta dalla data effettiva di cessazione.

P07-X1 — Crediti dopo cessazione:

- residui conservati nel ledger permanente;
- non rimborsabili, liquidabili o trasferibili ad altra P.IVA;
- non spendibili dopo cessazione;
- nessun azzeramento o cancellazione dello storico.

P07-X2 — Ambito:

- disdetta e cessazione riguardano il CommercialCustomer e tutte le Organization collegate;
- nessuna Organization può mantenere autonomamente i diritti del piano dopo la cessazione del cliente.

P07-X3 — Disdetta durante insoluto/grazia:

- disdetta durante periodo regolare: cessazione alla fine dell'ultimo periodo pagato;
- disdetta durante grazia, senza recupero: cessazione alla fine dei sette giorni di grazia;
- disdetta durante grazia, con recupero: cessazione alla fine del periodo di servizio regolarizzato;
- nel caso di disdetta durante la grazia senza recupero non si avvia un ulteriore percorso di sospensione ordinaria dal giorno 8;
- fatture insolute restano debiti dovuti anche dopo la cessazione;
- disdetta presentata dopo la sospensione non riavvia né prolunga la grazia.

## B04-DES-07 — Entitlements operativi

**APPROVATA**

OMNIA determina i diritti effettivi sulla base dello stato commerciale e operativo del CommercialCustomer, dei limiti, del wallet e delle autorizzazioni B02.

Matrice:

- Pre-attivazione: solo registrazione, configurazione iniziale e checkout; nessuna operatività gestionale.
- Attivo: piena operatività prevista dal piano.
- Disdetta pendente, periodo pagato ancora in corso: piena operatività.
- Grazia giorni 1–7: piena operatività.
- Sospensione dal giorno 8: Branch Admin e tutti gli altri utenti diversi dal Main Admin bloccati; Main Admin limitato a metodo di pagamento, fatture insolute e fatture.
- Cessazione: nessuna operatività gestionale per tutte le Organization; Main Admin può consultare documentazione di chiusura e fatturazione.

Creazione, inviti, attivazione, restore e reopen di utenti/immobili rispettano stato e limiti aggregati.

Consumo crediti e pubblicazione:

- consentiti in stato attivo e durante grazia;
- bloccati durante sospensione e cessazione.

MLS e collaborazione restano subordinate allo stato operativo e alle autorizzazioni B02, senza modificare le regole funzionali MLS.

Backend autorità definitiva. Stato del cliente applicato coerentemente a tutte le Organization. Nessuna perdita automatica di dati o storico.

## B04-DES-08 — Area Amministrazione e fatturazione B2B

**APPROVATA**

Un'unica area riferita al CommercialCustomer/P.IVA.

Main Admin:

- piano e abbonamento;
- metodo di pagamento;
- tutte le fatture OMNIA;
- storico pagamenti;
- insoluti e debiti;
- stato e richiesta di disdetta;
- wallet centrale;
- assegnazioni, revoche e redistribuzioni;
- consumi;
- limiti aggregati.

Branch Admin:

- nessun accesso al rapporto commerciale, abbonamento, metodo di pagamento, fatture o debiti;
- vede soltanto assegnazioni e consumi della propria Organization;
- può consultare i limiti aggregati, senza poteri di gestione commerciale.

Durante la grazia il Main Admin conserva l'accesso completo e può regolarizzare.

Durante sospensione si applicano le limitazioni B16 e DES-07.

Dopo disdetta ma prima della cessazione l'area resta normalmente disponibile, con data di cessazione visibile.

Dopo cessazione sono consentite consultazione e download della documentazione di chiusura e fatturazione, senza operazioni gestionali o di wallet.

Le operazioni sono tracciate secondo B02.

## B04-DES-09 — Mapping eventi Stripe → OMNIA

**APPROVATA**

Stripe comunica eventi e dati economici; OMNIA determina gli stati e le transizioni.

Eventi considerati:

- `customer.created`;
- `customer.updated`;
- `checkout.session.completed`;
- `customer.subscription.created`;
- `customer.subscription.updated`;
- `customer.subscription.deleted`;
- `invoice.created`;
- `invoice.finalized`;
- `invoice.paid`;
- `invoice.payment_failed`;
- `payment_method.attached`;
- `payment_method.updated`;
- `credit_note.created`;
- `charge.refunded`.

Principi:

- `checkout.session.completed` non equivale automaticamente ad attivazione pagata;
- `invoice.paid` alimenta le verifiche di attivazione, recupero insoluto e maturazione allowance, con idempotenza;
- `invoice.payment_failed` alimenta il primo insoluto e la grazia, senza riavvio per retry;
- `customer.subscription.deleted` richiede riconciliazione con disdetta, date e regole OMNIA;
- nessun singolo evento Stripe impone autonomamente sospensione o cessazione OMNIA;
- Customer Stripe riconciliato con il CommercialCustomer stabile;
- note di credito e rimborsi non modificano automaticamente il wallet;
- eventi duplicati/fuori ordine e riconciliazioni devono essere gestiti e tracciati;
- audit secondo B02.

## B04-DES-10 — Casi limite multi-Organization

**APPROVATA**

Regola invariabile:  
**Una P.IVA = un CommercialCustomer = un contratto = un wallet centrale.**

- variazioni organizzative tra Organization con stessa P.IVA non creano un nuovo cliente, contratto o wallet;
- uscita dalla gerarchia, riorganizzazione e chiusura ordinaria di Organization sono gestite dagli Admin autorizzati secondo B02;
- nessun workflow ordinario del Super Admin;
- Super Admin soltanto per interventi eccezionali, motivati e tracciati;
- P.IVA diversa comporta un nuovo CommercialCustomer, un nuovo contratto e un nuovo wallet.

La decisione non autorizza trasferimenti automatici di immobili o documenti. Le operazioni su tali risorse devono rispettare ownership, autorizzazioni e poteri effettivi. Nessuna copia o trasferimento silenzioso.

---

# 4. Vincoli ereditati da B01–B03 e B16

Cursor deve rispettare integralmente:

**B01 — Modello dati**

- CommercialCustomer identificato da P.IVA normalizzata;
- unicità sul CommercialCustomer, non su Organization;
- più Organization per lo stesso cliente;
- Organization autonoma per identità MLS;
- User, Person, Membership e Representation distinti;
- non creare Person inventate;
- mapping legacy con riconciliazione umana per P.IVA ambigue o mancanti.

**B02 — Autorizzazioni e audit**

- ruoli distinti da capability;
- deny by default;
- backend autorità definitiva;
- Main Admin non ha accesso automatico al CRM delle filiali;
- Admin organizzazione = Branch Admin;
- deleghe e grant espliciti, selettivi, revocabili e tracciati;
- audit centrale append-only, inclusi denied e interventi Super Admin;
- nessuna escalation di privilegi.

**B03 — Identità, sessioni e inviti**

- email verificata prima delle funzioni operative;
- cambio/reset password invalida tutte le sessioni;
- accettazione invito atomica e idempotente;
- una sola Membership operativa attiva;
- invito distinto da Representation;
- nessuna escalation tramite invito.

**B16 — Billing**

- tutte le decisioni approvate su P.IVA, subscription, Founder, piani, crediti, grace, sospensione, cessazione, disdetta e fatturazione restano vincolanti;
- B16-CC-07: area unica Amministrazione e fatturazione per Main Admin;
- crediti conservati ma non spendibili durante sospensione;
- nessun rimborso o trasferimento dei residui alla cessazione.

Non riaprire decisioni già approvate.

# 5. Punti OPEN e fuori perimetro

La chiusura B04 non significa che ogni possibile questione futura sia già decisa.

I seguenti temi non autorizzano interpretazioni autonome:

1. **Repricing di abbonamenti attivi:** richiede una futura decisione Founder separata, secondo DES-03. Non implementare un meccanismo di modifica retroattiva o silenziosa. (Programma OMNIA: `B04-OPEN-FOLLOWUPS.md` → B04-OPEN-01.)
2. **Casi legacy di P.IVA mancanti, ambigue o duplicate:** seguono la riconciliazione umana prevista da B01. Nessuna associazione automatica per somiglianza.
3. **Trasferimento di immobili/documenti tra Organization:** non è autorizzata alcuna copia o migrazione silenziosa; il workflow futuro deve rispettare ownership e autorizzazioni.
4. **Dettagli tecnici non approvati singolarmente:** nomi definitivi dei campi, indici, collezioni, API, struttura webhook, retry tecnici, scheduler, osservabilità e procedure operative sono scelte implementative da verificare, non nuove decisioni funzionali.
5. **Verifica della baseline post-Slice 1:** l'audit B16 storico precede la Slice 1. Non usarlo come prova della situazione tecnica corrente.

Questi punti non riaprono il design B04 e non autorizzano Cursor a risolverli unilateralmente.

Fuori perimetro:

- B05 MLS;
- B06 documenti;
- B07 migrazione;
- implementazione e deploy;
- migrazione dati di produzione;
- interventi Stripe live;
- cambi di listino senza decisione Founder.

# 6. Ordine consigliato per la futura implementazione

L'ordine seguente è una proposta tecnica di sequenziamento, **non un'autorizzazione**.

**Slice B04-I — Fondazioni commerciali e Stripe**

- verificare il risultato della Slice 1;
- CommercialCustomer e Organization già introdotti;
- relazione stabile uno-a-uno con Stripe Customer;
- riuso Customer in checkout e aggiornamenti;
- catalogo versionato e snapshot delle condizioni;
- separazione stati Stripe, commerciali e operativi OMNIA.

**Slice B04-II — Wallet centrale e ledger**

- wallet per CommercialCustomer;
- lotti, allocazioni e ledger;
- assegnazione/revoca atomiche;
- FIFO;
- idempotenza dei movimenti;
- tracciabilità e riconciliazione.

**Slice B04-III — Allowance e cicli subscription**

- maturazione mensile;
- annuale senza accredito anticipato;
- rinnovo;
- upgrade/downgrade;
- Founder;
- prevenzione dei doppi accrediti.

**Slice B04-IV — Enforcement limiti aggregati**

- utenti e inviti;
- immobili secondo DES-05b;
- create, activate, restore e reopen;
- controlli atomici e concorrenza tra Organization.

**Slice B04-V — Macchina a stati e insoluti/disdette**

- grazia;
- notifiche 1/4/7 al Main Admin;
- sospensione giorno 8;
- recupero e riattivazione;
- disdetta regolare;
- disdetta durante grazia;
- cessazione di tutte le Organization;
- conservazione crediti e storico.

**Slice B04-VI — Entitlements e area amministrativa**

- permessi effettivi;
- restrizioni per stato;
- area Amministrazione e fatturazione;
- Main Admin e Branch Admin;
- consultazione fatture e storico;
- accesso limitato in sospensione e cessazione.

**Slice B04-VII — Riconciliazione, audit e collaudo**

- mapping eventi Stripe;
- eventi duplicati e fuori ordine;
- riconciliazione;
- audit;
- test multi-Organization;
- test limiti concorrenti;
- test disdetta e insoluto;
- test regressione B01–B03.

Le dipendenze reali dovranno essere verificate sul repository prima di fissare l'ordine definitivo.

# 7. Requisiti per il lavoro futuro di Cursor

Quando autorizzato dal Founder:

1. effettuare prima una verifica read-only della baseline e dello stato effettivo del codice;
2. confrontare le decisioni con il codice esistente, senza presumere che gli audit storici siano ancora aggiornati;
3. produrre una matrice decisione → componente/API/dati/test;
4. identificare gap e dipendenze;
5. proporre una slice circoscritta;
6. attendere autorizzazione esplicita per quella slice;
7. implementare soltanto lo scope autorizzato;
8. fornire test, evidenze, commit e PR;
9. distinguere chiaramente implementato, testato, mergiato e verificato in produzione.

Non eseguire migrazioni o operazioni distruttive senza autorizzazione specifica.

# 8. Stato finale

**DESIGN B04 — CHIUSO**

Decisioni Founder:

- B04-DES-01 — APPROVATA
- B04-DES-02 — APPROVATA
- B04-DES-03 — APPROVATA
- B04-DES-04 — APPROVATA
- B04-DES-05 — APPROVATA
- B04-DES-05b — APPROVATA
- B04-DES-06 — APPROVATA, P01–P07 e X1/X2/X3
- B04-DES-07 — APPROVATA
- B04-DES-08 — APPROVATA
- B04-DES-09 — APPROVATA
- B04-DES-10 — APPROVATA

Tutte le decisioni sono funzionalmente approvate. Questo non equivale a implementazione o verifica tecnica.

**ISTRUZIONE A CURSOR:** acquisire questo documento come specifica decisionale B04. Non scrivere codice, non modificare repository, database o Stripe, non avviare migrazioni e non passare a B05–B07. Attendere una successiva autorizzazione esplicita del Founder.

**Fine handoff B04.**
