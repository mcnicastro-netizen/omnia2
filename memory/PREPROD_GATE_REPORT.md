# Pre-production confidence gate

**Run**: `63c82729` · 2026-09-17T10:27:37.883011+00:00
**Verdict**: ✅ PASS (required)

## Policy

- No Resend bulk send · No Stripe checkout · No paid visure · No fal.ai · No Nominatim hammer
- Mongo + our HTTP stack are load-tested; vendors are soft-probed only

## Summary

| Area | OK | Notes |
|------|:--:|-------|
| local_rate_reset | ✅ | localhost counters only |
| health_readiness | ✅ | prod flags pending: cors_explicit, cookie_secure, credentials_master_key, monitoring_configured, omnia_env_production |
| security | ✅ |  |
| regressions | ✅ |  |
| mongo_internal | ✅ |  |
| api_portal_fanout | ✅ |  |
| api_crm_fanout | ✅ |  |
| soft_externals | ✅ | vendors soft-probed only |
| pytest_subset | ✅ |  |

## Load metrics (our stack only)

- Mongo: 500 docs write 10.4 ms · 200 concurrent reads p50=3.24 ms p95=18.02 ms · cleanup 500
- Portal search ×40: p50=98.2 ms p95=118.0 ms errors=0
- Portal facets ×30: p50=63.8 ms p95=76.6 ms errors=0
- CRM clients ×30: p50=49.0 ms p95=64.6 ms errors=0
- CRM kpis ×20: p50=74.1 ms p95=114.8 ms errors=0

## Prod flags still WARN (expected in local)

- `cors_explicit` — set on Vercel/prod host before go-live
- `cookie_secure` — set on Vercel/prod host before go-live
- `credentials_master_key` — set on Vercel/prod host before go-live
- `monitoring_configured` — set on Vercel/prod host before go-live
- `omnia_env_production` — set on Vercel/prod host before go-live

## What this gate does NOT prove

- Real Resend delivery, Stripe Checkout, paid visure PDF, fal.ai video, Nominatim under load
- Full browser UX / mobile layout / accessibility
- Multi-region failover or cold-start under real traffic
- Absolute absence of bugs — only that critical hot paths + security walls held under this run

## How to re-run

```bash
bash scripts/omnia-stack.sh ensure
cd backend && source .venv/bin/activate
python scripts/preprod_confidence_gate.py
```

JSON: `memory/reports/preprod_gate_63c82729.json`

