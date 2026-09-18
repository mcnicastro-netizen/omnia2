#!/usr/bin/env python3
"""Mini-sample accuracy check for the GIS valuator (Italy).

Does NOT claim full OMI ~27k coverage. Validates a representative sample:
  - curated cities in CITY_PRICES (exact band check)
  - small comuni via Nominatim → province fallback (province band ± tolerance)
  - relative ordering (high-price cities > low-price cities)

Auth: agency/admin session (base valuator requires login).
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

API = os.environ.get("OMNIA_API", "http://127.0.0.1:43121/api")
EMAIL = os.environ.get("OMNIA_QC_EMAIL", "mcnicastro@gmail.com")
PASSWORD = os.environ.get("OMNIA_QC_PASSWORD", "OmniaFounder2026!")
OUT_JSON = Path("/workspace/memory/reports/valuator_accuracy_sample_latest.json")
OUT_MD = Path("/workspace/memory/GESTIONALE_VALUATOR_ACCURACY_SAMPLE.md")

# Fixed property profile — multipliers appartamento×buono = 1.0
BASE = {
    "zone": "semicentro",
    "property_type": "appartamento",
    "surface_sqm": 80,
    "condition": "buono",
}

# Expected €/m² bands from curated dataset / province tables (semicentro).
# For curated cities: must match CITY_PRICES semicentro (min, max).
# For fallback towns: expected province semicentro band after ~12% small-town discount.
SAMPLE = [
    # —— curated (city_in_dataset) ——
    {"city": "Milano", "layer": "city", "band": (5500, 7500), "region_hint": "lombardia"},
    {"city": "Roma", "layer": "city", "band": (4000, 5500), "region_hint": "lazio"},
    {"city": "Napoli", "layer": "city", "band": (2200, 3200), "region_hint": "campania"},
    {"city": "Torino", "layer": "city", "band": (1900, 2700), "region_hint": "piemonte"},
    {"city": "Bologna", "layer": "city", "band": (3200, 4500), "region_hint": "emilia_romagna"},
    {"city": "Firenze", "layer": "city", "band": (3500, 4800), "region_hint": "toscana"},
    {"city": "Catania", "layer": "city", "band": (1200, 1700), "region_hint": "sicilia"},
    {"city": "Palermo", "layer": "city", "band": (1200, 1800), "region_hint": "sicilia"},
    {"city": "Bari", "layer": "city", "band": (1800, 2500), "region_hint": "puglia"},
    {"city": "Genova", "layer": "city", "band": (1800, 2500), "region_hint": "liguria"},
    {"city": "Venezia", "layer": "city", "band": (3500, 5000), "region_hint": "veneto"},
    {"city": "Cagliari", "layer": "city", "band": (1700, 2400), "region_hint": "sardegna"},
    # —— fallback province (small comuni, not in CITY_PRICES) ——
    # VA semicentro 1700-2300 × 0.88 small-town ≈ 1496-2024
    {"city": "Saronno", "layer": "province", "band": (1496, 2024), "province_hint": "VA"},
    # CT semicentro 1400-1900 × 0.88 ≈ 1232-1672
    {"city": "Belpasso", "layer": "province", "band": (1232, 1672), "province_hint": "CT"},
    # MO semicentro from province table — lookup at runtime if needed
    {"city": "Carpi", "layer": "province", "band": None, "province_hint": "MO"},
    # AQ
    {"city": "Sulmona", "layer": "province", "band": None, "province_hint": "AQ"},
]

# Relative order checks (avg €/m²)
ORDER_CHECKS = [
    ("Milano", "Catania"),
    ("Milano", "Bari"),
    ("Firenze", "Palermo"),
    ("Bologna", "Catania"),
]

TOLERANCE = 0.12  # ±12% vs expected band edges


def _province_band(sigla: str):
    from apps.immocloud.data.province_prices import PROVINCE_PRICES

    row = PROVINCE_PRICES.get(sigla) or {}
    sc = row.get("semicentro")
    if not sc:
        return None
    # small-town discount ~12% as in valuator province fallback path
    return (round(sc[0] * 0.88), round(sc[1] * 0.88))


def login() -> requests.Session:
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    r.raise_for_status()
    csrf = s.cookies.get("omnia_csrf")
    if csrf:
        s.headers["X-CSRF-Token"] = csrf
    return s


def in_band(avg: float, band: tuple[float, float], tol: float = TOLERANCE) -> bool:
    lo, hi = band
    return (lo * (1 - tol)) <= avg <= (hi * (1 + tol))


def main() -> int:
    # Enrich None bands from province table
    for row in SAMPLE:
        if row["band"] is None and row.get("province_hint"):
            row["band"] = _province_band(row["province_hint"])

    s = login()
    rows = []
    started = datetime.now(timezone.utc).isoformat()

    for spec in SAMPLE:
        payload = {**BASE, "city": spec["city"]}
        t0 = time.time()
        try:
            r = s.post(f"{API}/cloud/valuator", json=payload, timeout=90)
            ms = round((time.time() - t0) * 1000, 1)
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        except Exception as e:
            rows.append(
                {
                    "city": spec["city"],
                    "layer_expected": spec["layer"],
                    "status": "FAIL",
                    "reason": f"request_error:{e}",
                    "ms": None,
                }
            )
            print(f"[FAIL] {spec['city']} request_error {e}")
            continue

        if r.status_code != 200:
            rows.append(
                {
                    "city": spec["city"],
                    "layer_expected": spec["layer"],
                    "status": "FAIL",
                    "reason": f"http_{r.status_code}:{(r.text or '')[:120]}",
                    "ms": ms,
                }
            )
            print(f"[FAIL] {spec['city']} http {r.status_code}")
            continue

        pps = (data.get("price_per_sqm") or {}).get("avg")
        est = (data.get("estimated_value") or {}).get("avg")
        band = spec.get("band")
        fallback = data.get("fallback_used")
        in_ds = data.get("city_in_dataset")

        reasons = []
        ok = True

        if pps is None:
            ok = False
            reasons.append("missing_price_per_sqm")
        if est is None:
            ok = False
            reasons.append("missing_estimated_value")
        if pps and est and BASE["surface_sqm"]:
            expected_total = pps * BASE["surface_sqm"]
            if abs(expected_total - est) / max(expected_total, 1) > 0.05:
                ok = False
                reasons.append(f"value_inconsistent_vs_pps ({est} vs {expected_total})")

        if spec["layer"] == "city":
            if not in_ds:
                ok = False
                reasons.append("expected_city_dataset_hit")
            if fallback:
                ok = False
                reasons.append(f"unexpected_fallback:{fallback}")
        else:
            if in_ds:
                # still OK if city unexpectedly curated
                reasons.append("note:city_ unexpectedly_in_dataset")
            elif fallback not in ("province", "regional"):
                ok = False
                reasons.append(f"expected_province_or_regional_fallback got:{fallback}")

        if band and pps is not None:
            if not in_band(float(pps), band):
                ok = False
                reasons.append(f"pps_avg {pps} outside band {band} (±{int(TOLERANCE*100)}%)")

        status = "PASS" if ok else "FAIL"
        row = {
            "city": spec["city"],
            "layer_expected": spec["layer"],
            "layer_actual": "city" if in_ds else (fallback or "unknown"),
            "city_resolved": data.get("city_resolved"),
            "province_sigla": data.get("province_sigla"),
            "region": data.get("region"),
            "pps_avg": pps,
            "value_avg": est,
            "band": band,
            "confidence": data.get("confidence"),
            "data_source": (data.get("data_source") or "")[:120],
            "status": status,
            "reasons": reasons,
            "ms": ms,
            "http": r.status_code,
        }
        rows.append(row)
        note = "; ".join(reasons) if reasons else ""
        print(f"[{status}] {spec['city']:12} pps={pps} band={band} layer={row['layer_actual']} {ms}ms {note}")

    # Relative ordering
    by_city = {r["city"]: r for r in rows if r.get("pps_avg") is not None}
    order_rows = []
    for hi, lo in ORDER_CHECKS:
        a, b = by_city.get(hi), by_city.get(lo)
        if not a or not b:
            order_rows.append({"pair": f"{hi}>{lo}", "status": "SKIP", "detail": "missing result"})
            continue
        ok = a["pps_avg"] > b["pps_avg"]
        order_rows.append(
            {
                "pair": f"{hi}>{lo}",
                "status": "PASS" if ok else "FAIL",
                "detail": f"{a['pps_avg']} vs {b['pps_avg']}",
            }
        )
        print(f"[{'PASS' if ok else 'FAIL'}] order {hi} > {lo}: {a['pps_avg']} vs {b['pps_avg']}")

    finished = datetime.now(timezone.utc).isoformat()
    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    for r in rows + order_rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    run_id = uuid.uuid4().hex[:8]
    payload = {
        "meta": {
            "started": started,
            "finished": finished,
            "run_id": run_id,
            "sample_size": len(SAMPLE),
            "tolerance": TOLERANCE,
            "profile": BASE,
            "counts": counts,
            "note": (
                "Mini-sample only. Does not prove OMI ~27k zone accuracy. "
                "Curated cities checked vs CITY_PRICES semicentro; "
                "small comuni vs province×0.88 band."
            ),
        },
        "rows": rows,
        "order_checks": order_rows,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    # also dated copy
    dated = OUT_JSON.with_name(f"valuator_accuracy_sample_{run_id}.json")
    dated.write_text(OUT_JSON.read_text(encoding="utf-8"), encoding="utf-8")

    lines = [
        "# Valutatore — mini-sample accuratezza",
        "",
        f"**Run**: {started} → {finished} (`{run_id}`)",
        f"**Profilo**: {BASE}",
        f"**Tolleranza banda**: ±{int(TOLERANCE*100)}%",
        f"**Counts**: {counts}",
        "",
        "## Cosa valida (e cosa no)",
        "",
        "- Sì: campione rappresentativo (grandi città curate + comuni piccoli con fallback provincia).",
        "- Sì: €/m² medio dentro banda attesa (dataset curato / provincia×0.88).",
        "- Sì: ordinamento relativo Milano/Firenze/Bologna vs Catania/Palermo/Bari.",
        "- No: non è una prova sulle ~27.000 zone OMI ufficiali.",
        "",
        "## Risultati città",
        "",
        "| Città | Layer | €/m² avg | Banda attesa | Status | Note |",
        "|-------|-------|---------:|--------------|:------:|------|",
    ]
    for r in rows:
        band = r.get("band")
        band_s = f"{band[0]}–{band[1]}" if band else "—"
        note = "; ".join(r.get("reasons") or []) or "—"
        lines.append(
            f"| {r['city']} | {r.get('layer_actual')} | {r.get('pps_avg') or '—'} | {band_s} | **{r['status']}** | {note} |"
        )
    lines += [
        "",
        "## Ordinamenti relativi",
        "",
        "| Check | Status | Detail |",
        "|-------|:------:|--------|",
    ]
    for o in order_rows:
        lines.append(f"| `{o['pair']}` | **{o['status']}** | {o.get('detail') or ''} |")
    lines += [
        "",
        f"JSON: `{OUT_JSON}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("WROTE", OUT_MD, counts)
    return 0 if counts.get("FAIL", 0) == 0 else 1


if __name__ == "__main__":
    # Ensure backend imports work when enriching province bands
    sys.path.insert(0, "/workspace/backend")
    raise SystemExit(main())
