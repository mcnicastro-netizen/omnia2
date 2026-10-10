# S10 — GTM-01 Demo Readiness (D-104)

**Data:** 10 Ottobre 2026  
**Stato:** ✅ LIVE PASS  
**Chiude:** checkpoint pre-outreach ~5k (A-036 / K-SC-01)

---

## Scope (D-104)

Non = 5000 concurrent. Verificare:

1. **Percorso prospect** — FE home → portale search → login demo → CRM properties/matches → plans self-serve → checkout B2B
2. **Smoke ~20 concurrent** — search + properties + matches + upload-tmp + read/serve media
3. **Trigger AD-01** — se smoke media fallisce → rivalutare object storage; qui **non** fallisce

## Artefatto

| Pezzo | Path |
|-------|------|
| Script | `scripts/gtm01_smoke.py` |
| Log LIVE | `docs/ops/runs/s10-gtm-01-live.log` |
| Decisione | **D-121** |

## Esito LIVE (10-Ott-2026)

| Metrica | Valore |
|---------|--------|
| Workers | 20 |
| Error rate | 0.0 |
| p50 / p95 | ~88 ms / ~106 ms |
| Upload+serve | 4/4 OK |
| Checkout | 200 session (Stripe test) |
| Preview FE | 200 (tunnel + :43123) |

**ESITO = PASS**

## Cosa non apre

- Outreach ~5k email (ora *ammesso* dal gate, non eseguito qui)
- Stripe **live** keys
- Object storage obbligatorio (smoke media OK → baseline FS resta)

## Limiti

Smoke leggero su Cloud sandbox. Stress ladder / 2000 clients = fuori S10 (`stress_gestionale.py`).
