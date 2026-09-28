# Audit architettura SaaS — note Founder

> Un punto alla volta. **Niente codice** senza «vai» esplicito di implementazione.  
> **Nessuna classificazione P0–P3** finché non si completa l’audit.  
> SoT: GitHub `mcnicastro-netizen/omnia2`.  
> Numerazione = quella costruita in sessione; temi allineati al prompt originario dove possibile.

**Ultimo aggiornamento**: 28-Set-2026 · P7 + **D-095** · **P8 Jobs consegnato**

---

## Stato audit

| # | Area | Stato |
|---|------|--------|
| P1 | Architettura attuale | 🟢 |
| P2 | Modello concettuale | 🟢 |
| P3 | Multi-tenancy | 🟠 finding aperti |
| P4 | AuthN/AuthZ | 🟠 finding aperti |
| P5 | Lifecycle + **D-094** | 🟠 finding aperti |
| P6 | Proiezioni / D-094 | 🟠 **ACQUISITO** · E-01…E-07 |
| P7 | Media / File + **D-095** | 🟠 finding aperti · M-01…M-14 |
| P8 | Jobs / processi asincroni | 🟠 Consegnato (feedback) |

```
… → NIENTE FIX → prossimo punto
```

**Nota numerazione**: lista originaria 1–27 non recuperabile in questo ambiente; P7 = Media/File (confermato Founder); P8 = Jobs/cron (continuum tipico post-Media). Founder può riallineare il titolo se il prompt originale differisce.

---

## Punto 6 — **ACQUISITO** Founder (28-Set)

D-094 corretta come dominio; **non** ancora applicata uniformemente a tutte le proiezioni/automazioni.

### Finding aperti (senza P0–P3)

E-01, E-02, E-03, E-04, E-06, E-07 (E-05/E-08/E-09 oss. utili).

### Attività (domanda aperta — non decidere ora)

Non assimilare automaticamente le Attività alle Richieste.  
Domanda corretta: *un’Attività appartiene al Cliente, alla Richiesta, all’Agente, o può essere autonoma?*  
Possibili grafi: Cliente→Richiesta→Attività · Cliente→Attività · Immobile→Attività.  
Rischio: archiviare/cancellare attività = perdita storico operativo.  
→ Risolvere con modello Attività + retention/privacy (punto dedicato), non in P6.

---

## Punto 3–5 (sintesi vincolante)

- P3: isolation applicativa sì · E2E no  
- P4: AuthN strutturata · AuthZ E2E incompleta (catena non uniforme)  
- P5 + **D-094**: Trash ≠ status; Cliente Trash → Richieste archiviate non distrutte; restore non riapre  

Cluster: P3.1+P4.1 fascicolo/media · P4.2 invite · P4.3–4 sessioni · P4.5–7 governance · L-* lifecycle

---

## Punto 7 — Media / File · finding aperti + **D-095** (28-Set)

### Verdetto acquisito

Storage fisico e AuthZ **non** sono realmente separati.  
Serve = un GET pubblico unico. Delete = solo Mongo → orfani.

### Cluster architetturali (non bug isolati)

1. **Media authorization** = P3.1 + P4.1 + **M-01** (stesso problema).  
2. **Lifecycle Mongo ⟷ blob inconsistente** = M-02 + M-03 + M-04 + L-05 + L-06.

### D-095 (dominio · codice ⏳)

| Tema | Direzione |
|------|-----------|
| Prefissi sensibili | **Fuori** dal GET pubblico; **no** “UUID = secret” |
| Foto pubblicabili | Pubblico ammissibile |
| Fascicolo/modulistica/… | AuthZ o URL firmati/temporanei (meccanismo dopo) |
| Cleanup blob | Regola **oggi**, indipendente da S3/R2; cleanup **idempotente** (non delete sincrono fragile) |

Finding **M-01…M-14** restano aperti (no P0–P3).

---

## Punto 8 — Jobs / processi asincroni · consegnato 28-Set (continuum post-Media)

### Verdetto

> I job globali (APScheduler + cron HTTP `super_admin`) sono **trusted execution paths** (P3): scorrono cross-tenant e poi ancorano `agency_id` *per item*.  
> Non ogni path background **enforcement** trash/D-094 né cleanup media/D-095.  
> Purge cestino e cleanup blob **non** sono nello scheduler; sync/matching leggono ancora `status=active` senza `with_not_trashed`.

### Inventario (sintesi)

| Job | Trigger | Auth | Tenant | D-094 trash | Media |
|-----|---------|------|--------|-------------|-------|
| `publishing_daily_sync` | APScheduler 06:00 UTC | trusted process | per `connection.agency_id` | **no** in `_fetch_properties` | n/a |
| `saved_searches_frequent` | APScheduler */5 min | trusted | B2C user; catalog pubblico | sì via `_base_filter` | n/a |
| `archive_daily_backup` | APScheduler 03:15 UTC | trusted | **globale** FS | dump tutto | copia tree local |
| `request_matching_nightly` | APScheduler 02:30 UTC | trusted | per `req.agency_id` | **no** su properties | n/a |
| HTTP `/cron/*` | manuale | JWT `super_admin` | come entrypoint | purge globale | no blob |
| `POST /publishing/sync/run-all` | manuale | `super_admin` | all connections | come sync | n/a |
| `sync-now` | API agenzia | agency_admin+ | `agency_id` user | come sync | n/a |
| Social publish | on-demand | agency | agency | (P6) | n/a |
| Staging / video / import / geocode / lead email | request-bound | auth path | misto | n/a | TTL job non schedulato |
| `reap_stale_jobs` | startup | trusted | globale status | n/a | no blob |

### Finding J-xx (no fix · no P0–P3)

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| **J-01** | gap | `_fetch_properties` sync: `agency_id`+`status=active` **senza** `with_not_trashed` | **E-01** · **D-094** |
| **J-02** | gap | `match_request` portfolio/MLS: stesso pattern no trash | **E-*** · **D-094** |
| **J-03** | gap | Purge trash **solo** HTTP cron — **assente** da APScheduler | L-05 · **D-094** |
| **J-04** | gap | Purge/trash = Mongo only; **nessun** job blob cleanup | **M-02/M-04** · **D-095** |
| **J-05** | oss. | Backup giornaliero = piano dati privilegiato globale (tutte le agenzie + media) | P3 #6 |
| **J-06** | oss. | Cron HTTP = JWT `super_admin` only (no service token / CRON_SECRET) | P3 trusted |
| **J-07** | gap | Favorite price-drop cron: `status=active` senza trash filter | D-094 |
| **J-08** | oss. | `schedule_geocode` update per `id` senza `agency_id` | P3 pattern id-only |
| **J-09** | oss. | `JOB_TTL_DAYS=30` staging dichiarato, **nessun** job di purge | D-095-adiacente |
| **J-10** | oss. | Lead email retry in-process poi drop; no coda durable | — |
| **J-11** | oss. | Request matching può notificare su cliente già in cestino (no check `deleted_at`) | D-094 cliente |
| **J-12** | oss. | Sync retry reload connection by `id` senza `agency_id` | basso se UUID |

### Link vincolanti

- **P3 trusted paths**: APScheduler + `super_admin` cron / `sync/run-all` = esecuzione fidata cross-tenant by design.
- **D-094**: dominio OK; job sync + matching + fav-drop **non** allineati (ribadisce E-01).
- **D-095**: nessun job cleanup blob; purge trash non tocca storage.
- **Purge trash**: `run_trash_purge` globale; trigger solo `POST /cron/trash/purge` (+ `/trash/purge-expired`).

### Domande aperte

1. Il purge cestino (e un futuro cleanup blob) devono entrare in APScheduler come gli altri job nightly, o restano solo trigger HTTP esterni?
2. I path trusted devono portare un *tenant cursor* esplicito (anche quando scorrono all-agencies), o basta lo scope per-item attuale?

### Prossimo

Punto successivo su ok Founder. **Niente fix.**
