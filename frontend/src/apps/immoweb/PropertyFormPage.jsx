import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams, Link } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import PhotoUploader from "./components/PhotoUploader";
import StagingStudio from "./components/StagingStudio";
import PropertyMatchesPreview from "./components/PropertyMatchesPreview";
import PublishingCenter from "./components/PublishingCenter";
import AlImproveButton from "../../shared/components/AlImproveButton";
import { api } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";

const TYPES = [
  "appartamento", "villa", "villetta_a_schiera", "loft", "attico", "monolocale",
  "rustico_casale", "ufficio", "negozio", "magazzino", "capannone", "garage_box",
  "terreno_agricolo", "terreno_edificabile", "palazzo_stabile", "altro",
];
const OPS = ["sale", "rent", "rent_to_buy", "auction"];
const STATUSES = ["draft", "active", "reserved", "sold", "rented", "withdrawn"];
const CONDITIONS = ["nuovo", "ottime", "buone", "da_ristrutturare", "ristrutturato"];
const FURNISHED = ["arredato", "parz_arredato", "non_arredato"];
const HEATING = ["autonomo", "centralizzato", "assente"];
const ENERGY_CLASSES = ["A4", "A3", "A2", "A1", "A", "B", "C", "D", "E", "F", "G"];

const FEATURES = [
  "balcone", "terrazza", "giardino", "piscina", "ascensore",
  "aria_condizionata", "riscaldamento_autonomo", "cantina", "soffitta",
  "posto_auto", "box_auto", "portineria", "videocitofono", "allarme",
  "porta_blindata", "cucina_abitabile", "camino", "parquet",
  "vista_panoramica", "luminoso", "arredato", "pannelli_solari",
  "cancello_elettrico", "impianto_domotico", "accesso_disabili",
];

const empty = {
  title: "", description: "", reference_code: "",
  property_type: "appartamento", operation: "sale", status: "draft", condition: "",
  address: "", city: "", province: "", postal_code: "", zone: "", hide_address: false,
  price: "", rent_monthly: "", condo_fees: "", price_negotiable: false,
  surface_sqm: "", rooms: "", bedrooms: "", bathrooms: "", floor: "", total_floors: "",
  year_built: "", furnished: "",
  energy: { energy_class: "", energy_value: "", heating: "" },
  features: Object.fromEntries(FEATURES.map((k) => [k, false])),
  owner: { name: "", phone: "", email: "" },
  seller_client_id: "",
  photos: [],
  is_listed_on_immobilcloud: true,
};

export default function PropertyFormPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { id } = useParams();
  const nav = useNavigate();
  const isEdit = !!id;
  const [form, setForm] = useState(empty);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [agency, setAgency] = useState(null);
  const [stagingPhoto, setStagingPhoto] = useState(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [loaded, setLoaded] = useState(!id);

  useEffect(() => {
    api.get(`/app/agencies/me`).then((r) => setAgency(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (!isEdit) return;
    // H4 — if the GET fails, block submit: never PATCH over real data with an empty form
    api.get(`/app/properties/${id}`).then((r) => {
      const d = r.data;
      const nn = (obj) => Object.fromEntries(Object.entries(obj || {}).map(([k, v]) => [k, v === null ? "" : v]));
      setForm({
        ...empty,
        ...nn(d),
        energy: { ...empty.energy, ...nn(d.energy) },
        features: { ...empty.features, ...nn(d.features) },
        owner: { ...empty.owner, ...nn(d.owner) },
      });
      setLoaded(true);
    }).catch(() => {
      setLoadFailed(true);
      setError(t("common.error"));
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const upd = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const updNested = (group, key, value) => setForm((f) => ({ ...f, [group]: { ...f[group], [key]: value } }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const numFields = ["price", "rent_monthly", "condo_fees", "surface_sqm", "rooms", "bedrooms", "bathrooms", "floor", "total_floors", "year_built"];
      const cleanGroup = (obj) => Object.fromEntries(Object.entries(obj || {}).filter(([, v]) => v !== "" && v != null));
      const payload = { ...form };
      numFields.forEach((f) => {
        if (payload[f] === "" || payload[f] == null) delete payload[f];
        else payload[f] = Number(payload[f]);
      });
      if (payload.condition === "") delete payload.condition;
      if (payload.furnished === "") delete payload.furnished;
      payload.energy = cleanGroup(form.energy);
      if (payload.energy.energy_value) payload.energy.energy_value = Number(payload.energy.energy_value);
      if (!Object.keys(payload.energy).length) delete payload.energy;
      payload.owner = cleanGroup(form.owner);
      if (!Object.keys(payload.owner).length) delete payload.owner;
      if (form.features) {
        payload.features = cleanGroup(form.features);
        if (!Object.keys(payload.features).length) delete payload.features;
      }
      if (payload.description === "") payload.description = null;
      Object.keys(payload).forEach((k) => {
        if (payload[k] === "") delete payload[k];
      });
      payload.seller_client_id = form.seller_client_id || null;
      payload.photos = form.photos || [];

      if (isEdit) {
        await api.patch(`/app/properties/${id}`, payload);
      } else {
        await api.post(`/app/properties`, payload);
      }
      nav(`/${lang}/app/properties`, { replace: true });
    } catch (err) {
      setError(formatApiErrorDetail(err?.response?.data?.detail) || t("common.error"));
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async () => {
    if (!window.confirm(t("properties.delete_confirm"))) return;
    await api.delete(`/app/properties/${id}`);
    nav(`/${lang}/app/properties`, { replace: true });
  };

  return (
    <AgencyShell current="properties">
      <section data-testid="property-form-page" className="max-w-4xl space-y-6">
        <div>
          <Link to={`/${lang}/app/properties`} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-900">
            {t("properties.back_to_list")}
          </Link>
          <h1
            className="text-3xl md:text-4xl tracking-tight mt-2"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {isEdit ? t("properties.form_title_edit") : t("properties.form_title_new")}
          </h1>
          {isEdit && (
            <Link
              to={`/${lang}/app/properties/${id}/fascicolo`}
              data-testid="fascicolo-link"
              className="inline-block mt-3 text-xs uppercase tracking-widest border border-stone-300 hover:border-stone-900 px-4 py-2 text-stone-700"
            >
              📁 Fascicolo Immobile AI
            </Link>
          )}
        </div>

        <form onSubmit={submit} className="space-y-8 bg-white border border-stone-200 rounded-lg p-6 md:p-8">
          {/* Basics */}
          <Section label={t("properties.section_basics")}>
            <Field label={t("properties.field_title")} required>
              <div className="flex items-start gap-2">
                <input data-testid="prop-title" required value={form.title} onChange={(e) => upd("title", e.target.value)} className="form-input flex-1" />
                <AlImproveButton
                  field="title"
                  value={form.title}
                  propertyData={form}
                  onApply={(text) => upd("title", text)}
                  testId="al-improve-title"
                />
              </div>
            </Field>
            <Field label={t("properties.field_description")}>
              <div className="space-y-2">
                <textarea data-testid="prop-description" value={form.description || ""} onChange={(e) => upd("description", e.target.value)} className="form-input h-24" />
                <div className="flex justify-end">
                  <AlImproveButton
                    field="description"
                    value={form.description}
                    propertyData={form}
                    onApply={(text) => upd("description", text)}
                    testId="al-improve-description"
                  />
                </div>
              </div>
            </Field>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Field label={t("properties.field_type")}>
                <select value={form.property_type} onChange={(e) => upd("property_type", e.target.value)} className="form-input">
                  {TYPES.map((tp) => <option key={tp} value={tp}>{t(`properties.type_${tp}`)}</option>)}
                </select>
              </Field>
              <Field label={t("properties.field_operation")}>
                <select value={form.operation} onChange={(e) => upd("operation", e.target.value)} className="form-input">
                  {OPS.map((op) => <option key={op} value={op}>{t(`properties.op_${op}`)}</option>)}
                </select>
              </Field>
              <Field label={t("properties.field_status")}>
                <select value={form.status} onChange={(e) => upd("status", e.target.value)} className="form-input">
                  {STATUSES.map((s) => <option key={s} value={s}>{t(`properties.status_${s}`)}</option>)}
                </select>
              </Field>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Field label={t("properties.field_reference")}>
                <input value={form.reference_code || ""} onChange={(e) => upd("reference_code", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_condition")}>
                <select value={form.condition || ""} onChange={(e) => upd("condition", e.target.value)} className="form-input">
                  <option value="">—</option>
                  {CONDITIONS.map((c) => <option key={c} value={c}>{t(`properties.cond_${c}`)}</option>)}
                </select>
              </Field>
            </div>
          </Section>

          {/* Location */}
          <Section label={t("properties.section_location")}>
            <Field label={t("properties.field_address")}>
              <input value={form.address || ""} onChange={(e) => upd("address", e.target.value)} className="form-input" />
            </Field>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Field label={t("properties.field_city")} required>
                <input data-testid="prop-city" required value={form.city} onChange={(e) => upd("city", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_province")}>
                <input maxLength={2} value={form.province || ""} onChange={(e) => upd("province", e.target.value.toUpperCase())} className="form-input" />
              </Field>
              <Field label={t("properties.field_postal_code")}>
                <input value={form.postal_code || ""} onChange={(e) => upd("postal_code", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_zone")}>
                <input value={form.zone || ""} onChange={(e) => upd("zone", e.target.value)} className="form-input" />
              </Field>
            </div>
            <label className="flex items-center gap-2 text-sm text-stone-600">
              <input type="checkbox" checked={form.hide_address} onChange={(e) => upd("hide_address", e.target.checked)} />
              {t("properties.field_hide_address")}
            </label>
          </Section>

          {/* Economics */}
          <Section label={t("properties.section_economics")}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Field label={t("properties.field_price")}>
                <input type="number" data-testid="prop-price" value={form.price} onChange={(e) => upd("price", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_rent")}>
                <input type="number" value={form.rent_monthly} onChange={(e) => upd("rent_monthly", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_condo_fees")}>
                <input type="number" value={form.condo_fees} onChange={(e) => upd("condo_fees", e.target.value)} className="form-input" />
              </Field>
            </div>
          </Section>

          {/* Size */}
          <Section label={t("properties.section_size")}>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Field label={t("properties.field_surface")}>
                <input type="number" value={form.surface_sqm} onChange={(e) => upd("surface_sqm", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_rooms")}>
                <input type="number" value={form.rooms} onChange={(e) => upd("rooms", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_bedrooms")}>
                <input type="number" value={form.bedrooms} onChange={(e) => upd("bedrooms", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_bathrooms")}>
                <input type="number" value={form.bathrooms} onChange={(e) => upd("bathrooms", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_floor")}>
                <input type="number" value={form.floor} onChange={(e) => upd("floor", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_total_floors")}>
                <input type="number" value={form.total_floors} onChange={(e) => upd("total_floors", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_year")}>
                <input type="number" value={form.year_built} onChange={(e) => upd("year_built", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_furnished")}>
                <select value={form.furnished || ""} onChange={(e) => upd("furnished", e.target.value)} className="form-input">
                  <option value="">—</option>
                  {FURNISHED.map((f) => <option key={f} value={f}>{t(`properties.furn_${f}`)}</option>)}
                </select>
              </Field>
            </div>
          </Section>

          {/* Features (25 checkboxes) */}
          <Section label={t("properties.section_features")}>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
              {FEATURES.map((f) => (
                <label key={f} className="flex items-center gap-2 text-sm text-stone-700">
                  <input
                    type="checkbox"
                    data-testid={`feat-${f}`}
                    checked={!!form.features[f]}
                    onChange={(e) => updNested("features", f, e.target.checked)}
                  />
                  {t(`properties.feat_${f}`)}
                </label>
              ))}
            </div>
          </Section>

          {/* Energy */}
          <Section label={t("properties.section_energy")}>
            <div className="grid grid-cols-3 gap-4">
              <Field label={t("properties.field_energy_class")}>
                <select value={form.energy.energy_class || ""} onChange={(e) => updNested("energy", "energy_class", e.target.value)} className="form-input">
                  <option value="">—</option>
                  {ENERGY_CLASSES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </Field>
              <Field label={t("properties.field_energy_value")}>
                <input type="number" value={form.energy.energy_value || ""} onChange={(e) => updNested("energy", "energy_value", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_heating")}>
                <select value={form.energy.heating || ""} onChange={(e) => updNested("energy", "heating", e.target.value)} className="form-input">
                  <option value="">—</option>
                  {HEATING.map((h) => <option key={h} value={h}>{t(`properties.heat_${h}`)}</option>)}
                </select>
              </Field>
            </div>
          </Section>

          {/* Photos */}
          <Section label="Foto immobile">
            <PhotoUploader
              photos={form.photos || []}
              onChange={(photos) => upd("photos", photos)}
              max={15}
              onStage={(p) => setStagingPhoto(p)}
            />
            <p className="text-xs text-stone-400 mt-2">
              🪄 Passa il mouse su una foto e clicca la bacchetta per arredarla con il Virtual Staging AI.
            </p>
          </Section>

          {/* Publishing Center (M3.S2) — toggle ImmobilCloud + Social share */}
          <Section label={t("properties.section_publishing")}>
            <PublishingCenter
              propertyId={isEdit ? id : null}
              property={form}
              agency={agency}
              isListedOnImmobilCloud={form.is_listed_on_immobilcloud}
              onToggleImmobilCloud={(v) => upd("is_listed_on_immobilcloud", v)}
            />
          </Section>

          {/* AI Match preview — only in edit mode */}
          {isEdit && id && (
            <Section label={t("matches.section_title") || "✨ Lead caldi per questo immobile"}>
              <PropertyMatchesPreview propertyId={id} lang={lang} />
            </Section>
          )}

          {/* Owner (reserved) */}
          <Section label={t("properties.section_owner")}>
            <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 px-3 py-2 rounded">
              🔒 Questi dati sono riservati: non vengono mai mostrati pubblicamente o nei portali esterni.
            </p>

            <Field label={t("properties.field_seller_client") || "Cliente venditore / proprietario"}>
              <SellerPicker
                value={form.seller_client_id}
                onChange={(cid, picked) => {
                  setForm((f) => {
                    // Auto-fill owner snapshot when picking, to keep public-portal owner-name aligned
                    const next = { ...f, seller_client_id: cid || "" };
                    if (cid && picked) {
                      next.owner = {
                        name: [picked.name, picked.surname].filter(Boolean).join(" "),
                        phone: picked.phone || f.owner.phone || "",
                        email: picked.email || f.owner.email || "",
                      };
                    }
                    return next;
                  });
                }}
                t={t}
                lang={lang}
              />
            </Field>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Field label={t("properties.field_owner_name")}>
                <input value={form.owner.name || ""} onChange={(e) => updNested("owner", "name", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_owner_phone")}>
                <input value={form.owner.phone || ""} onChange={(e) => updNested("owner", "phone", e.target.value)} className="form-input" />
              </Field>
              <Field label={t("properties.field_owner_email")}>
                <input type="email" value={form.owner.email || ""} onChange={(e) => updNested("owner", "email", e.target.value)} className="form-input" />
              </Field>
            </div>
          </Section>

          {error && (
            <p data-testid="prop-error" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</p>
          )}

          <div className="flex justify-between items-center pt-4 border-t border-stone-200">
            {isEdit && (
              <button type="button" onClick={onDelete} className="text-xs uppercase tracking-widest text-red-700 hover:text-red-900">
                {t("properties.delete")}
              </button>
            )}
            <button
              type="submit"
              disabled={saving || loadFailed || !loaded}
              data-testid="prop-save-btn"
              className="ml-auto px-6 py-3 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 disabled:opacity-50"
            >
              {saving ? t("common.loading") : t("properties.save")}
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

      {/* Virtual Staging modal — inline "Arreda questa foto" (M5.S4.2) */}
      {stagingPhoto && (
        <div
          data-testid="staging-modal"
          className="fixed inset-0 z-50 bg-stone-900/70 flex items-start justify-center p-4 sm:p-8 overflow-y-auto"
          onClick={(e) => e.target === e.currentTarget && setStagingPhoto(null)}
        >
          <div className="bg-stone-50 w-full max-w-4xl border border-stone-200 shadow-xl">
            <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200 bg-white">
              <div>
                <p className="text-[10px] uppercase tracking-[0.3em] text-amber-700">OMNIA · Virtual Staging AI</p>
                <h3 className="text-lg font-semibold text-stone-900">🪄 Arreda questa foto</h3>
              </div>
              <button
                type="button"
                onClick={() => setStagingPhoto(null)}
                data-testid="staging-modal-close"
                className="text-stone-500 hover:text-stone-900 text-xl px-2"
              >
                ✕
              </button>
            </div>
            <div className="p-4 sm:p-6">
              <StagingStudio
                initialImage={stagingPhoto.url}
                propertyId={isEdit ? id : null}
                onAddPhoto={(photo) => {
                  const cur = form.photos || [];
                  upd("photos", [
                    ...cur,
                    {
                      id: crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2),
                      url: photo.url,
                      caption: photo.caption,
                      order: cur.length,
                      is_cover: cur.length === 0,
                    },
                  ]);
                }}
              />
              <p className="mt-4 text-xs text-stone-500">
                Le varianti aggiunte compaiono tra le foto dell&apos;annuncio: ricorda di <strong>salvare l&apos;immobile</strong> per renderle definitive.
              </p>
            </div>
          </div>
        </div>
      )}
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

function SellerPicker({ value, onChange, t, lang }) {
  const [picked, setPicked] = useState(null);  // { id, name, surname, email, phone, client_type }
  const [q, setQ] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [loadingPicked, setLoadingPicked] = useState(false);

  // Hydrate when editing: fetch the existing seller client details
  useEffect(() => {
    if (!value) { setPicked(null); return; }
    if (picked && picked.id === value) return;
    setLoadingPicked(true);
    api.get(`/app/clients/${value}`).then((r) => {
      setPicked({
        id: r.data.id,
        name: r.data.name,
        surname: r.data.surname,
        email: r.data.email,
        phone: r.data.phone,
        client_type: r.data.client_type,
      });
    }).catch(() => setPicked(null)).finally(() => setLoadingPicked(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  // Debounced search
  useEffect(() => {
    if (!open) return;
    const handle = setTimeout(async () => {
      try {
        const { data } = await api.get(`/app/clients/sellers`, { params: { q: q || undefined, limit: 15 } });
        setResults(data.items || []);
      } catch {
        setResults([]);
      }
    }, 250);
    return () => clearTimeout(handle);
  }, [q, open]);

  const select = (item) => {
    setPicked(item);
    setOpen(false);
    setQ("");
    onChange(item.id, item);
  };
  const clear = () => {
    setPicked(null);
    setQ("");
    onChange(null, null);
  };

  if (picked && !open) {
    const label = `${picked.name || ""} ${picked.surname || ""}`.trim();
    return (
      <div data-testid="seller-picked" className="flex items-center justify-between bg-emerald-50 border border-emerald-200 rounded-md px-3 py-2.5">
        <div className="flex items-center gap-3">
          <span className="text-xs uppercase tracking-widest text-emerald-800 bg-white px-2 py-0.5 rounded border border-emerald-300">
            {t(`clients.type_${picked.client_type}`) || picked.client_type}
          </span>
          <div>
            <div className="text-sm font-medium text-stone-900">{label || picked.email || picked.id}</div>
            <div className="text-xs text-stone-500">{picked.email}{picked.phone ? ` · ${picked.phone}` : ""}</div>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <a
            href={`/${lang}/app/clients/${picked.id}`}
            target="_blank"
            rel="noreferrer"
            className="text-emerald-800 hover:underline"
            data-testid="seller-open-card"
          >
            {t("properties.seller_open_card") || "Apri scheda ↗"}
          </a>
          <button type="button" onClick={() => setOpen(true)} className="text-stone-600 hover:text-stone-900" data-testid="seller-change">
            {t("properties.seller_change") || "Cambia"}
          </button>
          <button type="button" onClick={clear} className="text-red-700 hover:text-red-900" data-testid="seller-clear">
            {t("properties.seller_clear") || "Rimuovi"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="relative">
      <input
        data-testid="seller-search"
        value={q}
        onChange={(e) => { setQ(e.target.value); setOpen(true); }}
        onFocus={() => setOpen(true)}
        placeholder={t("properties.seller_search_placeholder") || "Cerca un cliente venditore o proprietario…"}
        className="form-input"
      />
      {open && (
        <div className="absolute z-10 mt-1 w-full bg-white border border-stone-300 rounded-md shadow-lg max-h-64 overflow-y-auto">
          {loadingPicked && <div className="p-3 text-xs text-stone-500">{t("common.loading")}</div>}
          {results.length === 0 ? (
            <div className="p-3 text-xs text-stone-500">
              {t("properties.seller_empty") || "Nessun cliente venditore/proprietario trovato. Crealo prima nella sezione Clienti."}
              <a href={`/${lang}/app/clients/new`} target="_blank" rel="noreferrer" className="block mt-2 text-stone-900 underline">
                + {t("clients.new_btn")}
              </a>
            </div>
          ) : (
            results.map((it) => {
              const label = `${it.name || ""} ${it.surname || ""}`.trim();
              return (
                <button
                  type="button"
                  key={it.id}
                  data-testid={`seller-opt-${it.id}`}
                  onClick={() => select(it)}
                  className="w-full text-left px-3 py-2 hover:bg-stone-50 border-b border-stone-100 last:border-b-0"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-stone-900">{label || it.email || it.id}</span>
                    <span className="text-xs uppercase tracking-widest text-stone-500">{t(`clients.type_${it.client_type}`)}</span>
                  </div>
                  <div className="text-xs text-stone-500">{it.email}{it.phone ? ` · ${it.phone}` : ""}</div>
                </button>
              );
            })
          )}
          <div className="p-2 border-t border-stone-100 text-right">
            <button type="button" onClick={() => setOpen(false)} className="text-xs text-stone-500 hover:text-stone-900">
              {t("common.close") || "Chiudi"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
