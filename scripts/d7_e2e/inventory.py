"""Persistent per-run inventory + intent ledger (API objects lack d7_run_id)."""
from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from .run_id import validate_run_id


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class CreatedInventory:
    """Track {collection: [id, ...]} and intents; flush atomically after every mutation.

    Used because product endpoints do not stamp ``d7_run_id``. Cleanup deletes
    by exact id from this inventory plus tagged seed docs. Intents cover the
    create→register window (D1).
    """

    FILENAME = "created_ids.json"

    def __init__(self, run_path: Path, run_id: str):
        self.run_id = validate_run_id(run_id)
        self.run_path = Path(run_path)
        self.path = self.run_path / self.FILENAME
        self._data: dict[str, Any] = {
            "run_id": self.run_id,
            "by_collection": {},
            "pending": [],  # mid-flush markers collection:id
            "intents": [],  # pre-HTTP create intents
            "uncertain": [],  # ambiguous reconcile — never auto-delete
            "meta": {},
        }
        if self.path.exists():
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if loaded.get("run_id") != self.run_id:
                raise RuntimeError("inventory_run_id_mismatch")
            # Merge defaults for older files
            for k, v in self._data.items():
                loaded.setdefault(k, v if not isinstance(v, dict) else {})
            self._data = loaded

    # ---------- register confirmed IDs ----------

    def register(
        self,
        collection: str,
        doc_id: str,
        *,
        source: str = "",
        created_by_run: bool = True,
    ) -> None:
        if not collection or not isinstance(collection, str):
            raise ValueError("collection_required")
        if not doc_id or not isinstance(doc_id, str):
            raise ValueError("doc_id_required")
        pending_key = f"{collection}:{doc_id}"
        self._data.setdefault("pending", [])
        if pending_key not in self._data["pending"]:
            self._data["pending"].append(pending_key)
        self._flush()
        bucket = self._data.setdefault("by_collection", {}).setdefault(collection, [])
        if doc_id not in bucket:
            bucket.append(doc_id)
        if pending_key in self._data["pending"]:
            self._data["pending"].remove(pending_key)
        meta = self._data.setdefault("meta", {})
        meta[pending_key] = {
            "source": source,
            "created_by_run": bool(created_by_run),
            "registered_at": _now(),
        }
        self._flush()

    def register_many(
        self,
        collection: str,
        ids: Iterable[str],
        *,
        source: str = "",
        created_by_run: bool = True,
    ) -> None:
        for i in ids:
            self.register(collection, i, source=source, created_by_run=created_by_run)

    # ---------- intent ledger (D1) ----------

    def open_intent(
        self,
        *,
        step: str,
        collection: str,
        correlation: dict[str, Any],
    ) -> str:
        """Write intent *before* HTTP create. Does not invent resource IDs."""
        intent_id = str(uuid.uuid4())
        rec = {
            "intent_id": intent_id,
            "run_id": self.run_id,
            "step": step,
            "collection": collection,
            "correlation": dict(correlation or {}),
            "status": "pending_create",
            "http_status": None,
            "resource_id": None,
            "ts_opened": _now(),
            "ts_closed": None,
        }
        self._data.setdefault("intents", []).append(rec)
        self._flush()
        return intent_id

    def _find_intent(self, intent_id: str) -> dict[str, Any]:
        for rec in self._data.get("intents") or []:
            if rec.get("intent_id") == intent_id:
                return rec
        raise KeyError(f"intent_not_found:{intent_id}")

    def confirm_intent(
        self,
        intent_id: str,
        resource_id: str,
        *,
        http_status: Any = None,
        source: str = "",
        created_by_run: bool = True,
    ) -> None:
        rec = self._find_intent(intent_id)
        rec["status"] = "created"
        rec["resource_id"] = resource_id
        rec["http_status"] = http_status
        rec["ts_closed"] = _now()
        self._flush()
        self.register(
            rec["collection"],
            resource_id,
            source=source or rec.get("step") or "",
            created_by_run=created_by_run,
        )

    def fail_intent(self, intent_id: str, *, http_status: Any = None, reason: str = "") -> None:
        rec = self._find_intent(intent_id)
        rec["status"] = "failed"
        rec["http_status"] = http_status
        rec["reason"] = reason
        rec["ts_closed"] = _now()
        self._flush()

    def mark_orphan_suspected(self, intent_id: str, *, http_status: Any = None) -> None:
        rec = self._find_intent(intent_id)
        rec["status"] = "orphan_suspected"
        rec["http_status"] = http_status
        rec["ts_closed"] = _now()
        self._flush()

    # Max reconcile attempts before marking reconcile_exhausted (still blocks CLEAN).
    MAX_RECONCILE_RETRIES = 3

    def _append_uncertain(self, entry: dict[str, Any]) -> None:
        bucket = self._data.setdefault("uncertain", [])
        # Dedup by intent_id when present
        iid = entry.get("intent_id")
        if iid:
            bucket[:] = [u for u in bucket if u.get("intent_id") != iid]
        bucket.append(entry)

    def reconcile_intent(
        self,
        intent_id: str,
        matches: list[str],
        *,
        source: str = "reconcile",
    ) -> str:
        """Correlate orphan intent. 0→uncertain (NOT failed), 1→reconciled, >1→uncertain.

        Zero matches do **not** prove the resource was never created (lag, wrong
        correlation, eventual consistency). CLEAN remains blocked.
        """
        rec = self._find_intent(intent_id)
        attempts = int(rec.get("reconcile_attempts") or 0) + 1
        rec["reconcile_attempts"] = attempts
        rec.setdefault("reconcile_log", []).append(
            {"ts": _now(), "attempt": attempts, "match_count": len(matches)}
        )

        if len(matches) == 0:
            # DEF-01: absence not proven → orphan_unconfirmed / uncertain
            if attempts >= self.MAX_RECONCILE_RETRIES:
                rec["status"] = "reconcile_exhausted"
                rec["reason"] = "reconcile_zero_matches_retries_exhausted"
            else:
                rec["status"] = "orphan_unconfirmed"
                rec["reason"] = "reconcile_zero_matches_unconfirmed"
            rec["ts_closed"] = None  # still open for further reconcile attempts
            self._append_uncertain(
                {
                    "intent_id": intent_id,
                    "collection": rec["collection"],
                    "candidate_ids": [],
                    "correlation": rec.get("correlation"),
                    "reason": rec["reason"],
                    "reconcile_attempts": attempts,
                    "ts": _now(),
                }
            )
            self._flush()
            return "uncertain"

        if len(matches) > 1:
            rec["status"] = "orphan_suspected"
            rec["reason"] = "reconcile_ambiguous"
            rec["ts_closed"] = None
            self._append_uncertain(
                {
                    "intent_id": intent_id,
                    "collection": rec["collection"],
                    "candidate_ids": list(matches),
                    "correlation": rec.get("correlation"),
                    "reason": "reconcile_ambiguous",
                    "reconcile_attempts": attempts,
                    "ts": _now(),
                }
            )
            self._flush()
            return "uncertain"

        # exactly one — clear uncertain entry for this intent
        rid = matches[0]
        rec["status"] = "reconciled"
        rec["resource_id"] = rid
        rec["ts_closed"] = _now()
        rec["reason"] = None
        bucket = self._data.setdefault("uncertain", [])
        self._data["uncertain"] = [u for u in bucket if u.get("intent_id") != intent_id]
        self._flush()
        self.register(rec["collection"], rid, source=source, created_by_run=True)
        return "reconciled"

    OPEN_INTENT_STATUSES = frozenset(
        {
            "pending_create",
            "orphan_suspected",
            "orphan_unconfirmed",
            "reconcile_exhausted",
        }
    )

    def open_intents(self) -> list[dict[str, Any]]:
        return [
            r
            for r in (self._data.get("intents") or [])
            if r.get("status") in self.OPEN_INTENT_STATUSES
        ]

    def has_open_intents(self) -> bool:
        return bool(self.open_intents())

    def has_uncertain(self) -> bool:
        return bool(self._data.get("uncertain"))

    def pending_id_pairs(self) -> list[tuple[str, str]]:
        """Parse pending keys ``collection:id`` for cleanup (D2)."""
        out: list[tuple[str, str]] = []
        for key in self._data.get("pending") or []:
            if not isinstance(key, str) or ":" not in key:
                continue
            coll, doc_id = key.split(":", 1)
            if coll and doc_id:
                out.append((coll, doc_id))
        return out

    def certification_ok(self) -> bool:
        """CLEAN inventory preconditions (not full cleanup proof)."""
        return (
            not self.has_pending()
            and not self.has_open_intents()
            and not self.has_uncertain()
        )

    def as_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(self._data))

    def all_ids(self) -> dict[str, list[str]]:
        return {k: list(v) for k, v in (self._data.get("by_collection") or {}).items()}

    def has_pending(self) -> bool:
        return bool(self._data.get("pending"))

    def meta_for(self, collection: str, doc_id: str) -> dict[str, Any]:
        return dict((self._data.get("meta") or {}).get(f"{collection}:{doc_id}") or {})

    def _flush(self) -> None:
        self.run_path.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._data, indent=2, sort_keys=True) + "\n"
        fd, tmp = tempfile.mkstemp(
            prefix=".created_ids.",
            suffix=".tmp",
            dir=str(self.run_path),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.path)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise


def load_inventory(run_path: Path, run_id: str) -> CreatedInventory | None:
    p = Path(run_path) / CreatedInventory.FILENAME
    if not p.exists():
        return None
    return CreatedInventory(run_path, run_id)


def reconcile_by_correlation(
    db: Any,
    collection: str,
    correlation: dict[str, Any],
) -> list[str]:
    """Lookup helper for orphan reconcile — exact field equality only (no regex wipe)."""
    if not correlation:
        return []
    # Only allow equality filters on known scalar fields
    flt: dict[str, Any] = {}
    for k, v in correlation.items():
        if k.startswith("$"):
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            flt[k] = v
    if not flt:
        return []
    coll = db[collection]
    ids: list[str] = []
    for doc in coll.find(flt, {"_id": 0, "id": 1}):
        if doc.get("id"):
            ids.append(doc["id"])
    return ids
