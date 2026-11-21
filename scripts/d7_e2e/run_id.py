"""Strict run_id validation — refuse path traversal and unsafe charset."""
from __future__ import annotations

import re

# Documented contract: 12–64 chars, alphanumeric + underscore + hyphen only.
# new_run_id() emits UTC_YYYYMMDDThhmmssZ_<8hex> which matches this.
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{12,64}$")
RUN_ID_MIN_LEN = 12
RUN_ID_MAX_LEN = 64


class InvalidRunId(ValueError):
    """Raised when a run_id is refused before any FS/DB operation."""


def validate_run_id(run_id: str) -> str:
    """Return run_id if safe; raise InvalidRunId otherwise.

    Rejects empty, too short/long, path separators, ``..``, absolute paths,
    and any character outside ``[A-Za-z0-9_-]``.
    """
    if not isinstance(run_id, str):
        raise InvalidRunId("run_id_not_str")
    if run_id != run_id.strip():
        raise InvalidRunId("run_id_whitespace")
    if not run_id:
        raise InvalidRunId("run_id_empty")
    if len(run_id) < RUN_ID_MIN_LEN:
        raise InvalidRunId("run_id_too_short")
    if len(run_id) > RUN_ID_MAX_LEN:
        raise InvalidRunId("run_id_too_long")
    # Explicit rejects (also covered by charset, kept for clear errors)
    for bad in ("/", "\\", "..", "\x00"):
        if bad in run_id:
            raise InvalidRunId(f"run_id_forbidden_token:{bad!r}")
    if run_id.startswith(("/", "\\", "~")):
        raise InvalidRunId("run_id_absolute_or_home")
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise InvalidRunId("run_id_charset")
    return run_id
