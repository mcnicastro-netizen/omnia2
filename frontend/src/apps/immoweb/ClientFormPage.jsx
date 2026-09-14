import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams, Link } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";

const CLIENT_TYPES = ["buyer", "seller", "tenant", "landlord", "investor"];
const CLIENT_STATUSES = ["new", "contacted", "qualified", "negotiating", "closed_won", "closed_lost", "archived"];

const OPERATIONS = ["", "sale", "rent", "rent_to_buy", "auction"];
const PROPERTY_TYPES = [
  "appartamento", "villa", "villetta_a_schiera", "loft", "attico", "monolocale",
  "rustico_casale", "ufficio", "negozio", "magazzino", "capannone", "garage_box",
  "terreno_agricolo", "terreno_edificabile", "palazzo_stabile", "altro",
];
const CONDITIONS = ["nuovo", "buone", "da_ristrutturare", "ristrutturato"];
const FLOORS = ["terra", "intermedi", "ultimo"];
const ENERGY_CLASSES = ["", "A", "B", "C", "D", "E", "F", "G"];
const FEATURES = [
  "balcone", "terrazza", "giardino", "piscina", "ascensore",
  "aria_condizionata", "riscaldamento_autonomo", "cantina", "soffitta",
  "posto_auto", "box_auto", "portineria", "videocitofono", "allarme",
  "porta_blindata", "cucina_abitabile", "camino", "parquet",
  "vista_panoramica", "luminoso", "arredato", "pannelli_solari",
  "cancello_elettrico", "impianto_domotico", "accesso_disabili",
];

const emptyPrefs = {
  operation: "",
  property_types: [],
  cities: [],
  zones: [],
  price_min: "",
  price_max: "",
  surface_min: "",
  surface_max: "",
  rooms_min: "",
  rooms_max: "",
  bedrooms_min: "",
  bathrooms_min: "",
  conditions: [],
  floor_preferences: [],
  must_have_features: [],
  energy_min_class: "",
  needs_photos: false,
  needs_virtual_tour: false,
  notes: "",
};

const empty = {
  name: "",
  surname: "",
  email: "",
  phone: "",
  whatsapp: "",
  fiscal_code: "",
  client_type: "buyer",
  status: "new",
  source: "",
  gdpr_consent: false,
  notes: "",
  preferences: emptyPrefs,
};

// helpers for comma-separated input ↔ array
const arrToText = (a) => (a || []).join(", ");
const textToArr = (s) => (s || "").split(",").map((x) => x.trim()).filter(Boolean);

export default function ClientFormPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { id } = useParams();
  const nav = useNavigate();
  const isEdit = !!id;
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(isEdit);
  const [carriedProperties, setCarriedProperties] = useState([]);
  const isSellerType = form.client_type === "seller" || form.client_type === "landlord";

  useEffect(() => {
    if (!isEdit || !id) return;
    if (!isSellerType) { setCarriedProperties([]); return; }
    api.get(`/app/clients/${id}/properties`)
      .then((r) => setCarriedProperties(r.data.items || []))
      .catch(() => setCarriedProperties([]));
  }, [id, isEdit, isSellerType]);

  useEffect(() => {
    if (!isEdit) return;
    setLoading(true);
    api.get(`/app/clients/${id}`).then((r) => {
      const d = r.data;
      const incomingPrefs = d.preferences || {};
      // Coerce null → "" for all string/number fields used as controlled inputs.
      const safePrefs = { ...emptyPrefs, ...incomingPrefs };
      Object.keys(emptyPrefs).forEach((k) => {
        const defVal = emptyPrefs[k];
        if (safePrefs[k] == null) {
          // arrays default to []; booleans to false; strings/numbers to ""
          safePrefs[k] = Array.isArray(defVal) ? [] : typeof defVal === "boolean" ? false : "";
        }
      });
      // Same for top-level scalar fields
      const safeTop = { ...empty, ...d };
      Object.keys(empty).forEach((k) => {
        if (k === "preferences") return;
        const defVal = empty[k];
        if (safeTop[k] == null) {
          safeTop[k] = Array.isArray(defVal) ? [] : typeof defVal === "boolean" ? false : "";
        }
      });
      setForm({ ...safeTop, preferences: safePrefs });
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const upd = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const updPref = (key, value) => setForm((f) => ({ ...f, preferences: { ...f.preferences, [key]: value } }));

  const togglePrefArr = (key, val) =>
    setForm((f) => {
      const cur = f.preferences[key] || [];
      const next = cur.includes(val) ? cur.filter((x) => x !== val) : [...cur, val];
      return { ...f, preferences: { ...f.preferences, [key]: next } };
    });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      // build payload
      const p = form.preferences;
      const numKeys = ["price_min", "price_max", "surface_min", "surface_max", "rooms_min", "rooms_max", "bedrooms_min", "bathrooms_min"];
      const prefs = { ...p };
      numKeys.forEach((k) => {
        if (prefs[k] === "" || prefs[k] == null) prefs[k] = null;
        else prefs[k] = Number(prefs[k]);
      });
      if (!prefs.operation) prefs.operation = null;
      if (!prefs.energy_min_class) prefs.energy_min_class = null;
      if (!prefs.notes || !prefs.notes.trim()) prefs.notes = null;

      const payload = {
        name: form.name.trim(),
        surname: form.surname?.trim() || null,
        email: form.email?.trim() || null,
        phone: form.phone?.trim() || null,
        whatsapp: form.whatsapp?.trim() || null,
        fiscal_code: form.fiscal_code?.trim() || null,
        client_type: form.client_type,
        status: form.status,
        source: form.source?.trim() || null,
        notes: form.notes?.trim() || null,
        gdpr_consent: !!form.gdpr_consent,
        preferences: prefs,
      };

      if (isEdit) {
        await api.patch(`/app/clients/${id}`, payload);
      } else {
        await api.post(`/app/clients`, payload);
      }
      nav(`/${lang}/app/clients`, { replace: true });
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || t("common.error"));
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!window.confirm(t("clients.delete_confirm"))) return;
    try {
      await api.delete(`/app/clients/${id}`);
      nav(`/${lang}/app/clients`, { replace: true });
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const msg = (detail && typeof detail === "object" && detail.message)
        ? detail.message
        : (typeof detail === "string" ? detail : t("common.error"));
      setError(msg);
      // Scroll up so user sees the error
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  if (loading) {
    return (
      <AgencyShell current="clients">
        <p className="text-stone-500 text-sm">{t("common.loading")}</p>
      </AgencyShell>
    );
  }

  return (
    <AgencyShell current="clients">
      <section data-testid="client-form-page" className="max-w-4xl space-y-6">
        <div>
          <Link to={`/${lang}/app/clients`} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900">
            {t("clients.back_to_list")}
          </Link>
          <h1
            className="text-3xl md:text-4xl tracking-tight mt-2"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {isEdit ? t("clients.form_title_edit") : t("clients.form_title_new")}
          </h1>
        </div>

        <form onSubmit={submit} className="space-y-8 bg-white border border-stone-200 rounded-lg p-6 md:p-8">
          {/* Anagrafica */}
          <Section label={t("clients.section_personal")}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label={t("clients.field_name")} required>
                <input data-testid="client-name" required value={form.name} onChange={(e) => upd("name", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.field_surname")}>
                <input data-testid="client-surname" value={form.surname || ""} onChange={(e) => upd("surname", e.target.value)} className="form-input" />
              </Field>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Field label={t("clients.field_email")}>
                <input data-testid="client-email" type="email" value={form.email || ""} onChange={(e) => upd("email", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.field_phone")}>
                <input data-testid="client-phone" value={form.phone || ""} onChange={(e) => upd("phone", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.field_whatsapp")}>
                <input value={form.whatsapp || ""} onChange={(e) => upd("whatsapp", e.target.value)} className="form-input" />
              </Field>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Field label={t("clients.field_type")}>
                <select data-testid="client-type" value={form.client_type} onChange={(e) => upd("client_type", e.target.value)} className="form-input">
                  {CLIENT_TYPES.map((c) => <option key={c} value={c}>{t(`clients.type_${c}`)}</option>)}
                </select>
              </Field>
              <Field label={t("clients.field_status")}>
                <select data-testid="client-status" value={form.status} onChange={(e) => upd("status", e.target.value)} className="form-input">
                  {CLIENT_STATUSES.map((s) => <option key={s} value={s}>{t(`clients.status_${s}`)}</option>)}
                </select>
              </Field>
              <Field label={t("clients.field_source")}>
                <input value={form.source || ""} onChange={(e) => upd("source", e.target.value)} placeholder={t("clients.field_source_placeholder")} className="form-input" />
              </Field>
            </div>
            <Field label={t("clients.field_fiscal_code")}>
              <input value={form.fiscal_code || ""} onChange={(e) => upd("fiscal_code", e.target.value.toUpperCase())} className="form-input" />
            </Field>
            <label className="flex items-start gap-2 text-sm text-stone-700 mt-2">
              <input
                type="checkbox"
                checked={!!form.gdpr_consent}
                onChange={(e) => upd("gdpr_consent", e.target.checked)}
                className="mt-1"
                data-testid="client-gdpr"
              />
              <span>{t("clients.field_gdpr")}</span>
            </label>
          </Section>

          {/* Immobili in carico — only for seller/landlord (M2.S3.5, D-026) */}
          {isEdit && isSellerType && (
            <Section label={t("clients.section_carried_properties") || "Immobili in carico"}>
              {carriedProperties.length === 0 ? (
                <p data-testid="carried-empty" className="text-sm text-stone-500 bg-stone-50 border border-stone-200 rounded-md px-4 py-6 text-center">
                  {t("clients.carried_empty") || "Questo cliente non ha ancora immobili in carico. Vai in Immobili → Nuovo e selezionalo come proprietario."}
                </p>
              ) : (
                <ul data-testid="carried-list" className="space-y-2">
                  {carriedProperties.map((p) => (
                    <li key={p.id}>
                      <a
                        href={`/${lang}/app/properties/${p.id}`}
                        target="_blank"
                        rel="noreferrer"
                        data-testid={`carried-prop-${p.id}`}
                        className="flex items-center justify-between gap-3 border border-stone-200 rounded-md p-3 hover:bg-stone-50 focus:outline-none focus:ring-2 focus:ring-stone-900/10"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          {p.cover_photo_url ? (
                            <img src={p.cover_photo_url} alt="" className="w-16 h-12 object-cover rounded border border-stone-200" />
                          ) : (
                            <div className="w-16 h-12 bg-stone-100 border border-stone-200 rounded flex items-center justify-center text-[9px] text-stone-400 uppercase tracking-widest">no photo</div>
                          )}
                          <div className="min-w-0">
                            <div className="font-medium text-stone-900 truncate">{p.title}</div>
                            <div className="text-xs text-stone-500 truncate">
                              {t(`properties.type_${p.property_type}`)} · {t(`properties.op_${p.operation}`)} · {p.city}
                              {p.rooms ? ` · ${p.rooms} ${t("properties.field_rooms_short") || "loc."}` : ""}
                              {p.surface_sqm ? ` · ${p.surface_sqm} m²` : ""}
                            </div>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-sm font-medium text-stone-900">
                            {p.price ? new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(p.price)
                              : p.rent_monthly ? `${new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(p.rent_monthly)}/mese`
                              : "—"}
                          </div>
                          <div className="text-[10px] uppercase tracking-widest text-stone-500">
                            {t(`properties.status_${p.status}`) || p.status}
                          </div>
                        </div>
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </Section>
          )}

          {/* Preferenze di ricerca (mirror idealista filters) */}
          <Section label={t("clients.section_preferences")}>
            <p className="text-sm text-stone-600 -mt-2">{t("clients.section_preferences_hint")}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label={t("clients.pref_operation")}>
                <select value={form.preferences.operation || ""} onChange={(e) => updPref("operation", e.target.value)} className="form-input">
                  {OPERATIONS.map((op) => (
                    <option key={op} value={op}>{op ? t(`properties.op_${op}`) : t("clients.pref_any")}</option>
                  ))}
                </select>
              </Field>
              <Field label={t("clients.pref_cities")}>
                <input
                  data-testid="pref-cities"
                  value={arrToText(form.preferences.cities)}
                  onChange={(e) => updPref("cities", textToArr(e.target.value))}
                  placeholder={t("clients.pref_cities_placeholder")}
                  className="form-input"
                />
              </Field>
            </div>

            <Field label={t("clients.pref_zones")}>
              <input
                value={arrToText(form.preferences.zones)}
                onChange={(e) => updPref("zones", textToArr(e.target.value))}
                placeholder={t("clients.pref_zones_placeholder")}
                className="form-input"
              />
            </Field>

            {/* Property types — chips */}
            <Field label={t("clients.pref_property_types")}>
              <div className="flex flex-wrap gap-2">
                {PROPERTY_TYPES.map((pt) => {
                  const on = form.preferences.property_types?.includes(pt);
                  return (
                    <button
                      key={pt}
                      type="button"
                      data-testid={`pref-pt-${pt}`}
                      onClick={() => togglePrefArr("property_types", pt)}
                      className={`text-xs px-3 py-1.5 rounded-full border transition ${
                        on ? "bg-stone-900 text-stone-50 border-stone-900" : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
                      }`}
                    >
                      {t(`properties.type_${pt}`)}
                    </button>
                  );
                })}
              </div>
            </Field>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Field label={t("clients.pref_price_min")}>
                <input data-testid="pref-price-min" type="number" value={form.preferences.price_min} onChange={(e) => updPref("price_min", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.pref_price_max")}>
                <input data-testid="pref-price-max" type="number" value={form.preferences.price_max} onChange={(e) => updPref("price_max", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.pref_surface_min")}>
                <input type="number" value={form.preferences.surface_min} onChange={(e) => updPref("surface_min", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.pref_surface_max")}>
                <input type="number" value={form.preferences.surface_max} onChange={(e) => updPref("surface_max", e.target.value)} className="form-input" />
              </Field>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Field label={t("clients.pref_rooms_min")}>
                <input type="number" value={form.preferences.rooms_min} onChange={(e) => updPref("rooms_min", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.pref_rooms_max")}>
                <input type="number" value={form.preferences.rooms_max} onChange={(e) => updPref("rooms_max", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.pref_bedrooms_min")}>
                <input type="number" value={form.preferences.bedrooms_min} onChange={(e) => updPref("bedrooms_min", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("clients.pref_bathrooms_min")}>
                <input type="number" value={form.preferences.bathrooms_min} onChange={(e) => updPref("bathrooms_min", e.target.value)} className="form-input" />
              </Field>
            </div>

            <Field label={t("clients.pref_conditions")}>
              <div className="flex flex-wrap gap-2">
                {CONDITIONS.map((c) => {
                  const on = form.preferences.conditions?.includes(c);
                  return (
                    <button
                      key={c}
                      type="button"
                      onClick={() => togglePrefArr("conditions", c)}
                      className={`text-xs px-3 py-1.5 rounded-full border transition ${
                        on ? "bg-stone-900 text-stone-50 border-stone-900" : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
                      }`}
                    >
                      {t(`properties.cond_${c}`)}
                    </button>
                  );
                })}
              </div>
            </Field>

            <Field label={t("clients.pref_floors")}>
              <div className="flex flex-wrap gap-2">
                {FLOORS.map((f) => {
                  const on = form.preferences.floor_preferences?.includes(f);
                  return (
                    <button
                      key={f}
                      type="button"
                      onClick={() => togglePrefArr("floor_preferences", f)}
                      className={`text-xs px-3 py-1.5 rounded-full border transition ${
                        on ? "bg-stone-900 text-stone-50 border-stone-900" : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
                      }`}
                    >
                      {t(`clients.floor_${f}`)}
                    </button>
                  );
                })}
              </div>
            </Field>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Field label={t("clients.pref_energy_min")}>
                <select value={form.preferences.energy_min_class || ""} onChange={(e) => updPref("energy_min_class", e.target.value)} className="form-input">
                  {ENERGY_CLASSES.map((c) => (
                    <option key={c} value={c}>{c || t("clients.pref_any")}</option>
                  ))}
                </select>
              </Field>
              <label className="flex items-center gap-2 text-sm text-stone-700 mt-7">
                <input type="checkbox" checked={!!form.preferences.needs_photos} onChange={(e) => updPref("needs_photos", e.target.checked)} />
                {t("clients.pref_needs_photos")}
              </label>
              <label className="flex items-center gap-2 text-sm text-stone-700 mt-7">
                <input type="checkbox" checked={!!form.preferences.needs_virtual_tour} onChange={(e) => updPref("needs_virtual_tour", e.target.checked)} />
                {t("clients.pref_needs_vtour")}
              </label>
            </div>

            <Field label={t("clients.pref_features")}>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {FEATURES.map((f) => {
                  const on = form.preferences.must_have_features?.includes(f);
                  return (
                    <label key={f} className="flex items-center gap-2 text-sm text-stone-700">
                      <input
                        type="checkbox"
                        checked={!!on}
                        onChange={() => togglePrefArr("must_have_features", f)}
                      />
                      {t(`properties.feat_${f}`)}
                    </label>
                  );
                })}
              </div>
            </Field>

            <Field label={t("clients.pref_notes")}>
              <textarea
                value={form.preferences.notes || ""}
                onChange={(e) => updPref("notes", e.target.value)}
                className="form-input h-24"
                placeholder={t("clients.pref_notes_placeholder")}
              />
            </Field>
          </Section>

          <Section label={t("clients.section_notes")}>
            <Field label={t("clients.field_notes")}>
              <textarea
                value={form.notes || ""}
                onChange={(e) => upd("notes", e.target.value)}
                className="form-input h-28"
                placeholder={t("clients.field_notes_placeholder")}
              />
            </Field>
          </Section>

          {error && (
            <p data-testid="client-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</p>
          )}

          <div className="flex justify-between items-center pt-4 border-t border-stone-200">
            {isEdit && (
              <button type="button" onClick={onDelete} data-testid="client-delete-btn" className="text-xs uppercase tracking-widest text-red-700 hover:text-red-900">
                {t("clients.delete")}
              </button>
            )}
            <button
              type="submit"
              disabled={saving}
              data-testid="client-save-btn"
              className="ml-auto px-6 py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50"
            >
              {saving ? t("common.loading") : t("clients.save")}
            </button>
          </div>
        </form>

        <style>{`
          .form-input {
            width: 100%;
            padding: 0.5rem 0.75rem;
            background: white;
            border: 1px solid #d6d3d1;
            border-radius: 6px;
            font-size: 0.875rem;
          }
          .form-input:focus {
            outline: none;
            border-color: #1c1917;
            box-shadow: 0 0 0 3px rgba(28,25,23,0.06);
          }
        `}</style>
      </section>
    </AgencyShell>
  );
}

function Section({ label, children }) {
  return (
    <fieldset className="space-y-4">
      <legend className="text-xs uppercase tracking-widest text-stone-500 font-semibold mb-2">{label}</legend>
      {children}
    </fieldset>
  );
}

function Field({ label, required, children }) {
  return (
    <div>
      <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
        {label}{required && <span className="text-red-600 ml-1">*</span>}
      </label>
      {children}
    </div>
  );
}
