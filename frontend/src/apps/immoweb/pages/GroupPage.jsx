import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth } from "../../../shared/lib/auth";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * GroupPage — M2.5.1 Multi-branch / Franchising layer (D-041).
 * Visibile solo a group_admin / super_admin.
 * Mostra: dati gruppo, KPI consolidati, elenco branch con rollup.
 */
export default function GroupPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [group, setGroup] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        // Try /groups/me first (group_admin case)
        let g = null;
        try {
          const r = await api.get("/app/groups/me");
          g = r.data;
        } catch (err) {
          if (err?.response?.status === 404) {
            // super_admin without group_id → list all and take the first (rare edge)
            if (user?.role === "super_admin") {
              const list = await api.get("/app/groups");
              g = list.data?.items?.[0] || null;
            }
          } else {
            throw err;
          }
        }
        if (!mounted) return;
        if (!g) {
          setGroup(false);
          setLoading(false);
          return;
        }
        setGroup(g);

        // Consolidated + branches in parallel
        const [kpiRes, brRes] = await Promise.all([
          api.get(`/app/groups/${g.id}/consolidated`),
          api.get(`/app/groups/${g.id}/branches`),
        ]);
        if (!mounted) return;
        setKpis(kpiRes.data);
        setBranches(brRes.data?.items || []);
      } catch (err) {
        if (mounted) setError(err?.response?.data?.detail || "load_error");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [user?.role]);

  // No group case
  if (!loading && group === false) {
    return (
      <AgencyShell current="group">
        <section data-testid="group-page-empty" className="max-w-2xl">
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · Franchising</Brand>
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight mb-4"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("group.empty_title") || "Nessun gruppo attivo"}
          </h1>
          <p className="text-stone-600 mb-6">
            {t("group.empty_hint") ||
              "Non appartieni ancora a un gruppo/holding. Da super_admin puoi crearne uno con POST /api/app/groups."}
          </p>
        </section>
      </AgencyShell>
    );
  }

  return (
    <AgencyShell current="group">
      <section data-testid="group-page" className="space-y-8">
        <div>
          <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
            <Brand>ImmoWeb · Franchising / Multi-branch</Brand>
          </p>
          <h1
            className="text-3xl md:text-4xl tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            data-testid="group-title"
          >
            {loading ? "…" : group?.name || "—"}
          </h1>
          {group?.franchise_name && (
            <p className="text-sm text-stone-600 mt-1" data-testid="group-franchise">
              {group.franchise_name}
            </p>
          )}
        </div>

        {error && (
          <div
            data-testid="group-error"
            className="border border-red-300 bg-red-50 text-red-700 text-sm px-4 py-3 rounded"
          >
            {error}
          </div>
        )}

        {/* Consolidated KPIs */}
        <div>
          <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-3">
            {t("group.consolidated") || "KPI consolidati gruppo"}
          </p>
          <div
            className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3"
            data-testid="group-consolidated-grid"
          >
            {[
              { key: "branches", label: t("group.branches") || "Filiali", value: kpis?.branches_count },
              { key: "branches_active", label: t("group.branches_active") || "Attive", value: kpis?.branches_active },
              { key: "props_active", label: t("group.properties_active") || "Immobili attivi", value: kpis?.properties_active },
              { key: "props_total", label: t("group.properties_total") || "Immobili totali", value: kpis?.properties_total },
              { key: "clients", label: t("group.clients_total") || "Clienti", value: kpis?.clients_total },
              { key: "leads_open", label: t("group.leads_open") || "Lead aperti", value: kpis?.leads_open },
            ].map((k) => (
              <div
                key={k.key}
                data-testid={`group-kpi-${k.key}`}
                className="bg-white border border-stone-200 rounded-lg px-4 py-3"
              >
                <p className="text-[10px] uppercase tracking-widest text-stone-500 mb-1">
                  {k.label}
                </p>
                <p
                  className="text-2xl font-medium text-stone-900"
                  style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                >
                  {loading ? "—" : k.value ?? 0}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Branches list */}
        <div>
          <div className="flex items-baseline justify-between mb-3">
            <p className="text-[10px] uppercase tracking-widest text-stone-500">
              {t("group.branches_list") || "Filiali del gruppo"}
            </p>
            <p className="text-xs text-stone-500" data-testid="group-branches-count">
              {branches.length} {t("group.total") || "totali"}
            </p>
          </div>
          <div className="border border-stone-200 rounded-lg overflow-hidden bg-white">
            <table className="w-full text-sm">
              <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">
                    {t("group.branch_name") || "Filiale"}
                  </th>
                  <th className="text-left px-4 py-3 font-medium">
                    {t("group.branch_code") || "Codice"}
                  </th>
                  <th className="text-left px-4 py-3 font-medium">
                    {t("group.city") || "Città"}
                  </th>
                  <th className="text-left px-4 py-3 font-medium">
                    {t("group.plan_type") || "Track"}
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    {t("group.properties_active") || "Immobili"}
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    {t("group.clients_total") || "Clienti"}
                  </th>
                  <th className="text-right px-4 py-3 font-medium">
                    {t("group.leads_open") || "Lead"}
                  </th>
                </tr>
              </thead>
              <tbody data-testid="group-branches-table-body">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-6 text-stone-500 text-center">
                      …
                    </td>
                  </tr>
                ) : branches.length === 0 ? (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-4 py-6 text-stone-500 text-center"
                      data-testid="group-branches-empty"
                    >
                      {t("group.no_branches") ||
                        "Nessuna filiale collegata. Da super_admin: POST /api/app/groups/{id}/branches."}
                    </td>
                  </tr>
                ) : (
                  branches.map((b) => (
                    <tr
                      key={b.id}
                      data-testid={`group-branch-row-${b.id}`}
                      className="border-t border-stone-200 hover:bg-stone-50"
                    >
                      <td className="px-4 py-3">
                        <span className="font-medium text-stone-900">{b.display_name}</span>
                        {!b.is_active && (
                          <span className="ml-2 text-[9px] uppercase tracking-widest text-stone-400">
                            inactive
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-stone-600 font-mono text-xs">
                        {b.branch_code || "—"}
                      </td>
                      <td className="px-4 py-3 text-stone-600">{b.city || "—"}</td>
                      <td className="px-4 py-3">
                        <span
                          className="inline-block px-2 py-0.5 rounded text-[10px] uppercase tracking-widest bg-stone-100 text-stone-700"
                          data-testid={`branch-plan-type-${b.id}`}
                        >
                          {b.plan_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-stone-900">
                        {b.properties_active}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-stone-900">
                        {b.clients_total}
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-stone-900">
                        {b.leads_open}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <p className="text-xs text-stone-500 max-w-2xl">
          {t("group.footer_hint") ||
            "M2.5.1 (D-041) — visione consolidata del gruppo. Creazione/gestione filiali via API in questa fase; UI amministrativa completa arriva nel prossimo sprint."}
        </p>
      </section>
    </AgencyShell>
  );
}
