import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth, formatApiErrorDetail } from "../../shared/lib/auth";
import { api } from "../../shared/lib/api";
import Brand from "../../shared/components/Brand";

/**
 * Sala d'attesa CRM (D-157 gestionale):
 * 1) upload KYC (visura + CI)
 * 2) pagamento Stripe
 * 3) attesa Super Admin → email con API key = password
 */
export default function WaitingActivationPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { user, logout, refresh } = useAuth();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const [agency, setAgency] = useState(null);
  const [paid, setPaid] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [checking, setChecking] = useState(false);
  const [payBusy, setPayBusy] = useState(false);
  const [upBusy, setUpBusy] = useState(false);

  const loadStatus = useCallback(async () => {
    setErr("");
    try {
      if (typeof refresh === "function") await refresh();
      const r = await api.get("/app/agencies/me");
      const a = r.data;
      setAgency(a);
      const st = a?.activation_status || "active";
      if (st === "active" || user?.role === "super_admin") {
        nav(`/${lang}/app/dashboard`, { replace: true });
        return a;
      }
      try {
        const sub = await api.get("/billing/subscription");
        const s = sub.data?.subscription;
        const ok =
          s && ["active", "trialing", "paid"].includes(String(s.status || "").toLowerCase());
        setPaid(Boolean(ok) || searchParams.get("paid") === "1");
      } catch {
        setPaid(searchParams.get("paid") === "1");
      }
      return a;
    } catch (e) {
      if (e?.response?.status === 404) {
        setErr(
          t(
            "waiting_activation.still_pending",
            "Agenzia ancora in verifica oppure sessione non allineata. Riprova tra un minuto o esci e rientra."
          )
        );
        return null;
      }
      setErr(t("waiting_activation.load_error", "Non riesco a caricare lo stato agenzia."));
      return null;
    }
  }, [lang, nav, refresh, searchParams, t, user?.role]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const kyc = agency?.kyc || {};
  const hasVisura = Boolean(kyc?.checklist?.visura_camerale);
  const hasId = Boolean(kyc?.checklist?.id_titolare);
  const kycReady = hasVisura && hasId;
  const readyForOps = kycReady && paid;

  const uploadKyc = async (docType, file) => {
    if (!file) return;
    setUpBusy(true);
    setMsg("");
    const ct = (file.type || "").toLowerCase();
    const okTypes = ["application/pdf", "image/png", "image/jpeg", "image/webp"];
    if (ct && !okTypes.includes(ct)) {
      setMsg(
        t(
          "waiting_activation.doc_type_error",
          "Formato non supportato. Usa PDF, PNG, JPG o WebP (niente HEIC/GIF)."
        )
      );
      setUpBusy(false);
      return;
    }
    if (file.size > 8 * 1024 * 1024) {
      setMsg(t("waiting_activation.doc_size_error", "File troppo grande (max 8 MB)."));
      setUpBusy(false);
      return;
    }
    try {
      const fd = new FormData();
      fd.append("file", file, file.name);
      fd.append("doc_type", docType);
      await api.post("/app/agencies/me/kyc/documents", fd, { timeout: 60000 });
      setMsg(t("waiting_activation.doc_ok", "Documento caricato."));
      await loadStatus();
    } catch (e) {
      setMsg(formatApiErrorDetail(e?.response?.data?.detail) || "Upload fallito");
    } finally {
      setUpBusy(false);
    }
  };

  const startPay = async () => {
    setPayBusy(true);
    setMsg("");
    try {
      const tier = agency?.preferred_plan_tier || "pro";
      const r = await api.post("/billing/checkout", {
        plan_tier: tier,
        billing_cycle: "monthly",
      });
      const url = r.data?.checkout_url;
      if (!url) throw new Error("no_checkout_url");
      window.location.href = url;
    } catch (e) {
      const d = e?.response?.data?.detail;
      setMsg(
        (typeof d === "object" && (d.message || d.error)) ||
          d ||
          t("waiting_activation.pay_error", "Checkout non disponibile. Riprova o contatta Ops.")
      );
      setPayBusy(false);
    }
  };

  const onLogout = async () => {
    await logout();
    nav(`/${lang}/login`, { replace: true });
  };

  return (
    <div
      data-testid="waiting-activation"
      className="min-h-screen bg-gradient-to-b from-[#f7f4ef] to-stone-100 flex flex-col"
    >
      <header className="px-6 py-4 flex items-center justify-between border-b border-stone-200/80 bg-white/70 backdrop-blur">
        <Brand>OMNIA</Brand>
        <button
          type="button"
          onClick={onLogout}
          className="text-xs uppercase tracking-widest text-stone-600 hover:text-[#0B1E3F]"
        >
          {t("common.logout", "Esci")}
        </button>
      </header>
      <main className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="max-w-lg w-full space-y-6">
          <div className="text-center space-y-3">
            <p className="text-[10px] uppercase tracking-[0.35em] text-[#C19A6B]">
              {t("waiting_activation.eyebrow", "Attivazione in corso")}
            </p>
            <h1
              className="text-3xl text-[#0B1E3F] tracking-tight"
              style={{ fontFamily: "'Fraunces', Georgia, serif" }}
            >
              {t("waiting_activation.title", "Completa registrazione e pagamento")}
            </h1>
            <p className="text-stone-600 text-sm leading-relaxed">
              {t(
                "waiting_activation.body_gestionale",
                "Per {{name}}: carica visura e documento, paga il pacchetto, poi il Super Admin verifica e ti invia la chiave API (password iniziale)."
              ).replace("{{name}}", agency?.display_name || "…")}
            </p>
            {agency?.preferred_plan_tier ? (
              <p className="text-sm text-stone-700">
                {t("waiting_activation.plan", "Piano")}:{" "}
                <span className="font-medium uppercase">{agency.preferred_plan_tier}</span>
              </p>
            ) : null}
          </div>

          <section className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-3">
            <h2 className="text-[10px] uppercase tracking-widest text-stone-500">
              1 · {t("waiting_activation.kyc_title", "Identificazione (PDF)")}
            </h2>
            <p className="text-xs text-stone-500">
              Visura: {hasVisura ? "ok" : "manca"} · Documento: {hasId ? "ok" : "manca"}
            </p>
            <label className="block text-xs uppercase tracking-widest text-stone-600">
              Visura camerale
              <input
                type="file"
                accept="application/pdf,image/png,image/jpeg,image/webp,.pdf,.png,.jpg,.jpeg,.webp"
                disabled={upBusy}
                data-testid="waiting-upload-visura"
                className="block mt-1 text-xs normal-case tracking-normal"
                onChange={(e) => {
                  uploadKyc("visura_camerale", e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
            </label>
            <label className="block text-xs uppercase tracking-widest text-stone-600">
              Documento identità titolare
              <input
                type="file"
                accept="application/pdf,image/png,image/jpeg,image/webp,.pdf,.png,.jpg,.jpeg,.webp"
                disabled={upBusy}
                data-testid="waiting-upload-id"
                className="block mt-1 text-xs normal-case tracking-normal"
                onChange={(e) => {
                  uploadKyc("documento_identita", e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
            </label>
          </section>

          <section className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-3">
            <h2 className="text-[10px] uppercase tracking-widest text-stone-500">
              2 · {t("waiting_activation.pay_title", "Pagamento pacchetto")}
            </h2>
            <p className="text-sm text-stone-600">
              {paid
                ? t("waiting_activation.paid_ok", "Pagamento ricevuto.")
                : t("waiting_activation.paid_need", "Completa il checkout Stripe prima della verifica Ops.")}
            </p>
            {!paid ? (
              <button
                type="button"
                data-testid="waiting-pay"
                disabled={payBusy || !kycReady}
                onClick={startPay}
                className="w-full text-xs uppercase tracking-widest px-4 py-3 rounded bg-[#0B1E3F] text-white disabled:opacity-40"
              >
                {payBusy
                  ? t("common.loading")
                  : t("waiting_activation.pay_cta", "Paga e invia richiesta")}
              </button>
            ) : null}
            {!kycReady && !paid ? (
              <p className="text-xs text-amber-800">
                {t("waiting_activation.pay_need_kyc", "Carica prima visura e documento.")}
              </p>
            ) : null}
          </section>

          <section className="bg-white border border-stone-200 rounded-lg px-4 py-4 space-y-2 text-center">
            <h2 className="text-[10px] uppercase tracking-widest text-stone-500">
              3 · {t("waiting_activation.ops_title", "Verifica Super Admin")}
            </h2>
            <p className="text-sm text-stone-600">
              {readyForOps
                ? t(
                    "waiting_activation.ops_ready",
                    "Richiesta completa. Ti arriverà l’email con la chiave API quando l’account sarà attivato."
                  )
                : t(
                    "waiting_activation.ops_wait",
                    "Completa documenti e pagamento per far partire la verifica."
                  )}
            </p>
          </section>

          {err ? (
            <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              {err}
            </p>
          ) : null}
          {msg ? <p className="text-sm text-[#0B1E3F]">{msg}</p> : null}

          <div className="flex flex-wrap gap-3 justify-center pt-2">
            <Link
              to={`/${lang}/cloud`}
              className="text-xs uppercase tracking-widest px-4 py-2.5 rounded border border-stone-300 bg-white"
            >
              {t("waiting_activation.cta_cloud", "Vai a ImmobilCloud")}
            </Link>
            <button
              type="button"
              data-testid="waiting-refresh"
              disabled={checking}
              onClick={async () => {
                setChecking(true);
                try {
                  await loadStatus();
                } finally {
                  setChecking(false);
                }
              }}
              className="text-xs uppercase tracking-widest px-4 py-2.5 rounded border border-stone-300 bg-white text-stone-700 disabled:opacity-50"
            >
              {checking
                ? t("common.loading", "Caricamento…")
                : t("waiting_activation.refresh", "Controlla di nuovo")}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
