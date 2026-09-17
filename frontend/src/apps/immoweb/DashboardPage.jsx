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
  { key: "matches", to: "matches", labelKey: "dashboard.qa_matches", fallback: "Match" },
  { key: "publishing", to: "publishing", labelKey: "dashboard.qa_publishing", fallback: "Portali" },
  { key: "hal", to: "hal-knowledge", labelKey: "dashboard.qa_hal", fallback: "HAL Knowledge" },
];

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const { lang } = useParams();
  const l = (lang || "it").slice(0, 2);
  const [kpis, setKpis] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    api
      .get("/app/dashboard/kpis")
      .then((r) => mounted && setKpis(r.data || []))
      .catch(() => mounted && setKpis([]))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <AgencyShell current="dashboard">
      <section data-testid="dashboard-page" className="space-y-8">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · {t("dashboard.title")}</Brand>
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("dashboard.welcome")}, {user?.name?.split(" ")[0] || ""}.
          </h1>
          <p className="mt-2 text-sm font-sans text-stone-600 max-w-2xl">
            {t("dashboard.subtitle", "Portafoglio, clienti, match e portali — tutto da qui.")}
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

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="kpi-grid">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-32 rounded-xl bg-stone-100 animate-pulse" />
              ))
            : kpis.map((kpi) => <KPICard key={kpi.key} kpi={kpi} />)}
        </div>

        <p className="text-xs text-stone-500 max-w-2xl">
          {t("dashboard.kpis_locked_hint")}
        </p>
      </section>
    </AgencyShell>
  );
}
