# Prossima sessione — programma passi

**Aggiornato**: 21 Novembre 2026 (~23:00 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**PR #242**: merge W4/B14 (D-192) — tip pre-merge docs su branch `cursor/w4-staging-e2e-b894`  
**Verdetto W4**: **B** (non A)

---

## Dove siamo

| Item | Stato |
|------|-------|
| B14 session SoT Mongo + fail-closed | in PR #242 / main post-merge |
| W4 obbligatori eseguibili (revoke multi-istanza, FE, W4-08/13/18, B8 restart) | PASS attestati staging |
| L5 Resend | **BLOCKED** — manca `RESEND_API_KEY` + `SENDER_EMAIL` su Railway staging |
| Stripe Test (W4-21/22) | **BLOCKED** — manca `STRIPE_ENABLED` + `STRIPE_SECRET_KEY` (+ webhook se serve) |
| Manuale Cap.01 + HAL B14 | sync D-084 (D-192) |
| Config Founder Resend/Stripe | **domani** (mandato esplicito di questa sera) |

## Prossimo passo (domani)

1. Configurare su Railway staging (`omnia-api` **e** `omnia-api-w4b` se ancora attivo) le vars del contratto:  
   - Resend: `RESEND_API_KEY`, `SENDER_EMAIL` (dominio verificato OK)  
   - Stripe Test: `STRIPE_ENABLED=true`, `STRIPE_SECRET_KEY` (test), webhook se richiesto dal flusso  
2. Restart API → B8 health/flags → rieseguire L5 + W4-21/22 con evidenze.  
3. Solo allora rivalutare verdetto W4 (A solo se obbligatori PASS + evidenze).  
4. Reindex HAL post-merge: `POST /api/app/hal/knowledge/reindex?force=true` (super_admin).

## Non fare

- Stripe **Live** / email a destinatari reali.  
- Dichiarare W4 **A** o production-ready senza L5+Stripe Test PASS.  
- Reset/stash/clean del worktree o force-push su main.  
- Aprire H4 sealed / C5–C8 Dogfood senza nuovo OK Founder.
