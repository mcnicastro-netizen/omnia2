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
          className="text-[9px] uppercase tracking-widest px-1.5 py-0.5 border border-crm-gold/40 text-crm-navy bg-crm-gold-soft/40"
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
  const [page, setPage] = useState(() => Math.max(1, parseInt(searchParams.get("page") || "1", 10) || 1));
  const pageSize = 20;
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

  const load = async (pageOverride) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      const p = pageOverride ?? page;
      params.set("page", String(p));
      params.set("page_size", String(pageSize));
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
    load(page);
    const next = new URLSearchParams();
    if (status) next.set("status", status);
    if (smart) next.set("smart", smart);
    if (sort && sort !== "updated_desc") next.set("sort", sort);
    if (view === "table") next.set("view", "table");
    if (page > 1) next.set("page", String(page));
    setSearchParams(next, { replace: true });
    localStorage.setItem("omnia_props_view", view);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, smart, sort, view, page]);

  useEffect(() => {
    setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, smart, sort, operation]);

  const onSearch = (e) => {
    e.preventDefault();
    if (page !== 1) setPage(1);
    else load(1);
  };

  const openProp = (id) => nav(`/${lang}/app/properties/${id}`);

  return (
    <AgencyShell current="properties">
      <section data-testid="properties-page" className="crm-desk space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="crm-eyebrow" data-testid="properties-crm-eyebrow">
              Bancone Immobili
            </p>
            <h1 className="crm-title text-3xl md:text-4xl mt-1">{t("properties.title")}</h1>
            <p className="text-crm-muted mt-1 text-sm">{t("properties.subtitle")}</p>
          </div>
          <div className="flex gap-3 flex-wrap">
            <div
              className="inline-flex border border-crm-line overflow-hidden rounded-md"
              data-testid="properties-view-toggle"
            >
              <button
                type="button"
                data-testid="view-cards"
                onClick={() => setView("cards")}
                className={`px-3 py-2 text-[10px] uppercase tracking-widest ${
                  view === "cards" ? "crm-btn-primary" : "bg-white text-crm-navy"
                }`}
              >
                Card
              </button>
              <button
                type="button"
                data-testid="view-table"
                onClick={() => setView("table")}
                className={`px-3 py-2 text-[10px] uppercase tracking-widest ${
                  view === "table" ? "crm-btn-primary" : "bg-white text-crm-navy"
                }`}
              >
                Tabella
              </button>
            </div>
            <Link
              to={`/${lang}/app/properties/import`}
              data-testid="properties-import-btn"
              className="crm-btn-ghost px-4 py-2.5 text-xs uppercase tracking-widest font-medium rounded-md transition"
            >
              {t("properties.import_btn")}
            </Link>
            <Link
              to={`/${lang}/app/properties/new`}
              data-testid="properties-new-btn"
              className="crm-btn-primary px-5 py-2.5 text-xs uppercase tracking-widest font-medium rounded-md transition"
            >
              {t("properties.new_btn")}
            </Link>
          </div>
        </div>

        <form
          onSubmit={onSearch}
          className="crm-panel flex flex-wrap gap-3 items-end p-4 bg-crm-mist/60"
        >
          <div className="flex-1 min-w-[180px]">
            <label className="block text-xs uppercase tracking-widest text-crm-muted mb-1.5">
              {t("common.search")}
            </label>
            <input
              data-testid="search-input"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("properties.search_placeholder")}
              className="crm-input w-full px-3 py-2 border border-crm-line rounded-md text-sm bg-white"
            />
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-crm-muted mb-1.5">
              {t("properties.filter_status")}
            </label>
            <select
              data-testid="filter-status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="crm-input px-3 py-2 border border-crm-line rounded-md text-sm bg-white"
            >
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s ? t(`properties.status_${s}`) : t("properties.filter_all")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-crm-muted mb-1.5">
              {t("properties.filter_operation")}
            </label>
            <select
              data-testid="filter-operation"
              value={operation}
              onChange={(e) => setOperation(e.target.value)}
              className="crm-input px-3 py-2 border border-crm-line rounded-md text-sm bg-white"
            >
              {OPS.map((s) => (
                <option key={s} value={s}>
                  {s ? t(`properties.op_${s}`) : t("properties.filter_all")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-crm-muted mb-1.5">Smart</label>
            <select
              data-testid="filter-smart"
              value={smart}
              onChange={(e) => setSmart(e.target.value)}
              className="crm-input px-3 py-2 border border-crm-line rounded-md text-sm bg-white"
            >
              {SMART.map((s) => (
                <option key={s.id || "all"} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs uppercase tracking-widest text-crm-muted mb-1.5">Ordina</label>
            <select
              data-testid="filter-sort"
              value={sort}
              onChange={(e) => setSort(e.target.value)}
              className="crm-input px-3 py-2 border border-crm-line rounded-md text-sm bg-white"
            >
              {SORTS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            className="crm-btn-primary px-4 py-2 text-xs uppercase tracking-widest rounded-md"
          >
            {t("common.search")}
          </button>
        </form>

        {!loading && (
          <p className="text-xs text-crm-muted" data-testid="properties-total">
            {data.total} immobili
            {smart ? ` · filtro ${SMART.find((s) => s.id === smart)?.label || smart}` : ""}
          </p>
        )}

        {loading ? (
          <p className="text-crm-muted text-sm">{t("common.loading")}</p>
        ) : data.items.length === 0 ? (
          <div data-testid="empty-state" className="crm-panel p-12 text-center">
            <p className="crm-title text-2xl mb-2">{t("properties.empty_title")}</p>
            <p className="text-crm-muted mb-6 max-w-md mx-auto">{t("properties.empty_subtitle")}</p>
          </div>
        ) : view === "table" ? (
          <div className="overflow-x-auto crm-panel" data-testid="properties-table">
            <table className="min-w-full text-sm">
              <thead className="bg-crm-mist text-[10px] uppercase tracking-widest text-crm-muted text-left">
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
              <tbody className="divide-y divide-crm-line/70">
                {data.items.map((p) => (
                  <tr
                    key={p.id}
                    data-testid={`property-row-${p.id}`}
                    onClick={() => openProp(p.id)}
                    className="cursor-pointer hover:bg-crm-mist/80"
                  >
                    <td className="px-3 py-2.5 font-medium text-crm-navy max-w-[220px] truncate">{p.title}</td>
                    <td className="px-3 py-2.5 text-crm-muted">{p.city || "—"}</td>
                    <td className="px-3 py-2.5 text-crm-muted">{t(`properties.status_${p.status}`)}</td>
                    <td className="px-3 py-2.5 text-crm-navy font-medium">{formatPrice(p.price || p.rent_monthly)}</td>
                    <td className="px-3 py-2.5 text-crm-muted">{p.surface_sqm ?? "—"}</td>
                    <td className="px-3 py-2.5 text-crm-muted">{p.photo_count ?? 0}</td>
                    <td className="px-3 py-2.5 text-crm-muted max-w-[120px] truncate" title={p.listing_agent_name || ""}>
                      {p.listing_agent_name || "—"}
                    </td>
                    <td className="px-3 py-2.5">
                      <FlagChips flags={p.listing_flags} />
                    </td>
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
                className="cursor-pointer crm-panel overflow-hidden hover:border-crm-navy/40 transition group"
              >
                {p.cover_photo_url ? (
                  <div className="aspect-[4/3] bg-crm-mist overflow-hidden">
                    <img
                      src={p.cover_photo_url}
                      alt={p.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  </div>
                ) : (
                  <div className="aspect-[4/3] bg-crm-mist flex items-center justify-center text-crm-line text-sm uppercase tracking-widest">
                    Senza foto
                  </div>
                )}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2 text-[10px] uppercase tracking-widest">
                    <span
                      className={`px-2 py-0.5 border ${
                        p.status === "active"
                          ? "border-crm-navy/30 bg-crm-navy text-white"
                          : p.status === "draft"
                            ? "border-crm-gold/50 bg-crm-gold-soft/50 text-crm-navy"
                            : "border-crm-line bg-white text-crm-muted"
                      }`}
                    >
                      {t(`properties.status_${p.status}`)}
                    </span>
                    <span className="text-crm-gold">{t(`properties.op_${p.operation}`)}</span>
                  </div>
                  <h3 className="font-semibold text-crm-navy mb-1 line-clamp-1">{p.title}</h3>
                  <p className="text-xs text-crm-muted mb-2 line-clamp-1">{p.address || p.city}</p>
                  <FlagChips flags={p.listing_flags} />
                  <div className="flex items-center justify-between mt-3">
                    <span className="font-semibold text-crm-navy">{formatPrice(p.price || p.rent_monthly)}</span>
                    <span className="text-xs text-crm-muted">
                      {p.surface_sqm ? `${p.surface_sqm} m² · ` : ""}
                      {p.photo_count ?? 0} foto
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!loading && data.total > pageSize ? (
          <div className="flex items-center justify-between gap-3 pt-2" data-testid="properties-pagination">
            <button
              type="button"
              data-testid="properties-page-prev"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="crm-btn-ghost px-3 py-2 text-xs uppercase tracking-widest rounded-md disabled:opacity-40"
            >
              Precedente
            </button>
            <span className="text-xs text-crm-muted" data-testid="properties-page-label">
              Pagina {data.page || page} · {data.total} immobili
            </span>
            <button
              type="button"
              data-testid="properties-page-next"
              disabled={(data.page || page) * pageSize >= data.total}
              onClick={() => setPage((p) => p + 1)}
              className="crm-btn-ghost px-3 py-2 text-xs uppercase tracking-widest rounded-md disabled:opacity-40"
            >
              Successiva
            </button>
          </div>
        ) : null}
      </section>
    </AgencyShell>
  );
}
