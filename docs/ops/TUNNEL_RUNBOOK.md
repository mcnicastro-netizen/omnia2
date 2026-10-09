# Tunnel runbook (Cloud Agent / trycloudflare) — P-058

**Ambito**: ambienti Cloud con `*.trycloudflare.com` · non produzione custom domain.  
**Correlati**: P-026 (whsec vault) · P-051 (`COOKIE_SECURE`) · P-056 (noindex).

## Sintomi tipici

- Tunnel 502 / pagina bianca
- Login cookie “sparisce” su HTTPS
- Stripe webhook `invalid_signature` dopo rotazione URL
- CSRF 403 dopo fix P-051 (atteso senza header)

## Procedura

1. **Restart stack**  
   `bash scripts/omnia-stack.sh ensure`  
   Verifica: API `43121`, preview `43123`, `tunnel_ok=true`.

2. **Public URL**  
   `scripts/sync-public-base-url.py` upsert `FRONTEND_*` / `OMNIA_PUBLIC_URL` + **`COOKIE_SECURE=true`** su HTTPS.  
   Se `CHANGED=1` → API restart (omnia-stack).

3. **Webhook Stripe**  
   `scripts/sync-stripe-webhook-url.py` punta l’endpoint test al tunnel corrente.  
   Su **CREATE** scrive `STRIPE_WEBHOOK_SECRET` in `.env`.  
   Su solo UPDATE URL il secret non ruota.

4. **P-026 — vault whsec**  
   Se il vault Cursor ha un `STRIPE_WEBHOOK_SECRET` diverso da quello dell’endpoint auto-sync:  
   - runtime preferisce `.env` allineato all’endpoint  
   - **Founder**: aggiorna Save Secrets env omnia2 al whsec dell’endpoint “OMNIA Cloud Agent portal (auto-sync)”  
   - disabilita endpoint Stripe orfani in Dashboard

5. **SEO demo**  
   Host tunnel → `noindex, nofollow` (P-056). Non usare tunnel per SEO prod.

6. **Verifica rapida**  
   - `GET /api/billing/plans` → `mode=test` `enabled=true`  
   - login → cookie `Secure` + CSRF cookie  
   - PATCH `/api/auth/me` senza `X-CSRF-Token` → **403**  
   - checkout test + webhook 200

## Rollback

- Disabilitare endpoint Stripe non usati  
- `COOKIE_SECURE=false` solo per HTTP locale puro (non tunnel)
