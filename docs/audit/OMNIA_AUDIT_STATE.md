# OMNIA — MASTER AUDIT STATE

**Purpose:** stato operativo compatto dell'audit logico, architetturale e funzionale di OMNIA.

**Usage rule:** questo documento è la fonte di continuità dell'audit.
Prima di analizzare un nuovo punto, leggere questo file. Non riaprire decisioni già fissate salvo nuove evidenze. Non inventare informazioni mancanti.

**Current status:** P1–P19 **chiusi** · **P20 Scalabilità consegnato** ⏳ analisi Founder. Nessun fix. Listino fermo. SoT: questo file. **Niente codice** senza «vai».

**Next:** analisi Founder su P20 → tipicamente **P21 Coerenza prodotto/tecnologia** (master §20). GTM-01 in coda.

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

# 21. P20 — SCALABILITÀ (consegnato · ⏳ analisi Founder · master §19)

**Verdetto:** per **GTM-01 (~20 concurrent)** monolitico single-replica + Mongo + FS locale è **adeguato in verticale**, se non si martella Match/media in parallelo. **Non** è pronto a orizzontale (FS locale, APScheduler in-process — **D-101**/ **D-103**). Crescita **200–1000 agenzie** collassa prima su **storage+bak (~31× B-01)**, serve media, match on-read e job globali — non su “mancano 5000 user contemporanei”.
**Nessun nuovo P0–P3** da P20. Nessun fix finché «vai». **D-101 / D-103 / B-01 / GTM-01 non riaperti.**

### Finding SC-*

| ID | Tipo | Problema | Prior |
|----|------|----------|-------|
| SC-01 | oss. | 1 processo uvicorn + APScheduler in-API; no worker; horizontal = doppio scheduler | D-101 · D-103 · JA-01 |
| SC-02 | rischio crescita | `.media` locale + `get_object` full-read in RAM via API — no multi-istanza / no CDN | M-* · C-09 |
| SC-03 | rischio eco | Bak full `copytree` ~31× — pressione disco ≫ concurrent users | B-01 · C-04 |
| SC-04 | rischio demo/load | Match on-read fino a 400×400 (+ scoped 2000); stress ~5,8s @10k clienti | — |
| SC-05 | gap | Nessun indice su `deleted_at`; `with_not_trashed` = `$or` | trash |
| SC-06 | gap | `rate_limit_events` senza index in `ensure_indexes` (solo stress script) | — |
| SC-07 | oss. | Motor `AsyncIOMotorClient()` senza pool esplicito — default OK GTM | — |
| SC-08 | debito demo | Properties FE senza `page` / controlli (**AF-04**) | AF-04 |
| SC-09 | rischio crescita | Saved-search tick ogni 5m su **tutte** le ricerche attive | JA · A-020 |
| SC-10 | rischio ops | Overlap HTTP cron ↔ APScheduler; `max_instances=1` solo in-proc | JA-01 · B-08 · RC-09 |
| SC-11 | rischio crescita | Feed pubblico fino a 5000 prop full-doc | C-09 |
| SC-12 | oss. | Auth: JWT cookie + `users.find_one` per request | — |
| SC-13 | rischio crescita | Publishing sync sequenziale fino a 1000 connection | J-* |
| SC-14 | oss. | Liste CRM API con `page_size` capped; FE gaps AF-04/AF-11 | AF-04 |
| SC-15 | rischio demo | Hot path media: upload + serve sullo stesso event loop | AF-05 · EH-03 |

### Domande aperte

1. **K-SC-01**: Prima di GTM-01, smoke load dedicato (upload+media+match ×~20) o basta ladder stress esistente?
2. **K-SC-02**: Soglia agenzie/storage per forzare object storage condiviso + CDN (prima di worker — **D-103**)?

### Lettura Founder

| Classe | Cosa |
|--------|------|
| **Già solido** | Liste properties/clients paginate lato API; match capped; job `max_instances=1`+`coalesce`; rate limit pubblico; quota upload; single-replica job (**D-101**) |
| **Realmente rischioso** | Media via API+FS; match 400×400 in demo; bak 31×; AF-04 stock>20; overlap HTTP↔sched |
| **Da decidere** | **K-SC-01** · **K-SC-02** |
| **Può aspettare** | Pool Motor esplicito; indici `deleted_at`; precompute match; worker (**D-103**); horizontal API |

Dettaglio: `memory/AUDIT_ARCHITETTURA_NOTE.md` § Punto 20.

---

# 22. PROSSIMO PUNTO

**P21 — Coerenza prodotto/tecnologia** (master §20) — tipico dopo acquisizione P20.

Il Master Audit State deve essere aggiornato dopo il completamento di ogni punto significativo.

**Current next action:** analisi Founder su **P20** (SC-* · K-SC-01/02). P19 chiuso. GTM-01 in coda (vincolo pre-~5000 email).

**Niente fix. Nessuna severità P0–P3. Listino fermo. Attende «vai».**
