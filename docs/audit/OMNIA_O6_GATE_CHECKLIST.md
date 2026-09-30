# O6 — Gate attivazione account (checklist)

**Regola (D-115):** nessun pagamento self-serve finché questa checklist ≠ **PASS**.  
**Durante FAIL:** solo provisioning assistito dichiarato (SLA interno ≤5 gg lav. provvisorio).

| # | Onda / decisione | Criterio | Esito |
|---|------------------|----------|-------|
| 1 | **O0** D-114 | Design bak/media vincolante scritto + numeri; listino fermo | ✅ PASS (`OMNIA_O0_BAK_MEDIA_DESIGN.md`) |
| 2 | **O1a** D-095 | Fascicolo/modulistica non pubblici via `/api/media` | ✅ PASS |
| 3 | **O1b** D-100 | Invite: no overwrite password; `user_exists` | ✅ PASS |
| 4 | **O1c** D-106 | `active_agency_id` SoT, no fallback `agency_ids[0]` | ✅ PASS |
| 5 | **O2** D-094/D-111 | Trash uniforme nei job; client trash → richieste `frozen`; update bloccato | ✅ PASS (codice) |
| 6 | **O3a** D-105 | Founder Ops: bak OK/PARTIAL/FAILED + alert | ✅ PASS (codice) |
| 7 | **O3b** D-113 | Procedura restore manuale documentata non-prod | ✅ PASS docs (`docs/ops/RESTORE_MANUAL.md`) · **run firmata:** ⏳ da eseguire su non-prod |
| 8 | **O4a** D-109 | Landing prezzi da `GET /billing/plans` | ✅ PASS |
| 9 | **O4b** D-110 | `localStorage` ≠ entitlement; piano attivo solo server | ✅ PASS |
| 10 | **O5** D-104/107/108/112 | Upload stati+retry; pagination properties; owner APScheduler; seed demo | ✅ PASS (minimi) |
| 11 | Self-serve Stripe | Abilitare checkout pubblico solo dopo PASS completo incluso run restore | ❌ **BLOCCATO** finché riga 7 run ≠ firmata e Founder non apre rubinetto |

## Verdetto corrente

**Gate O6: CONDITIONAL PASS (codice+docs)** — self-serve resta **OFF**.  
Manca la **run restore firmata** su non-prod (O3b operativo). Provisioning assistito ammesso.

## Firma Founder (quando si apre self-serve)

| Campo | Valore |
|-------|--------|
| Data | |
| Restore run rif. | |
| Note | |
| Decisione | self-serve ON / resta assistito |
