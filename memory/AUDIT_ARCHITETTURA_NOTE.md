# Audit architettura SaaS — note Founder

> Un punto alla volta. **Niente codice** senza «vai».  
> Nessuna classificazione P0–P3 definitiva finché non si vede l’intero sistema.  
> SoT: GitHub `mcnicastro-netizen/omnia2` (mai Origin-tmp).

**Ultimo aggiornamento**: 28-Set-2026 · P4 acquisito · P5 lifecycle consegnato

---

## Stato audit

| Area | Stato |
|------|--------|
| P1 — Architettura attuale | 🟢 Ricostruito |
| P2 — Modello concettuale | 🟢 Ricostruito / approvato |
| P3 — Multi-tenancy | 🟠 Isolamento applicativo presente, E2E incompleto · **ACQUISITO** |
| P4 — AuthN/AuthZ | 🟠 Strutturato, AuthZ E2E incompleta · **ACQUISITO** |
| P5 — Lifecycle entità | 🟠 Consegnato (feedback Founder) |

---

## Punto 1 — Contesto (chiuso)

| Tema | Realtà |
|------|--------|
| Storage | Locale oggi; Emergent legacy; S3/R2 non in codice |
| Purge cestino 30g | Endpoint cron; **non** in APScheduler |
| Deploy API | Target Vercel+ASGI; oggi Cloud Agent |

---

## Punto 2 — Modello · APPROVATO

Agenzia = confine · Cliente ≠ Richiesta · Due mondi stesso DB = zona sensibile.

---

## Punto 3 — Multi-tenancy · ACQUISITO

> Tenant isolation **applicativa**: generalmente presente.  
> Tenant isolation **end-to-end**: incompleta.

Finding: media pubblici; guard non universale; trusted paths super_admin/job; `id` senza agency_id; `agency_ids[0]`; backup privileged data plane.

---

## Punto 4 — AuthN/AuthZ · **ACQUISITO** Founder (28-Set)

### Formulazione vincolante

> OMNIA ha diversi meccanismi di sicurezza individualmente sensati,  
> ma **non ancora una catena di autorizzazione completamente uniforme**  
> dal login fino alla singola risorsa.

Diverso da “AuthN insicura”: AuthN strutturata; fragilità soprattutto in **verifica contesto risorsa** e **lifecycle sessione**.

### Finding aperti (tutti e 7, senza severità definitiva)

| ID | Cluster | Contenuto |
|----|---------|-----------|
| **P3.1 + P4.1** | Documenti fascicolo | Access control + media access (concreto) |
| **P4.2** | Account lifecycle | Accept invite riscrive password — delicato |
| **P4.3–P4.4** | Session management | No refresh rotation; reset non revoca — incident response |
| **P4.5–P4.6** | Agency governance | `agency_ids[0]`; privilege boundaries |
| **P4.7** | Membership → endpoint | Condizionato: problematico se membership debole |

Non defect automatici: super_admin bypass, register pubblico, superfici pubbliche (valutare nel contesto).

---

## Punto 5 — Lifecycle entità · consegnato 28-Set (feedback)

### Verdetto (bozza agente)

> Lifecycle **strutturato** su Immobile/Cliente (cestino 30g) e su Richieste (macchina a stati D-090).  
> Lifecycle **end-to-end incompleto** su feed/sync vs trash, cascate orfane, blob fascicolo, agency senza deactivate/delete — più i legami già aperti in P3/P4.

### Mappa sintetica

| Entità | Maturità ciclo | Note |
|--------|----------------|------|
| Immobile | Soft-delete 30g + restore/purge | `status` non cambia al trash; feed/sync **senza** `with_not_trashed` |
| Cliente | Soft-delete 30g (block se immobili) | Non cascada richieste/attività |
| Richiesta | Stati open→…→archived | Delete = archive; no trash/hard purge |
| Attività | open/done/cancelled | Hard delete immediato |
| Match | On-read | No persist; scan può includere trashed |
| Agency | Create/update | **Nessuna** API deactivate/delete |
| Invite | pending→accepted/revoked/expired | Vedi P4.2 |
| Fascicolo/media | Upload OK | Delete = solo ref DB; blob resta → P3.1/P4.1 |
| API key | Issue/revoke | No hard delete ledger |
| User erase | GDPR self | Non chiude CRM agenzia |

### Finding lifecycle (L-xx) — acquisibili, no fix, no P0–P3

| ID | Tipo | Sintesi | Link |
|----|------|---------|------|
| L-01 | gap | Richieste: archive sì, trash/hard purge no | — |
| L-02 | gap | Trash cliente non cascada richieste/attività | — |
| L-03 | rischio | Immobile in cestino può restare in **feed/sync** (`status=active`, no `with_not_trashed`) | P3 E2E |
| L-04 | oss. | Match/nightly stesso pattern vs trash | — |
| L-05 | gap | Purge Mongo senza cleanup blob/notif/cache | **P3.1** |
| L-06 | rischio | Fascicolo delete senza `delete_object` + scoping fragile | **P3.1+P4.1** |
| L-07 | rischio | Invite overwrite password | **P4.2** |
| L-08 | gap | Agency senza deactivate/delete API | **P4.5–6** |
| L-09 | oss. | Attività: hard delete, no soft | — |
| L-10 | gap | migrate prefs filtra `trashed_at` (campo morto; reale è `deleted_at`) | — |
| L-11 | oss. | Erasure user ≠ chiusura CRM; sessioni | **P4.3–4** |
| L-12 | oss. | `agency_ids[0]` / remove member | **P4.5–7** |
| L-13 | oss. | No unmatch se immobile poi trashed | — |

### Domande aperte (non bloccanti per continuare)

1. Soft-delete immobile → deve uscire da feed/sync (solo filtro trash) o anche forzare `status=withdrawn`?
2. Delete cliente → archiviare/cascadare richieste, o lasciarle storiche?

### Prossimo

Punto 6 solo su ok Founder. Nessun fix.
