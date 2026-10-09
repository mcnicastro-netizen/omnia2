"""P-042 — Redact email addresses from log records."""
from __future__ import annotations

import logging
import re
from typing import Any

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def redact_emails(text: str) -> str:
    return _EMAIL_RE.sub("[REDACTED_EMAIL]", text)


class RedactPIIFilter(logging.Filter):
    """Strip email-like strings from log messages and %-format args."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = redact_emails(record.msg)
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: redact_emails(v) if isinstance(v, str) else v
                        for k, v in record.args.items()
                    }
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        redact_emails(a) if isinstance(a, str) else a
                        for a in record.args
                    )
        except Exception:
            pass
        return True


def install_pii_redaction(root: logging.Logger | None = None) -> None:
    """Attach filter to root logger (and common handlers). Idempotent."""
    target = root or logging.getLogger()
    for f in target.filters:
        if isinstance(f, RedactPIIFilter):
            return
    filt = RedactPIIFilter()
    target.addFilter(filt)
    for h in list(target.handlers):
        if not any(isinstance(x, RedactPIIFilter) for x in h.filters):
            h.addFilter(filt)
    # uvicorn access / error loggers
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "omnia"):
        lg = logging.getLogger(name)
        if not any(isinstance(x, RedactPIIFilter) for x in lg.filters):
            lg.addFilter(filt)
