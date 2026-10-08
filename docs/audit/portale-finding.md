# Audit Portale — registro finding `P-###`

**Aggiornato**: 2026-10-08 · Onda A  
**Regola**: nessun fix senza «vai» Founder (D-118)

| ID | Sev | Onda | Titolo | Stato |
|--|--|--|--|--|
| P-001 | P0 | A | Search/schede vuote: seed `visibility` null + Nicastro trashed | APERTO |
| P-002 | P2 | A | Tunnel trycloudflare stale ma `tunnel_ok=true` | APERTO |
| P-003 | P2 | A | Register intents solo sell/rent_out/get_alerts (no buy) | APERTO |
| P-004 | P3 | A | `GET /api/ready` 404 | APERTO |
| P-005 | P1 | A | Footer B2C senza Privacy/Cookie/Termini | APERTO |
| P-006 | P3 | A | check-secrets shell ≠ uvicorn env | APERTO |
| P-007 | P2 | A | HAL Legal assente da CloudTopNav | APERTO |
| P-008 | P2 | A | Register email esistente → 409 (no auto-login) | APERTO |

## P-001 — dettaglio

- **File**: `backend/apps/immocloud/public_portal.py` → `_base_filter()`
- **Sintomo**: `GET /cloud/search` → `total=0`; `GET /cloud/property/demo-prop-roma-01` → 404
- **Causa**: nessun documento soddisfa contemporaneamente `visibility=public`, not trashed, active, listed, mod∉pending/rejected
- **Impatto**: dogfood “cerca casa” inutilizzabile; inquiry/preferiti su scheda pubblica bloccati
- **Fix proposto (solo con «vai»)**: (1) seed demo: settare `visibility:"public"` sugli annunci listati; (2) ripristinare o ri-seed Nicastro non trashed; (3) QC script che fallisce se `match_base_filter==0`
