/* OMNIA — Public Property Detail Page (M3.S4)
 *
 * Public landing page for a single property listed on ImmobilCloud.
 * Path: /it/cloud/property/:pid
 *
 * Sections:
 *  1. Hero with title, price, city, share buttons
 *  2. Photo gallery (cover + thumbnails)
 *  3. Key info (surface, rooms, bedrooms, bathrooms, energy class)
 *  4. Description + features list
 *  5. Mini map (Leaflet) if lat/lng available
 *  6. Agency card + contact form → POST /api/cloud/property/:pid/contact
 *  7. Schema.org RealEstateListing JSON-LD for SEO
 *
 * Lead is auto-created in the agency's CRM with source="ImmobilCloud".
 */
import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import "leaflet/dist/leaflet.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/cloud`;

function formatPrice(p) {
  if (!p) return "";
  const v = p.operation === "rent" ? p.rent_monthly : p.price;
  if (!v) return "";
  return p.operation === "rent"
    ? `€ ${Number(v).toLocaleString("it-IT")}/mese`
    : `€ ${Number(v).toLocaleString("it-IT")}`;
}

// Stima rapida rata: mutuo 25 anni, LTV 80%, TAN indicativo 3.6% (allineato al comparatore)
function estimateInstallment(price) {
  const loan = price * 0.8;
  const i = 0.036 / 12;
  const n = 300;
  return (loan * i) / (1 - Math.pow(1 + i, -n));
}

export default function PropertyDetailPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { pid } = useParams();
  const [prop, setProp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activePhoto, setActivePhoto] = useState(0);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/property/${pid}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? "not_found" : "fetch_error");
        return r.json();
      })
      .then((d) => setProp(d))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [pid]);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12" data-testid="property-detail-loading">
        <p className="text-stone-500 text-sm">{t("common.loading")}</p>
      </div>
    );
  }
  if (error === "not_found" || !prop) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-20 text-center" data-testid="property-detail-notfound">
        <h1 className="text-3xl font-light mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          {t("cloud.detail_not_found_title")}
        </h1>
        <p className="text-stone-600 mb-6">{t("cloud.detail_not_found_desc")}</p>
        <Link to={`/${lang}/cloud/search`} className="text-sm uppercase tracking-widest text-[#0B1E3F] hover:underline">
          ← {t("cloud.back_to_search")}
        </Link>
      </div>
    );
  }

  const photos = prop.photos || [];
  const cover = photos[activePhoto];
  const publicUrl = `${window.location.origin}/${lang}/cloud/property/${pid}`;

  const energy = prop.energy?.energy_class || "—";
  const features = Object.entries(prop.features || {}).filter(([_, v]) => v).map(([k]) => k);

  return (
    <div data-testid="property-detail-page" className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
      <SchemaOrgJsonLd prop={prop} publicUrl={publicUrl} />

      {/* Breadcrumb */}
      <nav className="text-xs text-stone-500 mb-4">
        <Link to={`/${lang}/cloud`} className="hover:text-[#0B1E3F]">{t("cloud.b2c_home_short")}</Link>
        <span className="mx-2">·</span>
        <Link to={`/${lang}/cloud/search`} className="hover:text-[#0B1E3F]">{t("cloud.search_label")}</Link>
        <span className="mx-2">·</span>
        <span className="text-stone-800">{prop.city}</span>
      </nav>

      {/* Hero: title + price */}
      <div className="flex flex-wrap items-end justify-between gap-3 mb-6">
        <div>
          <h1 data-testid="detail-title" className="text-3xl md:text-4xl font-light tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {prop.title || prop.property_type}
          </h1>
          <p className="text-stone-600 text-sm mt-1">
            {prop.city}{prop.zone ? ` · ${prop.zone}` : ""}{prop.property_type ? ` · ${prop.property_type}` : ""}
          </p>
          <ShareBar title={prop.title || prop.property_type} publicUrl={publicUrl} />
        </div>
        <div className="text-right">
          <div data-testid="detail-price" className="text-2xl md:text-3xl font-semibold text-[#0B1E3F]">
            {formatPrice(prop) || t("cloud.price_on_request")}
          </div>
          {prop.operation && (
            <span className="text-xs uppercase tracking-widest text-stone-500">
              {prop.operation === "rent" ? t("cloud.op_rent") : t("cloud.op_sale")}
            </span>
          )}
          {prop.operation !== "rent" && prop.price > 20000 && (
            <Link
              to={`/${lang}/cloud/mutui?price=${prop.price}`}
              data-testid="detail-mortgage-box"
              className="mt-2 flex items-center gap-2 justify-end text-sm text-stone-600 hover:text-[#0B1E3F] group"
              title={t("mutui.detail_box_note")}
            >
              <span>
                {t("mutui.detail_box_title")} {t("mutui.detail_box_from")}{" "}
                <strong className="text-[#0B1E3F]">
                  € {Math.round(estimateInstallment(prop.price)).toLocaleString("it-IT")}/{t("mutui.month")}
                </strong>
              </span>
              <span className="text-[11px] uppercase tracking-widest text-[#C19A6B] group-hover:underline">
                {t("mutui.detail_box_cta")} →
              </span>
            </Link>
          )}
          {/* Cap. 21 · Valutatore CTA speculare al box mutui */}
          <div className="mt-3 flex flex-col md:flex-row gap-2 justify-end items-end text-sm" data-testid="detail-valuator-box">
            <span className="text-stone-600">{t("valuator.detail_box_title", "Quanto vale questo immobile?")}</span>
            <Link
              to={`/${lang}/cloud/valutatore?tier=base&city=${encodeURIComponent(prop.city || "")}&property_type=${encodeURIComponent(prop.property_type || "appartamento")}&surface_sqm=${prop.surface_sqm || ""}`}
              data-testid="detail-valuator-base-cta"
              className="px-3 py-1.5 border border-stone-300 rounded text-stone-700 hover:bg-stone-100"
            >
              {t("valuator.detail_box_base_cta", "Stima gratuita")}
            </Link>
            <Link
              to={`/${lang}/cloud/valutatore?tier=uni&city=${encodeURIComponent(prop.city || "")}&property_type=${encodeURIComponent(prop.property_type || "appartamento")}&surface_sqm=${prop.surface_sqm || ""}`}
              data-testid="detail-valuator-uni-cta"
              className="px-3 py-1.5 bg-emerald-700 text-white rounded hover:bg-emerald-800"
            >
              {t("valuator.detail_box_uni_cta", "Report UNI · €2,99")}
            </Link>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* LEFT COLUMN — gallery + info + map */}
        <div className="lg:col-span-2 space-y-8">
          {/* Photo gallery */}
          {photos.length > 0 ? (
            <div data-testid="detail-gallery">
              <div className="aspect-video bg-stone-100 rounded-lg overflow-hidden mb-2">
                <img
                  src={`${BACKEND_URL}${cover.url}`}
                  alt={cover.caption || prop.title}
                  className="w-full h-full object-cover"
                />
              </div>
              {photos.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {photos.map((ph, i) => (
                    <button
                      key={i}
                      data-testid={`detail-thumb-${i}`}
                      onClick={() => setActivePhoto(i)}
                      className={`shrink-0 w-20 h-20 rounded overflow-hidden border-2 transition ${
                        i === activePhoto ? "border-[#0B1E3F]" : "border-transparent opacity-70 hover:opacity-100"
                      }`}
                    >
                      <img src={`${BACKEND_URL}${ph.url}`} alt="" className="w-full h-full object-cover" />
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="aspect-video bg-stone-100 rounded-lg flex items-center justify-center text-stone-400 text-sm">
              {t("cloud.no_photos")}
            </div>
          )}

          {/* Key info grid */}
          <div data-testid="detail-key-info" className="grid grid-cols-2 md:grid-cols-4 gap-4 bg-white border border-stone-200 rounded-lg p-5">
            <InfoCell label={t("cloud.info_surface")} value={prop.surface_sqm ? `${prop.surface_sqm} m²` : "—"} testid="info-surface" />
            <InfoCell label={t("cloud.info_rooms")} value={prop.rooms || "—"} testid="info-rooms" />
            <InfoCell label={t("cloud.info_bedrooms")} value={prop.bedrooms || "—"} testid="info-bedrooms" />
            <InfoCell label={t("cloud.info_bathrooms")} value={prop.bathrooms || "—"} testid="info-bathrooms" />
            <InfoCell label={t("cloud.info_floor")} value={prop.floor != null ? `${prop.floor}/${prop.total_floors || "—"}` : "—"} testid="info-floor" />
            <InfoCell label={t("cloud.info_year")} value={prop.year_built || "—"} testid="info-year" />
            <InfoCell label={t("cloud.info_energy")} value={energy} testid="info-energy" />
            <InfoCell label={t("cloud.info_ref")} value={prop.reference_code || "—"} testid="info-ref" />
          </div>

          {/* Description */}
          {prop.description && (
            <section data-testid="detail-description">
              <h2 className="text-xl font-light mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                {t("cloud.detail_description")}
              </h2>
              <p className="text-stone-700 text-sm leading-relaxed whitespace-pre-line">
                {prop.description}
              </p>
            </section>
          )}

          {/* Features */}
          {features.length > 0 && (
            <section data-testid="detail-features">
              <h2 className="text-xl font-light mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                {t("cloud.detail_features")}
              </h2>
              <ul className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm text-stone-700">
                {features.map((f) => (
                  <li key={f} className="flex items-center gap-2 before:content-['✓'] before:text-emerald-600 before:font-bold">
                    <span>{t(`features.${f}`, { defaultValue: f.replace(/_/g, " ") })}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Mini map */}
          {prop.lat && prop.lng && (
            <section data-testid="detail-map">
              <h2 className="text-xl font-light mb-3" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                {t("cloud.detail_location")}
              </h2>
              <div className="h-72 rounded-lg overflow-hidden border border-stone-200">
                <MapContainer center={[prop.lat, prop.lng]} zoom={14} scrollWheelZoom={false} className="h-full w-full">
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <Marker position={[prop.lat, prop.lng]} />
                </MapContainer>
              </div>
            </section>
          )}
        </div>

        {/* RIGHT COLUMN — agency card + contact form */}
        <aside className="lg:col-span-1 space-y-6 lg:sticky lg:top-6 lg:self-start">
          {prop.agency && <AgencyCard agency={prop.agency} />}
          <ContactForm pid={pid} propertyTitle={prop.title} />
        </aside>
      </div>
    </div>
  );
}

/* Share bar: WhatsApp, Facebook, X, email, copy link (+ native share on mobile) */
function ShareBar({ title, publicUrl }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const shareText = t("cloud.share_text", { title });
  const enc = encodeURIComponent;

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(publicUrl);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = publicUrl;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const nativeShare = () => navigator.share({ title, text: shareText, url: publicUrl }).catch(() => {});

  const btnCls = "w-8 h-8 rounded-full border border-stone-200 bg-white flex items-center justify-center text-stone-600 hover:text-white transition";

  return (
    <div data-testid="detail-share-bar" className="flex items-center gap-2 mt-3">
      <span className="text-[11px] uppercase tracking-widest text-stone-500 mr-1">{t("cloud.share_label")}</span>
      <a
        data-testid="share-whatsapp" title={t("cloud.share_whatsapp")} aria-label={t("cloud.share_whatsapp")}
        href={`https://wa.me/?text=${enc(`${shareText}\n${publicUrl}`)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-[#25D366] hover:border-[#25D366]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
      </a>
      <a
        data-testid="share-facebook" title={t("cloud.share_facebook")} aria-label={t("cloud.share_facebook")}
        href={`https://www.facebook.com/sharer/sharer.php?u=${enc(publicUrl)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-[#1877F2] hover:border-[#1877F2]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="currentColor"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
      </a>
      <a
        data-testid="share-x" title={t("cloud.share_x")} aria-label={t("cloud.share_x")}
        href={`https://twitter.com/intent/tweet?text=${enc(shareText)}&url=${enc(publicUrl)}`}
        target="_blank" rel="noopener noreferrer"
        className={`${btnCls} hover:bg-black hover:border-black`}
      >
        <svg viewBox="0 0 24 24" className="w-3.5 h-3.5" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      </a>
      <a
        data-testid="share-email" title={t("cloud.share_email")} aria-label={t("cloud.share_email")}
        href={`mailto:?subject=${enc(title || "")}&body=${enc(`${shareText}\n\n${publicUrl}`)}`}
        className={`${btnCls} hover:bg-[#0B1E3F] hover:border-[#0B1E3F]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 7L2 7"/></svg>
      </a>
      <button
        data-testid="share-copy" type="button" title={t("cloud.share_copy")} aria-label={t("cloud.share_copy")}
        onClick={copyLink}
        className={`${btnCls} hover:bg-[#C19A6B] hover:border-[#C19A6B]`}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
      </button>
      {typeof navigator !== "undefined" && navigator.share && (
        <button
          data-testid="share-native" type="button" title={t("cloud.share_native")} aria-label={t("cloud.share_native")}
          onClick={nativeShare}
          className={`${btnCls} hover:bg-stone-700 hover:border-stone-700`}
        >
          <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.59 13.51 6.83 3.98m-.01-10.98-6.82 3.98"/></svg>
        </button>
      )}
      {copied && (
        <span data-testid="share-copied-toast" className="text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-2 py-0.5">
          {t("cloud.share_copied")}
        </span>
      )}
    </div>
  );
}

function InfoCell({ label, value, testid }) {
  return (
    <div data-testid={testid}>
      <div className="text-[11px] uppercase tracking-widest text-stone-500">{label}</div>
      <div className="text-sm font-medium text-stone-900 mt-0.5">{value}</div>
    </div>
  );
}

function AgencyCard({ agency }) {
  const { t } = useTranslation();
  return (
    <div data-testid="detail-agency-card" className="bg-white border border-stone-200 rounded-lg p-5">
      <div className="text-xs uppercase tracking-widest text-stone-500 mb-2">{t("cloud.detail_agency_label")}</div>
      <div className="flex items-center gap-3 mb-3">
        {agency.logo_url ? (
          <img src={agency.logo_url} alt={agency.display_name} className="w-12 h-12 rounded object-contain bg-stone-50 border border-stone-200" />
        ) : (
          <div className="w-12 h-12 rounded bg-[#0B1E3F] text-white flex items-center justify-center text-lg font-light">
            {agency.display_name?.[0] || "A"}
          </div>
        )}
        <div className="min-w-0">
          <div className="text-sm font-medium text-stone-900 truncate">{agency.display_name}</div>
          {agency.city && <div className="text-xs text-stone-500 truncate">{agency.city}</div>}
        </div>
      </div>
      <div className="space-y-1 text-xs text-stone-600">
        {agency.phone && <div data-testid="agency-phone">📞 <a href={`tel:${agency.phone}`} className="hover:text-[#0B1E3F]">{agency.phone}</a></div>}
        {agency.email && <div data-testid="agency-email">✉ <a href={`mailto:${agency.email}`} className="hover:text-[#0B1E3F]">{agency.email}</a></div>}
      </div>
    </div>
  );
}

function ContactForm({ pid, propertyTitle }) {
  const { t } = useTranslation();
  const [form, setForm] = useState({
    name: "", surname: "", email: "", phone: "",
    message: t("cloud.contact_default_message", { title: propertyTitle || "" }),
    visit_requested: false,
    gdpr_consent: false,
  });
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!form.gdpr_consent) {
      setError(t("cloud.contact_err_gdpr"));
      return;
    }
    setBusy(true);
    setError("");
    try {
      const r = await fetch(`${API}/property/${pid}/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const d = await r.json();
      if (!r.ok) {
        setError(d.detail || t("cloud.contact_err_generic"));
      } else {
        setDone(true);
      }
    } catch {
      setError(t("cloud.contact_err_generic"));
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div data-testid="contact-done" className="bg-emerald-50 border border-emerald-200 rounded-lg p-5 text-center">
        <div className="text-3xl mb-2">✓</div>
        <h3 className="text-base font-medium text-emerald-900 mb-1">{t("cloud.contact_done_title")}</h3>
        <p className="text-xs text-emerald-700">{t("cloud.contact_done_desc")}</p>
      </div>
    );
  }

  return (
    <form data-testid="contact-form" onSubmit={onSubmit} className="bg-white border border-stone-200 rounded-lg p-5 space-y-3">
      <h3 className="text-sm font-medium text-stone-900 mb-1">{t("cloud.contact_title")}</h3>
      <p className="text-xs text-stone-500 -mt-2 mb-2">{t("cloud.contact_desc")}</p>

      <Input testid="contact-name" placeholder={t("cloud.contact_name")} required
        value={form.name} onChange={(v) => setForm({ ...form, name: v })} />
      <Input testid="contact-email" type="email" placeholder={t("cloud.contact_email")} required
        value={form.email} onChange={(v) => setForm({ ...form, email: v })} />
      <Input testid="contact-phone" placeholder={t("cloud.contact_phone")}
        value={form.phone} onChange={(v) => setForm({ ...form, phone: v })} />
      <textarea
        data-testid="contact-message" rows={4} required minLength={10}
        placeholder={t("cloud.contact_message")}
        value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })}
        className="w-full px-3 py-2 border border-stone-300 rounded text-sm focus:outline-none focus:border-[#0B1E3F]"
      />

      <label className="flex items-center gap-2 text-xs text-stone-700 cursor-pointer">
        <input type="checkbox" data-testid="contact-visit"
          checked={form.visit_requested}
          onChange={(e) => setForm({ ...form, visit_requested: e.target.checked })} />
        {t("cloud.contact_visit")}
      </label>

      <label className="flex items-start gap-2 text-xs text-stone-600 cursor-pointer">
        <input type="checkbox" data-testid="contact-gdpr" required
          checked={form.gdpr_consent}
          onChange={(e) => setForm({ ...form, gdpr_consent: e.target.checked })} />
        <span>{t("cloud.contact_gdpr")}</span>
      </label>

      {error && <p data-testid="contact-error" className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2">{error}</p>}

      <button
        type="submit"
        data-testid="contact-submit"
        disabled={busy}
        className="w-full bg-[#0B1E3F] text-white py-2.5 rounded text-sm uppercase tracking-widest font-medium hover:bg-[#C19A6B] transition disabled:opacity-50"
      >
        {busy ? t("cloud.contact_submitting") : t("cloud.contact_submit")}
      </button>
    </form>
  );
}

function Input({ testid, value, onChange, ...rest }) {
  return (
    <input
      data-testid={testid}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-3 py-2 border border-stone-300 rounded text-sm focus:outline-none focus:border-[#0B1E3F]"
      {...rest}
    />
  );
}

/* Schema.org RealEstateListing JSON-LD for SEO + sharing rich previews */
function SchemaOrgJsonLd({ prop, publicUrl }) {
  const data = {
    "@context": "https://schema.org",
    "@type": "RealEstateListing",
    name: prop.title,
    description: prop.description,
    url: publicUrl,
    address: {
      "@type": "PostalAddress",
      addressLocality: prop.city,
      addressRegion: prop.province,
      postalCode: prop.postal_code,
      addressCountry: "IT",
    },
    ...(prop.lat && prop.lng ? {
      geo: { "@type": "GeoCoordinates", latitude: prop.lat, longitude: prop.lng }
    } : {}),
    ...(prop.price ? {
      offers: { "@type": "Offer", price: prop.price, priceCurrency: "EUR" }
    } : {}),
    ...(prop.surface_sqm ? {
      floorSize: { "@type": "QuantitativeValue", value: prop.surface_sqm, unitCode: "MTK" }
    } : {}),
  };
  return (
    <script
      type="application/ld+json"
      data-testid="schema-jsonld"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}
