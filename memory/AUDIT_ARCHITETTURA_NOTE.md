# Audit architettura SaaS — note Founder

> Un punto alla volta. **Niente codice** senza «vai» esplicito di implementazione.  
> **Nessuna classificazione P0–P3** finché non si completa l’audit.  
> SoT: GitHub `mcnicastro-netizen/omnia2`.  
> **Numerazione = continuum di sessione** (non forzare allineamento al master).  
> Prompt master: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27) — corrispondenza in tabella sotto.

**Ultimo aggiornamento**: 30-Set-2026 · **SoT** `docs/audit/OMNIA_AUDIT_STATE.md` · **P24 CHIUSO** · **P25** ⏳ analisi

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
| P11 | Restore | §10 | 🟠 **ACQUISITO** · **D-096** |
| P12 | Backup vs Cestino | §11 | 🟠 **ACQUISITO** · **D-097** · BC-* / T-* |
| P13 | Retention | §12 | 🟠 **ACQUISITO** · **D-098** · RET-* |
| P14 | GDPR / privacy | §13 | 🟠 **ACQUISITO** · **D-099** · G-* |
| P15 | Concorrenza / race | §14 | 🟠 **ACQUISITO** · **RC-*** · invite → **D-100** · jobs → **D-101** |
| P16 | Job asincroni (approfondimento) | §15 | 🟠 **ACQUISITO** · **JA-*** · **D-102** · **D-103** |
| P17 | Osservabilità | §16 | 🟠 **ACQUISITO** (Master State) · **O-*** · **D-105** bak health |
| P18 | API / Frontend | §17 | 🟢 **CHIUSO** · baseline · **D-106** · AF-05=GTM-01 min |
| P19 | Error handling | §18 | 🟢 **CHIUSO** · **EH-*** · **D-107** |
| P20 | Scalabilità | §19 | 🟢 **CHIUSO** · **SC-*** · **D-108** · SC-08=GTM-01 |
| P21 | Coerenza prodotto/tecnologia | §20 | 🟢 **CHIUSO** · **CT-*** · **D-109** · **D-110** |
| P22 | Casi limite | §21 | 🟢 **CHIUSO** · **EC-*** · **D-111** · **D-112** · D-094/D-106↑ |
| P23 | Debito architetturale | §22 | 🟢 **CHIUSO** · **AD-*** · **D-113** |
| P24 | Non una lista infinita | §24 | 🟢 **CHIUSO** · **NI-*** · classificazione **congelata** |
| P25 | Report finale A–K | §25 | 🟠 Consegnato · ⏳ analisi |
| — | Cestino (blocco dedicato) | §6 | 🟡 coperto in P5 + P12 + D-111 |
| — | Priorità P0–P3 | §23 | ⬜ **CLOSED** fino al «vai» |
| — | … | §26–§27 | ⬜ rituale opzionale dopo P25 |
| **GTM-01** | Demo Readiness / primo afflusso | **post-audit** | 🟠 **ACQUISITO** · **D-104** · in coda · **vincolo pre-~5000 email** |

Decisioni dominio (codice ⏳): **D-094** … **D-115**.  
P18–P24 chiusi · Programma pre-attivazione **APPROVATO** (D-115). SoT: Master §25bis + `OMNIA_PROGRAMMA_PRE_ATTIVAZIONE.md`.  
**Continuità SoT**: `docs/audit/OMNIA_AUDIT_STATE.md` (non riaprire decisioni fissate). · **Niente codice** senza «vai».

---

## Cluster già emersi (no P0–P3 finché Founder non apre §23)

1. **Media authorization** = P3.1 + P4.1 + M-01 → D-095  
2. **Mongo ⟷ blob lifecycle** = M-02…M-04 + L-05/L-06 → D-095 · **RET-02**  
3. **Proiezioni/jobs vs D-094** = E-* · J-01…J-04  
4. **AuthZ non uniforme** login→risorsa (P4)  
5. **Attività**: appartenenza aperta (non = Richieste)  
6. **Costo infra massimo / bak** = C-* + **B-01** (~31×) — listino fermo  
7. **Disaster recovery incompleto** = B-* · R-* → **D-096**  
8. **Cestino ≠ Backup** = BC-* / T-* → **D-097** (copy + trash-in-bak)  
9. **Retention incompleta** = RET-* (orphan ∞ · no offboarding · copy da allineare)  
10. **GDPR / privacy** = **G-*** (erase ≠ wipe · fascicolo/media · DPA · no DSAR export)  
11. **Trusted path / APScheduler** = **D-101** single-instance · **D-102** purge+blob da automatizzare · **D-103** no worker ora  
12. **Concorrenza / race** = **RC-*** · invite → **D-100**  
13. **Jobs deepen** = **JA-*** · J-* · **JA-02**/JA-03 in registro finale  
14. **Osservabilità** = **O-*** · **D-105** bak health minimo  
15. **GTM / Demo Readiness** = **GTM-01 ACQUISITO** · **D-104** — in coda; **obbligatorio prima delle ~5000 email**  
16. **API / Frontend** = **AF-*** · **D-106** · P18 CHIUSO · AF-05=GTM-01 min  
17. **Error handling** = **EH-*** · **D-107** · P19 CHIUSO  
18. **Scalabilità** = **SC-*** · **D-108** · P20 CHIUSO · SC-08=GTM-01  
19. **Coerenza prodotto/tecnologia** = **CT-***

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

→ **P12 Backup vs Cestino** (sotto).  
**Niente fix. Nessuna severità definitiva. Listino fermo.**

---

## Punto 11 — **ACQUISITO** Founder (29-Set) · **D-096**

P11 cambia la lettura del progetto, ma **non** implica fermarsi né cambiare listino subito.

### Decisioni fissate

1. **Restore: partire dalla singola agenzia**  
   Promessa commerciale: *«In caso di necessità, il supporto può ripristinare i dati dell’agenzia.»*  
   **Non** promettere oggi il ripristino dell’intera piattaforma.  
   Modello: **backup globale → possibilità di recuperare una singola agenzia**; restore completo piattaforma = procedura interna di emergenza (opzionale).  
   Riduce il rischio di sovrascrivere per errore dati di altre agenzie.

2. **Backup + Restore si progettano insieme** (**D-096**)  
   Sequenza corretta: **Backup → Restore → costi reali → eventuale revisione listino**.  
   Per ora: €49/€99/€299 **fermi** · quota storage **ferma** · €0,04/GB **non confermato** · nessun nuovo limite video.

3. **Insight chiave**  
   > *«Facciamo il backup» non significa ancora «i dati sono realmente recuperabili».*  
   Target di protezione:  
   **Agenzia A perde dati → scegliamo un backup valido → ripristiniamo → immobili, clienti, richieste, attività, documenti e media tornano coerenti.**  
   Non necessariamente automatico / con pulsante cliente: può essere **procedura interna supporto**, ma deve **esistere ed essere testabile**.

Finding **R-01…R-12** restano aperti. **Niente fix.**

---

## Punto 12 — Backup vs Cestino · consegnato 29-Set (master §11)

### Verdetto (linguaggio normale)

Sono **due macchine diverse** con lo **stesso numero magico (30 giorni)** — e questo confonde.

| | Cestino | Backup |
|--|---------|--------|
| Problema | «Ho cancellato per sbaglio» | «Abbiamo perso dati / disco / DB» |
| Chi agisce | Titolare in UI | Supporto OMNIA (promessa) |
| Cosa fa | Soft-delete → ripristina il **record** | Copia giornaliera JSONL+media |
| Cosa **non** fa | Non ricostruisce un’agenzia dopo un disastro | Non è il cestino; **non** ha ancora un restore tool |

Cap.19 lo dice già in una frase — ma Cap.3/4 ripetono «dopo 30 giorni **non si recupera più**» senza menzionare il bak. Stesso «30 giorni» su due sistemi = falsa equivalenza.

### Tabella confronto

| | **Cestino** | **Backup** | **Retention** (cenni · §12 futuro) |
|--|-------------|------------|-------------------------------------|
| Scopo | Undo delete accidentale | Disaster / guaio grave | Quanto restano le **copie** (live, trash, bak, orphan) e quando spariscono davvero |
| Self-service | Sì (`/app/trash`) | No (via supporto) | Policy + job, non UI agente |
| Entità | Solo `properties` + `clients` | Whitelist Mongo + `MEDIA_ROOT` | Tutte le copie incl. GDPR |
| Media blob | Soft-delete: **restano**; purge: **non** cancellati → orphan (D-095) | `copytree` di tutto (trash/orphan inclusi) | Cleanup blob + scadenza bak |
| Richieste / attività | **Fuori** cestino; client trash **non** archivia richieste (D-094 ⏳) | **OUT** del dump (`client_requests`, `activities`) | Da definire |
| Finestra | 30 gg (`TRASH_RETENTION_DAYS`) | 30 gg cartelle (`BACKUP_RETENTION_DAYS`) | Può differire da entrambe |
| Dopo «Elimina per sempre» | Record Mongo sparito; blob orphan; UI dice irrecuperabile | Copia può restare nel bak del giorno finché non scade | Domanda GDPR: quante copie restano? |

### Cosa fa oggi il codice (evidenza)

**Cestino — soft-delete**
- Immobile: `properties.py:536-550` → `$set` `deleted_at` / `deleted_by` (`soft_delete_fields`).
- Cliente: `clients.py:190-218` → stesso; **blocca** se immobili non-trashed collegati; **nessun** touch a `client_requests`.
- Helper: `shared/db/trash.py:14-44` — `TRASH_RETENTION_DAYS=30`; restore = `$unset deleted_at/deleted_by`.

**Cestino — UI restore / purge**
- Lista + restore + purge-now: `trash.py:59-141` — solo update/delete sul documento `properties`|`clients`.
- **Non** ripristina/cancella: richieste, attività, media blob, documenti esterni.
- Cap.3 (`03-immobili.md:324`) «Foto, documenti e dati restano insieme» = **vero in soft-delete** (refs restano sul doc); **non** è un restore dei blob (non erano mai stati tolti).

**Cestino — purge 30gg**
- `run_trash_purge` `trash.py:154-166`: `delete_many` su properties/clients con `deleted_at <= cutoff`.
- **Zero** chiamata a `delete_object` / cleanup media → orphan (gap D-095 / L-05·L-06 / J-04).
- Trigger: solo HTTP `POST /cron/trash/purge` (`cron.py:37-42`) — **non** in APScheduler (a differenza del bak 03:15). Docs «purge automatico» = fragile se nessuno chiama l’endpoint (J-03).

**Backup vs stato trash**
- Dump `find({}, …)` senza filtro trash → **record trashed IN bak** (`backup_job.py:54-61`, B-10).
- Media: `copytree` intero `MEDIA_ROOT` → blob di item in cestino / orphan **inclusi** finché su disco (`backup_job.py:67-74`).
- OUT: `client_requests`, `activities`, … (B-02) — quindi lo scenario Founder P11 «requests + activities coerenti» **non** è coperto dal bak attuale.

**Due path dopo perdita dati**

| Scenario utente | Path | Oggi |
|-----------------|------|------|
| Eliminato per sbaglio, ≤30gg, ancora in Cestino | UI Ripristina | Funziona (record + refs media) |
| «Elimina per sempre» / purge scaduto | Cestino chiuso | Cap.3/4: «non si recupera»; bak può ancora avere copia ~30gg — **ma restore tool assente** (R-01/R-02) |
| Disastro DB/disk / agenzia | Bak → restore supporto | Promesso Cap.19/D-085; codice restore **assente**; target Founder = **singola agenzia** (P11) ancora da costruire |

### Rischi di confusione prodotto/docs

1. **Stesso «30 giorni»** Cestino e Backup → sembra un solo sistema (Cap.3/4 vs Cap.19).  
2. Cap.3/4 / HAL `cestino.ripristinare`: «dopo 30gg **non si può più**» — omette che il bak *potrebbe* ancora avere una copia (e omette che il restore non esiste).  
3. Cap.19: distingue bene Cestino ≠ Backup (`19-impostazioni-agenzia.md:220-226`) ma promette ripristino supporto **senza tool** (R-02).  
4. Commento `backup_job.py:22` «Collections that restore an agency archive» = intenzione, non codice (R-10).  
5. Procedura Founder testabile (props+clients+**requests**+**activities**+docs+media) **non** allineata al dump attuale.

### Finding BC-xx / T-xx (no P0–P3 · no fix)

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| **BC-01** | confusione | «30 giorni» condiviso Cestino/Backup → falsa equivalenza prodotto | Cap.3/4 · Cap.19 · D-085 |
| **BC-02** | oss. | Due path distinti: empty-trash ≠ disaster restore | R-12 · master §11 |
| **BC-03** | oss. | Trashed/orphan **dentro** bak (costo + rumore restore) | B-10 · R-09 · K-BAK-06 |
| **BC-04** | gap prodotto | Cap.3/4 «irrecuperabile» dopo purge ignora bak (e gap tool) | Cap.3:326 · Cap.4:312 · HAL |
| **BC-05** | gap | Scenario supporto testabile (requests/activities/media) ≠ bake attuale | P11 dec.3 · B-02 · R-03 |
| **T-01** | gap | Restore cestino = solo `$unset deleted_at` (no cascade) | `trash.py:108-123` |
| **T-02** | gap | Purge cestino = solo hard-delete Mongo; **blob non toccati** | `trash.py:154-166` · D-095 |
| **T-03** | gap | Client trash **non** archivia richieste (D-094 ⏳); campo legacy `trashed_at` in migrate prefs | `clients.py:212-218` · `client_requests_service.py:288` |
| **T-04** | rischio | Purge cestino **non** schedulato in APScheduler (solo HTTP) | `cron.py:37` · J-03 |
| **T-05** | oss. | Soft-delete: media «tornano» perché non erano mai stati rimossi — non è un restore blob | Cap.3:324 · D-095 |

### Link

| Ref | Ruolo |
|-----|--------|
| **D-085** | Cestino separato; bak 30g + restore via supporto; linguaggio onesto |
| **D-094** | Trash ≠ status; client trash → richieste archiviate; codice ⏳ |
| **D-095** | Lifecycle blob indipendente; cleanup ⏳ |
| **B-*** / **R-*** | Bak incompleto · no restore tool · trash in bak |
| **J-03 / J-04** | Purge non automatico · no blob cleanup job |
| **P11 decisioni** | Agency-first restore · Bak+Restore insieme · procedura testabile · listino fermo |

### Domande aperte P12 — **chiuse** dal Founder → **D-097**

1. Copy «Elimina per sempre» → vedi acquisizione sotto.  
2. Trashed nel bak → **sì, restano** (almeno inizialmente).

---

## Punto 12 — **ACQUISITO** Founder (29-Set) · **D-097**

Due decisioni nette per evitare promessa commerciale ambigua.

### 1. «Elimina per sempre» ≠ «irrecuperabile in assoluto»

> **«Elimina per sempre» = il dato viene eliminato definitivamente dall’area operativa e non è più recuperabile dall’utente tramite il Cestino. In caso di grave incidente, il supporto può valutare un recupero da backup valido, se ancora disponibile.**

| Livello | Significato |
|---------|-------------|
| Cestino | Recuperabile **dall’utente** entro 30 giorni |
| Elimina per sempre | **Non** recuperabile dall’utente |
| Backup | Eventuale recupero **straordinario** via supporto, se bak valido ancora esiste |

Evita di promettere che ogni cosa cancellata sia sempre recuperabile.

### 2. Elementi nel Cestino possono restare nel backup

**Sì, almeno inizialmente.** Non introdurre «se è nel Cestino, non va nel bak».  
Il bak rappresenta una situazione recuperabile del sistema, non solo i dati «visibili».

Timeline acquisita:

```text
G1: soft-delete → Cestino
G1–G30: Cestino + backup possono contenerlo
G30: Cestino purge → fuori area operativa utente
Backup: può ancora avere copia fino a propria scadenza
Scadenza bak: anche quella copia scompare
```

→ Porta direttamente a **P13 Retention**: *per quanto tempo può sopravvivere un dato dopo «elimina per sempre»?* (Cestino / bak / media / chiusura agenzia — semplici).

Finding **BC-*** / **T-*** restano aperti. **Niente fix.**

---

## Punto 13 — Retention · consegnato 29-Set (master §12 · continuum sessione)

### Verdetto (linguaggio normale)

**Domanda Founder:** *Per quanto tempo può sopravvivere un dato dopo che l’utente lo ha «eliminato per sempre»?*

**Oggi — risposta onesta:**

| Dove | Dopo «elimina per sempre» / purge |
|------|-----------------------------------|
| Area operativa / Cestino | **Sparisce subito** (allineato D-097 #1) |
| Backup JSONL | Solo se un bak aveva già fotografato il record; i bak *nuovi* non lo hanno più |
| File/media | Spesso restano come **orphan** — **nessun GC**, vita potenzialmente **indefinita** |
| Cartelle bak media | Continuano a copiare l’orphan finché è su disco; cartelle scadono a ~**30 gg** bak |
| Supporto | **Può** valutare un bak valido — **non garantito**; tool restore assente (D-096) |

Quindi: **fuori dall’utente sì**; **sparito da ogni copia no**.

### Matrice retention oggi

| Area | Clock | Finestra | Dopo | Evidenza |
|------|-------|----------|------|----------|
| **Cestino** | soft-delete `deleted_at` | **30 gg hardcoded** (`TRASH_RETENTION_DAYS`) | hard-delete Mongo; blob **non** toccati | `shared/db/trash.py` · `trash.py` |
| **Backup** | cartella giorno bak | **`BACKUP_RETENTION_DAYS` env · default 30** | purge cartelle vecchie; trash/orphan inclusi | `backup_job.py` |
| **Media/blob** | upload / orphan da purge | **Nessun TTL / nessun GC** | orphan ∞ su disco (D-095 ⏳) | `objstore.py` · T-02 |
| **Agenzia chiusa** | — | **Assente** | no wipe / offboarding a cancel sub | billing webhook · no agency delete |
| **GDPR utente** | `POST /auth/me/erase` | immediato | wipe PII user; inventory agenzia **tenuto** | `erasure.py` |
| **Refresh token** | emissione | **7 gg** | cleanup opportunistico | `REFRESH_TOKEN_DAYS` |
| **Crediti / ledger / API keys** | — | **nessun TTL** | append-only / revoke flag | — |
| **Staging jobs** | create | `JOB_TTL_DAYS=30` **dichiarato ma non applicato** | solo reaper stale / delete manuale | `virtual_staging.py` |

Purge cestino automatico: **solo HTTP** cron — non in APScheduler (J-03 / T-04 / RET-03).

### Timeline esempio (allineata D-097)

| Giorno | Live Mongo | Cestino UI | Blob | Bak |
|--------|------------|------------|------|-----|
| G1 soft-delete | `deleted_at` | recuperabile utente | refs OK | notturno include record+media |
| G1–G30 | in trash | sì | sì | copia trash+media |
| G30+ purge* | hard-delete | no (D-097) | **orphan** | nuovi bak: no JSONL; media orphan sì |
| fino a scadenza bak | — | — | orphan | snapshot storici |
| dopo expiry bak + GC (oggi **no GC**) | — | — | oggi: **resta** | bak sparito |

\*Se qualcuno chiama `POST /cron/trash/purge`.

### Gap vs D-097

| Decisione | Oggi | Gap |
|-----------|------|-----|
| Copy: fuori Cestino; supporto MAY bak | Cap.3/4/HAL: «non si può più recuperare» assoluto | **RET-04** / BC-04 — copy da riallineare (docs, non codice ora) |
| Trash può restare in bak | Sì (comportamento attuale) | OK concettualmente; orphan ∞ rompe «poi gone» |
| Clock separati Cestino/bak/media/agenzia | Solo Cestino+Bak hanno numeri; media=∞; offboarding=∅ | K-RET sotto |

### Finding RET-xx (no fix · no P0–P3)

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| **RET-01** | confusione | Trash 30 hardcoded vs Bak env 30 — due clock, stesso numero | BC-01 |
| **RET-02** | gap | Purge = solo Mongo; blob orphan senza GC | D-095 · T-02 |
| **RET-03** | rischio | Purge cestino non schedulato | J-03 · T-04 |
| **RET-04** | gap prodotto | Copy «irrecuperabile» ≠ D-097 (support MAY) | Cap.3/4 · HAL |
| **RET-05** | gap | Nessun offboarding / wipe agenzia | D-085 residuo |
| **RET-06** | gap | GDPR erase = utente, non cliente CRM / agenzia | D-094 · erasure.py |
| **RET-07** | oss. | Orphan + bak daily → costo e vita copie | B-01 · B-10 · BC-03 |
| **RET-08** | gap | `JOB_TTL_DAYS=30` staging non applicato | Cap.9 |
| **RET-09** | gap | Audit/consent «N anni» senza job | A-022 |
| **RET-10** | oss. | Crediti/ledger/API keys senza scadenza retention | — |

### Decisioni da prendere (K-style · semplici · no implement)

1. **K-RET-01** — Allineare copy prodotto a D-097 (testo unico Founder).  
2. **K-RET-02** — Quattro numeri max: Cestino 30 · Bak 30 · Media orphan (grace?) · Agenzia chiusa (N gg o manuale v1).  
3. **K-RET-03** — Clock espliciti: soft-delete / hard-delete / giorno bak / chiusura agenzia.  
4. **K-RET-04** — Purge cestino deve diventare automatico/osservabile (lega P8).

### Domande aperte (max 2)

1. Dopo purge: i **blob orphan** — grace (0 / 7 / allineati al bak) o restano finché scade l’ultimo bak che li ha copiati?  
2. **Chiusura abbonamento/agenzia**: grace (30/90 gg) + wipe, o solo procedura legale/manuale v1?

### Link

**D-094** · **D-095** · **D-096** · **D-097** · BC-* · T-* · B-* · R-* · J-03/J-04

### Domande aperte P13 — **chiuse** dal Founder → **D-098**

1. Orphan WHEN (0/7/30) → **non fissare ora**; prima regola di percorso, timing col bak.  
2. Agency wipe auto → **no** in V1; procedura controllata.

---

## Punto 13 — **ACQUISITO** Founder (29-Set) · **D-098**

Attenzione: **non complicare** le decisioni prima del design definitivo del backup.

### 1. File orphan

Il problema non è scegliere subito 0 / 7 / 30 giorni.  
Il problema è: **oggi un file può restare sul disco anche quando il record che lo indicava è eliminato** (sostenibilità + pulizia storage).

Regola da portare avanti:

> **Un file non più referenziato dall’applicazione deve avere un percorso verso la cancellazione definitiva.**

Il **quando** lo decidiamo **insieme al design definitivo del backup**. Evitare di fissare ora i 7 giorni.

### 2. Chiusura dell’agenzia

Non fissare ancora cancellazione automatica aggressiva (Mongo + media + bak + fatture + obblighi conservazione + riattivazione + wipe).

Decisione provvisoria V1:

> **Chiusura agenzia = account disattivato + dati non operativi + procedura di retention/wipe da definire.**

Non promettere cancellazione immediata di ogni traccia.

### Conferma metodologica

Storage e backup vanno **progettati insieme**. Oggi: media→orphan→spazio; bak→copie→moltiplica spazio.  
Regola unica da costruire:

```text
dato creato → modificato → cancellato → Cestino → purge → backup → scadenza bak → cancellazione definitiva
```

Solo allora si sa quanto storage reale si paga.

**RET-01…RET-10** restano aperti. **Nessun fix.** → P14.

---

## Punto 14 — GDPR / Privacy · consegnato 29-Set (master §13 · continuum sessione)

**Ambito**: SaaS multi-tenant immobiliare IT · read-only · no fix · no P0–P3.  
**Non è consulenza legale**: distingue *tecnico* vs *validazione legale/DPO*.

### Verdetto (SaaS commerciale: quanto è difendibile oggi?)

**Parzialmente difendibile su superfici “account utente” e lead pubblici; non ancora difendibile come pacchetto SaaS B2B completo.**

Esiste un nucleo tecnico onesto: erase account (`POST /auth/me/erase`), consent log append-only, hard-gate su alcuni lead, privacy L1–L4 annunci, isolamento applicativo `agency_id`, checklist E-* in `SECURITY_CHECKLIST.md`.  
Manca il perimetro commerciale tipico go-live IT: informativa/cookie policy piattaforma, DPA/art.28, diritti accesso/portabilità/rettifica self-service, wipe cliente CRM e chiusura agenzia, AuthZ media sensibili (fascicolo vs `/api/media` pubblico), retention audit dichiarata ma senza job (A-022 / RET-09), third-party inventariato (fal / LLM / Resend / Stripe / Emergent storage) senza transfer map.

Per vendita Founders: **non** presentare OMNIA come “GDPR-ready end-to-end”. Presentare: *cancellazione account utente sì; inventory agenzia tenuta; procedura chiusura agenzia e diritti DSAR ancora da definire con legale*.

### Cosa esiste vs cosa manca (tabella diritti GDPR)

| Diritto | Esiste oggi? | Evidenza | Gap |
|---------|--------------|----------|-----|
| **Informativa / trasparenza** (art. 12–14) | 🟡 parziale | Modulistica `informativa_privacy` per *agenzia* (`modulistica/catalog.py`); Domain Sovereignty Policy; Cap.8 no Analytics default | **Nessuna** Privacy Policy / Cookie Policy piattaforma OMNIA in FE routes; B2B register senza `gdpr_consent` backend |
| **Consenso** (art. 6/7) | 🟡 | Hard: B2C register, contact, mutui lead, widget lead, domain lead/kit. Log `consent_events` | CRM cliente: flag `gdpr_consent` **non** hard-gate create; Cap.11 testo “non bloccante” **obsoleto** vs codice mutui hard; marketing consent separato = claim Cap.11, **campo assente** |
| **Accesso** (art. 15) | ❌ | Solo template legale *verso altri fornitori* (`gdpr_20`) | Nessun endpoint DSAR / “esporta i miei dati” utente o cliente |
| **Rettifica** (art. 16) | 🟡 | PATCH profilo / clienti / immobili via CRUD normale | Non inquadrato come diritto; no audit “rectification request” |
| **Cancellazione** (art. 17) | 🟡 | User erase + cestino cliente/immobile | Erase ≠ wipe CRM/agenzia; purge lascia orphan; bak può tenere copie (D-097); no agency wipe |
| **Limitazione** (art. 18) | ❌ | — | Assente |
| **Portabilità** (art. 20) | 🟡 Track B only | `GET /api/v1/leads/export` (agenzia→CRM esterno) | Non per interessato B2C/utente; template PDF è *lettera a fornitore*, non export OMNIA |
| **Opposizione / marketing** (art. 21) | 🟡 | Notification preferences PATCH | No marketing_consent distinto; no cookie banner (e oggi no tracker terzi default — aiuta) |

### Superfici dati sensibili

| Superficie | Cosa c’è | Rischio privacy |
|------------|----------|-----------------|
| **User account** | email, nome, phone, MFA, Google sub | Erase anonimizza + revoca sessioni; inventory agenzia **tenuta** (`erasure.py:17-19`) |
| **CRM clients** | PII + `fiscal_code` + notes + `gdpr_consent` | Soft-delete 30g → hard Mongo; blob N/A; D-094 richieste→archivio ⏳; **nessun** erase GDPR cliente |
| **Fascicolo** | CI venditore, atti, APE, visure — path `omnia/fascicolo/…` | Download API **auth+agency** (`fascicolo.py:276`); ma `GET /api/media/{path}` **pubblico senza auth** (`media.py:26-34`) → **D-095 / P3.1**: path≠secret |
| **Foto annuncio** | pubbliche by design | OK portale; L3/L4 escluse feed |
| **B2C private listings** | `contact_public` email/phone/WA gate | Erase withdraw+strip; detail espone canali se flag |
| **Lead / mutui / contact** | email/phone + consent log | Mutui hard-gate codice; Cap.11 docs drift |
| **API keys / Track B** | hash SHA-256, `api_usage_log`, leads widget | Erase revoca keys `created_by`; log/usage **senza TTL** (RET-10) |
| **Audit trails** | 10 coll. + `consent_events` | Claim retention Cap.18 / A-022 **senza job** (RET-09) |
| **Third parties** | fal.ai (foto staging), LLM Gemini, Resend, Stripe, Emergent objstore legacy | Nessuna mappa transfer / DPA sub-processor in repo |

### 1) User erase — cosa fa / non fa

**Endpoint**: `POST /auth/me/erase` (`auth.py:233-268`) — confirm `DELETE` + password (salvo OAuth); log `account_erasure`; clear cookie.

**Fa** (`erasure.py:14-129`):
- delete: favorites, saved_searches, notifications, password_reset_tokens, refresh_tokens
- delete lead: mortgage_leads, visura_orders, cloud_contact_leads, contact_leads (by email/uid)
- B2C listings: withdraw + strip owner/contact PII
- revoke api_keys `created_by`
- anonymize user (tombstone email, wipe PII, `is_active=False`, clear agency_ids)

**Non fa**:
- clienti CRM / richieste / attività / matches / publishing / fascicolo docs / properties **agenzia**
- `consent_events` (restano con email/user_id pre-erase se loggati prima)
- audit collections, api_usage_log, bak copies, media orphan
- wipe intera agenzia

Allineato docstring: *agency inventory kept*.

### 2) Consensi / policy / cookie

- `log_consent` → `consent_events` (`consent_log.py:14-42`) su register B2B (senza field gdpr), B2C register, contact, mutui, erase.
- Cookie = auth HttpOnly (+ CSRF); **nessun** CookieBanner / CookieConsent in FE.
- Cap.8: no Google Analytics default — riduce pressione cookie marketing.
- Informativa piattaforma OMNIA: **assente** come pagina prodotto (solo Domain Sovereignty + modulistica *per agenzia*).

### 3) Cliente CRM + D-094

- Campo `gdpr_consent` su Client (`client.py:56`) — UI checkbox; create **non** rifiuta se false.
- Delete = Cestino 30g (`clients.py:190-218`); purge hard Mongo (`trash.py:154-166`); **non** archivia richieste in codice (D-094 ⏳).
- Significato GDPR “cliente cancellato” = **ancora aperto** (D-094 fuori scope → qui).

### 4) Fascicolo vs media pubblici (D-095)

- Cap.7: fascicolo “utente esterno / pubblico: mai”.
- Serve blob: download gated; **passthrough** `/api/media` no-auth serve qualsiasi path incluso `omnia/fascicolo/…` se noto.
- Decisione D-095 codice ⏳.

### 5) Multi-tenant (link P3)

- Isolation **applicativa** sì: filtri `agency_id`, middleware inject `/api/app/*` (`tenant_middleware.py`, `tenant_guard.py` TENANT_COLLECTIONS).
- E2E / media AuthZ **no** (P3 sintesi: isolation sì · E2E no; cluster P3.1+P4.1+M-01→D-095).
- Job trusted cross-tenant OK by design (P8).
- Agenzia A **non** dovrebbe vedere CRM B via `/api/app` se route disciplina agency_id; eccezione rischio = media path pubblici + bug AuthZ non uniformi (P4).

### 6) DPA / data processor

- Unico cenno: residuo D-085 «testo contratto/DPA fine abbonamento con legale» (`DECISIONS.md` ~1434).
- **Nessun** DPA art.28, registro trattamenti, elenco sub-processor in repo.

### 7) Log / audit vs A-022

- Claim Cap.18 / A-022: 90gg / 365gg / 5 anni su coll. audit.
- Codice: indici su `consent_events`; **nessun** TTL/job archivio audit (RET-09).
- Crescita ∞ fino a policy reale.

### 8) B2C private listings PII

- Sentinel `_private_listings`; `contact_public` gated; contact form → inquiries.
- Erase withdraw+strip; PUBLIC_FIELDS nasconde owner crudo.

### 9) API keys / Track B

- Keys hash-only; scoped `agency_id`; leads export/ingest tenant-scoped.
- Usage log append-only no retention; erase revoca solo keys dell’utente.

### 10) Cross-border / third parties

- fal.ai (upload foto staging), Gemini via key Emergent/Google, Resend, Stripe, objstore Emergent legacy.
- **Nessuna** documentazione transfer UE/extra-UE / SCC in repo. → legale/DPO.

### 11) Accesso / portabilità / rettifica endpoints

- **No** `/me/export`, **no** DSAR client.
- Unico “export”: Track B leads (operativo B2B, non diritto interessato).

### 12) Gap: agency wipe vs user erase vs client trash

| Meccanismo | Target | Effetto | Copie residue |
|------------|--------|---------|---------------|
| **User erase** | persona/account | PII user wiped; inventory agenzia tenuta | bak, consent_events, audit, orphan media |
| **Client trash→purge** | record CRM | fuori operativo poi hard Mongo | richieste (oggi non archiviate auto), bak, no blob GC |
| **Agency close** | tenant intero | **Assente** (RET-05); Founder V1 = procedura controllata non auto-wipe | tutto resta finché non definito |

### Finding G-xx (no P0–P3 · no fix)

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| **G-01** | gap | Erase utente ≠ erase cliente CRM ≠ wipe agenzia | RET-06 · erasure.py · D-094 |
| **G-02** | rischio | Fascicolo sensibile raggiungibile via `/api/media` pubblico se path noto | D-095 · M-01 · media.py |
| **G-03** | gap | No Privacy/Cookie Policy piattaforma; B2B register senza gdpr_consent field | RegisterRequest · FE routes |
| **G-04** | gap | No endpoint accesso/portabilità/rettifica interessato | art.15/16/20 |
| **G-05** | gap | DPA / sub-processor / transfer map assenti (solo residuo D-085) | legale |
| **G-06** | drift | Cap.11 mutui “consent non bloccante” vs codice hard-gate | mutui.py:64-65 |
| **G-07** | gap | CRM `gdpr_consent` soft (no hard create); marketing_consent assente | client.py · Cap.11 |
| **G-08** | gap | Retention audit/consent dichiarata, job assente | A-022 · RET-09 |
| **G-09** | gap | Agency offboarding assente; V1 = procedura controllata (Founder P13) | RET-05 |
| **G-10** | oss. | consent_events / usage / ledger sopravvivono all’erase | erasure.py scope |
| **G-11** | oss. | Isolamento app OK; E2E media/AuthZ incompleto (P3) | tenant_guard · D-095 |
| **G-12** | oss. | Third parties (fal/LLM/Resend/Stripe) operativi senza inventario privacy | Cap.9 · shared/llm |

### Decisioni da prendere (K-style · semplici · prima del bak design)

1. **K-GDPR-01** — Ruoli: OMNIA = titolare (B2C) / responsabile (B2B CRM agenzia)? (legale)  
2. **K-GDPR-02** — V1 diritti: solo erase account + canale email DSAR, o anche export self-service?  
3. **K-GDPR-03** — Cliente CRM cancellato: trash+purge basta, o serve “anonimizza PII / mantieni storico”? (lega D-094)  
4. **K-GDPR-04** — Agency close V1: testo procedura (disable + non-operative + retention TBD) — **no** auto-wipe (già Founder)  
5. **K-GDPR-05** — Media: fascicolo **mai** su path pubblico (enforce D-095) — prima o insieme al bak?  
6. **K-GDPR-06** — Orphan WHEN: solo con design bak finale (già Founder P13)

### Domande aperte P14 — **chiuse** dal Founder → **D-099**

1. Founders DSAR → procedura assistita OK (non self-service bloccante).  
2. Fascicolo AuthZ → **prima** del backup.

---

## Punto 14 — **ACQUISITO** Founder (29-Set) · **D-099**

Non trasformare “GDPR-ready” in una montagna di funzionalità immediate.

### 1. Founders: email DSAR + erase + DPA

**Soluzione provvisoria**, non stato finale. Per i primi utenti: gestione assistita (richiesta email → verifica → export/risposta supporto → erase dove applicabile → DPA contrattuale).  
Self-service export **non** blocca i Founders; va in **roadmap prima di scala significativa**.  
Criterio: la procedura deve **esistere ed essere eseguibile**.

### 2. AuthZ fascicolo: prima del backup

**Sì.** `/api/media/...` raggiungibile se si conosce il path = problema di **accesso**, non di backup.

Sequenza adottata:

```text
1. Proteggere fascicolo / media sensibili
2. Sistemare cancellazione / orphan
3. Progettare Backup + Restore
4. Definire retention definitiva
5. Verificare costi
```

### Precisazione

Il finding fascicolo **non** significa che tutto OMNIA sia esposto: è specifico sul controllo di accesso a quei file.  
**G-01…G-12** restano aperti; non allargare oltre il verificato.

---

## Punto 15 — Concorrenza / Race Conditions · consegnato 29-Set (master §14)

**Tipo**: audit read-only · **nessun fix** · **no P0–P3**.  
**Contesto Founder P14 / D-099**: Founders GDPR provisional; fascicolo AuthZ **prima** bak; G-* aperti.

### Verdetto (dove può rompersi sotto uso reale)

Sotto uso reale (due agenti, doppio click, webhook retry, HTTP cron + APScheduler):

1. **TOCTOU edit/upload vs soft-delete** — PATCH/upload non chiudono atomicamente sul filtro `not_trashed` → scrittura su record appena cestino.  
2. **Sync / matching vs Trash** — già E/J + D-094 ⏳: fetch `status=active` **senza** `deleted_at`; non è un nuovo bug di lock, è la stessa lacuna di dominio sotto carico concurrent.  
3. **Backup stesso giorno** HTTP ↔ APScheduler (B-08) — nessun lock; `rmtree`+`copytree` sul path `YYYY-MM-DD`.  
4. **Stripe topup** — `applied_at` è check-then-act, non CAS → rischio doppio accredito su redelivery parallela.  
5. **Invite accept** — password overwrite su utente esistente (P4.2 / Cap.13) + status `pending→accepted` non atomico.  
6. **Multi-agency** — CRM core usa `optional_agency_id`; `/agencies/me*` ancora `agency_ids[0]`.

**Locked (onesto)**: wallet `debit_credits` e debit API-key con `$gte`+`$inc` atomici; restore/purge cestino usano filtro `in_trash()` (un vincitore, niente zombie); APScheduler `max_instances=1` **per processo**; dedup matching notifica `unique(request_id, property_id)`.

### Matrice scenari critici

| # | Scenario | Esito sotto race | Lock / difesa | Evidenza |
|---|----------|------------------|---------------|----------|
| 1 | Soft-delete + edit/publish | Edit può scrivere su trashed (TOCTOU); sync/publish ignorano trash | find `with_not_trashed` ma update **senza**; sync no filter | `properties.py:464-492` · `sync_engine.py:58-64` |
| 2 | Purge vs restore | Un vincitore (404 all’altro) — **OK** | `in_trash()` su restore e delete | `trash.py:117-141` · `154-166` |
| 3 | Double create prop/client | Duplicati possibili (no idempotency key; email/ref non unique) | index non unique | `properties.py:383-415` · `clients.py:69-81` · `connection.py:105-106` |
| 4 | Credit wallet debit | Wallet **locked**; staging può riddebitare se job ritenta; Kling su `agencies.credits_balance` parallelo | `find_one_and_update` `$gte` | `billing/routes.py:556-589` · `virtual_staging.py:471-487` · `micro_tour_video.py:473-498` |
| 5 | Publishing run-all overlap | Stesso processo: no overlap job; HTTP+scheduler **sì**; multi-replica **sì** | `max_instances=1` solo in-proc | `sync_engine.py:274-281` · `publishing.py:366-370` |
| 6 | Backup HTTP + APScheduler | Stesso giorno → race `rmtree`/`copytree` (B-08) | **assente** | `backup_job.py:38-73` · `cron.py:45-50` · `sync_engine.py:308-315` |
| 7 | Agency switch | Switcher OK su tenant helper; `/agencies/me*` ignora `active_agency_id` | misto | `tenant.py:12-17` · `agencies.py:120-172` |
| 8 | Invite accept password | Overwrite password utente esistente **by design**; doppio accept non CAS | check `status!=pending` poi update | `invites.py:225-284` · Cap.13:249-254 |
| 9 | MFA / refresh | Refresh **non** ruota (riuso jti OK); backup code RMW race | store jti; no rotation | `auth.py:316-345` · `session_store.py` · `mfa_routes.py:196-208` |
| 10 | Upload media + delete prop | Upload **non** filtra trash; blob su prop cestino / orphan | find solo `id+agency` | `properties.py:587-636` |
| 11 | Matching vs trash | Match su `status=active` anche trashed (D-094 ⏳) | dedup notifica OK | `client_requests_service.py:454-457` · `request_matching_job.py:179-181` |
| 12 | Stripe webhook vs sub | Sub update last-write-wins OK; topup **non** CAS su `applied_at` | commento “idempotent” fragile | `billing/routes.py:366-447` · `498-510` |

### Finding RC-xx

| ID | Tipo | Problema | Evidenza |
|----|------|----------|----------|
| **RC-01** | rischio | PATCH property: read not_trashed → write senza filtro (TOCTOU vs soft-delete) | `properties.py:464-492` |
| **RC-02** | rischio | Upload foto su prop senza `with_not_trashed` (+ race vs delete) | `properties.py:587-636` |
| **RC-03** | gap* | Sync portali / match: no `deleted_at` (D-094 ⏳ · già J-01/J-02/E-*) | `sync_engine.py:61` · `client_requests_service.py:454-457` |
| **RC-04** | ok | Restore vs purge hard: filtri `in_trash()` — race benigna | `trash.py:117-141` |
| **RC-05** | rischio | Create property/client non idempotenti; no unique `(agency,email)` / `reference_code` | `properties.py:415` · `clients.py:81` · `connection.py:105-106` |
| **RC-06** | ok+gap | Wallet `debit_credits` atomico (**locked**); API adjust RMW; Kling wallet separato su `agencies` | `routes.py:567-571` · `api_keys.py:196-204` · `micro_tour_video.py:473-498` |
| **RC-07** | rischio | Staging: debit post-success senza guard `credits_charged` → ritento = doppio addebito | `virtual_staging.py:471-487` |
| **RC-08** | rischio | Publishing: `max_instances=1` ≠ lock vs HTTP `/sync/run-all` / multi-pod (P8) | `sync_engine.py:274-281` · `publishing.py:366-370` |
| **RC-09** | rischio | **B-08** backup: nessun lock HTTP↔scheduler; stesso `BACKUP_ROOT/day` | `backup_job.py:41-73` · note P10 |
| **RC-10** | drift | `/agencies/me*` = `agency_ids[0]`; resto = `active_agency_id` | `agencies.py:120-172` · `tenant.py:12-17` |
| **RC-11** | gap | Invite accept overwrite `password_hash` (P4.2); accept non CAS su status | `invites.py:246-284` |
| **RC-12** | oss. | Refresh senza rotation (no race invalidazione); MFA backup code RMW | `auth.py:339-344` · `mfa_routes.py:199-208` |
| **RC-13** | rischio | Stripe `_apply_session_side_effects`: check `applied_at` → grant → set (TOCTOU) | `billing/routes.py:372-447` |
| **RC-14** | oss. | `customer.subscription.updated` last-write-wins — accettabile v1 | `routes.py:498-510` |

\*RC-03 non è “nuova race di locking”: è D-094 non applicato, che sotto concorrenza produce sync/email su immobile cestino.

### Link P8 · B-08 · D-094 · crediti · trash

| Area | Collegamento |
|------|----------------|
| **P8 / J-*** | Orchestrazione aperta; `max_instances=1` in-process; HTTP cron parallelo; multi-replica = doppio scheduler |
| **B-08** | Conferma: race bak HTTP↔APScheduler (e multi-replica) |
| **D-094** | Trash ≠ status; codice ⏳ → RC-03 / J-01 / J-02 |
| **Crediti** | `credit_wallets` atomico; ledger senza unique su `ref_id`; API-key wallet distinto; Kling su `agencies.credits_balance` |
| **Trash** | Soft-delete/restore helpers OK; purge solo HTTP (J-03); blob orphan = D-095 |

### Decisioni Founder su P15 — **ACQUISITO** → **D-100** · **D-101**

#### 1. Backup/sync: single-instance (non lock complessi) — **D-101**

> **Una sola istanza responsabile dei job automatici**, finché non c’è un vero worker.

Evita due server che eseguono lo stesso bak/sync. **Non** infrastruttura sofisticata multi-pod ora.  
**Non definitiva**: a crescita servirà anti-duplicato condiviso.  
RC-08/RC-09 restano aperti; **non** blocco immediato.

#### 2. Invite: cambiare comportamento — **D-100** (fix-needed)

**Non** mantenere overwrite password utente già registrato.

| Caso | Comportamento |
|------|----------------|
| Utente **non** esistente | Creazione account + credenziali |
| Utente **già** esistente | Invito/collegamento agenzia + login/accettazione · **mai** modificare password esistente |

Evita che un admin agenzia cambi (anche involontariamente) le credenziali di chi ha già un account.  
**Da correggere**, non solo miglioramento futuro (P4.2 / RC-11).

#### 3. Tier RC (utile per priorità)

| Tier | Esempi | Azione |
|------|--------|--------|
| 🔴 Da correggere | Password overwrite / mutazione dati non prevista | Fix-needed (**D-100**) |
| 🟠 Da rendere robusti | Bak doppio, sync/match vs cestino | Aperti; single-instance mitiga parte |
| 🟢 Già buono | Wallet atomico · restore/purge cestino | Tenere |

**Non** trasformare ogni RC-01…RC-14 in fix immediato.

### Prossimo

→ **Punto 16** Jobs approfondito (sotto) · tipicamente poi osservabilità (§16 master).  
**Niente fix ora** (D-100 attende «vai»). Listino fermo.

---

## Punto 16 — Job asincroni (approfondimento post-P15) · consegnato 29-Set (master §15)

**Tipo**: audit read-only · **nessun fix** · **no P0–P3**.  
**Contesto**: P8 J-01…J-12 aperti; Founder single-instance per job automatici; deepen reliability.

### Verdetto (con decisione single-instance Founder)

Con **una sola replica API** per i job automatici, il rischio “due APScheduler = doppia esecuzione” è **mitigato operativamente**, non chiuso architetturalmente (`max_instances=1` resta **per-processo** — `sync_engine.py:274-337`).  
**Restano fragili anche a 1 istanza**: race HTTP cron ↔ scheduler (🟠 RC-08/RC-09 / B-08), purge cestino **mai** schedulato (J-03), D-094 non applicato in sync/match (J-01/J-02/RC-03), fallimento a metà senza ledger/DLQ, invite overwrite password (🔴 RC-11 → **D-100** fix-needed).  
Multi-pod = **critico solo allora** per anti-duplicato condiviso; RC restano aperti senza blocco immediato.

### Inventario aggiornato

| ID | Trigger | Single-instance? | Note |
|----|---------|------------------|------|
| `publishing_daily_sync` | APSched 06:00 UTC | **sì** (auto) | `max_instances=1`+coalesce · HTTP `/publishing/sync/run-all` parallelo | `sync_engine.py:274-282` · `publishing.py:366-370` |
| `saved_searches_frequent` | APSched `*/5` | **sì** | + HTTP `/cron/saved-searches/run-all` · include fav drop/ended | `sync_engine.py:291-298` · `saved_searches.py:289` · `cron.py:20-25` |
| `archive_daily_backup` | APSched 03:15 | **sì** | + HTTP `/cron/backup/daily` · path giorno senza lock | `sync_engine.py:308-315` · `backup_job.py:38-93` · `cron.py:45-50` |
| `request_matching_nightly` | APSched 02:30 | **sì** | + HTTP `/cron/requests/matching` + agency `/requests/run-matching` | `sync_engine.py:330-337` · `cron.py:28-34` · `client_requests.py:175-182` |
| Purge trash | **solo HTTP** | n/a (manca auto) | `/cron/trash/purge` · **non** in APScheduler | `cron.py:37-42` · `trash.py:154-166` |
| Geocode / lead email | `create_task` | request-bound | fire-and-forget; no durable queue | `geocoding.py:81-104` · `public_portal.py:1045-1094` |
| Staging / video / XML import | BackgroundTasks / `create_task` | request-bound | job doc Mongo; staging reap on boot | `virtual_staging.py:728` · `micro_tour_video.py:301,507` · `properties_import.py:539` |
| Staging reaper | lifespan startup | once/boot | marca stale failed | `server.py:69-72` · `virtual_staging.py:499-510` |

**Garanzia single-instance necessaria**: i 4 job APScheduler globali (+ qualsiasi futuro purge/blob).  
**Request-bound**: geocode, email lead, staging, video, XML URL import — scoped alla richiesta; restart può orphanare task in-flight (staging ha reaper).

### Cosa rimane fragile anche con 1 istanza

1. **HTTP ↔ APScheduler** sullo stesso entrypoint (bak/sync/match/saved-search) — nessun lock file/DB (`backup_job.py:41-73`; RC-09 🟠).  
2. **Purge zero volte** se nessuno chiama HTTP (J-03 / T-04).  
3. **D-094 nei job**: `_fetch_properties` e `match_request` = `status=active` senza `deleted_at` (`sync_engine.py:61`; `client_requests_service.py:454-457`); fav drop idem (`saved_searches.py:431-434`); matching client senza check trash (J-11). Compliance UI **sì** filtra trash (`publishing.py:340-343`) — drift vs sync.  
4. **Mid-job**: bak continua collection-by-collection, `ok=False` + MANIFEST, solo log (`backup_job.py:54-90`); sync ha `publishing_sync_logs` per connection ma **nessun** run ledger; matching **email/inbox prima** di `_mark_notified` (`request_matching_job.py:109-163`) → crash mid → possibile re-email.  
5. **Shutdown**: `stop_scheduler(wait=False)` (`server.py:108-109` · `sync_engine.py:346-353`) — abort senza checkpoint.  
6. **Osservabilità**: logger + report return HTTP; no metriche/alert dedicati job health (area §16).

### Cosa diventa critico solo multi-pod

- Due processi = due AsyncIOScheduler → doppio bak/sync/match/saved-search.  
- `max_instances=1` **non** cross-process.  
- Anti-duplicato condiviso (lease Mongo/Redis o worker unico) — **RC aperti, non blocco ora** (Founder).

### Finding JA-xx (nuovi) + link J-* / RC-*

| ID | Tipo | Problema | Link | Evidenza |
|----|------|----------|------|----------|
| **JA-01** | oss. | Single-replica mitiga doppio scheduler; **non** chiude HTTP↔sched overlap | RC-08 · RC-09 · B-08 | `sync_engine.py:274-337` · `cron.py` · `publishing.py:366-370` |
| **JA-02** | rischio | Matching: side-effect email/inbox **prima** del mark dedup → mid-crash = possibile doppia email | J-02 · J-11 | `request_matching_job.py:109-163` |
| **JA-03** | gap | Nessun run ledger / DLQ / checkpoint per bak·sync·match; solo log + MANIFEST/`PortalSyncLog` | J-05 · area P8 | `backup_job.py:45-90` · `sync_engine.py:67-92` |
| **JA-04** | gap | Purge+blob ancora fuori APScheduler; single-instance **non** crea il job mancante | J-03 · J-04 · T-04 · D-095 | `cron.py:37-42` · vs bak `sync_engine.py:308-315` |
| **JA-05** | drift | Compliance sync filtra trash; `_fetch_properties` del job **no** | J-01 · RC-03 · D-094 | `publishing.py:340-343` vs `sync_engine.py:58-64` |
| **JA-06** | gap | Gap vs worker futuro: no coda, no lock condiviso, no job-table globale, cron ancora JWT `super_admin` | J-06 · P8 area | `cron.py:17` · `server.py:64-65` |
| **JA-07** | fix-needed* | Invite accept overwrite password utente esistente — **D-100** | RC-11 · P4.2 | `invites.py:246-254` |

\*JA-07 non è “job”, citato qui per D-100 da feedback P15 (Founder: MUST change).

**Overlap intervallo**: APSched `max_instances=1`+`coalesce=True` evita overlap *stesso job stesso processo*. Sync retry sleep max ~36 min su cron giornaliero → OK. Saved-search `*/5` coalesce salta tick persi. Critico resta **secondo trigger HTTP** mentre il job gira.

### Domande aperte (max 2) — **RISOLTE** Founder

1. **K-JA-01 → SÌ schedulare ora** — purge + blob cleanup nel ciclo automatico (→ **D-102**). Non aspettare il worker.  
2. **K-JA-02 → NO worker dedicato ora** — resta **D-101** (1 replica → APScheduler). Eventuale anti-duplicato minimo stesso-giorno OK; worker quando il deploy lo richiede (→ **D-103**).

### Decisioni Founder su P16 — **ACQUISITO** → **D-102** · **D-103**

#### 1. Purge + blob: automatizzare ora — **D-102**

> Non lasciare una pulizia necessaria senza un processo automatico.

Convergenza graduale: **Cestino → purge → cleanup orphan** nel ciclo automatico OMNIA.  
Allinea **D-098** (orphan → path a delete). Non richiede sistema sofisticato subito — richiede che purge non resti solo HTTP (`cron.py:37-42`).

#### 2. Lease vs worker — **D-103** (conferma D-101)

**Non** introdurre worker dedicato solo per P16.  
Eventuale meccanismo minimo anti doppia esecuzione stesso giorno (job delicati) — non infrastruttura da 1000 agenzie.  
Worker = decisione quando l’architettura di deployment lo richiederà.

#### 3. Evidenze da registro

| ID | Nota Founder |
|----|----------------|
| **JA-02** | Più importante di quanto sembri: email **prima** del mark → mid-crash = possibile re-email. Tenere nel registro finale. |
| **JA-03** | Nessun ledger/DLQ/checkpoint — registro finale. |
| **D-101** | Confermata: risolve il problema principale della fase attuale, non pretendere di risolvere l’architettura futura. |
| **D-100** | Resta fix-needed. |

**Niente fix. Nessuna severità P0–P3. Listino fermo.**

### Prossimo

→ **Punto 17** Osservabilità (sotto). Particolarmente rilevante per Bak/Restore: non basta che il bak parta — sapere se è riuscito, incompleto, se serve intervento.

---

## Punto 17 — Osservabilità · consegnato 29-Set (master §16)

**Tipo**: audit read-only · **nessun fix** · **no P0–P3**.  
**Focus Founder**: Backup/Restore — sapere se bak riuscito / incompleto / serve intervento.

### Verdetto

Esiste un **nucleo utile** (health/readiness, Sentry opzionale + webhook/email, `ops_alerts` → Founder Ops, sync logs per-connection, MANIFEST filesystem).  
**Non** esiste un controllo operativo chiaro su successo/fallimento backup, né heartbeat dei job APScheduler, né Prometheus/OTel, né alert unificati per i job schedulati.  
Per Bak/Restore: oggi si sa che *qualcosa* ha scritto file e log; **non** si sa in UI/API/alert se l’ultimo bak è OK, parziale o fallito e se qualcuno deve intervenire.

### Inventario (cosa c’è)

| Area | Stato | Evidenza |
|------|-------|----------|
| Logging | stdlib testo piano; no JSON/request-id | `server.py:44-48` |
| Sentry + webhook/email | opzionale; init fail-soft; rate-limit | `shared/monitoring/alerts.py` · env `SENTRY_*` / `ERROR_ALERT_*` |
| `AlertLoggingHandler` | **definito, non installato** sul root logger | `alerts.py:143-159` |
| Exception HTTP → `notify_error` | sì | `server.py` global handler |
| `ops_alerts` Mongo | sì; UI Founder Ops ultimi 20; **no ack API** | `ops_alerts.py:16-40` · `founder_ops.py:398-426` |
| Chi chiama `ops_alerts` | HAL Agents/Legal, Stripe — **non** bak/sync/sched | grep chiamanti |
| Health | `GET /api/health` ping Mongo ma **sempre 200**; circuits snapshot | `server.py:191-211` |
| Readiness | checklist go-live incl. `monitoring_configured` | `server.py:214-251` |
| Sub-health | `/api/app/health` ecc. spesso **senza** DB | `immoweb/routes.py:48` |
| Backup status | solo `MANIFEST.json` + `logger.info`; tick swallowa → WARNING | `backup_job.py:38-93` · `sync_engine.py:300-306` |
| Sync portal | `publishing_sync_logs` + API per-connection | `sync_engine.py:67-92` · `publishing.py` |
| Job heartbeat / last_run | **assente** | — |
| Metrics RED/USE / `/metrics` | **assente** (no Prom/OTel) | — |
| Restore da bak | **assente** (restore = solo Cestino) | D-096 ⏳ |
| Founder Ops UI | COGS + ops_alerts LLM/Stripe; **no** bak/job panel | `FounderOpsPage.jsx` |
| Storage cliente | `GET /storage/usage` quota agenzia | D-085 |
| Disk bak / integrità | **assente** in ops | — |
| Audit prodotto | disperso (`privacy_audit`, `al_audit`, …) | Cap.18 note |
| Audit ops (chi ha lanciato cron/bak) | **assente** | — |

### Cosa serve per Bak (e oggi manca)

| Bisogno | Oggi |
|---------|------|
| Esito ultimo bak (ok / partial / fail) queryable | Solo filesystem MANIFEST + stdout |
| Alert se job non gira o fallisce | Assente (`ops_alerts` non usato; tick cattura e fa WARNING — niente Sentry/`notify_error`) |
| Incomplete vs ok (collection vs media) | Nel report in-memory/MANIFEST sì; **nessun surfacing** |
| “Needs intervention” + ack | Nessuno stato operativo; `acked` in schema senza endpoint |
| Heartbeat 03:15 vivo | Nessun `last_run` in DB |
| Restore status | Restore bak assente (D-096) |

### Finding O-xx

| ID | Tipo | Problema | Link | Evidenza |
|----|------|----------|------|----------|
| **O-01** | gap | Bak: nessun stato persistito/API/alert oltre MANIFEST+log → impossibile sapere successo/incomplete/intervento | B-* · JA-03 · focus Founder | `backup_job.py:38-93` |
| **O-02** | rischio | `_daily_backup_tick` swallowa errori → solo WARNING; niente Sentry/`ops_alerts` | JA-01 area | `sync_engine.py:300-306` |
| **O-03** | gap | Nessun restore da backup; “restore” = solo Cestino | D-096 · R-* | note P11 |
| **O-04** | gap* | Purge trash solo HTTP — **D-102** da automatizzare (non solo osservabilità) | JA-04 · J-03 · D-098 | `cron.py:37-42` |
| **O-05** | gap | Nessun heartbeat / `last_run` / `last_error` dei 4 job APScheduler | JA-03 · J-05 | `sync_engine.py:274-337` |
| **O-06** | drift | `AlertLoggingHandler` definito ma non wired al root logger | monitoring | `alerts.py:143-159` |
| **O-07** | gap | Nessun Prometheus / OTel / `/metrics` | master §16 | — |
| **O-08** | gap | `ops_alerts.acked` senza endpoint ack; UI read-only | Founder Ops | `founder_ops.py:403-424` |
| **O-09** | gap | `ops_alerts` non copre bak / sync massiva / scheduler / disk | O-01 · O-02 | `ops_alerts.py` chiamanti |
| **O-10** | oss. | Health globale non degrada HTTP su DB error (sempre 200; `db: error` nel body) | readiness vs liveness | `server.py:191-211` |
| **O-11** | oss. | `/api/app/health` non pinga Mongo (falso “verde” di processo) | — | `immoweb/routes.py:48` |
| **O-12** | drift | `BACKUP_ROOT` / `BACKUP_RETENTION_DAYS` assenti da `.env.example` | B-* | `.env.example` vs `backup_job.py` |
| **O-13** | gap | Founder Ops = COGS/LLM/Stripe, non job/bak/storage infra | O-01 · O-05 | `FounderOpsPage.jsx` |
| **O-14** | gap | Logging non strutturato; no correlazione request-id | — | `server.py:44-48` |
| **O-15** | gap | Sync portal: log per-connection OK; manca alert aggregato “N sync failed today” | J-* · publishing | `publishing_sync_logs` |

\*O-04 è gap di **orchestrazione** (D-102), citato qui perché senza job automatico non c’è neanche osservabilità del purge.

### Lettura Founder (stessa logica: solido / rischioso / decidere / aspetta)

| Classe | Cosa |
|--------|------|
| **Già solido** | Health + readiness go-live; Sentry/webhook/email opzionali; `notify_error` su exception HTTP; `ops_alerts` + UI Founder Ops (LLM/Stripe); sync portal `publishing_sync_logs` per-connection; MANIFEST scrive ok/partial; quota storage cliente |
| **Realmente rischioso** | **O-01/O-02**: bak fallisce in silenzio (WARNING only) — non sai se intervenire; **O-05**: nessun `last_run` → job “morto” invisibile; **O-09**: ops_alerts non copre bak/sched |
| **Da decidere** | — (K-O risolte → **D-105**) |
| **Può aspettare** | O-07 Prom/OTel; O-14 structured log/request-id; O-08 ack API; O-10/O-11 nuance health; O-12 `.env.example`; O-15 alert sync aggregato |

\*O-03/O-04 = restore/purge (D-096/D-102).

### Domande aperte — **RISOLTE** (Master State §11 → **D-105**)

1. **K-O-01 → minimo**: ultimo bak OK / PARTIAL / FAILED + data/ora + alert — non dashboard complessa.  
2. **K-O-02 → riusare** `ops_alerts` / `ERROR_ALERT_*`. Heartbeat/`last_run` job necessario. Prom/OTel attendono.

**P17 ACQUISITO** via Master Audit State. → **P18** sotto.

---

## GTM-01 — Demo Readiness / capacità primo afflusso · **ACQUISITO** 30-Set (**D-104** · **A-036**)

**Stato**: 🟠 **ACQUISITO** · **in coda** (non altera il percorso audit) · analisi **dopo** i punti principali.  
**Vincolo vincolante**: **prima delle ~5.000 email deve essere eseguito il checkpoint Demo Readiness.**

**Motivo**: ~5000 email outreach possono diventare rapidamente un test reale di OMNIA. Non dimensionare per 5000 utenti contemporanei — verificare il **picco** e il **percorso demo**.

### Rischio da evitare

> La demo interessa, ma quando arrivano le prime ~20 persone contemporaneamente OMNIA fa una brutta figura.

### Cosa *non* è

- Non = dimensionare OMNIA per 5000 utenti concurrent.  
- Non = costruire subito tutto per 200 clienti.  
- Non = aspettare 200 clienti paganti per scoprire i buchi.

### Distinzione picco vs volume

| Cosa | Cosa verificare |
|------|-----------------|
| Invio 5.000 email | infrastruttura email / provider |
| Richieste demo | form, notifiche, registrazione lead |
| 10–50 demo | capacità operativa del team |
| Accessi contemporanei | server / API / database |
| Upload foto/video | storage + performance |
| Demo con dati reali | isolamento tenant |
| Errori | logging + alert (**O-***) |
| Primo impatto | nessun errore evidente o funzione rotta |

Scala commerciale tipica: 2 demo = tranquillo · 50 = gestibile · 200 = da preparare · ~20 concurrent su funzioni chiave = **must hold**.

### Non solo capacità tecnica

Una demo fallisce anche con server OK se: pulsante rotto, pagina 15s, 500, immagine mancante, leak tenant, invite che altera password (**D-100**), demo agency dati incoerenti, job non aggiorna, upload fail, scaffold mascherato da feature.  
Questi gap emergono già dall’audit tecnico (RC-* · JA-* · O-* · M-* · …).

### Quattro domande checkpoint (post-audit)

1. **2 richieste demo** — tutto deve funzionare senza problemi.  
2. **50 richieste** — OMNIA + processo commerciale gestiscono.  
3. **200 richieste** — non obbligo 200 demo subito; evitare rottura sistema / perdita lead.  
4. **Clienti paganti** — processi fondamentali pronti: tenant, utenti, dati, storage, backup, sicurezza, billing, supporto.

### Pratica obbligata prima delle 5000 email

**“Demo sotto stress”** (non laboratorio sofisticato):  
nuova agenzia → admin → agente → immobili → foto → documenti → cliente → richiesta → matching → pubblicazione → logout/login → recupero → …  
= il percorso che si mostra ai prospect deve essere **solido**.

Collegamenti: seed `demo-agency-001` · A-025 (⏸) · stress scripts esistenti · finding audit già aperti.  

### Piano

- Percorso audit **invariato**: continuità via `docs/audit/OMNIA_AUDIT_STATE.md`.  
- **GTM-01 resta in coda** dopo i punti principali.  
- **Hard gate**: niente lancio ~5000 email senza checkpoint Demo Readiness eseguito.  
**Niente analisi GTM-01 ora. Niente fix. Listino fermo.**

---

## Punto 18 — API / Frontend · consegnato 30-Set (master §17)

**Tipo**: audit read-only · **nessun fix** · **no P0–P3**.  
**SoT continuità**: `docs/audit/OMNIA_AUDIT_STATE.md`.  
**Ambito**: coerenza FE ↔ API ↔ BE per percorso demo/commerciale — senza ripetere P1–P17.

### Verdetto

Nucleo demo (login cookie+CSRF, onboarding, CRM shell/role gate, matching, publishing, trash, billing catalog) **coerente** su mount/routing (`/api/app` ↔ `/:lang/app/*`, cloud, Track B `/api/v1`).  
Si spezza su: **D-100** ancora vivo nel contratto FE; **drift multi-agency** (`/agencies/me` = `agency_ids[0]` vs `active_agency_id` nei list CRM); **liste immobili senza paginazione UI**; upload foto silenziosi; pezzi B2C fuori dal client API shared.

### Lettura Founder

| Classe | Cosa |
|--------|------|
| **Già solido** | Mount chiaro; lang + `ProtectedRoute` + role aliases; axios cookie+CSRF+refresh 401; fascicolo visura gated; ErrorBoundary; i18n IT/EN/ES con test parità chiavi; OpenAPI off in prod |
| **Realmente rischioso** | **AF-01** D-100 invite FE+BE; **AF-02** `/api/media` pubblico (D-095); **AF-03** switcher vs `/agencies/me`; **AF-04** properties >20 invisibili; **AF-05** PhotoUploader silent; **AF-06** B2C URL raw; **AF-07** sessione unica B2B/B2C bleed |
| **Da decidere** | **K-AF-01** allineare `/me` o nascondere switcher; **K-AF-02** flusso FE D-100 oltre fix server |
| **Può aspettare** | Nav hardcoded IT; a11y row-click; Academy; OpenAPI `0.1.0`; KPI coming soon; esign mock etichettato |

### Finding AF-xx

| ID | Tipo | Problema | Link | Evidenza |
|----|------|----------|------|----------|
| **AF-01** | fix-needed* | Invite accept overwrite password; FE chiede sempre password | **D-100** · RC-11 | `invites.py:246-254` · `AcceptInvitePage.jsx:50,137-150` |
| **AF-02** | rischio | `GET /api/media/{path}` senza auth | **D-095** · G-02 · M-01 | `media.py:26-34` · `server.py:272-274` |
| **AF-03** | drift | Switcher setta `active_agency_id`; `/app/agencies/me*` usa `agency_ids[0]` (CRM list usa `require_agency` OK) | RC-10 | `agencies.py:120-172` · `tenant.py:12-17` · `AgencyShell.jsx` |
| **AF-04** | gap | Properties: API pagina 20; FE **non passa `page`** / no controlli → stock >20 invisibile in demo | GTM | `PropertiesPage.jsx:59,74-84` |
| **AF-05** | gap | PhotoUploader: catch vuoto, nessuna toast/413 (VideoUploader sì) | GTM upload | `PhotoUploader.jsx:86-102` |
| **AF-06** | drift | B2C Valuator/Checkout/PropertyCard: `REACT_APP_BACKEND_URL` grezzo ≠ `api.js` same-origin / CSRF | — | `ValuatorPage.jsx:19-24` · `api.js:10-12` |
| **AF-07** | rischio | Sessione unica B2B/B2C; login default → `/app/dashboard`; onboarding può promuovere client→admin | — | `LoginPage.jsx:36-39` · `agencies.py:50-98` |
| **AF-08** | oss. | Billing UI senza gate `plans.enabled`; checkout 503 se Stripe off sembra “live” | — | `BillingPage.jsx:31-35` · `billing/routes.py:35-47` |
| **AF-09** | gap | Error UX non uniforme: interceptor solo 401; Matches senza catch; 403 statico | — | `api.js:66-93` · `MatchesPage.jsx:29-36` |
| **AF-10** | perf | Match agency-wide scan pesante; SellPage 1+N `/stats` | — | `matches.py:71-99` · `SellPage.jsx:83-104` |
| **AF-11** | gap | Requests: stato `page` senza UI next/prev | — | `RequestsPage.jsx:68-84` |
| **AF-12** | oss. | Nav CRM: molte voci hardcoded IT | — | `AgencyShell.jsx:103-114` |
| **AF-13** | oss. | Versioning asimmetrico: CRM `/api/app` non versionato; solo `/api/v1` Track B | — | `server.py:118-126` |
| **AF-14** | rischio | CORS default `*` + credentials se `CORS_ORIGINS` assente | readiness | `server.py:128-141` |
| **AF-15** | oss. | a11y demo: row-click senza keyboard; aria miste | — | `RequestsPage.jsx:272` |
| **AF-16** | oss. | Fascicolo nasconde visura se off (bene); Modulistica mock esign etichettato | — | `FascicoloPage.jsx` · `ModulisticaPage.jsx` |

\*AF-01 = **D-100** (fix-needed, attende «vai»).

### Domande aperte — **RISOLTE / AFFINATE** Founder (osservazioni P18)

1. **K-AF-01 → D-106**: `active_agency_id` = SoT sessione; `agency_ids` = membership; **non** nascondere switcher.  
2. **K-AF-02**: tre stati invite (new / existing+auth esistente / expired-consumed); **contratto server prima**, poi FE; niente magia FE. Estende **D-100**.

### Nota decisionale P18 (pre-implementazione · nessun codice)

* SoT `active_agency_id` (**D-106**) — priorità tra fix FE/API.  
* Formalizzare tre stati invite (**D-100**).  
* Boundary media esplicito (file / enumerate / upload / mutate / associazione) — **D-095**; FE non forzato a URL pubblici per asset autenticati.  
* AF-04 pagination / AF-05 upload stato `pending→success/error` / error UX = **debito non bloccante** (AF-04/05 rilevanti demo).  
* B2C: stessa astrazione API del FE (**AF-06**).  
* Documentare se sessione B2B/B2C unica è deliberata (**AF-07**) — separato da “default → CRM”.  
* **Nessun nuovo P0–P3** da P18.

### Baseline P18 — **CHIUSO** Founder

D-106 · K-AF-02 (server→FE, 3 stati) · AF-02 boundary media · AF-04 debito demo · **AF-05 = GTM-01 min** (`pending→success/error`+retry, non P0) · AF-06 unica API · AF-07 sessione da chiarire.  
**Nessun nuovo P0–P3. Nessun codice.**

---

## Punto 19 — Error handling · consegnato 30-Set (master §18) · ⏳ analisi Founder

**Verdetto:** superficie utente decentemente protetta sui path “caldi” (auth, staging, form save con `formatApiErrorDetail`); operatori hanno `notify_error` + `ops_alerts` ma **non** sui tick job critici. Fail mid-demo tipici: upload foto silenzioso, match list = empty, invite “ok” senza email.

### Solid

| Area | Evidence |
|------|----------|
| Global 500 → i18n + `notify_error` | `server.py:312-329` |
| Auth lockout/disabled i18n | `auth.py:185-203` · `locales/it.json:13-14` |
| 401 refresh single-flight | `api.js:34-93` · `auth.jsx:59-64` |
| 403 page ProtectedRoute | `ProtectedRoute.jsx:36-45` |
| ErrorBoundary nested | `ErrorBoundary.jsx` · `App.js` |
| Staging errori job/UI | `virtual_staging.py:354-359` · `StagingStudio.jsx:532-534` |
| Sync portal retry + log | `sync_engine.py:196-227` |

### Risky / debito

| ID | Tipo | Problema | Link | Evidence |
|----|------|----------|------|----------|
| **EH-01** | debito | `detail` misto (i18n / code / object) | AF-08 area | auth `t(...)` vs CRM snake_case vs billing `{error,message}` |
| **EH-02** | gap | No handler 422 custom | — | solo `@exception_handler(Exception)` |
| **EH-03** | debito+oss. | PhotoUploader silent | **AF-05** | `PhotoUploader.jsx:86-102` |
| **EH-04** | debito demo | Matches no catch → empty | AF error UX | `MatchesPage.jsx:29-36` |
| **EH-05** | rischio | Job swallow WARNING | **O-02** · JA | `sync_engine.py:288-328` |
| **EH-06** | rischio | Email soft-fail | JA-02 area | `email/client.py:155-157` · invite `invites.py:110-123` · match `request_matching_job.py:115-127` |
| **EH-07** | gap | Geocode/Resend non user-visible | O-* | `geocoding.py:72-78` · circuit mock |
| **EH-08** | oss. | Billing load silent | **AF-08** | `BillingPage.jsx:36-39` |
| **EH-09** | gap | No request-id; AlertLoggingHandler unwired | **O-14** · **O-06** | `server.py:44-48` · `alerts.py:143-159` |
| **EH-10** | oss. | Liste CRM fail→empty | AF-04 area | `PropertiesPage.jsx:74-87` · `ClientsPage.jsx:231-234` |
| **EH-11** | solid* | Pattern buoni (vedi sopra) | — | — |
| **EH-12** | gap | No retry UX generale | — | solo 401 + sync BE |

### Domande — **RISOLTE** Founder

1. **K-EH-01 → D-107**: BE `code` stabile + `detail` diagnostico; FE i18n.  
2. **K-EH-02**: feedback utente se il fallimento altera il significato dell’azione; toast non obbligatorio come unico mezzo.

### Baseline P19 — **CHIUSO** Founder

EH-03=GTM-01 · EH-04 empty≠error · EH-05 job state≠log level · EH-06 op≠email delivery · **D-107** · feedback semantico (K-EH-02). Differiti: request-id/422/retry/geocode.  
**Nessun nuovo P0–P3. Nessun codice.** → **P20** sotto.


---

## Punto 20 — Scalabilità (master §19) · CONSEGNATO ⏳

**Vincoli non riaperti:** D-101 single-replica jobs · D-103 no worker ora · B-01 bak ~31× · GTM-01 ~20 concurrent (non 5000).

### Verdetto

Per **GTM (~20 concurrent)** il monolitico single-replica regge **in verticale** sulle liste CRM paginate; i colli demo sono **Match on-read**, **media via API/FS**, **AF-04**.  
Per **crescita 200–1000 agenzie** falliscono prima storage+bak, media locale e job globali — non il “mancano N worker HTTP”. Orizzontale API **non** pronto (FS + scheduler in-process).

### Dimensioni (separati)

| Dimensione | Cosa regge | Cosa si rompe prima |
|------------|------------|---------------------|
| **GTM ~20 concurrent** | properties/clients list API; KPI; JWT cookie; rate limit pubblico; job nightly non in picco demo | Match 400×400; N upload+serve media sullo stesso processo; FE stock>20 (AF-04) |
| **~50 agenzie** | stesso modello se inventario medio e 1 replica | bak disco (B-01); saved-search 5m cross-tenant; feed 5k; sync publishing sequenziale |
| **200–1000 agenzie** | richiede storage condiviso(+CDN), anti-dup job già deciso al multi-pod, match non on-read full-scan | FS non condiviso; doppio APScheduler se multi-replica; copytree bak; tick saved-search |

### Finding SC-*

| ID | Tipo | Problema | Link | Evidence |
|----|------|----------|------|----------|
| **SC-01** | oss. | 1 uvicorn + APScheduler in lifespan; stack `--reload` no workers | D-101 · D-103 · JA-01 | `server.py:51-65` · `sync_engine.py:258-337` · `omnia-stack.sh:147-148` |
| **SC-02** | rischio crescita | `.media` locale; `get_object` legge tutto in RAM; serve via `/api/media` | M-* · C-09 | `objstore.py:34-118` · `media.py:26-59` |
| **SC-03** | rischio eco | Bak `copytree` + dump ≤100k/coll → ~31× | B-01 · C-04 | `backup_job.py:38-77` |
| **SC-04** | rischio demo/load | Match agency 400×400; property/client scoped 2000; no_match smart 400×400 | — | `matches.py:71-79,125-128,197-199` · `properties.py:284-288` · stress ~5,8s |
| **SC-05** | gap | No index `deleted_at`; `with_not_trashed` `$or` | trash | `trash.py:19` · `connection.py:97-116` |
| **SC-06** | gap | `rate_limit_events` index solo in stress script | — | `rate_limit.py:37-56` vs `ensure_indexes` |
| **SC-07** | oss. | Motor senza `maxPoolSize` esplicito | — | `connection.py:54` |
| **SC-08** | debito demo | Properties FE no `page` / no next | **AF-04** | `PropertiesPage.jsx:59,74-84` |
| **SC-09** | rischio crescita | Saved-search ogni 5m su tutte le active | A-020 · JA | `sync_engine.py:283-297` · `saved_searches.py:299-300` |
| **SC-10** | rischio ops | HTTP cron ↔ sched overlap; coalesce solo in-proc | JA-01 · B-08 · RC-09 | `sync_engine.py:274-337` · `publishing.py:366-370` |
| **SC-11** | rischio crescita | Feed pubblico ≤5000 full docs | C-09 | `feed.py:44-50` |
| **SC-12** | oss. | Access JWT + `users.find_one` ogni request | — | `dependencies.py:18-28` · `session_store.py` |
| **SC-13** | rischio crescita | `run_all_active_syncs` sequenziale ≤1000 conn | J-* | `sync_engine.py:230-250` |
| **SC-14** | oss. | API page_size capped (prop ≤100); FE gaps | AF-04 · AF-11 | `properties.py:150-151` |
| **SC-15** | rischio demo | Upload+serve media sullo stesso event loop | AF-05 · EH-03 | `properties.py:573-637` · `media.py:26-59` |

### Domande — **RISOLTE** Founder

1. **K-SC-01 → smoke load GTM dedicato** ~20 concurrent (upload+media+match+combo) = **confidence gate GTM-01** (non P0–P3); stress ladder resta baseline.  
2. **K-SC-02 → soglia su capacità/traffico media** (due dimensioni), non solo n. agenzie; object storage+CDN **separato** da worker (**D-103**).

### Baseline P20 — **CHIUSO** Founder

* SC-02/15: OK GTM se assunto; **non** horizontal-ready.  
* SC-03: limite operativo; bak **non** scala automaticamente col n. agenzie.  
* SC-04: match costoso **non** via GET accidentale.  
* **SC-08/AF-04 = GTM-01**.  
* **SC-10 → D-108**: un solo owner di scheduling.  
**Nessun nuovo P0–P3. Nessun codice.** → **P21** sotto.

---

## Punto 21 — Coerenza prodotto/tecnologia · consegnato 30-Set (master §20 · continuum sessione)

**Ambito**: dove promesse prodotto / UI / docs / listino divergono dal comportamento reale del codice. Nessun fix. Nessun P0–P3. Decisioni D-094…D-108, GTM-01, baseline P18–P20 **non riaperte**.

### Verdetto

Nucleo CRM (quota D-085, Cestino, Match, publishing feed-pull, widget Valuator/Mutui, `GET /billing/plans`) allineato. Drift forte su **superficie commerciale pubblica** (landing listino morto), **promesse DR** (restore via supporto senza tool), **invite D-100**, **gate Stripe/demo localStorage**, Track B staging documentato ma 501, Founder Ops senza bak health.

### Finding CT-01…CT-14

| ID | Tipo | Problema | Link | Evidenza |
|----|------|----------|------|----------|
| **CT-01** | drift commerciale | `/it/agenzie` prezzi/quote Founders-50 morti | listino v3 · plans.py | `AgenziesLandingPage.jsx:12-61` |
| **CT-02** | gap enforcement | max_properties / max_agents solo catalogo+UI | C-01 · D-085 | `plans.py:38-75` · grep BE = solo plans/Billing |
| **CT-03** | promessa vs codice | Bak 30g + ripristino supporto — no restore tool | **D-096** · R-02 · D-085 | Cap.19:220 · `backup_job.py:22` |
| **CT-04** | copy vs policy | Cap.3/4 «non recuperabile» assoluto | **D-097** · BC-01 | Cap.3:326 · Cap.4:312 |
| **CT-05** | scaffold live | E-sign mock default, flusso UI operativo | D-042 | `esign.py:56-79` · `ModulisticaPage.jsx:170-176` |
| **CT-06** | gate commerciale | Stripe 503; demo unlock via localStorage | D-080 | `billing/routes.py:35-47` · `BillingPage.jsx:83-110` |
| **CT-07** | doc vs API | Staging Track B Cap.20/26 vs 501 + widget lead-only | Cap.20 · Cap.26 | `gateway.py:469-476` · `staging.html:51-72` |
| **CT-08** | rischio prodotto | Sessione B2B/B2C + promote client→admin | AF-07 | `LoginPage.jsx:36-39` · `agencies.py:94-98` |
| **CT-09** | fix-needed (già D-100) | Invite overwrite password; FE sempre chiede password | **D-100** · AF-01 | `invites.py:246-254` · `AcceptInvitePage.jsx:137-150` · Cap.13:249-254 |
| **CT-10** | marketing vs tetto | Agency ∞ immobili; PRICING_OMNIA senza riga GB | **D-085** | `PRICING_OMNIA.md:28-32` · Cap.19:221 |
| **CT-11** | ops vs decisione | Founder Ops senza bak health / last_run | **D-105** · O-01/O-13 | `founder_ops.py` (no backup) · `FounderOpsPage.jsx` |
| **CT-12** | GDPR copy | Erase UI vs scope solo user (no CRM wipe) | **D-099** · G-01 | `SecuritySettingsPanel.jsx:228` · `erasure.py` |
| **CT-13** | catalogo | setup_stripe ommette storage_100gb | C-13 · D-085 | `setup_stripe.py:70-86` |
| **CT-14** | oss. | Publishing coming_soon onesto; KPI locked residuo | — | `publishing.py:49-113` · `KPICard.jsx:47-53` |

### Domande — **RISOLTE** Founder

1. **K-CT-01 → D-109**: `GET /billing/plans` = SoT; landing allineata dinamicamente **oppure** ritirata/nascosta; Founders-50 solo se **esplicitamente legacy**.
2. **K-CT-02**: hard enforcement BE di `max_properties`/`max_agents` **solo** se entitlement GTM reali; altrimenti non simulare (storage **D-085** resta tetto tecnico).

### Baseline P21 — **CHIUSO** Founder

* **CT-01 / K-CT-01 → D-109**: una sola fonte autorevole per pricing; legacy esplicito.
* **CT-03**: bak esistente ≠ verificato ≠ restore disponibile ≠ restore testato; marketing/UI/Ops ≤ capability reale (**D-096**).
* **CT-06 → D-110**: demo mode esplicito sì; `localStorage` ≠ entitlement authority.
* **CT-09**: **D-100** decisione **trasversale** (contratto invite unico).
* **CT-11**: operatività → **D-105** bak health osservabile in Founder Ops.
* **K-CT-02**: enforcement BE solo per entitlement commerciali definiti.
**Nessun nuovo P0–P3. Nessun codice. Listino fermo.** → **P22** sotto.

---

## Punto 22 — Casi limite · consegnato 30-Set (master §21)

**Ambito**: happy + unhappy path che rompono demo SaaS o multi-tenant safety. Nessun fix. Nessun P0–P3. Non riaprire D-094…D-110 / GTM-01 / P18–P21 (solo link). Baseline P21 chiusa: **D-109** pricing SoT; bak≠restore; **D-110** localStorage≠entitlement; **D-100** trasversale; **D-105** bak health.

### Verdetto

Percorsi felici Cestino (restore/purge), limiti upload+quota, feed pubblico trash-aware, reject invite scaduto/revocato, empty properties, clear `active_agency_id` su remove-member tengono. Rotture reali demo/safety: **match/sync/smart senza `deleted_at`**, **client trash + matching email**, **invite overwrite + accept non atomico**, **SoT agency spezzata**, **JWT utente disabilitato**, **seed demo che riaggancia membership**.

### Finding EC-01…EC-15

Vedi tabella in `docs/audit/OMNIA_AUDIT_STATE.md` §23. Sintesi gruppi:

**Già mitigato:** restore→404 post-purge; feed+compliance `with_not_trashed`; size/quota upload; `..` su media; invite expired/revoked codes; empty UI properties; `optional_agency_id` fallback; storage addon Stripe-off messaggio.

**Rischio latente:** EC-04/06/08/09/10/11/12/14/15.

**Demo-critical:** EC-01, EC-02, EC-03, EC-05, EC-07, EC-13.

### Domande — **RISOLTE** Founder

1. **K-EC-01 → D-094 rafforzato**: uniforme pre-GTM su match/sync/smart; filtro = proprietà del dominio (default non-trashed; trash opt-in).
2. **K-EC-02 → D-111**: **freeze** (Cestino = non operativo); preserva dati/storico; `active → frozen` sulle richieste.

### Baseline P22 — **CHIUSO** Founder

* **EC-01 → D-106↑**: nessun fallback `agency_ids[0]`; missing/invalid = errore.
* **EC-02 / K-EC-01 → D-094↑**: invariante dominio uniforme pre-GTM.
* **EC-03 / K-EC-02 → D-111**: freeze nuove ops; storico preservato.
* **EC-05**: D-100 invariato (contratto invite unico).
* **EC-07**: D-110 invariato.
* **EC-13 → D-112**: seed idempotente/deterministico.
**Nessun nuovo P0–P3. Nessun codice. Listino fermo.** → **P23** sotto.

---

## Punto 23 — Debito architetturale · consegnato 30-Set (master §22)

**Ambito**: classificare debito OK / Monitorare / Migliorare / Critico (senza rewrite automatiche). Nessun fix. Nessun P0–P3. Non riaprire D-094…D-112 / GTM-01 / P18–P22 (solo link).

### Verdetto

Debito = lock-in intenzionali incompleti (FS, bak full-copy, single-replica) + drift accidentali (SoT agency, invite, trash, AuthZ media). Pre-GTM: SoT + fascicolo + invite + D-094/D-111 + bak health + onestà commerciale — non S3/worker/OTel.

### Finding AD-01…AD-16

Vedi tabella in `docs/audit/OMNIA_AUDIT_STATE.md` §24.

| Classe | Cosa |
|--------|------|
| **Già gestito** | D-101/103/108 · listino fermo · D-094/111 · D-097/098 · D-104 · D-112 |
| **Pre-GTM** | AD-05 · AD-08 · AD-09 · AD-10 · AD-12 · AD-13/14 · AD-03 onestà · GTM-01 min |
| **Post-GTM OK** | AD-01 storage · AD-02 bak incr. · AD-07 worker · OTel · wipe · DSAR |
| **Da decidere** | K-AD-01 · K-AD-02 |

### Domande — **RISOLTE** Founder

1. **K-AD-01 → D-113**: D-105 + linguaggio onesto + **restore manuale testabile** pre-GTM (non piattaforma DR; non “restore garantito” commerciale).
2. **K-AD-02**: FS + 1 replica = baseline GTM deliberata; trigger object storage/CDN = **fallimento smoke media** (K-SC-01 / GTM-01).

### Baseline P23 — **CHIUSO** Founder

* AD-05: AuthZ fascicolo senza anticipare AD-01 (separa storage / endpoint / AuthZ / associazione).
* AD-08/09/10: invarianti → implementare sui percorsi, non mega-cleanup.
* AD-12/13/14: stato dichiarato = stato reale (D-105/D-110/D-109).
* Pre-GTM da chiudere vs accettabile (vincolo dichiarato) — vedi Master State §24.
**Nessun nuovo P0–P3. Nessun codice. Listino fermo.** → **P24** sotto.

---

## Punto 24 — Non una lista infinita · consegnato 30-Set (master §24)

**Ambito**: distinguere problema reale · rischio potenziale · miglioramento opzionale · preferenza architetturale. Dire cosa è corretto. **§23 Priorità non aperto.** Nessun fix. Nessun P0–P3.

### Verdetto

Pochi drift ripetuti + lock-in intenzionali incompleti. D-094…D-113 filtrano già. Non ogni ID di §14 è priorità uguale. Monolite/AuthN/tenant CRM base OK per la fase.

### Classificazione NI-01…NI-12

Vedi `docs/audit/OMNIA_AUDIT_STATE.md` §25. Sintesi: **reale pre-GTM** = NI-01…07 (+ D-113); **potenziale** = NI-08/09; **opzionale/post** = NI-10/11; **OK** = NI-12.

### Domande — **RISOLTE** Founder

1. **K-NI-01**: report finale / GTM-01 ora; **§23 Priorità CLOSED** fino al «vai».
2. **K-NI-02**: distinzione ripago **congelata** (Master §25bis).

### Baseline P24 — **CHIUSO** Founder

* P24 = classificazione finale, **non** ricalcolo severità.
* NI-08/09 restano potenziale; NI-12 = OK fase (non eternità).
* Metodologia: P24 non modifica severità/listino/priorità congelate; implementazioni solo al «vai».
**Nessun nuovo P0–P3. Nessun codice. Listino fermo.** → **P25** sotto.

---

## Punto 25 — Report finale · consegnato 30-Set (master §25)

**Ambito:** formato A–K. Nessun fix. Nessun P0–P3. §23 CLOSED. Classificazione P24 congelata.

Vedi `docs/audit/OMNIA_AUDIT_STATE.md` §26 (A–K) e §25bis (SoT ripago).

### Domande

1. **K-RF-01**: acquisire P25 come CHIUSO continuum, o ancora §26/§27?
2. **K-RF-02**: prossimo = GTM-01 (dopo/accanto ripago), o stop fino a nuovo «vai»?

**Niente fix. Nessuna severità P0–P3. Listino fermo. Attende «vai».**

