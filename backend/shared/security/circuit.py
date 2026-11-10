"""OMNIA — circuit breaker for external dependencies.

Prevents cascading failures: if Resend/LLM/geocode flap, we open the
circuit and fail soft instead of hanging the whole API.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

logger = logging.getLogger("omnia.circuit")

T = TypeVar("T")


@dataclass
class _BreakerState:
    failures: int = 0
    opened_at: float = 0.0
    last_error: str = ""


_states: Dict[str, _BreakerState] = {}
# Kill-switch manuale (Cabina): resta aperto finché clear_hold — non auto-recovery
_manual_holds: Dict[str, str] = {}


@dataclass
class CircuitPolicy:
    name: str
    failure_threshold: int = 5
    recovery_seconds: float = 60.0


def _state(name: str) -> _BreakerState:
    if name not in _states:
        _states[name] = _BreakerState()
    return _states[name]


def force_hold(name: str, reason: str = "ops_kill_switch") -> None:
    n = (name or "").strip()
    if not n:
        return
    _manual_holds[n] = (reason or "ops_kill_switch")[:120]
    st = _state(n)
    st.failures = max(st.failures, 5)
    st.opened_at = time.monotonic()
    st.last_error = _manual_holds[n]
    logger.warning("circuit HOLD name=%s reason=%s", n, _manual_holds[n])


def clear_hold(name: str) -> None:
    n = (name or "").strip()
    if not n:
        return
    _manual_holds.pop(n, None)
    st = _state(n)
    st.failures = 0
    st.opened_at = 0.0
    st.last_error = ""
    logger.warning("circuit HOLD cleared name=%s", n)


def is_held(name: str) -> bool:
    return (name or "").strip() in _manual_holds


def circuit_open(name: str) -> bool:
    if is_held(name):
        return True
    st = _state(name)
    if st.failures <= 0:
        return False
    # half-open after recovery window
    if st.opened_at and (time.monotonic() - st.opened_at) >= 60.0:
        return False
    policy_threshold = 5
    return st.failures >= policy_threshold


def record_success(name: str) -> None:
    if is_held(name):
        return  # hold manuale: non chiudere automaticamente
    st = _state(name)
    st.failures = 0
    st.opened_at = 0.0
    st.last_error = ""


def record_failure(name: str, err: str, threshold: int = 5) -> None:
    st = _state(name)
    st.failures += 1
    st.last_error = (err or "")[:200]
    if st.failures >= threshold and not st.opened_at:
        st.opened_at = time.monotonic()
        logger.warning("circuit OPEN name=%s failures=%s err=%s", name, st.failures, st.last_error)


async def call_with_circuit(
    name: str,
    fn: Callable[[], Awaitable[T]],
    *,
    fallback: Optional[T] = None,
    threshold: int = 5,
    recovery_seconds: float = 60.0,
) -> T:
    """Run awaitable under circuit. If open, return fallback or raise soft error."""
    if is_held(name):
        logger.info("circuit hold short-circuit name=%s", name)
        if fallback is not None:
            return fallback
        raise RuntimeError(f"circuit_held:{name}")
    st = _state(name)
    if st.failures >= threshold:
        elapsed = time.monotonic() - (st.opened_at or 0.0)
        if elapsed < recovery_seconds:
            logger.info("circuit short-circuit name=%s", name)
            if fallback is not None:
                return fallback
            raise RuntimeError(f"circuit_open:{name}")
        # half-open: allow one try
    try:
        result = await fn()
        record_success(name)
        return result
    except Exception as e:
        record_failure(name, str(e), threshold=threshold)
        if fallback is not None:
            return fallback
        raise


def snapshot() -> Dict[str, Any]:
    out = {}
    names = set(_states.keys()) | set(_manual_holds.keys())
    for k in names:
        st = _state(k)
        out[k] = {
            "failures": st.failures,
            "open": circuit_open(k),
            "held": is_held(k),
            "hold_reason": _manual_holds.get(k),
            "last_error": st.last_error,
        }
    return out
