# R-01 — Fix MC-042 v2 refresh/session post-cessazione

**Data:** 18 novembre 2026 · Europe/Rome  
**Decisione Founder:** opzione **B** (§10) — Master non ultimato finché R-01 non corretto.  
**Branch / PR:** `cursor/mc042-r01-refresh-cease-e393` · **#224**  
**Autorizzazione:** scelta B = richiesta fix (nessun merge automatico).

## Cosa è R-01

Gap MC-042 cease: login già gateato, ma (1) `/auth/refresh` non lo era e (2) al cease i refresh in DB non venivano cancellati → sessione autonoma ancora rinnovabile.

## Correzione

1. `POST /auth/refresh` → `assert_user_login_allowed` (cease = blocco).  
2. `set_commercial_status(..., ceased)` → `revoke_sessions_for_commercial_customer` (utenti org del CC, skip `super_admin`).

## Residuo access JWT (chiarito)

L’access token già emesso resta firmato fino a TTL (~15 min), ma **non è un buco prodotto**: ogni `get_current_user` chiama `enforce_commercial_access` → cease = **403** `commercial_customer_ceased` (verificato E2E su `/auth/me`).

## Verifica

| Livello | Esito |
|---------|--------|
| Unit (`test_mc042_r01_refresh_cease.py`) | gate refresh + revoke al cease + enforce su access |
| Regressione MC-042/H2/Slice1 | 72+ passed |
| CI #224 | verde |
| **E2E live** API `:43121` (18 nov 2026 Europe/Rome) | **OK** — vedi sotto |

### E2E live (fixture temporanea, cleanup)

1. login → 200 + cookie  
2. refresh pre-cease → **200**  
3. ops `set-status` ceased → **200**, `refresh_tokens` utente = **0**  
4. refresh post-cease → **401** (jti revocato)  
5. `/auth/me` con access pre-cease → **403** `commercial_customer_ceased`  
6. login post-cease → **403** `commercial_customer_ceased`  

Artifact: `/opt/cursor/artifacts/r01-e2e-live.json`

## Fuori scope

- Merge #224 / #223 — solo Founder  
- Nuovo §10 «ULTIMATO» — dopo tua conferma  
- H4 / Strato C  
