"""OMNIA — TOTP MFA helpers (RFC 6238 via pyotp)."""
from __future__ import annotations

import base64
import hashlib
import io
import secrets
from typing import List, Optional, Tuple

import pyotp
import qrcode

from shared.auth.hashing import hash_password, verify_password
from shared.utils.crypto import encrypt_dict, decrypt_dict

ISSUER = "OMNIA"


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def encrypt_secret(secret: str) -> str:
    return encrypt_dict({"totp": secret})


def decrypt_secret(token: str) -> str:
    data = decrypt_dict(token)
    secret = (data or {}).get("totp") or ""
    if not secret:
        raise ValueError("mfa_secret_missing")
    return secret


def provisioning_uri(secret: str, email: str) -> str:
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=ISSUER)


def qr_png_data_uri(otpauth_uri: str) -> str:
    img = qrcode.make(otpauth_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def verify_totp(secret: str, code: str, *, window: int = 1) -> bool:
    code = (code or "").strip().replace(" ", "")
    if not code.isdigit() or len(code) not in (6, 8):
        return False
    totp = pyotp.TOTP(secret)
    return bool(totp.verify(code, valid_window=window))


def generate_backup_codes(n: int = 8) -> Tuple[List[str], List[str]]:
    """Return (plaintext_codes, hashed_codes). Show plaintext once."""
    plain: List[str] = []
    hashed: List[str] = []
    for _ in range(n):
        raw = secrets.token_hex(4).upper()  # 8 hex chars
        plain.append(raw)
        hashed.append(hash_password(raw))
    return plain, hashed


def consume_backup_code(stored_hashes: List[str], code: str) -> Optional[List[str]]:
    """If code matches a hash, return remaining hashes; else None."""
    code = (code or "").strip().upper().replace(" ", "")
    if not code:
        return None
    for i, h in enumerate(stored_hashes or []):
        if verify_password(code, h):
            return [x for j, x in enumerate(stored_hashes) if j != i]
    return None


def challenge_fingerprint(user_id: str, email: str) -> str:
    return hashlib.sha256(f"{user_id}:{email}".encode()).hexdigest()[:16]
