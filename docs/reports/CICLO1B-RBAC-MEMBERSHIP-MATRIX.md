# CICLO 1B — RBAC membership matrix (kickoff → avanzamento)

**Data (Europe/Rome):** 2026-11-26 ~18:25 CET  
**Branch:** `cursor/ciclo1-gtm-ops-merge-b894`  
**Base `main`:** `c342fb0` (post-merge #248)  
**Autorizzazione:** programma GTM — RBAC P1  
**PR:** #249 (aperta — **non** mergeata in questo sotto-ciclo)

---

## 1. Obiettivo

Avanzare il modello ruolo-per-membership oltre il kickoff: cambio ruolo, sospensione, audit, test matrix, senza forzare multi-membership parallele.

## 2. Problema / causa

- `users.role` globale poteva driftare rispetto a `memberships.operational_role`.  
- Mancavano API dedicate per downgrade/sospensione con revoke sessioni e audit.  
- `require_roles` non vedeva membership sospese se `is_active` restava true.

## 3. Soluzione

1. `security_events` append-only (`shared/auth/security_audit.py`).  
2. `set_operational_role` / `suspend_membership` / `unsuspend_membership` in `membership_service`.  
3. `activate_exclusive_membership` emette audit + dual-write `users.role`.  
4. Endpoint:
   - `PATCH /agencies/me/members/{id}/role` (`require_roles_exact` — no `branch_admin`)
   - `POST .../suspend` · `POST .../unsuspend`
5. `get_current_user`: membership sospesa → `403 membership_suspended`.  
6. `remove_member`: audit `member_removed`.

## 4. Test

| Suite | Esito |
|-------|-------|
| `test_rbac_membership_role_matrix.py` + slice1 RBAC | **17 passed** |

Casi: dual-write ruolo · audit · suspend/unsuspend · overlay membership · super_admin invariato · invite revoked/expired · branch_admin negato · owner role locked · cross-org 404 · change role success.

Log: `/opt/cursor/artifacts/ciclo1-rbac-matrix-unit2.log`

## 5. Residui RBAC

| Voce | Stato |
|------|--------|
| Multi-membership contemporanee (ruoli diversi per org) | **bloccato** da modello exclusive B01 — richiede decisione/fase di migrazione dedicata |
| FE UI cambio ruolo / sospensione | non aggiornata in questo sotto-ciclo |
| Staging HTTP mutativo ruoli | **non verificato** (no cookie admin staging) |
| Concorrenza doppia PATCH ruolo | unit lock non dedicato (session revoke serializza effetto) |
| Invito accept E2E HTTP | verify revoked/expired covered; accept full flow = preesistente |

## 6. Verdetto

**Implementato + testato localmente.** Non GTM. Non merge su `main` di #249 senza decisione Founder (solo #248 era autorizzata al merge).

## 7. Prossimo

Isolamento multi-tenant deep **oppure** merge #249 se Founder autorizza, poi FE cabina ruolo + smoke staging ruoli.
