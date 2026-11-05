"""D-137b — Automated UGC safety gate for private listings (Idealista-like).

Verdicts:
  ACCEPT — safe to auto-publish
  REVIEW — queue for human Founder moderation
  REJECT  — hard block (scam / severe abuse); stays draft + rejected

Layers:
  1) Deterministic heuristics + IT/EN blocklists (always on, no LLM cost)
  2) Optional Gemini classifier when heuristics are inconclusive / soft hits
  3) Periodic rescan of already-live private listings (scheduler)
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omnia.listing_safety_gate")

VERDICT_ACCEPT = "ACCEPT"
VERDICT_REVIEW = "REVIEW"
VERDICT_REJECT = "REJECT"

# Soft LLM REVIEW on live ads: alert Founder at most once per cooldown
# (hourly rescan otherwise re-mails the same «provaprova» false-positive every hour).
def _soft_alert_cooldown_hours() -> int:
    try:
        return max(1, int(os.environ.get("OMNIA_SAFETY_SOFT_ALERT_COOLDOWN_H", "24")))
    except ValueError:
        return 24


def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts or not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def soft_alert_in_cooldown(listing: Dict[str, Any], *, now: Optional[datetime] = None) -> bool:
    """True if we already emailed Founder for a soft live-flag within the cooldown window.

    Also treats a recent soft REVIEW already stored on `safety_gate` (pre-dedupe
    rows that spam-updated every hour) as already alerted — stops the mail flood
    without waiting for a new stamp field.
    """
    last = _parse_iso(listing.get("safety_soft_alerted_at"))
    if not last:
        sg = listing.get("safety_gate") or {}
        if (
            sg.get("verdict") == VERDICT_REVIEW
            and not (sg.get("hard_hits") or sg.get("soft_hits"))
        ):
            last = (
                _parse_iso(sg.get("scanned_at"))
                or _parse_iso(sg.get("checked_at"))
                or _parse_iso(listing.get("updated_at"))
            )
    if not last:
        return False
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    ref = now or datetime.now(timezone.utc)
    return (ref - last) < timedelta(hours=_soft_alert_cooldown_hours())


# Severe / reputation-damaging (hard reject). Keep list maintainable; expand via env.
_HARD_BLOCK_PATTERNS = [
    # Hate / severe insults (IT)
    r"\bnegr[oa]\b", r"\bterrone\b", r"\bpolentone\b", r"\bfrocio\b", r"\bricchione\b",
    r"\bhandicappat[oa]\b", r"\bmongoloide\b",
    # Explicit sexual solicitation in ads
    r"\bescort\b", r"\bmassagg[io].{0,20}erotic", r"\bsesso\s+a\s+pagamento\b",
    # Clear scam / fraud
    r"\bWestern\s*Union\b", r"\bMoneyGram\b", r"\binvia\s+soldi\b",
    r"\banticipo\s+obbligator", r"\bbonifico\s+estero\b",
    r"\bgarantito\s+al\s+100%\s+senza\s+visione\b",
]

# Soft hits → REVIEW (Founder decides)
_SOFT_BLOCK_PATTERNS = [
    r"\bputtana\b", r"\btroia\b", r"\bvaffanculo\b", r"\bstronz[oa]\b",
    r"\bidiot[ai]\b", r"\bimbesill", r"\bcretin[oa]\b",
    r"\bfuck\b", r"\bshit\b", r"\basshole\b", r"\bnigger\b", r"\bfaggot\b",
    r"\bscam\b", r"\btruffa\b", r"\bfake\s+listing\b",
    r"\bsolo\s+stranier", r"\bno\s+extracomunitar", r"\bno\s+immigrat",
    r"\bno\s+neri\b", r"\bno\s+arab", r"\bno\s+zingar",
    r"\barrivati\s+da\s+idealista\b",  # competitor smear spam often noisy
]

_URL_RE = re.compile(r"https?://|www\.|\bbit\.ly/|\bt\.me/|\bwa\.me/", re.I)
_PHONE_SPAM_RE = re.compile(r"(?:\+?\d[\d\s./-]{7,}\d)")
_CAPS_RATIO_RE = re.compile(r"[A-ZÀÈÉÌÒÙ]")
_WHATSAPP_SPAM_RE = re.compile(r"whats?\s*app|telegram|scrivimi\s+subito|solo\s+whatsapp", re.I)


@dataclass
class SafetyReport:
    verdict: str = VERDICT_ACCEPT
    reasons: List[str] = field(default_factory=list)
    hard_hits: List[str] = field(default_factory=list)
    soft_hits: List[str] = field(default_factory=list)
    llm_used: bool = False
    llm_verdict: Optional[str] = None
    scanned_text_len: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reasons": self.reasons[:12],
            "hard_hits": self.hard_hits[:8],
            "soft_hits": self.soft_hits[:8],
            "llm_used": self.llm_used,
            "llm_verdict": self.llm_verdict,
            "scanned_text_len": self.scanned_text_len,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }


def _compile(patterns: List[str]) -> List[re.Pattern]:
    out = []
    for p in patterns:
        try:
            out.append(re.compile(p, re.I | re.UNICODE))
        except re.error:
            logger.warning("bad safety pattern skipped: %s", p)
    return out


_HARD = _compile(_HARD_BLOCK_PATTERNS)
_SOFT = _compile(_SOFT_BLOCK_PATTERNS)


def _extra_patterns_from_env(prefix: str) -> List[re.Pattern]:
    raw = (os.environ.get(prefix) or "").strip()
    if not raw:
        return []
    parts = [x.strip() for x in raw.split("|") if x.strip()]
    return _compile(parts)


def listing_text_blob(listing: Dict[str, Any]) -> str:
    parts = [
        listing.get("title") or "",
        listing.get("description") or "",
        listing.get("zone") or "",
        listing.get("address") or "",
        (listing.get("owner") or {}).get("notes") or "",
        (listing.get("contact_public") or {}).get("display_name") or "",
    ]
    caps = []
    for ph in listing.get("photos") or []:
        if isinstance(ph, dict) and ph.get("caption"):
            caps.append(str(ph.get("caption")))
    parts.extend(caps[:20])
    return "\n".join(str(p) for p in parts if p).strip()


def _heuristic_scan(text: str) -> SafetyReport:
    report = SafetyReport(scanned_text_len=len(text))
    if not text:
        report.verdict = VERDICT_REVIEW
        report.reasons.append("empty_copy")
        return report

    hard = list(_HARD) + _extra_patterns_from_env("OMNIA_B2C_SAFETY_HARD_EXTRA")
    soft = list(_SOFT) + _extra_patterns_from_env("OMNIA_B2C_SAFETY_SOFT_EXTRA")

    for rx in hard:
        m = rx.search(text)
        if m:
            report.hard_hits.append(m.group(0)[:40])
    for rx in soft:
        m = rx.search(text)
        if m:
            report.soft_hits.append(m.group(0)[:40])

    # URL / contact spam in title-heavy ads
    title = text.split("\n", 1)[0]
    if _URL_RE.search(title):
        report.soft_hits.append("url_in_title")
        report.reasons.append("url_in_title")
    phones = _PHONE_SPAM_RE.findall(text)
    if len(phones) >= 3:
        report.soft_hits.append("phone_spam")
        report.reasons.append("multiple_phone_numbers")
    if _WHATSAPP_SPAM_RE.search(title) and len(title) < 80:
        report.soft_hits.append("whatsapp_title_spam")
        report.reasons.append("contact_channel_in_title")

    letters = [c for c in title if c.isalpha()]
    if len(letters) >= 12:
        caps = sum(1 for c in letters if c.isupper())
        if caps / max(len(letters), 1) >= 0.75:
            report.soft_hits.append("shouting_title")
            report.reasons.append("excessive_caps_title")

    if report.hard_hits:
        report.verdict = VERDICT_REJECT
        report.reasons.append("hard_blocklist")
        return report
    if report.soft_hits:
        report.verdict = VERDICT_REVIEW
        report.reasons.append("soft_blocklist_or_spam_heuristics")
        return report
    report.verdict = VERDICT_ACCEPT
    return report


async def _llm_classify(text: str) -> Optional[str]:
    """Return ACCEPT|REVIEW|REJECT or None if LLM unavailable."""
    if (os.environ.get("OMNIA_B2C_SAFETY_LLM") or "true").strip().lower() in (
        "0", "false", "no", "off",
    ):
        return None
    try:
        from shared.llm import generate_text, resolve_api_key
        resolve_api_key()
    except Exception:
        return None

    prompt = (
        "Sei il filtro reputazionale di ImmobilCloud (portale immobiliare IT).\n"
        "Classifica l'annuncio privato seguente. Rispondi con UNA sola parola:\n"
        "ACCEPT = testo normale, nessuno scandaloso\n"
        "REVIEW = dubbio (offese soft, discriminazione, spam, claim aggressivi)\n"
        "REJECT = grave (odio, scam chiaro, contenuti sessuali commerciali, frode)\n\n"
        f"TESTO:\n{text[:3500]}\n"
    )
    try:
        from shared.llm import generate_text
        out = await generate_text(
            prompt=prompt,
            system="Moderatore UGC immobiliare. Output: solo ACCEPT, REVIEW o REJECT.",
            temperature=0.0,
        )
        token = (out or "").strip().upper().split()[0] if out else ""
        if token in (VERDICT_ACCEPT, VERDICT_REVIEW, VERDICT_REJECT):
            return token
        if "REJECT" in (out or "").upper():
            return VERDICT_REJECT
        if "REVIEW" in (out or "").upper():
            return VERDICT_REVIEW
        if "ACCEPT" in (out or "").upper():
            return VERDICT_ACCEPT
    except Exception as e:
        logger.warning("listing safety LLM failed: %s", e)
    return None


async def evaluate_listing_safety(listing: Dict[str, Any]) -> SafetyReport:
    text = listing_text_blob(listing)
    report = _heuristic_scan(text)

    # Escalate soft → LLM when available; hard reject stays hard.
    if report.verdict == VERDICT_REJECT:
        return report

    # Always ask LLM on soft hits; optionally on ACCEPT for long descriptions
    need_llm = report.verdict == VERDICT_REVIEW or (
        report.verdict == VERDICT_ACCEPT and len(text) >= 400
    )
    if need_llm:
        llm = await _llm_classify(text)
        if llm:
            report.llm_used = True
            report.llm_verdict = llm
            # Never downgrade REJECT from heuristics; LLM can only tighten or confirm
            rank = {VERDICT_ACCEPT: 0, VERDICT_REVIEW: 1, VERDICT_REJECT: 2}
            if rank[llm] > rank[report.verdict]:
                report.verdict = llm
                report.reasons.append(f"llm_{llm.lower()}")
            elif report.verdict == VERDICT_REVIEW and llm == VERDICT_ACCEPT:
                # Soft hit but LLM says OK → still REVIEW (human) for reputation safety
                report.reasons.append("llm_accept_but_soft_hit_keeps_review")
    return report


def safety_gate_enabled() -> bool:
    raw = (os.environ.get("OMNIA_B2C_SAFETY_GATE") or "true").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _humanize_reason(code: str) -> str:
    """Map internal reason tokens to Italian Founder-facing lines."""
    raw = (code or "").strip()
    key = raw.lower()
    known = {
        "llm_review": "L'intelligenza artificiale ha trovato il testo dubbio (titolo o descrizione poco chiari / sospetti).",
        "llm_reject": "L'intelligenza artificiale ha indicato un contenuto da bloccare.",
        "llm_accept_but_soft_hit_keeps_review": "Ci sono parole sensibili: resta da verificare a mano anche se l'AI non ha bloccato.",
        "soft_hit": "Trovate parole sensibili o offensive.",
        "hard_hit": "Trovato contenuto vietato (odio, scam, abuso).",
    }
    if key in known:
        return known[key]
    if key.startswith("llm_"):
        return "Segnalazione automatica dall'intelligenza artificiale sul testo dell'annuncio."
    if raw:
        return f"Segnale automatico: {raw.replace('_', ' ')}."
    return "Motivo non specificato."


def founder_safety_alert_copy(
    listing: Dict[str, Any],
    report: SafetyReport,
    *,
    event: str = "submit",
) -> Dict[str, str]:
    """Plain-Italian copy for Founder email + in-app (no jargon)."""
    code = listing.get("reference_code") or listing.get("id") or "—"
    title = ((listing.get("title") or "Senza titolo").strip() or "Senza titolo")[:80]
    city = (listing.get("city") or "").strip()
    where = f"{title}" + (f" · {city}" if city else "")

    event_line = {
        "submit": "Un privato ha inviato un annuncio per la pubblicazione.",
        "edit": "Un privato ha modificato un annuncio già pubblicato.",
        "rescan_live_soft": (
            "Controllo automatico orario: possibile problema di contenuto. "
            "L'annuncio resta online per ora."
        ),
        "rescan_live": (
            "Controllo automatico orario: l'annuncio è stato tolto dalla pubblicazione "
            "in attesa del tuo controllo."
        ),
    }.get(event, "Segnalazione automatica sul contenuto di un annuncio.")

    if report.verdict == VERDICT_REJECT:
        severity = "Bloccato"
        severity_line = "Esito: bloccato. Non è pubblicabile così com'è."
        inbox_title = f"Annuncio bloccato · {code}"
        subject = f"[OMNIA] Annuncio bloccato · {code}"
        headline = f"Annuncio bloccato · {code}"
    else:
        severity = "Da controllare"
        if event == "rescan_live_soft":
            severity_line = (
                "Esito: da controllare. Non è un'emergenza: l'annuncio resta visibile, "
                "ma conviene darci un'occhiata."
            )
            inbox_title = f"Annuncio da controllare (resta online) · {code}"
            subject = f"[OMNIA] Annuncio da controllare (resta online) · {code}"
            headline = f"Annuncio da controllare · {code}"
        elif event == "rescan_live":
            severity_line = "Esito: da controllare. L'annuncio è stato nascosto finché non lo revisioni."
            inbox_title = f"Annuncio nascosto — da revisionare · {code}"
            subject = f"[OMNIA] Annuncio nascosto — da revisionare · {code}"
            headline = f"Annuncio nascosto · {code}"
        else:
            severity_line = "Esito: da controllare prima di restare (o andare) online."
            inbox_title = f"Annuncio da controllare · {code}"
            subject = f"[OMNIA] Annuncio da controllare · {code}"
            headline = f"Annuncio da controllare · {code}"

    why_bits = [_humanize_reason(r) for r in (report.reasons or [])[:6]]
    if report.hard_hits:
        why_bits.append(
            "Parole / schemi vietati trovati: " + ", ".join(report.hard_hits[:6]) + "."
        )
    if report.soft_hits:
        why_bits.append(
            "Parole sensibili trovate: " + ", ".join(report.soft_hits[:6]) + "."
        )
    if not why_bits:
        why_bits.append("Il sistema di sicurezza ha chiesto una revisione umana.")

    action = {
        "rescan_live_soft": (
            "Cosa fare: apri Moderazione, guarda titolo e descrizione. "
            "Se è solo un test (es. «provaprova»), puoi ignorare o sistemare il testo. "
            "Non serve ripubblicare: è già online."
        ),
        "rescan_live": (
            "Cosa fare: apri Moderazione, verifica il contenuto e approva o rifiuta."
        ),
        "edit": (
            "Cosa fare: apri Moderazione e verifica le modifiche prima che restino pubbliche."
        ),
        "submit": (
            "Cosa fare: apri Moderazione e decidi se pubblicare o rifiutare."
        ),
    }.get(event, "Cosa fare: apri Moderazione e revisiona l'annuncio.")

    why_text = " ".join(why_bits)
    detail = "\n".join([
        f"Annuncio: {where}",
        f"Codice: {code}",
        event_line,
        severity_line,
        f"Perché: {why_text}",
        action,
    ])
    inbox_body = f"{where} — {severity}. {event_line}"

    return {
        "subject": subject,
        "headline": headline,
        "listing_label": where,
        "code": code,
        "severity": severity,
        "event_line": event_line,
        "severity_line": severity_line,
        "why_line": why_text,
        "action_line": action,
        "detail": detail,
        "inbox_title": inbox_title,
        "inbox_body": inbox_body[:240],
        "moderation_path": "/app/moderation",
    }


async def notify_founder_safety_flag(
    listing: Dict[str, Any],
    report: SafetyReport,
    *,
    event: str = "submit",
) -> None:
    """Best-effort email + inbox when an ad is held or pulled for safety."""
    if report.verdict == VERDICT_ACCEPT:
        return
    try:
        from apps.billing.b2c_payment_alerts import founder_alert_emails
        from shared.email.client import send_email
        from shared.notifications.center import TYPE_LISTING_MODERATION, notify_users
        from shared.db.connection import Database

        copy = founder_safety_alert_copy(listing, report, event=event)
        for to in founder_alert_emails():
            await send_email(
                to=to,
                template="listing_safety_alert",
                lang="it",
                subject=copy["subject"],
                variables={
                    "headline": copy["headline"],
                    "listing_label": copy["listing_label"],
                    "code": copy["code"],
                    "severity": copy["severity"],
                    "event_line": copy["event_line"],
                    "severity_line": copy["severity_line"],
                    "why_line": copy["why_line"],
                    "action_line": copy["action_line"],
                    "moderation_path": copy["moderation_path"],
                },
            )
        db = Database.get()
        admins = await db.users.find(
            {"role": "super_admin", "is_active": {"$ne": False}},
            {"_id": 0, "id": 1},
        ).to_list(length=20)
        ids = [a["id"] for a in admins if a.get("id")]
        if ids:
            await notify_users(
                ids,
                type=TYPE_LISTING_MODERATION,
                title=copy["inbox_title"],
                body=copy["inbox_body"],
                link="/app/moderation",
                meta={"listing_id": listing.get("id"), "verdict": report.verdict, "event": event},
            )
    except Exception:
        logger.exception("founder safety notify failed listing=%s", listing.get("id"))


async def apply_safety_hold(
    db,
    listing_id: str,
    report: SafetyReport,
    *,
    reject: bool,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    notes = f"safety_gate:{report.verdict} · " + "; ".join(report.reasons[:5])
    notes = notes[:500]
    fields: Dict[str, Any] = {
        "moderation_status": "rejected" if reject else "pending",
        "status": "draft",
        "visibility": "private",
        "moderation_notes": notes,
        "moderation_reviewed_at": now,
        "moderation_reviewed_by": "safety_gate",
        "safety_gate": report.to_dict(),
        "updated_at": now,
    }
    await db.properties.update_one({"id": listing_id}, {"$set": fields})


async def rescan_live_private_listings(*, limit: int = 80) -> Dict[str, Any]:
    """Reputation protection on already-live private ads.

    Policy (D-137b, dogfood 4-Nov):
      · ACCEPT → refresh safety_gate only
      · REJECT → unpublish (hard block)
      · REVIEW with heuristic soft/hard hits → unpublish to Founder queue
      · REVIEW only from LLM (no heuristic hits) → stay live + alert Founder
        (Gemini alone must not yank a human-approved / auto-published ad —
         titles like «provaprova» were false-positives that re-hid live ads)
    """
    if not safety_gate_enabled():
        return {"ok": True, "skipped": True, "reason": "gate_disabled"}
    from shared.db.connection import Database
    from shared.db.trash import with_not_trashed

    db = Database.get()
    cur = db.properties.find(
        with_not_trashed({
            "is_private_listing": True,
            "status": "active",
            "moderation_status": "approved",
        }),
        {"_id": 0},
    ).sort("updated_at", -1).limit(limit)
    items = await cur.to_list(length=limit)
    held = 0
    flagged = 0
    scanned = 0
    for listing in items:
        scanned += 1
        try:
            report = await evaluate_listing_safety(listing)
            if report.verdict == VERDICT_ACCEPT:
                await db.properties.update_one(
                    {"id": listing["id"]},
                    {"$set": {"safety_gate": report.to_dict()}},
                )
                continue

            reject = report.verdict == VERDICT_REJECT
            heuristic_hit = bool(report.hard_hits or report.soft_hits)
            # Pure LLM REVIEW on an already-live ad: alert, do not auto-unpublish
            if report.verdict == VERDICT_REVIEW and not heuristic_hit and not reject:
                now_iso = datetime.now(timezone.utc).isoformat()
                fields: Dict[str, Any] = {
                    "safety_gate": report.to_dict(),
                    "updated_at": now_iso,
                }
                # Dedupe Founder email: same soft false-positive must not mail every hour
                if soft_alert_in_cooldown(listing):
                    await db.properties.update_one({"id": listing["id"]}, {"$set": fields})
                    logger.info(
                        "safety rescan soft-flag cooldown (no email) listing=%s reasons=%s",
                        listing.get("id"), report.reasons[:3],
                    )
                    continue
                fields["safety_soft_alerted_at"] = now_iso
                await db.properties.update_one({"id": listing["id"]}, {"$set": fields})
                await notify_founder_safety_flag(
                    listing, report, event="rescan_live_soft",
                )
                flagged += 1
                logger.info(
                    "safety rescan soft-flag (stay live) listing=%s verdict=%s reasons=%s",
                    listing.get("id"), report.verdict, report.reasons[:3],
                )
                continue

            await apply_safety_hold(
                db, listing["id"], report, reject=reject,
            )
            await notify_founder_safety_flag(listing, report, event="rescan_live")
            held += 1
            logger.warning(
                "safety rescan held listing=%s verdict=%s", listing.get("id"), report.verdict,
            )
        except Exception:
            logger.exception("safety rescan failed listing=%s", listing.get("id"))
    return {"ok": True, "scanned": scanned, "held": held, "flagged_soft": flagged}
