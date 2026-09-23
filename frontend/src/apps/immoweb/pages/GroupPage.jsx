import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import { useAuth } from "../../../shared/lib/auth";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * GroupPage — M2.5.1 Multi-branch / Franchising (D-041).
 * Wizard: crea gruppo · collega filiale esistente.
 */
export default function GroupPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [group, setGroup] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [branches, setBranches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadTick, setReloadTick] = useState(0);

  // Create wizard
  const [createForm, setCreateForm] = useState({ name: "", franchise_name: "", credits_mode: "branch" });
  const [creating, setCreating] = useState(false);

  // Attach branch wizard
  const [attachOpen, setAttachOpen] = useState(false);
  const [attachable, setAttachable] = useState([]);
  const [attachAgencyId, setAttachAgencyId] = useState("");
  const [attachCode, setAttachCode] = useState("");
  const [attaching, setAttaching] = useState(false);

  const reload = () => setReloadTick((n) => n + 1);

  useEffect(() => {
    let mounted = true;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        let g = null;
        try {
          const r = await api.get("/app/groups/me");
          g = r.data;
        } catch (err) {
          if (err?.response?.status === 404) {
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
  }, [user?.role, reloadTick]);

  const onCreateGroup = async (e) => {
    e.preventDefault();
    if (!createForm.name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await api.post("/app/groups", {
        name: createForm.name.trim(),
        franchise_name: createForm.franchise_name.trim() || null,
        credits_mode: createForm.credits_mode || "branch",
      });
      // Dopo create, /groups/me usa group_id sul user — ricarica sessione se serve
      try {
        await api.get("/auth/me");
      } catch {
        /* ignore */
      }
      window.location.reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "create_error");
      setCreating(false);
    }
  };

  const openAttach = async () => {
    setAttachOpen(true);
    setError(null);
    try {
      // Agenzie dell'utente non ancora in un gruppo
      const r = await api.get("/auth/my-agencies");
      const mine = r.data?.items || [];
      const free = mine.filter((a) => !a.group_id);
      // Se già in tabella branches, escludile
      const branchIds = new Set(branches.map((b) => b.id));
      setAttachable(free.filter((a) => !branchIds.has(a.id)));
      setAttachAgencyId(free[0]?.id || "");
    } catch {
      setAttachable([]);
    }
  };

  const onAttach = async (e) => {
    e.preventDefault();
    if (!group?.id || !attachAgencyId) return;
    setAttaching(true);
    setError(null);
    try {
      await api.post(`/app/groups/${group.id}/branches`, {
        agency_id: attachAgencyId,
        branch_code: attachCode.trim() || null,
      });
      setAttachOpen(false);
      setAttachCode("");
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "attach_error");
    } finally {
      setAttaching(false);
    }
  };

  // No group case — create wizard
  if (!loading && group === false) {
    return (
      <AgencyShell current="group">
        <section data-testid="group-page-empty" className="max-w-xl space-y-6">
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
              <Brand>ImmoWeb · Franchising</Brand>
            </p>
            <h1
              className="text-3xl md:text-4xl tracking-tight mb-2"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("group.empty_title") || "Nessun gruppo attivo"}
            </h1>
            <p className="text-stone-600">
              {t("group.empty_wizard_hint")}
            </p>
          </div>

          {error && (
            <div data-testid="group-error" className="border border-red-300 bg-red-50 text-red-700 text-sm px-4 py-3 rounded">
              {typeof error === "string" ? error : JSON.stringify(error)}
            </div>
          )}

          <form
            data-testid="group-create-form"
            onSubmit={onCreateGroup}
            className="border border-stone-200 bg-white rounded-lg p-5 space-y-4"
          >
            <div>
              <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
                {t("group.create_name")}
              </label>
              <input
                data-testid="group-create-name"
                value={createForm.name}
                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm"
                required
                minLength={2}
                placeholder={t("group.create_name_placeholder")}
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
                {t("group.create_franchise")}
              </label>
              <input
                data-testid="group-create-franchise"
                value={createForm.franchise_name}
                onChange={(e) => setCreateForm({ ...createForm, franchise_name: e.target.value })}
                className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm"
                placeholder={t("group.create_franchise_placeholder")}
              />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
                {t("group.create_credits_mode")}
              </label>
              <select
                data-testid="group-create-credits"
                value={createForm.credits_mode}
                onChange={(e) => setCreateForm({ ...createForm, credits_mode: e.target.value })}
                className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm"
              >
                <option value="branch">{t("group.credits_branch")}</option>
                <option value="central">{t("group.credits_central")}</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={creating}
              data-testid="group-create-submit"
              className="px-5 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700 disabled:opacity-50"
            >
              {creating ? "…" : t("group.create_submit")}
            </button>
          </form>
        </section>
      </AgencyShell>
    );
  }

  return (
    <AgencyShell current="group">
      <section data-testid="group-page" className="space-y-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
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
          <button
            type="button"
            data-testid="group-attach-open"
            onClick={openAttach}
            className="px-4 py-2.5 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md hover:bg-stone-700"
          >
            {t("group.attach_branch_btn")}
          </button>
        </div>

        {error && (
          <div
            data-testid="group-error"
            className="border border-red-300 bg-red-50 text-red-700 text-sm px-4 py-3 rounded"
          >
            {typeof error === "string" ? error : JSON.stringify(error)}
          </div>
        )}

        {attachOpen && (
          <form
            data-testid="group-attach-form"
            onSubmit={onAttach}
            className="border border-stone-200 bg-white rounded-lg p-5 space-y-4 max-w-lg"
          >
            <h2 className="text-lg tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
              {t("group.attach_title")}
            </h2>
            <p className="text-sm text-stone-600">{t("group.attach_hint")}</p>
            {attachable.length === 0 ? (
              <p data-testid="group-attach-empty" className="text-sm text-stone-500">
                {t("group.attach_none")}
              </p>
            ) : (
              <>
                <div>
                  <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
                    {t("group.attach_agency")}
                  </label>
                  <select
                    data-testid="group-attach-agency"
                    value={attachAgencyId}
                    onChange={(e) => setAttachAgencyId(e.target.value)}
                    className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm"
                    required
                  >
                    {attachable.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.display_name || a.name || a.id}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs uppercase tracking-widest text-stone-600 mb-1.5">
                    {t("group.attach_code")}
                  </label>
                  <input
                    data-testid="group-attach-code"
                    value={attachCode}
                    onChange={(e) => setAttachCode(e.target.value)}
                    className="w-full px-3 py-2 border border-stone-300 rounded-md text-sm"
                    placeholder="MI-01"
                  />
                </div>
              </>
            )}
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={attaching || attachable.length === 0}
                data-testid="group-attach-submit"
                className="px-4 py-2 bg-stone-900 text-stone-50 text-xs uppercase tracking-widest rounded-md disabled:opacity-50"
              >
                {attaching ? "…" : t("group.attach_submit")}
              </button>
              <button
                type="button"
                onClick={() => setAttachOpen(false)}
                className="px-4 py-2 border border-stone-300 text-xs uppercase tracking-widest rounded-md"
              >
                {t("common.cancel") || "Annulla"}
              </button>
            </div>
          </form>
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
                      {t("group.no_branches_ui")}
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
          {t("group.footer_hint")}
        </p>
      </section>
    </AgencyShell>
  );
}
