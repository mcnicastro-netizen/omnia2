/* OMNIA — B2C Sell Page (M3.S5 v2)
 *
 * Authenticated B2C users (account_type='b2c') can create/edit/submit one free
 * private property listing. If not logged in, redirects to registration with
 * intent=sell prefilled. Shows current listing status and any rejection notes.
 *
 * Media: up to 30 photos + optional floor plan (planimetria) via B2C upload-tmp.
 */
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth, formatApiErrorDetail } from "../../../shared/lib/auth";
import AlImproveButton from "../../../shared/components/AlImproveButton";
import PhotoUploader from "../../immoweb/components/PhotoUploader";

const B2C_MEDIA_UPLOAD = "/cloud/me/properties/media/upload-tmp";
const B2C_MAX_PHOTOS = 30;

const empty = {
  title: "",
  description: "",
  property_type: "appartamento",
  operation: "sale",
  city: "",
  address: "",
  postal_code: "",
  price: "",
  rent_monthly: "",
  surface_sqm: "",
  rooms: "",
  bedrooms: "",
  bathrooms: "",
  photos: [],
  floor_plan_url: "",
};

const PROPERTY_TYPES = [
  "appartamento", "villa", "loft", "attico", "monolocale",
  "rustico_casale", "ufficio", "negozio", "magazzino",
  "garage_box", "terreno_agricolo", "terreno_edificabile", "altro",
];

export default function SellPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const { user } = useAuth();
  const [listings, setListings] = useState([]);
  const [editing, setEditing] = useState(null); // listing object or null
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [boostCatalog, setBoostCatalog] = useState([]);
  const [boostBusy, setBoostBusy] = useState(null); // product_key being purchased

  // Redirect if not logged in or not a B2C user
  useEffect(() => {
    if (user === null) return; // still loading
    if (!user || user.account_type !== "b2c") {
      nav(`/${lang}/cloud/register?intent=sell`, { replace: true });
    }
  }, [user, lang, nav]);

  // Load listings + boost catalog
  useEffect(() => {
    if (user && user.account_type === "b2c") {
      api.get("/cloud/me/properties")
        .then((r) => setListings(r.data.items || []))
        .catch(() => {});
      api.get("/billing/b2c/boosts")
        .then((r) => setBoostCatalog(r.data.products || []))
        .catch(() => {});
    }
  }, [user]);

  const buyBoost = async (listingId, productKey) => {
    setBoostBusy(productKey);
    setError("");
    try {
      const origin = window.location.origin;
      const { data } = await api.post("/billing/b2c/checkout", {
        product_key: productKey,
        listing_id: listingId,
        success_url: `${origin}/${lang}/cloud/account/sell?boost=ok`,
        cancel_url: `${origin}/${lang}/cloud/account/sell?boost=cancel`,
      });
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
        return;
      }
      setError(t("cloud.sell.boost_checkout_error"));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail) || t("cloud.sell.boost_checkout_error"));
    } finally {
      setBoostBusy(null);
    }
  };

  const boostActive = (l) => {
    if (!l?.boost_tier || !l?.boost_until) return null;
    const until = Date.parse(l.boost_until);
    if (Number.isNaN(until) || until <= Date.now()) return null;
    return l.boost_tier;
  };

  const startNew = () => {
    setEditing(null);
    setForm(empty);
    setShowForm(true);
    setError("");
  };

  const startEdit = (listing) => {
    setEditing(listing);
    setForm({
      title: listing.title || "",
      description: listing.description || "",
      property_type: listing.property_type || "appartamento",
      operation: listing.operation || "sale",
      city: listing.city || "",
      address: listing.address || "",
      postal_code: listing.postal_code || "",
      price: listing.price || "",
      rent_monthly: listing.rent_monthly || "",
      surface_sqm: listing.surface_sqm || "",
      rooms: listing.rooms || "",
      bedrooms: listing.bedrooms || "",
      bathrooms: listing.bathrooms || "",
      photos: Array.isArray(listing.photos) ? listing.photos : [],
      floor_plan_url: listing.floor_plan_url || "",
    });
    setShowForm(true);
    setError("");
  };

  const save = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    try {
      const payload = { ...form };
      ["price", "rent_monthly", "surface_sqm", "rooms", "bedrooms", "bathrooms"].forEach((k) => {
        if (payload[k] === "" || payload[k] == null) delete payload[k];
        else payload[k] = Number(payload[k]);
      });
      if (!payload.floor_plan_url) payload.floor_plan_url = null;
      if (!Array.isArray(payload.photos)) payload.photos = [];
      if (payload.photos.length > B2C_MAX_PHOTOS) {
        setError(t("cloud.sell.err_photos_limit"));
        setBusy(false);
        return;
      }
      if (editing) {
        await api.patch(`/cloud/me/properties/${editing.id}`, payload);
      } else {
        await api.post("/cloud/me/properties", payload);
      }
      setShowForm(false);
      setEditing(null);
      const r = await api.get("/cloud/me/properties");
      setListings(r.data.items || []);
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    } finally { setBusy(false); }
  };

  const submitForReview = async (pid) => {
    setBusy(true); setError("");
    try {
      await api.post(`/cloud/me/properties/${pid}/submit`);
      const r = await api.get("/cloud/me/properties");
      setListings(r.data.items || []);
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    } finally { setBusy(false); }
  };

  const deleteListing = async (pid) => {
    if (!window.confirm(t("cloud.sell.confirm_delete"))) return;
    setBusy(true); setError("");
    try {
      await api.delete(`/cloud/me/properties/${pid}`);
      setListings(listings.filter((l) => l.id !== pid));
    } catch (e) {
      setError(formatApiErrorDetail(e?.response?.data?.detail));
    } finally { setBusy(false); }
  };

  if (user === null) {
    return <div className="max-w-3xl mx-auto p-6 text-stone-500 text-sm">{t("common.loading")}</div>;
  }
  if (!user || user.account_type !== "b2c") {
    return null; // redirecting
  }

  const hasActive = listings.some((l) => l.status !== "withdrawn" && l.moderation_status !== "rejected");

  return (
    <div data-testid="sell-page" className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <header className="mb-8">
        <h1 className="text-3xl md:text-4xl font-light tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          {t("cloud.sell.title")}
        </h1>
        <p className="text-stone-500 text-sm mt-1">{t("cloud.sell.subtitle")}</p>
      </header>

      {error && (
        <div data-testid="sell-error" className="mb-4 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded px-3 py-2">
          {error}
        </div>
      )}

      {/* Existing listings */}
      {listings.length > 0 && (
        <section data-testid="sell-listings" className="mb-8 space-y-3">
          {listings.map((l) => (
            <article
              key={l.id}
              data-testid={`listing-${l.id}`}
              className="bg-white border border-stone-200 rounded-lg p-5"
            >
              <div className="flex items-start justify-between gap-4 flex-wrap">
                <div className="min-w-0 flex-1">
                  <h2 className="text-base font-medium text-stone-900">{l.title || t("cloud.sell.untitled")}</h2>
                  <p className="text-xs text-stone-600 mt-0.5">
                    {l.city} · {l.property_type}
                    {l.operation === "rent" && l.rent_monthly ? ` · € ${l.rent_monthly.toLocaleString("it-IT")}/mese` :
                     l.price ? ` · € ${l.price.toLocaleString("it-IT")}` : ""}
                  </p>
                  {(l.photos?.length > 0 || l.floor_plan_url) && (
                    <p className="text-[11px] text-stone-500 mt-1" data-testid={`listing-media-${l.id}`}>
                      {l.photos?.length > 0 ? `${l.photos.length} ${t("cloud.sell.photos_count")}` : null}
                      {l.photos?.length > 0 && l.floor_plan_url ? " · " : null}
                      {l.floor_plan_url ? t("cloud.sell.has_floor_plan") : null}
                    </p>
                  )}
                  <StatusBadge status={l.moderation_status} listingStatus={l.status} notes={l.moderation_notes} />
                  {boostActive(l) && (
                    <p className="text-[11px] text-emerald-800 mt-1" data-testid={`boost-active-${l.id}`}>
                      {t("cloud.sell.boost_active", {
                        tier: String(boostActive(l)).toUpperCase(),
                        until: new Date(l.boost_until).toLocaleDateString(lang),
                      })}
                    </p>
                  )}
                </div>
                <div className="flex gap-2 flex-wrap">
                  <button
                    data-testid={`edit-${l.id}`}
                    onClick={() => startEdit(l)}
                    className="px-3 py-1.5 text-[11px] uppercase tracking-widest border border-stone-300 rounded hover:bg-stone-50"
                  >
                    {t("common.edit")}
                  </button>
                  {l.moderation_status !== "pending" && (
                    <button
                      data-testid={`submit-${l.id}`}
                      onClick={() => submitForReview(l.id)}
                      disabled={busy}
                      className="px-3 py-1.5 text-[11px] uppercase tracking-widest bg-[#0B1E3F] text-white rounded hover:bg-[#C19A6B] disabled:opacity-50"
                    >
                      {l.moderation_status === "rejected" ? t("cloud.sell.resubmit") : t("cloud.sell.submit_review")}
                    </button>
                  )}
                  <button
                    data-testid={`delete-${l.id}`}
                    onClick={() => deleteListing(l.id)}
                    className="px-3 py-1.5 text-[11px] uppercase tracking-widest text-rose-700 border border-rose-200 rounded hover:bg-rose-50"
                  >
                    {t("common.delete")}
                  </button>
                </div>
              </div>
              {boostCatalog.length > 0 && (
                <div className="mt-4 pt-4 border-t border-stone-100" data-testid={`boost-panel-${l.id}`}>
                  <p className="text-[11px] uppercase tracking-widest text-stone-500 mb-2">
                    {t("cloud.sell.boost_title")}
                  </p>
                  <p className="text-xs text-stone-600 mb-3">{t("cloud.sell.boost_subtitle")}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                    {boostCatalog.map((p) => (
                      <button
                        key={p.key}
                        type="button"
                        data-testid={`boost-buy-${p.key}`}
                        disabled={!!boostBusy}
                        onClick={() => buyBoost(l.id, p.key)}
                        className="text-left px-3 py-2.5 border border-stone-200 rounded hover:border-[#0B1E3F] hover:bg-stone-50 disabled:opacity-50 transition"
                      >
                        <div className="text-xs font-medium text-stone-900">{p.label_it}</div>
                        <div className="text-sm text-[#0B1E3F] mt-0.5">
                          € {Number(p.price_eur).toLocaleString("it-IT", { minimumFractionDigits: 2 })}
                        </div>
                        <div className="text-[10px] uppercase tracking-widest text-stone-500 mt-1">
                          {boostBusy === p.key ? t("common.saving") : t("cloud.sell.boost_cta")}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </article>
          ))}
        </section>
      )}

      {/* CTA new listing */}
      {!showForm && !hasActive && (
        <button
          data-testid="sell-new-btn"
          onClick={startNew}
          className="w-full md:w-auto px-6 py-3 bg-[#0B1E3F] text-white text-sm uppercase tracking-widest rounded hover:bg-[#C19A6B] transition"
        >
          + {t("cloud.sell.create_listing")}
        </button>
      )}
      {!showForm && hasActive && (
        <p data-testid="sell-limit-notice" className="text-xs text-stone-500 italic">
          {t("cloud.sell.free_limit_notice")}
        </p>
      )}

      {/* Form */}
      {showForm && (
        <form data-testid="sell-form" onSubmit={save} className="bg-white border border-stone-200 rounded-lg p-6 space-y-4">
          <h2 className="text-xl font-light mb-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            {editing ? t("cloud.sell.form_edit_title") : t("cloud.sell.form_new_title")}
          </h2>

          <Field label={t("cloud.sell.f_title")} required>
            <div className="flex items-start gap-2">
              <input data-testid="sell-f-title" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                required minLength={3} maxLength={200} className={`${inputCls} flex-1`} />
              <AlImproveButton
                field="title"
                value={form.title}
                propertyData={form}
                onApply={(text) => setForm({ ...form, title: text })}
                testId="sell-al-improve-title"
              />
            </div>
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label={t("cloud.sell.f_type")}>
              <select data-testid="sell-f-type" value={form.property_type} onChange={(e) => setForm({ ...form, property_type: e.target.value })} className={inputCls}>
                {PROPERTY_TYPES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </Field>
            <Field label={t("cloud.sell.f_operation")}>
              <select data-testid="sell-f-operation" value={form.operation} onChange={(e) => setForm({ ...form, operation: e.target.value })} className={inputCls}>
                <option value="sale">{t("cloud.sell.op_sale")}</option>
                <option value="rent">{t("cloud.sell.op_rent")}</option>
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label={t("cloud.sell.f_city")} required>
              <input data-testid="sell-f-city" value={form.city} required onChange={(e) => setForm({ ...form, city: e.target.value })} className={inputCls} />
            </Field>
            <Field label={t("cloud.sell.f_postal")}>
              <input data-testid="sell-f-postal" value={form.postal_code} onChange={(e) => setForm({ ...form, postal_code: e.target.value })} className={inputCls} />
            </Field>
          </div>

          <Field label={t("cloud.sell.f_address")}>
            <input data-testid="sell-f-address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className={inputCls} />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            {form.operation === "sale" ? (
              <Field label={t("cloud.sell.f_price")}>
                <input data-testid="sell-f-price" type="number" min="0" value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} className={inputCls} />
              </Field>
            ) : (
              <Field label={t("cloud.sell.f_rent")}>
                <input data-testid="sell-f-rent" type="number" min="0" value={form.rent_monthly} onChange={(e) => setForm({ ...form, rent_monthly: e.target.value })} className={inputCls} />
              </Field>
            )}
            <Field label={t("cloud.sell.f_surface")}>
              <input data-testid="sell-f-surface" type="number" min="0" value={form.surface_sqm} onChange={(e) => setForm({ ...form, surface_sqm: e.target.value })} className={inputCls} />
            </Field>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Field label={t("cloud.sell.f_rooms")}>
              <input data-testid="sell-f-rooms" type="number" min="0" value={form.rooms} onChange={(e) => setForm({ ...form, rooms: e.target.value })} className={inputCls} />
            </Field>
            <Field label={t("cloud.sell.f_bedrooms")}>
              <input data-testid="sell-f-bedrooms" type="number" min="0" value={form.bedrooms} onChange={(e) => setForm({ ...form, bedrooms: e.target.value })} className={inputCls} />
            </Field>
            <Field label={t("cloud.sell.f_bathrooms")}>
              <input data-testid="sell-f-bathrooms" type="number" min="0" value={form.bathrooms} onChange={(e) => setForm({ ...form, bathrooms: e.target.value })} className={inputCls} />
            </Field>
          </div>

          <Field label={t("cloud.sell.f_description")}>
            <div className="space-y-2">
              <textarea data-testid="sell-f-description" rows={4} maxLength={10000}
                value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
                className={inputCls} />
              <div className="flex justify-end">
                <AlImproveButton
                  field="description"
                  value={form.description}
                  propertyData={form}
                  onApply={(text) => setForm({ ...form, description: text })}
                  testId="sell-al-improve-description"
                />
              </div>
            </div>
          </Field>

          <Field label={t("cloud.sell.f_photos")}>
            <p className="text-xs text-stone-500 mb-2">{t("cloud.sell.f_photos_hint")}</p>
            <PhotoUploader
              photos={form.photos || []}
              onChange={(photos) => setForm({ ...form, photos })}
              max={B2C_MAX_PHOTOS}
              uploadUrl={B2C_MEDIA_UPLOAD}
              uploadExtraFields={{ kind: "photo" }}
            />
          </Field>

          <Field label={t("cloud.sell.f_floor_plan")}>
            <p className="text-xs text-stone-500 mb-2">{t("cloud.sell.f_floor_plan_hint")}</p>
            <FloorPlanUploader
              url={form.floor_plan_url}
              onChange={(url) => setForm({ ...form, floor_plan_url: url || "" })}
            />
          </Field>

          <div className="flex gap-3 pt-2">
            <button type="submit" disabled={busy} data-testid="sell-save-btn"
              className="px-6 py-2.5 bg-[#0B1E3F] text-white text-sm uppercase tracking-widest rounded hover:bg-[#C19A6B] transition disabled:opacity-50">
              {busy ? t("common.saving") : t("common.save")}
            </button>
            <button type="button" onClick={() => { setShowForm(false); setEditing(null); }}
              className="px-6 py-2.5 border border-stone-300 text-sm uppercase tracking-widest rounded hover:bg-stone-50">
              {t("common.cancel")}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

const inputCls = "w-full px-3 py-2 border border-stone-300 rounded text-sm focus:outline-none focus:border-[#0B1E3F]";

function Field({ label, children, required }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">
        {label}{required && " *"}
      </label>
      {children}
    </div>
  );
}

function FloorPlanUploader({ url, onChange }) {
  const { t } = useTranslation();
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [err, setErr] = useState("");

  const resizeToBlob = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const maxW = 2000;
        let { width, height } = img;
        if (width > maxW) {
          height = Math.round((height * maxW) / width);
          width = maxW;
        }
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        canvas.getContext("2d").drawImage(img, 0, 0, width, height);
        canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))), "image/jpeg", 0.88);
      };
      img.onerror = reject;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

  const handleFile = async (file) => {
    if (!file || !file.type.startsWith("image/")) return;
    setUploading(true);
    setErr("");
    try {
      const blob = await resizeToBlob(file);
      const fd = new FormData();
      fd.append("file", blob, (file.name || "planimetria").replace(/\.[^.]+$/, "") + ".jpg");
      fd.append("kind", "floor_plan");
      const { data } = await api.post(B2C_MEDIA_UPLOAD, fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 45000,
      });
      onChange(data.url);
    } catch (e) {
      setErr(formatApiErrorDetail(e?.response?.data?.detail) || t("cloud.sell.err_floor_plan_upload"));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div data-testid="floor-plan-uploader" className="space-y-3">
      {!url ? (
        <div
          role="button"
          tabIndex={0}
          data-testid="floor-plan-dropzone"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); inputRef.current?.click(); } }}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0]);
          }}
          className="border-2 border-dashed border-stone-300 rounded-lg p-5 text-center cursor-pointer hover:border-stone-500 hover:bg-stone-50 transition"
        >
          <p className="text-sm text-stone-700 font-medium">
            {uploading ? t("common.saving") : t("cloud.sell.floor_plan_drop")}
          </p>
          <p className="text-xs text-stone-500 mt-1">{t("cloud.sell.floor_plan_formats")}</p>
        </div>
      ) : (
        <div className="relative border border-stone-200 rounded-lg overflow-hidden bg-stone-50 max-w-md">
          <img
            src={url}
            alt={t("cloud.sell.f_floor_plan")}
            data-testid="floor-plan-preview"
            className="w-full max-h-64 object-contain bg-white"
          />
          <button
            type="button"
            data-testid="floor-plan-remove"
            onClick={() => onChange("")}
            className="absolute top-2 right-2 bg-red-600 text-white text-xs px-2 py-1 rounded hover:bg-red-700"
          >
            {t("common.delete")}
          </button>
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        data-testid="floor-plan-file-input"
        className="hidden"
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
      {err && <p className="text-xs text-rose-700" data-testid="floor-plan-error">{err}</p>}
    </div>
  );
}

function StatusBadge({ status, listingStatus, notes }) {
  const { t } = useTranslation();
  const config = {
    pending: { cls: "bg-amber-100 text-amber-800 border-amber-200", label: t("cloud.sell.status_pending") },
    approved: { cls: "bg-emerald-100 text-emerald-800 border-emerald-200", label: t("cloud.sell.status_approved") },
    rejected: { cls: "bg-rose-100 text-rose-800 border-rose-200", label: t("cloud.sell.status_rejected") },
  }[status] || { cls: "bg-stone-100 text-stone-800 border-stone-200", label: status };
  return (
    <div className="mt-2 flex items-center gap-2 flex-wrap">
      <span data-testid={`status-${status}`}
        className={`inline-block text-[10px] uppercase tracking-widest px-2 py-1 rounded border ${config.cls}`}>
        {config.label}
      </span>
      {listingStatus === "active" && status === "approved" && (
        <span className="text-[10px] text-emerald-700">✓ {t("cloud.sell.status_live")}</span>
      )}
      {status === "rejected" && notes && (
        <span data-testid="rejection-notes" className="text-[11px] text-rose-700 italic">&ldquo;{notes}&rdquo;</span>
      )}
    </div>
  );
}
