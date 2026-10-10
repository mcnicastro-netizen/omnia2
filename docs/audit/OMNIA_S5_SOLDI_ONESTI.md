# S5 — Soldi onesti (C2 / C3)

**Data:** 10 Ottobre 2026  
**Stato:** ✅ codice + LIVE  
**Chiude:** C2 (hard-gate) · parte di C3 (UI valuator + Legal edge)

---

## C2 — Self-serve ≠ Stripe sandbox

| Flag | Significato | Default |
|------|-------------|---------|
| `STRIPE_ENABLED` | Infrastruttura pagamenti (test/live) | sandbox Cloud: spesso `true` |
| `OMNIA_SELF_SERVE_ENABLED` | Rubinetto checkout **B2B** (O6 / D-115) | default codice OFF · **S9 ON** (`true`, D-120) |

Endpoint B2B bloccati se self-serve OFF (503 `self_serve_blocked`):

- `POST /billing/checkout`
- `POST /billing/credits/purchase`
- `POST /billing/storage/purchase` (risposta assistita, non session)

`GET /billing/plans` espone `enabled` **e** `self_serve_enabled`.

**Fuori gate S5:** checkout B2C one-shot (Visura / valuator € / Legal €1) — rail portale; Stripe sandbox resta usabile per dogfood.

---

## C3 — Narrativa vs addebito

| Path | Prima | Ora (S5) |
|------|-------|----------|
| Valuator agenzia | Copy “12 crediti / Usa crediti” senza debit | Copy **incluso piano v1** (nessun addebito) |
| HAL Legal senza `active_agency_id` | Gratis silenzioso (`rail: none`) | **403** `active_agency_required` |
| HAL Legal con agency | Debit 12 crediti (P-036) | **incluso piano** (D-119 · `agency_included`) |
| HAL Legal B2C | Stripe €1 | invariato |

---

## Prove

- Unit: `backend/tests/test_s5_soldi_onesti.py`
- LIVE: `docs/ops/runs/s5-soldi-onesti-live.log` — Stripe ON + self-serve OFF → checkout/credits 503

---

## Aperto (non S5)

- Debit reale valuator agenzia (se Founder vuole listino crediti invece di incluso)

## Chiuso dopo S5

- **D-119** (10-Ott-2026): D-075 vs P-036 — HAL Legal CRM **incluso**; B2C €1 e API crediti restano
- **S9 / D-120** (10-Ott-2026): O6 PASS · `OMNIA_SELF_SERVE_ENABLED=true`
