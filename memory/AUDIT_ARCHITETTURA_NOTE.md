# Audit architettura SaaS — note Founder

> Un punto alla volta. **Niente codice** senza «vai» esplicito di implementazione.  
> **Nessuna classificazione P0–P3** finché non si completa l’audit.  
> SoT: GitHub `mcnicastro-netizen/omnia2`.  
> **Numerazione = continuum di sessione** (non forzare allineamento al master).  
> Prompt master: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27) — corrispondenza in tabella sotto.

**Ultimo aggiornamento**: 28-Set-2026 · **P9 ACQUISITO** · **P10 Backup consegnato**

---

## Stato audit (numerazione sessione)

| # | Area | Master § | Stato |
|---|------|----------|--------|
| P1 | Architettura attuale | §1 | 🟢 |
| P2 | Modello concettuale | §2 | 🟢 |
| P3 | Multi-tenancy | §3 | 🟠 finding aperti |
| P4 | AuthN/AuthZ | §4 | 🟠 finding aperti |
| P5 | Lifecycle + **D-094** | §5 (+ pezzi §6) | 🟠 finding aperti |
| P6 | Proiezioni / D-094 | fuori indice | 🟠 **ACQUISITO** · E-* |
| P7 | Media / File + **D-095** | §7 | 🟠 **ACQUISITO** · M-* |
| P8 | Jobs / processi asincroni | §15 (anticipato) | 🟠 **ACQUISITO** · J-* |
| P9 | Storage e costi | §8 | 🟠 **ACQUISITO** · C-* |
| P10 | Backup | §9 | 🟠 Consegnato (feedback) |
| — | Cestino (blocco dedicato) | §6 | 🟡 parziale in P5 |
| — | Restore / Retention / GDPR… | §10–§14 | ⬜ prossimo naturale: **§10 Restore** |
| — | Osservabilità → report | §16–§27 | ⬜ |

Decisioni dominio (codice ⏳): **D-094**, **D-095**.

---

## Cluster già emersi (no P0–P3 finché Founder non apre §23)

1. **Media authorization** = P3.1 + P4.1 + M-01 → D-095  
2. **Mongo ⟷ blob lifecycle** = M-02…M-04 + L-05/L-06 → D-095  
3. **Proiezioni/jobs vs D-094** = E-* · J-01…J-04  
4. **AuthZ non uniforme** login→risorsa (P4)  
5. **Attività**: appartenenza aperta (non = Richieste)  
6. **Costo infra massimo / bak** = C-* + **B-01** (full-copy ~31×) — €/GB all-in **non confermato**  
7. **Trusted path tenant context** = domanda aperta P8 (bak = *nessun* tenant scope)  
8. **APScheduler in-process** = *area da verificare* in affidabilità/deployment (**non** finding ancora)

---

## Punto 3–7 (sintesi vincolante)

- P3: isolation applicativa sì · E2E no  
- P4: AuthN strutturata · AuthZ E2E incompleta  
- P5 + **D-094**: Trash ≠ status; Cliente Trash → Richieste archiviate; restore non riapre  
- P6: D-094 non uniforme su proiezioni (E-01…E-07); Attività = domanda aperta  
- P7 + **D-095**: pubblico vs privato; cleanup blob indipendente da S3/R2; M-01…M-14 aperti  

---

## Punto 8 — Jobs / processi asincroni · **ACQUISITO** Founder (28-Set)

### Verdetto acquisito

> I job globali (APScheduler + cron HTTP `super_admin`) sono **trusted execution paths**: scorrono cross-tenant e poi ancorano `agency_id` *per item*.  
> D-094/D-095 **non** sono enforcement uniforme nei job.  
> Purge cestino e cleanup blob **non** sono automatici osservabili oggi («qualcuno deve ricordarsi di chiamare l’endpoint» = fragile per SaaS commerciale).

### Finding aperti (no fix · no P0–P3)

**J-01…J-12** restano aperti come consegnati.

### Precisazioni metodologiche Founder (acquisite — non chiuse)

#### 1. Purge Trash + blob cleanup — **decisione ancora aperta**

Annotato come direzione, **non** scelta di orchestrazione:

> **Purge e blob cleanup devono diventare processi automatici e osservabili; resta da decidere se l’orchestrazione primaria sarà APScheduler o un cron/worker esterno.**

Criterio vincolante: non deve restare dipendenza da richiamo manuale dell’endpoint.  
La scelta *dove gira* può emergere dopo Backup / Restore / Retention / Deployment (coerenza tra tutti i job periodici).

#### 2. Trusted paths — scope per-item **necessario ma non sufficiente**

Direzione P8 confermata. Domanda lasciata aperta (da approfondire su backup, restore, sync, matching, cleanup, future elaborazioni media):

```text
Job trusted
   ↓
qual è il tenant context?
   ↓
come viene creato?
   ↓
come viene propagato?
   ↓
come si dimostra che ogni operazione è scoped?
```

#### 3. APScheduler nel processo API — **area da verificare** (non finding)

```text
API process
 ├── HTTP requests
 └── scheduler
```

Da verificare nei capitoli affidabilità / scalabilità / deployment (master §16/§19):

- riavvio processo a metà job  
- due istanze API → doppia esecuzione  
- job più lungo dell’intervallo  
- fallimento a metà  
- deploy mentre gira un job  

**Non** trasformato in finding J-* ora.

### Inventario (sintesi)

| Job | Trigger | Tenant | D-094 trash | Note |
|-----|---------|--------|-------------|------|
| `publishing_daily_sync` | APScheduler 06:00 | per connection | **no** | J-01 |
| `saved_searches_frequent` | */5 min | B2C | sì via filter | — |
| `archive_daily_backup` | 03:15 | **globale** | dump tutto | J-05 · costo in P9 |
| `request_matching_nightly` | 02:30 | per request | **no** | J-02/J-11 |
| HTTP `/cron/*` | manuale `super_admin` | entrypoint | purge solo HTTP | J-03/J-04/J-06 |

### Domande aperte (non chiudere prima di backup/deploy)

1. Orchestrazione purge + blob cleanup: APScheduler vs cron/worker esterno?  
2. Modello di *tenant context* per trusted paths (creazione / propagazione / prova di scope)?

---

## Punto 9 — Storage e costi · **ACQUISITO** Founder (28-Set · master §8)

### Verdetto acquisito (formulazione Founder)

> Esiste un **tetto commerciale** chiaro (D-085: 30/100/300 GB + addon €15/100 GB + **413**).  
> Il cliente **non** può consumare storage infinito senza acquistarlo.  
> Formulazione corretta:  
> **«Il costo infra massimo per cliente non è ancora sufficientemente determinabile con l’architettura di backup attuale.»**  
> (Non: “il costo non è prevedibile” — il tetto commerciale c’è; manca la determinazione di quanto costa un **GB venduto** all-in: primario + bak + retention + traffico + repliche + video.)

### Lettura Founder degli elementi (acquisita)

| Elemento | Valutazione |
|----------|-------------|
| D-085 30/100/300 + addon | ✅ Modello commerciale chiaro |
| 413 al superamento | ✅ Enforcement tecnico corretto |
| Metering + blocco | 🟠 Da verificare nei dettagli (`max_properties` non enforced) |
| C-01 `max_properties` | 🟠 Finding corretto, aperto |
| 60 foto / 3×80 MB / 5 planimetrie | ✅ Limiti utili |
| C-04 bak full ×30g | 🔴 Non fix ora — **approfondito in P10** |
| Crediti ≠ storage | ✅ Concettualmente corretto |
| C-09 bandwidth | 🟠 Aperto (importante con video/download) |
| C-08 B2C senza quota | 🟠 Da verificare nel modello economico |
| Agency ∞ + video | 🟠 Non necessariamente problema (c’è tetto storage); bak può amplificare → C-10 |

### Risposte alle domande aperte P9

1. **€0,04/GB** → **non confermato**; si aspetta l’analisi Backup (P10).  
2. **Video** → **nessun secondo tetto** specifico; limite principale = storage.

Finding **C-01…C-15** e **K-STOR-01…08** restano aperti. **Niente fix.**

---

## Punto 9 — dettaglio tecnico (riferimento)

### Verdetto tecnico (pre-acquisizione, riformulato)

> Tetto commerciale B2B presente. Costo infra **massimo** non ancora sufficientemente determinabile con bak full-copy attuale.

### Mappa limiti piano vs storage

| Piano | Canone | Immobili (listino) | Enforced create? | Storage incluso | Extra |
|-------|--------|--------------------|------------------|-----------------|-------|
| Starter | €49 | 30 | **No** | **30 GB** | +100 GB €15/mese |
| Pro | €99 | 200 | **No** | **100 GB** | idem |
| Agency | €299 | ∞ (−1) | N/A | **300 GB** | idem |
| Free / no sub | — | — | — | **5 GB** soft | — |

**Evidenza**
- Listino immobili/agenti: `backend/apps/billing/plans.py` (`max_properties` 30 / 200 / −1).  
- Quota runtime: `backend/shared/storage/quota.py` — `TIER_QUOTA_GB`, addon 100 GB / €15, meter, `assert_can_upload` → **413**.  
- Create immobile: `properties.py` `create_property` — **nessun** check `max_properties`.  
- Contatore: foto + video + floor_plans + documents su **tutte** le properties (Cestino **incluso**). Foto senza `size_bytes` → stima 600 KB.

### Tetti per immobile (upload B2B)

| Asset | Max | Size |
|-------|-----|------|
| Foto | 60 | 8 MB |
| Video | 3 | 80 MB |
| Planimetrie | 5 | 15 MB |

Worst-case grezzo ≈ **~0,78–0,85 GB/immobile** (+ fascicolo). **Nessun** check risoluzione 4K — solo MIME + size.

### Scenari di costo (ordine di grandezza)

| Scenario | Archivio stimato | Quota | Nota costo OMNIA |
|----------|------------------|-------|------------------|
| Starter 30 imm. full media | ~25 GB | 30 GB | Live sotto tetto; bak full ×30g moltiplica disco ops |
| Pro 200 imm. full media | ~170 GB | 100 GB → **413** | Serve addon o meno video |
| Agency video-heavy | sale fino a 300 GB | 300 GB | Solo freno = quota/addon; bak naive = rischio margine |
| Agency leggera | pochi GB | 300 GB | Margine alto se uso basso |

**Backup (impatto costo — anteprima §9 master)**: `backup_job.py` fa `shutil.copytree` di **tutto** `MEDIA_ROOT` ogni giorno, retention `BACKUP_RETENTION_DAYS` default **30**. Non entra nel meter cliente; è costo OMNIA. Collegato a J-05 e alla decisione aperta sull’orchestrazione job (P8).

**Crediti ≠ storage**: wallet/ledger vs `storage_extra_gb` / `storage_addon` — separazione billing OK.

**Staging/fal**: costo compute a crediti; save-to-property può restare base64 in Mongo senza `assert_can_upload` (meter sottostima / Mongo ingrossa).

**B2C private listings**: max 1 annuncio free, 30 foto × 8 MB; **nessuna** quota agency / `assert_can_upload`.

**Bandwidth**: zero metering; `GET /api/media/{path}` pubblico + cache + Range video.

### Finding C-xx (no fix · no P0–P3)

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| **C-01** | gap | `max_properties` solo catalogo; create non enforce | plans vs `create_property` |
| **C-02** | oss. | Quota D-085: meter + 413 + addon — implementata | `quota.py` · test D-085 |
| **C-03** | oss. | Contatore unico; trash conteggiato | allineato Modello A D-085 |
| **C-04** | rischio | Backup full-copy media ×30g → moltiplicatore disco ~31× | `backup_job.py` · J-05 |
| **C-05** | gap | Limiti foto/video/planimetrie OK; **no** tetto 4K/risoluzione | `properties.py` |
| **C-06** | gap | Fascicolo multipart quotato; path **base64** documents bypass `assert_can_upload` | `fascicolo.py` |
| **C-07** | oss. | Staging a crediti; save-to-property senza quota object-store | M-* adiacente |
| **C-08** | rischio | B2C media senza quota agency — costo unbounded su n° utenti | `private_listings.py` |
| **C-09** | gap | Zero metering bandwidth/CDN/egress | `media.py` · M-01 pubblico |
| **C-10** | rischio | Agency ∞ immobili + solo tetto 300 GB; bak amplifica | listino vs D-085 |
| **C-11** | gap | upload-tmp orfani: su disco (+ bak) ma fuori meter se non legati a property | M-06 |
| **C-12** | oss. | Crediti e storage billing separati — OK | checkout kinds |
| **C-13** | gap | Seed Stripe `storage_100gb` potenzialmente assente da setup | D-085 residuo |
| **C-14** | oss. | D-095 lifecycle blob: dominio sì, codice ⏳ | M-02…M-04 |
| **C-15** | gap | Import XML URL esterni senza `size_bytes` → meter sottostima | import |

### Link

| Ref | Ruolo |
|-----|--------|
| **D-085** | Quota GB per piano — applicata (meter/blocco) |
| **D-095** | Pubblico/privato + cleanup blob — codice ⏳ |
| **M-*** | AuthZ media + orphan |
| **J-03/J-04/J-05** | Purge non automatico · no blob cleanup · bak globale |
| Cap. 19 / `PRICING_OMNIA.md` | Listino commerciale |

### Decisioni da prendere (K-style · **non** implementare ora)

1. **K-STOR-01** — Enforce hard `max_properties` / `max_agents`, o listino soft esplicito?  
2. **K-STOR-02** — Backup: accettare full-copy ~31×, o target incremental/snapshot? (si lega a master §9 e alla decisione P8 sull’orchestrazione)  
3. **K-STOR-03** — Agency a quota piena: solo addon, o soft-cap prodotto (meno video / compressione)?  
4. **K-STOR-04** — Bandwidth/egress: incluso nel canone o metered?  
5. **K-STOR-05** — B2C media: quota globale / per-utente / leave-as-is?  
6. **K-STOR-06** — Staging save → object store + quota (no base64 Mongo)?  
7. **K-STOR-07** — Chiudere path fascicolo base64 vs solo multipart quotato?  
8. **K-STOR-08** — Seed Stripe live `storage_100gb_monthly` prima del go-live?

### Domande aperte P9 — **chiuse** dal Founder (vedi sopra)

1. €0,04/GB → non confermato; aspetta Backup.  
2. Video → nessun secondo tetto; limite = storage.

---

## Punto 10 — Backup · consegnato 28-Set (master §9 · continuum sessione)

### Verdetto (bozza)

> Il backup giornaliero esiste (APScheduler 03:15 UTC + `POST /cron/backup/daily` `super_admin`) e fa ciò che D-085 promette a livello di *intent*: dump Mongo whitelist + copia media local + retention 30g.  
> Architettura: **full `shutil.copytree`** di tutto `LOCAL_STORAGE_ROOT` ogni giorno, **senza** incremental/dedup/snapshot → in regime stazionario  
> `GB_backup ≈ X × (R+1)` ≈ **31×** live (R=30); live+bak ≈ **32×**.  
> Quindi: **€0,04/GB all-in non è confermabile** con questo modello (allinea P9).  
> Inoltre il dump Mongo è **parziale** (manca CRM critico: `client_requests`, activities, …); `"groups"` ≠ `agency_groups`; media Emergent **OUT**; **nessun** restore code path (→ P11); bak **globale** multi-tenant (trusted path senza tenant context — chiarisce P8).

### Trigger

| Meccanismo | Dove | Note |
|------------|------|------|
| APScheduler `archive_daily_backup` | `sync_engine.py` 03:15 UTC | `max_instances=1`, `coalesce=True` |
| HTTP `POST /api/app/cron/backup/daily` | `cron.py` | JWT `super_admin` |
| Lock condiviso HTTP↔scheduler | **assente** | race possibile sullo stesso giorno |

### Cosa viene salvato / cosa no

**IN Mongo** (`backup_job.py` `_COLLECTIONS`):  
`agencies`, `users`, `properties`, `clients`, `leads`, `subscriptions`, `credit_wallets`, `credit_ledger`, `api_keys`, `groups`, `publishing_connections`  
— dump **globale**, cap `to_list(100_000)`, include record **trashed**.

**IN media**: `copytree` di tutto `MEDIA_ROOT` se presente (local). Trashed/orphan blob inclusi finché restano su disco.

**OUT / gap**:
| Asset | Stato |
|-------|--------|
| `client_requests`, `activities`, calendar, matches, social_*, favorites, saved_searches, HAL… | **OUT** |
| `agency_groups` (codice reale) vs `"groups"` in bak | **OUT di fatto** (nome sbagliato) |
| `refresh_tokens`, modulistica meta | **OUT** |
| Emergent / non-local object store | **OUT** |
| Checksum / cifratura bak | **assenti** |
| Restore automatizzato | **assente** (P11) |

### Modello di costo (conferma C-04)

```text
GB_backup_tree  ≈ X × (R + 1)     # R=BACKUP_RETENTION_DAYS default 30 → ~31X
GB_disk_totale  ≈ X × (R + 2)     # live + bak → ~32X
```

| Quota piena | X live | Bak ≈31X | Live+bak ≈32X |
|-------------|--------|----------|---------------|
| Starter 30 GB | 30 | ~930 GB | ~960 GB |
| Pro 100 GB | 100 | ~3,1 TB | ~3,2 TB |
| Agency 300 GB | 300 | ~9,3 TB | ~9,6 TB |

Bak = costo **OMNIA** (non nel meter cliente). Un tenant pesante amplifica il tree **globale**.

### Affidabilità (sintesi)

- Failure collection/media → `ok=false`, cartella giorno può restare **parziale**; MANIFEST scritto comunque; purge vecchi gira dopo.  
- APScheduler: no overlap stesso job (`max_instances=1`); **no** lock vs HTTP cron; multi-istanza API → doppio scheduler (area P8).  
- Nessun test `backup_job` in `backend/tests/`.  
- Trusted path: bak = **assenza di tenant scope** (dump all).

### Finding B-xx (no fix · no P0–P3)

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| **B-01** | rischio | Full copytree × (R+1) → ~31× disco | **C-04** |
| **B-02** | gap | Dump Mongo parziale (CRM critico fuori) | — |
| **B-03** | gap | `"groups"` ≠ `agency_groups` | Cap.24 |
| **B-04** | gap | Cap soft 100k doc senza warning | — |
| **B-05** | rischio | Emergent → media bak incompleto | M-12 · STORAGE |
| **B-06** | gap | Nessuna cifratura at-rest / ACL esplicita BACKUP_ROOT | — |
| **B-07** | gap | Manifest senza checksum | — |
| **B-08** | rischio | Concorrenza HTTP cron ↔ APScheduler; multi-replica | P8 area |
| **B-09** | oss. | Giorno parziale + purge può cancellare vecchi comunque | — |
| **B-10** | oss. | Trashed + orphan inclusi → allungano costo bak | D-095 · D-094 |
| **B-11** | gap | `BACKUP_*` poco documentati in `.env.example` | — |
| **B-12** | gap | Nessun restore code path | → **P11** |
| **B-13** | oss. | Bak globale: no isolamento disaster/costo per cliente | P3 · P8 |
| **B-14** | oss. | Doppia orchestration in-process + HTTP | P8 decisione aperta |

### Link

| Ref | Ruolo |
|-----|--------|
| **C-04** | Rischio P9 — deep dive qui: **confermato** |
| **J-05** | Job bak globale trusted |
| **P8** | Orchestrazione e tenant context ancora aperti; bak = no tenant |
| **D-085** | Promessa bak 30g + restore via supporto; €0,04 / “versionato” ≠ codice full-copy |

### Decisioni da prendere (K-style · non implementare)

1. **K-BAK-01** — Accettare full-copy ~31×, o incremental/snapshot/object-versioning? (= chiude anche K-STOR-02)  
2. **K-BAK-02** — Orchestrazione unica bak (+ purge/blob): APScheduler in-API / cron esterno / worker dedicato?  
3. **K-BAK-03** — Scope dump: ampliare whitelist vs `mongodump` vs per-tenant?  
4. **K-BAK-04** — Media: solo local, o mirror obbligatorio anche Emergent/S3/R2?  
5. **K-BAK-05** — Cifratura / path / ACL / offsite di `BACKUP_ROOT`?  
6. **K-BAK-06** — Trashed/orphan nel bak: ok fino a retention, o exclude + policy (→ Retention §12)?

### Domande aperte (max 2)

1. Si vuole ancora basare il listino GB su un all-in tipo **€0,04/GB**, sapendo che il moltiplicatore disco bak è **~31× full-copy**?  
2. Per bak (+ future purge/blob): **APScheduler nel processo API** resta accettabile in produzione, o si impone **cron/worker esterno** come orchestrazione primaria?

### Anteprima Restore (defer P11)

**Non esiste** entrypoint di restore (né API né script). Il prodotto promette ripristino “via supporto OMNIA” (Cap.19 / D-085). Il commento in `backup_job.py` descrive un’intenzione, non codice. Gap per P11: completo vs per-agenzia, relazioni, media Emergent, collection fuori whitelist, giorno `ok=false`.

### Prossimo

Su ok Founder: **Restore** (master §10 / sessione P11).  
**Niente fix. Nessuna severità definitiva.**
