import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import AgencyShell from "../components/AgencyShell";
import Brand from "../../../shared/components/Brand";

/**
 * Cruscotto Founder — tutti i consumi/costi OMNIA (super_admin).
 */
export default function FounderOpsPage() {
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
      const r = await api.get(`/app/ops/overview?days=${d}`);
      setData(r.data);
    } catch (e) {
      setError(
        e?.response?.status === 403
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

  const t = data?.totals || {};
  const finance = data?.finance || {};
  const monthly = finance.monthly || null;
  const maxDay = Math.max(1, ...(data?.by_day || []).map((d) => d.events));

  return (
    <AgencyShell current="ops">
      <section data-testid="founder-ops" className="space-y-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-[10px] uppercase tracking-[0.3em] text-stone-500 mb-2">
              <Brand>Founder · Ops</Brand>
            </p>
            <h1
              className="text-3xl md:text-4xl tracking-tight text-[#0B1E3F]"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              Cruscotto costi e incassi
            </h1>
            <p className="text-sm text-stone-600 mt-2 max-w-2xl">
              Incassi per voce, fatture Stripe, riepilogo mensile e consumi AI/ops.
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

        {data?.backup ? (
          <div
            className={`rounded-lg border px-4 py-3 text-sm ${
              data.backup.status === "OK"
                ? "border-emerald-300 bg-emerald-50 text-emerald-950"
                : data.backup.status === "PARTIAL"
                  ? "border-amber-300 bg-amber-50 text-amber-950"
                  : "border-rose-300 bg-rose-50 text-rose-950"
            }`}
            data-testid="ops-backup-health"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="font-medium">
                Backup ·{" "}
                <span data-testid="ops-backup-status">{data.backup.status || "—"}</span>
              </p>
              <span className="text-xs text-stone-600">
                {(data.backup.created_at || "").slice(0, 19).replace("T", " ") || "nessun run"}
                {data.backup.day ? ` · giorno ${data.backup.day}` : ""}
              </span>
            </div>
            {data.backup.message ? (
              <p className="text-xs mt-1">{data.backup.message}</p>
            ) : (
              <p className="text-xs mt-1 text-stone-600">
                Ultimo MANIFEST OK/PARTIAL/FAILED · scheduler owner:{" "}
                {data.scheduler?.owner || "apscheduler"}
              </p>
            )}
          </div>
        ) : null}

        {data?.alerts?.recent?.length ? (
          <div
            className={`rounded-lg border px-4 py-3 text-sm ${
              (data.alerts.unacked || 0) > 0
                ? "border-amber-300 bg-amber-50 text-amber-950"
                : "border-stone-200 bg-stone-50 text-stone-700"
            }`}
            data-testid="ops-alerts"
          >
            <div className="flex items-center justify-between gap-2 mb-2">
              <p className="font-medium">
                Allarmi operativi
                {(data.alerts.unacked || 0) > 0
                  ? ` · ${data.alerts.unacked} da vedere`
                  : ""}
              </p>
            </div>
            <ul className="space-y-1.5 text-xs">
              {data.alerts.recent.slice(0, 8).map((a) => (
                <li key={a.id} className="flex gap-2">
                  <span className="uppercase tracking-wider text-[10px] shrink-0 w-14">
                    {a.severity}
                  </span>
                  <span className="flex-1">{a.message}</span>
                  <span className="text-stone-400 shrink-0">
                    {(a.created_at || "").slice(0, 16).replace("T", " ")}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {data ? (
          <>
            <div className="rounded-lg border border-emerald-200 bg-emerald-50/60 px-4 py-3 text-sm text-emerald-950 space-y-1">
              <p><strong>In agenzia (incluso):</strong> {data.policy?.in_app_ai}</p>
              <p><strong>A crediti:</strong> {data.policy?.credits}</p>
              <p><strong>B2C:</strong> {data.policy?.b2c}</p>
            </div>

            {monthly ? (
              <div
                className="rounded-xl border border-[#0B1E3F]/20 bg-gradient-to-br from-[#f7f4ef] to-white p-5 space-y-4"
                data-testid="ops-monthly-pnl"
              >
                <div className="flex flex-wrap items-end justify-between gap-3">
                  <div>
                    <p className="text-[10px] uppercase tracking-widest text-[#C19A6B]">Scheda mensile</p>
                    <h2
                      className="text-2xl text-[#0B1E3F] mt-1"
                      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
                    >
                      {monthly.label || monthly.month}
                    </h2>
                  </div>
                  <p className="text-xs text-stone-500 max-w-md">{monthly.note}</p>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Kpi label="Incasso mese" value={eur(monthly.revenue_eur)} hint="B2C + B2B paid" />
                  <Kpi
                    label="Costo reale (stima)"
                    value={eur(monthly.cogs_eur)}
                    hint={`ops ${eur(monthly.ops_cogs_eur)} · prodotto ${eur(monthly.product_cogs_eur)} · Stripe ${eur(monthly.stripe_fees_eur)}`}
                  />
                  <Kpi
                    label="Margine mese"
                    value={eur(monthly.margin_eur)}
                    hint="Incasso − costo"
                    tone={(monthly.margin_eur ?? 0) >= 0 ? "good" : "bad"}
                  />
                  <Kpi
                    label="Voci con vendita"
                    value={(monthly.by_line || []).length}
                    hint="solo linee con almeno 1 pagamento"
                  />
                </div>
                {(monthly.by_line || []).length > 0 ? (
                  <ul className="text-sm divide-y divide-stone-100 border border-stone-200 rounded-lg bg-white">
                    {monthly.by_line.map((l) => (
                      <li key={l.key} className="px-4 py-2.5 flex justify-between gap-3">
                        <span>
                          {l.label}
                          <span className="text-stone-400 text-xs ml-2">×{l.count}</span>
                        </span>
                        <span className="tabular-nums text-stone-800">{eur(l.revenue_eur)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-stone-500">Nessun incasso carta nel mese corrente.</p>
                )}
              </div>
            ) : null}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Kpi label="Eventi periodo" value={t.events ?? 0} />
              <Kpi label="Costi (stima)" value={`€ ${(t.cogs_eur ?? 0).toFixed(2)}`} hint="COGS + Stripe fee" />
              <Kpi
                label="Incassi"
                value={`€ ${(t.revenue_eur ?? 0).toFixed(2)}`}
                hint={`carta ${eur(t.cash_revenue_eur)} · crediti ${eur(t.credit_revenue_eur)}`}
              />
              <Kpi
                label="Margine"
                value={`€ ${(t.margin_eur ?? 0).toFixed(2)}`}
                hint="Incassi − Costi"
                tone={(t.margin_eur ?? 0) >= 0 ? "good" : "bad"}
              />
            </div>

            {/* Incassi per voce */}
            <div className="rounded-lg border border-stone-200 bg-white overflow-hidden" data-testid="ops-revenue-lines">
              <div className="px-4 py-3 border-b border-stone-200">
                <h2 className="text-xs uppercase tracking-widest text-stone-500">Incassi per voce</h2>
                <p className="text-[11px] text-stone-500 mt-1">
                  Periodo selezionato · totale carta {eur(finance.revenue_total_eur)} · fee Stripe {eur(finance.stripe_fees_eur)}
                </p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500">
                    <tr>
                      <th className="text-left px-4 py-2 font-medium">Voce</th>
                      <th className="text-left px-4 py-2 font-medium">Canale</th>
                      <th className="text-right px-4 py-2 font-medium">N°</th>
                      <th className="text-right px-4 py-2 font-medium">Incasso €</th>
                      <th className="text-right px-4 py-2 font-medium">Costo €</th>
                      <th className="text-right px-4 py-2 font-medium">Margine €</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {(finance.revenue_lines || []).map((l) => (
                      <tr key={l.key} className={l.count ? "hover:bg-stone-50/80" : "opacity-50"}>
                        <td className="px-4 py-2.5 text-stone-900">{l.label}</td>
                        <td className="px-4 py-2.5">
                          <ChannelBadge channel={l.channel === "b2b" ? "abbonamento" : "b2c"} />
                        </td>
                        <td className="px-4 py-2.5 text-right tabular-nums">{l.count}</td>
                        <td className="px-4 py-2.5 text-right tabular-nums">{eur(l.revenue_eur)}</td>
                        <td className="px-4 py-2.5 text-right tabular-nums text-stone-500">
                          {eur(l.cogs_total_eur)}
                        </td>
                        <td className={`px-4 py-2.5 text-right tabular-nums font-medium ${
                          (l.margin_eur ?? 0) >= 0 ? "text-emerald-700" : "text-rose-700"
                        }`}>
                          {eur(l.margin_eur)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Fatture Stripe + ricevute B2C */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="rounded-lg border border-stone-200 bg-white overflow-hidden" data-testid="ops-invoices">
                <div className="px-4 py-3 border-b border-stone-200">
                  <h2 className="text-xs uppercase tracking-widest text-stone-500">Fatture emesse</h2>
                  <p className="text-[11px] text-stone-500 mt-1">{finance.invoices_note}</p>
                </div>
                {(finance.invoices || []).length === 0 ? (
                  <p className="px-4 py-4 text-sm text-stone-500">Nessuna fattura Stripe in archivio.</p>
                ) : (
                  <ul className="divide-y divide-stone-100 max-h-80 overflow-y-auto">
                    {finance.invoices.map((inv) => (
                      <li key={inv.stripe_invoice_id || inv.id} className="px-4 py-3 text-sm flex justify-between gap-3">
                        <div className="min-w-0">
                          <p className="font-medium text-stone-900 truncate">
                            {inv.number || inv.stripe_invoice_id || "—"}
                          </p>
                          <p className="text-[11px] text-stone-500 truncate">
                            {inv.customer_email || inv.customer_name || inv.description || "—"}
                            {" · "}
                            {(inv.stripe_created_at || inv.created_at || "").slice(0, 10)}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="tabular-nums">{eur(inv.amount_paid)}</p>
                          <p className="text-[10px] uppercase tracking-wider text-stone-400">{inv.status}</p>
                          {inv.hosted_invoice_url ? (
                            <a
                              href={inv.hosted_invoice_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-[10px] text-[#1F6B5C] hover:underline"
                            >
                              Apri
                            </a>
                          ) : null}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div className="rounded-lg border border-stone-200 bg-white overflow-hidden" data-testid="ops-b2c-receipts">
                <div className="px-4 py-3 border-b border-stone-200">
                  <h2 className="text-xs uppercase tracking-widest text-stone-500">Ricevute B2C (Checkout)</h2>
                  <p className="text-[11px] text-stone-500 mt-1">
                    Pagamenti one-shot carta nel periodo (visura, legal, boost, …).
                  </p>
                </div>
                {(finance.b2c_receipts || []).length === 0 ? (
                  <p className="px-4 py-4 text-sm text-stone-500">Nessuna ricevuta B2C nel periodo.</p>
                ) : (
                  <ul className="divide-y divide-stone-100 max-h-80 overflow-y-auto">
                    {finance.b2c_receipts.map((r, i) => (
                      <li key={`${r.stripe_session_id || i}`} className="px-4 py-3 text-sm flex justify-between gap-3">
                        <div className="min-w-0">
                          <p className="font-medium text-stone-900 truncate">{r.label}</p>
                          <p className="text-[11px] text-stone-500 truncate">
                            {(r.paid_at || "").slice(0, 16).replace("T", " ")}
                            {r.stripe_session_id ? ` · ${String(r.stripe_session_id).slice(0, 18)}…` : ""}
                          </p>
                        </div>
                        <p className="tabular-nums shrink-0">{eur(r.amount_eur)}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Kpi
                label="Se tutto a listino"
                value={`€ ${(t.list_value_eur ?? 0).toFixed(2)}`}
                hint={`margine teorico € ${(t.margin_if_listed_eur ?? 0).toFixed(2)}`}
              />
              <Kpi
                label="Tavily free rimasti"
                value={`${data.tavily?.free_left ?? 0} / ${data.tavily?.free_credits_month ?? 1000}`}
                hint={data.providers?.tavily_configured ? "crediti ricerca Legal" : "chiave Tavily assente"}
              />
              <Kpi
                label="Wallet crediti agenzie"
                value={data.wallets?.agency_credits_balance ?? 0}
                hint={`≈ € ${(data.wallets?.list_value_of_balance_eur ?? 0).toFixed(0)} listino`}
              />
            </div>

            {/* Services table */}
            <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
              <div className="px-4 py-3 border-b border-stone-200 flex items-center justify-between gap-3">
                <h2 className="text-xs uppercase tracking-widest text-stone-500">Servizi</h2>
                <Link
                  to={`/${lang}/app/ops/legal`}
                  className="text-[11px] uppercase tracking-widest text-[#1F6B5C] hover:underline"
                >
                  Dettaglio Legal →
                </Link>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-stone-50 text-[10px] uppercase tracking-widest text-stone-500">
                    <tr>
                      <th className="text-left px-4 py-2 font-medium">Servizio</th>
                      <th className="text-left px-4 py-2 font-medium">Canale</th>
                      <th className="text-right px-4 py-2 font-medium">Eventi</th>
                      <th className="text-right px-4 py-2 font-medium">Costi €</th>
                      <th className="text-right px-4 py-2 font-medium">Incassi €</th>
                      <th className="text-right px-4 py-2 font-medium">Margine €</th>
                      <th className="text-right px-4 py-2 font-medium">A listino €</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {(data.services || []).map((s) => (
                      <tr key={s.key} className="hover:bg-stone-50/80">
                        <td className="px-4 py-3">
                          <div className="text-stone-900 font-medium">{s.label}</div>
                          <div className="text-[11px] text-stone-500">{s.note}</div>
                        </td>
                        <td className="px-4 py-3">
                          <ChannelBadge channel={s.channel} />
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums">{s.events}</td>
                        <td className="px-4 py-3 text-right tabular-nums">
                          {s.cogs_eur == null ? "—" : eur(s.cogs_eur)}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums">
                          {eur(s.revenue_eur)}
                        </td>
                        <td className={`px-4 py-3 text-right tabular-nums font-medium ${
                          (s.margin_eur ?? 0) >= 0 ? "text-emerald-700" : "text-rose-700"
                        }`}>
                          {s.margin_eur == null ? "—" : eur(s.margin_eur)}
                        </td>
                        <td className="px-4 py-3 text-right tabular-nums text-stone-500">
                          {eur(s.list_eur)}
                          {s.margin_if_listed_eur != null ? (
                            <div className="text-[10px]">Δ {eur(s.margin_if_listed_eur)}</div>
                          ) : null}
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-stone-50 font-medium">
                      <td className="px-4 py-3" colSpan={2}>Totale</td>
                      <td className="px-4 py-3 text-right tabular-nums">{t.events ?? 0}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{eur(t.cogs_eur)}</td>
                      <td className="px-4 py-3 text-right tabular-nums">{eur(t.revenue_eur)}</td>
                      <td className={`px-4 py-3 text-right tabular-nums ${
                        (t.margin_eur ?? 0) >= 0 ? "text-emerald-700" : "text-rose-700"
                      }`}>{eur(t.margin_eur)}</td>
                      <td className="px-4 py-3 text-right tabular-nums text-stone-500">{eur(t.list_value_eur)}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="px-4 py-3 text-[11px] text-stone-500 border-t border-stone-100">
                {data.assumptions?.note}
              </p>
            </div>

            {/* Daily chart */}
            <div className="rounded-lg border border-stone-200 bg-white p-4">
              <h2 className="text-xs uppercase tracking-widest text-stone-500 mb-4">Andamento eventi</h2>
              {(data.by_day || []).length === 0 ? (
                <p className="text-sm text-stone-500">Nessun evento nel periodo.</p>
              ) : (
                <div className="flex items-end gap-1 h-32 overflow-x-auto">
                  {data.by_day.map((d) => (
                    <div key={d.day} className="flex flex-col items-center gap-1 min-w-[18px] flex-1" title={`${d.day}: ${d.events}`}>
                      <span className="text-[9px] text-stone-500">{d.events}</span>
                      <div
                        className="w-full bg-[#1F6B5C] rounded-t"
                        style={{ height: `${Math.max(4, (d.events / maxDay) * 100)}%` }}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {(data.api_by_endpoint || []).length > 0 ? (
              <div className="rounded-lg border border-stone-200 bg-white overflow-hidden">
                <div className="px-4 py-3 border-b border-stone-200">
                  <h2 className="text-xs uppercase tracking-widest text-stone-500">API Track B per endpoint</h2>
                </div>
                <ul className="divide-y divide-stone-100">
                  {data.api_by_endpoint.map((e, i) => (
                    <li key={i} className="px-4 py-2.5 text-sm flex justify-between gap-3">
                      <span className="truncate font-mono text-xs text-stone-700">{e.endpoint}</span>
                      <span className="text-stone-500 whitespace-nowrap">
                        {e.calls} call · {e.credits} cr · € {Number(e.list_eur).toFixed(2)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        ) : null}
      </section>
    </AgencyShell>
  );
}

function eur(n) {
  return `€ ${Number(n || 0).toFixed(2)}`;
}

function Kpi({ label, value, hint, tone }) {
  const toneCls =
    tone === "good" ? "text-emerald-800" : tone === "bad" ? "text-rose-800" : "text-[#0B1E3F]";
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4">
      <p className="text-[10px] uppercase tracking-widest text-stone-500">{label}</p>
      <p className={`text-2xl mt-1 ${toneCls}`} style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
        {value}
      </p>
      {hint ? <p className="text-[11px] text-stone-500 mt-1">{hint}</p> : null}
    </div>
  );
}

function ChannelBadge({ channel }) {
  const map = {
    in_app_incluso: { label: "Incluso", cls: "bg-emerald-100 text-emerald-800" },
    crediti: { label: "Crediti", cls: "bg-amber-100 text-amber-900" },
    b2c: { label: "B2C", cls: "bg-sky-100 text-sky-900" },
    misto: { label: "Misto", cls: "bg-violet-100 text-violet-900" },
    abbonamento: { label: "Abbonamento", cls: "bg-stone-200 text-stone-800" },
  };
  const m = map[channel] || { label: channel, cls: "bg-stone-100 text-stone-700" };
  return (
    <span className={`text-[10px] uppercase tracking-widest px-2 py-0.5 rounded ${m.cls}`}>
      {m.label}
    </span>
  );
}
