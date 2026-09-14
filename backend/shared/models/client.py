"""OMNIA — Client (cliente) + Lead model for CRM."""
from typing import List, Optional, Literal
from pydantic import Field, EmailStr
from uuid import uuid4

from shared.models.base import TenantModel, OmniaBaseModel

ClientType = Literal["buyer", "seller", "tenant", "landlord", "investor"]
ClientStatus = Literal["new", "contacted", "qualified", "negotiating", "closed_won", "closed_lost", "archived"]
LeadStatus = Literal["new", "contacted", "visit_scheduled", "visited", "offer_made", "won", "lost"]


class SearchPreferences(OmniaBaseModel):
    """What the client is looking for. Mirrors idealista-style filters."""
    operation: Optional[Literal["sale", "rent", "rent_to_buy", "auction"]] = None
    property_types: List[str] = Field(default_factory=list)
    cities: List[str] = Field(default_factory=list)
    zones: List[str] = Field(default_factory=list)
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    surface_min: Optional[float] = None
    surface_max: Optional[float] = None
    rooms_min: Optional[int] = None
    rooms_max: Optional[int] = None
    bedrooms_min: Optional[int] = None
    bathrooms_min: Optional[int] = None
    # Acceptable conditions (multi-select). Empty list = any.
    conditions: List[str] = Field(default_factory=list)
    # Floor preferences (multi-select): "terra", "intermedi", "ultimo". Empty = any.
    floor_preferences: List[str] = Field(default_factory=list)
    # Must-have feature flags (subset of PropertyFeatures bool keys).
    must_have_features: List[str] = Field(default_factory=list)
    # Energy class requirement: "A","B","C","D","E","F","G". Min acceptable class.
    energy_min_class: Optional[str] = None
    # Multimedia requirements
    needs_photos: bool = False
    needs_virtual_tour: bool = False
    notes: Optional[str] = Field(default=None, max_length=2000)


class ClientInDB(TenantModel):
    """Client (CRM record). Multi-tenant via agency_id."""
    name: str = Field(min_length=1, max_length=200)
    surname: Optional[str] = Field(default=None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    whatsapp: Optional[str] = Field(default=None, max_length=30)
    fiscal_code: Optional[str] = Field(default=None, max_length=20)
    client_type: ClientType = "buyer"
    status: ClientStatus = "new"
    source: Optional[str] = Field(default=None, max_length=100)  # "Idealista", "Walk-in", "Referral", ...
    assigned_agent_id: Optional[str] = None
    preferences: SearchPreferences = Field(default_factory=SearchPreferences)
    notes: Optional[str] = Field(default=None, max_length=5000)
    gdpr_consent: bool = False


class ClientCreate(OmniaBaseModel):
    name: str = Field(min_length=1, max_length=200)
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    fiscal_code: Optional[str] = None
    client_type: ClientType = "buyer"
    status: ClientStatus = "new"
    source: Optional[str] = None
    preferences: Optional[SearchPreferences] = None
    notes: Optional[str] = None
    gdpr_consent: bool = False


class ClientUpdate(OmniaBaseModel):
    name: Optional[str] = None
    surname: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    fiscal_code: Optional[str] = None
    client_type: Optional[ClientType] = None
    status: Optional[ClientStatus] = None
    source: Optional[str] = None
    preferences: Optional[SearchPreferences] = None
    notes: Optional[str] = None
    gdpr_consent: Optional[bool] = None


class ClientListItem(OmniaBaseModel):
    id: str
    name: str
    surname: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    client_type: ClientType
    status: ClientStatus
    source: Optional[str] = None
    created_at: str
    updated_at: str


class ClientListResponse(OmniaBaseModel):
    items: List[ClientListItem]
    total: int
    page: int
    page_size: int


class ClientCSVPayload(OmniaBaseModel):
    rows: List[dict]
    filename: Optional[str] = None


# Lead = manifest interest of a Client toward a specific Property
class LeadInDB(TenantModel):
    client_id: str
    property_id: str
    status: LeadStatus = "new"
    score: Optional[int] = None  # 0-100 matching score
    notes: Optional[str] = Field(default=None, max_length=2000)
    assigned_agent_id: Optional[str] = None
