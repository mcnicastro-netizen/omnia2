# Audit architettura SaaS — note Founder

> Un punto alla volta. **Niente codice** senza «vai» esplicito di implementazione.  
> **Nessuna classificazione P0–P3** finché non si completa l’audit.  
> SoT: GitHub `mcnicastro-netizen/omnia2`.  
> **Numerazione = continuum di sessione** (non forzare allineamento al master).  
> Prompt master: `memory/AUDIT_PROMPT_MASTER.md` (§1–§27) — corrispondenza in tabella sotto.

**Ultimo aggiornamento**: 28-Set-2026 · **P8 ACQUISITO** · **P9 Storage e costi consegnato**

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
| P9 | Storage e costi | §8 | 🟠 Consegnato (feedback) |
| — | Cestino (blocco dedicato) | §6 | 🟡 parziale in P5 |
| — | Backup / Restore / Retention… | §9–§14 | ⬜ prossimo naturale: **§9 Backup** |
| — | Osservabilità → report | §16–§27 | ⬜ |

Decisioni dominio (codice ⏳): **D-094**, **D-095**.

---

## Cluster già emersi (no P0–P3 finché Founder non apre §23)

1. **Media authorization** = P3.1 + P4.1 + M-01 → D-095  
2. **Mongo ⟷ blob lifecycle** = M-02…M-04 + L-05/L-06 → D-095  
3. **Proiezioni/jobs vs D-094** = E-* · J-01…J-04  
4. **AuthZ non uniforme** login→risorsa (P4)  
5. **Attività**: appartenenza aperta (non = Richieste)  
6. **Costo infra / margine piano** = C-* (P9) · backup full-copy · Agency ∞ immobili  
7. **Trusted path tenant context** = domanda aperta P8 (approfondire su backup/restore/sync/cleanup)  
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

## Punto 9 — Storage e costi · consegnato 28-Set (master §8 · continuum sessione)

### Verdetto (bozza)

> Esiste un **tetto commerciale** sul volume archivio B2B (D-085: tier GB + meter + blocco **413** + addon €15/100 GB) e tetti per-immobile (foto/video/planimetrie).  
> Il **costo infra reale per cliente non è ancora prevedibile end-to-end**: `max_properties` è catalogo non enforced; il backup fa **full `copytree`** di tutto `.media` × retention 30g (~moltiplicatore fino a ~31× sul live); **nessun** metering bandwidth/CDN; B2C e alcuni path legacy sfuggono al contatore.  
> Con Agency «∞ immobili» + video, il rischio di pressione sul margine del canone è reale se il backup resta full-copy.

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

### Domande aperte (max 2)

1. Il Founder conferma ancora ~**€0,04/GB/mese** come costo all-in, sapendo che il codice fa **full daily copytree** (non bak “smart”)?  
2. Su Agency video-heavy: resta **solo freno storage** (D-085) o serve anche un tetto soft su n° video/agenzia oltre i 3/immobile?

### Prossimo

Su ok Founder: tipicamente **Backup** (master §9) — chiarirà anche orchestrazione job periodici (P8) e moltiplicatore costo (C-04).  
**Niente fix. Nessuna severità definitiva.**
