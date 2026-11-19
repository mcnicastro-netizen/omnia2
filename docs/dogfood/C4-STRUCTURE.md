# D-175 · C4 — Schema struttura Dogfood

```
CommercialCustomer (1)
  vat_number_normalized  ← unicità (country_code, vat)
  main_admin_user_id     ← nominato solo se User esiste (Founder)
  │
  ├── Organization × N (agencies.dogfood_org_key)
  │     activation_status = pending (CRM unlock esplicito)
  │
  └── cc_credit_wallets × 1 (wallet centrale)
```

## Matrice autorità

Vedi `ROLE_AUTHORITY_MATRIX` in `backend/shared/dogfood/c4_structure.py` e `docs/dogfood/C4-FOUNDER-PROCEDURE.md`.

## Script

| Script | Ruolo |
|---|---|
| `dogfood_c4_workcopy.py` | CLEAN/CONTINUITY da permanente (read) |
| `dogfood_c4_apply_manifest.py` | Struttura + nominate/membership se utenti esistono |
| `dogfood_c4_verify.py` | T1–T13 |

## Permanente

Mai target di seed/wipe/clone. Identity C3 invariata.
