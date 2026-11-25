# Prossima sessione — programma passi

**Aggiornato**: 25 Novembre 2026 (~12:20 CET — Europe/Rome)  
**Repo**: https://github.com/mcnicastro-netizen/omnia2 ✅  
**W4**: **A con residui** (D-193)

---

## Dove siamo

| Item | Stato |
|------|-------|
| B14 + PR #242 | in `main` |
| W4-19 L5 Resend | **PASS** |
| W4-21/22 Stripe Test | **PASS** (webhook+plans+sdk); app B2B checkout gated self-serve |
| Verdetto W4 | **A con residui** |

## Residui noti (non urgenti)

1. `OMNIA_SELF_SERVE_ENABLED=false` → `/billing/checkout` 503 `self_serve_blocked` (D-115/O6).  
2. Side-effect wallet/crediti post-webhook non deep-verificato.  
3. Reindex HAL se non fatto post-#242.

## Prossimo passo (solo con nuovo mandato Founder)

- Aprire self-serve / H4 / Stripe Live / GTM / Dogfood C5+ — **vietato** senza OK esplicito.  
- Oppure lavoro prodotto altro (S1 follow-up, etc.).

## Non fare

- Stripe Live · email a destinatari reali · dichiarare GTM-ready solo perché W4 è A-con-residui.
