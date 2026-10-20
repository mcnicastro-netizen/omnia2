# YouTrust (Yousign) — Modulistica e-sign

**Scopo**: firma elettronica OTP email su mandati / proposte / compliance.  
**Anti-wedge (D-042)**: nessuna FEA/FEQ proprietaria.

## Branding OMNIA vs whitelabel

Stessi template e stesso flusso firma. Differisce solo il PDF:

| `plan_type` | Footer |
|---|---|
| `hybrid` / turnkey | nota generator «No Paper» (ecosistema OMNIA) |
| `whitelabel` | solo brand agenzia — niente OMNIA |

## Env

| Var | Note |
|---|---|
| `ESIGN_PROVIDER=yousign` | altrimenti mock |
| `YOUSIGN_API_KEY` | sandbox/prod — **scadenza sandbox tipica breve** |
| `YOUSIGN_API_BASE` | default `https://api-sandbox.yousign.app/v3` |
| `YOUSIGN_WEBHOOK_SECRET` | 32 char HMAC per `x-yousign-signature-256` |

## Endpoint

| Method | Path | Auth |
|---|---|---|
| `POST` | `/api/app/modulistica/esign/webhook` | HMAC YouTrust |
| `POST` | `/api/app/modulistica/documents/{id}/send-sign` | agency |
| `POST` | `/api/app/modulistica/documents/{id}/sync-esign` | agency (poll + download) |
| `GET` | `/api/app/modulistica/documents/{id}/download?signed=1` | agency |

Su `signature_request.done` (webhook o sync): status → `signed`, PDF in `signed_storage_path`.

## Sync webhook

```bash
# Genera/persiste YOUSIGN_WEBHOOK_SECRET + stampa endpoint target
backend/.venv/bin/python scripts/sync-yousign-webhook.py
# Oppure verso API Railway:
backend/.venv/bin/python scripts/sync-yousign-webhook.py --railway
```

**Sandbox YouTrust**: le subscription webhook **non** si creano via API (403) — solo da  
[YouTrust App → Webhooks](https://yousign.app/) (ambiente Sandbox):

1. Endpoint: `$OMNIA_API_PUBLIC_URL/api/app/modulistica/esign/webhook` (prod)  
   oppure tunnel Cloud `https://….trycloudflare.com/api/app/modulistica/esign/webhook`
2. Eventi: `signature_request.done`, `declined`, `canceled`, `expired`
3. Secret: allinea `YOUSIGN_WEBHOOK_SECRET` (32 char) tra App ↔ vault Environment ↔ Railway Variables

Finché il webhook UI non è attivo, usa in CRM **Aggiorna stato firma** (`POST …/sync-esign`).

Poi su **Railway Variables** (service API):  
`YOUSIGN_API_KEY`, `ESIGN_PROVIDER=yousign`, `YOUSIGN_API_BASE`, `YOUSIGN_WEBHOOK_SECRET`.

## Scadenza key

Sandbox reiniettata **20-Ott-2026**, scadenza **25/10/2026**.  
Prima di quella data: rinnovare in console YouTrust → vault Environment + Railway Variables.
