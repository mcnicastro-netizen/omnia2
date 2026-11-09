/* OMNIA — SellPage constants (MOVE-ONLY from SellPage.jsx). */
export const CITY_SUGGESTIONS = [
  "Milano", "Roma", "Napoli", "Torino", "Palermo", "Genova", "Bologna", "Firenze",
  "Bari", "Catania", "Venezia", "Verona", "Messina", "Padova", "Trieste", "Brescia",
  "Parma", "Modena", "Reggio Emilia", "Prato", "Perugia", "Livorno", "Ravenna",
  "Cagliari", "Foggia", "Rimini", "Salerno", "Ferrara", "Sassari", "Monza",
  "Bergamo", "Trento", "Vicenza", "Bolzano", "Pisa", "Novara", "Ancona", "Udine",
  "Siracusa", "Pescara", "Lecce", "La Spezia", "Como", "Treviso", "Taranto",
  "Mascalucia", "Acireale", "Misterbianco", "Gravina di Catania", "San Giovanni la Punta",
];

export const STAGING_PENDING_KEY = "omnia_staging_pending";

export const B2C_MEDIA_UPLOAD = "/cloud/me/properties/media/upload-tmp";
export const B2C_MAX_PHOTOS = 30;

export const B2C_FEATURES = [
  "balcone", "terrazza", "giardino", "ascensore", "aria_condizionata",
  "posto_auto", "box_auto", "cantina", "arredato", "cucina_abitabile",
  "luminoso", "vista_panoramica", "pannelli_solari",
];

export const CONDITIONS = ["nuovo", "ottime", "buone", "da_ristrutturare", "ristrutturato"];
export const HEATING = ["autonomo", "centralizzato", "assente"];

export const empty = {
  title: "",
  description: "",
  property_type: "appartamento",
  operation: "sale",
  city: "",
  zone: "",
  address: "",
  street_number: "",
  postal_code: "",
  price: "",
  rent_monthly: "",
  condo_fees: "",
  surface_sqm: "",
  rooms: "",
  bedrooms: "",
  bathrooms: "",
  floor: "",
  total_floors: "",
  year_built: "",
  condition: "",
  energy: { energy_class: "", heating: "" },
  features: Object.fromEntries(B2C_FEATURES.map((k) => [k, false])),
  photos: [],
  floor_plan_url: "",
  contact_display_name: "",
  contact_show_email: true,
  contact_show_phone: false,
  contact_show_whatsapp: false,
  contact_phone: "",
  contact_whatsapp: "",
};

export const PROPERTY_TYPES = [
  "appartamento", "villa", "loft", "attico", "monolocale",
  "rustico_casale", "ufficio", "negozio", "magazzino",
  "garage_box", "terreno_agricolo", "terreno_edificabile", "altro",
];
