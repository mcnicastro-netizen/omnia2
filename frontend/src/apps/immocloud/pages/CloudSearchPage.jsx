import React, { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth } from "../../../shared/lib/auth";
import PropertyMapView from "../components/PropertyMapView";
import PropertyCard from "../components/PropertyCard";
import CloudPageHero from "../components/CloudPageHero";
import { FIELD, BTN_PRIMARY } from "../cloudTheme";

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
    cities: params.get("cities") || "",
    province: params.get("province") || "",
    property_type: params.get("property_type") || "",
    price_min: params.get("price_min") || "",
    price_max: params.get("price_max") || "",
    surface_min: params.get("surface_min") || "",
    rooms_min: params.get("rooms_min") || "",
    bedrooms_min: params.get("bedrooms_min") || "",
    energy_class: params.get("energy_class") || "",
    sort: params.get("sort") || "recent",
    page: parseInt(params.get("page") || "1"),
    mls: params.get("mls") === "1",
    near_me: params.get("near_me") === "1",
    radius_km: params.get("radius_km") || "5",
  }), [params]);

  const [advOpen, setAdvOpen] = useState(Boolean(filters.cities || filters.near_me));
  const [geoErr, setGeoErr] = useState("");

  useEffect(() => {
    setLoading(true);
    const page = filters.page || 1;

    // MLS network path (home dual-box)
    if (filters.mls) {
      const qs = new URLSearchParams();
      if (filters.operation) qs.set("operation", filters.operation);
      if (filters.province) qs.set("province", filters.province);
      if (filters.city) qs.set("city", filters.city);
      if (filters.price_min) qs.set("price_min", filters.price_min);
      if (filters.price_max) qs.set("price_max", filters.price_max);
      qs.set("limit", "20");
      qs.set("skip", String((page - 1) * 20));
      api.get(`/app/mls/search/public?${qs.toString()}`)
        .then((r) => {
          const items = (r.data.items || []).map((p) => ({
            ...p,
            surface_sqm: p.sqm || p.surface_sqm,
            cover_photo_url: p.cover_url,
          }));
          const total = r.data.total || items.length;
          setData({
            items,
            total,
            page,
            has_next: page * 20 < total,
            source: "mls",
            claim: r.data.claim,
          });
        })
        .catch(() => setData({ items: [], total: 0, has_next: false, page: 1 }))
        .finally(() => setLoading(false));
      return;
    }

    // Advanced: multi-city / near-me
    const cityList = (filters.cities || "")
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);
    const useAdvanced = cityList.length > 1 || filters.near_me;

    if (useAdvanced) {
      const body = {
        operation: filters.operation || "sale",
        property_types: filters.property_type ? [filters.property_type] : undefined,
        price_min: filters.price_min ? Number(filters.price_min) : undefined,
        price_max: filters.price_max ? Number(filters.price_max) : undefined,
        surface_min: filters.surface_min ? Number(filters.surface_min) : undefined,
        rooms_min: filters.rooms_min ? Number(filters.rooms_min) : undefined,
        bedrooms_min: filters.bedrooms_min ? Number(filters.bedrooms_min) : undefined,
        energy_class: filters.energy_class || undefined,
        sort: filters.sort || "recent",
        page,
        page_size: 20,
        cities: cityList.length ? cityList : (filters.city ? [filters.city] : undefined),
        compare_prices: true,
      };
      const run = (near) => {
        if (near) body.near_me = near;
        api.post("/cloud/search/advanced", body)
          .then((r) => setData({ ...r.data, source: "advanced" }))
          .catch(() => setData({ items: [], total: 0, has_next: false, page: 1 }))
          .finally(() => setLoading(false));
      };
      if (filters.near_me) {
        if (!navigator.geolocation) {
          setGeoErr("Geolocalizzazione non disponibile");
          setLoading(false);
          return;
        }
        navigator.geolocation.getCurrentPosition(
          (pos) => run({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            radius_km: Number(filters.radius_km) || 5,
          }),
          () => {
            setGeoErr("Permesso posizione negato");
            setLoading(false);
          },
          { timeout: 8000 },
        );
      } else {
        run(null);
      }
      return;
    }

    const qs = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => {
      if (["mls", "near_me", "radius_km", "cities", "province"].includes(k)) return;
      if (v) qs.set(k, v);
    });
    qs.set("page_size", "20");
    api.get(`/cloud/search?${qs.toString()}`)
      .then((r) => setData({ ...r.data, source: "cloud" }))
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

  const heroTitle = filters.city
    ? t("cloud.results_in_city", { city: filters.city })
    : t("cloud.all_results");

  return (
    <div data-testid="cloud-search-page">
      <CloudPageHero
        eyebrow="ImmobilCloud · Cerca"
        title={heroTitle}
        subtitle="Affina i filtri. Apri un annuncio. Lascia che Scout ti sussurri cosa chiedere."
        image="/cloud/living.jpg"
        compact
      />

      <section className="px-5 sm:px-8 md:px-16 py-10 max-w-6xl mx-auto">
        <div className="flex flex-col lg:flex-row gap-8 lg:gap-10">
          {/* Filters sidebar */}
          <aside className="lg:w-72 flex-shrink-0">
            <div className="rounded-2xl bg-[#f7f4ef] border border-stone-200/80 p-5 space-y-5 lg:sticky lg:top-24">
              <h2 className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B]">
                {t("cloud.filters")}
              </h2>

              <FilterBlock label={t("cloud.f_operation")}>
                <SegSelect
                  value={filters.operation}
                  onChange={(v) => updateFilter("operation", v)}
                  options={[
                    { v: "sale", l: t("cloud.op_sale") },
                    { v: "rent", l: t("cloud.op_rent") },
                  ]}
                />
              </FilterBlock>

              <FilterBlock label={t("cloud.f_city")}>
                <input
                  data-testid="filter-city"
                  value={filters.city}
                  onChange={(e) => updateFilter("city", e.target.value)}
                  placeholder={t("cloud.search_placeholder")}
                  className={FIELD}
                />
              </FilterBlock>

              <button
                type="button"
                data-testid="toggle-advanced-search"
                onClick={() => setAdvOpen((v) => !v)}
                className="text-[10px] uppercase tracking-widest text-[#0B1E3F] hover:text-[#C19A6B]"
              >
                {advOpen ? "Nascondi avanzata" : "Ricerca avanzata"}
              </button>

              {advOpen && (
                <div className="space-y-4 rounded-xl bg-white/80 border border-stone-200 p-3" data-testid="advanced-search-panel">
                  <FilterBlock label="Multi-città (virgola)">
                    <input
                      data-testid="filter-cities"
                      value={filters.cities}
                      onChange={(e) => updateFilter("cities", e.target.value)}
                      placeholder="Catania, Milano, Roma"
                      className={FIELD}
                    />
                  </FilterBlock>
                  <label className="flex items-center gap-2 text-sm text-stone-700">
                    <input
                      type="checkbox"
                      data-testid="filter-near-me"
                      checked={filters.near_me}
                      onChange={(e) => updateFilter("near_me", e.target.checked ? "1" : "")}
                    />
                    Vicino a me
                  </label>
                  {filters.near_me && (
                    <FilterBlock label="Raggio km">
                      <input
                        type="number"
                        min={1}
                        max={50}
                        value={filters.radius_km}
                        onChange={(e) => updateFilter("radius_km", e.target.value)}
                        className={FIELD}
                      />
                    </FilterBlock>
                  )}
                  {filters.mls && (
                    <p className="text-xs text-emerald-800">Modalità MLS network attiva</p>
                  )}
                  {geoErr && <p className="text-xs text-red-600">{geoErr}</p>}
                </div>
              )}

              <FilterBlock label={t("cloud.f_type")}>
                <select
                  data-testid="filter-type"
                  value={filters.property_type}
                  onChange={(e) => updateFilter("property_type", e.target.value)}
                  className={FIELD}
                >
                  <option value="">{t("cloud.any")}</option>
                  {["appartamento", "casa", "villa", "loft", "attico", "monolocale", "ufficio"].map((tp) => (
                    <option key={tp} value={tp}>{tp}</option>
                  ))}
                </select>
              </FilterBlock>

              <FilterBlock label={t("cloud.f_price")}>
                <div className="flex gap-2">
                  <input
                    data-testid="filter-price-min"
                    type="number"
                    placeholder={t("cloud.min")}
                    value={filters.price_min}
                    onChange={(e) => updateFilter("price_min", e.target.value)}
                    className={`w-1/2 ${FIELD}`}
                  />
                  <input
                    data-testid="filter-price-max"
                    type="number"
                    placeholder={t("cloud.max")}
                    value={filters.price_max}
                    onChange={(e) => updateFilter("price_max", e.target.value)}
                    className={`w-1/2 ${FIELD}`}
                  />
                </div>
              </FilterBlock>

              <FilterBlock label={t("cloud.f_surface_min")}>
                <input
                  data-testid="filter-surface-min"
                  type="number"
                  placeholder="m²"
                  value={filters.surface_min}
                  onChange={(e) => updateFilter("surface_min", e.target.value)}
                  className={FIELD}
                />
              </FilterBlock>

              <FilterBlock label={t("cloud.f_rooms_min")}>
                <select
                  data-testid="filter-rooms-min"
                  value={filters.rooms_min}
                  onChange={(e) => updateFilter("rooms_min", e.target.value)}
                  className={FIELD}
                >
                  <option value="">{t("cloud.any")}</option>
                  {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}+</option>)}
                </select>
              </FilterBlock>

              <FilterBlock label={t("cloud.f_bedrooms_min")}>
                <select
                  data-testid="filter-bedrooms-min"
                  value={filters.bedrooms_min}
                  onChange={(e) => updateFilter("bedrooms_min", e.target.value)}
                  className={FIELD}
                >
                  <option value="">{t("cloud.any")}</option>
                  {[1, 2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}+</option>)}
                </select>
              </FilterBlock>

              <FilterBlock label={t("cloud.f_energy_class")}>
                <select
                  data-testid="filter-energy-class"
                  value={filters.energy_class}
                  onChange={(e) => updateFilter("energy_class", e.target.value)}
                  className={FIELD}
                >
                  <option value="">{t("cloud.any")}</option>
                  {["A4", "A3", "A2", "A1", "A", "B", "C", "D", "E", "F", "G"].map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </FilterBlock>
            </div>
          </aside>

          {/* Results */}
          <main className="flex-1 min-w-0">
            <div className="flex items-center justify-between flex-wrap gap-3 mb-5">
              <p className="text-sm text-stone-600" data-testid="results-count">
                {t("cloud.total_results", { n: data.total })}
              </p>
              <div className="flex items-center gap-2">
                <div
                  className="inline-flex bg-white border border-stone-200 rounded-lg overflow-hidden text-[10px] uppercase tracking-widest"
                  role="tablist"
                  aria-label="Vista risultati"
                >
                  <button
                    data-testid="view-toggle-list"
                    role="tab"
                    aria-selected={viewMode === "list"}
                    onClick={() => setViewMode("list")}
                    className={`px-3 py-2 transition ${
                      viewMode === "list" ? "bg-[#0B1E3F] text-white" : "text-stone-600 hover:bg-stone-50"
                    }`}
                  >
                    {t("cloud.view_list")}
                  </button>
                  <button
                    data-testid="view-toggle-map"
                    role="tab"
                    aria-selected={viewMode === "map"}
                    onClick={() => setViewMode("map")}
                    className={`px-3 py-2 transition ${
                      viewMode === "map" ? "bg-[#0B1E3F] text-white" : "text-stone-600 hover:bg-stone-50"
                    }`}
                  >
                    {t("cloud.view_map")}
                  </button>
                </div>
                <select
                  data-testid="filter-sort"
                  value={filters.sort}
                  onChange={(e) => updateFilter("sort", e.target.value)}
                  className="px-3 py-2 bg-white border border-stone-200 rounded-lg text-sm"
                >
                  <option value="recent">{t("cloud.sort_recent")}</option>
                  <option value="price_asc">{t("cloud.sort_price_asc")}</option>
                  <option value="price_desc">{t("cloud.sort_price_desc")}</option>
                  <option value="surface_desc">{t("cloud.sort_surface_desc")}</option>
                </select>
              </div>
            </div>

            <SaveSearchButton filters={filters} />

            {viewMode === "map" ? (
              <div className="rounded-2xl overflow-hidden border border-stone-200">
                <PropertyMapView markers={mapMarkers} />
              </div>
            ) : loading ? (
              <div
                className="rounded-2xl bg-[#f7f4ef] border border-stone-200 px-6 py-16 text-center"
                data-testid="search-loading"
              >
                <p className="text-stone-500 text-sm">{t("common.loading")}</p>
              </div>
            ) : data.items.length === 0 ? (
              <div
                className="rounded-2xl bg-[#f7f4ef] border border-stone-200 px-6 py-16 text-center"
                data-testid="search-empty"
              >
                <p
                  className="text-2xl text-[#0B1E3F] mb-2 font-light"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  Nessuna casa qui
                </p>
                <p className="text-stone-600 text-sm max-w-sm mx-auto">
                  {t("cloud.no_results")} Prova a allargare città o budget — Scout aspetta il prossimo annuncio.
                </p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6" data-testid="search-results-list">
                  {data.items.map((p) => <PropertyCard key={p.id} p={p} />)}
                </div>
                {(data.has_next || data.page > 1) && (
                  <div className="flex justify-center gap-2 mt-10" data-testid="pagination">
                    <button
                      onClick={() => goToPage(data.page - 1)}
                      disabled={data.page <= 1}
                      className="px-4 py-2 border border-stone-200 rounded-lg disabled:opacity-30 hover:bg-[#f7f4ef] text-sm"
                    >
                      ← {t("cloud.prev")}
                    </button>
                    <span className="px-4 py-2 text-sm text-stone-600">
                      {t("cloud.page_of", { page: data.page, total: Math.ceil(data.total / 20) })}
                    </span>
                    <button
                      onClick={() => goToPage(data.page + 1)}
                      disabled={!data.has_next}
                      className="px-4 py-2 border border-stone-200 rounded-lg disabled:opacity-30 hover:bg-[#f7f4ef] text-sm"
                    >
                      {t("cloud.next")} →
                    </button>
                  </div>
                )}
              </>
            )}
          </main>
        </div>
      </section>
    </div>
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
    <div className="flex bg-white border border-stone-200 rounded-lg p-0.5">
      {options.map((o) => (
        <button
          key={o.v}
          type="button"
          onClick={() => onChange(o.v)}
          data-testid={`seg-${o.v}`}
          className={`flex-1 px-3 py-2 text-sm rounded-md transition ${
            value === o.v
              ? "bg-[#0B1E3F] text-white font-medium"
              : "text-stone-600 hover:bg-stone-50"
          }`}
        >
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
      <div data-testid="save-search-done" className="mb-4 text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-3">
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
        className="mb-5 inline-flex items-center gap-2 px-4 py-2.5 text-xs uppercase tracking-widest border border-[#0B1E3F] text-[#0B1E3F] rounded-lg hover:bg-[#0B1E3F] hover:text-white transition"
      >
        {t("cloud.save_search.cta")}
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
    <form data-testid="save-search-form" onSubmit={submit} className="mb-5 bg-[#f7f4ef] border border-stone-200 rounded-2xl p-5 space-y-3">
      <h3 className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B] font-medium">
        {t("cloud.save_search.title")}
      </h3>
      <input
        data-testid="save-search-name" required minLength={2} maxLength={120}
        value={name} onChange={(e) => setName(e.target.value)}
        placeholder={t("cloud.save_search.name_ph")}
        className={`${FIELD} focus:outline-none`}
      />
      <select
        data-testid="save-search-freq" value={freq} onChange={(e) => setFreq(e.target.value)}
        className={FIELD}
      >
        <option value="instant">{t("cloud.account.freq_instant")}</option>
        <option value="daily">{t("cloud.account.freq_daily")}</option>
        <option value="weekly">{t("cloud.account.freq_weekly")}</option>
      </select>
      {error && <p className="text-xs text-rose-700">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={busy} data-testid="save-search-submit"
          className={BTN_PRIMARY}>
          {busy ? t("common.saving") : t("cloud.save_search.submit")}
        </button>
        <button type="button" onClick={() => setOpen(false)}
          className="px-4 py-2.5 border border-stone-200 text-xs uppercase tracking-widest rounded-lg hover:bg-white">
          {t("common.cancel")}
        </button>
      </div>
    </form>
  );
}
