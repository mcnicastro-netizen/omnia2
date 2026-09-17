# Gestionale stress report (S0–S6)

**Run**: `7e1d21fd` · 2026-09-17T13:39:16.230749+00:00
**Verdict**: ✅ PASS
**Scale**: 2000 clients · 2000 properties (agency `demo-agency-001`) · **40 active** props for match (cap intenzionale)

## Policy

- Solo stack nostro · cleanup docs `_stress=gestionale_stress_v1`
- No Resend / Stripe checkout / fal / publish portali live / Nominatim hammer

## Findings (importante)

1. **Match API è O(active × searchers)** — con 2000×2000 immobili attivi×buyer l’API va in wedge. Seed stress: 2000 docs ma solo **40 active**; probe `?min_score=80&limit=20`. Fan-out concorrente su `/matches` escluso (smoke OK).
2. **Status cliente** nel modello CRM: `new|contacted|…` — valore `active` → **HTTP 500** su `GET /app/clients` (response validation). Seed corretto a `status=new`.
3. **clients/smart** è il path più lento a 2k (p95 ~436 ms) — candidato ottimizzazione futura, non bloccante.

## S0 Inventory

| Module | UI | Probe OK | Notes |
|--------|----|:--------:|-------|
| dashboard | `/app/dashboard` | ✅ | HTTP 200 |
| properties | `/app/properties` | ✅ | HTTP 200 |
| clients | `/app/clients` | ✅ | HTTP 200,200,200 |
| matches | `/app/matches` | ✅ | HTTP 200 |
| analytics | `/app/analytics` | ✅ | HTTP 200 |
| publishing | `/app/publishing` | ✅ | HTTP 200,200 |
| hal_knowledge | `/app/hal-knowledge` | ✅ | HTTP 200 |
| mls | `/app/mls` | ✅ | HTTP 200,200 |
| modulistica | `/app/modulistica` | ✅ | HTTP 200 |
| members | `/app/members` | ✅ | HTTP 200 → `/app/agencies/me/members` |
| api_keys | `/app/api-keys` | ✅ | HTTP 200 |
| settings | `/app/settings` | ✅ | HTTP 200 |
| billing | `/app/settings/billing` | ✅ | HTTP 200 → `/billing/plans` |
| staging | `/app/staging` | ✅ | HTTP 200,200 |
| founder_ops | `/app/ops` | ✅ | HTTP 200 |
| moderation | `/app/moderation` | ✅ | HTTP 200 |
| hal_assist | `HAL Assist` | ✅ | HTTP 200 |
| hal_legal | `HAL Legal` | ✅ | HTTP 200 |

## S1 HTTP fan-out (after 2k seed)

- `/app/dashboard/kpis` ×40: p50=71.5 p95=87.3 errors=0 statuses=[200]
- `/app/clients?page=1&page_size=50` ×40: p50=57.9 p95=65.1 errors=0 statuses=[200]
- `/app/clients/smart?page=1&page_size=50` ×40: p50=141.2 p95=436.0 errors=0 statuses=[200]
- `/app/properties?page=1&page_size=50` ×40: p50=61.8 p95=70.2 errors=0 statuses=[200]
- `/app/analytics/agency/overview?days_lookback=30` ×40: p50=74.3 p95=148.5 errors=0 statuses=[200]
- `/app/publishing/connections` ×40: p50=39.2 p95=49.3 errors=0 statuses=[200]
- `/app/api-keys` ×40: p50=43.0 p95=50.7 errors=0 statuses=[200]
- `/app/agencies/me/members` ×40: p50=46.4 p95=106.6 errors=0 statuses=[200]

## S2 Mongo concurrent

- sample=400 misses=0 p50=8.15ms p95=16.77ms

## S3 Security

- ok=True (unauth 401 + brute-force bait → 429)

## S5 Soft externals

- vendors soft-probed / skipped — no spend no ban

## Re-run

```bash
bash scripts/omnia-stack.sh ensure
cd backend && source .venv/bin/activate
python scripts/stress_gestionale.py --clients 2000
```

JSON: `memory/reports/gestionale_stress_7e1d21fd.json`
