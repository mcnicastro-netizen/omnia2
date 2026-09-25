# Audit architettura SaaS — note Founder (sessione 25-Set-2026)

> Appunti vincolanti per la prosecuzione dell’audit **1→27**, un punto alla volta.  
> **Niente codice** finché il Founder non dice «vai».

---

## Punto 1 — Contesto runtime (chiarimenti chiusi)

| Domanda | Risposta operativa (repo + Founder) |
|---------|-------------------------------------|
| Storage produzione | **Locale** oggi (`STORAGE_BACKEND=local`). Emergent = legacy. S3/R2 = obiettivo docs, **non implementato** nel codice. |
| Purge cestino 30g | Endpoint `POST /api/app/cron/trash/purge` (super_admin). **Non** in APScheduler → automatico solo se cron esterno lo chiama. |
| Deploy API oltre Cloud Agent | Target: Vercel FE + API ASGI (Railway/Render/Fly/VPS). **Oggi** demo/dev = Cloud Agent. Emergent non è più host prod. |

---

## Punto 2 — Modello concettuale · **APPROVATO** Founder

### Osservazioni di precisione (non correzioni sostanziali)

1. **Agenzia = confine dominio / tenant**  
   Premessa fondamentale. Nei punti 3+ verificare che non sia solo convenzione UI/app, ma vincolo **ovunque**: API, query Mongo, file, job, publishing, backup/restore, API key, cache, ecc.

2. **Cliente ≠ Richiesta**  
   Mantenere la distinzione: Cliente = chi è; Richiesta = cosa cerca / lavoro aperto. **Non fondere** `client` e `client_request`. Serve per lifecycle, cancellazione, storico, match, attività.

3. **“Due mondi sullo stesso DB”** (B2B + B2C)  
   Non è un bug dichiarato: è **zona sensibile** da verificare dopo. Domande future: campi che escono dal tenant; chi decide pubblicabilità; stessa entità vs proiezione; modifica/delete; leak privato→pubblico; cache/feed/pubblicazioni già generate.

### Mappa concettuale da portare avanti

```
                 OMNIA
                   │
        ┌──────────┼──────────┐
        │          │          │
     B2B/App     B2C/Cloud   API v1
        │          │          │
     Agenzia    Utente B2C   Partner
        │
 ┌──────┼───────────────┐
 │      │       │       │
Utenti Immobili Clienti Attività
           │      │
           │   Richieste
           │      │
           └── Match
           │
      Pubblicazione
           │
    Portali / Sito / Social
```

Separati / incompleti:

- Academy → fuori perimetro attuale  
- MLS → previsto / incompleto  
- Franchising → scheletro / incompleto  

### Prossimo (storico)

Punto 3 avviato su richiesta Founder — vedi sotto.

---

## Punto 3 — Multi-tenancy · consegnato 25-Set-2026 (in attesa feedback Founder)

### Verdetto
**Per lo più impermeabile** sul CRM JWT→Mongo (`/api/app` + agency_admin/agent).  
**Non impermeabile end-to-end**: foro principale media pubblici + path fascicolo; gap secondari su collezioni fuori guard e bypass super_admin/job.

### Meccanismo
1. Agenzia attiva da JWT (`active_agency_id` ∈ `agency_ids`, else primo).
2. Auto-inject `agency_id` su `TENANT_COLLECTIONS` solo se `tenant_enforce` (`/api/app/*`).
3. Bypass: path non-app, job, **`super_admin`**.
4. Route tipiche: `require_agency` + filtro esplicito.

### Gap da tenere in audit (no fix senza «vai»)
1. `GET /api/media/{path}` pubblico → fascicolo `omnia/fascicolo/{pid}/{doc}` leggibile se si conosce il path.
2. Collezioni tenant-like fuori da `TENANT_COLLECTIONS` (es. activities, social_channels, import_jobs…).
3. Query solo-`id` sotto bypass (fascicolo, jobs, alcuni client_requests).
4. Multi-agenzia: alcuni flussi usano `agency_ids[0]` invece di active (api_keys/invites).
5. Backup giornaliero = dump pan-tenant su disco (rischio operativo filesystem).

### Prossimo
Punto 4 solo su richiesta Founder.
