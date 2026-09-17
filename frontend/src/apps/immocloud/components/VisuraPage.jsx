/**
 * ImmobilCloud — Visura catastale B2C (pagamento carta Stripe, mai crediti).
 * Flow: form → Stripe Checkout → success?session_id → poll → download PDF
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
  subalterno: "",
  tipo_catasto: "F",
};

export default function VisuraPage() {
  const { i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");

  const [catalog, setCatalog] = useState(null);
  const [form, setForm] = useState(empty);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [order, setOrder] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.get("/cloud/visura/catalog").then((r) => setCatalog(r.data)).catch(() => {});
    api.get("/auth/me").then((r) => setUser(r.data)).catch(() => setUser(null));
  }, []);

  const pollOrder = useCallback(async (sid) => {
    try {
      const r = await api.get(`/cloud/visura/orders/${sid}`);
      setOrder(r.data);
      return r.data;
    } catch (e) {
      setErr(e.response?.data?.detail || "Impossibile leggere lo stato dell'ordine");
      return null;
    }
  }, []);

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
      window.location.href = `/${lang}/cloud/register?next=${encodeURIComponent(`/${lang}/cloud/visura`)}`;
      return;
    }
    if (!form.provincia.trim() || !form.comune.trim() || !form.foglio.trim() || !form.particella.trim()) {
      setErr("Compila provincia, comune, foglio e particella");
      return;
    }
    setBusy(true);
    try {
      const origin = window.location.origin;
      const r = await api.post("/cloud/visura/checkout", {
        ...form,
        provincia: form.provincia.trim().toUpperCase().slice(0, 2),
        subalterno: form.subalterno.trim() || null,
        success_url: `${origin}/${lang}/cloud/visura`,
        cancel_url: `${origin}/${lang}/cloud/visura?cancel=1`,
      });
      if (r.data?.checkout_url) {
        sessionStorage.setItem("omnia_visura_pending", JSON.stringify(form));
        window.location.href = r.data.checkout_url;
        return;
      }
      setErr("Checkout non disponibile");
    } catch (ex) {
      const d = ex.response?.data?.detail;
      setErr(typeof d === "string" ? d : d?.message || "Pagamento non avviato");
    } finally {
      setBusy(false);
    }
  };

  const downloadPdf = async () => {
    if (!sessionId) return;
    setBusy(true);
    setErr("");
    try {
      const r = await api.get(`/cloud/visura/orders/${sessionId}/documento`, { responseType: "blob" });
      const url = window.URL.createObjectURL(r.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = "visura-catastale.pdf";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (ex) {
      setErr(ex.response?.data?.detail || "Download PDF non riuscito");
    } finally {
      setBusy(false);
    }
  };

  const price = catalog?.price_eur ?? 4.9;

  return (
    <div data-testid="cloud-visura-page">
      <CloudPageHero
        eyebrow="ImmobilCloud · Visura"
        title="Visura catastale"
        subtitle="Richiedi il PDF ufficiale e paga con carta. Nessun credito — solo Stripe."
        image="/cloud/intent-value.jpg"
        compact
      />
      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-10">
        <h1 className="sr-only" data-testid="cloud-visura-title">Visura catastale</h1>
        <Link to={`/${lang}/cloud`} className="text-xs uppercase tracking-widest text-stone-500 hover:text-[#0B1E3F]">
          ← Torna al portale
        </Link>

        {!user && (
          <div className="mt-6 p-4 rounded-2xl border border-amber-200 bg-amber-50 text-sm text-amber-900" data-testid="cloud-visura-anon">
            Accedi o registrati su ImmobilCloud per acquistare la visura.
            <Link to={`/${lang}/cloud/register`} className="ml-2 underline font-medium">Registrati</Link>
          </div>
        )}

        {sessionId && (
          <div className="mt-6 border border-stone-200 bg-white rounded-2xl p-5 space-y-3" data-testid="cloud-visura-order">
            <p className="text-[10px] uppercase tracking-widest text-[#C19A6B]">Il tuo ordine</p>
            <p className="text-sm text-stone-800">
              Pagamento: <strong>{order?.payment_status || "…"}</strong>
              {" · "}
              Visura: <strong>{order?.status || "…"}</strong>
            </p>
            {order?.download_ready && (
              <button
                type="button"
                onClick={downloadPdf}
                disabled={busy}
                data-testid="cloud-visura-download"
                className="bg-[#0B1E3F] text-white text-xs uppercase tracking-widest px-4 py-2 rounded-lg disabled:bg-stone-300 hover:bg-[#C19A6B]"
              >
                Scarica PDF
              </button>
            )}
            {order?.payment_status === "paid" && !order?.download_ready && order?.status !== "failed" && (
              <p className="text-xs text-stone-500">Stiamo preparando il documento…</p>
            )}
          </div>
        )}

        {!sessionId && (
          <form onSubmit={pay} className="mt-8 border border-stone-200 bg-white rounded-2xl p-6 space-y-4" data-testid="cloud-visura-form">
            <div className="flex items-baseline justify-between gap-3">
              <p className="text-sm font-medium text-stone-800">Dati catastali</p>
              <p className="text-lg text-[#0B1E3F]" data-testid="cloud-visura-price">
                € {Number(price).toFixed(2).replace(".", ",")}
              </p>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="text-xs text-stone-600 space-y-1">
                <span>Provincia</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm" maxLength={2}
                  value={form.provincia} onChange={(e) => setField("provincia", e.target.value)} data-testid="cloud-visura-provincia" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>Comune</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.comune} onChange={(e) => setField("comune", e.target.value)} data-testid="cloud-visura-comune" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>Foglio</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.foglio} onChange={(e) => setField("foglio", e.target.value)} data-testid="cloud-visura-foglio" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>Particella</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.particella} onChange={(e) => setField("particella", e.target.value)} data-testid="cloud-visura-particella" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>Subalterno</span>
                <input className="w-full border border-stone-200 px-2 py-1.5 text-sm"
                  value={form.subalterno} onChange={(e) => setField("subalterno", e.target.value)} data-testid="cloud-visura-subalterno" />
              </label>
              <label className="text-xs text-stone-600 space-y-1">
                <span>Catasto</span>
                <select className="w-full border border-stone-200 px-2 py-1.5 text-sm bg-white"
                  value={form.tipo_catasto} onChange={(e) => setField("tipo_catasto", e.target.value)} data-testid="cloud-visura-tipo">
                  <option value="F">Fabbricati</option>
                  <option value="T">Terreni</option>
                </select>
              </label>
            </div>
            <p className="text-[11px] text-stone-500">
              Dopo il pagamento ricevi il PDF ufficiale. Documento informativo — non sostituisce la consulenza di un tecnico.
            </p>
            <button
              type="submit"
              disabled={busy || catalog?.stripe_enabled === false}
              data-testid="cloud-visura-pay-btn"
              className="w-full sm:w-auto bg-[#0B1E3F] hover:bg-[#16305a] disabled:bg-stone-300 text-white text-xs uppercase tracking-widest px-5 py-2.5"
            >
              {busy ? "Reindirizzamento…" : `Paga € ${Number(price).toFixed(2).replace(".", ",")} con carta`}
            </button>
            {catalog && !catalog.stripe_enabled && (
              <p className="text-xs text-amber-700">Pagamenti carta non ancora attivi su questo ambiente.</p>
            )}
          </form>
        )}

        {err && <p className="mt-4 text-sm text-red-700" data-testid="cloud-visura-err">{typeof err === "string" ? err : JSON.stringify(err)}</p>}
      </div>
    </div>
  );
}
