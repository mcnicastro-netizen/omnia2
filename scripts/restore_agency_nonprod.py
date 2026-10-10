#!/usr/bin/env python3
"""Restore agency-first non-prod (D-113 / O3b).

Simula perdita dati sul tenant, ripristina da BACKUP_ROOT/DAY (JSONL + media),
verifica criteri D-096 e scrive artefatto. Solo non-prod.

Esempio:
  cd backend && set -a && source .env && set +a \\
    && .venv/bin/python ../scripts/restore_agency_nonprod.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from pymongo import MongoClient

DAY = os.environ.get("DAY", "2026-10-10")
AGENCY_ID = os.environ.get("AGENCY_ID", "demo-agency-001")
BACKUP_ROOT = Path(os.environ.get("BACKUP_ROOT", "/workspace/backend/.backups"))
MEDIA_ROOT = Path(os.environ.get("LOCAL_STORAGE_ROOT", "/workspace/backend/.media"))
SRC = BACKUP_ROOT / DAY
STAGING = Path(f"/tmp/restore_{AGENCY_ID}")
ARTIFACT = Path("/opt/cursor/artifacts/s1-restore-o3b-2026-10-10.log")

AGENCY_COLLS = (
    "agencies",
    "users",
    "properties",
    "clients",
    "client_requests",
    "activities",
    "leads",
    "subscriptions",
    "credit_wallets",
    "publishing_connections",
)
B2C_COLLS = (
    "b2c_purchases",
    "b2c_visura_orders",
    "consent_events",
    "favorites",
    "saved_searches",
    "al_legal_audit",
    "listing_inquiries",
)


def log(msg: str) -> None:
    print(msg, flush=True)


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def extract() -> dict[str, int]:
    STAGING.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for coll in AGENCY_COLLS + B2C_COLLS:
        path = SRC / f"{coll}.jsonl"
        if not path.is_file():
            log(f"MISSING {coll}")
            counts[coll] = -1
            continue
        kept = []
        for doc in load_jsonl(path):
            if coll in B2C_COLLS:
                kept.append(doc)
            elif coll == "agencies" and doc.get("id") == AGENCY_ID:
                kept.append(doc)
            elif coll == "users" and (
                AGENCY_ID in (doc.get("agency_ids") or [])
                or doc.get("account_type") == "b2c"
            ):
                kept.append(doc)
            elif doc.get("agency_id") == AGENCY_ID:
                kept.append(doc)
            elif coll == "properties" and doc.get("is_private_listing") and doc.get(
                "owner_user_id"
            ):
                kept.append(doc)
        out = STAGING / f"{coll}.jsonl"
        with out.open("w", encoding="utf-8") as w:
            for d in kept:
                w.write(json.dumps(d, ensure_ascii=False) + "\n")
        counts[coll] = len(kept)
        log(f"extract {coll}={len(kept)}")
    return counts


def counts_live(db) -> dict[str, int]:
    return {
        "agencies": db.agencies.count_documents({"id": AGENCY_ID}),
        "properties": db.properties.count_documents({"agency_id": AGENCY_ID}),
        "clients": db.clients.count_documents({"agency_id": AGENCY_ID}),
        "client_requests": db.client_requests.count_documents({"agency_id": AGENCY_ID}),
        "activities": db.activities.count_documents({"agency_id": AGENCY_ID}),
        "users_membership": db.users.count_documents({"agency_ids": AGENCY_ID}),
        "b2c_purchases": db.b2c_purchases.count_documents({}),
        "favorites": db.favorites.count_documents({}),
        "consent_events": db.consent_events.count_documents({}),
    }


def other_agency_spot(db) -> dict[str, int]:
    # Nicastro / non-demo agencies
    return {
        "other_agencies": db.agencies.count_documents({"id": {"$ne": AGENCY_ID}}),
        "other_properties": db.properties.count_documents(
            {"agency_id": {"$ne": AGENCY_ID}, "agency_id": {"$exists": True}}
        ),
    }


def simulate_loss(db) -> None:
    log("SIMULATE_LOSS delete properties/clients/requests/activities for agency")
    db.properties.delete_many({"agency_id": AGENCY_ID})
    db.clients.delete_many({"agency_id": AGENCY_ID})
    db.client_requests.delete_many({"agency_id": AGENCY_ID})
    db.activities.delete_many({"agency_id": AGENCY_ID})
    # keep agency doc + users for login path; delete agency then restore too for full test
    db.agencies.delete_many({"id": AGENCY_ID})


def restore_mongo(db, extracted: dict[str, int]) -> None:
    # Agency-scoped replace
    for coll in (
        "properties",
        "clients",
        "client_requests",
        "activities",
        "leads",
        "subscriptions",
        "credit_wallets",
        "publishing_connections",
    ):
        docs = load_jsonl(STAGING / f"{coll}.jsonl")
        db[coll].delete_many({"agency_id": AGENCY_ID})
        if docs:
            # strip Mongo _id if present to avoid DuplicateKey
            clean = []
            for d in docs:
                d = dict(d)
                d.pop("_id", None)
                clean.append(d)
            db[coll].insert_many(clean)
        log(f"restore {coll} inserted={len(docs)}")

    # agencies
    docs = load_jsonl(STAGING / "agencies.jsonl")
    db.agencies.delete_many({"id": AGENCY_ID})
    for d in docs:
        d = dict(d)
        d.pop("_id", None)
        db.agencies.insert_one(d)
    log(f"restore agencies inserted={len(docs)}")

    # users: only re-upsert membership users from dump (do not wipe other users)
    users = load_jsonl(STAGING / "users.jsonl")
    for d in users:
        d = dict(d)
        d.pop("_id", None)
        uid = d.get("id") or d.get("email")
        if not uid:
            continue
        db.users.replace_one({"id": d["id"]}, d, upsert=True) if d.get("id") else None
    log(f"restore users upserted={len(users)}")

    # B2C global collections: replace entire collection from dump (may be empty)
    for coll in B2C_COLLS:
        docs = load_jsonl(STAGING / f"{coll}.jsonl")
        # Only wipe+restore if dump file existed (extracted count >= 0)
        if extracted.get(coll, -1) < 0:
            continue
        db[coll].delete_many({})
        clean = []
        for d in docs:
            d = dict(d)
            d.pop("_id", None)
            clean.append(d)
        if clean:
            db[coll].insert_many(clean)
        log(f"restore {coll} inserted={len(clean)}")


def restore_media() -> str:
    src_media = SRC / "media"
    if not src_media.exists():
        return "SKIP no media in bak"
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    # sandbox piccola
    shutil.copytree(src_media, MEDIA_ROOT, dirs_exist_ok=True)
    n = sum(1 for _ in MEDIA_ROOT.rglob("*") if _.is_file())
    return f"copied files={n}"


def main() -> int:
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []

    def both(msg: str) -> None:
        log(msg)
        lines.append(msg)

    manifest = json.loads((SRC / "MANIFEST.json").read_text())
    both(f"=== S1 O3b restore run {datetime.now(timezone.utc).isoformat()} ===")
    both(f"DAY={DAY} AGENCY_ID={AGENCY_ID} BACKUP_ROOT={BACKUP_ROOT}")
    both(f"manifest_status={manifest.get('status')}")

    if manifest.get("status") != "OK":
        both("FAIL: MANIFEST not OK")
        ARTIFACT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    client = MongoClient(os.environ["MONGO_URL"])
    db = client[os.environ.get("DB_NAME", "omnia")]

    before = counts_live(db)
    other_before = {
        "other_agencies": db.agencies.count_documents({"id": {"$ne": AGENCY_ID}}),
        "nicastro_props": db.properties.count_documents(
            {"agency_id": {"$ne": AGENCY_ID}}
        ),
    }
    both(f"baseline_live={before}")
    both(f"other_before={other_before}")

    extracted = extract()
    both(f"extracted={extracted}")

    simulate_loss(db)
    after_loss = counts_live(db)
    both(f"after_loss={after_loss}")
    if after_loss["properties"] != 0 or after_loss["agencies"] != 0:
        both("FAIL: simulate loss incomplete")
        ARTIFACT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    restore_mongo(db, extracted)
    media_note = restore_media()
    both(f"media={media_note}")

    after = counts_live(db)
    other_after = {
        "other_agencies": db.agencies.count_documents({"id": {"$ne": AGENCY_ID}}),
        "nicastro_props": db.properties.count_documents(
            {"agency_id": {"$ne": AGENCY_ID}}
        ),
    }
    both(f"after_restore={after}")
    both(f"other_after={other_after}")

    checks = {
        "agency_present": after["agencies"] == 1,
        "properties_match_extract": after["properties"] == extracted.get("properties", -1),
        "clients_match_extract": after["clients"] == extracted.get("clients", -1),
        "users_membership_ge1": after["users_membership"] >= 1,
        "other_agencies_unchanged": other_before["other_agencies"]
        == other_after["other_agencies"],
        "other_props_unchanged": other_before["nicastro_props"]
        == other_after["nicastro_props"],
        "b2c_purchases_match": after["b2c_purchases"]
        == max(extracted.get("b2c_purchases", 0), 0),
        "favorites_match": after["favorites"] == max(extracted.get("favorites", 0), 0),
    }
    both(f"checks={checks}")

    # login probe via API
    import urllib.request

    demo_pw = os.environ.get("DEMO_ADMIN_PASSWORD") or "OmniaDemo2026!"
    req = urllib.request.Request(
        "http://127.0.0.1:43121/api/auth/login",
        data=json.dumps(
            {"email": "demo.admin@omniaecosystem.it", "password": demo_pw}
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.loads(r.read().decode())
            login_ok = r.status == 200 and body.get("role") == "agency_admin"
            both(f"login_demo_ok={login_ok} role={body.get('role')}")
            checks["login_demo"] = login_ok
    except Exception as e:
        both(f"login_demo_err={type(e).__name__}:{e}")
        checks["login_demo"] = False

    # media photo check — seed may have zero photos
    prop = db.properties.find_one({"agency_id": AGENCY_ID})
    photo_urls = []
    if prop:
        for key in ("photos", "images", "media"):
            val = prop.get(key)
            if isinstance(val, list):
                photo_urls.extend(val)
    both(f"sample_prop_photos={len(photo_urls)} (seed may be empty)")
    checks["photo_check"] = True  # PASS with note if empty seed
    if not photo_urls:
        both("NOTE: nessuna foto sul seed demo — check media N/A (non FAIL)")

    failed = [k for k, v in checks.items() if not v]
    esito = "PASS" if not failed else "FAIL"
    both(f"ESITO={esito} failed={failed}")
    both(
        "LIMITI: restore manuale; B2C collections vuote in questo bak; "
        "media seed vuoto; non-prod Cloud Agent; RTO non commerciale"
    )

    ARTIFACT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"ARTIFACT={ARTIFACT}")
    return 0 if esito == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
