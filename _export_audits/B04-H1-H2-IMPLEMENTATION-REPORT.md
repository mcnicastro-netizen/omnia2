# B04-H1 + B04-H2 — Implementation Report

**Data:** 17 novembre 2026 · Europe/Rome  
**Autorizzazione Founder:** solo H1 + H2 (non H3/H4/legacy/B04-III)  
**Merge:** non eseguito (fuori mandato)

---

## 1. Commit di partenza

`93252d87bc396db410a143794a226c5e9cdab7ad` (`main`, post-merge B04-II)

## 2. File modificati

| File | Motivo |
|---|---|
| `backend/shared/auth/dependencies.py` | Nuovo `require_roles_exact` (no alias D-041) |
| `backend/apps/billing/routes.py` | Wallet admin → exact roles; revoke bind CC |
| `backend/shared/billing/credit_wallet_service.py` | `revoke_allocation` richiede `commercial_customer_id` |
| `backend/tests/test_b04ii_wallet_ledger.py` | Adattamento chiamata revoke |
| `backend/tests/test_b04_h1_h2_wallet_authz.py` | Suite H1/H2 (nuova) |
| `_export_audits/B04-H1-H2-IMPLEMENTATION-REPORT.md` | Questo report |

Nessuna modifica frontend (nessuna UI allocate/revoke presente).

## 3. Modifiche H1 — Isolamento revoche

- `revoke_allocation(..., commercial_customer_id: str)` obbligatorio.
- Update atomico con filtro `{id, commercial_customer_id, remaining_qty > 0}`.
- Cross-tenant / missing → `404 allocation_not_found` **senza** mutare il wallet vittima.
- Route `POST /billing/wallet/revoke`: risolve CC da `require_agency(user)` via `resolve_cc_id_for_agency`; rifiuta se CC assente (`400 commercial_customer_required`).
- Client `allocation_id` non è prova di autorizzazione.

## 4. Modifiche H2 — Main Admin / Branch Admin

- Introdotto `require_roles_exact` (deny-by-default sul ruolo letterale).
- **Non** modificato l’alias globale D-041 di `require_roles` (preserva franchising altrove).
- Endpoint wallet admin usano `_WALLET_MAIN_ADMIN = require_roles_exact("super_admin", "agency_admin", "group_admin")`:
  - `GET /billing/wallet`
  - `POST /billing/wallet/allocate`
  - `POST /billing/wallet/revoke`
- `GET /billing/wallet/organization` resta accessibile a Branch Admin / agent, **scoped** a `require_agency(user)` (solo org attiva).

## 5. Matrice permessi prima / dopo

| Capacità | Prima | Dopo |
|---|---|---|
| `GET /wallet` (centrale) | agency_admin **+ branch_admin** (alias) | agency_admin / group_admin / super_admin **esatti** |
| `POST /wallet/allocate` | + branch_admin | solo exact Main roles |
| `POST /wallet/revoke` | + branch_admin; revoke senza bind CC | exact Main + bind CC |
| `GET /wallet/organization` | branch_admin OK, solo org attiva | invariato (consentito) |

Nota residua (già in B04-H): non esiste ancora un ruolo DB `main_admin` distinto; `agency_admin` esatto su una filiale può ancora amministrare il wallet del CC della propria agency. Gap modellistico DES-08 vs ruoli attuali — fuori scope H1/H2.

## 6. Test aggiunti

File: `backend/tests/test_b04_h1_h2_wallet_authz.py`

**H1:** same-CC OK; cross-tenant no mutation; missing CC; unknown; duplicate; concurrent; route bind CC.  
**H2:** exact rejects branch_admin; alias still allows (D-041); exact allows agency_admin; rejects agent; endpoints wire exact guard; org wallet scoped.

## 7. Test eseguiti e risultati

```
pytest tests/test_b04_h1_h2_wallet_authz.py \
       tests/test_b04ii_wallet_ledger.py \
       tests/test_b04i_foundations.py -v
→ 28 passed (0.39s)
```

Log: `/opt/cursor/artifacts/b04-h1-h2-pytest.log`

## 8. Test non eseguiti

- Suite completa backend oltre B04-I/II/H: non richiesta; scope circoscritto.
- Test E2E browser / Stripe live: vietati / non pertinenti.
- Produzione / DB reale: vietato.

## 9. Regressioni / rischi residui

- Callers interni di `revoke_allocation` devono passare `commercial_customer_id` (unico caller: route + test).
- Gap Main Admin vs `agency_admin` di filiale (vedi §5).
- Alias D-041 resta attivo su altre API non-wallet (voluto).

## 10. Dipendenze H3 / H4

Nessuna bloccante. H3 (allocate require linked CC) e H4 (top-up customer=) **non** toccate.  
H1/H2 completabili indipendentemente.

## 11. Commit prodotto

Vedi git log sul branch `cursor/b04-h1-h2-wallet-authz-e393`.

## 12. Branch e PR

- Branch: `cursor/b04-h1-h2-wallet-authz-e393`
- Base: `main`
- PR: aperta da questo run (no merge)

## 13. Conferma esplicita di perimetro

**Confermato:** non modificati H3, H4, R-03/R-04/R-05, migrazioni legacy, dual-write, B04-III…VII, Stripe produzione, ambienti esterni. Nessun merge. Nessun deploy.
