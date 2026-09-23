import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "./components/AgencyShell";
import KPICard from "./components/KPICard";
import { api } from "../../shared/lib/api";
import { useAuth } from "../../shared/lib/auth";
import Brand from "../../shared/components/Brand";

const QUICK_ACTIONS = [
  { key: "new_property", to: "properties/new", labelKey: "dashboard.qa_new_property", fallback: "Nuovo immobile" },
  { key: "new_client", to: "clients/new", labelKey: "dashboard.qa_new_client", fallback: "Nuovo cliente" },
  { key: "new_request", to: "requests/new", labelKey: "dashboard.qa_new_request", fallback: "Nuova richiesta" },
  { key: "matches", to: "matches", labelKey: "dashboard.qa_matches", fallback: "Match" },
  { key: "publishing", to: "publishing", labelKey: "dashboard.qa_publishing", fallback: "Pubblicità su portali" },
  { key: "hal", to: "hal-knowledge", labelKey: "dashboard.qa_hal", fallback: "HAL Knowledge" },
];

function appHref(lang, href) {
  if (!href) return `/${lang}/app/dashboard`;
  if (href.startsWith("/app/")) return `/${lang}${href}`;
  if (href.startsWith("/")) return `/${lang}/app${href}`;
  return `/${lang}/app/${href}`;
}

function TodayCockpit({ today, loading, lang, t }) {
  if (loading) {
    return (
      <div data-testid="today-cockpit-loading" className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 bg-stone-100 animate-pulse" />
        ))}
      </div>
    );
  }

  const actions = today?.actions || [];
  if (!actions.length) {
    return (
      <div
        data-testid="today-cockpit-empty"
        className="border border-dashed border-stone-300 px-5 py-8 text-sm font-sans text-stone-600"
      >
        {t(
          "dashboard.today_empty",
          "Niente di urgente in coda. Usa le azioni rapide o apri Clienti smart."
        )}
      </div>
    );
  }

  return (
    <div data-testid="today-cockpit" className="space-y-6">
      {actions.map((group) => (
        <div key={group.id} data-testid={`today-group-${group.id}`} className="border-t border-stone-200 pt-4">
          <div className="flex flex-wrap items-baseline justify-between gap-2 mb-3">
            <div>
              <h3
                className="text-lg tracking-tight text-stone-900"
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}
              >
                {t(group.title_key, group.title)}
              </h3>
              <p className="text-[11px] uppercase tracking-widest text-stone-500 font-sans mt-1">
                {group.count_label || group.count}{" "}
                {t("dashboard.today_in_queue", "in coda")}
              </p>
            </div>
            <Link
              to={appHref(lang, group.href)}
              data-testid={`today-cta-${group.id}`}
              className="text-[11px] font-sans uppercase tracking-widest text-stone-800 border-b border-stone-400 hover:border-stone-900"
            >
              {t(group.cta_key, group.cta)} →
            </Link>
          </div>
          {(group.items || []).length > 0 && (
            <ul className="divide-y divide-stone-100 border border-stone-200 bg-white">
              {group.items.map((item) => (
                <li key={`${group.id}-${item.id}`}>
                  <Link
                    to={appHref(lang, item.href)}
                    data-testid={`today-item-${group.id}-${item.id}`}
                    className="flex flex-wrap items-baseline justify-between gap-2 px-4 py-3 hover:bg-stone-50 transition"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-sans text-stone-900 truncate">{item.label}</p>
                      <p className="text-[11px] font-sans text-stone-500 mt-0.5">
                        {t(item.reason_key, item.reason)}
                        {item.meta ? ` · ${item.meta}` : ""}
                      </p>
                    </div>
                    <span className="text-[10px] uppercase tracking-widest text-stone-400 shrink-0">
                      {t("dashboard.today_open", "Apri")}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

function RecentStrip({ recent, t }) {
  if (!recent?.length) return null;
  return (
    <div data-testid="today-recent" className="mt-8">
      <h3
        className="text-sm uppercase tracking-[0.2em] text-stone-500 mb-3 font-sans"
      >
        {t("dashboard.today_recent", "Ultime attività")}
      </h3>
      <ul className="space-y-2">
        {recent.map((r, i) => (
          <li
            key={`${r.kind}-${r.at}-${i}`}
            className="text-sm font-sans text-stone-700 flex flex-wrap gap-x-3 gap-y-1"
          >
            <span className="text-stone-900">{r.label}</span>
            {r.at && (
              <span className="text-[11px] uppercase tracking-widest text-stone-400">
                {String(r.at).slice(0, 16).replace("T", " ")}
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { lang } = useParams();
  const l = (lang || "it").slice(0, 2);
  const [kpis, setKpis] = useState([]);
  const [today, setToday] = useState(null);
  const [loadingKpis, setLoadingKpis] = useState(true);
  const [loadingToday, setLoadingToday] = useState(true);
  const [todayError, setTodayError] = useState(false);

  useEffect(() => {
    let mounted = true;
    api
      .get("/app/dashboard/kpis")
      .then((r) => mounted && setKpis(r.data || []))
      .catch(() => mounted && setKpis([]))
      .finally(() => mounted && setLoadingKpis(false));
    api
      .get("/app/dashboard/today")
      .then((r) => {
        if (!mounted) return;
        setToday(r.data || null);
        setTodayError(false);
      })
      .catch(() => {
        if (!mounted) return;
        setToday(null);
        setTodayError(true);
      })
      .finally(() => mounted && setLoadingToday(false));
    return () => {
      mounted = false;
    };
  }, []);

  const groups = today?.summary?.action_groups ?? 0;

  return (
    <AgencyShell current="dashboard">
      <section data-testid="dashboard-page" className="space-y-10">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · {t("dashboard.today_brand", "Oggi")}</Brand>
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("dashboard.today_heading", "Cosa fare oggi")}
            {user?.name?.split(" ")[0] ? `, ${user.name.split(" ")[0]}` : ""}.
          </h1>
          <p className="mt-2 text-sm font-sans text-stone-600 max-w-2xl">
            {t(
              "dashboard.today_subtitle",
              "Priorità operative dell’agenzia — poi i numeri di stato."
            )}
            {!loadingToday && groups > 0 && (
              <span className="text-stone-500">
                {" "}
                · {groups} {t("dashboard.today_queues", "code di lavoro")}
              </span>
            )}
          </p>
        </div>

        <div
          data-testid="dashboard-quick-actions"
          className="flex flex-wrap gap-2"
        >
          {QUICK_ACTIONS.map((a) => (
            <Link
              key={a.key}
              to={`/${l}/app/${a.to}`}
              data-testid={`qa-${a.key}`}
              className="inline-flex items-center px-3.5 py-2 text-[11px] font-sans uppercase tracking-widest border border-stone-300 bg-white text-stone-800 hover:border-stone-900 hover:bg-stone-900 hover:text-white transition"
            >
              {t(a.labelKey, a.fallback)}
            </Link>
          ))}
        </div>

        <section aria-labelledby="today-cockpit-title">
          <h2 id="today-cockpit-title" className="sr-only">
            {t("dashboard.today_heading", "Cosa fare oggi")}
          </h2>
          {todayError ? (
            <p data-testid="today-cockpit-error" className="text-sm text-stone-600 font-sans">
              {t("dashboard.today_error", "Impossibile caricare le priorità di oggi. Riprova tra poco.")}
            </p>
          ) : (
            <TodayCockpit today={today} loading={loadingToday} lang={l} t={t} />
          )}
          <RecentStrip recent={today?.recent} t={t} />
        </section>

        <section aria-labelledby="kpi-section-title" className="space-y-4">
          <div>
            <h2
              id="kpi-section-title"
              className="text-sm uppercase tracking-[0.2em] text-stone-500 font-sans"
            >
              {t("dashboard.kpis_section", "Stato agenzia")}
            </h2>
            <p className="mt-1 text-xs text-stone-500 max-w-2xl font-sans">
              {t("dashboard.kpis_locked_hint")}
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="kpi-grid">
            {loadingKpis
              ? Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-32 rounded-xl bg-stone-100 animate-pulse" />
                ))
              : kpis.map((kpi) => <KPICard key={kpi.key} kpi={kpi} />)}
          </div>
        </section>
      </section>
    </AgencyShell>
  );
}
