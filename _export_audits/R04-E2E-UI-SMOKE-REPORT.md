# R-04 — E2E UI smoke (post-Master)

**Data:** 18 novembre 2026 · ~16:25 Europe/Rome  
**Residuo Master:** R-04 — «E2E UI non rieseguito in questa certificazione»  
**Ambiente:** stack locale API `43121` + preview `43123` · tip `main` post-#227  
**Natura:** riesecuzione smoke UI/API. **Nessun gap Master riaperto.**

## Perimetro smoke

| Step | Esito | Evidenza |
|---|---|---|
| API login demo admin | **OK** 200 | `r04-api-smoke.json` |
| API `/auth/me` + refresh | **OK** 200 | idem |
| API properties / clients / notifications / billing plans+subscription | **OK** | probe agent |
| UI login → `/it/app/avvio` | **OK** | `r04-02-app-shell.png` |
| UI Immobili `/it/app/properties` | **OK** (4 immobili demo) | `r04-04-properties.png` |
| UI Billing `/it/app/settings/billing` | **OK** | `r04-03-billing.png` |
| UI path errato `/it/app/billing` | **404 FE** (route reale = `settings/billing`) | notato in smoke |

## Artifact

`/opt/cursor/artifacts/r04-*.png` · `r04-ui-smoke.json` · `r04-api-smoke.json` · `r04-billing-check.json`

## Verdetto

**R-04 CHIUSO** come riesecuzione smoke post-certificazione Master.  
Non equivale al pacchetto dogfood readiness completo (§11).

## Fuori scope

Dogfood checklist completa · Stripe live · H4 · harden TOCTOU R-01
