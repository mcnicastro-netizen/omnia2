/**
 * ImmobilCloud — Planimetria catastale B2C (elaborato planimetrico).
 * Flow: form → Stripe Checkout €12 → success?session_id → poll → download PDF
 * Fulfillment: OpenAPI.it POST /elaborato_planimetrico (sandbox ok).
 */
import React, { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../../../shared/lib/api";
import CloudPageHero from "./CloudPageHero";

const empty = {
  provincia: "",
  comune: "",
  foglio: "",
  particella: "",
  sezione: "",
  sezione_urbana: "",
};

export default function PlanimetriaPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [params] = useSearchParams();
  const sessionId = params.get("session_id") || (() => {
    try { return sessionStorage.getItem("omnia_b2c_checkout_sid") || ""; }
    catch { return ""; }
  })();

  const [catalog, setCatalog] = useState(null);
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [order, setOrder] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.get("/cloud/planimetria/catalog").then((r) => setCatalog(r.data)).catch(() => {});
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => setUser(null));
  }, []);

  const pollOrder = useCallback(async (sid) => {
    try {
      const r = await api.get(`/cloud/planimetria/orders/${sid}`);
      setOrder(r.data);
      return r.data;
    } catch (e) {
      setErr(e.response?.data?.detail || t("cloud.planimetria.err_order_status"));
      return null;
    }
  }, [t]);

  useEffect(() => {
    if (!sessionId || !user) return;
    let cancelled = false;
    let n = 0;
    async function loop() {
      if (cancelled) return;
      const o = await pollOrder(sessionId);
      if (cancelled || !o) return;
      if (o.download_ready || o.status === "failed" || n >= 20) return;
      n += 1;
      setTimeout(loop, 2000);
    }
    loop();
    return () => { cancelled = true; };
  }, [sessionId, user, pollOrder]);

  const setField = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const pay = async (e) => {
    e.preventDefault();
    setErr("");
    if (!user) {
      window.location.href = `/${lang}/cloud/register?next=${encodeURIComponent(`/${lang}/cloud/planimetria`)}`;
      return;
    }
    if (!form.provincia.trim() || !form.comune.trim() || !form.foglio.trim() || !form.particella.trim()) {
      setErr(t("cloud.planimetria.err_required_fields"));
      return;
    }
    setBusy(true);
    try {
      const origin = window.location.origin;
      const r = await api.post("/cloud/planimetria/checkout", {
        provincia: form.provincia.trim().toUpperCase().slice(0, 2),
        comune: form.comune.trim(),
        foglio: form.foglio.trim(),
        particella: form.particella.trim(),
        sezione: form.sezione.trim() || null,
        sezione_urbana: form.sezione_urbana.trim() || null,
        success_url: `${origin}/${lang}/cloud/planimetria`,
        cancel_url: `${origin}/${lang}/cloud/planimetria?cancel=1`,
      });
      if (r.data?.checkout_url) {
        sessionStorage.setItem("omnia_planimetria_pending", JSON.stringify(form));
        window.location.href = r.data.checkout_url;
        return;
      }
      setErr(t("cloud.planimetria.err_checkout"));
    } catch (ex) {
      const d = ex.response?.data?.detail;
      setErr(typeof d === "string" ? d : d?.message || t("cloud.planimetria.err_pay_start"));
    } finally {
      setBusy(false);
    }
  };

  const downloadPdf = async () => {
    if (!sessionId) return;
    setBusy(true);
    setErr("");
    try {
      const r = await api.get(`/cloud/planimetria/orders/${sessionId}/documento`, { responseType: "blob" });
      const url = window.URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "planimetria-catastale.pdf";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (ex) {
      setErr(ex.response?.data?.detail || t("cloud.planimetria.err_download"));
    } finally {
      setBusy(false);
    }
  };

  const price = catalog?.price_eur ?? 12;
  const priceLabel = Number(price).toFixed(2).replace(".", ",");

  return (
    <div data-testid="cloud-planimetria-page">
      <CloudPageHero
        eyebrow={t("cloud.planimetria.eyebrow")}
        title={t("cloud.planimetria.title")}
        subtitle={t("cloud.planimetria.subtitle")}
        image="/cloud/intent-sell.jpg"
        compact
      />
      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-10">
        <h1 className="sr-only" data-testid="cloud-planimetria-title">{t("cloud.planimetria.title")}</h1>
        <div className="flex flex-wrap gap-4 text-xs uppercase tracking-widest text-stone-500">
          <Link to={`/${lang}/cloud`} className="hover:text-[#0B1E3F]">
            {t("cloud.planimetria.back")}
          </Link>
          <Link to={`/${lang}/cloud/account/sell`} className="hover:text-[#0B1E3F]" data-testid="cloud-planimetria-back-sell">
            {t("cloud.planimetria.back_sell")}
          </Link>
        </div>

        {!user && (
          <div className="mt-6 p-4 rounded-2xl border border-amber-200 bg-amber-50 text-sm text-amber-900" data-testid="cloud-planimetria-anon">
            {t("cloud.planimetria.anon")}
            <Link to={`/${lang}/cloud/register?intent=sell`} className="ml-2 underline font-medium">{t("cloud.planimetria.register")}</Link>
          </div>
        )}

        {sessionId && (
          <div className="mt-6 border border-stone-200 bg-white rounded-2xl p-5 space-y-3" data-testid="cloud-planimetria-order">
            <p className="text-[10px] uppercase tracking-widest text-[#C19A6B]">{t("cloud.planimetria.order_label")}</p>
            <p className="text-sm text-stone-800">
              {t("cloud.planimetria.payment")}: <strong>{order?.payment_status || "…"}</strong>
              {" · "}
              {t("cloud.planimetria.status")}: <strong>{order?.status || "…"}</strong>
            </p>
            {order?.download_ready && (
              <button
                type="button"
                onClick={downloadPdf}
                disabled={busy}
                data-testid="cloud-planimetria-download"
                className="bg-[#0B1E3F] text-white text-xs uppercase tracking-widest px-4 py-2 rounded-lg disabled:bg-stone-300 hover:bg-[#C19A6B]"
              >
                {t("cloud.planimetria.download_pdf")}
              </button>
            )}
            {order?.payment_status === "paid" && !order?.download_ready && order?.status !== "failed" && (
              <p className="text-xs text-stone-500">{t("cloud.planimetria.preparing")}</p>
            )}
          </div>
        )}

        {!sessionId && (
          <form onSubmit={pay} className="mt-8 border border-stone-200 bg-white rounded-2xl p-6 space-y-4" data-testid="cloud-planimetria-form">
            <p className="text-sm font-medium text-stone-800">{t("cloud.planimetria.form_legend")}</p>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-xs text-stone-600 space-y-1">
                <span>{t("cloud.planimetria.f_provincia")}</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm" maxLength={2}
                  value={form.provincia} onChange={(e) => setField("provincia", e.target.value)} data-testid="cloud-planimetria-provincia" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>{t("cloud.planimetria.f_comune")}</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.comune} onChange={(e) => setField("comune", e.target.value)} data-testid="cloud-planimetria-comune" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>{t("cloud.planimetria.f_foglio")}</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.foglio} onChange={(e) => setField("foglio", e.target.value)} data-testid="cloud-planimetria-foglio" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>{t("cloud.planimetria.f_particella")}</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.particella} onChange={(e) => setField("particella", e.target.value)} data-testid="cloud-planimetria-particella" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>{t("cloud.planimetria.f_sezione")}</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.sezione} onChange={(e) => setField("sezione", e.target.value)} data-testid="cloud-planimetria-sezione" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>{t("cloud.planimetria.f_sezione_urbana")}</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.sezione_urbana} onChange={(e) => setField("sezione_urbana", e.target.value)} data-testid="cloud-planimetria-sezione-urbana" />
              </label>
            </div>
            <p className="text-[11px] text-stone-500">{t("cloud.planimetria.disclaimer")}</p>
            {catalog?.openapi_enabled === false && (
              <p className="text-xs text-amber-700" data-testid="cloud-planimetria-openapi-off">{t("cloud.planimetria.openapi_off")}</p>
            )}
            <button
              type="submit"
              disabled={busy || catalog?.stripe_enabled === false || catalog?.openapi_enabled === false}
              data-testid="cloud-planimetria-pay-btn"
              className="w-full sm:w-auto bg-[#0B1E3F] hover:bg-[#16305a] disabled:bg-stone-300 text-white text-xs uppercase tracking-widest px-5 py-2.5"
            >
              {busy ? t("cloud.planimetria.redirecting") : t("cloud.planimetria.pay_cta", { price: priceLabel })}
            </button>
            {catalog && !catalog.stripe_enabled && (
              <p className="text-xs text-amber-700">{t("cloud.planimetria.stripe_off")}</p>
            )}
          </form>
        )}

        {err && <p className="mt-4 text-sm text-red-700" data-testid="cloud-planimetria-err">{typeof err === "string" ? err : JSON.stringify(err)}</p>}
      </div>
    </div>
  );
}
