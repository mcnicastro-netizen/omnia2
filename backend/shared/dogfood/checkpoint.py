"""D-175 C7 — Unsigned checkpoints + Ed25519 pure verify (RFC 8032).

Signing is offline (Founder). This module builds unsigned payloads and verifies
signatures with the documented public key. Private keys are never loaded from
Dogfood secrets for operational signing.
"""
from __future__ import annotations

import hashlib
import uuid
from pathlib import Path
from typing import Any, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from shared.dogfood.jcanonical import (
    JOURNAL_FORMAT_VERSION,
    CanonicalError,
    canonical_json_bytes,
    validate_ts_utc,
)
from shared.dogfood.permanent import dogfood_root
from shared.dogfood.session_registry import RegistryError, sessions_root

CHECKPOINT_FORMAT_VERSION = "omnia.dogfood.checkpoint.v1"
DOMAIN_LOGICAL = "OMNIA_DOGFOOD_CHECKPOINT_V1"
SIGNATURE_ALG = "ed25519"
DOMAIN_SEPARATOR = b"\n"


def build_unsigned_checkpoint(
    *,
    session_id: str,
    seq: int,
    journal_tip_hash: str,
    closed_at: str,
    final_session_status: str,
    key_id: str = "founder-primary",
    checkpoint_id: Optional[str] = None,
) -> dict[str, Any]:
    validate_ts_utc(closed_at)
    if final_session_status not in (
        "COMPLETED",
        "INTERRUPTED",
        "ABORTED",
        "INVALID",
    ):
        raise RegistryError(f"invalid_final_session_status:{final_session_status}")
    if seq < 0:
        raise RegistryError("seq_negative")
    event_count = seq + 1
    payload = {
        "session_id": session_id,
        "checkpoint_id": checkpoint_id or str(uuid.uuid4()),
        "seq": seq,
        "event_count": event_count,
        "journal_tip_hash": journal_tip_hash,
        "closed_at": closed_at,
        "final_session_status": final_session_status,
        "journal_format_version": JOURNAL_FORMAT_VERSION,
        "checkpoint_format_version": CHECKPOINT_FORMAT_VERSION,
        "signature_alg": SIGNATURE_ALG,
        "key_id": key_id,
        "domain": DOMAIN_LOGICAL,
    }
    # MUST coherence
    if payload["event_count"] != payload["seq"] + 1:
        raise RegistryError("event_count_mismatch")
    if payload["domain"] != DOMAIN_LOGICAL:
        raise RegistryError("domain_mismatch")
    return payload


def checkpoint_message(payload: dict[str, Any]) -> bytes:
    if payload.get("domain") != DOMAIN_LOGICAL:
        raise RegistryError("domain_field_mismatch")
    return (
        DOMAIN_LOGICAL.encode("ascii")
        + DOMAIN_SEPARATOR
        + canonical_json_bytes(payload)
    )


def fingerprint_sha256(raw_public_key_32: bytes) -> str:
    if len(raw_public_key_32) != 32:
        raise RegistryError("pubkey_must_be_32_bytes")
    return "sha256:" + hashlib.sha256(raw_public_key_32).hexdigest()


def load_raw_pubkey(path: Path) -> bytes:
    """Load Ed25519 raw 32-byte public key.

    Accepted file formats:
    - 32 raw bytes
    - 64 hex chars (optional whitespace stripped)
    """
    data = path.read_bytes()
    if len(data) == 32:
        return data
    text = data.decode("utf-8").strip().replace(" ", "").replace("\n", "")
    if text.startswith("sha256:"):
        raise RegistryError("pubkey_file_is_fingerprint_not_key")
    if len(text) == 64 and all(c in "0123456789abcdefABCDEF" for c in text):
        return bytes.fromhex(text)
    raise RegistryError("pubkey_format_unrecognized")


def default_pubkey_path() -> Path:
    # docs/dogfood/c7_registry_verify.pub relative to repo root
    return Path(__file__).resolve().parents[3] / "docs" / "dogfood" / "c7_registry_verify.pub"


def verify_fingerprint(raw_pub: bytes, expected: str) -> None:
    fp = fingerprint_sha256(raw_pub)
    if fp != expected.strip():
        raise RegistryError("FINGERPRINT_MISMATCH")


def verify_checkpoint_signature(
    payload: dict[str, Any],
    signature_hex: str,
    *,
    raw_public_key: bytes,
    expected_fingerprint: Optional[str] = None,
) -> None:
    if payload.get("signature_alg") != SIGNATURE_ALG:
        raise RegistryError("signature_alg_mismatch")
    if expected_fingerprint:
        verify_fingerprint(raw_public_key, expected_fingerprint)
    if len(raw_public_key) != 32:
        raise RegistryError("pubkey_must_be_32_bytes")
    try:
        sig = bytes.fromhex(signature_hex.strip().lower())
    except ValueError as e:
        raise RegistryError("signature_hex_invalid") from e
    if len(sig) != 64:
        raise RegistryError("signature_length_invalid")
    msg = checkpoint_message(payload)
    pub = Ed25519PublicKey.from_public_bytes(raw_public_key)
    try:
        pub.verify(sig, msg)
    except InvalidSignature as e:
        raise RegistryError("SIGNED_INVALID") from e


def attach_signature(
    registry_root: Path,
    payload: dict[str, Any],
    signature_hex: str,
    *,
    raw_public_key: bytes,
    expected_fingerprint: Optional[str] = None,
) -> Path:
    """Verify and store signed checkpoint. Does not perform Founder signing."""
    verify_checkpoint_signature(
        payload,
        signature_hex,
        raw_public_key=raw_public_key,
        expected_fingerprint=expected_fingerprint,
    )
    sroot = sessions_root(registry_root) if registry_root.name != "sessions" else registry_root
    # If registry_root is dogfood root, sessions_root wraps it; if already sessions, use it.
    if (registry_root / "unsigned_checkpoints").exists():
        sroot = registry_root
    else:
        sroot = sessions_root(registry_root)
    out_dir = sroot / "signed_checkpoints"
    out_dir.mkdir(parents=True, exist_ok=True)
    cid = payload["checkpoint_id"]
    out = out_dir / f"{cid}.sig"
    if out.exists():
        raise RegistryError("checkpoint_signature_already_attached")
    out.write_text(signature_hex.strip().lower() + "\n", encoding="utf-8")
    # keep payload copy next to sig for verify
    (out_dir / f"{cid}.json").write_bytes(canonical_json_bytes(payload) + b"\n")
    return out
