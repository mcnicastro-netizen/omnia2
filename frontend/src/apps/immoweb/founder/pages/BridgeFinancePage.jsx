import React, { useEffect, useState } from "react";
import { api } from "../../../../shared/lib/api";

function Kpi({ label, value, hint }) {
  return (
    <div className="bg-white border border-stone-200 rounded-lg px-4 py-4">
      <p className="text-[10px] uppercase tracking-widest text-stone-500">{label}</p>
      <p
        className="mt-2 text-2xl text-[#0B1E3F] font-light"
        style={{ fontFamily: "'Fraunces', Georgia, serif" }}
      >
        {value}
      </p>
      {hint ? <p className="text-xs text-stone-500 mt-1">{hint}</p> : null}
    </div>
  );
}

export default function BridgeFinancePage() {
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    setBusy(true);
    setErr(null);
    api
      .get(`/app/ops/overview?days=${days}`)
      .then((r) => setData(r.data))
      .catch(() => {
        setErr("Overview non disponibile.");
        setData(null);
      })
      .finally(() => setBusy(false));
  }, [days]);

  const t = data?.totals || {};
  const finance = data?.finance || {};

  return (
    <div data-testid="bridge-finance" className="space-y-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1
            className="text-3xl text-[#0B1E3F] tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            Finanze
          </h1>
          <p className="mt-2 text-sm text-stone-600 max-w-2xl">
            Costi AI, incassi B2C/B2B, margini. Telemetria operativa — non sostituisce la
            contabilità.
          </p>
        </div>
        <div className="flex gap-2">
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setDays(d)}
              className={`text-xs uppercase tracking-widest px-3 py-1.5 rounded border ${
                days === d
                  ? "bg-[#0B1E3F] text-white border-[#0B1E3F]"
                  : "border-stone-300 text-stone-600"
              }`}
            >
              {d}g
            </button>
          ))}
        </div>
      </header>

      {busy ? <p className="text-sm text-stone-500">Caricamento…</p> : null}
      {err ? <p className="text-sm text-red-700">{err}</p> : null}

      {data ? (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Kpi
              label="Incassi periodo"
              value={`€ ${(t.revenue_eur ?? finance.revenue_eur ?? 0).toFixed(2)}`}
            />
            <Kpi
              label="COGS stimati"
              value={`€ ${(t.cogs_eur ?? finance.cogs_total_eur ?? 0).toFixed(2)}`}
            />
            <Kpi
              label="Margine"
              value={`€ ${(t.margin_eur ?? finance.margin_total_eur ?? 0).toFixed(2)}`}
            />
            <Kpi
              label="Fee Stripe"
              value={`€ ${(finance.stripe_fees_eur ?? 0).toFixed(2)}`}
            />
          </div>

          {(data.services || []).length ? (
            <section>
              <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-3">
                Per servizio
              </h2>
              <div className="overflow-x-auto border border-stone-200 rounded-lg bg-white">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-stone-200 text-[10px] uppercase tracking-widest text-stone-500 text-left">
                      <th className="px-3 py-2">Servizio</th>
                      <th className="px-3 py-2 text-right">Eventi</th>
                      <th className="px-3 py-2 text-right">COGS €</th>
                      <th className="px-3 py-2 text-right">A listino €</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.services.map((s) => (
                      <tr key={s.key || s.label} className="border-b border-stone-100 last:border-0">
                        <td className="px-3 py-2">{s.label || s.key}</td>
                        <td className="px-3 py-2 text-right">{s.events ?? s.count ?? "—"}</td>
                        <td className="px-3 py-2 text-right">
                          {(s.cogs_eur ?? 0).toFixed?.(2) ?? s.cogs_eur}
                        </td>
                        <td className="px-3 py-2 text-right">
                          {(s.list_eur ?? s.listed_eur ?? 0).toFixed?.(2) ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}

          {data.portal ? (
            <section className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Kpi label="Reg. B2C" value={data.portal.b2c_registrations_period ?? 0} />
              <Kpi label="Pagamenti B2C" value={data.portal.b2c_paid_period ?? 0} />
              <Kpi label="Lead mutui" value={data.portal.mortgage_leads_period ?? 0} />
              <Kpi label="Inquiry UGC" value={data.portal.listing_inquiries_period ?? 0} />
            </section>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
