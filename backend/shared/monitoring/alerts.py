"""OMNIA — error alerting (Sentry optional + webhook/email fallback).

Env:
  SENTRY_DSN          — if set, init sentry-sdk
  ERROR_ALERT_WEBHOOK — Slack/Discord-compatible incoming webhook URL
  ERROR_ALERT_EMAIL   — founder email for critical alerts
  ERROR_ALERT_MAX_PER_HOUR — default 20
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import traceback
from typing import Any, Dict, Optional

logger = logging.getLogger("omnia.alerts")

_sentry_ready = False
_recent: list[float] = []


def _max_per_hour() -> int:
    try:
        return max(1, int(os.environ.get("ERROR_ALERT_MAX_PER_HOUR") or "20"))
    except ValueError:
        return 20


def _allowed() -> bool:
    now = time.monotonic()
    cutoff = now - 3600
    while _recent and _recent[0] < cutoff:
        _recent.pop(0)
    if len(_recent) >= _max_per_hour():
        return False
    _recent.append(now)
    return True


def init_monitoring() -> None:
    """Call once at startup. Fail-soft if Sentry missing/misconfigured."""
    global _sentry_ready
    dsn = (os.environ.get("SENTRY_DSN") or "").strip()
    if not dsn:
        logger.info("Sentry disabled (no SENTRY_DSN) — webhook/email alerts only")
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=(os.environ.get("OMNIA_ENV") or "development"),
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE") or "0.05"),
            integrations=[
                FastApiIntegration(),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
            ],
            send_default_pii=False,
        )
        _sentry_ready = True
        logger.info("Sentry initialized")
    except Exception as e:
        logger.warning("Sentry init failed: %s", e)
        _sentry_ready = False


async def notify_error(
    *,
    title: str,
    detail: str,
    path: Optional[str] = None,
    exc: Optional[BaseException] = None,
) -> None:
    """Fire best-effort alert. Never raises to the request path."""
    if not _allowed():
        logger.warning("alert rate-limited title=%s", title)
        return

    body = detail[:2000]
    if exc is not None:
        body = f"{body}\n\n{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))[:3000]}"

    if _sentry_ready:
        try:
            import sentry_sdk
            with sentry_sdk.push_scope() as scope:
                if path:
                    scope.set_tag("path", path)
                scope.set_level("error")
                if exc is not None:
                    sentry_sdk.capture_exception(exc)
                else:
                    sentry_sdk.capture_message(f"{title}: {body}", level="error")
        except Exception as e:
            logger.warning("sentry capture failed: %s", e)

    webhook = (os.environ.get("ERROR_ALERT_WEBHOOK") or "").strip()
    if webhook:
        try:
            import httpx
            payload: Dict[str, Any] = {
                "text": f"[OMNIA] {title}\npath={path or '-'}\n{body[:1500]}",
                "content": f"**OMNIA** {title}\n`{path or '-'}`\n```{body[:1200]}```",
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                await client.post(webhook, json=payload)
        except Exception as e:
            logger.warning("webhook alert failed: %s", e)

    email_to = (os.environ.get("ERROR_ALERT_EMAIL") or "").strip()
    if email_to:
        try:
            from shared.email import send_email
            await send_email(
                to=email_to,
                template="error_alert",
                lang="it",
                variables={
                    "title": title,
                    "path": path or "-",
                    "detail": body[:1800],
                },
            )
        except Exception as e:
            logger.warning("email alert failed: %s", e)

    logger.error("ALERT %s path=%s detail=%s", title, path, detail[:500])


def schedule_notify_error(**kwargs) -> None:
    """Fire-and-forget from sync contexts."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(notify_error(**kwargs))
    except RuntimeError:
        logger.error("ALERT(no-loop) %s", kwargs.get("title"))


class AlertLoggingHandler(logging.Handler):
    """Forward ERROR+ logs to alert channel (rate-limited)."""

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno < logging.ERROR:
            return
        if record.name.startswith("omnia.alerts"):
            return
        try:
            msg = self.format(record)
            schedule_notify_error(
                title=f"log:{record.name}",
                detail=msg,
                path=getattr(record, "pathname", None),
            )
        except Exception:
            pass
