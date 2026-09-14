import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * Cruscotto Founder (super_admin) — monitoraggio HAL Legal / costi.
 * Route: /:lang/app/ops/legal
 */
export default function FounderLegalOpsPage() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(true);

  const load = async (d = days) => {
    setBusy(true);
    setError(null);
    try {
      const r = await api.get(`/app/legal/ops/overview?days=${d}`);
      setData(r.data);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      setError(
        detail === "forbidden" || e?.response?.status === 403
          ? "Solo il founder (super admin) può aprire questo cruscotto."
          : "Non riesco a caricare i dati. Riprova."
      );
      setData(null);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    load(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [days]);

  const v = data?.volume || {};
  const c = data?.costs || {};
  const p = data?.providers || {};
  const maxDay = Math.max(1, ...(data?.by_day || []).map((d) => d.queries));

  return (
    <AgencyShell current="ops">
      <section data-testid="founder-legal-ops" className="space-y-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
              <Brand>Founder · Ops · Legal</Brand>
            </p>
            <h1
              className="text-3xl md:text-4xl tracking-tight text-[#0B1E3F]"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              Cruscotto HAL Legal
            </h1>
            <p className="text-sm text-stone-600 mt-2 max-w-2xl">
              Dettaglio HAL Legal.{" "}
              <Link to={`/${lang}/app/ops`} className="text-[#1F6B5C] underline">
                ← Torna a tutti i costi
              </Link>
            </p>
          </div>
          <div className="flex items-center gap-2">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDays(d)}
                className={`text-xs uppercase tracking-widest px-3 py-1.5 rounded border transition ${
                  days === d
                    ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                    : "border-stone-300 text-stone-600 hover:bg-stone-100"
                }`}
              >
                {d}g
              </button>
            ))}
            <button
              type="button"
              onClick={() => load(days)}
              className="text-xs uppercase tracking-widest px-3 py-1.5 rounded border border-stone-300 text-stone-600 hover:bg-stone-100"
            >
              Aggiorna
            </button>
          </div>
        </div>

        {busy && !data ? (
          <p className="text-sm text-stone-500 uppercase tracking-widest">Caricamento…</p>
        ) : null}

        {error ? (
          <div className="text-sm text-red-800 bg-red-50 border border-red-200 rounded p-3">{error}</div>
        ) : null}

        {data ? (
          <>
            {/* Policy strip */}
            <div className="rounded-lg border border-emerald-200 bg-emerald-50/60 px-4 py-3 text-sm text-emerald-950">
              <strong>Politica:</strong> in agenzia = incluso · API partner = crediti · privato B2C = a pagamento
            </div>

            {/* KPI */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Kpi label="Domande periodo" value={v.total_queries ?? 0} />
              <Kpi label="Questo mese" value={v.month_to_date ?? 0} />
              <Kpi label="Confidence media" value={`${Math.round((v.avg_confidence || 0) * 100)}%`} />
              <Kpi
                label="Costo effettivo mese"
                value={`€ ${(c.month_effective_eur ?? 0).toFixed(2)}`}
                hint="Gemini + Tavily oltre free"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Kpi label="Stima lorda periodo" value={`€ ${(c.period_gross_eur ?? 0).toFixed(2)}`} hint="prima del free Tavily" />
              <Kpi label="Valore listino (€0,60)" value={`€ ${(c.period_list_price_value_eur ?? 0).toFixed(2)}`} hint="se fossero tutte a crediti" />
              <Kpi label="€ / domanda (stima)" value={`€ ${(c.per_query_eur ?? 0).toFixed(3)}`} />
            </div>

            {/* Providers */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="rounded-lg border border-stone-200 bg-white p-4">
                <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">Provider</h2>
                <ul className="space-y-2 text-sm text-stone-800">
                  <li className="flex justify-between gap-3">
                    <span>Gemini (LLM)</span>
                    <StatusOk ok={p.llm_configured} label={p.model || "—"} />
                  </li>
                  <li className="flex justify-between gap-3">
                    <span>Tavily (fonti)</span>
                    <StatusOk ok={p.tavily_configured} label={p.tavily_configured ? "chiave OK" : "manca chiave"} />
                  </li>
                  <li className="flex justify-between gap-3">
                    <span>Crediti Tavily usati (mese)</span>
                    <span className="font-medium">{c.month_tavily_credits_used ?? 0}</span>
                  </li>
                  <li className="flex justify-between gap-3">
                    <span>Free Tavily rimasti</span>
                    <span className={`font-medium ${(c.month_tavily_free_credits_left ?? 0) < 100 ? "text-amber-700" : "text-emerald-700"}`}>
                      {c.month_tavily_free_credits_left ?? 0} / 1000
                    </span>
                  </li>
                </ul>
                {!p.tavily_configured ? (
                  <p className="mt-3 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded p-2">
                    Senza <code>TAVILY_API_KEY</code> le citazioni live non partono.
                  </p>
                ) : null}
              </div>

              <div className="rounded-lg border border-stone-200 bg-white p-4">
                <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">Dettaglio volume</h2>
                <ul className="space-y-2 text-sm text-stone-800">
                  <li className="flex justify-between"><span>Chat</span><span>{v.chats ?? 0}</span></li>
                  <li className="flex justify-between"><span>Analisi PDF</span><span>{v.pdf_analyses ?? 0}</span></li>
                  <li className="flex justify-between"><span>Con fonti</span><span>{v.with_citations ?? 0}</span></li>
                  <li className="flex justify-between"><span>API Track B (legal)</span><span>{data.api_track_b?.calls ?? 0} · {data.api_track_b?.credits_charged ?? 0} cr</span></li>
                </ul>
                <p className="mt-3 text-[11px] text-stone-500">{c.assumptions?.note}</p>
              </div>
            </div>

            {/* Chart by day */}
            <div className="rounded-lg border border-stone-200 bg-white p-4">
              <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-4">Andamento giornaliero</h2>
              {(data.by_day || []).length === 0 ? (
                <p className="text-sm text-stone-500">Nessuna domanda nel periodo. I dati arriveranno appena userai HAL Legal.</p>
              ) : (
                <div className="flex items-end gap-1 h-32 overflow-x-auto">
                  {data.by_day.map((d) => (
                    <div key={d.day} className="flex flex-col items-center gap-1 min-w-[18px] flex-1" title={`${d.day}: ${d.queries}`}>
                      <span className="text-[9px] text-stone-500">{d.queries}</span>
                      <div
                        className="w-full bg-[#1F6B5C] rounded-t"
                        style={{ height: `${Math.max(4, (d.queries / maxDay) * 100)}%` }}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <SimpleTable
                title="Top utenti"
                empty="Nessun utente ancora"
                rows={(data.top_users || []).map((u) => [
                  u.name || u.email || u.user_id?.slice(0, 8) || "—",
                  `${u.queries} dom.`,
                ])}
              />
              <SimpleTable
                title="Top agenzie"
                empty="Nessuna agenzia ancora"
                rows={(data.top_agencies || []).map((a) => [a.name, `${a.queries} dom.`])}
              />
            </div>

            <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
              <div className="px-4 py-3 border-b border-stone-200">
                <h2 className="text-xs uppercase tracking-widest text-stone-500">Ultime domande</h2>
              </div>
              {(data.recent || []).length === 0 ? (
                <p className="p-4 text-sm text-stone-500">Ancora nessuna attività.</p>
              ) : (
                <ul className="divide-y divide-stone-100">
                  {data.recent.map((r, i) => (
                    <li key={i} className="px-4 py-3 text-sm">
                      <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-stone-500">
                        <span>{r.ts ? new Date(r.ts).toLocaleString("it-IT") : "—"} · {r.kind}</span>
                        <span>
                          conf. {Math.round((r.confidence || 0) * 100)}% · fonti {r.citation_count || 0}
                          {r.cost_estimate?.total_eur != null ? ` · ~€${r.cost_estimate.total_eur}` : ""}
                        </span>
                      </div>
                      <p className="text-stone-800 mt-1">{r.preview || "—"}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        ) : null}
      </section>
    </AgencyShell>
  );
}

function Kpi({ label, value, hint }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4">
      <p className="text-[10px] uppercase tracking-widest text-stone-500">{label}</p>
      <p className="text-2xl mt-1 text-[#0B1E3F]" style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
        {value}
      </p>
      {hint ? <p className="text-[11px] text-stone-500 mt-1">{hint}</p> : null}
    </div>
  );
}

function StatusOk({ ok, label }) {
  return (
    <span className={`text-xs font-medium ${ok ? "text-emerald-700" : "text-amber-700"}`}>
      {ok ? "●" : "○"} {label}
    </span>
  );
}

function SimpleTable({ title, rows, empty }) {
  return (
    <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
      <div className="px-4 py-3 border-b border-stone-200">
        <h2 className="text-xs uppercase tracking-widest text-stone-500">{title}</h2>
      </div>
      {rows.length === 0 ? (
        <p className="p-4 text-sm text-stone-500">{empty}</p>
      ) : (
        <ul className="divide-y divide-stone-100">
          {rows.map((r, i) => (
            <li key={i} className="px-4 py-2.5 text-sm flex justify-between gap-3">
              <span className="truncate text-stone-800">{r[0]}</span>
              <span className="text-stone-500 whitespace-nowrap">{r[1]}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
