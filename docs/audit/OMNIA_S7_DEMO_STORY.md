# S7 — Una demo story (C8)

**Data:** 10 Ottobre 2026  
**Stato:** ✅ codice + LIVE ×2  
**Chiude:** C8 (due seed = due storie → una storia GTM)

---

## Decisione

| Ruolo | Agency | Uso |
|-------|--------|-----|
| **Demo story GTM** | `demo-agency-001` | Sandbox time-boxed; percorso prospect |
| Dogfood Founder | Nicastro | Fuori pitch GTM — non sostituisce la demo |

Funnel (Founder): richiesta → **sandbox a tempo** (gestionale + annunci portale) → a scadenza **Acquista pacchetto** — senza call.  
Checkout B2B aperto da **S9** (`OMNIA_SELF_SERVE_ENABLED=true` · D-120).

---

## Codice

| Pezzo | Cosa |
|-------|------|
| `shared/demo_story.py` | Finestra `demo_started_at` / `demo_expires_at` (default 7g, `OMNIA_DEMO_TRIAL_DAYS`) |
| `seed_demo_gestionale.py` | Imposta `demo_story=true` + finestra a ogni seed |
| `GET /billing/demo-status` (+ campo `demo` su `/billing/subscription`) | Stato sandbox / CTA |
| `BillingPage` | Banner sandbox; a scadenza CTA **Acquista pacchetto** (assistito se self-serve OFF) |
| `scripts/demo_story_probe.py` | Probe ripetibile: seed → login → CRM → portale → expire → Acquista → checkout 503 |

---

## Prove

- Unit: `backend/tests/test_s7_demo_story.py`
- LIVE ×2: `docs/ops/runs/s7-demo-story-live.log` — entrambi PASS

---

## Chiuso dopo S7

- S8 SoT · S9 self-serve · **S10 GTM-01 PASS** (D-121)

## Aperto (non S7)

- S3.1 firma meter · D-038 APE
