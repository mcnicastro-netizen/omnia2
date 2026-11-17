# B04-H2 Main Admin residual — Implementation Report

**Data:** 17 novembre 2026 · Europe/Rome  
**Commit di partenza:** `3b425a8e53e29a14fa209f050a58530231bd3fa8` (`main`)  
**Branch:** `cursor/b04-h2-main-admin-impl-e393`  
**Merge:** **non eseguito** (attende Founder)

## Decisioni Founder applicate

D01–D12 come in `_export_audits/B04-H2-MAIN-ADMIN-DECISIONS-CONFORMITY.md`  
(TTL 48h; Super Admin mutate solo straordinario; Cabina+email best-effort).

## Modello autorizzazione

- Binding: `commercial_customers.main_admin_user_id` (+ appointed_at/by)
- Eventi: `commercial_main_admin_events` (append-only)
- Transfer: `commercial_main_admin_transfers` (pending→accepted/cancelled/expired), token **hash** only
- Guard wallet: Main Admin idoneo; `null`/non match/non idoneo/CC non operabile → deny
- Super Admin allocate/revoke: solo con `extraordinary_reason` (≥8 char) + audit D07
- H1 preservato (revoke con `commercial_customer_id`)

## File modificati / aggiunti

| File | Ruolo |
|---|---|
| `backend/shared/models/commercial_customer.py` | campi Main Admin |
| `backend/shared/billing/main_admin_service.py` | **nuovo** — ciclo vita + assert |
| `backend/shared/db/connection.py` | indici |
| `backend/apps/billing/routes.py` | wallet guards + transfer API |
| `backend/apps/immoweb/founder_ops.py` | Ops nominate/revoke |
| `backend/tests/test_b04_h2_main_admin.py` | **nuovo** |
| `backend/tests/test_b04_h1_h2_wallet_authz.py` | adattamento H1 route + guard |
| `backend/tests/test_b04ii_wallet_ledger.py` | FakeColl.update_many |
| `_export_audits/B04-H2-MAIN-ADMIN-*.md` | design, conformità, report |

## Endpoint

| Endpoint | Comportamento |
|---|---|
| `GET /billing/wallet` | Main Admin / Super Admin read |
| `POST /billing/wallet/allocate\|revoke` | Main Admin **o** Super Admin + `extraordinary_reason` |
| `GET /billing/wallet/organization` | invariato (org-scoped) |
| `GET /billing/commercial/main-admin` | stato binding |
| `POST .../transfer` `accept` `cancel` | D08–D10 |
| `POST /ops/commercial-customers/main-admin` | D01 nominate |
| `POST /ops/.../main-admin/revoke` | clear binding |

## Test eseguiti

```
pytest tests/test_b04_h2_main_admin.py \
       tests/test_b04_h1_h2_wallet_authz.py \
       tests/test_b04ii_wallet_ledger.py \
       tests/test_b04i_foundations.py \
       tests/test_slice1_b01_b03.py
→ 50 passed
```

Log: `/opt/cursor/artifacts/b04-h2-main-admin-pytest.log`

## Migrazione dati

**Nessuna auto-assegnazione.** CC esistenti restano `main_admin_user_id=null` → deny wallet admin finché Ops nomina (D01). Nessuna migrazione massiva eseguita.

## Limiti residui

- UI Cabina per accept transfer: API pronta; schermata FE non in scope.
- Job expiry: lazy on accept/propose (D09).
- H3/H4/legacy: non toccati.

## Conferma perimetro

Non modificati H3, H4, migrazione legacy, B04-III, Stripe live, produzione. No merge.
