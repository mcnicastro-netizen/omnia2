# OMNIA — MASTER AUDIT STATE

**Purpose:** stato operativo compatto dell'audit logico, architetturale e funzionale di OMNIA.

**Usage rule:** questo documento è la fonte di continuità dell'audit.
Prima di analizzare un nuovo punto, leggere questo file. Non riaprire decisioni già fissate salvo nuove evidenze. Non inventare informazioni mancanti.

**Current status:** P1–P21 **chiusi** · **P22 Casi limite consegnato** ⏳ analisi Founder. Nessun fix. Listino fermo. SoT: questo file. **Niente codice** senza «vai».

**Next:** analisi Founder su **P22 (EC-*)**. GTM-01 in coda.

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

## D-106 — `active_agency_id` SoT sessione

* `active_agency_id` = agency operativa corrente (source of truth).
* `agency_ids` = membership / agency disponibili.
* Flusso: `active_agency_id → /agencies/me* → FE`.
* **Non** nascondere lo switcher per evitare il drift.
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

### Error handling

EH-01…EH-12 · **D-107** · P19 CHIUSO

### Scalabilità

SC-01…SC-15

### Coerenza prodotto/tecnologia

CT-01…CT-14 · **D-109** pricing SoT · **D-110** demo≠entitlement · **P21 CHIUSO**

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


# 23. P22 — CASI LIMITE (consegnato · ⏳ analisi Founder · master §21)

**Verdetto:** I percorsi felici CRM (Cestino restore/purge, size/quota upload, feed pubblico trash-aware, guard invite scaduto/revocato, webhook `applied_at`, empty properties) tengono. I casi limite che rompono **demo multi-tenant** o **safety** sono: matching/sync che ignorano `deleted_at` (D-094), client trash con richieste ancora operative + email matching, invite overwrite (D-100) + accept non atomico, SoT agency `agency_ids[0]` vs `active_agency_id` (D-106), JWT disabilitato ancora valido, seed demo che riaggancia `demo.admin`/Founder a `demo-agency-001`.
**Nessun nuovo P0–P3.** Nessun fix. **D-094…D-110 / GTM-01 / P18–P21 non riaperti** (solo link).

### Finding EC-*

| ID | Tipo | Problema | Prior | Evidenza |
|----|------|----------|-------|----------|
| EC-01 | drift SoT | CRM usa `active_agency_id`; `/agencies/me`, invites, billing usano `agency_ids[0]` → switcher non governa tutto | **D-106** · AF-03 | `tenant.py:12-17` · `agencies.py:120` · `invites.py:51` · `billing/routes.py:91` |
| EC-02 | gap D-094 | Match + sync + smart-clients: `status=active` **senza** `with_not_trashed` | **D-094** · E-* · RC | `client_requests_service.py:454-456` · `sync_engine.py:58-64` · `clients_smart.py:382-384` |
| EC-03 | gap D-094 | Client trash non tocca richieste open; job matching continua (email) | **D-094** · T-03 | `clients.py:190-218` · `request_matching_job.py:184-193` · `104-110` |
| EC-04 | bug campo | Migrate prefs filtra `trashed_at` (inesistente) non `deleted_at` | T-03 | `client_requests_service.py:284-289` |
| EC-05 | fix-needed | Accept invite overwrite password utente esistente; verify senza `user_exists` | **D-100** · CT-09 | `invites.py:246-254` · `176-206` |
| EC-06 | race | Accept non-atomic (check pending → write); doppio accept possibile | RC-invite | `invites.py:222-284` |
| EC-07 | demo gate | Stripe off 503; FE sblocca checkout con `localStorage omnia_demo_done` | **D-110** · CT-06 | `billing/routes.py:41-47` · `BillingPage.jsx:83-110` |
| EC-08 | race | Webhook `applied_at` idempotente in seriale; TOCTOU doppio credito sotto replay concorrente | RC | `billing/routes.py:366-374` · `481-491` |
| EC-09 | gap | Downgrade piano: nessun clamp usage; solo block upload 413 se over quota | CT-02 · D-085 | `quota.py:46-52` · `138-152` |
| EC-10 | AuthZ | Fascicolo path sotto `/api/media` pubblico se noto; media trashed resta servibile | **D-095** · M-01 | `media.py:26-34` · `fascicolo.py:252` · `objstore.py:109-118` |
| EC-11 | sessione | `get_current_user` non ricontrolla `is_active`; reset password non revoca refresh | P4 auth | `dependencies.py:18-40` · `auth.py:427-452` · `session_store.py:34-42` |
| EC-12 | job | Trash purge **solo** HTTP cron, non APScheduler; cron+sched stesso giorno su bak/match | **D-102** · **D-108** | `sync_engine.py:258-337` · `cron.py:37-50` |
| EC-13 | seed | Seed forza `demo.admin` (+ Founder senza agency) su `demo-agency-001` | demo | `seed.py:52-61` · `104-112` · `seed_demo_gestionale.py` |
| EC-14 | upload edge | Upload foto su property **già trashed** (find senza `with_not_trashed`) | L / RC | `properties.py:587-589` |
| EC-15 | i18n | Codici invite BE non in locale; FE collassa verify a `accept_invite.invalid` | **D-107** | `AcceptInvitePage.jsx:39-41` · `locales/it.json` (solo auth.*) |

### Domande aperte

1. **K-EC-01**: Prima di GTM, matching/sync devono rifiutare trashed **ovunque** (enforcement uniforme D-094), o basta feed pubblico già filtrato?
2. **K-EC-02**: Client in Cestino → archiviare/freeze richieste open subito, o solo escluderle dai job finché il client è trashed?

### Lettura Founder

| Classe | Cosa |
|--------|------|
| **Già mitigato** | Restore/purge happy+404 post-purge; feed XML + compliance `with_not_trashed`; size limit upload + 413 quota; `..` in media path; invite expired/revoked codes; empty properties UI; remove_member clear `active_agency_id`; addon Stripe-off messaggio supporto |
| **Rischio latente** | EC-06/08 race; EC-09 downgrade; EC-10/14 media; EC-11 sessioni; EC-12 dual schedule + purge non schedulato; EC-04 trashed_at; EC-15 i18n |
| **Demo-critical** | EC-01 multi-agency SoT; EC-02/03 D-094 match+client; EC-05 D-100; EC-07 Stripe/localStorage; EC-13 seed collision |
| **Da decidere** | K-EC-01 · K-EC-02 |
| **Può aspettare** | Null geocode soft-fail; sessioni concurrent deliberate; MFA challenge TTL |

Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 22.

---

# 24. PROSSIMO PUNTO

Dopo acquisizione Founder su **P22**: tipicamente master §22+ / GTM-01 in coda.

Il Master Audit State deve essere aggiornato dopo il completamento di ogni punto significativo.

**Current next action:** analisi Founder su **P22 (EC-*)**. GTM-01 in coda (vincolo pre-~5000 email).

**Niente fix. Nessuna severità P0–P3. Listino fermo. Attende «vai».**
