# Audit architettura SaaS — note Founder

> Un punto alla volta. **Niente codice** senza «vai» esplicito di implementazione.  
> **Nessuna classificazione P0–P3** finché non si completa l’audit.  
> SoT: GitHub `mcnicastro-netizen/omnia2`.  
> **Numerazione = continuum di sessione** (non forzare allineamento al master).  
> Prompt master: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27) — corrispondenza in tabella sotto.

**Ultimo aggiornamento**: 28-Set-2026 · **P10 ACQUISITO** · **P11 Restore consegnato**

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
| P10 | Backup | §9 | 🟠 **ACQUISITO** · B-* |
| P11 | Restore | §10 | 🟠 Consegnato (feedback) |
| — | Cestino (blocco dedicato) | §6 | 🟡 parziale in P5 |
| — | Retention / GDPR… | §11–§14 | ⬜ prossimo naturale: **§11 Backup vs cestino** o §12 Retention |
| — | Osservabilità → report | §16–§27 | ⬜ |

Decisioni dominio (codice ⏳): **D-094**, **D-095**.

---

## Cluster già emersi (no P0–P3 finché Founder non apre §23)

1. **Media authorization** = P3.1 + P4.1 + M-01 → D-095  
2. **Mongo ⟷ blob lifecycle** = M-02…M-04 + L-05/L-06 → D-095  
3. **Proiezioni/jobs vs D-094** = E-* · J-01…J-04  
4. **AuthZ non uniforme** login→risorsa (P4)  
5. **Attività**: appartenenza aperta (non = Richieste)  
6. **Costo infra massimo / bak** = C-* + **B-01** (~31×) — €/GB all-in **non confermato**; listino **non** toccare  
7. **Disaster recovery incompleto** = Backup pesante + dump parziale + **nessun Restore** (R-*)  
8. **Trusted path tenant context** = domanda aperta P8 (bak = *nessun* tenant scope)  
9. **APScheduler in-process** = *area da verificare* — decisione orchestrazione **rimandata** post Backup+Restore design

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

## Punto 10 — Backup · **ACQUISITO** Founder (28-Set · master §9)

### Verdetto acquisito (linguaggio normale Founder)

| | |
|--|--|
| 🟢 | **Il backup esiste** (ogni giorno). |
| 🟠 | **Troppo pesante**: ricopia **tutto** ogni giorno (es. 100 GB → ~3.000 GB bak in 30g + i 100 live). |
| 🔴 | **Non salva ancora tutti i dati importanti** (es. richieste clienti, attività). |
| 🔴 | **Non c’è ancora il sistema per ripristinare** OMNIA da un backup → P11. |
| 🟠 | **Costo reale non ancora calcolabile con sicurezza.** |

### Quattro problemi principali (acquisiti)

1. **Backup incompleto** (CRM critico OUT) → **va sistemato** (quando si progetta).  
2. **Può partire due volte** (auto + manuale) → da controllare, non necessariamente disastro.  
3. **Prende anche trash/orphan** → migliorare quando si definisce il sistema definitivo.  
4. **Restore assente** → **punto più importante**; metà del lavoro manca.

### Risposte alle domande aperte P10

1. **€0,04/GB** → **NO, non confermare**. Non cambiare listino. Aspettare Backup+Restore design, poi i conti.  
2. **APScheduler vs esterno** → **non decidere ancora**. Prima capire bak + restore.

**Decisione operativa ora:** niente codice, niente listino. Finding **B-01…B-14** e **K-BAK-*** restano aperti.

---

## Punto 10 — dettaglio tecnico (riferimento)

### Verdetto tecnico (pre-acquisizione)

> Bak giornaliero esiste; full `copytree` ~31×; dump Mongo parziale; nessun restore path.

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

### Domande aperte P10 — **chiuse** dal Founder (vedi sopra)

1. €0,04 → non confermare; listino fermo.  
2. Orchestrazione → non decidere ancora.

---

## Punto 11 — Restore · consegnato 28-Set (master §10 · continuum sessione)

### Verdetto in linguaggio normale

**Domanda fondamentale Founder:**

> *«Se domani mattina perdiamo database e file, possiamo riportare OMNIA esattamente alla situazione di ieri?»*

**Risposta: NO** (al massimo un ripristino **parziale e manuale**, senza procedura né tool).

- Il backup del giorno esiste come cartella su disco.  
- **Non esiste** restore automatico (né API, né script, né CLI, né runbook ops).  
- Cap.19 / D-085 promettono «ripristino via supporto OMNIA», ma il supporto oggi **non ha un tool**: avrebbe solo JSONL + media da ricostruire a mano.  
- Anche a mano: dump Mongo **incompleto** → non si ricostruisce «OMNIA di ieri» in modo fedele (mancano richieste, attività, …; gruppi sbagliati; media Emergent fuori).

### Cosa esiste vs cosa manca

| Esiste | Manca |
|--------|--------|
| Bak giornaliero (scheduler + cron HTTP) | Qualsiasi `restore` disaster |
| JSONL whitelist + media local + MANIFEST | Playbook ops «disastro → passi 1…N» |
| Promessa Cap.19 / D-085 «via supporto» | Codice/tool che attua la promessa |
| Cestino self-service (`trash` restore) | ≠ disaster restore piattaforma/agenzia |

Commento in `backup_job.py` («Collections that restore an agency archive») = **intenzione**, non codice.

### Scenario disastro (oggi)

Operatore esperto *potrebbe* tentare: leggere MANIFEST → import JSONL → copiare `media/` su `LOCAL_STORAGE_ROOT` → riavvio.  
**Non testato, non automatizzato.** Rischi: giorno `ok=false` parziale; collisioni unique se DB non vuoto; `groups.jsonl` inutile; CRM fuori bak **perso**; Emergent = blob irrecuperabili; **no** restore singola agenzia sicuro (bak globale).

### Finding R-xx (no fix · no P0–P3)

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| **R-01** | gap | Nessun restore code path | **B-12** |
| **R-02** | rischio | Promessa «via supporto» senza tool | Cap.19 · D-085 |
| **R-03** | gap | Dump incompleto → restore incompleto | **B-02** |
| **R-04** | gap | `groups` ≠ `agency_groups` | **B-03** |
| **R-05** | rischio | Media Emergent OUT | **B-05** |
| **R-06** | rischio | Giorno `ok=false` comunque scritto | **B-09** |
| **R-07** | rischio | Collisioni unique su restore DB non vuoto | indexes users/agencies |
| **R-08** | gap | Bak globale → no restore single-agency sicuro | **B-13** |
| **R-09** | oss. | Trash/orphan nel bak = rumore + costo | **B-10** |
| **R-10** | oss. | Commento codice sovrastima capacità | `backup_job.py:22` |
| **R-11** | gap | No checksum / cifratura documentata | **B-06/B-07** |
| **R-12** | oss. | Cestino ≠ disaster restore | Cap.19 |

### Stima costo ops — 1 / 10 / 100 / 1.000 agenzie

**Onestà:** non c’è foglio costi hosting ufficiale nel repo. Ordini di grandezza da assunzioni P9/P10 — **non** conferma listino.

**Nota metodologica (Founder 28-Set):** nella prima consegna P11 Mongo era mescolato con “API” in un range grezzo — **andava separato prima**. Sotto: voce Mongo a sé (foto/video **non** stanno in Mongo).

#### Assunzioni

| Assumption | Valore |
|------------|--------|
| Mix piani | 50% Starter / 35% Pro / 15% Agency |
| Quota | 30 / 100 / 300 GB |
| Utilizzo medio vs quota | A 25% · B 50% · C 80% |
| Bak | full-copy ≈ **31×** live; live+bak ≈ **32×** |
| €/GB disco media (range grezzo) | **€0,02–0,08 /GB/mese** (≠ €0,04 D-085 confermato) |
| ARPU mix | ≈ **€104**/agenzia (`0,5×49 + 0,35×99 + 0,15×299`) |
| Mongo | Atlas (prod); locale in Cloud Agent ≈ €0 marginale |
| API / egress / LLM | **voci separate**; non nel dettaglio Mongo sotto |

#### Solo Mongo (Atlas — ordine di grandezza)

Dev/Cloud Agent = `mongod` locale ≈ €0. Prod target = Atlas (`DEPLOY_VERCEL.md` / D-*).  
Foto/video **fuori** Mongo → il DB cresce molto meno del media store.

| Tier Atlas (listino AWS tipico) | ≈ €/mese* |
|---------------------------------|-----------|
| M0 Free | €0 |
| Flex / shared | ~€9–€30 |
| M10 | ~€55–€60 |
| M20 | ~€140–€150 |
| M30 | ~€380–€400 |
| M40+ | ~€750+ |

\*USD listino convertito; regione/storage extra variano. Produzione HA a 3 nodi può avvicinarsi a **~3×** il singolo nodo — da verificare sul preventivo Atlas.

| Agenzie | Tier plausibile | Mongo ≈ / mese |
|---------|-----------------|----------------|
| **1** | Free / Flex o Mongo sulla VPS | **€0–€30** |
| **10** | M10 | **~€55–€180** (con HA) |
| **100** | M20–M30 | **~€150–€1.200** |
| **1000** | M30–M40+ | **~€400–€2.500+** |

**Lettura:** Mongo è costo a **scaglioni**, non “€ per GB di foto”. Il rischio margine a scala resta soprattutto **media + bak full-copy**, non Mongo.

GB live medi/agenzia (mix): A ≈ **22 GB** · B ≈ **44 GB** · C ≈ **70 GB**  
×32 live+bak: A ≈ **700 GB** · B ≈ **1,4 TB** · C ≈ **2,2 TB**

#### Ordine di grandezza €/mese

| N | Storage (A–C, €0,02–0,08) | + Mongo/API | Totale grezzo | Revenue mix (~€104×N) |
|---|---------------------------|-------------|---------------|------------------------|
| **1** | ~€14–€180 | ~€70–€230 | **~€80–€400** | ~€49–€299 (1 piano) |
| **10** | ~€140–€1,8k | ~€150–€500 | **~€0,3k–€2,3k** | ~€1,0k |
| **100** | ~€1,4k–€18k | ~€0,4k–€2k | **~€2k–€20k** | ~€10k |
| **1000** | ~€14k–€180k | ~€2k–€15k | **~€16k–€200k** | ~€104k |

Esempio: 100 agenzie × 1,4 TB × €0,04 ≈ **€5,6k/mese solo disco** a utilizzo medio.

#### I prezzi €49 / €99 / €299 hanno senso?

| Lettura | Verdetto |
|---------|----------|
| Uso basso (A) + disco economico + pochi Agency pieni | Margine **possibile** su Pro/Agency; Starter €49 **stretto** se riempie i 30 GB (~960 GB live+bak ≈ **€38** solo disco a €0,04 vs €49) |
| Uso medio/alto (B/C) + bak **31×** | A 100–1000 agenzie il disco può **mangiare** gran parte del canone; Agency 300 GB pieni ≈ 9,6 TB → **€190–€770/mese** solo disco a €0,02–0,08 — nel caso alto **> €299** |
| Bak incrementale (~1,2–3×) | Economics molto più difendibili; razionale €0,04 torna plausibile |
| Listino ora | **Non toccare** — prima design Backup+Restore, poi i conti |

**Sintesi:** i canoni possono funzionare come posizionamento se l’uso medio resta sotto quota **e** si riduce il moltiplicatore bak. Con full-copy attuale e Agency al tetto, l’economia storage **non** regge da sola.

### Decisioni da prendere / Domande aperte (max 2)

1. **Contratto restore:** disaster **piattaforma intera** vs **singola agenzia** «via supporto» (Cap.19) — oggi nessuno dei due è affidabile; quale è la promessa reale?  
2. Conferma metodo Founder: **chiudere design Backup+Restore** prima di qualsiasi conferma €/GB o cambio listino?

### Link

| Ref | Ruolo |
|-----|--------|
| **B-01 / C-04** | ~31× → pressione su ARPU |
| **B-02…B-05, B-12, B-13** | Incompletezza bak → incompletezza restore |
| **D-085** | Promessa ripristino via supporto; €0,04 non confermato |
| Cap.19 §19.10.2bis | Testo cliente |

### Prossimo

Su ok Founder: tipicamente **Backup vs cestino** (master §11) o **Retention** (§12).  
**Niente fix. Nessuna severità definitiva. Listino fermo.**
