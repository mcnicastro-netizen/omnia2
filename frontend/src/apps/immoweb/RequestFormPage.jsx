import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";
import { formatApiErrorDetail } from "../../shared/lib/auth";

const emptyCriteria = {
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
};

function formatPrice(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(v);
}

export default function RequestFormPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const nav = useNavigate();
  const isNew = !id || id === "new";

  const [form, setForm] = useState({
    client_id: searchParams.get("client_id") || "",
    request_type: searchParams.get("type") || "search_brief",
    property_id: searchParams.get("property_id") || "",
    title: "",
    notes: "",
    mls_shared: false,
    auto_match: true,
    match_tolerances: { price_pct: 10, surface_pct: 10, min_score: 50 },
    source: "manual",
    criteria: { ...emptyCriteria },
  });
  const [clientLabel, setClientLabel] = useState("");
  const [clientQ, setClientQ] = useState("");
  const [clientHits, setClientHits] = useState([]);
  const [matches, setMatches] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(!isNew);

  useEffect(() => {
    if (isNew) return;
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get(`/app/requests/${id}`);
        setForm({
          client_id: data.client_id,
          request_type: data.request_type,
          property_id: data.property_id || "",
          title: data.title || "",
          notes: data.notes || "",
          mls_shared: !!data.mls_shared,
          auto_match: data.auto_match !== false,
          match_tolerances: {
            price_pct: data.match_tolerances?.price_pct ?? 10,
            surface_pct: data.match_tolerances?.surface_pct ?? 10,
            min_score: data.match_tolerances?.min_score ?? 50,
          },
          source: data.source || "manual",
          status: data.status,
          criteria: {
            ...emptyCriteria,
            ...(data.criteria || {}),
            cities: data.criteria?.cities || [],
            zones: data.criteria?.zones || [],
            property_types: data.criteria?.property_types || [],
          },
        });
        if (data.client_id) {
          try {
            const { data: c } = await api.get(`/app/clients/${data.client_id}`);
            setClientLabel(`${c.name || ""} ${c.surname || ""}`.trim());
          } catch { /* ignore */ }
        }
        const { data: m } = await api.get(`/app/requests/${id}/matches?min_score=50`);
        setMatches(m);
      } catch (e) {
        setError(formatApiErrorDetail(e) || t("requests.load_error"));
      } finally {
        setLoading(false);
      }
    })();
  }, [id, isNew]); // eslint-disable-line react-hooks/exhaustive-deps

  // Prefill client label when ?client_id=
  useEffect(() => {
    if (!isNew || !form.client_id) return;
    (async () => {
      try {
        const { data: c } = await api.get(`/app/clients/${form.client_id}`);
        setClientLabel(`${c.name || ""} ${c.surname || ""}`.trim());
      } catch { /* ignore */ }
    })();
  }, [isNew, form.client_id]);

  const searchClients = async (q) => {
    setClientQ(q);
    if (!q || q.length < 2) {
      setClientHits([]);
      return;
    }
    try {
      const { data } = await api.get(`/app/clients`, { params: { q, page_size: 10, client_type: "buyer" } });
      // Also tenants/investors — fetch without type if few results
      let items = data.items || [];
      if (items.length < 5) {
        const { data: d2 } = await api.get(`/app/clients`, { params: { q, page_size: 10 } });
        items = (d2.items || []).filter((c) => ["buyer", "tenant", "investor"].includes(c.client_type));
      }
      setClientHits(items);
    } catch {
      setClientHits([]);
    }
  };

  const upd = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const updCrit = (k, v) => setForm((f) => ({ ...f, criteria: { ...f.criteria, [k]: v } }));

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      const cities = Array.isArray(form.criteria.cities)
        ? form.criteria.cities
        : String(form.criteria.cities || "").split(",").map((x) => x.trim()).filter(Boolean);
      const criteria = {
        ...form.criteria,
        cities,
        price_min: form.criteria.price_min === "" ? null : Number(form.criteria.price_min) || null,
        price_max: form.criteria.price_max === "" ? null : Number(form.criteria.price_max) || null,
        surface_min: form.criteria.surface_min === "" ? null : Number(form.criteria.surface_min) || null,
        surface_max: form.criteria.surface_max === "" ? null : Number(form.criteria.surface_max) || null,
        rooms_min: form.criteria.rooms_min === "" ? null : Number(form.criteria.rooms_min) || null,
        rooms_max: form.criteria.rooms_max === "" ? null : Number(form.criteria.rooms_max) || null,
        operation: form.criteria.operation || null,
      };

      if (isNew) {
        if (!form.client_id) {
          setError(t("requests.err_client_required"));
          setSaving(false);
          return;
        }
        const body = {
          client_id: form.client_id,
          request_type: form.request_type,
          property_id: form.request_type === "property_interest" ? form.property_id || null : null,
          title: form.title || null,
          notes: form.notes || null,
          mls_shared: !!form.mls_shared,
          source: "manual",
          criteria,
        };
        const { data } = await api.post("/app/requests", body);
        // set tolerances / auto_match after create
        await api.patch(`/app/requests/${data.id}`, {
          auto_match: !!form.auto_match,
          match_tolerances: {
            price_pct: Number(form.match_tolerances.price_pct) || 10,
            surface_pct: Number(form.match_tolerances.surface_pct) || 10,
            min_score: Number(form.match_tolerances.min_score) || 50,
          },
        });
        nav(`/${lang}/app/requests/${data.id}`, { replace: true });
      } else {
        await api.patch(`/app/requests/${id}`, {
          request_type: form.request_type,
          property_id: form.request_type === "property_interest" ? form.property_id || null : null,
          title: form.title || null,
          notes: form.notes || null,
          mls_shared: !!form.mls_shared,
          auto_match: !!form.auto_match,
          match_tolerances: {
            price_pct: Number(form.match_tolerances.price_pct) || 10,
            surface_pct: Number(form.match_tolerances.surface_pct) || 10,
            min_score: Number(form.match_tolerances.min_score) || 50,
          },
          criteria,
          status: form.status,
        });
        const { data: m } = await api.get(`/app/requests/${id}/matches?min_score=50`);
        setMatches(m);
      }
    } catch (err) {
      setError(formatApiErrorDetail(err) || t("requests.save_error"));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <AgencyShell current="requests">
        <p className="text-stone-500 text-sm">{t("common.loading")}</p>
      </AgencyShell>
    );
  }

  return (
    <AgencyShell current="requests">
      <section data-testid="request-form-page" className="space-y-6 max-w-3xl">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <Link to={`/${lang}/app/requests`} className="text-xs uppercase tracking-widest text-stone-500 hover:text-stone-800">
              {t("requests.back")}
            </Link>
            <h1 className="text-3xl tracking-tight mt-1" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {isNew ? t("requests.form_new") : t("requests.form_edit")}
            </h1>
          </div>
        </div>

        {error && (
          <p className="text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-md px-3 py-2">{error}</p>
        )}

        <form onSubmit={save} className="space-y-5 bg-white border border-stone-200 rounded-lg p-6">
          {/* Client */}
          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1">{t("requests.field_client")}</label>
            {isNew ? (
              <div className="relative">
                <input
                  data-testid="request-client-search"
                  value={clientLabel || clientQ}
                  onChange={(e) => {
                    setClientLabel("");
                    upd("client_id", "");
                    searchClients(e.target.value);
                  }}
                  placeholder={t("requests.client_search_ph")}
                  className="form-input w-full"
                />
                {clientHits.length > 0 && !form.client_id && (
                  <ul className="absolute z-10 mt-1 w-full bg-white border border-stone-300 rounded-md shadow-sm max-h-48 overflow-auto">
                    {clientHits.map((c) => (
                      <li key={c.id}>
                        <button
                          type="button"
                          className="w-full text-left px-3 py-2 text-sm hover:bg-stone-100"
                          onClick={() => {
                            upd("client_id", c.id);
                            setClientLabel(`${c.name || ""} ${c.surname || ""}`.trim());
                            setClientHits([]);
                          }}
                        >
                          {c.name} {c.surname} · {t(`clients.type_${c.client_type}`)}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="text-stone-800">
                <Link to={`/${lang}/app/clients/${form.client_id}`} className="underline underline-offset-2">
                  {clientLabel || form.client_id}
                </Link>
                <span className="ml-2 text-[10px] uppercase tracking-widest text-stone-400">{form.source}</span>
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1">{t("requests.field_type")}</label>
              <select
                data-testid="request-type"
                value={form.request_type}
                onChange={(e) => upd("request_type", e.target.value)}
                className="form-input w-full"
              >
                <option value="search_brief">{t("requests.type_search_brief")}</option>
                <option value="property_interest">{t("requests.type_property_interest")}</option>
              </select>
            </div>
            {form.request_type === "property_interest" && (
              <div>
                <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1">{t("requests.field_property_id")}</label>
                <input
                  data-testid="request-property-id"
                  value={form.property_id}
                  onChange={(e) => upd("property_id", e.target.value)}
                  placeholder="UUID immobile"
                  className="form-input w-full"
                />
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1">{t("requests.field_title")}</label>
            <input value={form.title} onChange={(e) => upd("title", e.target.value)} className="form-input w-full" />
          </div>

          {/* Criteria */}
          <fieldset className="border border-stone-200 rounded-md p-4 space-y-3">
            <legend className="text-xs uppercase tracking-widest text-stone-500 px-1">{t("requests.section_criteria")}</legend>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-stone-500">{t("clients.pref_operation")}</label>
                <select value={form.criteria.operation || ""} onChange={(e) => updCrit("operation", e.target.value)} className="form-input w-full">
                  <option value="">{t("clients.pref_any")}</option>
                  <option value="sale">{t("clients.op_sale")}</option>
                  <option value="rent">{t("clients.op_rent")}</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-stone-500">{t("clients.pref_cities")}</label>
                <input
                  value={Array.isArray(form.criteria.cities) ? form.criteria.cities.join(", ") : form.criteria.cities}
                  onChange={(e) => updCrit("cities", e.target.value)}
                  className="form-input w-full"
                  placeholder="Roma, Milano"
                />
              </div>
              <div>
                <label className="text-xs text-stone-500">{t("clients.pref_price_max")}</label>
                <input type="number" value={form.criteria.price_max || ""} onChange={(e) => updCrit("price_max", e.target.value)} className="form-input w-full" />
              </div>
            </div>
          </fieldset>

          <label className="flex items-start gap-2 text-sm text-stone-700">
            <input
              type="checkbox"
              data-testid="request-mls-shared"
              checked={!!form.mls_shared}
              onChange={(e) => upd("mls_shared", e.target.checked)}
              className="mt-1"
            />
            <span>{t("requests.field_mls_shared")}</span>
          </label>

          <label className="flex items-start gap-2 text-sm text-stone-700">
            <input
              type="checkbox"
              data-testid="request-auto-match"
              checked={!!form.auto_match}
              onChange={(e) => upd("auto_match", e.target.checked)}
              className="mt-1"
            />
            <span>{t("requests.field_auto_match")}</span>
          </label>

          <fieldset className="border border-stone-200 rounded-md p-4 space-y-3">
            <legend className="text-xs uppercase tracking-widest text-stone-500 px-1">{t("requests.section_tolerances")}</legend>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div>
                <label className="text-xs text-stone-500">{t("requests.tol_price")}</label>
                <input
                  type="number"
                  min={0}
                  max={50}
                  value={form.match_tolerances.price_pct}
                  onChange={(e) => setForm((f) => ({
                    ...f,
                    match_tolerances: { ...f.match_tolerances, price_pct: e.target.value },
                  }))}
                  className="form-input w-full"
                />
              </div>
              <div>
                <label className="text-xs text-stone-500">{t("requests.tol_surface")}</label>
                <input
                  type="number"
                  min={0}
                  max={50}
                  value={form.match_tolerances.surface_pct}
                  onChange={(e) => setForm((f) => ({
                    ...f,
                    match_tolerances: { ...f.match_tolerances, surface_pct: e.target.value },
                  }))}
                  className="form-input w-full"
                />
              </div>
              <div>
                <label className="text-xs text-stone-500">{t("requests.tol_min_score")}</label>
                <input
                  type="number"
                  min={0}
                  max={100}
                  value={form.match_tolerances.min_score}
                  onChange={(e) => setForm((f) => ({
                    ...f,
                    match_tolerances: { ...f.match_tolerances, min_score: e.target.value },
                  }))}
                  className="form-input w-full"
                />
              </div>
            </div>
          </fieldset>

          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1">{t("requests.field_notes")}</label>
            <textarea value={form.notes || ""} onChange={(e) => upd("notes", e.target.value)} rows={3} className="form-input w-full" />
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={saving}
              data-testid="request-save"
              className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md disabled:opacity-50"
            >
              {saving ? t("common.saving") : t("requests.save")}
            </button>
            <Link to={`/${lang}/app/requests`} className="px-5 py-2.5 border border-stone-300 text-xs uppercase tracking-widest rounded-md">
              {t("common.cancel")}
            </Link>
          </div>
        </form>

        {!isNew && matches && (
          <div data-testid="request-matches" className="space-y-3">
            <h2 className="text-xl" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("requests.matches_title")}
            </h2>
            <p className="text-sm text-stone-600">
              {matches.scope_used === "portfolio" && t("requests.matches_from_portfolio")}
              {matches.scope_used === "mls" && t("requests.matches_from_mls")}
              {matches.scope_used === "none" && t("requests.matches_none")}
            </p>
            {(matches.items || []).length === 0 ? (
              <p className="text-stone-500 text-sm">{t("requests.matches_empty")}</p>
            ) : (
              <ul className="space-y-2">
                {matches.items.map((m) => (
                  <li
                    key={`${m.property_id}-${m.scope}`}
                    className="bg-white border border-stone-200 rounded-lg px-4 py-3 flex flex-wrap justify-between gap-2"
                  >
                    <div>
                      <div className="font-medium text-stone-900">{m.title || m.reference_code || m.property_id}</div>
                      <div className="text-xs text-stone-500 uppercase tracking-widest mt-0.5">
                        {m.scope === "mls" ? t("requests.scope_mls") : t("requests.scope_portfolio")}
                        {m.city ? ` · ${m.city}` : ""}
                        {m.price != null ? ` · ${formatPrice(m.price)}` : ""}
                      </div>
                    </div>
                    <div className="text-2xl font-light text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                      {m.score}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </section>
    </AgencyShell>
  );
}
