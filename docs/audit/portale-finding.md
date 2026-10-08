# Audit Portale — registro finding `P-###`

**Aggiornato**: 2026-10-08 · Onda A · fix P-001…P-008 (vai Founder)  
**Regola**: nessun fix senza «vai» Founder (D-118)

| ID | Sev | Onda | Titolo | Stato |
|--|--|--|--|--|
| P-001 | P0 | A | Search/schede vuote: seed `visibility` null + Nicastro trashed | CHIUSO |
| P-002 | P2 | A | Tunnel trycloudflare stale ma `tunnel_ok=true` | CHIUSO |
| P-003 | P2 | A | Register intents solo sell/rent_out/get_alerts (no buy) | CHIUSO |
| P-004 | P3 | A | `GET /api/ready` 404 | CHIUSO |
| P-005 | P1 | A | Footer B2C senza Privacy/Cookie/Termini | CHIUSO |
| P-006 | P3 | A | check-secrets shell ≠ uvicorn env | CHIUSO |
| P-007 | P2 | A | HAL Legal assente da CloudTopNav | CHIUSO |
| P-008 | P2 | A | Register email esistente → 409 (no auto-login) | CHIUSO |

## P-001 — dettaglio

- **File**: `backend/apps/immocloud/public_portal.py` → `_base_filter()`
- **Sintomo**: `GET /cloud/search` → `total=0`; `GET /cloud/property/demo-prop-roma-01` → 404
- **Causa**: nessun documento soddisfa contemporaneamente `visibility=public`, not trashed, active, listed, mod∉pending/rejected
- **Impatto**: dogfood “cerca casa” inutilizzabile; inquiry/preferiti su scheda pubblica bloccati
- **Fix (vai 2026-10-08)**:
  1. `seed_demo_gestionale.py` + `seed_nicastro_agency.py`: `visibility:"public"` su ogni prop listata; upsert property con `$unset deleted_at/deleted_by`
  2. Re-seed → `match_base_filter=8`
  3. QC: `backend/scripts/qc_public_portal_inventory.py` (exit 1 se inventory=0)
- **Verifica**: `GET /api/cloud/search` → `total=8`; schede `demo-prop-roma-01` e `nicastro-prop-ct-01` → 200; FE proxy `43123` total=8

## P-002 — dettaglio

- **File**: `scripts/omnia-stack.sh` → `adopt_or_start_tunnel` / `ensure`
- **Fix**: non adottare URL trycloudflare senza `tunnel_alive`; se process up ma URL morto → kill + restart; `tunnel_ok=true` solo dopo probe live

## P-003 — dettaglio

- **File**: `backend/apps/immocloud/cloud_auth.py` (`Intent`) + `CloudRegisterPage.jsx` + i18n
- **Fix**: aggiunto intent `buy` (BE + FE + it/en/es)

## P-004 — dettaglio

- **File**: `backend/server.py`
- **Fix**: `GET /api/ready` alias di `/api/health/readiness`

## P-005 — dettaglio

- **File**: `FooterB2C.jsx`, `LegalDocPage.jsx`, route App.js `/:lang/{privacy,cookie,termini}`
- **Fix**: link footer + pagine statiche informativa/cookie/termini (i18n)

## P-006 — dettaglio

- **File**: `scripts/check-secrets-presence.sh`
- **Fix**: carica `backend/.env` per chiavi unset (parity con uvicorn dotenv); vault/process vince sul file

## P-007 — dettaglio

- **File**: `CloudTopNav.jsx`
- **Fix**: link `HAL Legal` → `/:lang/legal`

## P-008 — dettaglio

- **File**: `CloudRegisterPage.jsx`
- **Fix**: su 409 `email_already_registered` messaggio chiaro + link a `/:lang/login` (API resta 409; no auto-login)
