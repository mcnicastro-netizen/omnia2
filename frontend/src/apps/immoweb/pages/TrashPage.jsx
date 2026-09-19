import React, { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";

/**
 * Cestino — immobili e clienti eliminati, recuperabili per 30 giorni.
 */
export default function TrashPage() {
  const { t } = useTranslation();
  const [items, setItems] = useState([]);
  const [retentionDays, setRetentionDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [busyId, setBusyId] = useState(null);
  const [filter, setFilter] = useState("all");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = filter === "all" ? {} : { kind: filter };
      const { data } = await api.get("/app/trash", { params });
      setItems(data.items || []);
      setRetentionDays(data.retention_days || 30);
    } catch (e) {
      setError(
        e?.response?.data?.detail ||
          t("trash.load_error") ||
          "Non riesco a caricare il Cestino."
      );
    } finally {
      setLoading(false);
    }
  }, [filter, t]);

  useEffect(() => {
    load();
  }, [load]);

  const restore = async (item) => {
    setBusyId(item.id);
    try {
      await api.post(`/app/trash/${item.kind}/${item.id}/restore`);
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || t("trash.restore_error"));
    } finally {
      setBusyId(null);
    }
  };

  const purgeNow = async (item) => {
    const ok = window.confirm(
      t("trash.purge_confirm") ||
        "Eliminare per sempre? Dopo non si può più recuperare."
    );
    if (!ok) return;
    setBusyId(item.id);
    try {
      await api.delete(`/app/trash/${item.kind}/${item.id}`);
      await load();
    } catch (e) {
      setError(e?.response?.data?.detail || t("trash.purge_error"));
    } finally {
      setBusyId(null);
    }
  };

  const kindLabel = (kind) =>
    kind === "property"
      ? t("trash.kind_property") || "Immobile"
      : t("trash.kind_client") || "Cliente";

  return (
    <AgencyShell current="trash">
      <section data-testid="trash-page" className="space-y-6">
        <header className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="font-display text-3xl text-stone-900 tracking-tight">
              {t("trash.title") || "Cestino"}
            </h1>
            <p className="text-stone-600 mt-1 max-w-xl">
              {t("trash.subtitle", { days: retentionDays }) ||
                `Qui trovi immobili e clienti eliminati. Puoi ripristinarli entro ${retentionDays} giorni.`}
            </p>
          </div>
          <div className="flex gap-2">
            {[
              ["all", t("trash.filter_all") || "Tutti"],
              ["property", t("trash.filter_properties") || "Immobili"],
              ["client", t("trash.filter_clients") || "Clienti"],
            ].map(([k, label]) => (
              <button
                key={k}
                type="button"
                onClick={() => setFilter(k)}
                className={`px-3 py-1.5 text-xs uppercase tracking-widest rounded-md border ${
                  filter === k
                    ? "bg-stone-900 text-stone-50 border-stone-900"
                    : "bg-white text-stone-600 border-stone-200 hover:border-stone-400"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </header>

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 text-rose-800 text-sm px-4 py-3">
            {typeof error === "string" ? error : JSON.stringify(error)}
          </div>
        )}

        {loading ? (
          <p className="text-stone-500 text-sm">{t("common.loading") || "Caricamento…"}</p>
        ) : items.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-stone-200 rounded-lg">
            <p className="text-lg text-stone-800 font-medium">
              {t("trash.empty_title") || "Cestino vuoto"}
            </p>
            <p className="text-stone-500 mt-2 max-w-md mx-auto">
              {t("trash.empty_subtitle") ||
                "Quando elimini un immobile o un cliente, lo trovi qui per 30 giorni."}
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-stone-200 border border-stone-200 rounded-lg bg-white">
            {items.map((item) => (
              <li
                key={`${item.kind}-${item.id}`}
                className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between px-4 py-4"
                data-testid={`trash-row-${item.kind}-${item.id}`}
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] uppercase tracking-widest text-stone-500 border border-stone-200 px-1.5 py-0.5 rounded">
                      {kindLabel(item.kind)}
                    </span>
                    <h2 className="text-stone-900 font-medium truncate">{item.title}</h2>
                  </div>
                  {item.subtitle ? (
                    <p className="text-sm text-stone-500 mt-0.5 truncate">{item.subtitle}</p>
                  ) : null}
                  <p className="text-xs text-stone-400 mt-1">
                    {typeof item.days_left === "number"
                      ? t("trash.days_left", { days: item.days_left }) ||
                        `Ancora ${item.days_left} giorni per ripristinare`
                      : t("trash.days_unknown") || "Tempo di recupero in corso"}
                  </p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    type="button"
                    disabled={busyId === item.id}
                    onClick={() => restore(item)}
                    className="px-3 py-2 text-xs uppercase tracking-widest bg-emerald-700 text-white rounded-md hover:bg-emerald-800 disabled:opacity-50"
                    data-testid={`trash-restore-${item.id}`}
                  >
                    {t("trash.restore") || "Ripristina"}
                  </button>
                  <button
                    type="button"
                    disabled={busyId === item.id}
                    onClick={() => purgeNow(item)}
                    className="px-3 py-2 text-xs uppercase tracking-widest border border-rose-300 text-rose-700 rounded-md hover:bg-rose-50 disabled:opacity-50"
                    data-testid={`trash-purge-${item.id}`}
                  >
                    {t("trash.purge") || "Elimina per sempre"}
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </AgencyShell>
  );
}
