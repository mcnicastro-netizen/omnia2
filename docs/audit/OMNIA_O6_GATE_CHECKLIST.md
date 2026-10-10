# O6 — Gate attivazione account (checklist)

**Aggiornato:** 10 Ottobre 2026 (S8 — allineato a coerenza / S1)  
**Regola (D-115):** nessun pagamento self-serve finché questa checklist ≠ **PASS** *e* Founder non firma il rubinetto (S9).  
**Durante FAIL / CONDITIONAL:** solo provisioning assistito dichiarato (SLA interno ≤5 gg lav. provvisorio).  
**SoT freccia:** `OMNIA_COERENZA_SISTEMA.md` · puntatore `memory/NEXT_SESSION.md`.

| # | Onda / decisione | Criterio | Esito |
|---|------------------|----------|-------|
| 1 | **O0** D-114 | Design bak/media vincolante scritto + numeri; listino fermo | ✅ PASS (`OMNIA_O0_BAK_MEDIA_DESIGN.md`) · runtime bak = S2 ✅ |
| 2 | **O1a** D-095 | Fascicolo/modulistica non pubblici via `/api/media` | ✅ PASS |
| 3 | **O1b** D-100 | Invite: no overwrite password; `user_exists` | ✅ PASS |
| 4 | **O1c** D-106 | `active_agency_id` SoT, no fallback `agency_ids[0]` | ✅ PASS |
| 5 | **O2** D-094/D-111 | Trash uniforme nei job; client trash → richieste `frozen`; update bloccato | ✅ PASS (codice) · residui C5 fuori freccia |
| 6 | **O3a** D-105 | Founder Ops: bak OK/PARTIAL/FAILED + alert | ✅ PASS (codice) |
| 7 | **O3b** D-113 | Procedura restore + **run firmata** non-prod | ✅ PASS docs + **run firmata S1 2026-10-10** (`RESTORE_MANUAL` §6 · `docs/ops/runs/s1-restore-o3b-2026-10-10.log`) |
| 8 | **O4a** D-109 | Landing prezzi da `GET /billing/plans` | ✅ PASS |
| 9 | **O4b** D-110 | `localStorage` ≠ entitlement; piano attivo solo server | ✅ PASS |
| 10 | **O5** D-104/107/108/112 | Upload stati+retry; pagination; APScheduler; seed demo | ✅ PASS (minimi) · demo story = S7 |
| 11 | Self-serve Stripe | Checkout B2B pubblico solo dopo PASS + firma Founder | ❌ **BLOCCATO** in codice: `OMNIA_SELF_SERVE_ENABLED` default OFF (S5) — apre a **S9** |

## Verdetto corrente

**Gate O6: CONDITIONAL PASS** — prerequisiti tecnici O0–O5 + restore firmata OK; self-serve **hard OFF** finché Founder non firma (S9).  
Stripe sandbox può restare ON per probe B2C. Rubinetto B2B = solo S9.

## Firma Founder (quando si apre self-serve) — S9

| Campo | Valore |
|-------|--------|
| Data | |
| Restore run rif. | `s1-restore-o3b-2026-10-10` (già FIRMATO) |
| Note | |
| Decisione | self-serve ON / resta assistito |
