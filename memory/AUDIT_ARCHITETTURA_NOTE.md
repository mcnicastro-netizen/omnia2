# Audit architettura SaaS — note Founder

> Un punto alla volta. **Niente codice** senza «vai» esplicito di implementazione.  
> **Nessuna classificazione P0–P3** finché non si completa l’audit.  
> SoT: GitHub `mcnicastro-netizen/omnia2`.  
> Numerazione = quella costruita in sessione; temi allineati al prompt originario dove possibile.

**Ultimo aggiornamento**: 28-Set-2026 · P6 acquisito · **P7 Media/File consegnato**

---

## Stato audit

| # | Area | Stato |
|---|------|--------|
| P1 | Architettura attuale | 🟢 |
| P2 | Modello concettuale | 🟢 |
| P3 | Multi-tenancy | 🟠 finding aperti |
| P4 | AuthN/AuthZ | 🟠 finding aperti |
| P5 | Lifecycle + **D-094** | 🟠 finding aperti |
| P6 | Proiezioni / enforcement D-094 | 🟠 **ACQUISITO** · E-01…E-07 aperti |
| P7 | **Media / File** (prompt originario) | 🟠 Consegnato (feedback) |

```
P1…P6 → NIENTE FIX → P7 → …
```

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

## Punto 7 — Media / File · consegnato 28-Set (prompt originario)

### Verdetto (bozza)

> Upload autenticato e storage locale funzionano.  
> Il serve è **un unico GET pubblico** su tutto lo store: foto listing e documenti sensibili condividono lo stesso canale.  
> `delete_object` esiste ma **nessun caller** in app → delete/purge = solo Mongo → orfani su disco.

### Flusso

```
UPLOAD (auth) → put_object(path) → GET /api/media/{path} PUBBLICO → DELETE = solo DB
```

Path tipici: `omnia/properties/…`, `omnia/fascicolo/…`, `omnia/modulistica/…`, `omnia/private/…`, `omnia/b2c-visura/…`.  
Nessuna signed URL. Backup media solo se `STORAGE_BACKEND=local`. Emergent delete = no-op.

### Finding M-xx (no fix · no P0–P3)

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| **M-01** | rischio | Un GET pubblico per foto **e** fascicolo/modulistica/visura | **P3.1+P4.1** |
| **M-02** | gap | `delete_object` zero call-site app | — |
| **M-03** | gap | Fascicolo delete = `$pull` senza blob | **L-06** |
| **M-04** | gap | Purge cestino = Mongo only | **L-05** |
| M-05 | oss. | Update property può droppare array media senza cleanup | — |
| M-06 | gap | upload-tmp orfani se create abortisce | — |
| M-07 | gap | Quota incompleta (tmp, modulistica, B2C, base64) | — |
| M-08 | oss. | Path in API auth → se leak, media pubblico | M-01 |
| M-09 | oss. | Privacy gate nasconde planimetrie in JSON, non il blob | — |
| M-10 | oss. | Fascicolo multipart: MIME libero | — |
| M-11 | oss. | Range 206 carica file intero in RAM | — |
| M-12 | oss. | Backup media solo local; emergent escluso | P3 backup |
| M-13 | oss. | Doppio canale fascicolo (base64 + OS) | — |
| M-14 | oss. | Emergent `delete_object` no-op | — |

### Intenzionale vs incompleto

| Intenzionale | Incompleto |
|--------------|------------|
| Foto listing pubbliche (D-068 / B2C) | Stesso endpoint per doc sensibili |
| Quota tier (D-085) | Meter incompleto |
| Download fascicolo via API auth | Blob comunque su `/api/media` |
| Backup tree locale | No cleanup blob; emergent fuori backup |

### Domande aperte

1. Prefissi sensibili (`fascicolo`, `modulistica`, `b2c-visura`) devono uscire dal GET pubblico (auth-only / signed), o resta “UUID = secret”?
2. Cleanup blob a purge: local-first subito, o dopo S3/R2 (oggi emergent delete è no-op)?

### Prossimo

Punto 8 su ok Founder (indice originario). **Niente fix.**
