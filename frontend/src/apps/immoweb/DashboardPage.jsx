import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import AgencyShell from "./components/AgencyShell";
import KPICard from "./components/KPICard";
import { api } from "../../shared/lib/api";
import { useAuth } from "../../shared/lib/auth";
import Brand from "../../shared/components/Brand";

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
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
        </div>

        {/* KPI grid */}
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
