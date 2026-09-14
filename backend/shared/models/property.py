"""OMNIA — Property model (real estate listings, multi-tenant)."""
from typing import List, Optional, Literal
from pydantic import Field, EmailStr
from uuid import uuid4

from shared.models.base import TenantModel, OmniaBaseModel, TimestampedModel

# 16 property types (as planned in PROGRAMMA_OMNIA)
PropertyType = Literal[
    "appartamento", "villa", "villetta_a_schiera", "loft", "attico",
    "monolocale", "rustico_casale", "ufficio", "negozio", "magazzino",
    "capannone", "garage_box", "terreno_agricolo", "terreno_edificabile",
    "palazzo_stabile", "altro",
]

PropertyOperation = Literal["sale", "rent", "rent_to_buy", "auction"]
PropertyStatus = Literal["draft", "active", "reserved", "sold", "rented", "withdrawn"]
EnergyClass = Literal["A4", "A3", "A2", "A1", "A", "B", "C", "D", "E", "F", "G", "exempt"]
HeatingType = Literal["autonomo", "centralizzato", "assente"]
FurnishedState = Literal["arredato", "parz_arredato", "non_arredato"]
PropertyCondition = Literal["nuovo", "ottime", "buone", "da_ristrutturare", "ristrutturato"]


class PropertyFeatures(OmniaBaseModel):
    """25 boolean features for filtering and matching (M2.S4)."""
    balcone: bool = False
    terrazza: bool = False
    giardino: bool = False
    piscina: bool = False
    ascensore: bool = False
    aria_condizionata: bool = False
    riscaldamento_autonomo: bool = False
    cantina: bool = False
    soffitta: bool = False
    posto_auto: bool = False
    box_auto: bool = False
    portineria: bool = False
    videocitofono: bool = False
    allarme: bool = False
    porta_blindata: bool = False
    cucina_abitabile: bool = False
    camino: bool = False
    parquet: bool = False
    vista_panoramica: bool = False
    luminoso: bool = False
    arredato: bool = False
    pannelli_solari: bool = False
    cancello_elettrico: bool = False
    impianto_domotico: bool = False
    accesso_disabili: bool = False


class PropertyPhoto(OmniaBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    url: str
    caption: Optional[str] = None
    order: int = 0
    is_cover: bool = False


class PropertyOwner(OmniaBaseModel):
    """Reserved (internal) owner info — never exposed to public portal."""
    name: Optional[str] = Field(default=None, max_length=200)
    phone: Optional[str] = Field(default=None, max_length=30)
    email: Optional[EmailStr] = None
    notes: Optional[str] = Field(default=None, max_length=2000)


class PropertyEnergy(OmniaBaseModel):
    energy_class: Optional[EnergyClass] = None
    energy_value: Optional[float] = None  # kWh/m²·anno
    heating: Optional[HeatingType] = None


class PropertyInDB(TenantModel):
    """Property document stored in MongoDB. Multi-tenant via agency_id."""
    # Identification
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, max_length=10000)
    reference_code: Optional[str] = Field(default=None, max_length=50)  # codice interno agenzia

    # Classification
    property_type: PropertyType = "appartamento"
    operation: PropertyOperation = "sale"
    status: PropertyStatus = "draft"
    condition: Optional[PropertyCondition] = None

    # Location
    address: Optional[str] = Field(default=None, max_length=300)
    city: str = Field(min_length=1, max_length=100)
    province: Optional[str] = Field(default=None, max_length=10)
    postal_code: Optional[str] = Field(default=None, max_length=10)
    zone: Optional[str] = Field(default=None, max_length=100)  # quartiere/zona
    country: str = "IT"
    lat: Optional[float] = None
    lng: Optional[float] = None
    hide_address: bool = False  # privacy mode: hide exact address publicly

    # Economics
    price: Optional[float] = None
    price_per_sqm: Optional[float] = None
    rent_monthly: Optional[float] = None
    condo_fees: Optional[float] = None  # spese condominiali mensili
    price_negotiable: bool = False

    # Size / rooms
    surface_sqm: Optional[float] = None
    surface_useful_sqm: Optional[float] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor: Optional[int] = None  # piano
    total_floors: Optional[int] = None

    # Year / construction
    year_built: Optional[int] = None

    # Features (25 flags)
    features: PropertyFeatures = Field(default_factory=PropertyFeatures)
    furnished: Optional[FurnishedState] = None

    # Energy
    energy: PropertyEnergy = Field(default_factory=PropertyEnergy)

    # Media
    photos: List[PropertyPhoto] = Field(default_factory=list)
    virtual_tour_url: Optional[str] = Field(default=None, max_length=500)
    floor_plan_url: Optional[str] = Field(default=None, max_length=500)

    # Internal / privacy
    owner: PropertyOwner = Field(default_factory=PropertyOwner)
    seller_client_id: Optional[str] = None  # FK to Client (seller/landlord) — M2.S3.5 D-026
    is_exclusive: bool = False  # esclusiva agenzia
    commission_pct: Optional[float] = None  # provvigione
    visibility: Literal["public", "mls_only", "private"] = "public"
    # M3.S9 · Privacy audit 4 livelli (D-062)
    #   L1 = anonimo pubblico             (no indirizzo, no planimetria, no seller data, prezzo indicativo)
    #   L2 = utente B2C autenticato       (foto tutte, quartiere, ancora niente indirizzo esatto)
    #   L3 = utente qualificato (lead+GDPR con email confermata) → indirizzo esatto + planimetria
    #   L4 = agenzia proprietaria/agente  → tutto: proprietario, min_price trattabile, note interne
    privacy_level: Literal["L1", "L2", "L3", "L4"] = "L2"
    min_price_negotiable: Optional[float] = None  # visibile solo L4
    seller_notes: Optional[str] = Field(default=None, max_length=2000)  # visibile solo L4
    listing_agent_id: Optional[str] = None  # user_id of responsible agent

    # Cross-portal publishing (M3.S1 → finalized in M3.S2 Publishing Center)
    # When True, this property appears on the public ImmobilCloud B2C portal
    # (cloud.omniarealestateecosystem.it). Default ON (opt-out per agent/admin).
    is_listed_on_immobilcloud: bool = True

    # M3.S5 — Private listing (B2C user publishing without agency)
    is_private_listing: bool = False
    owner_user_id: Optional[str] = None  # link to users.id (B2C account)
    moderation_status: Literal["approved", "pending", "rejected"] = "approved"
    moderation_notes: Optional[str] = Field(default=None, max_length=2000)
    moderation_reviewed_at: Optional[str] = None
    moderation_reviewed_by: Optional[str] = None

    # Counters
    view_count: int = 0
    lead_count: int = 0


class PropertyCreate(OmniaBaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: Optional[str] = None
    property_type: PropertyType = "appartamento"
    operation: PropertyOperation = "sale"
    city: str = Field(min_length=1, max_length=100)
    address: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    zone: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    hide_address: bool = False
    price: Optional[float] = None
    rent_monthly: Optional[float] = None
    condo_fees: Optional[float] = None
    price_negotiable: bool = False
    surface_sqm: Optional[float] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    year_built: Optional[int] = None
    condition: Optional[PropertyCondition] = None
    features: Optional[PropertyFeatures] = None
    furnished: Optional[FurnishedState] = None
    energy: Optional[PropertyEnergy] = None
    reference_code: Optional[str] = None
    status: PropertyStatus = "draft"
    owner: Optional[PropertyOwner] = None
    seller_client_id: Optional[str] = None
    is_exclusive: bool = False
    commission_pct: Optional[float] = None
    visibility: Literal["public", "mls_only", "private"] = "public"
    privacy_level: Literal["L1", "L2", "L3", "L4"] = "L2"
    min_price_negotiable: Optional[float] = None
    seller_notes: Optional[str] = None
    virtual_tour_url: Optional[str] = None
    photos: Optional[List[PropertyPhoto]] = None
    is_listed_on_immobilcloud: bool = True  # M3.S2 Publishing Center


class PropertyUpdate(OmniaBaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[PropertyType] = None
    operation: Optional[PropertyOperation] = None
    status: Optional[PropertyStatus] = None
    condition: Optional[PropertyCondition] = None
    city: Optional[str] = None
    address: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    zone: Optional[str] = None
    hide_address: Optional[bool] = None
    price: Optional[float] = None
    rent_monthly: Optional[float] = None
    condo_fees: Optional[float] = None
    price_negotiable: Optional[bool] = None
    surface_sqm: Optional[float] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    year_built: Optional[int] = None
    features: Optional[PropertyFeatures] = None
    furnished: Optional[FurnishedState] = None
    energy: Optional[PropertyEnergy] = None
    photos: Optional[List[PropertyPhoto]] = None
    virtual_tour_url: Optional[str] = None
    owner: Optional[PropertyOwner] = None
    seller_client_id: Optional[str] = None
    is_exclusive: Optional[bool] = None
    commission_pct: Optional[float] = None
    visibility: Optional[Literal["public", "mls_only", "private"]] = None
    privacy_level: Optional[Literal["L1", "L2", "L3", "L4"]] = None
    min_price_negotiable: Optional[float] = None
    seller_notes: Optional[str] = None
    reference_code: Optional[str] = None
    is_listed_on_immobilcloud: Optional[bool] = None  # M3.S2 Publishing Center


class PropertyListItem(OmniaBaseModel):
    """Lightweight item for list view (no description, no owner)."""
    id: str
    title: str
    property_type: PropertyType
    operation: PropertyOperation
    status: PropertyStatus
    city: str
    address: Optional[str] = None
    price: Optional[float] = None
    rent_monthly: Optional[float] = None
    surface_sqm: Optional[float] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    cover_photo_url: Optional[str] = None
    reference_code: Optional[str] = None
    created_at: str
    updated_at: str


class PropertyListResponse(OmniaBaseModel):
    items: List[PropertyListItem]
    total: int
    page: int
    page_size: int


# -------------------- IMPORT --------------------

ImportSource = Literal["csv", "xml_feed"]
ImportStatus = Literal["pending", "processing", "completed", "completed_with_errors", "failed"]


class ImportJob(TenantModel):
    """Audit log of bulk import jobs (CSV/XML)."""
    source: ImportSource
    source_label: str  # filename for CSV, URL for XML
    status: ImportStatus = "pending"
    total_rows: int = 0
    imported_count: int = 0
    error_count: int = 0
    errors: List[dict] = Field(default_factory=list)  # [{row: N, message: "..."}]
    initiated_by: str  # user_id


class CSVImportPayload(OmniaBaseModel):
    """Bulk CSV import — rows already parsed by frontend."""
    rows: List[dict]  # already mapped to canonical OMNIA field names
    filename: Optional[str] = None


class XMLImportPayload(OmniaBaseModel):
    feed_url: Optional[str] = Field(default=None, max_length=500)
    xml_content: Optional[str] = Field(default=None, max_length=10_000_000)  # up to 10MB pasted
