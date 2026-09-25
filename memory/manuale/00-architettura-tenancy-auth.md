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

## 0.4 · Autenticazione e autorizzazioni (Punto 4 · consegnato, feedback aperto)

**Bozza verdetto:** AuthN generalmente solida per la fase; AuthZ a strati (ruolo + membership + agency) con buchi di scoping e lifecycle sessione.

### Finding candidati (no fix)

| Sev. | Finding |
|------|---------|
| rischio | Fascicolo: utente senza `agency_ids` → query solo per `id` immobile |
| rischio | Accept invite può riscrivere password di account già esistente |
| gap | Refresh senza rotation; reset password non revoca sessioni |
| gap | `get_current_user` non ricontrolla `is_active` |
| gap | Inviti / API keys legati a `agency_ids[0]` (vedi P3#5) |
| gap | Admin non-owner può invitare peer `agency_admin`; self-mint crediti API |
| oss. | MFA TOTP, CSRF prod, register role-lock presenti |

### Cosa c’è e funziona

- Cookie HttpOnly access (~15m) + refresh (~7g, jti revocabile).
- CSRF double-submit in produzione.
- Brute-force login; bcrypt; MFA TOTP.
- API key Track B hashata + crediti.
- Tre piani auth distinti (app / cloud / v1).

---

## 0.5 · Ripresa

1. Feedback Founder su Punto 4 (se serve rettifica formulazione).
2. Solo su richiesta: **Punto 5** dell’audit.
3. Fix codice: solo dopo backlog prioritizzato + «vai».

Backlog tracciato anche come **A-035** in `ASPETTI_DA_APPROFONDIRE.md`.
