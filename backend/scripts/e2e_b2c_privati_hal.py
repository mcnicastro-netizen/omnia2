#!/usr/bin/env python3
"""Simulate N private B2C sellers: register → listing+photos → HAL improve → tools."""
from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

import httpx

BASE = "http://127.0.0.1:43121/api"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 25
OUT = Path("/opt/cursor/artifacts") if Path("/opt/cursor/artifacts").exists() else Path("/workspace/memory/reports")
OUT.mkdir(parents=True, exist_ok=True)

CITIES = [
    ("Milano", "20121", "Via Torino"),
    ("Roma", "00184", "Via Nazionale"),
    ("Torino", "10121", "Via Garibaldi"),
    ("Firenze", "50122", "Via dei Neri"),
    ("Bologna", "40121", "Via Indipendenza"),
    ("Napoli", "80133", "Via Toledo"),
    ("Genova", "16121", "Via XX Settembre"),
    ("Verona", "37121", "Corso Porta Nuova"),
    ("Padova", "35121", "Via Roma"),
    ("Palermo", "90133", "Via Maqueda"),
]
TYPES = ["appartamento", "villa", "loft", "attico", "monolocale"]
RAW_DESCRIPTIONS = [
    "Casa carina zona centrale da rivedere un po.",
    "Bel trilocale luminoso vicino metro. Cucina ok.",
    "Appartamento vuoto da arredare, terzo piano senza ascensore.",
    "Bilocale ristrutturato, balcone piccolo, silenzioso.",
    "Attico con terrazzo vista citta, da aggiornare foto.",
]


async def hal_improve(c: httpx.AsyncClient, field: str, text: str, property_data: dict) -> Dict[str, Any]:
    try:
        r = await c.post(
            "/app/al/improve",
            json={
                "field": field,
                "current_text": text,
                "property_data": property_data,
                "target_lang": "it",
                "tone": "standard",
            },
            timeout=120.0,
        )
    except Exception as e:
        return {
            "ok": False,
            "status": 0,
            "detail": f"{type(e).__name__}:{e}",
            "improved": "",
            "mentions_staging": False,
            "len_in": len(text or ""),
            "len_out": 0,
        }
    body = r.json() if "application/json" in (r.headers.get("content-type") or "") else {}
    improved = (body.get("improved") or "") if isinstance(body, dict) else ""
    low = improved.lower()
    mentions = any(k in low for k in ("virtual staging", "home staging", "staging", "arreda foto", "arredamento virtuale"))
    return {
        "ok": r.status_code == 200 and bool(improved),
        "status": r.status_code,
        "detail": body.get("detail") if isinstance(body, dict) else body,
        "improved": improved,
        "mentions_staging": mentions,
        "len_in": len(text or ""),
        "len_out": len(improved),
    }


async def one_user(i: int) -> Dict[str, Any]:
    row: Dict[str, Any] = {"i": i}
    try:
        return await _one_user_inner(i, row)
    except Exception as e:
        row["ok"] = False
        row["fatal"] = f"{type(e).__name__}:{e}"
        print(f"[{i+1}/{N}] FATAL {row['fatal']}", flush=True)
        return row


async def _one_user_inner(i: int, row: Dict[str, Any]) -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=BASE, timeout=httpx.Timeout(120.0, connect=30.0)) as c:
        email = f"privato.e2e.{i}.{uuid4().hex[:6]}@example.com"
        r = await c.post(
            "/cloud/auth/register",
            json={
                "email": email,
                "password": "PrivatoTest2026!",
                "name": f"Privato Demo {i:02d}",
                "intents": ["sell", "get_alerts"],
                "notification_channels": ["email"],
                "lang": "it",
                "gdpr_consent": True,
            },
        )
        row["register"] = {"ok": r.status_code in (200, 201), "status": r.status_code, "email": email}
        if not row["register"]["ok"]:
            row["ok"] = False
            return row

        city, cap, street = CITIES[i % len(CITIES)]
        ptype = TYPES[i % len(TYPES)]
        desc = RAW_DESCRIPTIONS[i % len(RAW_DESCRIPTIONS)]
        title = f"{ptype.title()} in {city} n.{i}"
        payload = {
            "title": title,
            "description": desc,
            "property_type": ptype,
            "operation": "sale",
            "city": city,
            "postal_code": cap,
            "address": f"{street} {10 + i}",
            "price": 180000 + i * 12500,
            "surface_sqm": 45 + (i % 8) * 10,
            "rooms": 2 + (i % 3),
            "bedrooms": 1 + (i % 2),
            "bathrooms": 1,
            "photos": [
                {"url": f"https://picsum.photos/seed/omnia{i}/800/600", "caption": "Soggiorno", "order": 0, "is_cover": True},
                {"url": f"https://picsum.photos/seed/omnia{i}b/800/600", "caption": "Cucina", "order": 1, "is_cover": False},
            ],
        }
        r = await c.post("/cloud/me/properties", json=payload)
        listing = r.json() if "application/json" in (r.headers.get("content-type") or "") else {}
        row["listing"] = {
            "ok": r.status_code in (200, 201),
            "status": r.status_code,
            "id": listing.get("id") if isinstance(listing, dict) else None,
            "photos": len((listing or {}).get("photos") or []) if isinstance(listing, dict) else 0,
            "title": title,
            "raw_desc": desc,
        }
        if not row["listing"]["ok"]:
            row["ok"] = False
            row["listing_error"] = listing
            return row

        pdata = {
            "title": title,
            "description": desc,
            "city": city,
            "property_type": ptype,
            "surface_sqm": payload["surface_sqm"],
            "rooms": payload["rooms"],
            "operation": "sale",
        }
        imp = await hal_improve(c, "description", desc, pdata)
        row["hal_description"] = {
            "ok": imp["ok"],
            "status": imp["status"],
            "detail": imp.get("detail"),
            "len_in": imp["len_in"],
            "len_out": imp["len_out"],
            "mentions_staging": imp["mentions_staging"],
            "sample": (imp.get("improved") or "")[:240],
        }
        if imp["ok"]:
            r = await c.patch(f"/cloud/me/properties/{listing['id']}", json={"description": imp["improved"]})
            row["apply_improve"] = {"ok": r.status_code == 200, "status": r.status_code}
        else:
            row["apply_improve"] = {"ok": False}

        # title improve skipped for throughput; description is the critical HAL path
        row["hal_title"] = {"ok": None, "skipped": True}

        r = await c.post(f"/cloud/me/properties/{listing['id']}/submit")
        row["submit"] = {"ok": r.status_code == 200, "status": r.status_code}

        tools = {}
        try:
            r = await c.post(
                "/cloud/valuator",
                json={"city": "Milano", "property_type": "appartamento", "surface_sqm": 80, "rooms": 3},
                timeout=60.0,
            )
            tools["valuator"] = {"status": r.status_code, "ok": r.status_code == 200}
        except Exception as e:
            tools["valuator"] = {"status": 0, "ok": False, "err": str(e)[:120]}
        try:
            r = await c.post(
                "/cloud/mutui/compare",
                json={
                    "property_price": 300000,
                    "down_payment": 60000,
                    "duration_years": 25,
                    "rate_type": "fisso",
                    "first_home": True,
                },
                timeout=60.0,
            )
            tools["mutui"] = {"status": r.status_code, "ok": r.status_code == 200}
        except Exception as e:
            tools["mutui"] = {"status": 0, "ok": False, "err": str(e)[:120]}
        try:
            r = await c.get("/cloud/search", params={"q": city, "page_size": 1}, timeout=30.0)
            tools["search"] = {"status": r.status_code, "ok": r.status_code == 200}
        except Exception as e:
            tools["search"] = {"status": 0, "ok": False, "err": str(e)[:120]}
        try:
            r = await c.get("/app/staging/styles", timeout=30.0)
            tools["staging_styles_as_b2c"] = {
                "status": r.status_code,
                "accessible_to_b2c": r.status_code == 200,
            }
        except Exception as e:
            tools["staging_styles_as_b2c"] = {"status": 0, "accessible_to_b2c": False, "err": str(e)[:120]}
        row["tools"] = tools

        row["ok"] = bool(
            row["register"]["ok"]
            and row["listing"]["ok"]
            and row["listing"]["photos"] >= 1
            and row["hal_description"]["ok"]
        )
        print(f"[{i+1}/{N}] ok={row['ok']} hal={row['hal_description']['ok']} email={email}", flush=True)
        return row


async def main() -> None:
    t0 = time.time()
    rows = []
    # sequential for LLM stability (each improve ~10-20s)
    for i in range(N):
        rows.append(await one_user(i))

    ok = sum(1 for r in rows if r.get("ok"))
    hal_ok = sum(1 for r in rows if (r.get("hal_description") or {}).get("ok"))
    staging_mentions = sum(
        1
        for r in rows
        if (r.get("hal_description") or {}).get("mentions_staging")
        or (r.get("hal_title") or {}).get("mentions_staging")
    )
    photos_ok = sum(1 for r in rows if (r.get("listing") or {}).get("photos", 0) >= 1)
    staging_api = sum(1 for r in rows if (r.get("tools") or {}).get("staging_styles_as_b2c", {}).get("accessible_to_b2c"))
    mutui_ok = sum(1 for r in rows if (r.get("tools") or {}).get("mutui", {}).get("ok"))
    valuator_ok = sum(1 for r in rows if (r.get("tools") or {}).get("valuator", {}).get("ok"))

    summary = {
        "n": N,
        "elapsed_s": round(time.time() - t0, 1),
        "profiles_full_ok": ok,
        "profiles_ok_pct": round(100.0 * ok / N, 1),
        "hal_improve_description_ok": hal_ok,
        "hal_improve_pct": round(100.0 * hal_ok / N, 1),
        "hal_text_mentions_virtual_staging": staging_mentions,
        "photos_on_listing_via_api": photos_ok,
        "sell_ui_photo_uploader": False,
        "sell_ui_suggests_virtual_staging": False,
        "staging_crm_api_open_to_b2c_count": staging_api,
        "mutui_ok": mutui_ok,
        "valuator_ok": valuator_ok,
        "pass_hal_improves_text": hal_ok == N,
        "pass_hal_suggests_virtual_staging": False,
        "pass_100_pct_user_claim": False,
    }
    if ok == N and hal_ok == N:
        summary["verdict"] = (
            "PASS al 100% su: registrazione privati, annunci con foto (API), HAL migliora testo. "
            "FAIL su: HAL/SellPage NON suggerisce Virtual Staging (feature assente nel percorso B2C)."
        )
        summary["pass_100_pct_user_claim"] = False  # because staging suggestion missing
        summary["pass_core_without_staging_claim"] = True
    else:
        summary["verdict"] = "FAIL — non tutti i profili hanno completato register+listing+HAL"
        summary["pass_core_without_staging_claim"] = False

    path = OUT / f"b2c_privati_hal_e2e_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"REPORT={path}")


if __name__ == "__main__":
    asyncio.run(main())
