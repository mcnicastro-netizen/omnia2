"""OMNIA — Client Request (Richiesta CRM).

D-089: richiesta = oggetto CRM distinto dal cliente.
  - Tipo A `property_interest`: interesse su immobile noto
  - Tipo B `search_brief`: brief di ricerca (criteri)
1:1 di default; stesso cliente può avere N richieste nel tempo.
"""
from typing import List, Optional, Literal
from pydantic import Field

from shared.models.base import TenantModel, OmniaBaseModel
from shared.models.client import SearchPreferences

RequestType = Literal["property_interest", "search_brief"]
RequestStatus = Literal["open", "matched", "negotiating", "won", "lost", "archived"]


class ClientRequestInDB(TenantModel):
    """Richiesta collegata a un cliente acquirente/affittuario/investitore."""
    client_id: str
    request_type: RequestType = "search_brief"
    status: RequestStatus = "open"
    # Fonte acquisizione: ImmobilCloud | widget_* | manual | migration_preferences | import | …
    source: str = Field(default="manual", max_length=100)
    title: Optional[str] = Field(default=None, max_length=300)
    # Tipo A — immobile di interesse (portafoglio o MLS)
    property_id: Optional[str] = None
    # Criteri di ricerca (tipo B; anche A può tenerli)
    criteria: SearchPreferences = Field(default_factory=SearchPreferences)
    # Condividi con altre agenzie MLS per matching inverso
    mls_shared: bool = False
    assigned_agent_id: Optional[str] = None
    notes: Optional[str] = Field(default=None, max_length=5000)
    # Collegamento a lead legacy (ImmobilCloud / widget)
    lead_id: Optional[str] = None


class ClientRequestCreate(OmniaBaseModel):
    client_id: str
    request_type: RequestType = "search_brief"
    source: str = "manual"
    title: Optional[str] = None
    property_id: Optional[str] = None
    criteria: Optional[SearchPreferences] = None
    mls_shared: bool = False
    notes: Optional[str] = None
    status: RequestStatus = "open"


class ClientRequestUpdate(OmniaBaseModel):
    request_type: Optional[RequestType] = None
    status: Optional[RequestStatus] = None
    title: Optional[str] = None
    property_id: Optional[str] = None
    criteria: Optional[SearchPreferences] = None
    mls_shared: Optional[bool] = None
    auto_match: Optional[bool] = None
    match_tolerances: Optional[dict] = None
    notes: Optional[str] = None
    assigned_agent_id: Optional[str] = None


class ClientRequestListItem(OmniaBaseModel):
    id: str
    agency_id: str
    client_id: str
    request_type: RequestType
    status: RequestStatus
    source: str
    title: Optional[str] = None
    property_id: Optional[str] = None
    mls_shared: bool = False
    criteria: Optional[dict] = None
    notes: Optional[str] = None
    lead_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    # Enrichment (lista)
    client_name: Optional[str] = None
    client_type: Optional[str] = None
    property_title: Optional[str] = None
    property_ref: Optional[str] = None
    best_match_score: Optional[int] = None
    best_match_scope: Optional[Literal["portfolio", "mls", "none"]] = None
    matches_portfolio: int = 0
    matches_mls: int = 0


class ClientRequestListResponse(OmniaBaseModel):
    items: List[ClientRequestListItem]
    total: int
    page: int
    page_size: int
    counts: dict = Field(default_factory=dict)
