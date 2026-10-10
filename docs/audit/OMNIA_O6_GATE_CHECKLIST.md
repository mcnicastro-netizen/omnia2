# O6 — Gate attivazione account (checklist)

**Aggiornato:** 10 Ottobre 2026 (**S9 PASS**)  
**Regola (D-115):** nessun pagamento self-serve finché questa checklist ≠ **PASS** *e* Founder non firma il rubinetto (S9).  
**SoT freccia:** `OMNIA_COERENZA_SISTEMA.md` · puntatore `memory/NEXT_SESSION.md` · artefatto S9: `OMNIA_S9_O6_SELF_SERVE.md`.

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
| 11 | Self-serve Stripe | Checkout B2B pubblico solo dopo PASS + firma Founder | ✅ **APERTO S9** — `OMNIA_SELF_SERVE_ENABLED=true` (D-120) |

## Verdetto corrente

**Gate O6: PASS** — prerequisiti O0–O5 + restore firmata + firma Founder self-serve (S9 / D-120).  
Stripe Cloud resta `mode=test` finché non si decide live (fuori S9).

## Firma Founder — S9 ✅

| Campo | Valore |
|-------|--------|
| Data | 10 Ottobre 2026 |
| Restore run rif. | `s1-restore-o3b-2026-10-10` (FIRMATO) |
| Note | Ordine Founder: merge #26 → #25 → S9. Rubinetto B2B ON; Stripe test. |
| Decisione | **self-serve ON** |
| Firma | Founder (chat 10-Ott-2026 · «segui il tuo ordine») |
