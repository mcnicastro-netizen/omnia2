# Pre-demo ≥8 — hardening operativo

**Data:** 10 Ottobre 2026  
**Stato:** ✅ codice + LIVE  
**Decisione:** **D-122**  
**Checklist operativa:** `docs/ops/PRE_DEMO_CHECKLIST.md`

---

## Obiettivo

Salire da ~6/10 a **≥8/10** prima di inviare demo (non outreach 5k).

## Cosa è stato chiuso

| Area | Deliverable |
|------|-------------|
| Bak off-box | `offbox_backup.py` + hook post-bak · `OFFBOX_BACKUP_ROOT` |
| Restore dry-run | `scripts/restore_dry_run.py` (hot + off-box, zero write Mongo) |
| Monitoring | `GET /api/app/ops/preflight` · alert bak stale / off-box fail |
| Prospect + smoke | riuso `gtm01_smoke.py` nel probe unico |
| C5 trash | KPI dashboard + MLS inventory/search escludono `deleted_at` |
| Runbook | checklist + probe `pre_demo_probe.py` |

## Cosa resta Founder / esterni

- Stripe **live** keys  
- `OFFBOX_BACKUP_ROOT` su volume vero (prod)  
- Revisione legale / DPA  
- Outreach contenuto  
- S3.1 / D-038  

## Prove

- LIVE: `docs/ops/runs/pre-demo-8-live.log`  
- Unit: `backend/tests/test_pre_demo_8.py`
