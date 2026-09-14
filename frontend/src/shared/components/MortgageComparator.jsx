/*
 * OMNIA — M5.S5 MortgageComparator (componente condiviso B2C + CRM)
 *
 * Motore in-house (D-037): ammortamento francese, TAN = benchmark+spread,
 * TAEG, soglia usura TEGM, LTV/Consap, sostenibilità rata/reddito.
 * publicMode: mostra il box lead capture (portale B2C).
 */
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/cloud/mutui`;

const eur = (n) =>
  n || n === 0 ? `€ ${Math.round(n).toLocaleString("it-IT")}` : "—";
const eur2 = (n) => `€ ${(n || 0).toLocaleString("it-IT", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

function OfferCard({ o, t, loan }) {
  const [plan, setPlan] = useState(null);
  const [loadingPlan, setLoadingPlan] = useState(false);

  const togglePlan = async () => {
    if (plan) return setPlan(null);
    setLoadingPlan(true);
    try {
      const r = await fetch(`${API}/plan`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ loan_amount: loan, tan_pct: o.tan, duration_years: o.duration || o.years }),
      });
      setPlan(await r.json());
    } catch {
      /* noop */
    } finally {
      setLoadingPlan(false);
    }
  };

  return (
    <div
      data-testid={`mutui-offer-${o.rank}`}
      className={`border p-5 bg-white ${o.rank === 1 ? "border-emerald-400 ring-1 ring-emerald-200" : "border-stone-200"}`}
    >
      <div className="flex items-start justify-between flex-wrap gap-2">
        <div>
          <p className="text-sm font-semibold text-stone-900">
            {o.rank === 1 && <span className="text-emerald-700 mr-1">★ {t("mutui.best")}</span>}
            {o.bank}
          </p>
          <p className="text-xs text-stone-500">{o.product} · {o.type === "fisso" ? t("mutui.fisso") : t("mutui.variabile")}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-semibold text-[#0B1E3F]" data-testid={`mutui-rata-${o.rank}`}>{eur2(o.rata)}<span className="text-xs font-normal text-stone-500">/{t("mutui.month")}</span></p>
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 text-xs">
        <div><p className="text-stone-400 uppercase tracking-wider">TAN</p><p className="text-stone-800 font-medium">{o.tan}%</p></div>
        <div><p className="text-stone-400 uppercase tracking-wider">TAEG</p><p className="text-stone-800 font-medium">{o.taeg}%</p></div>
        <div><p className="text-stone-400 uppercase tracking-wider">{t("mutui.upfront")}</p><p className="text-stone-800 font-medium">{eur(o.upfront_total)}</p></div>
        <div><p className="text-stone-400 uppercase tracking-wider">{t("mutui.total_interest")}</p><p className="text-stone-800 font-medium">{eur(o.total_interest)}</p></div>
      </div>
      {!o.usury_ok && (
        <p className="mt-2 text-xs text-red-600">⚠ {t("mutui.usury_warn")}</p>
      )}
      <button
        type="button"
        onClick={togglePlan}
        data-testid={`mutui-plan-btn-${o.rank}`}
        className="mt-3 text-[11px] uppercase tracking-widest text-stone-500 hover:text-stone-900 underline"
      >
        {loadingPlan ? "..." : plan ? t("mutui.hide_plan") : t("mutui.show_plan")}
      </button>
      {plan && (
        <div className="mt-3 overflow-x-auto" data-testid={`mutui-plan-${o.rank}`}>
          <table className="w-full text-[11px] text-stone-600">
            <thead>
              <tr className="text-left text-stone-400 uppercase tracking-wider border-b border-stone-100">
                <th className="py-1 pr-3">{t("mutui.plan_year")}</th>
                <th className="py-1 pr-3">{t("mutui.plan_principal")}</th>
                <th className="py-1 pr-3">{t("mutui.plan_interest")}</th>
                <th className="py-1">{t("mutui.plan_balance")}</th>
              </tr>
            </thead>
            <tbody>
              {plan.years.map((y) => (
                <tr key={y.year} className="border-b border-stone-50">
                  <td className="py-1 pr-3">{y.year}</td>
                  <td className="py-1 pr-3">{eur(y.principal)}</td>
                  <td className="py-1 pr-3">{eur(y.interest)}</td>
                  <td className="py-1">{eur(y.balance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default function MortgageComparator({ publicMode = false, initialPrice = null }) {
  const { t } = useTranslation();
  const [config, setConfig] = useState(null);
  const [form, setForm] = useState({
    property_price: initialPrice || "",
    down_payment: initialPrice ? Math.round(initialPrice * 0.2) : "",
    duration_years: 25,
    rate_type: "entrambi",
    income_monthly: "",
    first_home: true,
    age_under_36: false,
  });
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [lead, setLead] = useState({ name: "", email: "", phone: "", sent: false, busy: false });

  useEffect(() => {
    fetch(`${API}/config`).then((r) => r.json()).then(setConfig).catch(() => {});
  }, []);

  const upd = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    setResult(null);
    try {
      const r = await fetch(`${API}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          property_price: Number(form.property_price),
          down_payment: Number(form.down_payment || 0),
          duration_years: Number(form.duration_years),
          rate_type: form.rate_type,
          income_monthly: form.income_monthly ? Number(form.income_monthly) : null,
          first_home: form.first_home,
          age_under_36: form.age_under_36,
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || t("common.error"));
      d.offers = (d.offers || []).map((o) => ({ ...o, duration: Number(form.duration_years) }));
      setResult(d);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const sendLead = async (e) => {
    e.preventDefault();
    setLead((l) => ({ ...l, busy: true }));
    try {
      await fetch(`${API}/lead`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: lead.name,
          email: lead.email,
          phone: lead.phone || null,
          property_price: Number(form.property_price),
          loan_amount: result.loan_amount,
          duration_years: Number(form.duration_years),
          rate_type: form.rate_type,
          best_rata: result.offers[0]?.rata || null,
          gdpr_consent: true,
        }),
      });
      setLead((l) => ({ ...l, sent: true, busy: false }));
    } catch {
      setLead((l) => ({ ...l, busy: false }));
    }
  };

  return (
    <div data-testid="mortgage-comparator" className="space-y-6">
      {/* Form */}
      <form onSubmit={submit} className="bg-white border border-stone-200 p-6 space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-stone-500">{t("mutui.price")} *</span>
            <input type="number" required min="20000" value={form.property_price} data-testid="mutui-price"
              onChange={(e) => upd("property_price", e.target.value)}
              className="mt-1 w-full border border-stone-300 px-3 py-2 text-sm" placeholder="250000" />
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-stone-500">{t("mutui.down_payment")} *</span>
            <input type="number" required min="0" value={form.down_payment} data-testid="mutui-down"
              onChange={(e) => upd("down_payment", e.target.value)}
              className="mt-1 w-full border border-stone-300 px-3 py-2 text-sm" placeholder="50000" />
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-stone-500">{t("mutui.duration")}</span>
            <select value={form.duration_years} data-testid="mutui-duration"
              onChange={(e) => upd("duration_years", e.target.value)}
              className="mt-1 w-full border border-stone-300 px-3 py-2 text-sm bg-white">
              {(config?.durations || [10, 15, 20, 25, 30]).map((d) => (
                <option key={d} value={d}>{d} {t("mutui.years")}</option>
              ))}
            </select>
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-stone-500">{t("mutui.rate_type")}</span>
            <select value={form.rate_type} data-testid="mutui-rate-type"
              onChange={(e) => upd("rate_type", e.target.value)}
              className="mt-1 w-full border border-stone-300 px-3 py-2 text-sm bg-white">
              <option value="entrambi">{t("mutui.entrambi")}</option>
              <option value="fisso">{t("mutui.fisso")}</option>
              <option value="variabile">{t("mutui.variabile")}</option>
            </select>
          </label>
          <label className="block">
            <span className="text-xs uppercase tracking-widest text-stone-500">{t("mutui.income")}</span>
            <input type="number" min="0" value={form.income_monthly} data-testid="mutui-income"
              onChange={(e) => upd("income_monthly", e.target.value)}
              className="mt-1 w-full border border-stone-300 px-3 py-2 text-sm" placeholder="2500" />
          </label>
          <div className="flex items-end gap-5 pb-1">
            <label className="flex items-center gap-2 text-sm text-stone-700">
              <input type="checkbox" checked={form.first_home} data-testid="mutui-first-home"
                onChange={(e) => upd("first_home", e.target.checked)} />
              {t("mutui.first_home")}
            </label>
            <label className="flex items-center gap-2 text-sm text-stone-700">
              <input type="checkbox" checked={form.age_under_36} data-testid="mutui-under36"
                onChange={(e) => upd("age_under_36", e.target.checked)} />
              {t("mutui.under36")}
            </label>
          </div>
        </div>
        <button type="submit" disabled={busy} data-testid="mutui-submit"
          className="bg-[#0B1E3F] hover:bg-[#152C55] disabled:opacity-50 text-white text-sm uppercase tracking-widest px-8 py-3 transition-colors">
          {busy ? t("mutui.computing") : t("mutui.submit")}
        </button>
        {config && (
          <p className="text-[11px] text-stone-400">
            {t("mutui.data_note", { n: config.banks_count, date: config.data_updated_at })}
          </p>
        )}
      </form>

      {error && <div data-testid="mutui-error" className="border border-red-300 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

      {/* Results */}
      {result && !result.eligible && (
        <div data-testid="mutui-ltv-error" className="border border-amber-300 bg-amber-50 text-amber-800 px-5 py-4 text-sm">
          <p className="font-medium">{t("mutui.ltv_error", { ltv: result.ltv, max: result.max_ltv })}</p>
          <p className="mt-1">{t("mutui.min_down", { amount: eur(result.min_down_payment) })}</p>
        </div>
      )}

      {result && result.eligible && (
        <div className="space-y-4" data-testid="mutui-results">
          <div className="flex flex-wrap gap-4 items-center bg-stone-100 border border-stone-200 px-5 py-3 text-sm text-stone-700">
            <span>{t("mutui.loan")}: <strong data-testid="mutui-loan">{eur(result.loan_amount)}</strong></span>
            <span>LTV: <strong>{result.ltv}%</strong></span>
            {result.consap_applied && <span className="text-emerald-700">✓ {t("mutui.consap_note")}</span>}
            {result.sustainability && (
              <span className={result.sustainability.ok ? "text-emerald-700" : "text-red-600"} data-testid="mutui-sustainability">
                {result.sustainability.ok
                  ? t("mutui.sustainability_ok", { pct: result.sustainability.ratio_pct })
                  : t("mutui.sustainability_ko", { pct: result.sustainability.ratio_pct, max: result.sustainability.max_pct })}
              </span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.offers.map((o) => (
              <OfferCard key={`${o.bank}-${o.product}`} o={o} t={t} loan={result.loan_amount} />
            ))}
          </div>

          {/* Lead capture (public B2C only) */}
          {publicMode && !lead.sent && (
            <form onSubmit={sendLead} data-testid="mutui-lead-form"
              className="bg-[#0B1E3F] text-white p-6 space-y-4">
              <p className="text-sm font-medium">{t("mutui.lead_title")}</p>
              <p className="text-xs text-stone-300">{t("mutui.lead_text")}</p>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <input required placeholder={t("mutui.lead_name")} value={lead.name} data-testid="mutui-lead-name"
                  onChange={(e) => setLead((l) => ({ ...l, name: e.target.value }))}
                  className="px-3 py-2 text-sm text-stone-900" />
                <input required type="email" placeholder={t("mutui.lead_email")} value={lead.email} data-testid="mutui-lead-email"
                  onChange={(e) => setLead((l) => ({ ...l, email: e.target.value }))}
                  className="px-3 py-2 text-sm text-stone-900" />
                <input placeholder={t("mutui.lead_phone")} value={lead.phone} data-testid="mutui-lead-phone"
                  onChange={(e) => setLead((l) => ({ ...l, phone: e.target.value }))}
                  className="px-3 py-2 text-sm text-stone-900" />
              </div>
              <button type="submit" disabled={lead.busy} data-testid="mutui-lead-submit"
                className="bg-[#C19A6B] hover:bg-[#a98354] text-white text-xs uppercase tracking-widest px-6 py-2.5">
                {lead.busy ? "..." : t("mutui.lead_submit")}
              </button>
            </form>
          )}
          {publicMode && lead.sent && (
            <div data-testid="mutui-lead-ok" className="border border-emerald-300 bg-emerald-50 text-emerald-800 px-5 py-4 text-sm">
              ✓ {t("mutui.lead_ok")}
            </div>
          )}

          <p className="text-[11px] text-stone-400 leading-relaxed" data-testid="mutui-disclaimer">
            {result.disclaimer}
          </p>
        </div>
      )}
    </div>
  );
}
