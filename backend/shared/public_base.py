"""Resolve the public portal base URL for emails / absolute links (P-019).

Priority:
1. Live tunnel file written by omnia-stack (`SHARE_URL` / `PUBLIC_BASE_URL`)
2. Non-localhost FRONTEND_BASE_URL / FRONTEND_URL / OMNIA_PUBLIC_URL
3. Localhost env (dev only)
4. Production fallback
"""
from __future__ import annotations

import os
import re
from pathlib import Path

_TUNNEL_RE = re.compile(r"^https://[a-z0-9-]+\.trycloudflare\.com/?$")
_SHARE_CANDIDATES = (
    Path("/tmp/omnia-stack/PUBLIC_BASE_URL.txt"),
    Path("/tmp/omnia-stack/SHARE_URL.txt"),
)
_PROD_FALLBACK = "https://omniarealestateecosystem.it"


def _norm(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _is_tunnel(url: str) -> bool:
    return bool(_TUNNEL_RE.match(_norm(url) + "/") or _TUNNEL_RE.match(_norm(url)))


def _is_localhost(url: str) -> bool:
    u = _norm(url).lower()
    return u.startswith("http://127.0.0.1") or u.startswith("http://localhost")


def get_public_base_url() -> str:
    for path in _SHARE_CANDIDATES:
        try:
            if path.is_file():
                u = _norm(path.read_text(encoding="utf-8").splitlines()[0] if path.stat().st_size else "")
                if _is_tunnel(u):
                    return u
        except OSError:
            pass

    candidates = [
        os.environ.get("FRONTEND_BASE_URL"),
        os.environ.get("FRONTEND_URL"),
        os.environ.get("OMNIA_PUBLIC_URL"),
    ]
    non_local = [_norm(c) for c in candidates if c and not _is_localhost(c)]
    for u in non_local:
        if u:
            return u
    for c in candidates:
        u = _norm(c or "")
        if u:
            return u
    return _PROD_FALLBACK
