import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

const STATUSES = ["", "draft", "active", "reserved", "sold", "rented", "withdrawn"];
const OPS = ["", "sale", "rent", "rent_to_buy", "auction"];

function formatPrice(v) {
  if (v == null) return "—";
  return new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(v);
}

export default function PropertiesPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 20 });
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [operation, setOperation] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      if (status) params.set("status", status);
      if (operation) params.set("operation", operation);
      const { data } = await api.get(`/app/properties?${params.toString()}`);
      setData(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSearch = (e) => {
    e.preventDefault();
    load();
  };

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
          <div className="flex gap-3">
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

        {/* Filters */}
        <form onSubmit={onSearch} className="flex flex-wrap gap-3 items-end bg-white border border-stone-200 rounded-lg p-4">
          <div className="flex-1 min-w-[200px]">
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
          <button type="submit" className="px-4 py-2 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700">
            {t("common.search")}
          </button>
        </form>

        {/* List */}
        {loading ? (
          <p className="text-stone-500 text-sm">{t("common.loading")}</p>
        ) : data.items.length === 0 ? (
          <div data-testid="empty-state" className="bg-white border border-stone-200 rounded-lg p-12 text-center">
            <p
              className="text-2xl mb-2"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("properties.empty_title")}
            </p>
            <p className="text-stone-500 mb-6 max-w-md mx-auto">{t("properties.empty_subtitle")}</p>
            <div className="flex justify-center gap-3">
              <Link
                to={`/${lang}/app/properties/new`}
                className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700"
              >
                {t("properties.new_btn")}
              </Link>
              <Link
                to={`/${lang}/app/properties/import`}
                className="px-5 py-2.5 border border-stone-300 bg-white text-xs uppercase tracking-widest rounded-md"
              >
                {t("properties.import_btn")}
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.items.map((p) => (
              <div
                key={p.id}
                data-testid={`property-card-${p.id}`}
                onClick={() => nav(`/${lang}/app/properties/${p.id}`)}
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
                  <p className="text-xs text-stone-500 mb-3 line-clamp-1">{p.address || p.city}</p>
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
                      {formatPrice(p.price || p.rent_monthly)}
                    </span>
                    {p.surface_sqm && (
                      <span className="text-xs text-stone-500">{p.surface_sqm} m²</span>
                    )}
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
