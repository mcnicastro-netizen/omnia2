"""W3 — concurrent CommercialCustomer create for same P.IVA (Mongo real).

Unique index (country_code, vat_number_normalized) is SoT. Two racing inserts
must yield exactly one CC; losers re-read existing. Does NOT change 1 P.IVA = 1 CC.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from pymongo import MongoClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://127.0.0.1:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")
# Digits-only VAT body so normalize_vat_number keeps uniqueness predictable.
_RUN_DIGITS = "".join(c for c in uuid.uuid4().hex if c.isdigit())[:8].ljust(8, "0")
RUN = f"9{_RUN_DIGITS}"  # 9 + 8 digits → 9-digit unique prefix


def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.isfile(env_path):
        return
    for line in open(env_path, encoding="utf-8", errors="ignore"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() in {"MONGO_URL", "DB_NAME"}:
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


@pytest.fixture
def mongo():
    _load_env()
    try:
        client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=2500)
        client.admin.command("ping")
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"Mongo unavailable: {e}")
    db = client[DB_NAME]
    yield db
    db.commercial_customers.delete_many(
        {"vat_number_normalized": {"$regex": f"^{RUN}"}}
    )
    db.commercial_customers.delete_many({"legal_name": {"$regex": f"Race Co {RUN}"}})


def test_unique_index_exists(mongo):
    names = {ix["name"] for ix in mongo.commercial_customers.list_indexes()}
    assert "country_code_1_vat_number_normalized_1" in names


def test_concurrent_get_or_create_single_cc(mongo):
    _load_env()
    from shared.db.connection import Database
    from shared.auth.commercial_customer_service import get_or_create_commercial_customer

    Database.reset()
    Database.connect()
    from shared.models.commercial_customer import normalize_vat_number

    vat_raw = f"{RUN}123456"
    vat_norm = normalize_vat_number(vat_raw)
    legal = f"Race Co {RUN}"

    async def one():
        db = Database.get()
        return await get_or_create_commercial_customer(
            db, vat_number=vat_raw, legal_name=legal, country_code="IT"
        )

    async def race():
        return await asyncio.gather(one(), one(), one(), one())

    results = asyncio.run(race())
    ids = {r["id"] for r in results}
    assert len(ids) == 1, ids
    assert all(r.get("vat_number_normalized") == vat_norm for r in results)
    n = mongo.commercial_customers.count_documents(
        {"country_code": "IT", "vat_number_normalized": vat_norm}
    )
    assert n == 1


def test_duplicate_key_on_raw_insert_rejected(mongo):
    from shared.models.commercial_customer import normalize_vat_number

    vat = normalize_vat_number(f"{RUN}999001")
    doc = {
        "id": str(uuid.uuid4()),
        "country_code": "IT",
        "vat_number_normalized": vat,
        "legal_name": "Dup",
    }
    mongo.commercial_customers.insert_one(doc)
    with pytest.raises(Exception):
        mongo.commercial_customers.insert_one(
            {**doc, "id": str(uuid.uuid4())}
        )
    assert (
        mongo.commercial_customers.count_documents(
            {"country_code": "IT", "vat_number_normalized": vat}
        )
        == 1
    )
