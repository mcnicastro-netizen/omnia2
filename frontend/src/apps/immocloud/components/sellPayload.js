/* OMNIA — SellPage payload helpers (MOVE-ONLY). */
import { B2C_FEATURES } from "./sellConstants";

/** HAL description needs enough structured data to avoid inventing facts. */
export function halDescriptionReady(form) {
  const hasCity = Boolean((form.city || "").trim());
  const hasType = Boolean(form.property_type);
  const hasSize = Boolean(form.surface_sqm) || Boolean(form.rooms);
  return hasCity && hasType && hasSize;
}

export function buildListingPayload(form) {
  const payload = { ...form };
  ["price", "rent_monthly", "condo_fees", "surface_sqm", "rooms", "bedrooms", "bathrooms", "floor", "total_floors", "year_built"].forEach((k) => {
    if (payload[k] === "" || payload[k] == null) delete payload[k];
    else payload[k] = Number(payload[k]);
  });
  if (!payload.floor_plan_url) payload.floor_plan_url = null;
  if (!payload.condition) delete payload.condition;
  if (!payload.zone) delete payload.zone;
  const sn = (payload.street_number || "").trim();
  payload.street_number = sn || null;
  if (!Array.isArray(payload.photos)) payload.photos = [];
  // Persist only Object Storage / remote URLs + cover flag (drop local preview / upload bookkeeping).
  // Staging must be saved as /api/media/… — data: URLs are stripped and would wipe AI photos.
  payload.photos = payload.photos
    .filter((p) => p && typeof p.url === "string" && !p.url.startsWith("data:") && p.upload_status !== "error")
    .map((p, i) => {
      const out = {
        id: p.id,
        url: p.url,
        caption: p.caption || "",
        order: p.order != null ? p.order : i,
        is_cover: Boolean(p.is_cover),
      };
      if (p.is_virtual_staging) {
        out.is_virtual_staging = true;
        if (p.source_photo_id) out.source_photo_id = p.source_photo_id;
        if (p.staging_mode) out.staging_mode = p.staging_mode;
      }
      return out;
    });
  if (payload.photos.length && !payload.photos.some((p) => p.is_cover)) {
    payload.photos[0].is_cover = true;
  }

  const energy = { ...(payload.energy || {}) };
  if (!energy.energy_class) delete energy.energy_class;
  if (!energy.heating) delete energy.heating;
  if (Object.keys(energy).length) payload.energy = energy;
  else delete payload.energy;

  const feats = {};
  B2C_FEATURES.forEach((k) => {
    if (payload.features?.[k]) feats[k] = true;
  });
  if (Object.keys(feats).length) payload.features = feats;
  else delete payload.features;

  payload.contact_public = {
    display_name: payload.contact_display_name || undefined,
    show_email: Boolean(payload.contact_show_email),
    show_phone: Boolean(payload.contact_show_phone),
    show_whatsapp: Boolean(payload.contact_show_whatsapp),
    phone: payload.contact_phone || null,
    whatsapp: payload.contact_whatsapp || null,
  };
  delete payload.contact_display_name;
  delete payload.contact_show_email;
  delete payload.contact_show_phone;
  delete payload.contact_show_whatsapp;
  delete payload.contact_phone;
  delete payload.contact_whatsapp;
  return payload;
}

