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

### Prossimo

**Punto 3 — Multi-tenancy**: dal “quali sono le entità?” al “il confine tra agenzie è impermeabile?”.  
Avviare solo su richiesta Founder.
