# OMNIA — AUDIT TECNICO B15 (verifica conformità decisioni)

**Fonte:** `bc-7947c9a1` · **Quando:** 2026-11-14 ~01:19 Europe/Rome  
**URL:** https://cursor.com/agents/bc-7947c9a1-3caa-4587-9443-85f55836c277

---

## Prompt commissionato

Preparo il nuovo incarico per Cursor. È un audit tecnico completo dell'Area B15, aggiornato con tutte le decisioni che abbiamo appena approvato.
Sola lettura — nessuna modifica autorizzata
# OMNIA — AUDIT TECNICO B15
## Verifica di conformità alle decisioni funzionali approvate
### 1. OBIETTIVO
Eseguire un audit tecnico approfondito del repository OMNIA per verificare lo stato effettivo del codice rispetto a tutte le decisioni funzionali e di sicurezza dell'Area B15.
L'obiettivo è produrre una fotografia attendibile della situazione attuale e un piano ordinato degli interventi necessari.
**ATTENZIONE: QUESTA È ESCLUSIVAMENTE UN'ATTIVITÀ DI AUDIT.**
È vietato:
- modificare codice;
- modificare database o documenti;
- modificare configurazioni;
- creare o modificare indici;
- eseguire migrazioni;
- correggere automaticamente problemi;
- modificare test esistenti;
- effettuare operazioni distruttive o di attivazione;
- modificare documentazione o registri decisionali.
Puoi esaminare codice, test, modelli, configurazioni e documentazione esistenti.
### 2. IDENTIFICAZIONE DEL CLIENTE OMNIA E PARTITA IVA
Decisioni approvate:
1. Una partita IVA identifica un solo cliente commerciale OMNIA.
2. La stessa partita IVA non può generare due clienti OMNIA distinti.
3. Una stessa persona può essere titolare o rappresentante di più organizzazioni, se hanno partite IVA differenti.
4. Organizzazioni con partite IVA differenti hanno clienti OMNIA, abbonamenti, quote, collaboratori e dati separati.
5. Le filiali con la stessa partita IVA appartengono invece allo stesso cliente OMNIA e condividono abbonamento e plafond.
6. Una seconda persona che inserisce una partita IVA già presente non ottiene automaticamente accesso all'organizzazione esistente.
7. L'accesso richiede verifica dei poteri e autorizzazione da parte dei soggetti legittimati.
8. L'unicità della partita IVA deve essere garantita anche a livello database, non soltanto attraverso controlli nell'interfaccia.
Verificare:
- dove viene memorizzata la partita IVA;
- quale entità rappresenta il cliente commerciale OMNIA;
- eventuali duplicazioni tra collection o modelli;
- presenza di controlli di unicità applicativi;
- presenza di indici univoci effettivi;
- gestione di partite IVA con formati differenti;
- normalizzazione e validazione;
- comportamento con registrazioni contemporanee;
- comportamento con richieste duplicate;
- eventuali conflitti con agenzie, filiali, gruppi e holding;
- eventuali effetti sui collegamenti Stripe e sugli abbonamenti.
NON proporre un indice univoco su owner_id: una stessa persona può rappresentare più organizzazioni con partite IVA differenti.
Verificare inoltre come vengono gestite eventuali partite IVA estere o soggetti privi di partita IVA, senza introdurre nuove regole funzionali.
### 3. IDENTITÀ PERSONALE E APPARTENENZA A PIÙ ORGANIZZAZIONI
Decisioni approvate:
1. Una persona fisica deve poter utilizzare una sola identità personale OMNIA.
2. La stessa identità può essere associata a più organizzazioni.
3. Ogni associazione ha ruolo, autorizzazioni e appartenenza indipendenti.
4. Le organizzazioni mantengono dati, collaboratori, abbonamenti e permessi separati.
5. L'accesso a una seconda organizzazione non deriva automaticamente dalla semplice identità personale.
Verificare:
- modello User;
- relazioni user-organization;
- agency memberships;
- eventuali vincoli di unicità sull'email;
- possibilità di associare lo stesso utente a più organizzazioni;
- selezione dell'organizzazione attiva;
- gestione di ruoli e permessi per singola organizzazione;
- eventuali conflitti con active_agency_id e agency_ids;
- impatto sulle sessioni JWT;
- eventuali accessi incrociati involontari.
### 4. CAMBIO DI ORGANIZZAZIONE ATTIVA
Decisioni approvate:
Quando una persona cambia organizzazione:
1. OMNIA deve verificare l'appartenenza alla nuova organizzazione.
2. Deve verificare nuovamente ruolo e autorizzazioni.
3. Deve sostituire il contesto precedente.
4. Non deve conservare permessi derivanti dall'organizzazione precedente.
5. Deve impedire accessi residui ai dati dell'organizzazione precedente.
6. Deve registrare il cambio nel registro comune degli eventi di sicurezza.
Verificare backend, frontend, API, token, cache, richieste simultanee e sessioni aperte.
Prestare particolare attenzione a:
- richieste API già avviate durante il cambio;
- schermate che conservano dati precedenti;
- ID di risorse appartenenti a un'altra organizzazione;
- controlli tenant;
- endpoint che utilizzano agency_ids;
- eventuali autorizzazioni ereditate o troppo ampie.
Non introdurre controlli che richiedano verifiche costose su ogni richiesta senza prima documentare le alternative tecniche.
### 5. ATTIVAZIONE ORGANIZZAZIONE E RISCHIO WIPE_CRM
Decisione approvata:
Una normale operazione Ops Attiva non può riattivare un'organizzazione già attiva.
Una seconda attivazione deve:
- essere rifiutata;
- non cancellare dati;
- non modificare CRM;
- non modificare abbonamento o stato;
- non produrre effetti collaterali.
Eventuali interventi straordinari su organizzazioni attive devono seguire una procedura separata, esplicita e tracciata.
Verificare:
- endpoint di attivazione;
- parametro wipe_crm;
- valore predefinito;
- controlli sullo stato corrente;
- possibilità di doppie richieste;
- idempotenza;
- eventuali webhook o retry;
- test esistenti;
- possibilità di perdita di dati.
Individuare in particolare ogni percorso che possa provocare la cancellazione del CRM di un'organizzazione già attiva.
### 6. INVITI E ATTIVAZIONE COLLABORATORI
Decisioni approvate:
1. Il collaboratore riceve un invito personale via email.
2. Il link permette di verificare il possesso dell'indirizzo email invitato.
3. Il token deve essere valido, non scaduto e monouso.
4. L'indirizzo verificato deve coincidere esattamente con quello dell'invito.
5. L'accettazione imposta email_verified=true.
6. L'accettazione registra correttamente la sessione e il refresh token.
7. Un account esistente mantiene la propria password.
8. L'accettazione dello stesso invito deve essere atomica anche con richieste simultanee.
9. Una sola richiesta può completare l'accettazione.
10. Le richieste successive devono essere rifiutate senza creare duplicazioni.
Verificare:
- generazione e conservazione del token;
- scadenza;
- uso singolo;
- revoca;
- atomicità del controllo e aggiornamento;
- concorrenza;
- collegamento a utenti esistenti;
- verifica dell'email;
- store_refresh;
- cookie e relative opzioni;
- creazione della membership;
- rispetto delle quote del piano;
- audit degli eventi.
Verificare specificamente il problema già segnalato da Cursor: l'accettazione dell'invito non registrava correttamente il refresh token e non impostava email_verified.
### 7. VERIFICA EMAIL UTENTI PRIVATI B2C
Decisione approvata:
Anche gli utenti privati che si registrano con email e password devono poter verificare il proprio indirizzo email.
La procedura prevista:
1. Registrazione.
2. Invio di un link personale.
3. Token monouso con scadenza.
4. Verifica dell'indirizzo.
5. Aggiornamento email_verified=true.
6. Accesso alle funzionalità che richiedono un indirizzo verificato.
La verifica email è distinta dalla verifica documentale KYC e dal pagamento delle agenzie.
Verificare:
- registrazione B2C;
- gestione email_verified;
- generazione e invio dei link;
- endpoint di verifica;
- scadenza e monouso;
- protezione da riutilizzo;
- sicurezza del token;
- eventuali funzionalità bloccate;
- flussi di recupero e reinvio della verifica;
- eventuali differenze tra registrazione con password e Google;
- test esistenti.
Non rimuovere il controllo email_verified dalle funzionalità che lo richiedono per aggirare il problema.
### 8. REGISTRO COMUNE DEGLI EVENTI
Verificare la compatibilità di tutti gli eventi precedenti con il registro comune B12 già approvato.
Gli eventi devono poter riportare:
- attore;
- utente interessato;
- data e ora;
- operazione;
- esito.
Verificare almeno:
- creazione organizzazione;
- tentativo di registrazione con partita IVA già presente;
- associazione di un utente a un'organizzazione;
- accettazione e rifiuto invito;
- cambio organizzazione attiva;
- attivazione e tentativo di riattivazione;
- verifica email;
- eventuali interventi Ops.
Riutilizzare i registri specifici già esistenti dove possibile, senza duplicare i sistemi di audit.
### 9. TEST E SICUREZZA
Esaminare test unitari, integrazione ed end-to-end.
Individuare test mancanti per:
- partita IVA duplicata;
- registrazioni simultanee con la stessa partita IVA;
- stessa persona con più organizzazioni;
- isolamento dei dati tra organizzazioni;
- cambio organizzazione;
- accesso con permessi non appartenenti al nuovo contesto;
- seconda attivazione Ops;
- doppia accettazione invito;
- accettazione invito simultanea;
- verifica email collaboratore;
- verifica email B2C;
- refresh token dopo accettazione invito;
- audit degli eventi.
Non eseguire test che modifichino dati reali o ambienti di produzione.
### 10. FORMATO OBBLIGATORIO DEL RAPPORTO
Produrre un rapporto strutturato con queste sezioni:
**A. Sintesi esecutiva**
- stato generale B15;
- criticità più importanti;
- rischi di sicurezza;
- rischi di perdita dati.
**B. Matrice decisioni/codice**
Per ogni decisione indicare:
- ID progressivo;
- decisione funzionale;
- file e funzioni interessati;
- stato: IMPLEMENTATO, PARZIALE, ASSENTE, NON VERIFICABILE;
- prove tecniche;
- eventuali anomalie.
**C. Problemi e rischi**\
Classificare:
- P0: rischio immediato di perdita dati o violazione grave;
- P1: problema di sicurezza o integrità importante;
- P2: funzionalità incompleta;
- P3: miglioramento non urgente.
**D. Dipendenze**\
Indicare quali interventi dipendono da altri interventi.
**E. Piano di intervento**\
Elencare gli interventi necessari, in ordine di priorità, senza implementare nulla.
**F. Test di accettazione**\
Per ogni intervento specificare i test che dovranno dimostrare il corretto funzionamento.
**G. Compatibilità**\
Indicare eventuali conflitti con:
- architettura multi-tenant;
- gerarchia organizzativa a matrioska;
- piani e abbonamenti;
- Stripe;
- MLS;
- ruoli e permessi;
- sessioni e sicurezza;
- decisioni già approvate nelle Aree A e B.
**H. Riepilogo finale**\
Separare chiaramente:
- già funzionante;
- da completare;
- da correggere;
- da decidere;
- da sottoporre a verifica legale o operativa.
### 11. REGOLE FINALI
Non reinterpretare le decisioni approvate.
Non introdurre nuove funzionalità o nuove regole di business.
Non considerare automaticamente un controllo frontend sufficiente a garantire la sicurezza.
Non proporre di ricostruire moduli già esistenti senza averne verificato il funzionamento.
Non confondere:
- persona fisica;
- soggetto fiscale;
- cliente commerciale OMNIA;
- organizzazione;
- filiale;
- membership;
- sessione.
Non modificare alcun file.
Il risultato deve essere un rapporto tecnico verificabile, con riferimenti precisi a file, funzioni, endpoint, modelli, indici e test.
**Al termine, fermati e attendi l'autorizzazione del Founder.**
### **Cosa fare adesso**
Invia a Cursor il documento completo e chiedigli di restituire il rapporto senza intervenire sul progetto.
Quando mi riporti il risultato, lo analizzeremo insieme: prima controlleremo le criticità e le prove tecniche, poi decideremo l'ordine degli interventi. Nessuna implementazione partirà automaticamente.

---

## Report

Marco, audit B15 completato in sola lettura. Nessuna modifica al progetto.

---

# OMNIA — AUDIT TECNICO B15  
## Conformità alle decisioni funzionali approvate

---

## A. Sintesi esecutiva

**Stato generale B15:** base operativa di registrazione, onboarding KYC/pagamento, inviti e multi-membership **parzialmente presente**, ma **non conforme** alle decisioni appena approvate su P.IVA=cliente, ruoli per organizzazione, idempotenza Attiva, sessione post-invito e verifica email B2C.

**Criticità più importanti**
1. **P0 — `wipe_crm=True` di default su Ops Attiva senza guard “già attiva”** → seconda Attiva può cancellare CRM di un’organizzazione già attiva.
2. **P0/P1 — unicità P.IVA assente** (né applicativa né indice DB); due titolari possono creare due “clienti” con la stessa P.IVA.
3. **P1 — accept-invite: niente `store_refresh`, niente `email_verified=true`, accettazione non atomica.**
4. **P1 — ruolo globale `users.role`**, non per organizzazione → permessi potenzialmente ereditati dopo switch/invito.
5. **P1 — verifica email B2C assente** (endpoint inesistente; gate valuator già richiede `email_verified`).

**Rischi sicurezza:** privilegio eccessivo cross-org via ruolo globale; refresh post-invito fragile; race su accept invite; nessuna traccia B12 su switch/Attiva/invito/VAT.

**Rischi perdita dati:** wipe CRM su ri-Attiva; wipe Ops dedicato senza procedura straordinaria tracciata; race create agency (controllo `owner_id` non atomico).

---

## B. Matrice decisioni / codice

| ID | Decisione funzionale | File / funzioni | Stato | Prove | Anomalie |
|---|---|---|---|---|---|
| **B15-01** | Una P.IVA = un solo cliente commerciale OMNIA | `AgencyInDB.fiscal.vat_number` in `backend/shared/models/agency.py`; create in `agencies.create_agency` | **ASSENTE** | Nessun `find` su VAT a create; manuale Cap.19 documenta “Nessun controllo unicità VAT” | Cliente commerciale = documento `agencies`, non entità dedicata |
| **B15-02** | Stessa P.IVA non genera due clienti | `ensure_indexes` in `connection.py` | **ASSENTE** | Indici agencies: `slug` unique, `owner_id` **non** unique; **nessun** indice su `fiscal.vat_number` | — |
| **B15-03** | Stessa persona può rappresentare più org con P.IVA diverse | `create_agency` L78–84 | **ASSENTE** (bloccato al contrario) | `find_one({"owner_id": user["id"]})` → `agency_already_exists` | Conflitto diretto con decisione approvata; **non** proporre unique su `owner_id` |
| **B15-04** | Org con P.IVA diverse = clienti/abbonamenti/dati separati | `subscriptions` / `credit_wallets` keyed by `agency_id` (`billing/models.py`) | **PARZIALE** | Isolamento per `agency_id` sì; ma create multi-org dello stesso titolare bloccata | — |
| **B15-05** | Filiali stessa P.IVA = stesso cliente, abbonamento/plafond condivisi | `AgencyGroup` + `group_id` (`groups.py`, `agency.py`) | **ASSENTE** | Group non ha VAT; ogni branch ha `fiscal` e subscription propri; `credits_mode` group/branch non equivale a “stesso cliente fiscale” | Matrioska ≠ cliente P.IVA |
| **B15-06** | Seconda persona con P.IVA già presente ≠ accesso automatico | create + invites | **PARZIALE** | Nessun auto-join su VAT; ma può creare **seconda** agency con stessa VAT | Manca flusso “richiesta accesso + verifica poteri” |
| **B15-07** | Accesso richiede verifica poteri + autorizzazione legittimati | invites / nessun claim-by-VAT | **PARZIALE** | Invito è il meccanismo di accesso; nessun flusso “claim P.IVA esistente” | — |
| **B15-08** | Unicità P.IVA anche a livello DB | `ensure_indexes` | **ASSENTE** | Solo slug unique | Normalizzazione `_norm_vat` solo in KYC (`kyc_auto_activate.py`), non a persistenza |
| **B15-09** | Una sola identità personale (email) | `users.email` unique index; `UserInDB` | **IMPLEMENTATO** | `create_index([("email", 1)], unique=True)` | — |
| **B15-10** | Stessa identità associabile a più organizzazioni | `agency_ids[]`, `_attach_user_to_agency`, accept-invite `$addToSet` | **IMPLEMENTATO** | Membership multipla funziona | Ruolo **non** per-org (vedi B15-12) |
| **B15-11** | Ogni associazione ha ruolo/autorizzazioni indipendenti | `users.role` singolo; Cap.13 | **ASSENTE** | Un solo `role` globale; accept upgrade solo se `role=="client"` | Admin in org A resta admin anche in org B se invitati come agent |
| **B15-12** | Org mantengono dati/permessi separati | tenant `active_agency_id` (D-106) | **PARZIALE** | Dati tenant sì; permessi via ruolo globale | — |
| **B15-13** | Accesso 2ª org non automatico da sola identità | invites | **IMPLEMENTATO** | Serve invite (o create come owner, limitato) | — |
| **B15-14** | Switch org: verifica appartenenza | `auth.set_active_agency` | **IMPLEMENTATO** | `agency_id not in agency_ids` → 403 | — |
| **B15-15** | Switch: ri-verifica ruolo/autorizzazioni | `set_active_agency` + `require_roles` | **ASSENTE** | Switch aggiorna solo `active_agency_id`; ruolo non ricalcolato | — |
| **B15-16** | Switch: sostituisce contesto, no permessi residui | FE `AgencyShell.switchAgency` → reload; BE `get_current_user` rilegge DB | **PARZIALE** | Reload + SoT DB buoni per dati; ruolo globale resta | JWT porta `role` ma guard usa DB |
| **B15-17** | Switch: impedisce accessi residui dati org precedente | tenant helpers + middleware | **PARZIALE** | Nuove request usano nuova active; in-flight pre-reload possibili | Alcuni endpoint controllano `agency_ids` (membership) non solo active |
| **B15-18** | Switch: evento nel registro comune B12 | `set_active_agency` | **ASSENTE** | Solo update Mongo; no audit strutturato | `logger` ≠ audit |
| **B15-19** | Ops Attiva non riattiva org già attiva; no side-effect | `founder_ops.ops_activate_agency` | **ASSENTE** | Nessun early-return se `activation_status=="active"`; `wipe_crm: bool = True` prima dello status set | **P0 wipe** |
| **B15-20** | Seconda attivazione rifiutata, no wipe/CRM/abbonamento | stesso + `wipe_agency_crm_data` | **ASSENTE** | Wipe può girare anche su org già active; grant_plan può rieseguire | Esiste anche `POST /wipe-agency-crm` separato senza gate “straordinario” |
| **B15-21** | Auto-Attiva KYC non riattiva se non pending | `maybe_auto_activate_from_kyc` | **IMPLEMENTATO** | Skip se `st != "pending"`; skip se `kyc_auto_activate_at` | Path Ops ≠ path auto |
| **B15-22** | Invito personale email + link verifica possesso | `invites.create_invite` / `accept_invite` | **PARZIALE** | Token email; accept non risetta password esistente (D-100) | Email verify flag non settato |
| **B15-23** | Token valido, non scaduto, monouso | verify + accept | **PARZIALE** | Expiry 7g, status pending→accepted/revoked; **non atomico** | Race: due accept paralleli |
| **B15-24** | Email verificata = email invito | accept usa `invite["email"]` | **IMPLEMENTATO** | Nessun override email da payload | — |
| **B15-25** | Accept → `email_verified=true` | `accept_invite` | **ASSENTE** | Nessun `$set` `email_verified` | Nuovo user: default `False` in `UserInDB` |
| **B15-26** | Accept registra sessione + refresh | accept L364–369 | **ASSENTE** (refresh) | Setta cookie access+refresh; **manca** `store_refresh(refresh)` | Refresh post-invito fallisce a validazione jti |
| **B15-27** | Account esistente mantiene password | accept L275–290 | **IMPLEMENTATO** | Commento D-100 + no overwrite hash | — |
| **B15-28** | Accept atomico sotto concorrenza | accept L248–334 | **ASSENTE** | `find` pending → mutate user → `update status`; no `find_one_and_update` condizionale | — |
| **B15-29** | Quote piano rispettate | create_invite max_agents | **IMPLEMENTATO** | members+pending vs plan | Wipe Attiva cancella anche invites |
| **B15-30** | B2C: verifica email dedicata | `cloud_auth.cloud_register`; commento verify-email | **ASSENTE** | `email_verified=False`; **nessun** route `/auth/verify-email` nel repo | Valuator gate già richiede verified |
| **B15-31** | Google → email_verified | `google_auth.py` | **IMPLEMENTATO** | Setta `email_verified: True` | Asimmetria password vs Google |
| **B15-32** | Eventi B12 (create org, VAT dup, invite, switch, Attiva, email verify, Ops) | consent_events, mls_events, logger | **ASSENTE** (registro comune account/security) | Solo `consent_events` su register; Attiva/invite/switch = `logger.info` | Allineato a B12 confermato: da aggiungere sul registro unico, riusando trail settoriali dove esistono |

**Normalizzazione / esteri / senza P.IVA (osservazione, senza nuove regole):**  
- FE: `validateItalianVat` / `normalizeVat` (solo IT 11 cifre).  
- BE create: obbligo presenza stringa, **nessuna** normalizzazione/checksum.  
- KYC: `_norm_vat` strip non-digit.  
- Nessun percorso esplicito P.IVA estera o soggetto senza P.IVA (D-162 impone campi fiscali).  
**Stato: NON VERIFICABILE / fuori scope decisionale attuale** oltre a “oggi è IT-centrico e non normalizzato a DB”.

---

## C. Problemi e rischi

### P0
1. **Ri-Attiva Ops con wipe di default su org già attiva** — `ActivateAgencyBody.wipe_crm=True`; `ops_activate_agency` non rifiuta se già `active`; chiama `wipe_agency_crm_data` (delete_many su tutte le collection con `agency_id`, inclusi properties/clients/invites).  
2. **Endpoint dedicato wipe** `POST .../wipe-agency-crm` — stesso wipe senza procedura straordinaria/tracciata B12.

### P1
3. **Unicità P.IVA assente** (app + DB) → due clienti OMNIA stessa P.IVA.  
4. **Blocco `owner_id` one-agency** → impedisce titolare multi-org con P.IVA diverse (contrario alla decisione).  
5. **Accept invite senza `store_refresh`** → sessione fragile.  
6. **Accept senza `email_verified=true`**.  
7. **Accept non atomico** → duplicazioni/membership inconsistenti sotto race.  
8. **Ruolo globale non per-org** → dopo invite/switch, privilegi dell’org A possono valere sull’org B.  
9. **Verifica email B2C assente** mentre feature gated su `email_verified`.  
10. **Nessun audit B12** su eventi B15 elencati.

### P2
11. Filiali stessa P.IVA ≠ cliente unico / abbonamento condiviso.  
12. Nessun flusso “P.IVA già presente → richiesta accesso con verifica poteri”.  
13. PATCH fiscal (`update_my_agency`) può cambiare VAT senza check unicità.  
14. Formati VAT non normalizzati a persistenza (`IT012…` vs `012…`).  
15. Test E2E/concurrency mancanti (vedi F).

### P3
16. Cap.19 manuale ancora dichiara VAT opzionale/senza unicità (diverge da D-162 + decisioni B15).  
17. Commento in `cloud_auth` che rimanda a verify-email “if present” (debt documentale).

---

## D. Dipendenze

```
[P0 guard Attiva / wipe] ── indipendente; fare prima (perdita dati)

[Normalizzazione VAT] ──► [Indice unique VAT] ──► [Check create + PATCH]
        │
        └──► [Modello “cliente commerciale” vs agency/filiale]
                    │
                    ├──► [Rimuovere/rilassare blocco owner_id] (dopo unique VAT)
                    └──► [Policy filiali stessa VAT / group billing] (da decidere mapping)

[Ruolo per-org o membership.role] ──► [Switch ricalcola auth] ──► [Audit switch B12]

[Accept: atomic + email_verified + store_refresh] ── indipendente ma prima dei test invite

[B2C verify-email flow] ──► [non rimuovere gate valuator]

[Registro B12 unico] ── dopo/in parallelo agli hook eventi (non blocca P0 wipe)
```

---

## E. Piano di intervento (solo elenco — **non implementare**)

1. **P0** — Guard idempotente Ops Attiva: se già `active` → reject, zero wipe/grant/email side-effect. Default `wipe_crm=False` su Attiva normale; wipe solo procedura Ops straordinaria esplicita + audit.  
2. **P0** — Soft-lock / conferma su `wipe-agency-crm`.  
3. **P1** — Normalizzare VAT a scrittura; unique index su VAT normalizzata (sparse se servono legacy null); check applicativo create+PATCH.  
4. **P1** — Rimuovere il blocco “un owner = un’agency” **dopo** unique VAT (consentire multi-org stesso user, P.IVA diverse). **Non** unique su `owner_id`.  
5. **P1** — Accept invite: `find_one_and_update` status pending→accepted; `email_verified=True`; `store_refresh`; cookie allineati al login.  
6. **P1** — Modello ruolo per membership (o tabella equivalenti) + enforce su switch/`require_roles`.  
7. **P1** — Flusso verify-email B2C (token monouso, update flag, resend).  
8. **P2** — Policy filiali stessa P.IVA / sharing subscription (mapping su group o cliente commerciale).  
9. **P2** — Flusso “P.IVA esistente → richiesta accesso” (no auto-join).  
10. **P2** — Hook eventi B12 (create, VAT conflict, invite accept/reject, switch, Attiva/reject, email verify, Ops straordinario).

---

## F. Test di accettazione (da scrivere dopo autorizzazione)

| Area | Test attesi |
|---|---|
| VAT | Create 2ª agency stessa VAT → reject; formati `IT`/`spazi` collidono; PATCH VAT duplicata → reject; concurrent create stessa VAT → una sola vince |
| Multi-org persona | Stesso user crea 2 org P.IVA diverse → OK; isolamento dati tra le due |
| Switch | Membership check; dopo switch API non legge dati org A; ruolo org B applicato; evento audit presente |
| Attiva | 2ª Attiva su already-active → 4xx, CRM invariato, subscription invariata; wipe solo path straordinario |
| Invite | Doppia accept sequenziale/parallela → una OK; `email_verified`; refresh jti valido; password esistente intatta; quota piano |
| B2C email | Register → link → verify → flag true; reuse token → fail; valuator con unverified → 403 resta |
| Audit | Ogni evento B15-32 scrive attore/soggetto/ts/operazione/esito |

**Nota:** non eseguire test distruttivi su dati reali/produzione.

---

## G. Compatibilità

| Area | Impatto |
|---|---|
| Multi-tenant D-106 | Switch/active_agency **compatibile**; rafforzare, non sostituire |
| Matrioska groups D-041/D-047 | Group ≠ cliente P.IVA; unificare policy filiali richiede decisione mapping, non rewrite group da zero |
| Piani / Stripe | Subscription per `agency_id`; sharing plafond stessa P.IVA **non** esiste — rischio doppia fatturazione stessa P.IVA oggi |
| MLS | Invariato; non introdurre share fascicolo |
| Ruoli B11 / Cap.13 | Conflitto: Cap.13 assume un ruolo; decisioni B15 chiedono ruolo per associazione |
| Sessioni B13 | Gap invite→refresh; resto JWT+jti ok |
| Area A | Nessun conflitto diretto |
| B12 | Eventi B15 da agganciare al registro unico già impostato |
| D-152/162/163 | Auto-Attiva già idempotente su pending; **Ops Attiva no** — allineare Ops alla stessa disciplina |

---

## H. Riepilogo finale

**Già funzionante**
- Email utente unica; membership multipla `agency_ids`; switch con check membership + reload FE; tenant su `active_agency_id`.
- Inviti: token, expiry 7g, revoke, refresh pending, quote piano, no overwrite password, email presa dall’invito.
- Onboarding B2B: fiscal obbligatori (D-162), KYC+pay → auto-Attiva con skip se non pending (D-163).
- Google setta `email_verified`; gate valuator rispetta il flag.
- Billing isolato per agency_id (quando le org sono separate).

**Da completare**
- Unicità P.IVA (app+DB+normalizzazione); multi-ownership con P.IVA diverse; ruolo per-org; verify-email B2C; audit B12 eventi B15; accept invite (`store_refresh` + `email_verified` + atomicità).

**Da correggere**
- Idempotenza Ops Attiva + default wipe; blocco `owner_id` one-agency (contrario alle decisioni); race accept/create.

**Da decidere** (senza inventare regole in implementazione)
- Entità “cliente commerciale” vs `agencies` (oggi coincidenti).
- Mapping filiali stessa P.IVA → un cliente / un abbonamento (group? campo shared? merge?).
- Forma del ruolo per-org (campo su membership vs collection).
- P.IVA estere / soggetti senza P.IVA (oggi IT-only di fatto).

**Da verifica legale/operativa**
- Procedura straordinaria wipe/riattivazione (chi autorizza, dual control, retention).
- Verifica poteri per accesso a org con P.IVA già intestata (documenti, chi firma).
- Implicazioni Stripe Customer unico per P.IVA vs N subscription per filiale.

---

**Fermato qui.** Nessun commit, PR, edit o implementazione.  
Quando vuoi, rivediamo insieme criticità e priorità; l’implementazione parte solo con la frase esatta:  
`OMNIA — AUTORIZZAZIONE ESPLICITA ALL'IMPLEMENTAZIONE`
