import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

const STATUSES = ["", "draft", "active", "reserved", "sold", "rented", "withdrawn"];
const OPS = ["", "sale", "rent", "rent_to_buy", "auction"];
const SMART = [
  { id: "", label: "Tutti" },
  { id: "no_photos", label: "Senza foto" },
  { id: "incomplete", label: "Incompleti" },
  { id: "weak_copy", label: "Testo debole" },
  { id: "no_match", label: "Senza match" },
  { id: "price_drop", label: "Ribasso recente" },
];
const SORTS = [
  { id: "updated_desc", label: "Aggiornati ↓" },
  { id: "updated_asc", label: "Aggiornati ↑" },
  { id: "price_desc", label: "Prezzo ↓" },
  { id: "price_asc", label: "Prezzo ↑" },
  { id: "surface_desc", label: "Superficie ↓" },
  { id: "created_desc", label: "Creati ↓" },
];

function formatPrice(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(v);
}

function FlagChips({ flags }) {
  if (!flags?.length) return null;
  const map = {
    no_photos: "Senza foto",
    incomplete: "Incompleto",
    weak_copy: "Testo debole",
    no_match: "Senza match",
    price_drop: "Ribasso",
  };
  return (
    <span className="flex flex-wrap gap-1">
      {flags.map((f) => (
        <span
          key={f}
          className="text-[9px] uppercase tracking-widest px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200"
        >
          {map[f] || f}
        </span>
      ))}
    </span>
  );
}

export default function PropertiesPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 20 });
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState(() => {
    const s = searchParams.get("status") || "";
    return STATUSES.includes(s) ? s : "";
  });
  const [operation, setOperation] = useState("");
  const [smart, setSmart] = useState(() => searchParams.get("smart") || "");
  const [sort, setSort] = useState(() => searchParams.get("sort") || "updated_desc");
  const [view, setView] = useState(() => {
    const v = searchParams.get("view") || localStorage.getItem("omnia_props_view") || "cards";
    return v === "table" ? "table" : "cards";
  });

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (status) params.set("status", status);
      if (operation) params.set("operation", operation);
      if (smart) params.set("smart", smart);
      if (sort) params.set("sort", sort);
      const { data: res } = await api.get(`/app/properties?${params.toString()}`);
      setData(res);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const next = new URLSearchParams();
    if (status) next.set("status", status);
    if (smart) next.set("smart", smart);
    if (sort && sort !== "updated_desc") next.set("sort", sort);
    if (view === "table") next.set("view", "table");
    setSearchParams(next, { replace: true });
    localStorage.setItem("omnia_props_view", view);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, smart, sort, view]);

  const onSearch = (e) => {
    e.preventDefault();
    load();
  };

  const openProp = (id) => nav(`/${lang}/app/properties/${id}`);

  return (
    <AgencyShell current="properties">
      <section data-testid="properties-page" className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1
              className="text-3xl md:text-4xl tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("properties.title")}
            </h1>
            <p className="text-stone-600 mt-1">{t("properties.subtitle")}</p>
          </div>
          <div className="flex gap-3 flex-wrap">
            <div
              className="inline-flex border border-stone-300 rounded-md overflow-hidden"
              data-testid="properties-view-toggle"
            >
              <button
                type="button"
                data-testid="view-cards"
                onClick={() => setView("cards")}
                className={`px-3 py-2 text-[10px] uppercase tracking-widest ${
                  view === "cards" ? "bg-stone-900 text-white" : "bg-white text-stone-700"
                }`}
              >
                Card
              </button>
              <button
                type="button"
                data-testid="view-table"
                onClick={() => setView("table")}
                className={`px-3 py-2 text-[10px] uppercase tracking-widest ${
                  view === "table" ? "bg-stone-900 text-white" : "bg-white text-stone-700"
                }`}
              >
                Tabella
              </button>
            </div>
            <Link
              to={`/${lang}/app/properties/import`}
              data-testid="properties-import-btn"
              className="px-4 py-2.5 border border-stone-300 bg-white text-stone-900 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-50 transition"
            >
              {t("properties.import_btn")}
            </Link>
            <Link
              to={`/${lang}/app/properties/new`}
              data-testid="properties-new-btn"
              className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 transition"
            >
              {t("properties.new_btn")}
            </Link>
          </div>
        </div>

        <form onSubmit={onSearch} className="flex flex-wrap gap-3 items-end bg-white border border-stone-200 rounded-lg p-4">
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">{t("common.search")}</label>
            <input
              data-testid="search-input"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("properties.search_placeholder")}
              className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm focus:outline-none focus:border-stone-900"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">{t("properties.filter_status")}</label>
            <select data-testid="filter-status" value={status} onChange={(e) => setStatus(e.target.value)} className="px-3 py-2 border border-stone-300 rounded-md text-sm">
              {STATUSES.map((s) => (
                <option key={s} value={s}>{s ? t(`properties.status_${s}`) : t("properties.filter_all")}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">{t("properties.filter_operation")}</label>
            <select data-testid="filter-operation" value={operation} onChange={(e) => setOperation(e.target.value)} className="px-3 py-2 border border-stone-300 rounded-md text-sm">
              {OPS.map((s) => (
                <option key={s} value={s}>{s ? t(`properties.op_${s}`) : t("properties.filter_all")}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">Smart</label>
            <select
              data-testid="filter-smart"
              value={smart}
              onChange={(e) => setSmart(e.target.value)}
              className="px-3 py-2 border border-stone-300 rounded-md text-sm"
            >
              {SMART.map((s) => (
                <option key={s.id || "all"} value={s.id}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-stone-500 mb-1.5">Ordina</label>
            <select
              data-testid="filter-sort"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="px-3 py-2 border border-stone-300 rounded-md text-sm"
            >
              {SORTS.map((s) => (
                <option key={s.id} value={s.id}>{s.label}</option>
              ))}
            </select>
          </div>
          <button type="submit" className="px-4 py-2 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700">
            {t("common.search")}
          </button>
        </form>

        {!loading && (
          <p className="text-xs text-stone-500" data-testid="properties-total">
            {data.total} immobili
            {smart ? ` · filtro ${SMART.find((s) => s.id === smart)?.label || smart}` : ""}
          </p>
        )}

        {loading ? (
          <p className="text-stone-500 text-sm">{t("common.loading")}</p>
        ) : data.items.length === 0 ? (
          <div data-testid="empty-state" className="bg-white border border-stone-200 rounded-lg p-12 text-center">
            <p className="text-2xl mb-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("properties.empty_title")}
            </p>
            <p className="text-stone-500 mb-6 max-w-md mx-auto">{t("properties.empty_subtitle")}</p>
          </div>
        ) : view === "table" ? (
          <div className="overflow-x-auto border border-stone-200 rounded-lg bg-white" data-testid="properties-table">
            <table className="min-w-full text-sm">
              <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500 text-left">
                <tr>
                  <th className="px-3 py-2 font-medium">Titolo</th>
                  <th className="px-3 py-2 font-medium">Città</th>
                  <th className="px-3 py-2 font-medium">Stato</th>
                  <th className="px-3 py-2 font-medium">Prezzo</th>
                  <th className="px-3 py-2 font-medium">m²</th>
                  <th className="px-3 py-2 font-medium">Foto</th>
                  <th className="px-3 py-2 font-medium">Agente</th>
                  <th className="px-3 py-2 font-medium">Flag</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {data.items.map((p) => (
                  <tr
                    key={p.id}
                    data-testid={`property-row-${p.id}`}
                    onClick={() => openProp(p.id)}
                    className="cursor-pointer hover:bg-stone-50"
                  >
                    <td className="px-3 py-2.5 font-medium text-stone-900 max-w-[220px] truncate">{p.title}</td>
                    <td className="px-3 py-2.5 text-stone-600">{p.city || "—"}</td>
                    <td className="px-3 py-2.5 text-stone-600">{t(`properties.status_${p.status}`)}</td>
                    <td className="px-3 py-2.5 text-stone-900">{formatPrice(p.price || p.rent_monthly)}</td>
                    <td className="px-3 py-2.5 text-stone-600">{p.surface_sqm ?? "—"}</td>
                    <td className="px-3 py-2.5 text-stone-600">{p.photo_count ?? 0}</td>
                    <td className="px-3 py-2.5 text-stone-600 max-w-[120px] truncate" title={p.listing_agent_name || ""}>
                      {p.listing_agent_name || "—"}
                    </td>
                    <td className="px-3 py-2.5"><FlagChips flags={p.listing_flags} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="properties-cards">
            {data.items.map((p) => (
              <div
                key={p.id}
                data-testid={`property-card-${p.id}`}
                onClick={() => openProp(p.id)}
                className="cursor-pointer bg-white border border-stone-200 rounded-lg overflow-hidden hover:border-stone-400 transition group"
              >
                {p.cover_photo_url ? (
                  <div className="aspect-[4/3] bg-stone-100 overflow-hidden">
                    <img src={p.cover_photo_url} alt={p.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                  </div>
                ) : (
                  <div className="aspect-[4/3] bg-stone-100 flex items-center justify-center text-stone-300 text-5xl">🏠</div>
                )}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2 text-[10px] uppercase tracking-widest">
                    <span className={`px-2 py-0.5 rounded ${
                      p.status === "active" ? "bg-emerald-50 text-emerald-700" :
                      p.status === "draft" ? "bg-amber-50 text-amber-700" :
                      "bg-stone-100 text-stone-500"
                    }`}>
                      {t(`properties.status_${p.status}`)}
                    </span>
                    <span className="text-stone-500">{t(`properties.op_${p.operation}`)}</span>
                  </div>
                  <h3 className="font-semibold text-stone-900 mb-1 line-clamp-1">{p.title}</h3>
                  <p className="text-xs text-stone-500 mb-2 line-clamp-1">{p.address || p.city}</p>
                  <FlagChips flags={p.listing_flags} />
                  <div className="flex items-center justify-between mt-3">
                    <span className="font-semibold text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                      {formatPrice(p.price || p.rent_monthly)}
                    </span>
                    <span className="text-xs text-stone-500">
                      {p.surface_sqm ? `${p.surface_sqm} m² · ` : ""}
                      {p.photo_count ?? 0} foto
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </AgencyShell>
  );
}
