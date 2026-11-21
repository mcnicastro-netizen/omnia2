# W3 Staging Verification Harness

Strumento riproducibile per la **verifica staging** del perimetro multi-tenant W3.

## Principi

- **Local-first**: il default è `--mode local` contro API/Mongo loopback.
- **Staging opt-in**: `--mode staging` richiede `OMNIA_STAGING_VERIFY=1`.
- **Nessuna email reale**, nessun charge Stripe live, cleanup solo su documenti con prefisso `w3stg-<run_id>`.
- Non equivale a Railway/Vercel: i test multi-processo locali dimostrano JWT+Mongo condivisi, non il bilanciatore.

## Uso

```bash
# Preflight locale (ciclo remediation)
cd /workspace   # o root repo
python -m scripts.w3_staging_harness --mode local

# Solo quando autorizzato il mandato staging remoto
OMNIA_STAGING_VERIFY=1 REACT_APP_BACKEND_URL=https://… \
  python -m scripts.w3_staging_harness --mode staging
```

## Criteri di ingresso staging (EC-1…EC-6)

Vedi output JSON `entry_criteria` e `OMNIA-W3-STAGING-READINESS-REPORT.md`.

## Scenari

Gli scenari multi-tenant HTTP sono già in `backend/tests/test_w3_http_dual_tenant_mongo.py`.
Questo harness orchestra preflight + report PASS/FAIL/BLOCKED e documenta le verifiche solo-staging.
