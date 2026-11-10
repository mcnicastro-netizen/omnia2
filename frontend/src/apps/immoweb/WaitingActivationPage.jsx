import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../shared/lib/auth";
import { api } from "../../shared/lib/api";
import Brand from "../../shared/components/Brand";

/**
 * Sala d'attesa CRM — agenzia creata ma non ancora attivata da Ops.
 */
export default function WaitingActivationPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [agency, setAgency] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let mounted = true;
    api
      .get("/app/agencies/me")
      .then((r) => {
        if (!mounted) return;
        const a = r.data;
        setAgency(a);
        const st = a?.activation_status || "active";
        if (st === "active" || user?.role === "super_admin") {
          nav(`/${lang}/app/dashboard`, { replace: true });
        }
      })
      .catch((e) => {
        if (!mounted) return;
        if (e?.response?.status === 404) {
          nav(`/${lang}/app/onboarding`, { replace: true });
        } else {
          setErr(t("waiting_activation.load_error", "Non riesco a caricare lo stato agenzia."));
        }
      });
    return () => {
      mounted = false;
    };
  }, [lang, nav, t, user?.role]);

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
              "Abbiamo ricevuto i dati di {{name}}. Un operatore OMNIA verifica l’agenzia, attiva il piano e ti invia una email di benvenuto con l’accesso al CRM. Non serve altro da parte tua."
            ).replace("{{name}}", agency?.display_name || "…")}
          </p>
          {agency?.slug ? (
            <p className="text-xs text-stone-500 font-mono">
              {t("waiting_activation.ref", "Riferimento")}: {agency.slug}
            </p>
          ) : null}
          {err ? (
            <p className="text-sm text-red-800 bg-red-50 border border-red-200 rounded px-3 py-2">{err}</p>
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
              onClick={() => window.location.reload()}
              className="text-xs uppercase tracking-widest px-4 py-2.5 rounded border border-stone-300 bg-white text-stone-700"
            >
              {t("waiting_activation.refresh", "Controlla di nuovo")}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
