# Pre-demo checklist (≥8 / 10)

**SoT:** `docs/audit/OMNIA_PRE_DEMO_8.md` · probe `scripts/pre_demo_probe.py`  
**Non sostituisce:** Stripe live · avvocato · hosting prod dedicato

## Automatico (ogni volta)

```bash
bash scripts/omnia-stack.sh ensure
cd /workspace && set -a && source backend/.env && set +a
backend/.venv/bin/python scripts/pre_demo_probe.py
```

Atteso: `ESITO=PASS` in `docs/ops/runs/pre-demo-8-live.log`.

Copre: bak OK → copia off-box → restore dry-run → `GET /app/ops/preflight` → GTM-01 smoke ~20.

## Manuale Founder (5–10 min)

| # | Azione | OK? |
|---|--------|-----|
| 1 | Apri FE pubblico (tunnel o :43123) — landing carica | ☐ |
| 2 | Login `demo.admin@…` — dashboard KPI sensati | ☐ |
| 3 | Portale search — ≥1 annuncio demo | ☐ |
| 4 | Billing — self-serve ON; prova «Attiva/Acquista» fino a Stripe Checkout test | ☐ |
| 5 | Founder Ops — bak OK + off-box presente; alert non rossi critici | ☐ |
| 6 | Un upload foto tmp su immobile demo | ☐ |

## Env prod-ish

| Var | Nota |
|-----|------|
| `OFFBOX_BACKUP_ROOT` | Volume **esterno** alla macchina API (non solo `/tmp`) |
| `OMNIA_SELF_SERVE_ENABLED=true` | S9 |
| `STRIPE_MODE=test` | finché non firmi live |
| `BACKUP_RETENTION_DAYS=7` | S2 |

## Blocca demo se

- preflight FAIL (bak assente/stale, off-box missing, self-serve OFF)
- restore dry-run FAIL
- GTM-01 FAIL
- Checkout self-serve 503
