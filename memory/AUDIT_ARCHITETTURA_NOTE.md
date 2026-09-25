# Audit architettura SaaS — note Founder (sessione 25-Set-2026)

> Appunti vincolanti per la prosecuzione dell’audit **1→27**, un punto alla volta.  
> **Niente codice** finché il Founder non dice «vai».  
> Metodo: raccogliere dove il confine può rompersi; priorità P0/P1 solo dopo; non confondere superfici privilegiate intenzionali con defect.

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

1. **Agenzia = confine dominio / tenant** — verificare ovunque nei punti 3+.
2. **Cliente ≠ Richiesta** — non fondere `client` / `client_request`.
3. **Due mondi sullo stesso DB** — zona sensibile, non defect dichiarato.

### Mappa da portare avanti

B2B/App → Agenzia → Utenti / Immobili / Clienti / Attività → Richieste → Match → Pubblicazione → Portali/Sito/Social  
Separati: B2C/Cloud, API v1 Partner; fuori/incompleti: Academy, MLS, Franchising.

---

## Punto 3 — Multi-tenancy · **ACQUISITO** Founder

### Verdetto Founder (formulazione vincolante)

> **Tenant isolation applicativa: generalmente presente.**  
> **Tenant isolation end-to-end: incompleta.**

Non elevare ancora a “multi-tenancy sicura”. Nei punti successivi verificare stesso confine su file, backup, restore, job, cache, publishing, API, logging ed errori.

### Finding già acquisiti (no fix)

1. Media/documenti sensibili — `GET /api/media/...` pubblico = criticità immediata (dato fisico, non solo Mongo).
2. Guard non universale — collezioni fuori rete di sicurezza.
3. Bypass `super_admin` / job = **trusted execution paths**, non API speciali.
4. `id` senza `agency_id` — fragile fuori contesto tenant.
5. Multi-agency / `agency_ids[0]` — possibile problema semantico (attiva vs prima).
6. Backup = **privileged data plane**, non confondere con isolation API.

---

## Punto 4 — Autenticazione e autorizzazioni · consegnato 25-Set-2026 (in attesa feedback)

### Verdetto (bozza agente)

AuthN mid-stage solido (cookie HttpOnly, CSRF, refresh revocabile, bcrypt, brute-force login, MFA TOTP, Google, API key Track B).  
AuthZ B2B su ruoli + membership + `agency_id`; ownership stretto solo su alcune azioni.  
Gap seri: scoping fascicolo senza agency, invite che riscrive password, inconsistenze sessione/multi-agency — **acquisire, non fixare**.

### AuthN (sintesi)

- Access JWT ~15m (cookie o Bearer); refresh ~7g cookie + jti in `refresh_tokens`; refresh **non ruota**.
- CSRF double-submit in prod; exempt login/public/v1/webhook.
- Brute-force login 5/15min; no RL su forgot/MFA verify.
- MFA TOTP + backup codes wired.
- Track B: `omk_live_*` hash SHA-256 + crediti + origin whitelist.

### AuthZ (sintesi)

- Ruoli: super_admin, agency_admin, agent, client, student, group/branch_*.
- `require_roles` + alias franchising.
- Escalation intenzionali: create_agency → agency_admin; invite; create group → group_admin.
- Tre piani: `/api/app` JWT+ruoli · `/api/cloud` JWT/public · `/api/v1` API key.

### Finding candidati P4 (no fix)

| Sev. | Finding |
|------|---------|
| rischio | Fascicolo: user senza agency_ids può query by property id |
| rischio | Accept invite sovrascrive password account esistente |
| gap | No refresh rotation; reset password non revoca sessioni |
| gap | `get_current_user` non ricontrolla `is_active` |
| gap | agency_ids[0] vs active (invites/api_keys) — già P3#5 |
| gap | agency_admin non-owner può invitare peer agency_admin |
| gap | Self-mint crediti API key da agency_admin |
| oss. | MFA/CSRF/register role-lock presenti |

### Prossimo

Punto 5 solo su ok Founder.
