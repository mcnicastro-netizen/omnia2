#!/usr/bin/env python3
"""S3 — meter economia storage (live + bak post-S2) + scenari vs listino.

Scrive artefatto JSON/testo. Non modifica listino.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

ARTIFACT = Path("/opt/cursor/artifacts/s3-meter-economia.log")
DURABLE = Path(__file__).resolve().parents[1] / "docs/ops/runs/s3-meter-economia.log"

# Listino D-085 (fermo finché Founder non decide altrimenti)
CANONI = {"starter": 49.0, "pro": 99.0, "agency": 299.0}
QUOTA_GB = {"starter": 30, "pro": 100, "agency": 300}
ADDON_GB = 100
ADDON_EUR = 15.0

# Sensitivity €/GB/mese ops (non confermato da fattura cloud — D-114)
EUR_PER_GB = (0.02, 0.04, 0.08)

# Multiplicatori disco ops post-S2 (hardlink + retention 7)
# base = live; bak unique ≈ live * (1 + churn*6) circa; JSONL trascurabile vs media
MULTIPLIERS = {
    "best_no_churn": 1.05,   # hardlink ≈1× + JSONL/overhead
    "mid_churn": 2.5,        # O0 mid (~2–4×)
    "worst_daily_rewrite": 7.2,  # ogni giorno riscrittura completa ×7 + overhead
}


def du_sb(path: Path) -> int:
    if not path.exists():
        return 0
    r = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        return 0
    return int(r.stdout.split()[0])


def scenario_rows() -> list[dict]:
    rows = []
    for tier, live_gb in QUOTA_GB.items():
        canon = CANONI[tier]
        for mult_name, mult in MULTIPLIERS.items():
            ops_gb = live_gb * mult
            cell = {
                "tier": tier,
                "canone_eur": canon,
                "live_quota_gb": live_gb,
                "mult": mult_name,
                "mult_x": mult,
                "ops_gb": round(ops_gb, 1),
            }
            for rate in EUR_PER_GB:
                cost = ops_gb * rate
                cell[f"cost_at_{rate}"] = round(cost, 2)
                cell[f"margin_disk_at_{rate}"] = round(canon - cost, 2)
                cell[f"disk_pct_canone_at_{rate}"] = round(100.0 * cost / canon, 1)
            rows.append(cell)
    # Addon unit economics (incremental 100 GB live → ops × mid)
    ops = ADDON_GB * MULTIPLIERS["mid_churn"]
    addon: dict = {
        "tier": "addon_100gb",
        "canone_eur": ADDON_EUR,
        "live_quota_gb": ADDON_GB,
        "mult": "mid_churn",
        "mult_x": MULTIPLIERS["mid_churn"],
        "ops_gb": round(ops, 1),
    }
    for rate in EUR_PER_GB:
        cost = ops * rate
        addon[f"cost_at_{rate}"] = round(cost, 2)
        addon[f"margin_disk_at_{rate}"] = round(ADDON_EUR - cost, 2)
        addon[f"disk_pct_canone_at_{rate}"] = round(100.0 * cost / ADDON_EUR, 1)
    rows.append(addon)
    return rows


def main() -> int:
    lines: list[str] = []

    def both(m: str) -> None:
        print(m, flush=True)
        lines.append(m)

    media = Path(os.environ.get("LOCAL_STORAGE_ROOT") or "/workspace/backend/.media")
    bak = Path(os.environ.get("BACKUP_ROOT") or "/workspace/backend/.backups")

    both(f"=== S3 meter economia {datetime.now(timezone.utc).isoformat()} ===")
    both(f"MEDIA_ROOT={media} du_bytes={du_sb(media)}")
    both(f"BACKUP_ROOT={bak} du_bytes={du_sb(bak)}")

    try:
        from apps.immoweb.backup_job import BACKUP_RETENTION_DAYS, read_latest_backup_health

        both(f"BACKUP_RETENTION_DAYS={BACKUP_RETENTION_DAYS}")
        h = read_latest_backup_health()
        both(
            f"bak_health status={h.get('status')} day={h.get('day')} "
            f"retention={h.get('retention_days')} media_mode={h.get('media_mode')}"
        )
    except Exception as e:  # noqa: BLE001
        both(f"bak_health_err={type(e).__name__}:{e}")

    # Agency meters (async)
    try:
        import asyncio
        from shared.db.connection import Database
        from shared.storage.quota import get_storage_status

        async def _ag():
            db = Database.get()
            agencies = await db.agencies.find({}, {"_id": 0, "id": 1}).to_list(50)
            out = []
            for a in agencies:
                out.append(await get_storage_status(db, a["id"]))
            return out

        meters = asyncio.run(_ag())
        both(f"agency_meters={json.dumps(meters, ensure_ascii=False)}")
    except Exception as e:  # noqa: BLE001
        both(f"agency_meters_err={type(e).__name__}:{e}")
        meters = []

    rows = scenario_rows()
    both("scenario_table_json=" + json.dumps(rows, ensure_ascii=False))

    # Verdict helpers at reference 0.04 mid
    both("--- reference €0.04/GB · mid_churn 2.5× ---")
    for tier in ("starter", "pro", "agency"):
        live = QUOTA_GB[tier]
        ops = live * MULTIPLIERS["mid_churn"]
        cost = ops * 0.04
        both(
            f"{tier}: live={live}GB ops≈{ops:.0f}GB cost≈€{cost:.2f} "
            f"vs canone €{CANONI[tier]:.0f} → disk={100*cost/CANONI[tier]:.1f}% canone"
        )
    addon_ops = ADDON_GB * MULTIPLIERS["mid_churn"]
    addon_cost = addon_ops * 0.04
    both(
        f"addon +100GB: ops≈{addon_ops:.0f}GB cost≈€{addon_cost:.2f} "
        f"vs €{ADDON_EUR:.0f} → margin_disk≈€{ADDON_EUR-addon_cost:.2f}"
    )

    # Contrast as-is 32× (pre-S2)
    both("--- contrast pre-S2 full×30 (~31× bak tree ≈32× live+bak) @ €0.04 ---")
    for tier in ("starter", "pro", "agency"):
        live = QUOTA_GB[tier]
        ops = live * 32
        cost = ops * 0.04
        both(
            f"{tier}_preS2: ops≈{ops}GB cost≈€{cost:.2f} vs €{CANONI[tier]:.0f} "
            f"({'FAIL margin' if cost > CANONI[tier] else 'ok'})"
        )

    both(
        "VERDICT_PROPOSED=LISTINO_FERMO — post-S2 mid@0.04 Agency disk≈€30 "
        f"({100*30/299:.1f}% canone); addon mid@0.04 ancora positivo; "
        "€/GB fattura cloud ancora NON confermato — ricalibrare quando c’è bill reale."
    )
    both(
        "LIMITI: sandbox Cloud media≈0; scenari = modello post-S2 hardlink+7g; "
        "non firma Founder automatica; non revisione prezzi in questo script."
    )

    text = "\n".join(lines) + "\n"
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(text, encoding="utf-8")
    DURABLE.parent.mkdir(parents=True, exist_ok=True)
    DURABLE.write_text(text, encoding="utf-8")
    print(f"ARTIFACT={ARTIFACT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
