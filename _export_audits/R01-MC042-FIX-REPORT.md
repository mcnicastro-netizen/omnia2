# R-01 — Fix MC-042 v2 refresh/session post-cessazione

**Data:** 18 novembre 2026 · Europe/Rome  
**Decisione Founder:** opzione **B** (§10) — Master non ultimato finché R-01 non corretto.  
**Branch:** `cursor/mc042-r01-refresh-cease-e393`  
**Autorizzazione:** scelta B = richiesta fix (nessun merge automatico).

## Correzione

1. `POST /auth/refresh` → `assert_user_login_allowed` (stesso gate del login).  
2. `set_commercial_status(..., ceased)` → `revoke_sessions_for_commercial_customer` (tutti gli utenti delle org del CC, escluso `super_admin`).

## Test

`tests/test_mc042_r01_refresh_cease.py` + regressione MC-042/H2/Slice1.

## Fuori scope

- Merge #223 docs Master  
- Nuovo §10 «ULTIMATO» (solo dopo verifica Founder di questo fix)  
- H4 / Strato C / CI workflow list  
