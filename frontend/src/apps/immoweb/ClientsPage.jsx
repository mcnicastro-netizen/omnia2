import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import AgencyShell from "./components/AgencyShell";
import { api } from "../../shared/lib/api";

/** D-FUTURE-04 Smart Clients List
 *  Editorial sober variant: stone palette only, no vivid colors.
 *  Order: lead_score desc (deterministic when AI not cached, AI when cached).
 *  Filters: bucket pills (to_call_today / rovente / caldo / tiepido / freddo / searchers / sellers / all).
 */

// Temperature labels in IT/EN/ES sourced from i18n at render-time.
const TEMP_ORDER = ["rovente", "caldo", "tiepido", "freddo"];

function TempPill({ temp, t }) {
  if (!temp) {
    return <span data-testid="temp-pill" className="text-[10px] uppercase tracking-widest text-stone-400">—</span>;
  }
  // Sober styling: monospace dot + grayscale label. No vivid colors.
  const dotShade = {
    rovente: "bg-stone-900",
    caldo: "bg-stone-700",
    tiepido: "bg-stone-400",
    freddo: "bg-stone-300",
  }[temp] || "bg-stone-300";
  return (
    <span data-testid={`temp-pill-${temp}`} className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-stone-600">
      <span className={`inline-block w-1.5 h-1.5 rounded-full ${dotShade}`} />
      {t(`clients_smart.temp_${temp}`)}
    </span>
  );
}

function ScoreBox({ score, cached }) {
  if (score === null || score === undefined) {
    return (
      <div className="w-14 text-center" data-testid="score-box-empty">
        <div className="text-stone-300 text-lg font-light" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>—</div>
        <div className="text-[9px] uppercase tracking-widest text-stone-400 mt-0.5">n/a</div>
      </div>
    );
  }
  return (
    <div className="w-14 text-center" data-testid="score-box" data-cached={cached ? "ai" : "rule"}>
      <div className="text-stone-900 text-2xl font-light leading-none" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
        {score}
      </div>
      <div className="text-[9px] uppercase tracking-widest text-stone-500 mt-1">
        {cached ? "AI" : "match"}
      </div>
    </div>
  );
}

function MatchesPill({ count, t }) {
  if (!count) {
    return (
      <span data-testid="matches-pill-zero" className="inline-flex items-center gap-1 text-[11px] uppercase tracking-widest text-stone-400 px-2 py-1 border border-dashed border-stone-300 rounded-md">
        {t("clients_smart.no_matches")}
      </span>
    );
  }
  return (
    <span data-testid="matches-pill" className="inline-flex items-center gap-1 text-[11px] uppercase tracking-widest text-stone-700 px-2.5 py-1 bg-stone-100 border border-stone-200 rounded-md">
      <span className="text-stone-900 font-semibold normal-case tracking-normal text-sm">{count}</span>
      <span>{t(count === 1 ? "clients_smart.match_singular" : "clients_smart.match_plural")}</span>
    </span>
  );
}

function FilterPill({ id, active, label, count, onClick }) {
  return (
    <button
      type="button"
      data-testid={`filter-pill-${id}`}
      onClick={onClick}
      className={`px-3.5 py-1.5 rounded-md text-xs uppercase tracking-widest transition border ${
        active
          ? "bg-stone-900 text-stone-50 border-stone-900"
          : "bg-white text-stone-700 border-stone-300 hover:border-stone-500"
      }`}
    >
      {label}
      {typeof count === "number" && (
        <span className={`ml-2 text-[10px] ${active ? "text-stone-300" : "text-stone-400"}`}>{count}</span>
      )}
    </button>
  );
}

export default function ClientsPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();

  const [data, setData] = useState({ items: [], counts: {}, total: 0 });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [bucket, setBucket] = useState("all");
  const [sort, setSort] = useState("score_desc");
  const [q, setQ] = useState("");
  const [toast, setToast] = useState("");

  const load = async (signal) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("sort", sort);
      if (bucket && bucket !== "all") params.set("bucket", bucket);
      if (q) params.set("q", q);
      const { data } = await api.get(`/app/clients/smart?${params.toString()}`, { signal });
      setData(data);
    } catch (e) {
      if (e.name !== "CanceledError") {
        console.error(e);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const ac = new AbortController();
    load(ac.signal);
    return () => ac.abort();
  }, [bucket, sort]);

  const onSearch = (e) => {
    e.preventDefault();
    load();
  };

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(""), 4000);
  };

  const refreshAi = async () => {
    setRefreshing(true);
    try {
      const { data: r } = await api.post("/app/clients/smart/refresh", { limit: 10 });
      showToast(t("clients_smart.refresh_done", { n: r.refreshed }));
      await load();
    } catch (e) {
      showToast(t("clients_smart.refresh_error"));
    } finally {
      setRefreshing(false);
    }
  };

  const counts = data.counts || {};
  const uncached = counts.ai_uncached_searchers || 0;

  const pills = useMemo(() => ([
    { id: "all",            label: t("clients_smart.bucket_all"),            count: counts.all },
    { id: "to_call_today",  label: t("clients_smart.bucket_to_call_today"),  count: counts.to_call_today },
    { id: "rovente",        label: t("clients_smart.bucket_rovente"),        count: counts.rovente },
    { id: "caldo",          label: t("clients_smart.bucket_caldo"),          count: counts.caldo },
    { id: "tiepido",        label: t("clients_smart.bucket_tiepido"),        count: counts.tiepido },
    { id: "freddo",         label: t("clients_smart.bucket_freddo"),         count: counts.freddo },
    { id: "searchers",      label: t("clients_smart.bucket_searchers"),      count: counts.searchers },
    { id: "sellers",        label: t("clients_smart.bucket_sellers"),        count: counts.sellers },
  ]), [counts, t]);

  return (
    <AgencyShell current="clients">
      <section data-testid="clients-page" className="space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl md:text-4xl tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("clients.title")}
            </h1>
            <p className="text-stone-600 mt-1">{t("clients_smart.subtitle")}</p>
          </div>
          <div className="flex gap-2">
            {uncached > 0 && (
              <button
                type="button"
                data-testid="clients-refresh-ai-btn"
                onClick={refreshAi}
                disabled={refreshing}
                className="px-4 py-2.5 bg-white border border-stone-400 text-stone-800 text-xs uppercase tracking-widest font-medium rounded-md hover:border-stone-700 disabled:opacity-50 transition"
                title={t("clients_smart.refresh_hint", { n: uncached })}
              >
                {refreshing ? t("clients_smart.refreshing") : t("clients_smart.refresh_ai_btn", { n: Math.min(uncached, 10) })}
              </button>
            )}
            <Link
              to={`/${lang}/app/clients/import`}
              data-testid="clients-import-csv-btn"
              className="px-4 py-2.5 bg-white border border-stone-300 text-stone-700 text-xs uppercase tracking-widest font-medium rounded-md hover:border-stone-700 transition"
            >
              {t("clients_smart.import_csv_btn")}
            </Link>
            <Link
              to={`/${lang}/app/clients/new`}
              data-testid="clients-new-btn"
              className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest font-medium rounded-md hover:bg-stone-700 transition"
            >
              {t("clients.new_btn")}
            </Link>
          </div>
        </div>

        {/* Smart sorting banner */}
        <div data-testid="smart-banner" className="bg-stone-100 border border-stone-200 rounded-lg p-4 flex gap-3 items-start text-sm text-stone-700">
          <span className="text-base leading-none mt-0.5">◆</span>
          <p>
            {t("clients_smart.banner_text")}
          </p>
        </div>

        {toast && (
          <p data-testid="clients-smart-toast" className="text-sm text-stone-700 bg-stone-100 border border-stone-200 rounded-md px-3 py-2">
            ✓ {toast}
          </p>
        )}

        {/* Search + bucket filters */}
        <form onSubmit={onSearch} className="flex flex-wrap gap-3 items-center">
          <input
            data-testid="clients-search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("clients.search_placeholder")}
            className="flex-1 min-w-[220px] px-3 py-2 bg-white border border-stone-300 rounded-md text-sm focus:outline-none focus:border-stone-900"
          />
          <button type="submit" className="px-4 py-2 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700">
            {t("common.search")}
          </button>
          <select
            data-testid="clients-sort"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="px-3 py-2 bg-white border border-stone-300 rounded-md text-sm"
          >
            <option value="score_desc">{t("clients_smart.sort_score_desc")}</option>
            <option value="score_asc">{t("clients_smart.sort_score_asc")}</option>
            <option value="created_desc">{t("clients_smart.sort_created_desc")}</option>
            <option value="name_asc">{t("clients_smart.sort_name_asc")}</option>
          </select>
        </form>

        <div className="flex flex-wrap gap-2" data-testid="bucket-filters">
          {pills.map((p) => (
            <FilterPill
              key={p.id}
              id={p.id}
              active={bucket === p.id}
              label={p.label}
              count={p.count}
              onClick={() => setBucket(p.id)}
            />
          ))}
        </div>

        {loading ? (
          <p className="text-stone-500 text-sm" data-testid="clients-loading">{t("common.loading")}</p>
        ) : data.items.length === 0 ? (
          <div data-testid="clients-empty" className="bg-white border border-stone-200 rounded-lg p-12 text-center">
            <p className="text-2xl mb-2" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("clients.empty_title")}
            </p>
            <p className="text-stone-500 mb-6 max-w-md mx-auto">{t("clients.empty_subtitle")}</p>
            <Link
              to={`/${lang}/app/clients/new`}
              className="inline-block px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700"
            >
              {t("clients.new_btn")}
            </Link>
          </div>
        ) : (
          <div className="space-y-2" data-testid="clients-smart-list">
            {data.items.map((c) => (
              <ClientRow key={c.id} c={c} lang={lang} t={t} onOpen={() => nav(`/${lang}/app/clients/${c.id}`)} />
            ))}
          </div>
        )}
      </section>
    </AgencyShell>
  );
}


function ClientRow({ c, lang, t, onOpen }) {
  const isSeller = !["buyer", "tenant", "investor"].includes(c.client_type);
  const fullName = `${c.name || ""} ${c.surname || ""}`.trim() || "—";
  const prefs = c.preferences || {};
  const prefBits = [];
  if (prefs.operation) prefBits.push(t(`clients.op_${prefs.operation}`, { defaultValue: prefs.operation }));
  if ((prefs.property_types || []).length) prefBits.push((prefs.property_types || []).slice(0, 2).join("/"));
  if ((prefs.cities || []).length) prefBits.push((prefs.cities || []).slice(0, 2).join(", "));
  if (prefs.price_max) prefBits.push(`fino a ${new Intl.NumberFormat("it-IT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(prefs.price_max)}`);
  const prefLine = prefBits.length ? prefBits.join(" · ") : (isSeller ? t("clients_smart.seller_no_prefs") : t("clients_smart.no_prefs_set"));

  // Quick-action links: tel: + wa.me
  const cleanPhone = (s) => String(s || "").replace(/[^\d+]/g, "");
  const phoneDigits = cleanPhone(c.phone);
  const waDigits = cleanPhone(c.whatsapp || c.phone).replace(/^\+/, "");
  const telHref = phoneDigits ? `tel:${phoneDigits}` : null;
  const aiHint = (c.action_hint || "").slice(0, 120);
  const waText = aiHint ? `Buongiorno ${c.name || ""}, ${aiHint}` : `Buongiorno ${c.name || ""}`;
  const waHref = waDigits ? `https://wa.me/${waDigits}?text=${encodeURIComponent(waText)}` : null;

  const stop = (e) => e.stopPropagation();

  return (
    <div
      data-testid={`client-row-${c.id}`}
      onClick={onOpen}
      className="bg-white border border-stone-200 rounded-lg px-5 py-4 cursor-pointer hover:border-stone-500 hover:shadow-sm transition grid grid-cols-1 md:grid-cols-[60px_1fr_auto_auto] gap-4 items-center"
    >
      <ScoreBox score={c.lead_score} cached={c.ai_cached} />

      <div className="min-w-0">
        <div className="flex items-center gap-3 flex-wrap">
          <span className="font-medium text-stone-900 text-base">{fullName}</span>
          <TempPill temp={c.temperature} t={t} />
          <span className="text-[10px] uppercase tracking-widest text-stone-400">
            {t(`clients.type_${c.client_type}`)}
          </span>
        </div>
        <div className="text-stone-600 text-sm mt-0.5 truncate">{prefLine}</div>
        {c.action_hint && (
          <div className="text-stone-500 text-xs mt-1.5 italic truncate">
            <span className="not-italic mr-1">·</span>{c.action_hint}
          </div>
        )}
      </div>

      <MatchesPill count={c.matches_count} t={t} />

      <div className="flex items-center gap-1.5" onClick={stop}>
        {telHref ? (
          <a
            href={telHref}
            data-testid={`row-call-${c.id}`}
            onClick={stop}
            title={t("clients_smart.action_call_title", { phone: c.phone })}
            aria-label={t("clients_smart.action_call_aria")}
            className="inline-flex items-center justify-center w-9 h-9 rounded-md border border-stone-300 bg-white text-stone-700 hover:border-stone-700 hover:text-stone-900 transition"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
          </a>
        ) : (
          <span
            data-testid={`row-call-disabled-${c.id}`}
            title={t("clients_smart.action_no_phone")}
            className="inline-flex items-center justify-center w-9 h-9 rounded-md border border-dashed border-stone-200 text-stone-300"
            aria-hidden="true"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
          </span>
        )}
        {waHref ? (
          <a
            href={waHref}
            target="_blank"
            rel="noopener noreferrer"
            data-testid={`row-whatsapp-${c.id}`}
            onClick={stop}
            title={t("clients_smart.action_wa_title")}
            aria-label={t("clients_smart.action_wa_aria")}
            className="inline-flex items-center justify-center w-9 h-9 rounded-md border border-stone-300 bg-white text-stone-700 hover:border-stone-700 hover:text-stone-900 transition"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor" aria-hidden="true">
              <path d="M.057 24l1.687-6.163A11.867 11.867 0 0 1 .157 11.892C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 0 1 8.413 3.488 11.824 11.824 0 0 1 3.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 0 1-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479c0 1.462 1.065 2.875 1.213 3.074.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/>
            </svg>
          </a>
        ) : (
          <span
            data-testid={`row-whatsapp-disabled-${c.id}`}
            title={t("clients_smart.action_no_wa")}
            className="inline-flex items-center justify-center w-9 h-9 rounded-md border border-dashed border-stone-200 text-stone-300"
            aria-hidden="true"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor"><path d="M.057 24l1.687-6.163A11.867 11.867 0 0 1 .157 11.892C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 0 1 8.413 3.488 11.824 11.824 0 0 1 3.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 0 1-5.688-1.448L.057 24z"/></svg>
          </span>
        )}
      </div>
    </div>
  );
}
