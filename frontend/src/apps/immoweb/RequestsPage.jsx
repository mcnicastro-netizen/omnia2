import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

const TYPE_FILTERS = ["all", "property_interest", "search_brief"];
const STATUS_FILTERS = ["open", "matched", "negotiating", "won", "lost", "archived", "all"];

function TypeBadge({ type, t }) {
  const label =
    type === "property_interest"
      ? t("requests.type_property_interest")
      : t("requests.type_search_brief");
  return (
    <span
      data-testid={`request-type-${type}`}
      className="text-[10px] uppercase tracking-widest text-stone-500 border border-stone-300 px-2 py-0.5 rounded"
    >
      {label}
    </span>
  );
}

function SourceBadge({ source }) {
  return (
    <span className="text-[10px] uppercase tracking-widest text-stone-400">
      {source || "—"}
    </span>
  );
}

function MatchScope({ scope, score, t }) {
  if (!scope || scope === "none" || score == null) {
    return (
      <span className="text-[11px] uppercase tracking-widest text-stone-400">
        {t("requests.no_match")}
      </span>
    );
  }
  const label =
    scope === "mls" ? t("requests.scope_mls") : t("requests.scope_portfolio");
  return (
    <span
      data-testid="request-match-scope"
      className="inline-flex items-center gap-2 text-[11px] uppercase tracking-widest text-stone-700 bg-stone-100 border border-stone-200 px-2.5 py-1 rounded-md"
    >
      <span className="text-base font-light normal-case tracking-normal text-stone-900" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
        {score}
      </span>
      {label}
    </span>
  );
}

export default function RequestsPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [data, setData] = useState({ items: [], counts: {}, total: 0, page: 1 });
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState(searchParams.get("type") || "all");
  const [statusFilter, setStatusFilter] = useState(searchParams.get("status") || "open");
  const [sourceFilter, setSourceFilter] = useState(searchParams.get("source") || "");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(1);
  const [toast, setToast] = useState("");
  const pageSize = 50;

  const load = async (signal) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("page", String(page));
      params.set("page_size", String(pageSize));
      if (typeFilter && typeFilter !== "all") params.set("request_type", typeFilter);
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter);
      if (sourceFilter) params.set("source", sourceFilter);
      if (q) params.set("q", q);
      const { data: res } = await api.get(`/app/requests?${params.toString()}`, { signal });
      setData(res);
    } catch (e) {
      if (e.name !== "CanceledError") console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const ac = new AbortController();
    load(ac.signal);
    return () => ac.abort();
  }, [typeFilter, statusFilter, sourceFilter, page]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const next = new URLSearchParams();
    if (typeFilter !== "all") next.set("type", typeFilter);
    if (statusFilter !== "all") next.set("status", statusFilter);
    if (sourceFilter) next.set("source", sourceFilter);
    setSearchParams(next, { replace: true });
  }, [typeFilter, statusFilter, sourceFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  const counts = data.counts || {};
  const bySource = counts.by_source || {};
  const sourceKeys = useMemo(() => Object.keys(bySource).sort(), [bySource]);

  const onSearch = (e) => {
    e.preventDefault();
    if (page !== 1) setPage(1);
    else load();
  };

  const toggleShare = async (id, current) => {
    try {
      await api.post(`/app/requests/${id}/share`, { mls_shared: !current });
      setToast(t(!current ? "requests.share_on" : "requests.share_off"));
      setTimeout(() => setToast(""), 3000);
      load();
    } catch (e) {
      setToast(t("requests.share_error"));
      setTimeout(() => setToast(""), 3000);
    }
  };

  return (
    <AgencyShell current="requests">
      <section data-testid="requests-page" className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("requests.title")}
            </h1>
            <p className="text-stone-600 mt-1">{t("requests.subtitle")}</p>
          </div>
          <Link
            to={`/${lang}/app/requests/new`}
            data-testid="requests-new-btn"
            className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 transition"
          >
            {t("requests.new_btn")}
          </Link>
        </div>

        <div className="bg-stone-100 border border-stone-200 rounded-lg p-4 text-sm text-stone-700" data-testid="requests-banner">
          {t("requests.banner")}
        </div>

        {toast && (
          <p className="text-sm text-stone-700 bg-stone-100 border border-stone-200 rounded-md px-3 py-2">✓ {toast}</p>
        )}

        {/* Type segments */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" data-testid="requests-type-filters">
          {TYPE_FILTERS.map((id) => {
            const count =
              id === "all" ? counts.all : id === "property_interest" ? counts.property_interest : counts.search_brief;
            const active = typeFilter === id;
            return (
              <button
                key={id}
                type="button"
                data-testid={`requests-type-${id}`}
                onClick={() => { setPage(1); setTypeFilter(id); }}
                className={`text-left px-4 py-3 rounded-lg border transition ${
                  active ? "bg-stone-900 text-stone-50 border-stone-900" : "bg-white border-stone-300 hover:border-stone-600"
                }`}
              >
                <div className="flex justify-between items-baseline gap-2">
                  <span className="text-xs uppercase tracking-widest">
                    {id === "all" ? t("requests.filter_all") : t(`requests.type_${id}`)}
                  </span>
                  {typeof count === "number" && (
                    <span className="text-xl font-light" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>{count}</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>

        <form onSubmit={onSearch} className="flex flex-wrap gap-3 items-center">
          <input
            data-testid="requests-search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("requests.search_placeholder")}
            className="flex-1 min-w-[200px] px-3 py-2 bg-white border border-stone-300 rounded-md text-sm"
          />
          <button type="submit" className="px-4 py-2 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md">
            {t("common.search")}
          </button>
          <select
            data-testid="requests-status"
            value={statusFilter}
            onChange={(e) => { setPage(1); setStatusFilter(e.target.value); }}
            className="px-3 py-2 bg-white border border-stone-300 rounded-md text-sm"
          >
            {STATUS_FILTERS.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? t("requests.filter_all_status") : t(`requests.status_${s}`)}
              </option>
            ))}
          </select>
          <select
            data-testid="requests-source"
            value={sourceFilter}
            onChange={(e) => { setPage(1); setSourceFilter(e.target.value); }}
            className="px-3 py-2 bg-white border border-stone-300 rounded-md text-sm"
          >
            <option value="">{t("requests.filter_all_sources")}</option>
            {sourceKeys.map((s) => (
              <option key={s} value={s}>{s} ({bySource[s]})</option>
            ))}
          </select>
        </form>

        {loading ? (
          <p className="text-stone-500 text-sm">{t("common.loading")}</p>
        ) : data.items.length === 0 ? (
          <div data-testid="requests-empty" className="bg-white border border-stone-200 rounded-lg p-12 text-center">
            <p className="text-2xl mb-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("requests.empty_title")}
            </p>
            <p className="text-stone-500 mb-6 max-w-md mx-auto">{t("requests.empty_subtitle")}</p>
            <Link
              to={`/${lang}/app/requests/new`}
              className="inline-block px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md"
            >
              {t("requests.new_btn")}
            </Link>
          </div>
        ) : (
          <div className="space-y-2" data-testid="requests-list">
            {data.items.map((r) => (
              <div
                key={r.id}
                data-testid={`request-row-${r.id}`}
                className="bg-white border border-stone-200 rounded-lg px-5 py-4 grid grid-cols-1 md:grid-cols-[1fr_auto_auto] gap-4 items-center hover:border-stone-500 transition cursor-pointer"
                onClick={() => nav(`/${lang}/app/requests/${r.id}`)}
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-stone-900">
                      {r.title || r.client_name || "—"}
                    </span>
                    <TypeBadge type={r.request_type} t={t} />
                    <SourceBadge source={r.source} />
                    {r.mls_shared && (
                      <span className="text-[10px] uppercase tracking-widest text-stone-600 border border-stone-400 px-2 py-0.5 rounded">
                        {t("requests.mls_shared_badge")}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-stone-600 mt-1 truncate">
                    {r.client_name && <span>{r.client_name}</span>}
                    {r.property_title && (
                      <span> · {r.property_ref ? `${r.property_ref} · ` : ""}{r.property_title}</span>
                    )}
                    {!r.property_title && r.criteria?.cities?.length > 0 && (
                      <span> · {(r.criteria.cities || []).slice(0, 2).join(", ")}</span>
                    )}
                  </div>
                  <div className="text-[10px] uppercase tracking-widest text-stone-400 mt-1">
                    {t(`requests.status_${r.status}`)}
                  </div>
                </div>

                <MatchScope scope={r.best_match_scope} score={r.best_match_score} t={t} />

                <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    data-testid={`request-share-${r.id}`}
                    onClick={() => toggleShare(r.id, r.mls_shared)}
                    className="px-3 py-1.5 text-[10px] uppercase tracking-widest border border-stone-300 rounded-md hover:border-stone-700"
                  >
                    {r.mls_shared ? t("requests.unshare_btn") : t("requests.share_btn")}
                  </button>
                  <Link
                    to={`/${lang}/app/requests/${r.id}`}
                    className="px-3 py-1.5 text-[10px] uppercase tracking-widest bg-stone-900 text-stone-50 rounded-md"
                  >
                    {t("requests.open_btn")}
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </AgencyShell>
  );
}
