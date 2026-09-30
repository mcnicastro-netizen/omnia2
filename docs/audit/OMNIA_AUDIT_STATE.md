# OMNIA — MASTER AUDIT STATE

**Purpose:** stato operativo compatto dell'audit logico, architetturale e funzionale di OMNIA.

**Usage rule:** questo documento è la fonte di continuità dell'audit.
Prima di analizzare un nuovo punto, leggere questo file. Non riaprire decisioni già fissate salvo nuove evidenze. Non inventare informazioni mancanti.

**Current status:** P1–P18 analizzati. Nessun fix applicato salvo dove esplicitamente indicato come già esistente. Listino fermo. SoT continuità: questo file.

**Next:** P19 — Error handling.

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

## D-094 — Lifecycle/proiezioni

Gli elementi cestinati non devono essere considerati operativi dalle proiezioni esterne.
Da rispettare in:

* feed;
* sync;
* matching;
* pubblicazioni;
* website/MLS;
* job correlati.

`status` commerciale e lifecycle/trash sono concetti distinti.

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

## D-100 — Invite

Invite verso utente già registrato:

> collegamento dell'utente all'agenzia / accettazione invito.

**Mai sovrascrivere la password esistente.**

Questo è **fix-needed**, in attesa di autorizzazione esplicita a intervenire.

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

* 2 richieste demo;
* 50 richieste;
* 200 richieste;
* circa 20 utenti contemporanei;
* percorso demo completo;
* stabilità delle funzioni mostrate ai prospect.

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

# 19. P18 — API / FRONTEND (consegnato 30-Set)

**Verdetto:** mount/routing demo coerenti; drift su invite (D-100), multi-agency `/me`, pagination properties, upload foto silenzioso, B2C URL raw, sessione B2B/B2C unica.

### Finding AF-*

| ID | Tipo | Problema |
|----|------|----------|
| AF-01 | fix-needed | Invite overwrite password · FE chiede sempre password (**D-100**) |
| AF-02 | rischio | `/api/media` pubblico (**D-095**) |
| AF-03 | drift | Switcher `active_agency_id` vs `/agencies/me` = `agency_ids[0]` |
| AF-04 | gap | Properties: no paginazione UI → >20 invisibili |
| AF-05 | gap | PhotoUploader silent fail |
| AF-06 | drift | B2C usa `REACT_APP_BACKEND_URL` grezzo |
| AF-07 | rischio | Sessione unica · login default → CRM |
| AF-08 | oss. | Billing UI senza gate Stripe enabled |
| AF-09 | gap | Error UX non uniforme |
| AF-10 | perf | Match scan pesante · SellPage 1+N stats |
| AF-11 | gap | Requests: page senza UI |
| AF-12…AF-16 | oss. | Nav IT hardcoded · versioning · CORS default · a11y · scaffold etichettato |

### Domande aperte

1. **K-AF-01** — Allineare `/agencies/me*` a `active_agency_id`, o nascondere switcher?
2. **K-AF-02** — D-100: flusso FE “utente esistente → link/login” subito, o solo fix server al «vai»?

Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 18.

---

# 20. PROSSIMO PUNTO

**P19 — Error handling** (master §18)

Il Master Audit State deve essere aggiornato dopo il completamento di ogni punto significativo.

**Current next action:** analizzare P19 senza ripetere integralmente P1–P18.