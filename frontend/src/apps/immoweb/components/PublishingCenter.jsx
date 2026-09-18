/* OMNIA — Publishing Center (M3.S2)
 *
 * Compact UI block inside PropertyFormPage that lets the agent:
 *   1. Toggle ImmobilCloud listing.
 *   2. Share the public property URL — explicitly "con chi":
 *      - a CRM client (WhatsApp to their phone / Email to their inbox)
 *      - or a channel (WhatsApp, Facebook, Email, Telegram, copy link)
 */
import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/** Normalize IT phone → digits for wa.me/<number> */
function toWaNumber(phone) {
  let d = String(phone || "").replace(/\D/g, "");
  if (!d) return null;
  if (d.startsWith("00")) d = d.slice(2);
  if (d.length === 10 && d.startsWith("3")) d = `39${d}`;
  return d;
}

function clientLabel(c) {
  return `${c.name || ""} ${c.surname || ""}`.trim() || c.email || c.phone || c.id;
}

export default function PublishingCenter({
  propertyId,
  property,
  agency,
  isListedOnImmobilCloud,
  onToggleImmobilCloud,
}) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [recipient, setRecipient] = useState(null);
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [pickerOpen, setPickerOpen] = useState(false);

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
  const shareBody = `${shareText}\n${publicUrl}`;

  const waGeneric = publicUrl
    ? `https://wa.me/?text=${encodeURIComponent(shareBody)}`
    : null;
  const fbHref = publicUrl
    ? `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(publicUrl)}`
    : null;
  const mailGeneric = publicUrl
    ? `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(`${shareText}\n\n${publicUrl}`)}`
    : null;
  const tgHref = publicUrl
    ? `https://t.me/share/url?url=${encodeURIComponent(publicUrl)}&text=${encodeURIComponent(shareText)}`
    : null;

  const recipientWa = useMemo(() => {
    if (!publicUrl || !recipient?.phone) return null;
    const num = toWaNumber(recipient.phone);
    if (!num) return null;
    return `https://wa.me/${num}?text=${encodeURIComponent(shareBody)}`;
  }, [publicUrl, recipient, shareBody]);

  const recipientMail = useMemo(() => {
    if (!publicUrl || !recipient?.email) return null;
    return `mailto:${encodeURIComponent(recipient.email)}?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(`${shareText}\n\n${publicUrl}`)}`;
  }, [publicUrl, recipient, title, shareText]);

  useEffect(() => {
    if (!pickerOpen) return undefined;
    const handle = setTimeout(async () => {
      try {
        const { data } = await api.get("/app/clients", {
          params: { q: q || undefined, page_size: 12 },
        });
        setResults(data.items || []);
      } catch {
        setResults([]);
      }
    }, 250);
    return () => clearTimeout(handle);
  }, [q, pickerOpen]);

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

  const canShare = !!propertyId && !!slug;

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

      {/* Share */}
      <div className="space-y-4">
        <div>
          <div className="text-xs uppercase tracking-widest text-stone-500">
            {t("properties.share_title")}
          </div>
          <p className="text-sm text-stone-600 mt-1" data-testid="share-who-hint">
            {t("properties.share_who_hint")}
          </p>
        </div>

        {!propertyId ? (
          <p
            data-testid="share-disabled-hint"
            className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2"
          >
            {t("properties.share_save_first")}
          </p>
        ) : !slug ? (
          <p className="text-xs text-stone-500">{t("properties.share_no_slug")}</p>
        ) : (
          <>
            {/* 1 · Cliente CRM */}
            <div data-testid="share-to-client" className="space-y-2">
              <p className="text-[11px] uppercase tracking-widest text-stone-500">
                {t("properties.share_to_client")}
              </p>

              {recipient && !pickerOpen ? (
                <div
                  data-testid="share-recipient-picked"
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border border-emerald-200 bg-emerald-50/60 rounded-md px-3 py-2.5"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-stone-900 truncate">
                      {clientLabel(recipient)}
                    </p>
                    <p className="text-xs text-stone-500 truncate">
                      {[recipient.phone, recipient.email].filter(Boolean).join(" · ") ||
                        t("properties.share_client_no_contact")}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 shrink-0">
                    {recipientWa ? (
                      <a
                        data-testid="share-client-whatsapp"
                        href={recipientWa}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center px-3 py-2 text-xs uppercase tracking-widest bg-[#25D366] text-white rounded hover:opacity-90"
                      >
                        WhatsApp
                      </a>
                    ) : (
                      <span
                        data-testid="share-client-whatsapp-disabled"
                        className="inline-flex items-center px-3 py-2 text-xs uppercase tracking-widest bg-stone-200 text-stone-500 rounded cursor-not-allowed"
                        title={t("properties.share_need_phone")}
                      >
                        WhatsApp
                      </span>
                    )}
                    {recipientMail ? (
                      <a
                        data-testid="share-client-email"
                        href={recipientMail}
                        className="inline-flex items-center px-3 py-2 text-xs uppercase tracking-widest bg-stone-900 text-white rounded hover:bg-stone-700"
                      >
                        Email
                      </a>
                    ) : (
                      <span
                        data-testid="share-client-email-disabled"
                        className="inline-flex items-center px-3 py-2 text-xs uppercase tracking-widest bg-stone-200 text-stone-500 rounded cursor-not-allowed"
                        title={t("properties.share_need_email")}
                      >
                        Email
                      </span>
                    )}
                    <button
                      type="button"
                      data-testid="share-recipient-change"
                      onClick={() => setPickerOpen(true)}
                      className="text-xs uppercase tracking-widest text-stone-600 hover:text-stone-900 underline"
                    >
                      {t("properties.share_change_client")}
                    </button>
                    <button
                      type="button"
                      data-testid="share-recipient-clear"
                      onClick={() => {
                        setRecipient(null);
                        setQ("");
                      }}
                      className="text-xs uppercase tracking-widest text-stone-500 hover:text-red-700"
                    >
                      {t("properties.share_remove_client")}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="relative">
                  <input
                    data-testid="share-client-search"
                    type="search"
                    value={q}
                    onChange={(e) => {
                      setQ(e.target.value);
                      setPickerOpen(true);
                    }}
                    onFocus={() => setPickerOpen(true)}
                    placeholder={t("properties.share_client_placeholder")}
                    className="form-input w-full"
                    disabled={!canShare}
                  />
                  {pickerOpen && (
                    <div
                      data-testid="share-client-results"
                      className="absolute z-20 mt-1 w-full max-h-56 overflow-auto bg-white border border-stone-200 rounded-md shadow-lg"
                    >
                      {results.length === 0 ? (
                        <p className="px-3 py-2 text-xs text-stone-500">
                          {t("properties.share_client_empty")}
                        </p>
                      ) : (
                        results.map((c) => (
                          <button
                            key={c.id}
                            type="button"
                            data-testid={`share-client-option-${c.id}`}
                            onClick={() => {
                              setRecipient(c);
                              setPickerOpen(false);
                              setQ("");
                            }}
                            className="w-full text-left px-3 py-2 text-sm hover:bg-stone-50 border-b border-stone-100 last:border-0"
                          >
                            <span className="font-medium text-stone-900">{clientLabel(c)}</span>
                            <span className="block text-xs text-stone-500 truncate">
                              {[c.client_type, c.phone, c.email].filter(Boolean).join(" · ")}
                            </span>
                          </button>
                        ))
                      )}
                      <button
                        type="button"
                        className="w-full text-left px-3 py-2 text-xs uppercase tracking-widest text-stone-500 hover:bg-stone-50"
                        onClick={() => setPickerOpen(false)}
                      >
                        {t("common.cancel")}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* 2 · Canali */}
            <div data-testid="share-channels" className="space-y-2">
              <p className="text-[11px] uppercase tracking-widest text-stone-500">
                {t("properties.share_via_channel")}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <a
                  data-testid="share-whatsapp"
                  href={waGeneric}
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
                  data-testid="share-telegram"
                  href={tgHref}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-2 text-xs uppercase tracking-widest bg-[#229ED9] text-white rounded hover:opacity-90"
                >
                  Telegram
                </a>
                <a
                  data-testid="share-email"
                  href={mailGeneric}
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
                  {copied ? t("properties.share_copied") : t("properties.share_copy_link")}
                </button>
              </div>
              <p
                data-testid="share-public-url"
                className="text-xs text-stone-500 truncate"
              >
                {publicUrl}
              </p>
            </div>
          </>
        )}

        {propertyId && !isListedOnImmobilCloud && (
          <p
            data-testid="immobilcloud-off-notice"
            className="text-xs text-stone-500"
          >
            {t("properties.share_immobilcloud_off")}
          </p>
        )}
      </div>
    </div>
  );
}
