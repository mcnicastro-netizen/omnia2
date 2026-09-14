"""OMNIA — AES-256-GCM helper for encrypting portal credentials at rest.

Key source: env var CREDENTIALS_MASTER_KEY (base64-encoded 32 bytes).
If missing (dev), we derive a stable key from MONGO_URL — good enough for
preview, but must be replaced with a strong key in prod.
"""
import base64
import hashlib
import json
import logging
import os
from typing import Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _master_key() -> bytes:
    raw = os.environ.get("CREDENTIALS_MASTER_KEY")
    if raw:
        try:
            return base64.b64decode(raw)
        except Exception:
            pass
    # dev fallback — deterministic 32-byte key from MONGO_URL
    # R2: accettabile SOLO in preview/dev. In produzione impostare CREDENTIALS_MASTER_KEY.
    logging.getLogger("omnia.crypto").warning(
        "CREDENTIALS_MASTER_KEY non impostata — chiave derivata da MONGO_URL (solo dev/preview; configurarla in produzione)"
    )
    seed = (os.environ.get("MONGO_URL") or "omnia-dev-fallback").encode("utf-8")
    return hashlib.sha256(seed).digest()


def encrypt_dict(data: Dict[str, str]) -> str:
    """Return base64(nonce+ciphertext) for a JSON-serializable dict."""
    key = _master_key()
    aes = AESGCM(key)
    nonce = os.urandom(12)
    payload = json.dumps(data or {}, ensure_ascii=False).encode("utf-8")
    ct = aes.encrypt(nonce, payload, None)
    return base64.b64encode(nonce + ct).decode("ascii")


def decrypt_dict(token: str) -> Dict[str, str]:
    if not token:
        return {}
    key = _master_key()
    aes = AESGCM(key)
    raw = base64.b64decode(token)
    nonce, ct = raw[:12], raw[12:]
    payload = aes.decrypt(nonce, ct, None)
    return json.loads(payload.decode("utf-8"))
