"""D-175 C7 — omnia.dogfood.jcanonical.v1 (deterministic JSON for hashing).

Not raw RFC 8785: JCS-like UTF-16 key order + journal constraints
(safe integers only, no floats, closed schema handled by callers).
"""
from __future__ import annotations

import calendar
import re
from typing import Any

JCANONICAL_VERSION = "omnia.dogfood.jcanonical.v1"
JOURNAL_FORMAT_VERSION = "omnia.dogfood.journal.v1"
SAFE_INT_MIN = -(2**53 - 1)
SAFE_INT_MAX = 2**53 - 1
GENESIS_PREV_HASH = "0" * 64

_TS_RE = re.compile(
    r"^(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})T"
    r"(?P<H>\d{2}):(?P<M>\d{2}):(?P<S>\d{2})\.(?P<ms>\d{3})Z$"
)


class CanonicalError(ValueError):
    pass


def _utf16_be_units(s: str) -> bytes:
    try:
        return s.encode("utf-16-be")
    except UnicodeEncodeError as e:
        raise CanonicalError(f"utf16_encode_failed:{e}") from e


def _key_sort_key(name: str) -> bytes:
    return _utf16_be_units(name)


def _json_string(s: str) -> str:
    # Reject lone surrogates by round-tripping through UTF-16
    try:
        s.encode("utf-16-be")
    except UnicodeEncodeError as e:
        raise CanonicalError(f"invalid_unicode_string:{e}") from e
    out: list[str] = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif o < 0x20:
            out.append(f"\\u{o:04x}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _decimal_int(n: int) -> str:
    if n < SAFE_INT_MIN or n > SAFE_INT_MAX:
        raise CanonicalError(f"integer_out_of_safe_range:{n}")
    if n == 0:
        return "0"
    return str(n)


def validate_ts_utc(value: str) -> str:
    if not isinstance(value, str):
        raise CanonicalError("timestamp_not_string")
    m = _TS_RE.match(value)
    if not m:
        raise CanonicalError(f"timestamp_format_invalid:{value}")
    y, mo, d = int(m.group("y")), int(m.group("m")), int(m.group("d"))
    H, Mi, S = int(m.group("H")), int(m.group("M")), int(m.group("S"))
    if mo < 1 or mo > 12:
        raise CanonicalError("timestamp_month_invalid")
    max_day = calendar.monthrange(y, mo)[1]
    if d < 1 or d > max_day:
        raise CanonicalError("timestamp_day_invalid")
    if H > 23 or Mi > 59 or S > 59:
        raise CanonicalError("timestamp_time_invalid")
    return value


def canonical_json(value: Any) -> str:
    """Return canonical JSON text (no surrounding whitespace)."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, bool):  # pragma: no cover — bool is subclass of int
        return "true" if value else "false"
    if isinstance(value, float):
        raise CanonicalError("float_forbidden")
    if isinstance(value, int):
        return _decimal_int(value)
    if isinstance(value, str):
        return _json_string(value)
    if isinstance(value, list):
        return "[" + ",".join(canonical_json(x) for x in value) + "]"
    if isinstance(value, dict):
        keys = list(value.keys())
        if any(not isinstance(k, str) for k in keys):
            raise CanonicalError("non_string_key")
        if len(keys) != len(set(keys)):
            raise CanonicalError("duplicate_keys")
        keys_sorted = sorted(keys, key=_key_sort_key)
        parts = [
            _json_string(k) + ":" + canonical_json(value[k]) for k in keys_sorted
        ]
        return "{" + ",".join(parts) + "}"
    raise CanonicalError(f"unsupported_type:{type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    text = canonical_json(value)
    if text.startswith("\ufeff"):
        raise CanonicalError("bom_forbidden")
    return text.encode("utf-8")
