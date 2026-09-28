# Cap. 00 · Architettura tenancy & autenticazione (audit SaaS)

**Ambito**: founder / super_admin / assistenza tecnica.  
**Fonte**: audit architettura 25-Set-2026 · `memory/AUDIT_ARCHITETTURA_NOTE.md`  
**Stato sessione**: **in pausa** dopo Punto 4 (AuthN/AuthZ). Punti 5–27 non avviati.  
**Regola**: **nessun fix codice** finché il Founder non dice «vai» e non si prioritizzano i finding.

---

## 0.1 · Metodo

L’audit procede **un punto alla volta**. Si descrive e si acquisiscono finding; non si patcha a caldo. Obiettivo: mappare dove il confine può rompersi, poi classificare P0/P1 vs superfici privilegiate intenzionali.

---

## 0.2 · Cosa è OMNIA (richiamo)

Tre piani: **B2B ImmoWeb** (`/app`) · **B2C ImmoCloud** (`/cloud`) · **API v1** partner.  
Tenant commerciale: **Agenzia**. Cliente ≠ Richiesta. Academy fuori perimetro; MLS/franchising incompleti.

---

## 0.3 · Multi-tenancy (Punto 3 · ACQUISITO)

**Formulazione Founder (vincolante):**

> Tenant isolation **applicativa**: generalmente presente.  
> Tenant isolation **end-to-end**: incompleta.

Non equivale ancora a “multi-tenancy sicura”.

### Finding acquisiti (no fix)

1. `GET /api/media/...` pubblico — rischio su documenti fisici (fascicolo), non solo query Mongo.
2. Guard Mongo non universale — alcune collection fuori dalla rete di sicurezza.
3. `super_admin` / job = **trusted execution paths**.
4. Pattern `id` senza `agency_id` fragile fuori contesto tenant.
5. Multi-agency: a volte `agency_ids[0]` invece di agenzia attiva (semantica).
6. Backup globale = **privileged data plane** (filesystem), non isolation API.

---

## 0.4 · Autenticazione e autorizzazioni (Punto 4 · **ACQUISITO**)

**Formulazione Founder:** meccanismi individualmente sensati, ma **non ancora una catena AuthZ uniforme** dal login alla singola risorsa. AuthN strutturata; fragilità su contesto risorsa e lifecycle sessione.

### Cluster finding (aperti, senza P0–P3)

| ID | Cluster |
|----|---------|
| P3.1 + P4.1 | Fascicolo: access control + media |
| P4.2 | Invite riscrive password (account lifecycle) |
| P4.3–P4.4 | Session management / revoca |
| P4.5–P4.6 | Governance agenzia / privilege boundaries |
| P4.7 | Membership → endpoint (condizionato) |

---

## 0.5 · Lifecycle entità (Punto 5 · consegnato)

Ciclo maturo su Immobile/Cliente (cestino) e Richieste (stati); incompleto E2E su feed/sync vs trash, blob, agency. Dettaglio L-01…L-13 in note.

### D-094 (dominio · codice ⏳)

- `status` = commerciale · `trashed` = lifecycle record — **non** confondere.
- Immobile trashed → **escluso** da feed/sync/pubblicazioni **senza** forzare `withdrawn`.
- Cliente Trash → Richieste **archiviate** (storico), non distrutte; restore Cliente **non** le riapre.

---

## 0.6 · Proiezioni esterne (Punto 6 · **ACQUISITO**)

D-094 dominio OK; enforcement a macchia di leopardo. Finding **E-01…E-07** aperti (no P0–P3).  
**Attività**: domanda aperta (appartenenza Cliente/Richiesta/Agente/autonoma) — non assimilare alle Richieste.

---

## 0.7 · Media / File (Punto 7 · consegnato · prompt originario)

Un GET pubblico `/api/media/*` serve foto listing **e** blob sensibili. `delete_object` senza caller → orfani. Finding **M-01…M-14** in note (cluster P3.1+P4.1, L-05, L-06). D-095 dominio (pubblico vs privato · lifecycle blob).

## 0.8 · Jobs / processi asincroni (Punto 8 · consegnato)

APScheduler in `sync_engine.start_scheduler` + cron HTTP `super_admin` = **trusted paths** (P3). Scope tenant per-item; sync/matching senza trash filter (D-094); purge trash non schedulato; nessun job blob (D-095). Finding **J-01…J-12** in note.

---

## 0.9 · Ripresa

1. Feedback Punto 8.
2. Solo su richiesta: prossimo punto audit.
3. Fix codice: solo dopo fine audit / priorità + «vai» esplicito implementazione.

Backlog **A-035**.
