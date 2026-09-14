/* OMNIA — Publishing Center (M3.S2)
 *
 * Compact UI block inside PropertyFormPage that lets the agent:
 *   1. Toggle whether the property is listed on the public B2C portal
 *      `ImmobilCloud` (writes `is_listed_on_immobilcloud` on the property doc).
 *   2. Share the property page on WhatsApp / Facebook / Email / Copy Link.
 *
 * Notes:
 * - The public URL is built from `agency.slug` (preferred) + propertyId. The
 *   route is the headless themed agency page (`/api/p/{slug}/{pid}`) served by
 *   site.py. If the property isn't saved yet (create flow), the share buttons
 *   are disabled with a "save first" hint.
 * - When `is_listed_on_immobilcloud=false` the share section still works but
 *   shows a small notice that the property won't appear on the B2C portal.
 */
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function PublishingCenter({
  propertyId,
  property,
  agency,
  isListedOnImmobilCloud,
  onToggleImmobilCloud,
}) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  const slug = agency?.slug || "";
  const publicUrl = useMemo(() => {
    if (!propertyId || !slug) return "";
    return `${BACKEND_URL}/api/p/${slug}/${propertyId}`;
  }, [propertyId, slug]);

  const title = property?.title || "Immobile";
  const priceFmt = property?.price
    ? `€ ${Number(property.price).toLocaleString("it-IT")}`
    : property?.rent_monthly
    ? `€ ${Number(property.rent_monthly).toLocaleString("it-IT")}/mese`
    : "";
  const shareText = `${title}${priceFmt ? " — " + priceFmt : ""}${
    property?.city ? " · " + property.city : ""
  }`;

  const waHref = publicUrl
    ? `https://wa.me/?text=${encodeURIComponent(`${shareText}\n${publicUrl}`)}`
    : null;
  const fbHref = publicUrl
    ? `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(publicUrl)}`
    : null;
  const mailHref = publicUrl
    ? `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(
        `${shareText}\n\n${publicUrl}`
      )}`
    : null;

  const copyLink = async () => {
    if (!publicUrl) return;
    try {
      await navigator.clipboard.writeText(publicUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* no-op */
    }
  };

  return (
    <div data-testid="publishing-center" className="space-y-5">
      {/* ImmobilCloud toggle */}
      <div className="flex items-start justify-between gap-4 bg-stone-50 border border-stone-200 rounded-md p-4">
        <div>
          <div className="text-sm font-medium text-stone-900">
            {t("properties.publish_immobilcloud_title")}
          </div>
          <p className="text-xs text-stone-600 mt-1 max-w-2xl">
            {t("properties.publish_immobilcloud_desc")}
          </p>
        </div>
        <label className="inline-flex items-center cursor-pointer shrink-0">
          <input
            type="checkbox"
            data-testid="publish-immobilcloud-toggle"
            checked={!!isListedOnImmobilCloud}
            onChange={(e) => onToggleImmobilCloud(e.target.checked)}
            className="sr-only peer"
          />
          <span className="relative w-11 h-6 bg-stone-300 rounded-full peer-checked:bg-emerald-600 transition">
            <span className="absolute left-0.5 top-0.5 w-5 h-5 bg-white rounded-full transition peer-checked:translate-x-5" />
          </span>
        </label>
      </div>

      {/* Share row */}
      <div>
        <div className="text-xs uppercase tracking-widest text-stone-500 mb-2">
          {t("properties.share_title")}
        </div>
        {!propertyId ? (
          <p
            data-testid="share-disabled-hint"
            className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2"
          >
            {t("properties.share_save_first")}
          </p>
        ) : !slug ? (
          <p className="text-xs text-stone-500">
            {t("properties.share_no_slug")}
          </p>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            <a
              data-testid="share-whatsapp"
              href={waHref}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-3 py-2 text-xs uppercase tracking-widest bg-[#25D366] text-white rounded hover:opacity-90"
            >
              WhatsApp
            </a>
            <a
              data-testid="share-facebook"
              href={fbHref}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-3 py-2 text-xs uppercase tracking-widest bg-[#1877F2] text-white rounded hover:opacity-90"
            >
              Facebook
            </a>
            <a
              data-testid="share-email"
              href={mailHref}
              className="inline-flex items-center gap-2 px-3 py-2 text-xs uppercase tracking-widest bg-stone-900 text-white rounded hover:bg-stone-700"
            >
              Email
            </a>
            <button
              type="button"
              data-testid="share-copy"
              onClick={copyLink}
              className="inline-flex items-center gap-2 px-3 py-2 text-xs uppercase tracking-widest bg-white border border-stone-300 text-stone-800 rounded hover:bg-stone-50"
            >
              {copied
                ? t("properties.share_copied")
                : t("properties.share_copy_link")}
            </button>
            <span
              data-testid="share-public-url"
              className="text-xs text-stone-500 truncate max-w-xs ml-2"
            >
              {publicUrl}
            </span>
          </div>
        )}
        {propertyId && !isListedOnImmobilCloud && (
          <p
            data-testid="immobilcloud-off-notice"
            className="text-xs text-stone-500 mt-2"
          >
            {t("properties.share_immobilcloud_off")}
          </p>
        )}
      </div>
    </div>
  );
}
