"""OMNIA StagingAgent — specialized virtual-staging controller (D-125).

Not a black-box embed of a third-party staging SaaS. Owns the plan → erase →
furnish → critique → retry loop on top of fal primitives already in
`virtual_staging.py`, with a hard USD cost cap so B2C resale at ~€0.90/img
stays profitable (D-033 unit economics).

Pattern mirrors HAL Legal (router + validator): a planner/critic wraps the
execution engines; quality gates decide retry vs accept vs fail-soft.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

logger = logging.getLogger("omnia.staging_agent")

# Soft target (D-033) vs hard cap that still leaves margin at €0.90 (~$1).
BUDGET_SOFT_USD = {
    "standard": 0.08,
    "empty": 0.18,
    "reverse": 0.24,
}
BUDGET_HARD_USD = {
    "standard": 0.14,
    "empty": 0.28,
    "reverse": 0.32,
}

# Minimum critic score (0–1) to accept without retry.
QUALITY_ACCEPT = 0.72
# Below this after retries → mark job warning (still deliver best attempt).
QUALITY_WARN = 0.55
MAX_FURNISH_RETRIES = 1
MAX_ERASE_RETRIES = 1


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
) -> StagingPlan:
    """Build an execution plan with mode-aware cost caps (no network)."""
    m = mode if mode in ("standard", "reverse", "empty") else "standard"
    n = max(1, min(int(num_variants or 1), 4))
    if variant_mode == "multi_style" and styles_list:
        styles = [s for s in styles_list if s][:n] or [style or "modern"]
    else:
        styles = [style or "modern"]
    soft = BUDGET_SOFT_USD[m] + max(0, n - 1) * 0.06
    hard = BUDGET_HARD_USD[m] + max(0, n - 1) * 0.07
    notes: List[str] = []
    if m in ("reverse", "empty"):
        notes.append("semantic_erase_evf_then_florence_remnants")
    if m != "empty":
        notes.append("apartment_staging_lora_primary")
    notes.append("no_third_party_staging_saas_embed")
    return StagingPlan(
        mode=m,
        need_erase=m in ("reverse", "empty"),
        need_furnish=m != "empty",
        num_variants=n if m != "empty" else 1,
        styles=styles if m != "empty" else ["empty"],
        room_type=room_type or "living",
        budget_soft_usd=round(soft, 4),
        budget_hard_usd=round(hard, 4),
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
        # Do not retry erase over openings — that invents walls.
    if wall_retries >= 3:
        issues.append("many_wall_retries")
        score -= 0.12

    if evf_ratio < 0.02 and pass1 == 0 and sweep == 0:
        issues.append("no_furniture_detected")
        # Empty-looking source: high score for empty mode.
        score = max(score, 0.85)
    elif evf_ratio >= 0.02 and not erased:
        issues.append("mask_built_but_nothing_erased")
        score -= 0.35
        retries.append("re_erase")
    elif pass1 + sweep >= 6:
        # Still finding many boxes after EVF → likely remnants remain.
        issues.append("high_remnant_box_count")
        score -= 0.18
        retries.append("re_erase_remnants")

    # Soft clutter left after big pieces.
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
    """Heuristic critic for furnished output (no vision LLM — avoids Gemini image 429)."""
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

    # Style-agnostic listing look: classic historically drifts "old/sad".
    if style == "classic":
        issues.append("classic_needs_bright_guard")
        score -= 0.03  # prompt already brightened; soft signal only

    score = max(0.0, min(1.0, score))
    return QualityReport(
        score=score,
        issues=issues,
        retry_actions=list(dict.fromkeys(retries)),
        signals={"engine": eng, "remnant_n": len(remnants), "style": style},
    )


def decide_accept(report: QualityReport, *, retries_left: int, can_afford: bool) -> str:
    """Return accept | retry | accept_with_warning."""
    if report.score >= QUALITY_ACCEPT:
        return "accept"
    if retries_left > 0 and can_afford and report.retry_actions:
        return "retry"
    if report.score >= QUALITY_WARN:
        return "accept_with_warning"
    return "accept_with_warning"  # still deliver best effort for B2C UX


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
