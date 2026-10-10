# S9 — O6 PASS + rubinetto self-serve

**Data:** 10 Ottobre 2026  
**Stato:** ✅ firma Founder + LIVE  
**Chiude:** C2 (self-serve OFF → ON) · riga O6 #11

---

## Decisione

Founder (ordine 10-Ott: merge D-119 → S8 → S9): **self-serve B2B ON**.

| Campo | Valore |
|-------|--------|
| Flag | `OMNIA_SELF_SERVE_ENABLED=true` |
| Stripe | resta `STRIPE_MODE=test` in Cloud (live = passo separato) |
| Restore rif. | `s1-restore-o3b-2026-10-10` (già FIRMATO) |
| Decisione SoT | **D-120** |

## Cosa apre

Endpoint B2B non più 503 `self_serve_blocked`:

- `POST /billing/checkout`
- `POST /billing/credits/purchase`
- `POST /billing/storage/purchase` (path checkout, non solo messaggio assistito)

`GET /billing/plans` → `self_serve_enabled: true`.

## Cosa non cambia

- Default codice senza env resta OFF (kill-switch emergenza)
- B2C one-shot invariato
- Stripe live keys / GTM outreach = **S10**, non S9

## Prove

- Unit: `backend/tests/test_s9_o6_self_serve.py`
- LIVE: `docs/ops/runs/s9-o6-self-serve-live.log`
