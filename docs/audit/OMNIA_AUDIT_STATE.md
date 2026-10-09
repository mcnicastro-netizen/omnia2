# OMNIA — MASTER AUDIT STATE

**Purpose:** stato operativo compatto dell'audit logico, architetturale e funzionale di OMNIA.

**Usage rule:** questo documento è la fonte di continuità dell'audit.
Prima di analizzare un nuovo punto, leggere questo file. Non riaprire decisioni già fissate salvo nuove evidenze. Non inventare informazioni mancanti.

**Current status:** P1–P24 **chiusi** · programma **APPROVATO** (**D-115**) · **«vai» O0 ∥ O1 in esecuzione**. Listino fermo. SoT: questo file.

**Next:** **D-118 Audit Portale** — Onde **A–G GREEN** (9 Ott) · Stripe test · OpenAPI D-116 · aperti P-021/024/026/032–036 · prossimo **Onda H** GDPR+AI Act. SoT: `OMNIA_PORTALE_AUDIT_PROGRAM.md` + `portale-finding.md`. Poi: O3b restore → **A-037** → self-serve. O6 CONDITIONAL. **no self-serve finché O6 ≠ PASS**. §23 Priorità **CLOSED**.

---

# 1. PRINCIPI DELL'AUDIT

L'audit valuta OMNIA come SaaS commerciale reale, con:

* dati reali di agenzie e clienti;
* utenti multipli;
* media e documenti;
* costi infrastrutturali;
* sicurezza e isolamento tenant;
* backup e restore;
* scalabilità;
* affidabilità operativa;
* UX/demo;
* coerenza tra prodotto, tecnica e modello commerciale.

Non confondere:

* problema reale;
* rischio potenziale;
* decisione di prodotto;
* miglioramento opzionale;
* preferenza architetturale.

Non introdurre fix durante l'audit salvo richiesta esplicita.

**Metodologia P24 (congelata):** la classificazione del debito **non** modifica severità, listino o priorità già congelate; non riapre P1–P23. Eventuali implementazioni solo al «vai». §23 Priorità resta CLOSED in audit.

---

# 2. ARCHITETTURA ATTUALE — CONTEXT MINIMO

* Backend: FastAPI monolitico.
* Frontend: React CRA.
* DB: MongoDB/Motor.
* Storage applicativo attuale: filesystem locale `.media`.
* Emergent object storage: legacy/non principale.
* S3/R2: target/documentazione, non implementazione applicativa attuale.
* APScheduler in-process.
* Attualmente considerata una sola replica per i job automatici.
* Auth: JWT cookie access + refresh, Google, MFA; API key `omk_live` per Track B.
* Multi-tenancy principalmente tramite `agency_id` / TenantContext / tenant guard.
* Ruoli: super_admin, agency_admin, agent, client, student, group_admin, branch_admin, branch_agent.
* External services: Stripe, Resend, Gemini, fal.ai, Nominatim, ANNCSU, Tavily, OpenAPI.it, Google OAuth, Web Push, Sentry/webhook, ecc.
* Produzione API definitiva non ancora fissata nell'analisi iniziale.

---

# 3. MODELLO DI DOMINIO — DECISIONI/CONTESTO

OMNIA comprende principalmente:

* ImmoWeb B2B CRM;
* ImmoCloud B2C;
* API Track B;
* Academy fuori dallo scope principale corrente.

Concetto fondamentale:

> **Client = chi è la persona.**
> **Request = cosa sta cercando / esigenza aperta.**

L'agenzia è il principale confine tenant B2B.
B2B e B2C condividono il DB ma hanno confini applicativi differenti.

---

# 4. DECISIONI FISSATE

## D-094 — Lifecycle/proiezioni (rafforzato P22)

Gli elementi cestinati non devono essere considerati operativi dalle proiezioni esterne.
Da rispettare in:

* feed;
* sync;
* matching;
* smart-clients / proiezioni correlate;
* pubblicazioni;
* website/MLS;
* job correlati.

`status` commerciale e lifecycle/trash sono concetti distinti.

**Invariante (P22 / K-EC-01):** il filtro trash è proprietà del **dominio operativo**, non del chiamante.
Default = **non-trashed**; accesso al trash solo via **opt-in esplicito** e percorso autorizzato.
Applicazione **uniforme pre-GTM** (non basta il feed già filtrato).

---

## D-095 — Media sensibili / Fascicolo

Il media endpoint pubblico non può essere il modello di autorizzazione per documenti sensibili.

* Listing photos pubbliche: possibile.
* Fascicolo/modulistica/documenti sensibili: devono avere controllo AuthZ o meccanismo equivalente.
* Il fatto che un path sia difficile da conoscere non è una misura di sicurezza sufficiente.

**Vincolo:** protezione AuthZ fascicolo prima del redesign definitivo del backup.

---

## D-096 — Restore

Restore commerciale = **singola agenzia via supporto**.

Modello:

> backup globale → estrazione/ripristino della singola agenzia.

Restore dell'intera piattaforma = procedura interna di emergenza.

Il restore deve essere **testabile** e riportare coerentemente almeno:

* immobili;
* clienti;
* richieste;
* attività;
* documenti;
* media.

Backup e Restore devono essere progettati insieme.

---

## D-097 — Backup vs Cestino

"Elimina per sempre" significa:

* fuori dall'area operativa;
* non recuperabile dall'utente tramite Cestino.

Il supporto può eventualmente valutare un recupero da backup valido, ma **non è garantito**.
Gli elementi nel Cestino possono restare nei backup fino alla scadenza della retention del backup.

---

## D-098 — Retention

### Orphan

Deve esistere un percorso verso la cancellazione definitiva dei file non più referenziati.
Il momento esatto della cancellazione sarà deciso insieme al design finale di backup/retention.

### Chiusura agenzia V1

Procedura controllata:

* account off;
* dati non operativi;
* wipe da definire.

Nessun auto-wipe aggressivo per ora.
Storage + backup + retention devono essere progettati come una catena unica.

---

## D-099 — GDPR / Privacy

Founders:

* DSAR assistito via email;
* erase;
* DPA;
* self-service export in roadmap, non blocco immediato.

Il pacchetto non è ancora considerato completamente "GDPR-ready".
Il finding relativo al fascicolo è specifico: non significa che "tutto OMNIA è esposto".

---

## D-100 — Invite (decisione **trasversale**)

Invite verso utente già registrato:

> collegamento dell'utente all'agenzia / accettazione invito.

**Mai sovrascrivere la password esistente.**

Questo è **fix-needed**, in attesa di autorizzazione esplicita a intervenire.
**Trasversale** (P18 AF / P19 EH / P21 CT / P22 EC): un solo contratto invite — evitare fix indipendenti sui sintomi.

---

## D-101 — Job automatici / replica

Fino a nuova decisione:

> **una sola istanza responsabile dei job automatici.**

Non introdurre ora lock multi-pod complessi.
Quando OMNIA crescerà / passerà a più repliche, valutare anti-duplicazione condiviso / worker dedicato.

---

## D-102 — Purge + orphan cleanup automatico

Purge cestino + percorso cleanup blob/orphan devono entrare nel ciclo automatico APScheduler.
Non aspettare il worker futuro. Allinea D-098 / D-095.

---

## D-103 — No worker dedicato ora

Nessun worker dedicato solo per chiudere i finding job.
Eventuale anti-duplicato minimo stesso-giorno OK; worker quando il deployment lo richiede.

---

## D-104 — GTM Demo Readiness

Prima dell'invio delle circa 5.000 email GTM deve essere eseguito un checkpoint:

**GTM-01 / A-036 — Demo Readiness / primo afflusso commerciale**

Verificare almeno:

* 2 / 50 / 200 richieste demo;
* circa 20 utenti contemporanei;
* percorso demo completo;
* stabilità delle funzioni mostrate ai prospect.

**Confidence gate (P20 / K-SC-01):** smoke load dedicato leggero ~20 concurrent — upload + read/serve media + match + combinazione; errori/latenza/memoria; ambiente rappresentativo. Stress ladder resta baseline. **Non** è gate P0–P3.

**Trigger AD-01 (P23 / K-AD-02):** FS + 1 replica = baseline GTM deliberata; anticipare object storage/CDN solo se lo **smoke media** fallisce (I/O, RAM, latenza, errori concorrenti, consistenza) — non “1 replica ⇒ object storage”.

**Requisiti minimi già collegati a GTM-01:** AF-05/EH-03 upload osservabile; EH-04 empty≠error; **SC-08/AF-04** paginazione FE properties.

Non significa dimensionare OMNIA per 5.000 utenti contemporanei.

**Vincolo hard:** checkpoint prima delle ~5.000 email.

---

## D-105 — Backup health minimo

Founder Ops deve poter mostrare almeno:

* ultimo backup OK / PARTIAL / FAILED;
* data/ora;
* alert quando necessario (`ops_alerts` / `ERROR_ALERT_*`).

Serve anche sapere l’ultimo run valido dei job (`last_run`).
Prometheus / OTel / structured logging avanzato possono aspettare.
Codice ⏳ — post-audit / «vai».

---

## D-106 — `active_agency_id` SoT sessione (rafforzato P22)

* `active_agency_id` = agency operativa corrente (source of truth).
* `agency_ids` = membership / agency disponibili.
* Flusso: `active_agency_id → /agencies/me* → FE`.
* **Non** nascondere lo switcher per evitare il drift.
* **Nessun fallback semantico a `agency_ids[0]`** quando il contesto richiede l’agency attiva (**EC-01**).
* Se `active_agency_id` manca o non è valida → **stato di errore**, non scelta arbitraria della prima agency.
Codice ⏳ — post-audit / «vai».


## D-107 — Contratto errori API: code stabile + i18n FE

* BE restituisce **error code** strutturato stabile (+ `detail` diagnostico/fallback).
* FE decide la localizzazione / UX.
* Non usare un `detail` umano come unico contratto (cambio wording non deve rompere i18n).
* Feedback utente obbligatorio quando il fallimento **altera il significato** dell’azione; toast = possibile implementazione, non il contratto.
Codice ⏳ — post-audit / «vai».


## D-108 — Scheduling: un solo owner di esecuzione

* Un solo meccanismo è **owner** dell’esecuzione dei job automatici (APScheduler in single-replica, **D-101**).
* HTTP cron / trigger manuale può al massimo essere **trigger controllato / fallback**, non seconda autorità di scheduling parallela.
* `max_instances=1` aiuta ma **non** sostituisce la definizione di ownership (**SC-10**).
Codice ⏳ — post-audit / «vai».


## D-109 — Pricing applicativo: una sola fonte autorevole

* **`GET /billing/plans` = source of truth** del pricing applicativo corrente.
* Landing/marketing: **allineata dinamicamente** al contratto corrente, **oppure ritirata/nascosta** finché non può esserlo.
* Eventuali prezzi legacy (es. Founders-50) solo se **nominati esplicitamente come legacy/founder offer** — mai come terza interpretazione nascosta del listino.
* Principio: una sola fonte autorevole per il prezzo corrente; legacy esplicito.
Codice/copy ⏳ — post-audit / «vai». **Listino fermo** (nessuna revisione €/quote ora).


## D-110 — Demo mode esplicito · `localStorage` ≠ entitlement

* `localStorage` (o storage client) **non** è autorità di entitlement / “utente ha pagato”.
* Demo mode accettabile solo come **modo applicativo esplicito** (presentazione), non come simulazione di piano reale via storage client.
* Coerente con una sola source of truth per lo stato semantico (come **D-106** agency, **D-107** errori).
* `Stripe off → 503` può restare legittimo se il billing non è disponibile.
* Conferma P22 (**EC-07**): il client non trasforma semanticamente “Stripe off / entitlement assente” in “piano attivo”.
Codice ⏳ — post-audit / «vai».


## D-111 — Cestino = stato non operativo (freeze)

* Entrando in `TRASHED`: non nuovi match/sync; non nuove notifiche automatiche; **blocco nuove operazioni** che producono side effect; dati/storico **preservati** (non cancellati).
* Richieste già esistenti: transizione esplicita (es. `active → frozen`); **non** cascade distruttivo.
* Restore client: storico disponibile; **non** riattivazione automatica delle richieste (coerente **D-094**).
* Job già in corso: regola di comportamento esplicita (non ambigua).
* Distinzione: **visibilità** ≠ **operatività**. Escludere dai soli job non basta se l’utente può ancora creare/modificare.
Codice ⏳ — post-audit / «vai».


## D-112 — Seed demo: idempotente e deterministico

* Identità demo → agency demo **prevista**, senza dipendere dall’ordine esistente delle agency.
* **Niente** logica “se manca X, usa la prima agency” (stesso errore concettuale di **EC-01** / **D-106**).
* Seed ripetibile: stessi input → stesso grafo membership demo.
Codice ⏳ — post-audit / «vai».


## D-113 — Restore manuale testabile pre-GTM (non piattaforma DR)

* Pre-GTM: **procedura manuale, documentata e ripetibile** di restore su ambiente **non-prod**, con esito verificabile.
* Non richiede automatizzazione / piattaforma disaster recovery.
* **D-105** risponde a “il processo bak funziona?”; il restore test risponde a “sappiamo recuperare?”.
* **Non** è ancora capability commerciale di “restore garantito” finché non esistono tempi/limiti operativi definiti.
* Linguaggio onesto: bak esistente ≠ bak verificato ≠ restore disponibile ≠ restore testato (**P21 CT-03**).
Codice/docs ops ⏳ — post-audit / «vai».


## D-114 — Sostenibilità bak/media = priorità pre-attivazione

* **Non si può prescindere** dal modello bak/media: ne va della **sostenibilità economica**.
* Full-copy giornaliero × retention (~32×) **non** resta “vincolo accettato in silenzio”.
* **O0 (K-PA-01):** numeri + **design vincolante** (retention, scope, full/incrementale, restore agency-first, costo, “questo implementeremo”) — **non** refactoring obbligatorio in O0.
* **Listino fermo** finché esistono i numeri — poi eventuale revisione commerciale.
* Distinto da: FS locale come backend fisico (può restare) vs modello economico del volume (da chiudere).
Design/ops ⏳ — al «vai» O0; codice bak nuovo = fase successiva.


## D-115 — Programma pre-attivazione · no self-serve prima di O6

* Programma **O0 ∥ O1 → O2 → O3 → O4 → O5 → O6** approvato (**K-PA-03**).
* O2 prima di O3 (regole trash/freeze → poi test recupero).
* Durante le onde: **provisioning assistito dichiarato** (**K-PA-02**).
* **Nessun pagamento self-serve finché O6 non è PASS.**
* SoT: `docs/audit/OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md`.
Codice ⏳ — attende «vai» sulle onde.

---

# 5. BACKUP — STATO E PROBLEMA ECONOMICO

Backup attuale:

* giornaliero;
* APScheduler 03:15;
* disponibile anche trigger HTTP/super_admin;
* full `copytree`;
* retention circa 30 giorni;
* nessun modello incrementale;
* backup globale;
* dump Mongo attualmente parziale;
* restore tool/procedura applicativa non ancora implementata.

Problema fondamentale:

> full copy giornaliero × ~30 giorni può moltiplicare enormemente lo storage.

Ordine di grandezza attuale considerato:

* Starter 30 GB → ~930 GB backup;
* Pro 100 GB → ~3,1 TB;
* Agency 300 GB → ~9,3 TB;
* circa 32× live+backup nel modello worst-case considerato.

**Conclusione:** il costo €0,04/GB all-in NON è confermato.
Non modificare ancora il listino.

---

# 6. STORAGE / COMMERCIAL MODEL

Piani attuali:

* Starter €49;
* Pro €99;
* Agency €299.

Quota storage considerata:

* Starter 30 GB;
* Pro 100 GB;
* Agency 300 GB;
* addon +100 GB / €15.

"Unlimited properties" NON significa "unlimited storage".
Video: nessun secondo tetto specifico deciso.
Il principale limite commerciale attuale è la quota storage.

### Decisione importante

Non modificare ancora:

* prezzi;
* quote;
* limite video.

Prima:

> Backup + Restore → retention → costo reale → eventuale revisione commerciale.

---

# 7. MEDIA / FILE

Problemi principali individuati:

* endpoint `/api/media/...` pubblico;
* documenti sensibili possono essere raggiungibili conoscendo il path;
* `delete_object` esiste ma non ha chiamanti effettivi;
* cancellazione DB non implica necessariamente cancellazione blob;
* trash purge non pulisce necessariamente i blob;
* possibili orphan;
* storage locale;
* backup dei media parte del problema economico.

Cluster fondamentale:

> **Mongo record ↔ blob storage devono avere lifecycle coerente.**

---

# 8. MULTI-TENANCY / SECURITY

Isolamento CRM generalmente presente ma **non end-to-end perfetto**.

Problemi già individuati:

* endpoint media;
* alcune collection fuori tenant guard;
* query potenzialmente solo per ID;
* uso di `agency_ids[0]` in alcuni percorsi;
* backup globale;
* trusted/super_admin paths.

AuthN generalmente solida per la fase attuale.

AuthZ a strati:

* ruolo;
* membership;
* agency;
* ownership dove applicabile.

Finding importanti già individuati:

* fascicolo/IDOR;
* invite overwrite password;
* refresh token non ruotato;
* password reset non revoca necessariamente sessioni esistenti;
* `get_current_user` non sempre ricontrolla `is_active`;
* agency selection tramite `agency_ids[0]`;
* alcuni admin possono avere capacità più ampie del necessario.

---

# 9. LIFECYCLE / TRASH

Property/client:

> soft delete → trash ~30 giorni → restore/purge.

Request:

> open → matched → altri stati → archived.

Activity:

> open → done/cancelled; delete hard.

Problemi:

* property trashed può ancora comparire in alcuni feed/sync;
* client trash non gestisce automaticamente richieste collegate;
* documenti possono essere eliminati da Mongo ma lasciare blob;
* requests non hanno necessariamente stesso lifecycle del client;
* agency offboarding/wipe non definito.

Decisione provvisoria:

> non fare cascade distruttivo delle richieste quando si cestina un client; preservare la storia e impedire che rimanga operativa in modo incoerente.

---

# 10. JOB / ASYNC

Sistema attuale:

* APScheduler;
* cron HTTP super_admin;
* fire-and-forget in alcuni percorsi;
* nessun worker dedicato;
* nessun ledger generale dei job;
* nessuna DLQ/checkpoint generale.

Finding principali:

* sync può ignorare trash;
* matching può ignorare trash;
* purge trash non è normalmente schedulato da APScheduler;
* blob cleanup non automatizzato;
* matching/email può avere problema di crash tra invio e dedup;
* backup/sync/match non hanno run ledger completo;
* overlap HTTP cron ↔ scheduler;
* cron protetto tramite JWT super_admin.

### Decisione operativa

Per ora una sola replica.
Purge + blob cleanup devono diventare un processo automatico; non aspettare necessariamente il futuro worker.
Worker dedicato / lease distribuito: decisione futura, non ora.

---

# 11. OSSERVABILITÀ

Esistente:

* health/readiness;
* Sentry/webhook/email opzionali;
* `notify_error`;
* `ops_alerts`;
* Founder Ops;
* sync logs;
* MANIFEST;
* quota storage.

Mancanza importante:

> non esiste ancora un controllo operativo sufficiente che dica chiaramente se il backup è riuscito.

Decisione da mantenere:

### Backup health minimo

Founder Ops deve poter mostrare almeno:

* ultimo backup OK;
* ultimo backup PARTIAL;
* ultimo backup FAILED;
* data/ora;
* alert quando necessario.

Non serve ora una dashboard complessa.
Alert backup: preferire il sistema esistente `ops_alerts` / `ERROR_ALERT_*`.

Altro finding importante:

> scheduler/job può smettere di funzionare senza essere immediatamente evidente.

Serve almeno poter sapere quando è avvenuto l'ultimo run valido.
Prometheus/OTel/structured logging avanzato possono aspettare.

---

# 12. RACE CONDITIONS

Problemi individuati:

* edit/upload vs trash;
* backup doppio;
* Stripe webhook duplicato;
* invite;
* sync/matching vs trash.

Già buono:

* wallet credit charge atomico;
* restore vs purge trash ha un vincitore.

Tier:

### 🔴

Invite/password overwrite.

### 🟠

Backup/sync/trash overlap.

### 🟢

Wallet + restore/purge.

Non trattare ogni race finding come fix immediato.

---

# 13. GDPR / RETENTION — STATO

Account user erase esiste.
Alcuni consent sono presenti.

Mancano o sono incompleti:

* DSAR accesso/portabilità self-service;
* wipe cliente CRM;
* wipe agenzia;
* policy privacy/cookie completa;
* DPA/subprocessor mapping;
* coordinamento backup/orphan/audit con cancellazione.

Non definire ancora una retention definitiva dei blob orphan finché non è definito il modello Backup + Restore.

---

# 14. FINDING / CLUSTER DA NON PERDERE

I seguenti cluster sono ancora aperti e devono comparire nel riepilogo finale:

### Backup

B-01…B-14

### Restore

R-01…R-12

### Backup vs Cestino

BC-01…BC-05

### Retention

RET-01…RET-10

### GDPR / Privacy

G-01…G-12

### Race

RC-01…RC-14

### Job Async

JA-01…JA-07

### Observability

O-01…O-15 · **D-105** bak health

### API / Frontend

AF-01…AF-16

### Error handling

EH-01…EH-12 · **D-107** · P19 CHIUSO

### Scalabilità

SC-01…SC-15

### Coerenza prodotto/tecnologia

CT-01…CT-14 · **D-109** pricing SoT · **D-110** demo≠entitlement · **P21 CHIUSO**

### Casi limite

EC-01…EC-15 · **D-094**/ **D-106** rafforzati · **D-111** freeze · **D-112** seed · **P22 CHIUSO**

### Debito architetturale

AD-01…AD-16 · **D-113** restore manuale · **P23 CHIUSO**

### Non una lista infinita

NI-01…NI-12 · **P24 CHIUSO** · classificazione **congelata** (vedi §25 / § SoT ripago)

### Report finale

P25 A–K · ⏳ analisi Founder · §23 Priorità CLOSED

### Storage

C-01…C-15

### Lifecycle

L-01…L-13

### External projections

E-01…E-09

### Media

M-01…M-14

### Auth / Authorization

Finding P4 già identificati, in particolare:

* fascicolo/IDOR;
* invite;
* session lifecycle;
* active user;
* agency_ids[0];
* privilege boundaries.

Non assumere che tutti i finding abbiano stessa priorità.

---

# 15. DECISIONI ECONOMICHE NON ANCORA CHIUSE

NON confermare ancora:

* €0,04/GB;
* costo massimo per cliente;
* sostenibilità definitiva dei piani;
* quote storage definitive;
* modello backup definitivo.

Regola:

> **Backup + Restore + Retention → stima infrastrutturale → verifica sostenibilità → eventuale decisione commerciale.**

Problema riconosciuto:

> l'attuale full-copy giornaliero rende il modello potenzialmente non sostenibile per clienti media-heavy, soprattutto Agency.

Questo è un problema reale da risolvere, ma NON implica ancora che il modello commerciale sia sbagliato.

---

# 16. GTM — VINCOLO FUTURO

GTM previsto:

* email a circa 5.000 indirizzi, forse di più;
* richieste demo;
* risultato incerto: potrebbe essere 2, 50, 200+ demo.

Non dimensionare per 5.000 utenti contemporanei.

Prima del lancio:

**GTM-01 / D-104 / A-036**

deve verificare:

* percorso demo;
* performance;
* errori;
* upload;
* tenant isolation;
* dati demo;
* accessi contemporanei;
* gestione lead;
* capacità operativa del team.

---

# 17. DIPENDENZE IMPORTANTI

Queste dipendenze NON devono essere perse:

```text
Fascicolo AuthZ
      ↓
Media/blob lifecycle
      ↓
Backup design
      ↓
Restore design
      ↓
Retention
      ↓
Costo reale
      ↓
Eventuale revisione storage/listino
```

Parallelamente:

```text
Osservabilità
      ↓
Backup health
      ↓
Restore testabile
      ↓
GTM Demo Readiness
      ↓
~5.000 email
```

E:

```text
1 replica
      ↓
job automatici APScheduler
      ↓
eventuale worker/lock distribuito solo quando necessario
```

---

# 18. REGOLE PER I PROSSIMI PUNTI

Per ogni nuovo punto:

1. usare questo file come contesto;
2. non riaprire decisioni già fissate senza nuova evidenza;
3. distinguere finding / decisione / rischio / preferenza;
4. non fare fix durante l'audit salvo richiesta;
5. non assegnare automaticamente P0–P3;
6. non modificare listino senza evidenza economica;
7. mantenere le dipendenze sopra;
8. aggiungere nuove decisioni con ID progressivo;
9. aggiungere nuovi finding senza cancellare quelli già aperti;
10. alla fine produrre un riepilogo unico:

* decisioni;
* finding;
* priorità;
* fix-needed;
* dipendenze;
* GTM readiness;
* piano pre-go-live;
* piano post-go-live.

---

# 19. P18 — API / FRONTEND (consegnato 30-Set · osservazioni Founder)

**Verdetto:** mount/routing demo coerenti; drift su invite (D-100), multi-agency `/me`, pagination, upload silenzioso, B2C URL raw, sessione B2B/B2C.
**Nessun nuovo P0–P3** da P18. Nessun fix finché «vai».

### Finding AF-*

| ID | Tipo | Problema |
|----|------|----------|
| AF-01 | fix-needed | Invite overwrite · tre stati da formalizzare (**D-100**) |
| AF-02 | rischio | `/api/media` pubblico — boundary da chiarire (**D-095**) |
| AF-03 | → **D-106** | Due fonti di verità agency: `agency_ids[0]` vs `active_agency_id` |
| AF-04 | debito demo | Properties senza paginazione UI → lista sembra completa |
| AF-05 | **GTM-01 min** | `pending→success/error` + retry (non P0 ora; requisito Demo Readiness) |
| AF-06 | drift | B2C config API duplicata (`REACT_APP_BACKEND_URL`) |
| AF-07 | doc/decisione | Sessione unica B2B/B2C — da documentare se deliberata |
| AF-08…AF-16 | oss./gap | Billing · error UX · perf · nav · versioning · CORS · a11y |

### Domande — RISOLTE / AFFINATE

1. **K-AF-01 → D-106**: `active_agency_id` = SoT; **non** nascondere switcher.
2. **K-AF-02**: contratto server prima (new / existing+auth / expired-consumed), poi FE; niente magia FE.

### Baseline P18 — **CHIUSO** (Founder 30-Set · nessun codice · no nuovi P0–P3)

* **D-106**: `active_agency_id` = SoT; switcher mantenuto.
* **K-AF-02**: contratto server prima, FE dopo; tre stati invite espliciti (**D-100**).
* **AF-02**: boundary media da definire esplicitamente (**D-095**).
* **AF-04**: debito demo / non-blocking.
* **AF-05**: requisito minimo **GTM-01** — `pending → success/error` + retry (non elevato a P0 ora).
* **AF-06**: unica astrazione API FE (anche B2C).
* **AF-07**: chiarire se sessione B2B/B2C condivisa è deliberata.
* **K-AF-01 / D-106** = priorità tra i fix FE/API post-«vai».

Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 18.

---

# 20. P19 — ERROR HANDLING — **CHIUSO** (Founder 30-Set · nessun codice · no nuovi P0–P3)

**Verdetto acquisito:** rete 500 ok; debito = swallow FE e soft-fail che mascherano fallimenti come risultati plausibili.

### Baseline P19

* **EH-03** → GTM-01 confermato (`pending→success/error`+retry; mai UI success prima della conferma upload).
* **EH-04** → `empty` ≠ `error`; **vietato** trasformare failure API in empty state (loading → success(data|empty) vs loading → error).
* **EH-05** → stato del job distinto dal livello di logging (completed / failed / retrying / partial); WARNING ≠ successo.
* **EH-06** → separare operazione da delivery: es. `invite_created=success` + `email_delivery=failed` (retry mail senza ricreare invite); stesso per match.
* **K-EH-01 → D-107**: BE `code` stabile + `detail` diagnostico; FE i18n.
* **K-EH-02**: feedback utente obbligatorio quando il fallimento altera il significato dell’azione; toast non necessariamente obbligatorio.
* Differiti: request-id / 422 / retry UX generale / geocode.
* **Nessun nuovo P0–P3. Nessun codice.**

Finding EH-01…EH-12 restano aperti nel registro. Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 19.

---

# 21. P20 — SCALABILITÀ — **CHIUSO** (Founder 30-Set · nessun codice · no nuovi P0–P3)

**Principio:** non confondere **capacità GTM** con **architettura target**.

### Baseline P20

* **SC-02/15** → accettabile per GTM se assunto esplicitamente; **non** horizontal-ready (coupling storage↔traffico↔API).
* **SC-03** → limite operativo da monitorare; **bak non scala automaticamente** col n. agenzie; “31×” non è soglia produzione da sola; worker (**D-103**) non è prerequisito GTM.
* **SC-04** → monitorare costo/frequenza match; **match costoso non deve diventare conseguenza accidentale di una GET** ordinaria (precompute non obbligatorio ora).
* **SC-08 / AF-04** → requisito **GTM-01** (API paginata + FE prima pagina = dataset incompleto).
* **SC-10 → D-108**: un solo owner dello scheduling; l’altro al massimo trigger/fallback.
* **K-SC-01** → smoke load dedicato ~20 concurrent (upload+media+match+combo) = **confidence gate GTM-01** (non gate P0–P3); stress ladder resta baseline.
* **K-SC-02** → soglia object storage+CDN su **capacità/traffico media** (due dimensioni), non solo n. agenzie; **separato** da worker (**D-103**).

Finding SC-01…SC-15 restano nel registro. Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 20.

---

# 22. P21 — COERENZA PRODOTTO/TECNOLOGIA — **CHIUSO** (Founder 30-Set · nessun codice · no nuovi P0–P3)

**Verdetto acquisito:** il rischio principale non è tecnico stretto, ma **contratto tra ciò che il prodotto dichiara e ciò che il sistema può fare**. Nessun nuovo P0–P3. Listino fermo. Nessun fix.

### Baseline P21

* **CT-01 / K-CT-01 → D-109**: `GET /billing/plans` = SoT pricing applicativo; landing allineata dinamicamente **oppure** ritirata/nascosta; Founders-50 solo se **esplicitamente legacy**.
* **CT-03**: distinguere **backup esistente** ≠ **backup verificato** ≠ **restore disponibile** ≠ **restore testato**. Marketing/UI/Ops non superano la capability reale (**D-096** / HAL onesto). Non inventare tool restore ora.
* **CT-06 → D-110**: demo mode sì come modo applicativo esplicito; `localStorage` **non** autorità di entitlement. Stripe off → 503 può restare legittimo.
* **CT-09**: **D-100** trattato come decisione **trasversale** (contratto invite unico) — non tre fix indipendenti su sintomi AF/EH/CT.
* **CT-11**: problema di **operatività** (non inconsistenza CRM) → **D-105**: Founder Ops rende osservabile bak health (chi scopre un bak fallito e come).
* **K-CT-02**: hard enforcement BE di `max_properties`/`max_agents` **solo** se sono entitlement commerciali GTM realmente definiti; altrimenti non simulare il limite (storage **D-085** resta enforcement tecnico reale).
* **Nessun fix. Nessun nuovo P0–P3. Listino fermo.**

Finding CT-01…CT-14 restano nel registro. Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 21.

---


# 23. P22 — CASI LIMITE — **CHIUSO** (Founder 30-Set · nessun codice · no nuovi P0–P3)

**Verdetto acquisito:** i casi limite non rivelano nuovi problemi strutturali, ma punti in cui il dominio **non applica in modo uniforme** decisioni già prese. **D-094, D-100, D-106, D-110** convergono come invarianti anche negli edge case. Nessun nuovo P0–P3. Nessun fix.

### Baseline P22

* **EC-01 → D-106 rafforzato**: nessun fallback semantico a `agency_ids[0]`; `active_agency_id` assente/invalida = **errore**.
* **EC-02 / K-EC-01 → D-094 rafforzato**: filtro trash **uniforme pre-GTM** su match/sync/smart; proprietà del dominio (default non-trashed; trash solo opt-in autorizzato).
* **EC-03 / K-EC-02 → D-111**: Cestino = **stato non operativo**; freeze nuove operazioni; preserva dati/storico; richieste `active → frozen` (no cancellazione).
* **EC-05**: **D-100** invariato — contratto invite unico; identità esistente intatta.
* **EC-07**: **D-110** invariato — demo esplicita sì; client non altera entitlement server-side.
* **EC-13 → D-112**: seed demo **idempotente e deterministico** (identità → agency prevista; no “prima agency”).
* **Nessun fix. Nessun nuovo P0–P3. Listino fermo.**

Finding EC-01…EC-15 restano nel registro. Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 22.

---

# 24. P23 — DEBITO ARCHITETTURALE — **CHIUSO** (Founder 30-Set · nessun codice · no nuovi P0–P3)

**Verdetto acquisito:** il debito non è “monolite = problema”, ma **quali assunzioni sono deliberate e quali rimaste incomplete**. Distinguere **debito da ripagare** vs **debito da accettare consapevolmente**. Nessun nuovo P0–P3. Nessun fix. Listino fermo.

### Baseline P23

* **AD-05**: correggere il **boundary di autorizzazione** fascicolo (storage fisico ≠ endpoint ≠ AuthZ ≠ associazione media↔fascicolo/agency). FS locale pre-GTM OK — **non** anticipare AD-01/object storage solo per questo.
* **AD-08/09/10**: **D-106 / D-100 / D-094·D-111** = invarianti di dominio. Implementare quando si toccano i percorsi relativi — non un grande “architecture cleanup” (evita di pagare due volte).
* **AD-12/13/14**: stesso problema — **lo stato dichiarato deve corrispondere allo stato reale** (**D-105**, **D-110**, **D-109** più importanti del refactor infra). Demo `localStorage` non deve diventare semantica di produzione.
* **K-AD-01 → D-113**: pre-GTM = **D-105 + linguaggio onesto + restore manuale testabile** (non-prod, documentato, ripetibile, esito verificabile). Non = piattaforma DR né “restore garantito” commerciale.
* **K-AD-02**: **FS + 1 replica = baseline GTM deliberata**; trigger misurabile per anticipare object storage/CDN = **fallimento smoke media** (confidence gate **K-SC-01** / GTM-01 — *non* “1 replica ⇒ object storage”). Coerente P20.
* **Pre-GTM da chiudere/garantire:** SoT agency · invite · trash · media AuthZ fascicolo · bak health · demo entitlement · pricing · restore manuale testabile.
* **Pre-GTM accettabile come vincolo dichiarato:** FS locale · single/limited replica · bak full · match on-read · no worker · no OTel · no object storage/CDN.
* **Nessun fix. Nessun nuovo P0–P3. Listino fermo.**

Finding AD-01…AD-16 restano nel registro. Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 23.

---

# 25. P24 — NON UNA LISTA INFINITA — **CHIUSO** (Founder 30-Set · nessun codice · no nuovi P0–P3)

**Verdetto acquisito:** P24 = **classificazione finale del debito**, non ricalcolo delle severità. Non riaprire continuamente la severità. Il report finale riporta i cluster NI e le decisioni già prese **senza** nuovi P0–P3. Quando arriverà il «vai», §23 può diventare operativo (cosa implementare e in quale sequenza) — distinto dall’audit.

### Baseline P24

* **K-NI-01**: report finale / GTM-01 ora; **§23 Priorità resta CLOSED** fino al «vai».
* **K-NI-02**: distinzione P23 **congelata** come SoT di ripago (sotto).
* **NI-08/09**: restano **potenziale** — non trasformare “oltre D-113” in “deve essere pre-GTM”.
* **NI-12**: OK **fase attuale / perimetro**, non certificazione eterna.
* **Metodologia:** la classificazione P24 **non** modifica severità, listino o priorità già congelate; eventuali implementazioni solo al «vai». Impedisce che P24 riapra retroattivamente P1–P23.
* **Nessun fix. Nessun nuovo P0–P3. Listino fermo.**

Finding NI-01…NI-12 restano nel registro. Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 24.

---

# 25bis. SoT RIPAGO — DISTINZIONE CONGELATA (P23/P24)

> **La classificazione P24 non modifica severità, listino o priorità già congelate; eventuali implementazioni vengono decise solo al «vai».**

### PRE-ATTIVAZIONE / DA CHIUDERE

*(Rinominato da “PRE-GTM”: priorità Founder = sicurezza dati · storage · anticrash · recupero — non corsa outreach.)*

* NI-01…NI-07
* Invarianti **D-094 / D-100 / D-106 / D-111**
* Fascicolo AuthZ (**D-095**)
* Pricing / demo (**D-109 / D-110**)
* Percorso anti-fallimento / Demo Readiness min (**D-104** · AF-05/EH-03 · EH-04 · SC-08/AF-04 · smoke ~20)
* Bak health (**D-105**) + restore manuale testabile (**D-113**)
* **Sostenibilità bak/media (**D-114**)** — non prescindibile: costo reale del modello storage+backup; design bak sostenibile (full-copy × retention **non** resta “vincolo silenzioso”). Listino **fermo** finché i numeri esistono (catena D-096).
* Correlati implementativi quando si toccano i percorsi: **D-107** · **D-108** · **D-112**

### PRE-ATTIVAZIONE / ACCETTATO COME VINCOLO

Baseline architetturale deliberata, purché superi i gate già definiti:

* filesystem locale `.media` **come backend fisico** (≠ sostenibilità economica del volume bak — quella è **D-114**)
* single / limited replica
* match on-read
* assenza worker
* assenza OTel
* assenza object storage/CDN **finché** smoke media / D-114 non impongono altrimenti

**Non più in “accettato silenzioso”:** bak full-copy illimitato come modello economico → **D-114** (da chiudere).

Trigger tecnico: fallimento **smoke media** (K-SC-01) → anticipare AD-01 — non “1 replica ⇒ object storage”.

### POTENZIALE

* NI-08 (restore **piattaforma**/DR oltre D-113) / NI-09 (orphan timing) — non blocker attivazione per default.
* Attenzione: la **sostenibilità economica** bak/media non è più qui — è **D-114** (da chiudere).

### POST-ATTIVAZIONE / RIPAGARE (roadmap)

* NI-08/09 quando raggiungono le condizioni definite (oltre quanto già coperto da D-113/D-114)
* NI-10 / NI-11 secondo roadmap
* Object storage/CDN / worker / OTel quando D-114 o smoke lo richiedono

**“Non fare ora” ≠ “non esiste”** — e non ogni elemento differito è un blocker.

**Nota Founder (30-Set):** non si può prescindere da bak/media — ne va della **sostenibilità economica**. Elevato a priorità pre-attivazione (**D-114**), non lasciato come debito “accettato”.

**Programma attuativo:** `docs/audit/OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md` — ✅ **APPROVATO** (**D-115** · K-PA-01…03). Gate: **no self-serve finché O6 ≠ PASS**.

---

# 26. P25 — REPORT FINALE (consegnato · ⏳ analisi Founder · master §25)

**Meta:** P1–P24 **CHIUSI** · classificazione P24 **congelata** · §23 Priorità **CLOSED** · nessun nuovo P0–P3 · listino fermo · nessun codice.

### A. Executive summary

* Monolite FastAPI + React + Mongo + FS `.media` + APScheduler 1-replica **adeguato alla fase**.
* Dominio: **Client ≠ Request**; soft-delete/Cestino; agency = confine B2B.
* Audit = **pochi drift ripetuti**, non cento bug: invite, SoT agency, trash, AuthZ fascicolo, pricing/demo, bak osservabile.
* **D-094…D-113** filtrano intenzionale vs accidentale; ripago pre-GTM = SoT §25bis.
* AuthN e tenant-guard CRM **OK fase**; AuthZ fascicolo e contratto invite **non**.
* Bak full-copy ×~30g → ~**32×** storage; €0,04/GB **non confermato**; listino **fermo**.
* **D-114**: sostenibilità bak/media = priorità pre-attivazione (non prescindibile).
* Restore = **D-105 + linguaggio onesto + D-113** — non DR commerciale.
* **GTM-01** obbligatorio prima delle ~5k email (smoke ~20, upload, pagination, seed).
* Catena: Fascicolo AuthZ → blob → bak → restore → retention → costi → *eventuale* listino.
* Fix solo al «vai»; §23 resta chiuso in audit.
* Verdetto: **base solida per continuare** se si ripaga il set pre-GTM e si tiene onesto il contratto commerciale.

### B. Mappa architettura attuale

Monolite FastAPI · React CRA · Mongo/Motor · FS `.media` · APScheduler 1-replica · JWT/refresh/Google/MFA + `omk_live` · TenantContext/`agency_id` · Stripe/Resend/Gemini/… · Ops: health, Sentry/webhook, `ops_alerts`, Founder Ops.

### C. Modello di dominio

Client = persona · Request = esigenza · Trash ≠ status (**D-094**) · Cestino = freeze (**D-111**) · Media pub/priv (**D-095**) · Pricing SoT (**D-109**) · Demo ≠ entitlement (**D-110**).

### D. Flussi principali

Login/`active_agency_id` · CRM property/client/request · Match/sync · Upload/serve media · Soft-delete→trash→purge · Invite · Billing · Demo seed · Bak · GTM demo path · Track B.

### E. Problemi — set ripago pre-GTM

*Registro completo: §14. Nessuna colonna P0–P3 — classe NI.*

| ID | Area | Problema | Impatto | Evidenza | Decisione |
|----|------|----------|---------|----------|-----------|
| NI-01 | AuthZ media | Fascicolo via path pubblico | Leak | AD-05 · M-01 | **D-095** |
| NI-02 | Invite | Overwrite password esistente | Account risk | AD-09 · AF-01 | **D-100** |
| NI-03 | Sessione | `agency_ids[0]` vs `active_agency_id` | Cross-agency | AD-08 · EC-01 | **D-106** |
| NI-04 | Lifecycle | Trash non uniforme + freeze | Dati morti operativi | AD-10 · EC-02/03 | **D-094** · **D-111** |
| NI-05 | Contratto | Pricing/demo/bak≠restore | Promesse false | AD-13/14 · CT-* | **D-109** · **D-110** · **D-113** |
| NI-06 | GTM | Minimi Demo Readiness | Demo fragile | AF-04/05 · EH-03/04 · SC-08 | **D-104** |
| NI-07 | Ops bak | No health OK/PARTIAL/FAILED | Bak silenzioso | AD-12 · O-01 | **D-105** |
| **D-114** | Economia bak/media | Full-copy × retention non sostenibile | Margine / listino cieco | AD-02 · B-01 · C-04 · SC-03 | **D-114** · D-096 |

Correlati: **D-107** errori · **D-108** scheduling · **D-112** seed · **D-113** restore.

### F. Cose che funzionano bene

AuthN fase-ok · tenant-guard CRM · Client/Request + soft-delete · monolite non errore · wallet atomico · restore/purge con vincitore · mount demo · D-094…D-113 come filtro · Ops base · listino deliberatamente fermo.

### G. Cose mancanti

Implementazione NI-01…07 (codice ⏳) · bak health UI · restore manuale testabile · contratto errori · owner scheduling · seed idempotente · (dopo) orphan WHEN · GDPR package · object storage/worker/OTel = **post**.

### H. Rischi futuri

Costi bak Agency media-heavy · orphan · overlap job · marketing > capability restore · GTM senza smoke · scalare senza owner scheduling · listino prima dei costi reali.

### I. Piano di intervento (senza etichette P0–P3)

| Fascia | Cosa |
|--------|------|
| **Pre-attivazione** | SoT §25bis DA CHIUDERE incl. **D-114** bak/media sostenibile · D-113 restore · linguaggio bak≠restore · listino fermo finché numeri |
| **~100** | D-098/102 orphan+purge · sharpen D-105 · object storage se smoke **o** D-114 lo impone |
| **~1000** | Bak+restore agency-first maturo → retention → costi → *eventuale* listino · rivalutare replica/CDN |
| **Dopo** | NI-10 GDPR · NI-11 worker/OTel/bak incr. · DR piattaforma se prodotto la richiede |

### J. Architettura consigliata (evolutiva)

Tenere monolite + 1 replica + FS finché smoke GTM regge. Rafforzare AuthZ/SoT dominio prima di infra. Bak+restore+retention = catena unica. Object storage = trigger capacità media. Worker solo dopo ownership scheduling. Nessun rewrite.

### K. Decisioni — prese / aperte

**Prese:** D-094…D-113 (vedi §4).  
**Aperte:** (1) esecuzione GTM-01 quando Founder dà sequenza; (2) «vai» sul ripago pre-GTM — §23 Priorità resta CLOSED.

### Domande aperte

1. **K-RF-01**: acquisire P25 come **CHIUSO** del continuum audit, o ancora rituale master §26/§27 prima di qualsiasi azione?
2. **K-RF-02**: prossimo passo = avvio **GTM-01** (dopo/accanto ripago NI), o solo acquisizione report fino a nuovo «vai»?

Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 25.

---

# 27. PROSSIMO PUNTO

Dopo acquisizione Founder su **P25**: tipicamente chiusura continuum · oppure rituale §26/§27 · GTM-01 in coda · «vai» sul ripago pre-GTM (allora §23 può diventare operativo).

Il Master Audit State deve essere aggiornato dopo il completamento di ogni punto significativo.

**Current next action:** Founder dà «vai» su **O0** e/o **O1**. Programma approvato (**D-115**). §23 Priorità CLOSED.

**Niente fix. Nessuna severità P0–P3. Listino fermo. Attende «vai».**
