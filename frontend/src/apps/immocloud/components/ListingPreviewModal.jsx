import React from "react";
import { useTranslation } from "react-i18next";
import { ENERGY_CLASS_OPTIONS } from "../../../shared/lib/energyClasses";
import { resolveMediaUrl } from "../../../shared/lib/api";

const FEATURE_KEYS = [
  "balcone", "terrazza", "giardino", "ascensore", "aria_condizionata",
  "posto_auto", "box_auto", "cantina", "arredato", "cucina_abitabile",
  "luminoso", "vista_panoramica", "pannelli_solari",
];

function coverPhoto(listing) {
  const photos = listing?.photos || [];
  return photos.find((p) => p.is_cover) || photos[0] || null;
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
 * Anteprima stile portale (card + scheda + video) prima di inviare in revisione.
 * Media sempre centrati e a riempimento (object-cover), mai letterbox a sinistra.
 */
export default function ListingPreviewModal({
  listing,
  open,
  onClose,
  onConfirm,
  busy,
  confirmLabel,
  showConfirm = true,
  videoUrl = null,
}) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  if (!open || !listing) return null;

  const cover = coverPhoto(listing);
  const img = resolveMediaUrl(cover?.url || "") || null;
  const feats = listing.features || {};
  const activeFeats = FEATURE_KEYS.filter((k) => feats[k]);
  const energy = listing.energy?.energy_class;
  const heating = listing.energy?.heating;
  const gallery = (listing.photos || []).slice(0, 8);

  return (
    <div
      data-testid="listing-preview-modal"
      className="fixed inset-0 z-[70] flex items-center justify-center bg-black/45 p-3 sm:p-4"
      onClick={onClose}
    >
      <div
        className="bg-[#fbf9f5] rounded-2xl shadow-2xl w-full max-w-3xl max-h-[92vh] overflow-y-auto"
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
          {/* Card stile ricerca — centrata */}
          <section data-testid="listing-preview-card" className="text-center">
            <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-2">
              {t("cloud.sell.preview_as_card")}
            </p>
            <div className="bg-white rounded-2xl overflow-hidden border border-stone-200 max-w-sm mx-auto text-left shadow-sm">
              <div className="aspect-[4/3] bg-stone-900 relative overflow-hidden">
                {img ? (
                  <img
                    src={img}
                    alt=""
                    className="absolute inset-0 w-full h-full object-cover object-center"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-stone-500 text-5xl">⌂</div>
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

          {/* Scheda dettaglio — hero full-bleed centrato */}
          <section data-testid="listing-preview-detail" className="bg-white border border-stone-200 rounded-2xl overflow-hidden">
            <p className="text-[10px] uppercase tracking-widest text-stone-500 px-5 pt-4">
              {t("cloud.sell.preview_as_detail")}
            </p>
            {img && (
              <div className="mt-3 relative w-full aspect-[16/10] bg-stone-900 overflow-hidden">
                <img
                  src={img}
                  alt=""
                  data-testid="listing-preview-hero"
                  className="absolute inset-0 w-full h-full object-cover object-center"
                />
                {cover?.is_virtual_staging && (
                  <span className="absolute top-3 left-3 text-[10px] uppercase tracking-widest text-white bg-black/60 px-2 py-1 rounded">
                    {t("cloud.staging_disclosure", "Render virtuale")}
                  </span>
                )}
              </div>
            )}
            <div className="p-5 space-y-4">
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
              {gallery.length > 1 && (
                <div className="grid grid-cols-4 gap-2">
                  {gallery.map((p, i) => (
                    <div key={p.id || i} className="aspect-[4/3] rounded overflow-hidden bg-stone-900 relative">
                      <img
                        src={resolveMediaUrl(p.url)}
                        alt=""
                        className="absolute inset-0 w-full h-full object-cover object-center"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Video tour centrato */}
          {videoUrl && (
            <section data-testid="listing-preview-video" className="space-y-2">
              <p className="text-[10px] uppercase tracking-widest text-stone-500 text-center">
                {t("cloud.sell.video_eyebrow", "Video tour")}
              </p>
              <div className="mx-auto w-full max-w-2xl rounded-xl overflow-hidden bg-stone-900 border border-stone-200">
                <video
                  src={videoUrl}
                  controls
                  playsInline
                  className="block w-full aspect-video object-contain object-center bg-stone-900"
                />
              </div>
            </section>
          )}
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
