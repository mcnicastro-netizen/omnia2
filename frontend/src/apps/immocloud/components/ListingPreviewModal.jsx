import React from "react";
import { useTranslation } from "react-i18next";
import { ENERGY_CLASS_OPTIONS } from "../../../shared/lib/energyClasses";

const FEATURE_KEYS = [
  "balcone", "terrazza", "giardino", "ascensore", "aria_condizionata",
  "posto_auto", "box_auto", "cantina", "arredato", "cucina_abitabile",
  "luminoso", "vista_panoramica", "pannelli_solari",
];

function coverUrl(listing) {
  const photos = listing?.photos || [];
  const cover = photos.find((p) => p.is_cover) || photos[0];
  return cover?.url || null;
}

function energyLabel(code) {
  const opt = ENERGY_CLASS_OPTIONS.find((o) => o.value === code);
  return opt?.label || code;
}

function formatPrice(listing, lang) {
  if (listing.operation === "rent" && listing.rent_monthly) {
    return `€ ${Number(listing.rent_monthly).toLocaleString(lang)}/mese`;
  }
  if (listing.price) {
    return `€ ${Number(listing.price).toLocaleString(lang)}`;
  }
  return "—";
}

function streetLine(listing) {
  const via = (listing.address || "").trim();
  const civ = (listing.street_number || "").trim();
  if (via && civ) return `${via}, ${civ}`;
  return via || civ || "";
}

/**
 * Anteprima stile portale (card + scheda) prima di inviare in revisione.
 */
export default function ListingPreviewModal({
  listing,
  open,
  onClose,
  onConfirm,
  busy,
  confirmLabel,
  showConfirm = true,
}) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  if (!open || !listing) return null;

  const img = coverUrl(listing);
  const feats = listing.features || {};
  const activeFeats = FEATURE_KEYS.filter((k) => feats[k]);
  const energy = listing.energy?.energy_class;
  const heating = listing.energy?.heating;

  return (
    <div
      data-testid="listing-preview-modal"
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/45 p-4"
      onClick={onClose}
    >
      <div
        className="bg-[#fbf9f5] rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 bg-[#fbf9f5]/95 backdrop-blur border-b border-stone-200 px-5 py-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.22em] text-[#C19A6B]">
              {t("cloud.sell.preview_eyebrow")}
            </p>
            <h2
              className="text-xl text-[#0B1E3F] font-light mt-1"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("cloud.sell.preview_title")}
            </h2>
            <p className="text-xs text-stone-600 mt-1">{t("cloud.sell.preview_subtitle")}</p>
          </div>
          <button
            type="button"
            data-testid="listing-preview-close"
            onClick={onClose}
            className="text-stone-500 hover:text-stone-800 text-sm px-2"
          >
            ✕
          </button>
        </div>

        <div className="p-5 space-y-6">
          {/* Card stile ricerca */}
          <section data-testid="listing-preview-card">
            <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
              {t("cloud.sell.preview_as_card")}
            </p>
            <div className="bg-white rounded-2xl overflow-hidden border border-stone-200 max-w-sm">
              <div className="aspect-[4/3] bg-stone-100 relative">
                {img ? (
                  <img src={img} alt="" className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-stone-300 text-5xl">⌂</div>
                )}
                {energy && (
                  <span className="absolute top-3 right-3 text-[10px] uppercase tracking-widest bg-white/90 px-2 py-1 rounded">
                    {t("cloud.energy")}: {energyLabel(energy)}
                  </span>
                )}
              </div>
              <div className="p-4">
                <p
                  className="text-xl font-semibold text-[#0B1E3F]"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  {formatPrice(listing, lang)}
                </p>
                <h3 className="text-sm font-medium text-stone-900 mt-1 line-clamp-2">
                  {listing.title || t("cloud.sell.untitled")}
                </h3>
                <p className="text-xs text-stone-500 mt-1">
                  {listing.city}
                  {listing.zone ? ` · ${listing.zone}` : ""}
                </p>
                <div className="flex items-center gap-3 mt-3 text-xs text-stone-600">
                  {listing.surface_sqm ? <span>{listing.surface_sqm} m²</span> : null}
                  {listing.rooms ? <span>· {listing.rooms} {t("cloud.rooms_short")}</span> : null}
                  {listing.bathrooms ? <span>· {listing.bathrooms} {t("cloud.baths_short")}</span> : null}
                </div>
              </div>
            </div>
          </section>

          {/* Scheda dettaglio */}
          <section data-testid="listing-preview-detail" className="bg-white border border-stone-200 rounded-2xl p-5 space-y-4">
            <p className="text-[10px] uppercase tracking-widest text-stone-500">
              {t("cloud.sell.preview_as_detail")}
            </p>
            <h3
              className="text-2xl text-[#0B1E3F] font-light"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {listing.title || t("cloud.sell.untitled")}
            </h3>
            <p className="text-lg font-medium text-[#0B1E3F]">{formatPrice(listing, lang)}</p>
            <p className="text-sm text-stone-600">
              {[streetLine(listing), listing.postal_code, listing.city, listing.zone]
                .filter(Boolean)
                .join(" · ")}
            </p>
            <dl className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
              {listing.property_type && (
                <div><dt className="text-[10px] uppercase text-stone-400">{t("cloud.sell.f_type")}</dt><dd>{listing.property_type}</dd></div>
              )}
              {listing.condition && (
                <div><dt className="text-[10px] uppercase text-stone-400">{t("cloud.sell.f_condition")}</dt><dd>{t(`cloud.sell.condition_${listing.condition}`, { defaultValue: listing.condition })}</dd></div>
              )}
              {listing.floor != null && listing.floor !== "" && (
                <div><dt className="text-[10px] uppercase text-stone-400">{t("cloud.sell.f_floor")}</dt><dd>{listing.floor}{listing.total_floors ? ` / ${listing.total_floors}` : ""}</dd></div>
              )}
              {listing.year_built && (
                <div><dt className="text-[10px] uppercase text-stone-400">{t("cloud.sell.f_year_built")}</dt><dd>{listing.year_built}</dd></div>
              )}
              {energy && (
                <div><dt className="text-[10px] uppercase text-stone-400">{t("cloud.sell.f_energy")}</dt><dd>{energyLabel(energy)}</dd></div>
              )}
              {heating && (
                <div><dt className="text-[10px] uppercase text-stone-400">{t("cloud.sell.f_heating")}</dt><dd>{t(`cloud.sell.heating_${heating}`, { defaultValue: heating })}</dd></div>
              )}
              {listing.condo_fees != null && listing.condo_fees !== "" && (
                <div><dt className="text-[10px] uppercase text-stone-400">{t("cloud.sell.f_condo_fees")}</dt><dd>€ {Number(listing.condo_fees).toLocaleString(lang)}</dd></div>
              )}
            </dl>
            {activeFeats.length > 0 && (
              <div>
                <p className="text-[10px] uppercase tracking-widest text-stone-400 mb-2">{t("cloud.sell.f_features")}</p>
                <div className="flex flex-wrap gap-2">
                  {activeFeats.map((k) => (
                    <span key={k} className="text-xs border border-stone-200 rounded-full px-2.5 py-1 text-stone-700">
                      {t(`cloud.sell.feat_${k}`, { defaultValue: k })}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {listing.description && (
              <div>
                <p className="text-[10px] uppercase tracking-widest text-stone-400 mb-2">{t("cloud.sell.f_description")}</p>
                <p className="text-sm text-stone-700 whitespace-pre-wrap leading-relaxed">{listing.description}</p>
              </div>
            )}
            {(listing.photos || []).length > 1 && (
              <div className="grid grid-cols-4 gap-2">
                {(listing.photos || []).slice(0, 8).map((p, i) => (
                  <div key={p.id || i} className="aspect-[4/3] rounded overflow-hidden bg-stone-100">
                    <img src={p.url} alt="" className="w-full h-full object-cover" />
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>

        <div className="sticky bottom-0 bg-white border-t border-stone-200 px-5 py-4 flex flex-wrap gap-3 justify-end">
          <button
            type="button"
            data-testid="listing-preview-edit"
            onClick={onClose}
            className="px-5 py-2.5 text-xs uppercase tracking-widest border border-stone-300 rounded-lg hover:bg-stone-50"
          >
            {t("cloud.sell.preview_edit")}
          </button>
          {showConfirm && (
            <button
              type="button"
              data-testid="listing-preview-confirm"
              disabled={busy}
              onClick={onConfirm}
              className="px-5 py-2.5 text-xs uppercase tracking-widest bg-[#0B1E3F] text-white rounded-lg hover:bg-[#C19A6B] disabled:opacity-50"
            >
              {busy ? t("common.saving") : (confirmLabel || t("cloud.sell.preview_confirm"))}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
