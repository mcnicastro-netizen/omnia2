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

## 0.6 · Proiezioni esterne (Punto 6 · consegnato)

Enforcement D-094 **a macchia di leopardo**: OK su ImmoCloud / v1 / publishing feed; **non** su OSF feed, sync_engine, sito, social, MLS, match. Client trash → archive richieste ancora assente. Finding E-01…E-09 in note.

---

## 0.7 · Ripresa

1. Feedback Punto 6.
2. Solo su richiesta: **Punto 7**.
3. Fix D-094 in codice: solo priorità + «vai» esplicito (non confondere con «vai» = prossimo punto audit).

Backlog **A-035**.
