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


@dataclass
class CircuitPolicy:
    name: str
    failure_threshold: int = 5
    recovery_seconds: float = 60.0


def _state(name: str) -> _BreakerState:
    if name not in _states:
        _states[name] = _BreakerState()
    return _states[name]


def circuit_open(name: str) -> bool:
    st = _state(name)
    if st.failures <= 0:
        return False
    # half-open after recovery window
    if st.opened_at and (time.monotonic() - st.opened_at) >= 60.0:
        return False
    policy_threshold = 5
    return st.failures >= policy_threshold


def record_success(name: str) -> None:
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
    for k, st in _states.items():
        out[k] = {
            "failures": st.failures,
            "open": circuit_open(k),
            "last_error": st.last_error,
        }
    return out
