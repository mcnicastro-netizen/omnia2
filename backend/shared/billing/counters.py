"""D-166 — Contatori scadenze abbonamento + crediti pacchetto (zero check a mano)."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("omnia.billing.counters")


def credits_low_threshold() -> int:
    try:
        return max(0, int(os.environ.get("OMNIA_CREDITS_LOW_THRESHOLD", "200")))
    except ValueError:
        return 200


def renewal_reminder_days() -> List[int]:
    raw = (os.environ.get("OMNIA_SUB_REMINDER_DAYS") or "30,7,1").strip()
    out: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            d = int(part)
            if d >= 0 and d not in out:
                out.append(d)
        except ValueError:
            continue
    return out or [30, 7, 1]


def _parse_iso(raw: Optional[str]) -> Optional[datetime]:
    if not raw or not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def days_until(iso_end: Optional[str], *, now: Optional[datetime] = None) -> Optional[int]:
    end = _parse_iso(iso_end)
    if not end:
        return None
    now = now or datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    delta = end - now
    return int(delta.total_seconds() // 86400)


def subscription_counter(sub: Optional[dict], *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Vista contatore abbonamento per UI Ops/cliente."""
    if not sub:
        return {
            "has_subscription": False,
            "status": None,
            "tier": None,
            "current_period_end": None,
            "days_left": None,
            "renewal_due_soon": False,
            "past_due": False,
        }
    status = (sub.get("status") or "").lower()
    end = sub.get("current_period_end")
    left = days_until(end, now=now)
    soon_days = max(renewal_reminder_days() or [7])
    return {
        "has_subscription": True,
        "status": status or None,
        "tier": sub.get("tier") or sub.get("plan_tier"),
        "current_period_start": sub.get("current_period_start"),
        "current_period_end": end,
        "days_left": left,
        "renewal_due_soon": left is not None and 0 <= left <= soon_days,
        "past_due": status in ("past_due", "unpaid", "canceled", "incomplete_expired"),
    }


def wallet_counter(wallet: Optional[dict]) -> Dict[str, Any]:
    bal = int((wallet or {}).get("balance") or 0)
    thr = credits_low_threshold()
    return {
        "balance": bal,
        "low_threshold": thr,
        "low": bal < thr,
        "source": "credit_wallets",
    }


async def enrich_agencies_billing(db, agency_ids: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """Batch: agency_id → {subscription, wallet, sub_counter, credits}."""
    ids = [a for a in agency_ids if a]
    out: Dict[str, Dict[str, Any]] = {
        aid: {
            "subscription": None,
            "wallet": None,
            "sub": subscription_counter(None),
            "credits": wallet_counter(None),
        }
        for aid in ids
    }
    if not ids:
        return out
    subs = await db.subscriptions.find(
        {"agency_id": {"$in": ids}},
        {"_id": 0},
    ).to_list(length=len(ids) + 5)
    for s in subs:
        aid = s.get("agency_id")
        if aid in out:
            out[aid]["subscription"] = s
            out[aid]["sub"] = subscription_counter(s)
    wallets = await db.credit_wallets.find(
        {"agency_id": {"$in": ids}},
        {"_id": 0},
    ).to_list(length=len(ids) + 5)
    for w in wallets:
        aid = w.get("agency_id")
        if aid in out:
            out[aid]["wallet"] = w
            out[aid]["credits"] = wallet_counter(w)
    return out


async def run_billing_reminders(db) -> Dict[str, Any]:
    """Cron giornaliero: mail rinnovo (30/7/1) + alert crediti bassi."""
    from shared.email.client import send_email
    from shared.email.portal_links import gestionale_enter_urls
    from shared.ops_alerts import record_alert
    from shared.public_base import get_public_base_url

    now = datetime.now(timezone.utc)
    report = {
        "ok": True,
        "at": now.isoformat(),
        "renewal_emails": 0,
        "credits_alerts": 0,
        "ops_alerts": 0,
        "skipped": 0,
    }
    reminder_days = set(renewal_reminder_days())
    thr = credits_low_threshold()

    # --- Subscription renewals ---
    cur = db.subscriptions.find(
        {"status": {"$in": ["active", "trialing", "past_due"]}},
        {"_id": 0},
    )
    subs = await cur.to_list(length=2000)
    for sub in subs:
        aid = sub.get("agency_id")
        if not aid:
            continue
        counter = subscription_counter(sub, now=now)
        left = counter.get("days_left")
        status = counter.get("status")

        if status == "past_due":
            await record_alert(
                kind="subscription_past_due",
                severity="error",
                message=f"Abbonamento past_due agenzia {aid}",
                meta={"agency_id": aid, "tier": counter.get("tier")},
                dedupe_hours=24,
            )
            report["ops_alerts"] += 1

        if left is None or left not in reminder_days:
            continue

        # Idempotenza per questa scadenza + giorno-soglia
        period_key = (counter.get("current_period_end") or "")[:10]
        sent_map = dict(sub.get("renewal_reminders_sent") or {})
        stamp_key = f"{period_key}:{left}"
        if sent_map.get(stamp_key):
            report["skipped"] += 1
            continue

        agency = await db.agencies.find_one({"id": aid}, {"_id": 0})
        if not agency:
            continue
        owner = await db.users.find_one(
            {"id": agency.get("owner_id")},
            {"_id": 0, "email": 1, "name": 1, "lang": 1},
        )
        to = (owner or {}).get("email") or ((agency.get("contact") or {}).get("email"))
        if not to:
            report["skipped"] += 1
            continue
        lang = ((owner or {}).get("lang") or "it")[:2]
        links = gestionale_enter_urls(lang)
        billing_url = f"{get_public_base_url().rstrip('/')}/{lang}/app/settings/billing"
        try:
            await send_email(
                to=to,
                template="subscription_renewal_reminder",
                lang=lang if lang in ("it", "en", "es") else "it",
                variables={
                    "name": (owner or {}).get("name") or "Colleague",
                    "agency_name": agency.get("display_name") or agency.get("slug") or "",
                    "days_left": str(left),
                    "period_end": (counter.get("current_period_end") or "")[:10],
                    "tier": (counter.get("tier") or "").upper(),
                    "billing_url": billing_url,
                    **links,
                },
            )
            sent_map[stamp_key] = now.isoformat()
            await db.subscriptions.update_one(
                {"agency_id": aid},
                {"$set": {"renewal_reminders_sent": sent_map, "updated_at": now.isoformat()}},
            )
            report["renewal_emails"] += 1
            if left <= 7:
                await record_alert(
                    kind="subscription_renewal_soon",
                    severity="warning",
                    message=f"Rinnovo tra {left}g · {agency.get('display_name') or aid}",
                    meta={"agency_id": aid, "days_left": left},
                    dedupe_hours=20,
                )
                report["ops_alerts"] += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("renewal reminder failed agency=%s: %s", aid, exc)

    # --- Low package credits ---
    wcur = db.credit_wallets.find({}, {"_id": 0})
    wallets = await wcur.to_list(length=5000)
    for w in wallets:
        aid = w.get("agency_id")
        bal = int(w.get("balance") or 0)
        if bal >= thr:
            if w.get("credits_low_alert_at"):
                await db.credit_wallets.update_one(
                    {"agency_id": aid},
                    {"$unset": {"credits_low_alert_at": ""}, "$set": {"updated_at": now.isoformat()}},
                )
            continue
        if w.get("credits_low_alert_at"):
            report["skipped"] += 1
            continue
        agency = await db.agencies.find_one({"id": aid}, {"_id": 0}) if aid else None
        if not agency:
            continue
        owner = await db.users.find_one(
            {"id": agency.get("owner_id")},
            {"_id": 0, "email": 1, "name": 1, "lang": 1},
        )
        to = (owner or {}).get("email") or ((agency.get("contact") or {}).get("email"))
        lang = ((owner or {}).get("lang") or "it")[:2]
        billing_url = f"{get_public_base_url().rstrip('/')}/{lang}/app/settings/billing"
        if to:
            try:
                await send_email(
                    to=to,
                    template="credits_low",
                    lang=lang if lang in ("it", "en", "es") else "it",
                    variables={
                        "name": (owner or {}).get("name") or "Colleague",
                        "agency_name": agency.get("display_name") or agency.get("slug") or "",
                        "balance": str(bal),
                        "threshold": str(thr),
                        "billing_url": billing_url,
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("credits_low email failed agency=%s: %s", aid, exc)
        await db.credit_wallets.update_one(
            {"agency_id": aid},
            {"$set": {"credits_low_alert_at": now.isoformat(), "updated_at": now.isoformat()}},
        )
        await record_alert(
            kind="credits_low",
            severity="warning",
            message=f"Crediti pacchetto bassi ({bal}<{thr}) · {agency.get('display_name') or aid}",
            meta={"agency_id": aid, "balance": bal, "threshold": thr},
            dedupe_hours=24,
        )
        report["credits_alerts"] += 1
        report["ops_alerts"] += 1

    logger.info("billing reminders done %s", report)
    return report
