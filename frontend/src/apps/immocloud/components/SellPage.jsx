/* OMNIA — B2C Sell Page (M3.S5 v2)
 *
 * Authenticated B2C users (account_type='b2c') can create/edit/submit one free
 * private property listing. If not logged in, redirects to registration with
 * intent=sell prefilled. Shows current listing status and any rejection notes.
 */
import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth, formatApiErrorDetail } from "../../../shared/lib/auth";
import AlImproveButton from "../../../shared/components/AlImproveButton";

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

  // Redirect if not logged in or not a B2C user
  useEffect(() => {
    if (user === null) return; // still loading
    if (!user || user.account_type !== "b2c") {
      nav(`/${lang}/cloud/register?intent=sell`, { replace: true });
    }
  }, [user, lang, nav]);

  // Load listings
  useEffect(() => {
    if (user && user.account_type === "b2c") {
      api.get("/cloud/me/properties")
        .then((r) => setListings(r.data.items || []))
        .catch(() => {});
    }
  }, [user]);

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
                  <StatusBadge status={l.moderation_status} listingStatus={l.status} notes={l.moderation_notes} />
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
