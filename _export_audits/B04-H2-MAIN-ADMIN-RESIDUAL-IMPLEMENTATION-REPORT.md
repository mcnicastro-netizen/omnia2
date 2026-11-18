# B04-H2 Main Admin residual — Implementation Report

**Data:** 17 novembre 2026 · Europe/Rome  
**Commit di partenza:** `3b425a8e53e29a14fa209f050a58530231bd3fa8` (`main`)  
**Branch:** `cursor/b04-h2-main-admin-impl-e393`  
**PR:** https://github.com/mcnicastro-netizen/omnia2/pull/216  
**Merge:** **non eseguito** (attende Founder)

## Decisioni Founder applicate

D01–D12 come in `_export_audits/B04-H2-MAIN-ADMIN-DECISIONS-CONFORMITY.md`  
(TTL 48h; Super Admin mutate solo straordinario; Cabina+email best-effort).

## Fix mirati post-analisi ChatGPT (autorizzati Founder)

| Fix | Prima | Dopo |
|---|---|---|
| **D10** accept | Transfer → `accepted`, poi update CC (non atomico) | Binding CC con filtro sul titolare attuale **prima**; poi claim transfer `pending→accepted`. Se claim fallisce → compensate (ripristino titolare) + 409. Nessun `accepted` orfano. |
| **D08** Cabina | `except` + log; evento notify `success` anche se Cabina falliva | Insert notifica su `db.notifications`; fallimento → transfer `cancelled` + evento `transfer_notify` `outcome=failed` + HTTP 503. Email resta best-effort. |
| **D02** multi-CC | `agency_id` vince e mismatch con CC esplicito → 403 | `commercial_customer_id` esplicito **vince**; auth resta su assert per-CC. Fallback agency solo se CC assente. |
| **D04/D11** idoneità | `is_active is False` deny; assente/null passava | Serve `is_active is True` (assente/null/False → non idoneo). |
| **Opzionale Ops force** | Overwrite silenzioso se MA già presente | Senza `force=true` → 409; con force + reason ≥8 → `ops_replace` auditato. |
| **Opzionale read limitata** | Prima: non definita | **MC-042 / D-176 (18/11/2026):** whitelist funzionale = documenti chiusura + fatturazione (sola lettura); vietata consultazione operativa wallet. **Enforcement codice non autorizzato / non presente** su `main`. |

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
| `backend/shared/billing/main_admin_service.py` | ciclo vita + assert + **fix D02/D04/D08/D10** + force Ops |
| `backend/shared/db/connection.py` | indici |
| `backend/apps/billing/routes.py` | wallet guards + transfer API |
| `backend/apps/immoweb/founder_ops.py` | Ops nominate/revoke + **`force`** |
| `backend/tests/test_b04_h2_main_admin.py` | suite H2 + test fix |
| `backend/tests/test_b04_h1_h2_wallet_authz.py` | adattamento H1 route + guard |
| `backend/tests/test_b04ii_wallet_ledger.py` | FakeColl.update_many |
| `_export_audits/B04-H2-MAIN-ADMIN-*.md` | design, conformità, report, handoff |

## Endpoint

| Endpoint | Comportamento |
|---|---|
| `GET /billing/wallet` | Main Admin / Super Admin read |
| `POST /billing/wallet/allocate\|revoke` | Main Admin **o** Super Admin + `extraordinary_reason` |
| `GET /billing/wallet/organization` | invariato (org-scoped) |
| `GET /billing/commercial/main-admin` | stato binding |
| `POST .../transfer` `accept` `cancel` | D08–D10 (Cabina obbligatoria su propose; accept binding-first) |
| `POST /ops/commercial-customers/main-admin` | D01 nominate; replace solo con `force=true` |
| `POST /ops/.../main-admin/revoke` | clear binding |

## Test eseguiti

```
pytest tests/test_b04_h2_main_admin.py \
       tests/test_b04_h1_h2_wallet_authz.py \
       tests/test_b04ii_wallet_ledger.py \
       tests/test_b04i_foundations.py \
       tests/test_slice1_b01_b03.py
→ 57 passed
```

Nuovi test mirati: idoneità `is_active` assente/null; multi-CC resolve; Cabina fail/success; double-accept; compensate claim-lost; Ops `force`.

Log: `/opt/cursor/artifacts/b04-h2-fix-pytest.log`

## CI

Attesa/verificata su push del branch PR #216 (job `Backend billing / B04 unit`).

## Migrazione dati

**Nessuna auto-assegnazione.** CC esistenti restano `main_admin_user_id=null` → deny wallet admin finché Ops nomina (D01). Nessuna migrazione massiva eseguita.

## Limiti residui

- UI Cabina per accept transfer: API pronta; schermata FE non in scope.
- Job expiry: lazy on accept/propose (D09).
- Read wallet su CC cessato/non operativo: decisione **MC-042** ora definisce whitelist (chiusura+fatturazione); sul codice `main` la read wallet operativa resta ancora ampia → scostamento documentato, fix solo con nuovo mandato.
- H3/H4/legacy/B04-III: **non toccati** (verifica: modifiche solo ai file elenco sopra + export audit H2).

## Conferma perimetro

Non modificati H3, H4, migrazione legacy, B04-III, Stripe live, produzione, UI FE. No merge.
