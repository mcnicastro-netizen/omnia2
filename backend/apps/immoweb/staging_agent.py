"""OMNIA StagingAgent — specialized virtual-staging controller (D-125).

Primary engine (Founder OK 19-Ott-2026): fal Nano Banana 2 one-shot
(= Gemini 3.1 Flash Image) × up to 4 styles + vision critic (Gemini Flash).

Legacy EVF/Ideogram/LoRA remains fallback only. Hard USD cap keeps B2C
resale at ~€0.90/img profitable (D-033).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("omnia.staging_agent")

# Nano Banana 2 edit = $0.08/img @ 1K (fal listino). Soft = N styles; hard allows 1 retry.
COST_NANO_BANANA_1K = 0.08
BUDGET_SOFT_USD = {
    "standard": 0.10,
    "empty": 0.10,
    "reverse": 0.10,
}
BUDGET_HARD_USD = {
    "standard": 0.20,
    "empty": 0.18,
    "reverse": 0.20,
}
# Extra per additional style variant (multi_style).
BUDGET_PER_EXTRA_STYLE = 0.08
BUDGET_HARD_PER_EXTRA_STYLE = 0.10

# Critic: accept if score >= 7/10 (mapped to 0.70).
QUALITY_ACCEPT = 0.70
QUALITY_WARN = 0.55
MAX_FURNISH_RETRIES = 1
MAX_ERASE_RETRIES = 0  # oneshot: no separate erase loop


@dataclass
class StagingPlan:
    mode: str
    need_erase: bool
    need_furnish: bool
    num_variants: int
    styles: List[str]
    room_type: str
    budget_soft_usd: float
    budget_hard_usd: float
    engine: str = "nano_banana"
    max_erase_retries: int = MAX_ERASE_RETRIES
    max_furnish_retries: int = MAX_FURNISH_RETRIES
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "need_erase": self.need_erase,
            "need_furnish": self.need_furnish,
            "num_variants": self.num_variants,
            "styles": list(self.styles),
            "room_type": self.room_type,
            "budget_soft_usd": self.budget_soft_usd,
            "budget_hard_usd": self.budget_hard_usd,
            "engine": self.engine,
            "max_erase_retries": self.max_erase_retries,
            "max_furnish_retries": self.max_furnish_retries,
            "notes": list(self.notes),
        }


@dataclass
class QualityReport:
    score: float
    issues: List[str] = field(default_factory=list)
    retry_actions: List[str] = field(default_factory=list)
    signals: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 3),
            "issues": list(self.issues),
            "retry_actions": list(self.retry_actions),
            "signals": dict(self.signals),
        }


@dataclass
class AgentLedger:
    """Running cost + decision log for one job."""
    spent_usd: float = 0.0
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def charge(self, amount: float, label: str, **extra: Any) -> None:
        self.spent_usd = round(self.spent_usd + float(amount or 0), 4)
        row = {"label": label, "cost_usd": round(float(amount or 0), 4), "spent_usd": self.spent_usd}
        row.update(extra)
        self.entries.append(row)

    def can_spend(self, next_cost: float, hard_cap: float) -> bool:
        return (self.spent_usd + float(next_cost or 0)) <= (hard_cap + 1e-9)

    def to_dict(self) -> Dict[str, Any]:
        return {"spent_usd": self.spent_usd, "entries": list(self.entries)}


def plan_staging(
    *,
    mode: str,
    style: str,
    room_type: str,
    num_variants: int = 1,
    variant_mode: str = "same_style",
    styles_list: Optional[Sequence[str]] = None,
    engine: str = "nano_banana",
) -> StagingPlan:
    """Build an execution plan with mode-aware cost caps (no network)."""
    m = mode if mode in ("standard", "reverse", "empty") else "standard"
    eng = engine if engine in ("nano_banana", "legacy") else "nano_banana"
    n = max(1, min(int(num_variants or 1), 4))
    if m == "empty":
        styles = ["empty"]
        n = 1
    elif variant_mode == "multi_style" and styles_list:
        styles = [s for s in styles_list if s][:n] or [style or "modern"]
        n = len(styles)
    else:
        styles = [style or "modern"]
        n = 1

    soft = BUDGET_SOFT_USD[m] + max(0, n - 1) * BUDGET_PER_EXTRA_STYLE
    hard = BUDGET_HARD_USD[m] + max(0, n - 1) * BUDGET_HARD_PER_EXTRA_STYLE
    notes: List[str] = ["no_third_party_staging_saas_embed"]
    if eng == "nano_banana":
        notes.append("nano_banana_2_oneshot")
        notes.append("vision_critic_gemini_flash")
        if m == "reverse":
            notes.append("oneshot_remove_and_furnish")
        elif m == "empty":
            notes.append("oneshot_empty_only")
        else:
            notes.append("oneshot_furnish_only")
    else:
        if m in ("reverse", "empty"):
            notes.append("semantic_erase_evf_then_florence_remnants")
        if m != "empty":
            notes.append("apartment_staging_lora_primary")

    return StagingPlan(
        mode=m,
        need_erase=m in ("reverse", "empty"),
        need_furnish=m != "empty",
        num_variants=n,
        styles=styles,
        room_type=room_type or "living",
        budget_soft_usd=round(soft, 4),
        budget_hard_usd=round(hard, 4),
        engine=eng,
        max_erase_retries=0 if eng == "nano_banana" else MAX_ERASE_RETRIES,
        max_furnish_retries=MAX_FURNISH_RETRIES,
        notes=notes,
    )


def critique_empty_from_meta(erase_meta: Optional[dict]) -> QualityReport:
    """Heuristic critic for emptied rooms — uses erase telemetry (zero LLM cost)."""
    meta = erase_meta or {}
    erased = list(meta.get("erased") or [])
    wall_retries = int(meta.get("wall_retries") or 0)
    evf_ratio = float(meta.get("evf_ratio") or 0)
    pass1 = int(meta.get("pass1") or 0)
    sweep = int(meta.get("sweep") or 0)
    issues: List[str] = []
    retries: List[str] = []
    score = 1.0

    skip_wall = sum(1 for e in erased if "skip_wall" in str(e))
    if skip_wall:
        issues.append(f"wall_invention_guard_fired:{skip_wall}")
        score -= 0.08 * min(skip_wall, 3)
    if wall_retries >= 3:
        issues.append("many_wall_retries")
        score -= 0.12

    if evf_ratio < 0.02 and pass1 == 0 and sweep == 0:
        issues.append("no_furniture_detected")
        score = max(score, 0.85)
    elif evf_ratio >= 0.02 and not erased:
        issues.append("mask_built_but_nothing_erased")
        score -= 0.35
        retries.append("re_erase")
    elif pass1 + sweep >= 6:
        issues.append("high_remnant_box_count")
        score -= 0.18
        retries.append("re_erase_remnants")

    soft_left = sum(1 for e in erased if any(x in str(e) for x in (":sweep", "rug", "carpet")))
    if soft_left == 0 and pass1 >= 3:
        issues.append("no_soft_clutter_pass")
        score -= 0.05

    score = max(0.0, min(1.0, score))
    if score < QUALITY_ACCEPT and "re_erase" not in retries and "re_erase_remnants" not in retries:
        if pass1 > 0:
            retries.append("re_erase_remnants")
    return QualityReport(
        score=score,
        issues=issues,
        retry_actions=list(dict.fromkeys(retries)),
        signals={
            "evf_ratio": evf_ratio,
            "wall_retries": wall_retries,
            "pass1": pass1,
            "sweep": sweep,
            "erased_n": len(erased),
        },
    )


def critique_furnished_heuristic(
    *,
    style: str,
    engine: str,
    erase_meta: Optional[dict] = None,
    remnant_labels: Optional[Sequence[str]] = None,
) -> QualityReport:
    """Heuristic critic for furnished output (legacy path)."""
    issues: List[str] = []
    retries: List[str] = []
    score = 0.88
    remnants = [r for r in (remnant_labels or []) if r]
    eng = engine or ""

    if eng.startswith("flux_inpaint"):
        issues.append("fallback_flux_inpaint")
        score -= 0.12
        retries.append("re_furnish_lora")
    if remnants:
        bad = {"gym machine", "exercise equipment", "weight bench", "pedestal"}
        hit = [r for r in remnants if r in bad or "gym" in r]
        if hit:
            issues.append(f"gym_or_sad_remnants:{','.join(hit[:4])}")
            score -= 0.25
            retries.append("re_erase_remnants")
            retries.append("re_furnish")
        elif len(remnants) >= 3:
            issues.append(f"furniture_remnants:{len(remnants)}")
            score -= 0.15
            retries.append("re_erase_remnants")

    erase = erase_meta or {}
    if int(erase.get("wall_retries") or 0) >= 2:
        issues.append("geometry_risk_from_erase")
        score -= 0.08

    if style == "classic":
        issues.append("classic_needs_bright_guard")
        score -= 0.03

    score = max(0.0, min(1.0, score))
    return QualityReport(
        score=score,
        issues=issues,
        retry_actions=list(dict.fromkeys(retries)),
        signals={"engine": eng, "remnant_n": len(remnants), "style": style},
    )


def parse_vision_critique(raw: str) -> QualityReport:
    """Parse critic JSON → QualityReport (score normalized 0–1)."""
    cleaned = (raw or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    parsed: Dict[str, Any] = {}
    try:
        parsed = json.loads(cleaned)
    except Exception:
        m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                parsed = {}
    if not parsed:
        return QualityReport(
            score=0.65,
            issues=["critic_parse_error"],
            retry_actions=["re_furnish"],
            signals={"raw": cleaned[:300]},
        )

    raw_score = parsed.get("score", 7)
    try:
        s = float(raw_score)
        # Accept 0–10 or 0–1
        score = s / 10.0 if s > 1.0 else s
        score = max(0.0, min(1.0, score))
    except Exception:
        score = 0.65

    issues: List[str] = []
    for key in ("artifacts", "issues", "problems"):
        v = parsed.get(key)
        if isinstance(v, list):
            issues.extend(str(x)[:120] for x in v if x)
    for flag, label in (
        ("architecture_ok", "architecture_fail"),
        ("geometry_ok", "geometry_fail"),
        ("scale_ok", "scale_fail"),
        ("lighting_ok", "lighting_fail"),
    ):
        if flag in parsed and parsed.get(flag) is False:
            issues.append(label)

    verdict = str(parsed.get("verdict") or "").lower()
    retries: List[str] = []
    if verdict == "retry" or score < QUALITY_ACCEPT:
        retries.append("re_furnish")
    if "architecture_fail" in issues or "geometry_fail" in issues:
        retries.append("re_furnish")

    rationale = str(parsed.get("rationale") or "")[:300]
    return QualityReport(
        score=score,
        issues=list(dict.fromkeys(issues))[:12],
        retry_actions=list(dict.fromkeys(retries)),
        signals={
            "verdict": verdict or ("accept" if score >= QUALITY_ACCEPT else "retry"),
            "rationale": rationale,
            "score_10": round(score * 10, 1),
        },
    )


def decide_accept(report: QualityReport, *, retries_left: int, can_afford: bool) -> str:
    """Return accept | retry | accept_with_warning."""
    if report.score >= QUALITY_ACCEPT:
        return "accept"
    if retries_left > 0 and can_afford and report.retry_actions:
        return "retry"
    return "accept_with_warning"


class StagingAgent:
    """Orchestrates one staging job under a hard cost budget."""

    def __init__(self, plan: StagingPlan):
        self.plan = plan
        self.ledger = AgentLedger()
        self.quality: Dict[str, Any] = {}
        self.erase_retries = 0
        self.furnish_retries = 0

    def charge(self, amount: float, label: str, **extra: Any) -> None:
        self.ledger.charge(amount, label, **extra)

    def can_spend(self, next_cost: float) -> bool:
        return self.ledger.can_spend(next_cost, self.plan.budget_hard_usd)

    def over_soft(self) -> bool:
        return self.ledger.spent_usd > self.plan.budget_soft_usd

    def record_quality(self, phase: str, report: QualityReport, decision: str) -> None:
        self.quality[phase] = {**report.to_dict(), "decision": decision}
        logger.info(
            "staging_agent quality phase=%s score=%.2f decision=%s issues=%s",
            phase, report.score, decision, report.issues[:4],
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "agent": "StagingAgent",
            "plan": self.plan.to_dict(),
            "ledger": self.ledger.to_dict(),
            "quality": self.quality,
            "over_soft_budget": self.over_soft(),
            "within_hard_budget": self.ledger.spent_usd <= self.plan.budget_hard_usd + 1e-9,
        }
