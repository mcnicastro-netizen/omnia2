# PRE-GTM — Sicurezza e multi-tenancy

**Aggiornato:** 2026-11-21 21:19 CET · branch `cursor/w4-staging-e2e-b894` HEAD `3f34c5f`  
**Rapporti:**  
- `OMNIA-W3-TENANT-GUARD-E2E-VERIFICATION.md`  
- `OMNIA-W3-SECONDARY-ACCESS-PATHS-HARDENING.md`  
- `OMNIA-W3-RESIDUAL-IDOR-CLOSURE.md`  
- `OMNIA-W3-STAGING-READINESS-REPORT.md`  
- `OMNIA-W3-SESSION-REVOCATION-FINAL-GATE.md` (B14 locale)
- `OMNIA-W4-STAGING-E2E-REPORT.md` ← **W4 staging (verdetto B)**

## Stato

| Area | Stato |
|------|-------|
| Tenant guard force + fail-closed + scrub update | implementato verificato |
| Deal/MLS/docs/chat/video actor filters | implementato verificato |
| Properties B2C/CRM filtri atomici | implementato verificato |
| CC join / checkout MA / remove_member / invites | implementato verificato |
| Sessioni B14 (`sid`/`sv` + Mongo `active_session_ids`) | implementato verificato (HTTP + multi-processo) |
| HTTP dual-tenant Mongo | **19 scenari** PASS locale |
| Multi-processo locale (2 uvicorn) | **5** PASS incl. revoke access JWT cross-process |
| Harness staging | `scripts/w3_staging_harness` preflight PASS (health/mongo/unauth/**session_revocation**) |
| Staging E2E W4 | **B — NON SUPERATO** (repliche/L5/Stripe/FE drift) |
| Staging / GTM cert | **NO** |

## Test session gate + regressione

```text
16 passed — session HTTP + multi-processo B14 + P.IVA concorrente
226 passed — regressione W3/D-175/authz aggregata
Harness locale PASS — /opt/cursor/artifacts/w3_staging_harness_session.json
```

## Residui solo staging

- multi-replica Railway (attestazione dietro LB), B8/L5/T22, Stripe webhook, cookie Vercel  
- ~~access JWT TTL post-revoke~~ → **chiuso localmente** (SoT Mongo sessioni)
