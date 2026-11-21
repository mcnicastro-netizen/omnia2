"""Strict classification helpers — never PASS on unexpected status / 5xx / skipped checks."""
from __future__ import annotations

from typing import Any, Iterable, Optional


ALLOWED_DENY = frozenset({401, 403})
ALLOWED_CLIENT_ERROR = frozenset({400, 401, 403, 404, 409, 422})


def is_5xx(status: Any) -> bool:
    try:
        return 500 <= int(status) <= 599
    except (TypeError, ValueError):
        return False


def expect_status(
    step: str,
    status: Any,
    allowed: Iterable[int],
    *,
    body: Any = None,
) -> dict:
    """Return a step result dict. Unexpected / 5xx / missing → FAIL."""
    allowed_set = frozenset(int(x) for x in allowed)
    try:
        code = int(status)
    except (TypeError, ValueError):
        return {
            "step": step,
            "result": "FAIL",
            "status": status,
            "reason": "non_integer_status",
            "detail": _safe_detail(body),
        }
    if is_5xx(code):
        return {
            "step": step,
            "result": "FAIL",
            "status": code,
            "reason": "http_5xx",
            "detail": _safe_detail(body),
        }
    if code not in allowed_set:
        return {
            "step": step,
            "result": "FAIL",
            "status": code,
            "reason": "unexpected_status",
            "expected": sorted(allowed_set),
            "detail": _safe_detail(body),
        }
    return {
        "step": step,
        "result": "PASS",
        "status": code,
        "detail": _safe_detail(body),
    }


def expect_predicate(
    step: str,
    ok: bool,
    *,
    status: Any = None,
    reason: str = "predicate_failed",
    detail: Any = None,
) -> dict:
    if not ok:
        return {
            "step": step,
            "result": "FAIL",
            "status": status,
            "reason": reason,
            "detail": _safe_detail(detail),
        }
    return {
        "step": step,
        "result": "PASS",
        "status": status,
        "detail": _safe_detail(detail),
    }


def blocked(step: str, reason: str, detail: Any = None) -> dict:
    return {
        "step": step,
        "result": "BLOCKED",
        "reason": reason,
        "detail": _safe_detail(detail),
    }


def aggregate(steps: list[dict]) -> str:
    """PASS only if every step is PASS. Any FAIL → FAIL. Any BLOCKED (and no FAIL) → BLOCKED."""
    if not steps:
        return "FAIL"
    results = [s.get("result") for s in steps]
    if any(r is None or r == "NOT_RUN" for r in results):
        return "FAIL"
    if any(r == "FAIL" for r in results):
        return "FAIL"
    if any(r == "BLOCKED" for r in results):
        return "BLOCKED"
    if all(r == "PASS" for r in results):
        return "PASS"
    return "FAIL"


def _safe_detail(body: Any) -> Any:
    """Strip likely secrets from payloads for artifacts."""
    if body is None:
        return None
    if isinstance(body, dict):
        out = {}
        for k, v in body.items():
            lk = str(k).lower()
            if any(
                x in lk
                for x in ("password", "token", "secret", "api_key", "authorization", "cookie")
            ):
                out[k] = "[REDACTED]"
            else:
                out[k] = _safe_detail(v) if isinstance(v, (dict, list)) else v
        return out
    if isinstance(body, list):
        return [_safe_detail(x) for x in body[:50]]
    if isinstance(body, str) and len(body) > 800:
        return body[:800] + "…"
    return body
