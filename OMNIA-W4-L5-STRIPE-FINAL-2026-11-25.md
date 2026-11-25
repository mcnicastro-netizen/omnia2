# OMNIA — W4 L5 + Stripe Test final (25-Nov-2026)

**CET:** ~12:04–12:17 Europe/Rome  
**Decisione:** D-193  
**Verdetto W4:** **A con residui**

## Presence (no secret values)

Entrambi `omnia-api` e `omnia-api-w4b`:

| Var | Classe |
|-----|--------|
| `RESEND_API_KEY` | `re_` |
| `SENDER_EMAIL` | dominio `omniarealestateecosystem.it` |
| `STRIPE_ENABLED` | `true` |
| `STRIPE_SECRET_KEY` | `sk_test` |
| `STRIPE_PUBLISHABLE_KEY` | `pk_test` |
| `STRIPE_WEBHOOK_SECRET` | `whsec` |

Deploy SUCCESS su entrambi ~11:04 UTC / 12:04 CET.

## W4-19 L5

- Bridge kill/revive Resend → health `resend_kill.killed` True→False su A e B.  
- Bridge item `resend.configured=true`.  
- Destinatari solo sintetici `@example.com`.  
- Nessuna produzione.

## W4-21 / W4-22

- `GET /api/billing/plans` → `enabled=true`, `mode=test`, publishable `pk_test`.  
- Webhook: firma invalida **400** `invalid_signature`; firma valida **200** `received`; replay **200**.  
- Stripe SDK: sessione `cs_test_…` creata.  
- App B2B `/billing/checkout` → **503** `self_serve_blocked` (gate O6, atteso).

## Residui

1. Self-serve OFF.  
2. Wallet/credits deep post-webhook non attestato.  
3. Resend emails list API 403 (scope).

## Artefatti macchina

- `w4r/w4_19_l5_and_stripe_2026-11-25.json`  
- `w4r/config_presence_matrix_2026-11-25.json`
