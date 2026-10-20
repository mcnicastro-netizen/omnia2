# YouTrust (Yousign) — Modulistica e-sign

**Scopo**: firma elettronica OTP email su mandati / proposte / compliance.  
**Anti-wedge (D-042)**: nessuna FEA/FEQ proprietaria.

## Branding OMNIA vs whitelabel

Stessi template e stessa firma. Differisce solo il PDF:

| `plan_type` | Footer |
|---|---|
| `hybrid` / turnkey | nota generator «No Paper» |
| `whitelabel` | solo brand agenzia — niente OMNIA |

## Sandbox vs produzione

| Ambiente | Completion |
|---|---|
| **Sandbox** (attuale) | **Niente webhook** (limite YouTrust). Dopo OTP → `POST …/sync-esign` o bottone «Aggiorna stato firma» (poll UI ogni 20s). |
| **Produzione** | Webhook HMAC opzionale + stesso sync-esign di fallback |

## Env

| Var | Note |
|---|---|
| `ESIGN_PROVIDER=yousign` | altrimenti mock |
| `YOUSIGN_API_KEY` | sandbox/prod — **scadenza sandbox 25/10/2026** |
| `YOUSIGN_API_BASE` | sandbox: `https://api-sandbox.yousign.app/v3` |
| `YOUSIGN_WEBHOOK_SECRET` | solo produzione (32 char) |

## Endpoint utili

| Method | Path | Quando |
|---|---|---|
| `POST` | `/documents/{id}/send-sign` | invio firma |
| `POST` | `/documents/{id}/sync-esign` | **sandbox + fallback** — poll + download PDF firmato |
| `GET` | `/documents/{id}/download?signed=1` | PDF firmato se salvato |
| `POST` | `/esign/webhook` | **solo produzione** (sandbox → 501) |

## Railway (sandbox attuale)

Variables: `ESIGN_PROVIDER=yousign`, `YOUSIGN_API_KEY`, `YOUSIGN_API_BASE`.  
`YOUSIGN_WEBHOOK_SECRET` non serve finché si resta in sandbox.

## Scadenza key

Sandbox reiniettata **20-Ott-2026**, scadenza **25/10/2026**.  
Rinnovare in console YouTrust → vault Environment + Railway.
