import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth } from "../../../shared/lib/auth";
import PropertyMapView from "../components/PropertyMapView";
import PropertyCard from "../components/PropertyCard";

export default function CloudSearchPage() {
  const { t } = useTranslation();
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState({ items: [], total: 0, has_next: false, page: 1 });
  const [loading, setLoading] = useState(false);
  const viewMode = params.get("view") === "map" ? "map" : "list"; // deep-linkable
  const [mapMarkers, setMapMarkers] = useState([]);

  const setViewMode = (mode) => {
    const next = new URLSearchParams(params);
    if (mode === "map") next.set("view", "map"); else next.delete("view");
    setParams(next, { replace: true });
  };

  const filters = useMemo(() => ({
    operation: params.get("operation") || "sale",
    city: params.get("city") || "",
    property_type: params.get("property_type") || "",
    price_min: params.get("price_min") || "",
    price_max: params.get("price_max") || "",
    surface_min: params.get("surface_min") || "",
    rooms_min: params.get("rooms_min") || "",
    bedrooms_min: params.get("bedrooms_min") || "",
    energy_class: params.get("energy_class") || "",
    sort: params.get("sort") || "recent",
    page: parseInt(params.get("page") || "1"),
  }), [params]);

  useEffect(() => {
    setLoading(true);
    const qs = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => v && qs.set(k, v));
    qs.set("page_size", "20");
    api.get(`/cloud/search?${qs.toString()}`)
      .then((r) => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filters]);

  // M3.S3 — fetch map markers when switching to map view or filters change
  useEffect(() => {
    if (viewMode !== "map") return;
    const qs = new URLSearchParams();
    ["operation", "city", "property_type", "price_min", "price_max",
     "rooms_min", "bedrooms_min", "energy_class"].forEach((k) => {
      if (filters[k]) qs.set(k, filters[k]);
    });
    qs.set("limit", "500");
    api.get(`/cloud/map?${qs.toString()}`)
      .then((r) => setMapMarkers(r.data.items || []))
      .catch(() => setMapMarkers([]));
  }, [viewMode, filters]);

  const updateFilter = (k, v) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    next.delete("page");
    setParams(next);
  };

  const goToPage = (n) => {
    const next = new URLSearchParams(params);
    next.set("page", n);
    setParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <section className="px-5 sm:px-8 md:px-16 py-8 max-w-6xl mx-auto" data-testid="cloud-search-page">
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Filters sidebar */}
        <aside className="lg:w-64 flex-shrink-0 space-y-6">
          <h2 className="text-xs uppercase tracking-widest text-stone-500">
            {t("cloud.filters")}
          </h2>

          <FilterBlock label={t("cloud.f_operation")}>
            <SegSelect value={filters.operation} onChange={(v) => updateFilter("operation", v)}
              options={[
                { v: "sale", l: t("cloud.op_sale") },
                { v: "rent", l: t("cloud.op_rent") },
              ]} />
          </FilterBlock>

          <FilterBlock label={t("cloud.f_city")}>
            <input
              data-testid="filter-city" value={filters.city}
              onChange={(e) => updateFilter("city", e.target.value)}
              placeholder={t("cloud.search_placeholder")}
              className="w-full px-3 py-2 bg-white border border-stone-300 rounded text-sm"
            />
          </FilterBlock>

          <FilterBlock label={t("cloud.f_type")}>
            <select
              data-testid="filter-type"
              value={filters.property_type}
              onChange={(e) => updateFilter("property_type", e.target.value)}
              className="w-full px-3 py-2 bg-white border border-stone-300 rounded text-sm">
              <option value="">{t("cloud.any")}</option>
              {["appartamento", "casa", "villa", "loft", "attico", "monolocale", "ufficio"].map((tp) => (
                <option key={tp} value={tp}>{tp}</option>
              ))}
            </select>
          </FilterBlock>

          <FilterBlock label={t("cloud.f_price")}>
            <div className="flex gap-2">
              <input
                data-testid="filter-price-min" type="number" placeholder={t("cloud.min")}
                value={filters.price_min}
                onChange={(e) => updateFilter("price_min", e.target.value)}
                className="w-1/2 px-2 py-2 bg-white border border-stone-300 rounded text-sm"
              />
              <input
                data-testid="filter-price-max" type="number" placeholder={t("cloud.max")}
                value={filters.price_max}
                onChange={(e) => updateFilter("price_max", e.target.value)}
                className="w-1/2 px-2 py-2 bg-white border border-stone-300 rounded text-sm"
              />
            </div>
          </FilterBlock>

          <FilterBlock label={t("cloud.f_surface_min")}>
            <input
              data-testid="filter-surface-min" type="number" placeholder="m²"
              value={filters.surface_min}
              onChange={(e) => updateFilter("surface_min", e.target.value)}
              className="w-full px-3 py-2 bg-white border border-stone-300 rounded text-sm"
            />
          </FilterBlock>

          <FilterBlock label={t("cloud.f_rooms_min")}>
            <select
              data-testid="filter-rooms-min" value={filters.rooms_min}
              onChange={(e) => updateFilter("rooms_min", e.target.value)}
              className="w-full px-3 py-2 bg-white border border-stone-300 rounded text-sm">
              <option value="">{t("cloud.any")}</option>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}+</option>)}
            </select>
          </FilterBlock>

          <FilterBlock label={t("cloud.f_bedrooms_min")}>
            <select
              data-testid="filter-bedrooms-min" value={filters.bedrooms_min}
              onChange={(e) => updateFilter("bedrooms_min", e.target.value)}
              className="w-full px-3 py-2 bg-white border border-stone-300 rounded text-sm">
              <option value="">{t("cloud.any")}</option>
              {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}+</option>)}
            </select>
          </FilterBlock>

          <FilterBlock label={t("cloud.f_energy_class")}>
            <select
              data-testid="filter-energy-class" value={filters.energy_class}
              onChange={(e) => updateFilter("energy_class", e.target.value)}
              className="w-full px-3 py-2 bg-white border border-stone-300 rounded text-sm">
              <option value="">{t("cloud.any")}</option>
              {["A4", "A3", "A2", "A1", "A", "B", "C", "D", "E", "F", "G"].map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </FilterBlock>
        </aside>

        {/* Results */}
        <main className="flex-1 min-w-0">
          <div className="flex items-baseline justify-between flex-wrap gap-2 mb-6">
            <h1 className="text-2xl md:text-3xl font-light tracking-tight"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {filters.city ? t("cloud.results_in_city", { city: filters.city }) : t("cloud.all_results")}
            </h1>
            <div className="flex items-center gap-3">
              {/* M3.S3 — list/map view toggle */}
              <div className="inline-flex bg-white border border-stone-300 rounded overflow-hidden text-xs uppercase tracking-widest" role="tablist" aria-label="Vista risultati">
                <button
                  data-testid="view-toggle-list"
                  role="tab" aria-selected={viewMode === "list"}
                  onClick={() => setViewMode("list")}
                  className={`px-3 py-1.5 transition ${
                    viewMode === "list" ? "bg-[#0B1E3F] text-white" : "text-stone-600 hover:bg-stone-50"
                  }`}>
                  {t("cloud.view_list")}
                </button>
                <button
                  data-testid="view-toggle-map"
                  role="tab" aria-selected={viewMode === "map"}
                  onClick={() => setViewMode("map")}
                  className={`px-3 py-1.5 transition ${
                    viewMode === "map" ? "bg-[#0B1E3F] text-white" : "text-stone-600 hover:bg-stone-50"
                  }`}>
                  {t("cloud.view_map")}
                </button>
              </div>
              <select
                data-testid="filter-sort" value={filters.sort}
                onChange={(e) => updateFilter("sort", e.target.value)}
                className="px-3 py-1.5 bg-white border border-stone-300 rounded text-sm">
                <option value="recent">{t("cloud.sort_recent")}</option>
                <option value="price_asc">{t("cloud.sort_price_asc")}</option>
                <option value="price_desc">{t("cloud.sort_price_desc")}</option>
                <option value="surface_desc">{t("cloud.sort_surface_desc")}</option>
              </select>
            </div>
          </div>

          <p className="text-xs text-stone-500 mb-4" data-testid="results-count">
            {t("cloud.total_results", { n: data.total })}
          </p>

          <SaveSearchButton filters={filters} />

          {viewMode === "map" ? (
            <PropertyMapView markers={mapMarkers} />
          ) : loading ? (
            <p className="text-stone-500 text-sm" data-testid="search-loading">
              {t("common.loading")}
            </p>
          ) : data.items.length === 0 ? (
            <p className="text-stone-500 text-base py-12" data-testid="search-empty">
              {t("cloud.no_results")}
            </p>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="search-results-list">
                {data.items.map((p) => <PropertyCard key={p.id} p={p} />)}
              </div>
              {(data.has_next || data.page > 1) && (
                <div className="flex justify-center gap-2 mt-10" data-testid="pagination">
                  <button onClick={() => goToPage(data.page - 1)} disabled={data.page <= 1}
                    className="px-4 py-2 border border-stone-300 rounded disabled:opacity-30 hover:bg-stone-100 text-sm">
                    ← {t("cloud.prev")}
                  </button>
                  <span className="px-4 py-2 text-sm text-stone-600">
                    {t("cloud.page_of", { page: data.page, total: Math.ceil(data.total / 20) })}
                  </span>
                  <button onClick={() => goToPage(data.page + 1)} disabled={!data.has_next}
                    className="px-4 py-2 border border-stone-300 rounded disabled:opacity-30 hover:bg-stone-100 text-sm">
                    {t("cloud.next")} →
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </section>
  );
}

function FilterBlock({ label, children }) {
  return (
    <div>
      <label className="block text-[10px] uppercase tracking-widest text-stone-500 mb-1.5">{label}</label>
      {children}
    </div>
  );
}

function SegSelect({ value, onChange, options }) {
  return (
    <div className="flex bg-stone-100 rounded p-0.5">
      {options.map((o) => (
        <button key={o.v} type="button" onClick={() => onChange(o.v)}
          data-testid={`seg-${o.v}`}
          className={`flex-1 px-3 py-1.5 text-sm rounded transition ${
            value === o.v ? "bg-white text-stone-900 shadow-sm font-medium" : "text-stone-600"
          }`}>
          {o.l}
        </button>
      ))}
    </div>
  );
}

function SaveSearchButton({ filters }) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [freq, setFreq] = useState("daily");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");

  if (done) {
    return (
      <div data-testid="save-search-done" className="mb-4 text-xs text-emerald-700 bg-emerald-50 border border-emerald-200 rounded px-3 py-2">
        ✓ {t("cloud.save_search.done")}{" "}
        <Link to={`/${lang}/cloud/account`} className="underline">
          {t("cloud.save_search.go_dashboard")}
        </Link>
      </div>
    );
  }

  if (!open) {
    return (
      <button
        data-testid="save-search-open"
        onClick={() => {
          if (!user || user.account_type !== "b2c") {
            window.location.href = `/${lang}/cloud/register?intent=get_alerts`;
            return;
          }
          setOpen(true);
          setName(filters.city ? `${filters.city} — ${filters.operation === "rent" ? t("cloud.op_rent") : t("cloud.op_sale")}` : t("cloud.save_search.default_name"));
        }}
        className="mb-4 inline-flex items-center gap-2 px-4 py-2 text-xs uppercase tracking-widest border border-[#0B1E3F] text-[#0B1E3F] rounded hover:bg-[#0B1E3F] hover:text-white transition"
      >
        🔔 {t("cloud.save_search.cta")}
      </button>
    );
  }

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    const apiFilters = { ...filters };
    delete apiFilters.sort; delete apiFilters.page;
    Object.keys(apiFilters).forEach((k) => { if (!apiFilters[k]) delete apiFilters[k]; });
    ["price_min", "price_max", "surface_min", "rooms_min", "bedrooms_min", "bathrooms_min"].forEach((k) => {
      if (apiFilters[k]) apiFilters[k] = Number(apiFilters[k]);
    });
    try {
      await api.post("/cloud/me/saved-searches", { name, filters: apiFilters, frequency: freq });
      setDone(true);
    } catch (e) {
      setError(e?.response?.data?.detail === "saved_searches_limit_reached"
        ? t("cloud.save_search.err_limit")
        : t("cloud.save_search.err_generic"));
    } finally { setBusy(false); }
  };

  return (
    <form data-testid="save-search-form" onSubmit={submit} className="mb-4 bg-stone-50 border border-stone-200 rounded p-4 space-y-3">
      <h3 className="text-xs uppercase tracking-widest text-stone-500 font-medium">
        🔔 {t("cloud.save_search.title")}
      </h3>
      <input
        data-testid="save-search-name" required minLength={2} maxLength={120}
        value={name} onChange={(e) => setName(e.target.value)}
        placeholder={t("cloud.save_search.name_ph")}
        className="w-full px-3 py-2 border border-stone-300 rounded text-sm focus:outline-none focus:border-[#0B1E3F]"
      />
      <select
        data-testid="save-search-freq" value={freq} onChange={(e) => setFreq(e.target.value)}
        className="px-3 py-2 border border-stone-300 rounded text-sm"
      >
        <option value="instant">{t("cloud.account.freq_instant")}</option>
        <option value="daily">{t("cloud.account.freq_daily")}</option>
        <option value="weekly">{t("cloud.account.freq_weekly")}</option>
      </select>
      {error && <p className="text-xs text-rose-700">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={busy} data-testid="save-search-submit"
          className="px-4 py-2 bg-[#0B1E3F] text-white text-xs uppercase tracking-widest rounded hover:bg-[#C19A6B] disabled:opacity-50">
          {busy ? t("common.saving") : t("cloud.save_search.submit")}
        </button>
        <button type="button" onClick={() => setOpen(false)}
          className="px-4 py-2 border border-stone-300 text-xs uppercase tracking-widest rounded hover:bg-stone-50">
          {t("common.cancel")}
        </button>
      </div>
    </form>
  );
}
