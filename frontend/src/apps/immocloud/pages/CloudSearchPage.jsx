import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth } from "../../../shared/lib/auth";
import PropertyMapView, { boundsToBboxParam } from "../components/PropertyMapView";
import PropertyCard from "../components/PropertyCard";
import CloudPageHero from "../components/CloudPageHero";
import { FIELD, BTN_PRIMARY, formatEUR } from "../cloudTheme";
import { ENERGY_CLASS_LETTER_OPTIONS } from "../../../shared/lib/energyClasses";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function CloudSearchPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [params, setParams] = useSearchParams();
  const [data, setData] = useState({ items: [], total: 0, has_next: false, page: 1 });
  const [loading, setLoading] = useState(false);
  const viewMode = params.get("view") === "map" ? "map" : "list";
  const [mapMarkers, setMapMarkers] = useState([]);
  const [mapLoading, setMapLoading] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [pendingBounds, setPendingBounds] = useState(null);
  const [areaDirty, setAreaDirty] = useState(false);
  const listRef = useRef(null);
  const initialFitDone = useRef(false);

  const setViewMode = (mode) => {
    const next = new URLSearchParams(params);
    if (mode === "map") next.set("view", "map");
    else {
      next.delete("view");
      next.delete("bbox");
    }
    setParams(next, { replace: true });
    setAreaDirty(false);
    setPendingBounds(null);
    initialFitDone.current = false;
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
    page: parseInt(params.get("page") || "1", 10),
    mls: params.get("mls") === "1",
    near_me: params.get("near_me") === "1",
    radius_km: params.get("radius_km") || "5",
    bbox: params.get("bbox") || "",
  }), [params]);

  const [advOpen, setAdvOpen] = useState(Boolean(filters.cities || filters.near_me));
  const [geoErr, setGeoErr] = useState("");

  const appendCommonFilters = useCallback((qs, { includeCity = true, includeBbox = true } = {}) => {
    ["operation", "property_type", "price_min", "price_max",
      "rooms_min", "bedrooms_min", "energy_class", "surface_min"].forEach((k) => {
      if (filters[k]) qs.set(k, filters[k]);
    });
    if (includeBbox && filters.bbox) qs.set("bbox", filters.bbox);
    if (includeCity && !filters.bbox && filters.city) qs.set("city", filters.city);
  }, [filters]);

  // Lista (list mode + map mode con bbox/filtri)
  useEffect(() => {
    setLoading(true);
    const page = filters.page || 1;

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

    const cityList = (filters.cities || "")
      .split(",")
      .map((c) => c.trim())
      .filter(Boolean);
    const useAdvanced = !filters.bbox && (cityList.length > 1 || filters.near_me);

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
        page_size: viewMode === "map" ? 40 : 20,
        cities: cityList.length ? cityList : (filters.city ? [filters.city] : undefined),
        compare_prices: true,
      };
      const run = (near) => {
        if (near) body.near_me = near;
        api.post("/cloud/search/advanced", body)
          .then((r) => {
            const payload = r?.data && typeof r.data === "object" && !Array.isArray(r.data) ? r.data : {};
            setData({
              items: Array.isArray(payload.items) ? payload.items : [],
              total: Number(payload.total) || 0,
              page: Number(payload.page) || page,
              has_next: Boolean(payload.has_next),
              source: "advanced",
            });
          })
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
      if (k === "city" && filters.bbox) return;
      if (v) qs.set(k, v);
    });
    qs.set("page_size", viewMode === "map" ? "40" : "20");
    api.get(`/cloud/search?${qs.toString()}`)
      .then((r) => {
        const payload = r?.data && typeof r.data === "object" && !Array.isArray(r.data) ? r.data : {};
        setData({
          items: Array.isArray(payload.items) ? payload.items : [],
          total: Number(payload.total) || 0,
          page: Number(payload.page) || page,
          has_next: Boolean(payload.has_next),
          sort: payload.sort,
          source: "cloud",
        });
      })
      .catch(() => setData({ items: [], total: 0, has_next: false, page: 1 }))
      .finally(() => setLoading(false));
  }, [filters, viewMode]);

  // Marker mappa
  useEffect(() => {
    if (viewMode !== "map") return;
    setMapLoading(true);
    const qs = new URLSearchParams();
    appendCommonFilters(qs, { includeCity: !filters.bbox, includeBbox: true });
    qs.set("limit", "500");
    api.get(`/cloud/map?${qs.toString()}`)
      .then((r) => setMapMarkers(r.data.items || []))
      .catch(() => setMapMarkers([]))
      .finally(() => setMapLoading(false));
  }, [viewMode, filters, appendCommonFilters]);

  // Scroll lista → card selezionata
  useEffect(() => {
    if (!selectedId || !listRef.current) return;
    const el = listRef.current.querySelector(`[data-map-row="${selectedId}"]`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [selectedId]);

  const updateFilter = (k, v) => {
    const next = new URLSearchParams(params);
    if (v) next.set(k, v); else next.delete(k);
    next.delete("page");
    // Cambio filtri classici → reset area mappa
    if (k !== "bbox" && k !== "sort" && k !== "page") {
      next.delete("bbox");
      setAreaDirty(false);
      setPendingBounds(null);
      initialFitDone.current = false;
    }
    setParams(next);
  };

  const applyAreaSearch = () => {
    if (!pendingBounds) return;
    const bbox = boundsToBboxParam(pendingBounds);
    const next = new URLSearchParams(params);
    next.set("view", "map");
    next.set("bbox", bbox);
    next.delete("page");
    // Area vince sulla città (come Idealista)
    next.delete("city");
    setParams(next);
    setAreaDirty(false);
    initialFitDone.current = true; // non rifare fitBounds dopo ricerca area
  };

  const onBoundsIdle = (b) => {
    setPendingBounds(b);
    if (initialFitDone.current || filters.bbox) {
      setAreaDirty(true);
    } else {
      // Primo fit completato: memorizza bounds senza chiedere subito
      initialFitDone.current = true;
    }
  };

  const goToPage = (n) => {
    const next = new URLSearchParams(params);
    next.set("page", n);
    setParams(next);
    if (viewMode !== "map") window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const heroTitle = filters.city
    ? t("cloud.results_in_city", { city: filters.city })
    : t("cloud.all_results");

  const filterSidebar = (
    <div className="space-y-4">
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

      {!filters.bbox && (
        <FilterBlock label={t("cloud.f_city")}>
          <input
            data-testid="filter-city"
            value={filters.city}
            onChange={(e) => updateFilter("city", e.target.value)}
            placeholder={t("cloud.search_placeholder")}
            className={FIELD}
          />
        </FilterBlock>
      )}
      {filters.bbox && (
        <p className="text-xs text-stone-500" data-testid="map-area-active">
          {t("cloud.map_area_active", "Ricerca sull’area della mappa")}
        </p>
      )}

      <button
        type="button"
        data-testid="toggle-advanced-search"
        onClick={() => setAdvOpen((v) => !v)}
        className="text-[10px] uppercase tracking-widest text-[#0B1E3F] hover:text-[#C19A6B]"
      >
        {advOpen ? "Nascondi avanzata" : "Ricerca avanzata"}
      </button>

      {advOpen && (
        <div className="space-y-3 rounded-xl bg-white/80 border border-stone-200 p-3" data-testid="advanced-search-panel">
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

      <FilterBlock label={t("cloud.f_energy_class")}>
        <select
          data-testid="filter-energy-class"
          value={filters.energy_class}
          onChange={(e) => updateFilter("energy_class", e.target.value)}
          className={FIELD}
        >
          <option value="">{t("cloud.any")}</option>
          {ENERGY_CLASS_LETTER_OPTIONS.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
      </FilterBlock>
    </div>
  );

  const viewToggle = (
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
  );

  /* ——— Idealista-like map flow ——— */
  if (viewMode === "map") {
    return (
      <div
        data-testid="cloud-search-page"
        className="bg-[#f7f4ef] flex flex-col"
        style={{ height: "calc(100dvh - 4.5rem)", minHeight: 520 }}
      >
        {/* Toolbar */}
        <div className="shrink-0 border-b border-stone-200 bg-white px-4 sm:px-6 py-3 flex flex-wrap items-center gap-3 justify-between z-20">
          <div className="flex items-center gap-3 min-w-0">
            <p className="text-sm text-stone-700 truncate" data-testid="results-count">
              {loading || mapLoading
                ? t("common.loading")
                : t("cloud.total_results", { n: data.total })}
            </p>
            {viewToggle}
          </div>
          <div className="flex items-center gap-2">
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
            <SaveSearchButton filters={filters} compact />
          </div>
        </div>

        <div className="flex-1 min-h-0 flex flex-col lg:flex-row">
          {/* Left: filters + list */}
          <aside
            className="lg:w-[400px] xl:w-[440px] shrink-0 border-r border-stone-200 bg-white flex flex-col min-h-0 max-h-[42vh] lg:max-h-none"
            data-testid="map-side-panel"
          >
            <div className="shrink-0 px-4 pt-4 pb-2 border-b border-stone-100">
              <p className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B] mb-3">
                {t("cloud.filters")}
              </p>
              <div className="max-h-40 overflow-y-auto pr-1">{filterSidebar}</div>
            </div>
            <div ref={listRef} className="flex-1 overflow-y-auto" data-testid="map-results-list">
              {loading ? (
                <p className="p-6 text-sm text-stone-500">{t("common.loading")}</p>
              ) : !(data.items || []).length ? (
                <div className="p-6 text-center" data-testid="search-empty">
                  <p className="text-[#0B1E3F] font-light text-lg" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                    {t("cloud.map_no_in_area", "Nessuna casa in quest’area")}
                  </p>
                  <p className="text-sm text-stone-500 mt-2">{t("cloud.no_results")}</p>
                </div>
              ) : (
                <ul className="divide-y divide-stone-100">
                  {(data.items || []).map((p) => (
                    <li key={p.id}>
                      <MapListRow
                        p={p}
                        lang={lang}
                        selected={selectedId === p.id}
                        onSelect={() => setSelectedId(p.id)}
                      />
                    </li>
                  ))}
                </ul>
              )}
              {(data.has_next || data.page > 1) && (
                <div className="flex justify-center gap-2 py-4 border-t border-stone-100" data-testid="pagination">
                  <button
                    type="button"
                    onClick={() => goToPage(data.page - 1)}
                    disabled={data.page <= 1}
                    className="px-3 py-1.5 border border-stone-200 rounded-lg disabled:opacity-30 text-sm"
                  >
                    ←
                  </button>
                  <span className="px-2 py-1.5 text-xs text-stone-600">
                    {data.page}
                  </span>
                  <button
                    type="button"
                    onClick={() => goToPage(data.page + 1)}
                    disabled={!data.has_next}
                    className="px-3 py-1.5 border border-stone-200 rounded-lg disabled:opacity-30 text-sm"
                  >
                    →
                  </button>
                </div>
              )}
            </div>
          </aside>

          {/* Right: map */}
          <div className="relative flex-1 min-h-[48vh] lg:min-h-0" data-testid="map-stage">
            <PropertyMapView
              markers={mapMarkers}
              selectedId={selectedId}
              onSelect={setSelectedId}
              onBoundsIdle={onBoundsIdle}
              fitOnLoad={!filters.bbox}
              bbox={filters.bbox}
              heightClass="h-full"
            />
            {areaDirty && (
              <button
                type="button"
                data-testid="map-search-area"
                onClick={applyAreaSearch}
                className="absolute top-4 left-1/2 -translate-x-1/2 z-[500] px-5 py-2.5 rounded-full bg-[#0B1E3F] text-white text-xs uppercase tracking-widest shadow-lg hover:bg-[#C19A6B] transition"
              >
                {t("cloud.map_search_area", "Cerca in questa zona")}
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  /* ——— List mode (invariato nel layout) ——— */
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
          <aside className="lg:w-72 flex-shrink-0">
            <div className="rounded-2xl bg-[#f7f4ef] border border-stone-200/80 p-5 space-y-5 lg:sticky lg:top-24">
              <h2 className="text-[11px] uppercase tracking-[0.28em] text-[#C19A6B]">
                {t("cloud.filters")}
              </h2>
              {filterSidebar}
            </div>
          </aside>

          <main className="flex-1 min-w-0">
            <div className="flex items-center justify-between flex-wrap gap-3 mb-5">
              <p className="text-sm text-stone-600" data-testid="results-count">
                {t("cloud.total_results", { n: data.total })}
              </p>
              <div className="flex items-center gap-2">
                {viewToggle}
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

            {loading ? (
              <div
                className="rounded-2xl bg-[#f7f4ef] border border-stone-200 px-6 py-16 text-center"
                data-testid="search-loading"
              >
                <p className="text-stone-500 text-sm">{t("common.loading")}</p>
              </div>
            ) : !(data.items || []).length ? (
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
                  {(data.items || []).map((p) => <PropertyCard key={p.id} p={p} />)}
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

function MapListRow({ p, lang, selected, onSelect }) {
  const { t } = useTranslation();
  const cover = p.cover_url ? `${BACKEND_URL}${p.cover_url}` : null;
  const price = p.operation === "rent"
    ? `${formatEUR(p.rent_monthly)}/mese`
    : formatEUR(p.price);

  return (
    <div
      data-map-row={p.id}
      data-testid={`map-row-${p.id}`}
      className={`flex gap-3 p-3 cursor-pointer transition ${
        selected ? "bg-[#f7f4ef] ring-1 ring-inset ring-[#C19A6B]" : "hover:bg-stone-50"
      }`}
      onMouseEnter={onSelect}
      onClick={onSelect}
      onKeyDown={(e) => { if (e.key === "Enter") onSelect(); }}
      role="button"
      tabIndex={0}
    >
      <div className="w-24 h-20 shrink-0 rounded-lg overflow-hidden bg-stone-100">
        {cover ? (
          <img src={cover} alt="" className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-stone-300 text-2xl">⌂</div>
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-base font-semibold text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          {price}
        </p>
        <p className="text-sm text-stone-800 line-clamp-1">{p.title}</p>
        <p className="text-xs text-stone-500 mt-0.5">
          {p.city}{p.zone ? ` · ${p.zone}` : ""}
          {p.surface_sqm ? ` · ${p.surface_sqm} m²` : ""}
        </p>
        <Link
          to={`/${lang}/cloud/property/${p.id}`}
          className="text-[10px] uppercase tracking-widest text-[#C19A6B] hover:underline mt-1 inline-block"
          onClick={(e) => e.stopPropagation()}
        >
          {t("cloud.view_detail")} →
        </Link>
      </div>
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

function SaveSearchButton({ filters, compact = false }) {
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
      <div data-testid="save-search-done" className={`${compact ? "" : "mb-4"} text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2`}>
        ✓ {t("cloud.save_search.done")}
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
        className={`${compact ? "" : "mb-5"} inline-flex items-center gap-2 px-3 py-2 text-[10px] uppercase tracking-widest border border-[#0B1E3F] text-[#0B1E3F] rounded-lg hover:bg-[#0B1E3F] hover:text-white transition`}
      >
        {t("cloud.save_search.cta")}
      </button>
    );
  }

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setError("");
    const apiFilters = { ...filters };
    delete apiFilters.sort; delete apiFilters.page; delete apiFilters.bbox;
    Object.keys(apiFilters).forEach((k) => { if (!apiFilters[k]) delete apiFilters[k]; });
    ["price_min", "price_max", "surface_min", "rooms_min", "bedrooms_min", "bathrooms_min"].forEach((k) => {
      if (apiFilters[k]) apiFilters[k] = Number(apiFilters[k]);
    });
    try {
      await api.post("/cloud/me/saved-searches", { name, filters: apiFilters, frequency: freq });
      setDone(true);
    } catch (err) {
      setError(err?.response?.data?.detail === "saved_searches_limit_reached"
        ? t("cloud.save_search.err_limit")
        : t("cloud.save_search.err_generic"));
    } finally { setBusy(false); }
  };

  return (
    <form data-testid="save-search-form" onSubmit={submit} className={`${compact ? "absolute right-4 top-14 z-[600] w-72 shadow-xl" : "mb-5"} bg-[#f7f4ef] border border-stone-200 rounded-2xl p-4 space-y-3`}>
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
