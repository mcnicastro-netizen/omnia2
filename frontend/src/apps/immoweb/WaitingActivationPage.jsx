import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../shared/lib/auth";
import { api } from "../../shared/lib/api";
import Brand from "../../shared/components/Brand";

/**
 * Sala d'attesa CRM — agenzia creata ma non ancora attivata da Ops.
 * «Controlla di nuovo» NON deve riportare all'onboarding/registrazione.
 */
export default function WaitingActivationPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { user, logout, refresh } = useAuth();
  const nav = useNavigate();
  const [agency, setAgency] = useState(null);
  const [err, setErr] = useState("");
  const [checking, setChecking] = useState(false);

  const loadStatus = useCallback(async () => {
    setErr("");
    try {
      if (typeof refresh === "function") {
        await refresh();
      }
      const r = await api.get("/app/agencies/me");
      const a = r.data;
      setAgency(a);
      const st = a?.activation_status || "active";
      if (st === "active" || user?.role === "super_admin") {
        nav(`/${lang}/app/dashboard`, { replace: true });
      }
      return a;
    } catch (e) {
      const code = e?.response?.status;
      if (code === 404) {
        // Resta in sala: non rimandare al wizard (bug «Controlla di nuovo → registrazione»)
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
  }, [lang, nav, refresh, t, user?.role]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const onCheckAgain = async () => {
    setChecking(true);
    try {
      await loadStatus();
    } finally {
      setChecking(false);
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
      <main className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="max-w-lg w-full text-center space-y-6">
          <p className="text-[10px] uppercase tracking-[0.35em] text-[#C19A6B]">
            {t("waiting_activation.eyebrow", "Attivazione in corso")}
          </p>
          <h1
            className="text-3xl md:text-4xl text-[#0B1E3F] tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t(
              "waiting_activation.title",
              "Il gestionale non è ancora sbloccato"
            )}
          </h1>
          <p className="text-stone-600 text-sm md:text-base leading-relaxed">
            {t(
              "waiting_activation.body",
              "Abbiamo ricevuto i dati di {{name}}. Un operatore OMNIA verifica l’identità dell’agenzia (documenti / visura), attiva il piano e ti invia l’email di sblocco CRM. Non serve altro da parte tua."
            ).replace("{{name}}", agency?.display_name || "…")}
          </p>
          {agency?.preferred_plan_tier ? (
            <p className="text-sm text-stone-700">
              {t("waiting_activation.plan", "Piano richiesto")}:{" "}
              <span className="font-medium uppercase">{agency.preferred_plan_tier}</span>
            </p>
          ) : null}
          {agency?.slug ? (
            <p className="text-xs text-stone-500 font-mono">
              {t("waiting_activation.ref", "Riferimento")}: {agency.slug}
            </p>
          ) : null}
          {err ? (
            <p className="text-sm text-amber-900 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              {err}
            </p>
          ) : null}
          <div className="flex flex-wrap gap-3 justify-center pt-2">
            <Link
              to={`/${lang}/cloud`}
              className="text-xs uppercase tracking-widest px-4 py-2.5 rounded bg-[#0B1E3F] text-white"
            >
              {t("waiting_activation.cta_cloud", "Vai a ImmobilCloud")}
            </Link>
            <button
              type="button"
              data-testid="waiting-refresh"
              disabled={checking}
              onClick={onCheckAgain}
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
