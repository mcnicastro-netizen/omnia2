# Audit architettura SaaS — note Founder (sessione 25-Set-2026)

> Appunti vincolanti per la prosecuzione dell’audit **1→27**, un punto alla volta.  
> **Niente codice** finché il Founder non dice «vai».  
> Metodo: raccogliere dove il confine può rompersi; priorità P0/P1 solo dopo; non confondere superfici privilegiate intenzionali con defect.

**Stato sessione**: ⏸ **IN PAUSA** (Founder: «per adesso basta») dopo Punto 4. Sync docs/manuale/HAL 25-Set.

---

## Punto 1 — Contesto runtime (chiarimenti chiusi)

| Domanda | Risposta operativa (repo + Founder) |
|---------|-------------------------------------|
| Storage produzione | **Locale** oggi (`STORAGE_BACKEND=local`). Emergent = legacy. S3/R2 = obiettivo docs, **non implementato** nel codice. |
| Purge cestino 30g | Endpoint `POST /api/app/cron/trash/purge` (super_admin). **Non** in APScheduler → automatico solo se cron esterno lo chiama. |
| Deploy API oltre Cloud Agent | Target: Vercel FE + API ASGI (Railway/Render/Fly/VPS). **Oggi** demo/dev = Cloud Agent. Emergent non è più host prod. |

---

## Punto 2 — Modello concettuale · **APPROVATO** Founder

1. **Agenzia = confine dominio / tenant**
2. **Cliente ≠ Richiesta**
3. **Due mondi sullo stesso DB** — zona sensibile, non defect dichiarato

Mappa: B2B/App → Agenzia → Utenti/Immobili/Clienti/Attività → Richieste → Match → Pubblicazione.  
Separati: B2C, API v1. Fuori/incompleti: Academy, MLS, Franchising.

---

## Punto 3 — Multi-tenancy · **ACQUISITO** Founder

> **Tenant isolation applicativa: generalmente presente.**  
> **Tenant isolation end-to-end: incompleta.**

Finding acquisiti: media pubblici; guard non universale; trusted paths super_admin/job; `id` senza agency_id; agency_ids[0]; backup privileged data plane.

---

## Punto 4 — Autenticazione e autorizzazioni · **CONSEGNATO** (feedback aperto · sessione in pausa)

AuthN generalmente solida; AuthZ a strati con gap scoping/sessione.  
Finding candidati: fascicolo senza agency_ids; invite password overwrite; no refresh rotation; reset non revoca sessioni; is_active su access; peer invite admin; self-mint API credits.

---

## Sync documentale (questa pausa)

| Artefatto | Path |
|-----------|------|
| Cap. 00 | `memory/manuale/00-architettura-tenancy-auth.md` |
| HAL | `api.tenant-isolation` · `api.auth-lifecycle` · `api.audit-architettura-stato` in `00-api-codice.yaml` |
| Cap. 13 / 7 | limiti multi-agenzia + accesso documenti |
| Backlog | **A-035** in ASPETTI |
| CHANGELOG | entry 25-Set audit P1–P4 |

### Ripresa
- Feedback P4 se serve, **oppure** Punto 5 su richiesta, **oppure** «vai» su finding prioritizzati.
