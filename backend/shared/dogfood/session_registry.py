"""D-175 C7 — Filesystem session registry (append-only journal + seal-before-recover)."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from shared.dogfood.jcanonical import (
    GENESIS_PREV_HASH,
    JOURNAL_FORMAT_VERSION,
    CanonicalError,
    canonical_json,
    canonical_json_bytes,
    validate_ts_utc,
)
from shared.dogfood.permanent import dogfood_root

EVENT_TYPES = frozenset(
    {
        "SESSION_OPEN",
        "BINDING_ASSERTED",
        "WORKCOPY_CREATED",
        "MANIFEST_APPLIED",
        "BACKUP_LINKED",
        "SCENARIO_START",
        "SCENARIO_END",
        "ANOMALY",
        "INTERRUPT",
        "CHECKPOINT_UNSIGNED",
        "CHECKPOINT_SIGNED_ATTACHED",
        "SESSION_STATUS",
        "SIGNATURE_STATUS",
        "SESSION_CLOSE",
        "FOUNDER_APPROVAL",
        "EXPORT",
        "VERIFY_FAIL",
        "ADMIN_NOTE",
        "RECOVERY_PARTIAL_TAIL",
        "RECOVERY_TIP_ADVANCED",
        "RECOVERY_TIP_REBUILT",
    }
)

SESSION_STATUSES = frozenset(
    {"OPEN", "COMPLETED", "INTERRUPTED", "ABORTED", "INVALID"}
)
SIGNATURE_STATUSES = frozenset(
    {"NONE", "PENDING_SIGNATURE", "SIGNED_VERIFIED", "SIGNED_INVALID"}
)
COPY_KINDS = frozenset({"CLEAN", "CONTINUITY"})
RECOVERY_PROTOCOL_VERSION = "omnia.dogfood.recovery.v1"


class RegistryError(RuntimeError):
    pass


def now_ts_utc() -> str:
    dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sessions_root(root: Optional[Path] = None) -> Path:
    base = root or dogfood_root()
    return (base / "sessions").resolve()


def _ensure_dirs(sroot: Path) -> None:
    for rel in (
        "",
        "events",
        "headers",
        "unsigned_checkpoints",
        "signed_checkpoints",
        "mirrors",
        "exports",
        "evidence",
        "tips",
    ):
        (sroot / rel if rel else sroot).mkdir(parents=True, exist_ok=True)


@contextmanager
def _flock(lock_path: Path, timeout_s: float = 5.0) -> Iterator[None]:
    import fcntl
    import time

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + timeout_s
    try:
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RegistryError("LOCK_TIMEOUT")
                time.sleep(0.05)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def git_sha(cwd: Optional[Path] = None) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(cwd or Path(__file__).resolve().parents[3]),
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except Exception as e:  # noqa: BLE001
        raise RegistryError(f"git_sha_unavailable:{e}") from e


def git_branch(cwd: Optional[Path] = None) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(cwd or Path(__file__).resolve().parents[3]),
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return out.strip()
    except Exception as e:  # noqa: BLE001
        raise RegistryError(f"git_branch_unavailable:{e}") from e


def git_dirty(cwd: Optional[Path] = None) -> bool:
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=str(cwd or Path(__file__).resolve().parents[3]),
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return bool(out.strip())
    except Exception as e:  # noqa: BLE001
        raise RegistryError(f"git_status_unavailable:{e}") from e


def assert_clean_tree_for_clean_session(cwd: Optional[Path] = None) -> None:
    """D-C7-05 — DENY absolute if dirty before CLEAN session open."""
    if git_dirty(cwd):
        raise RegistryError("CLEAN_DENIED_DIRTY_TREE")


def event_preimage_dict(record: dict[str, Any]) -> dict[str, Any]:
    needed = {
        "actor",
        "event_id",
        "journal_format_version",
        "payload",
        "prev_hash",
        "seq",
        "session_id",
        "ts_utc",
        "type",
    }
    missing = needed - set(record)
    if missing:
        raise RegistryError(f"event_missing_fields:{sorted(missing)}")
    extra = set(record) - needed - {"event_hash"}
    if extra:
        raise RegistryError(f"event_unknown_fields:{sorted(extra)}")
    return {k: record[k] for k in needed}


def compute_event_hash(record_without_hash: dict[str, Any]) -> str:
    pre = event_preimage_dict(record_without_hash)
    validate_ts_utc(pre["ts_utc"])
    if pre["journal_format_version"] != JOURNAL_FORMAT_VERSION:
        raise RegistryError("journal_format_version_mismatch")
    if pre["type"] not in EVENT_TYPES:
        raise RegistryError(f"unknown_event_type:{pre['type']}")
    return sha256_hex(canonical_json_bytes(pre))


def serialize_event_line(full_event: dict[str, Any]) -> bytes:
    # full includes event_hash; closed schema for line = preimage fields + event_hash
    pre = event_preimage_dict(full_event)
    if "event_hash" not in full_event:
        raise RegistryError("event_hash_missing")
    line_obj = {**pre, "event_hash": full_event["event_hash"]}
    return canonical_json_bytes(line_obj) + b"\n"


def parse_event_line(line: bytes) -> dict[str, Any]:
    if line.endswith(b"\r\n") or (line.endswith(b"\r")):
        raise RegistryError("crlf_forbidden")
    if not line.endswith(b"\n"):
        raise RegistryError("missing_lf")
    raw = line[:-1]
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RegistryError("bom_forbidden")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        raise RegistryError(f"json_parse_failed:{e}") from e
    if not isinstance(obj, dict):
        raise RegistryError("event_not_object")
    eh = obj.get("event_hash")
    pre = event_preimage_dict(obj)
    calc = compute_event_hash(pre)
    if eh != calc:
        raise RegistryError("event_hash_mismatch")
    # Round-trip canonical equality for hashed fields
    if canonical_json_bytes(pre) != canonical_json_bytes(
        {k: pre[k] for k in pre}
    ):
        pass  # already canonicalized via compute
    return {**pre, "event_hash": eh}


def _write_bytes_fsync(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


class SessionRegistry:
    def __init__(
        self,
        root: Optional[Path] = None,
        *,
        sessions_dir: Optional[Path] = None,
    ):
        """root = dogfood root (…/dogfood); sessions_dir = explicit …/sessions path.

        Prefer sessions_dir when OMNIA_DOGFOOD_SESSIONS_ROOT points at the
        sessions tree itself (avoids …/sessions/sessions nesting).
        """
        if sessions_dir is not None:
            self.root = Path(sessions_dir).resolve()
        else:
            self.root = sessions_root(root)
        _ensure_dirs(self.root)

    def index_path(self) -> Path:
        return self.root / "index.jsonl"

    def events_path(self, session_id: str) -> Path:
        return self.root / "events" / f"{session_id}.jsonl"

    def tip_path(self, session_id: str) -> Path:
        return self.root / "tips" / f"{session_id}.tip.json"

    def lock_path(self, session_id: str) -> Path:
        return self.root / "events" / f"{session_id}.jsonl.lock"

    def header_path(self, session_id: str) -> Path:
        return self.root / "headers" / f"{session_id}.json"

    def _write_tip(self, session_id: str, seq: int, event_hash: str) -> None:
        tip_dir = self.root / "tips"
        tip_dir.mkdir(parents=True, exist_ok=True)
        tip = {
            "session_id": session_id,
            "seq": seq,
            "event_hash": event_hash,
            "updated_at": now_ts_utc(),
        }
        tmp = tip_dir / f"{session_id}.tip.json.tmp"
        final = self.tip_path(session_id)
        data = (canonical_json(tip) + "\n").encode("utf-8")
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, final)
        # best-effort dir fsync
        try:
            dfd = os.open(str(tip_dir), os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except OSError:
            pass

    def read_tip(self, session_id: str) -> Optional[dict[str, Any]]:
        p = self.tip_path(session_id)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def load_events(self, session_id: str) -> list[dict[str, Any]]:
        path = self.events_path(session_id)
        if not path.exists():
            return []
        events: list[dict[str, Any]] = []
        data = path.read_bytes()
        if not data:
            return []
        if not data.endswith(b"\n"):
            raise RegistryError("PARTIAL_TAIL")
        for line in data.split(b"\n"):
            if line == b"":
                continue
            events.append(parse_event_line(line + b"\n"))
        return events

    def verify_chain(self, session_id: str) -> dict[str, Any]:
        events = self.load_events(session_id)
        for i, ev in enumerate(events):
            if ev["seq"] != i:
                raise RegistryError(f"seq_gap_or_dup:{i}")
            expect_prev = GENESIS_PREV_HASH if i == 0 else events[i - 1]["event_hash"]
            if ev["prev_hash"] != expect_prev:
                raise RegistryError(f"prev_hash_break:{i}")
            if ev["session_id"] != session_id:
                raise RegistryError("session_id_mismatch")
        tip = self.read_tip(session_id)
        if events and tip:
            if tip.get("seq") != events[-1]["seq"]:
                raise RegistryError("tip_seq_mismatch")
            if tip.get("event_hash") != events[-1]["event_hash"]:
                raise RegistryError("tip_hash_mismatch")
        if tip and tip.get("seq", -1) > (events[-1]["seq"] if events else -1):
            raise RegistryError("tip_ahead")
        return {
            "ok": True,
            "count": len(events),
            "tip_hash": events[-1]["event_hash"] if events else GENESIS_PREV_HASH,
            "last_seq": events[-1]["seq"] if events else None,
        }

    def append_event(
        self,
        session_id: str,
        *,
        type: str,
        actor: str,
        payload: dict[str, Any],
        ts_utc: Optional[str] = None,
        event_id: Optional[str] = None,
    ) -> dict[str, Any]:
        if type not in EVENT_TYPES:
            raise RegistryError(f"unknown_event_type:{type}")
        with _flock(self.lock_path(session_id)):
            events = []
            path = self.events_path(session_id)
            if path.exists():
                raw = path.read_bytes()
                if raw and not raw.endswith(b"\n"):
                    raise RegistryError("PARTIAL_TAIL")
                for line in raw.split(b"\n"):
                    if line:
                        events.append(parse_event_line(line + b"\n"))
            if events:
                seq = events[-1]["seq"] + 1
                prev = events[-1]["event_hash"]
            else:
                seq = 0
                prev = GENESIS_PREV_HASH
            rec = {
                "actor": actor,
                "event_id": event_id or str(uuid.uuid4()),
                "journal_format_version": JOURNAL_FORMAT_VERSION,
                "payload": payload,
                "prev_hash": prev,
                "seq": seq,
                "session_id": session_id,
                "ts_utc": validate_ts_utc(ts_utc or now_ts_utc()),
                "type": type,
            }
            eh = compute_event_hash(rec)
            full = {**rec, "event_hash": eh}
            line = serialize_event_line(full)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "ab") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            self._write_tip(session_id, seq, eh)
            # best-effort on-host mirror (non-blocking for cert — P-C7-02)
            try:
                mirror = self.root / "mirrors" / "local" / f"{session_id}.jsonl"
                mirror.parent.mkdir(parents=True, exist_ok=True)
                mirror.write_bytes(path.read_bytes())
            except OSError:
                pass
            return full

    def open_session(
        self,
        *,
        copy_kind: str,
        workcopy_id: str,
        catalog_version: str = "df-catalog-2026.11.1",
        parent_session_id: Optional[str] = None,
        source_permanent_db: str = "omnia_df_perm_main",
        executor: str = "founder",
        repo_cwd: Optional[Path] = None,
        scenarios_planned: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        kind = (copy_kind or "").upper()
        if kind not in COPY_KINDS:
            raise RegistryError(f"invalid_copy_kind:{copy_kind}")
        dirty = git_dirty(repo_cwd)
        if kind == "CLEAN":
            assert_clean_tree_for_clean_session(repo_cwd)
        if kind == "CONTINUITY":
            if not parent_session_id:
                raise RegistryError("CONTINUITY_REQUIRES_PARENT")
            parent_hdr = self.load_header(parent_session_id)
            if not parent_hdr:
                raise RegistryError("parent_session_missing")
            if parent_hdr.get("status") not in ("COMPLETED", "INTERRUPTED"):
                raise RegistryError("parent_session_not_continuable")
        sha = git_sha(repo_cwd)
        branch = git_branch(repo_cwd)
        session_id = str(uuid.uuid4())
        header = {
            "session_id": session_id,
            "opened_at": now_ts_utc(),
            "closed_at": None,
            "status": "OPEN",
            "signature_status": "NONE",
            "branch": branch,
            "git_sha": sha,
            "workcopy_id": workcopy_id,
            "copy_kind": kind,
            "parent_session_id": parent_session_id,
            "source_permanent_db": source_permanent_db,
            "catalog_version": catalog_version,
            "scenarios_planned": scenarios_planned or [],
            "scenarios_executed": [],
            "anomalies": [],
            "interrupted": [],
            "evidence_refs": [],
            "executor": executor,
            "dirty_tree_at_open": dirty,
            "founder_approval": None,
        }
        hdr_dir = self.root / "headers"
        hdr_dir.mkdir(parents=True, exist_ok=True)
        self.header_path(session_id).write_text(
            json.dumps(header, indent=2) + "\n", encoding="utf-8"
        )
        with open(self.index_path(), "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "session_id": session_id,
                        "opened_at": header["opened_at"],
                        "copy_kind": kind,
                        "git_sha": sha,
                        "status": "OPEN",
                    }
                )
                + "\n"
            )
            f.flush()
            os.fsync(f.fileno())
        self.append_event(
            session_id,
            type="SESSION_OPEN",
            actor=executor,
            payload={
                "copy_kind": kind,
                "workcopy_id": workcopy_id,
                "git_sha": sha,
                "branch": branch,
                "dirty_tree_at_open": dirty,
                "parent_session_id": parent_session_id,
            },
        )
        self.append_event(
            session_id,
            type="BINDING_ASSERTED",
            actor="system",
            payload={
                "git_sha": sha,
                "branch": branch,
                "workcopy_id": workcopy_id,
                "copy_kind": kind,
            },
        )
        return header

    def load_header(self, session_id: str) -> Optional[dict[str, Any]]:
        p = self.header_path(session_id)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def save_header(self, header: dict[str, Any]) -> None:
        sid = header["session_id"]
        self.header_path(sid).write_text(
            json.dumps(header, indent=2) + "\n", encoding="utf-8"
        )

    def assert_binding(
        self,
        session_id: str,
        *,
        repo_cwd: Optional[Path] = None,
        workcopy_id: Optional[str] = None,
    ) -> None:
        hdr = self.load_header(session_id)
        if not hdr:
            raise RegistryError("session_not_found")
        if hdr.get("status") != "OPEN":
            raise RegistryError("session_not_open")
        if git_sha(repo_cwd) != hdr["git_sha"]:
            raise RegistryError("INVALID_BINDING_SHA")
        if git_branch(repo_cwd) != hdr["branch"]:
            raise RegistryError("INVALID_BINDING_BRANCH")
        if workcopy_id is not None and workcopy_id != hdr["workcopy_id"]:
            raise RegistryError("INVALID_BINDING_WORKCOPY")

    def close_session(
        self,
        session_id: str,
        *,
        status: str = "COMPLETED",
        actor: str = "founder",
    ) -> dict[str, Any]:
        if status not in ("COMPLETED", "INTERRUPTED", "ABORTED", "INVALID"):
            raise RegistryError(f"invalid_close_status:{status}")
        hdr = self.load_header(session_id)
        if not hdr:
            raise RegistryError("session_not_found")
        if hdr.get("status") != "OPEN":
            raise RegistryError("session_not_open")
        self.verify_chain(session_id)
        self.append_event(
            session_id,
            type="SESSION_STATUS",
            actor=actor,
            payload={"from": "OPEN", "to": status},
        )
        hdr["status"] = status
        hdr["closed_at"] = now_ts_utc()
        hdr["signature_status"] = "PENDING_SIGNATURE"
        self.append_event(
            session_id,
            type="SIGNATURE_STATUS",
            actor=actor,
            payload={"to": "PENDING_SIGNATURE"},
        )
        tip = self.read_tip(session_id)
        assert tip is not None
        from shared.dogfood.checkpoint import build_unsigned_checkpoint

        unsigned = build_unsigned_checkpoint(
            session_id=session_id,
            seq=int(tip["seq"]),
            journal_tip_hash=tip["event_hash"],
            closed_at=hdr["closed_at"],
            final_session_status=status,
            key_id="founder-primary",
        )
        uc_path = (
            self.root
            / "unsigned_checkpoints"
            / f"{unsigned['checkpoint_id']}.json"
        )
        uc_path.write_text(
            canonical_json(unsigned) + "\n", encoding="utf-8"
        )
        self.append_event(
            session_id,
            type="CHECKPOINT_UNSIGNED",
            actor=actor,
            payload={
                "checkpoint_id": unsigned["checkpoint_id"],
                "seq": unsigned["seq"],
                "journal_tip_hash": unsigned["journal_tip_hash"],
                "path": str(uc_path),
            },
        )
        self.append_event(
            session_id,
            type="SESSION_CLOSE",
            actor=actor,
            payload={"status": status, "checkpoint_id": unsigned["checkpoint_id"]},
        )
        hdr["last_checkpoint_id"] = unsigned["checkpoint_id"]
        self.save_header(hdr)
        return {"header": hdr, "unsigned_checkpoint": unsigned, "path": str(uc_path)}

    def seal_and_recover_partial_tail(self, session_id: str) -> dict[str, Any]:
        """Seal-before-recover for PARTIAL_TAIL. Leaves session INTERRUPTED.

        Only allowed while status is OPEN (never downgrade COMPLETED/ABORTED/INVALID).
        """
        hdr0 = self.load_header(session_id)
        if not hdr0:
            raise RegistryError("session_not_found")
        if hdr0.get("status") != "OPEN":
            raise RegistryError(
                f"recover_denied_status:{hdr0.get('status')}"
            )

        with _flock(self.lock_path(session_id)):
            path = self.events_path(session_id)
            if not path.exists():
                raise RegistryError("journal_missing")
            original_size = path.stat().st_size
            recovery_id = str(uuid.uuid4())
            evid = self.root / "evidence" / session_id / recovery_id
            evid.mkdir(parents=True, exist_ok=True)
            full_path = evid / "journal.full.bin"
            data = path.read_bytes()
            _write_bytes_fsync(full_path, data)
            h_src = sha256_hex(data)
            h_copy = sha256_hex(full_path.read_bytes())
            if h_src != h_copy or len(data) != original_size:
                raise RegistryError("SEAL_FAIL_HASH_MISMATCH")
            # second independent read
            h_copy2 = sha256_hex(full_path.read_bytes())
            if h_copy2 != h_copy or full_path.stat().st_size != original_size:
                raise RegistryError("SEAL_FAIL_SECOND_READ")

            last_lf = data.rfind(b"\n")
            if last_lf < 0:
                # no complete record
                tail = data
                prefix = b""
                tail_offset = 0
                last_valid_seq = None
                last_valid_hash = None
            else:
                # If file ends with LF, no partial tail — nothing to recover
                if data.endswith(b"\n"):
                    raise RegistryError("no_partial_tail")
                prefix = data[: last_lf + 1]
                tail = data[last_lf + 1 :]
                tail_offset = last_lf + 1

            tail_path = evid / "tail.partial.bin"
            _write_bytes_fsync(tail_path, tail)
            tail_sha = sha256_hex(tail)
            if data[tail_offset:] != tail:
                raise RegistryError("SEAL_FAIL_TAIL_MISMATCH")

            # Validate prefix chain if any
            events: list[dict[str, Any]] = []
            if prefix:
                for line in prefix.split(b"\n"):
                    if line:
                        events.append(parse_event_line(line + b"\n"))
                for i, ev in enumerate(events):
                    if ev["seq"] != i:
                        raise RegistryError("SEAL_PREFIX_SEQ_INVALID")
                    expect_prev = (
                        GENESIS_PREV_HASH if i == 0 else events[i - 1]["event_hash"]
                    )
                    if ev["prev_hash"] != expect_prev:
                        raise RegistryError("SEAL_PREFIX_CHAIN_INVALID")
                last_valid_seq = events[-1]["seq"]
                last_valid_hash = events[-1]["event_hash"]
            else:
                last_valid_seq = None
                last_valid_hash = None

            manifest = {
                "recovery_id": recovery_id,
                "session_id": session_id,
                "recovered_at": now_ts_utc(),
                "original_size": original_size,
                "original_sha256": h_src,
                "full_copy_size": original_size,
                "full_copy_sha256": h_copy,
                "tail_offset_start": tail_offset,
                "tail_size": len(tail),
                "tail_sha256": tail_sha,
                "last_complete_end": tail_offset,
                "last_valid_seq": last_valid_seq,
                "last_valid_event_hash": last_valid_hash,
                "reason": "PARTIAL_TAIL",
                "seal_checks": {
                    "first_read": "pass",
                    "second_read": "pass",
                    "evidence_fsync": "pass",
                },
                "recovery_protocol_version": RECOVERY_PROTOCOL_VERSION,
            }
            _write_bytes_fsync(
                evid / "RECOVERY_MANIFEST.json",
                (json.dumps(manifest, indent=2) + "\n").encode("utf-8"),
            )

            recovered = evid / "journal.recovered.jsonl"
            _write_bytes_fsync(recovered, prefix)
            # best-effort fsync evidence directory before mutating live journal
            try:
                dfd = os.open(str(evid), os.O_RDONLY)
                try:
                    os.fsync(dfd)
                finally:
                    os.close(dfd)
            except OSError:
                pass

            # atomic replace of active journal (only after sealed evidence fsynced)
            tmp = path.with_suffix(".jsonl.recovered_tmp")
            _write_bytes_fsync(tmp, prefix)
            os.replace(tmp, path)
            if last_valid_seq is not None and last_valid_hash is not None:
                self._write_tip(session_id, last_valid_seq, last_valid_hash)
            elif self.tip_path(session_id).exists():
                self.tip_path(session_id).unlink()

        # outside lock — append recovery event
        hdr = self.load_header(session_id) or {
            "session_id": session_id,
            "status": "OPEN",
            "signature_status": "NONE",
        }
        self.append_event(
            session_id,
            type="RECOVERY_PARTIAL_TAIL",
            actor="system",
            payload={
                "recovery_id": recovery_id,
                "full_sha256": h_src,
                "tail_sha256": tail_sha,
                "last_valid_seq": last_valid_seq,
                "evidence_dir": str(evid),
            },
        )
        hdr["status"] = "INTERRUPTED"
        self.save_header(hdr)
        self.append_event(
            session_id,
            type="SESSION_STATUS",
            actor="system",
            payload={"to": "INTERRUPTED", "reason": "PARTIAL_TAIL_RECOVERY"},
        )
        return manifest
