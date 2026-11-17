"""OMNIA — Membership (B01 / D-173): appartenenza operativa a un'organizzazione."""
from typing import Literal, Optional
from uuid import uuid4

from pydantic import Field

from shared.models.base import OmniaBaseModel, TimestampedModel, utcnow_iso

MembershipStatus = Literal["active", "ended", "suspended"]
OperationalRole = Literal[
    "agency_admin",
    "agent",
    "branch_admin",
    "branch_agent",
    "group_admin",
]


class MembershipInDB(TimestampedModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    organization_id: str  # agencies.id (Organization)
    operational_role: OperationalRole
    membership_status: MembershipStatus = "active"
    valid_from: str = Field(default_factory=utcnow_iso)
    valid_to: Optional[str] = None
    ended_at: Optional[str] = None


class MembershipPublic(OmniaBaseModel):
    id: str
    user_id: str
    organization_id: str
    operational_role: str
    membership_status: MembershipStatus
    valid_from: str
    valid_to: Optional[str] = None
