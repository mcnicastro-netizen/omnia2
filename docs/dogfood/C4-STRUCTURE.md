# D-175 · C4 — Schema struttura Dogfood

**Stato:** ✅ **CHIUSO in main** (19-Nov-2026) · PR #234 · head `2ae1234` · merge `67b5e92` · D-189  
**Non include:** C5–C8 · E2E completo · network franchising multi-P.IVA

```
CommercialCustomer (1)
  vat_number_normalized  ← unicità (country_code, vat)
  main_admin_user_id     ← nominato solo se User esiste
  │
  ├── Organization × N (agencies.dogfood_org_key)
  │     activation_status = pending (CRM unlock esplicito)
  │
  └── cc_credit_wallets × 1 (wallet centrale)
```

## Due casi da non confondere

| Caso | Modello OMNIA | Collaudo C4 |
|---|---|---|
| Stessa ditta, più filiali (stessa P.IVA) | 1 CC → N Organization | ✅ sì |
| Affiliati network autonomi (P.IVA distinte, tipo Tecnocasa) | 1 CC per affiliato; rete ≠ customer | ❌ non ancora E2E |

## Matrice autorità

Vedi `ROLE_AUTHORITY_MATRIX` in `backend/shared/dogfood/c4_structure.py` e `docs/dogfood/C4-FOUNDER-PROCEDURE.md`.

## Script

| Script | Ruolo |
|---|---|
| `dogfood_c4_workcopy.py` | CLEAN/CONTINUITY da permanente (read) |
| `dogfood_c4_apply_manifest.py` | Struttura + nominate/membership se utenti esistono |
| `dogfood_c4_verify.py` | T1–T13 |
| `dogfood_c4_bind_runtime.sh` | API su CLEAN (mai permanente) |
| `dogfood_c4_print_verify_link.py` | Link conferma email (Resend HOLD) |

## Permanente

Mai target di seed/wipe/clone. Identity C3 invariata.
