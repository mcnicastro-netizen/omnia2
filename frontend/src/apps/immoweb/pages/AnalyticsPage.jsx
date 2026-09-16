import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import AgencyShell from "../components/AgencyShell";
import { api } from "../../../shared/lib/api";

/**
 * A/B analytics dashboard — compare 2–6 listings on views/leads/CTR.
 */
export default function AnalyticsPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [props, setProps] = useState([]);
  const [selected, setSelected] = useState([]);
  const [days, setDays] = useState(30);
  const [result, setResult] = useState(null);
  const [overview, setOverview] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/app/properties?page=1&page_size=100")
      .then((r) => setProps(r.data.items || r.data.properties || []))
      .catch(() => setProps([]));
    api.get("/app/analytics/agency/overview?days_lookback=30")
      .then((r) => setOverview(r.data))
      .catch(() => {});
  }, []);

  const toggle = (id) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 6) return prev;
      return [...prev, id];
    });
  };

  const run = async () => {
    if (selected.length < 2) {
      setError("Seleziona almeno 2 immobili");
      return;
    }
    setBusy(true);
    setError("");
    try {
      const { data } = await api.post("/app/analytics/ab-test", {
        property_ids: selected,
        days_lookback: days,
      });
      setResult(data);
    } catch (e) {
      setError(e?.response?.data?.detail || "Errore confronto");
    } finally {
      setBusy(false);
    }
  };

  return (
    <AgencyShell current="analytics">
      <section data-testid="analytics-page" className="space-y-6">
        <div>
          <h1 className="text-3xl tracking-tight" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
            Analytics A/B
          </h1>
          <p className="text-stone-600 mt-1 text-sm">
            Confronta views, lead e conversion rate tra 2–6 annunci della tua agenzia.
          </p>
        </div>

        {overview && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="analytics-overview">
            <Stat label="Immobili attivi" value={overview.properties?.active} />
            <Stat label="Lead totali" value={overview.leads?.total} />
            <Stat label="Lead periodo" value={overview.leads?.recent_period} />
            <Stat label="Sync OK" value={overview.publishing_recent?.sync_success} />
          </div>
        )}

        <div className="bg-white border border-stone-200 rounded-lg p-4 space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <label className="text-xs uppercase tracking-widest text-stone-500">
              Giorni
              <input
                type="number"
                min={1}
                max={365}
                value={days}
                onChange={(e) => setDays(Number(e.target.value) || 30)}
                className="ml-2 w-20 px-2 py-1 border border-stone-300 rounded text-sm"
              />
            </label>
            <button
              type="button"
              data-testid="analytics-run"
              disabled={busy || selected.length < 2}
              onClick={run}
              className="px-4 py-2 bg-stone-900 text-white text-xs uppercase tracking-widest rounded disabled:opacity-40"
            >
              {busy ? "Calcolo…" : `Confronta (${selected.length})`}
            </button>
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="max-h-64 overflow-y-auto space-y-1" data-testid="analytics-property-picker">
            {props.map((p) => (
              <label key={p.id} className="flex items-center gap-2 text-sm py-1 border-b border-stone-100">
                <input
                  type="checkbox"
                  checked={selected.includes(p.id)}
                  onChange={() => toggle(p.id)}
                />
                <span className="truncate">{p.title || p.id}</span>
                <span className="text-stone-400 text-xs ml-auto">{p.city}</span>
              </label>
            ))}
            {props.length === 0 && (
              <p className="text-sm text-stone-500">
                Nessun immobile.{" "}
                <Link to={`/${lang}/app/properties/new`} className="underline">Crea il primo</Link>
              </p>
            )}
          </div>
        </div>

        {result && (
          <div data-testid="analytics-results" className="space-y-3">
            <p className="text-sm text-stone-600">
              Vincitore: <strong>{result.winner_id}</strong> · media views {result.avg_views} · media lead {result.avg_leads}
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-stone-200">
                <thead className="bg-stone-100 text-left text-xs uppercase tracking-widest text-stone-500">
                  <tr>
                    <th className="p-2">Annuncio</th>
                    <th className="p-2">Views</th>
                    <th className="p-2">Lead</th>
                    <th className="p-2">CTR</th>
                    <th className="p-2">Δ views</th>
                    <th className="p-2">Sync OK</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.items || []).map((m) => (
                    <tr key={m.id} className={m.id === result.winner_id ? "bg-emerald-50" : ""}>
                      <td className="p-2">
                        <Link to={`/${lang}/app/properties/${m.id}`} className="underline">
                          {m.title || m.id}
                        </Link>
                      </td>
                      <td className="p-2">{m.views_total}</td>
                      <td className="p-2">{m.leads_total}</td>
                      <td className="p-2">{m.conversion_rate != null ? (m.conversion_rate * 100).toFixed(2) + "%" : "—"}</td>
                      <td className="p-2">{m.delta_views_vs_avg}</td>
                      <td className="p-2">{m.publishing?.sync_success ?? 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>
    </AgencyShell>
  );
}

function Stat({ label, value }) {
  return (
    <div className="bg-white border border-stone-200 rounded-lg p-3">
      <p className="text-[10px] uppercase tracking-widest text-stone-400">{label}</p>
      <p className="text-2xl font-light mt-1" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
        {value ?? "—"}
      </p>
    </div>
  );
}
