import React, { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../../shared/lib/auth";
import CloudPageHero from "../components/CloudPageHero";
import usePwaInstall from "../../../shared/hooks/usePwaInstall";

/**
 * Area riservata ImmobilCloud — ingresso chiaro: Accedi | Crea account.
 * Evita di mandare chi ha già un account dritto sul form di registrazione.
 * QR «Scarica app» atterra qui (?from=pwa) con striscia Installa (D-143).
 */
export default function CloudAreaPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const { user } = useAuth();
  const [params] = useSearchParams();
  const intent = params.get("intent") || "";
  const fromPwa = params.get("from") === "pwa";
  const nextRaw = params.get("next") || "";
  const nextPath = (
    nextRaw.startsWith("/")
    && !nextRaw.startsWith("//")
    && !nextRaw.includes("://")
  ) ? nextRaw : `/${lang}/cloud/account`;

  useEffect(() => {
    if (user === null) return;
    if (user && user.account_type === "b2c") {
      nav(intent === "sell" ? `/${lang}/cloud/account/sell` : nextPath, { replace: true });
    }
  }, [user, lang, nav, intent, nextPath]);

  const loginTo = `/${lang}/login?from=cloud&next=${encodeURIComponent(nextPath)}`;
  const registerTo = intent
    ? `/${lang}/cloud/register?intent=${encodeURIComponent(intent)}&next=${encodeURIComponent(nextPath)}`
    : `/${lang}/cloud/register?next=${encodeURIComponent(nextPath)}`;
  const agencyLoggedIn = Boolean(user && user.id && user.account_type !== "b2c");

  if (user === null) {
    return (
      <div className="max-w-xl mx-auto px-5 py-16 text-center text-stone-500 text-sm" data-testid="cloud-area-loading">
        {t("common.loading")}
      </div>
    );
  }

  return (
    <div data-testid="cloud-area-page">
      <CloudPageHero
        eyebrow="ImmobilCloud · Area riservata"
        title={t("cloud.area_title")}
        subtitle={
          fromPwa
            ? t(
                "cloud.area_subtitle_pwa",
                "Accedi o crea il tuo account. Poi, se vuoi, installa ImmobilCloud tra le app del telefonino."
              )
            : t("cloud.area_subtitle")
        }
        image="/cloud/scout.jpg"
        compact
      />
      {fromPwa && !agencyLoggedIn ? <AreaPwaInstallStrip lang={lang} /> : null}
      {agencyLoggedIn && (
        <div
          data-testid="cloud-area-agency-session"
          className="max-w-2xl mx-auto px-5 mt-6 rounded-xl border border-amber-200 bg-amber-50 text-amber-950 text-sm p-4"
        >
          <p className="font-medium mb-1">{t("cloud.area_agency_session_title")}</p>
          <p className="text-amber-900/90 mb-3">{t("cloud.area_agency_session_desc")}</p>
          <div className="flex flex-wrap gap-3 text-[11px] uppercase tracking-widest">
            <Link to={`/${lang}/app/dashboard`} className="underline text-[#0B1E3F]">
              {t("cloud.area_agency_login")}
            </Link>
            <Link to={registerTo} className="underline text-[#0B1E3F]">
              {t("cloud.area_register_title")}
            </Link>
          </div>
        </div>
      )}
      <section className="max-w-2xl mx-auto px-5 py-10 grid sm:grid-cols-2 gap-4">
        <Link
          to={loginTo}
          data-testid="cloud-area-login"
          className="group rounded-2xl border border-stone-200 bg-white p-6 hover:border-[#0B1E3F] hover:shadow-[0_16px_36px_rgba(11,30,63,0.1)] transition"
        >
          <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-2">
            {t("cloud.area_login_tag")}
          </p>
          <h2
            className="text-xl text-[#0B1E3F] mb-2 tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("cloud.area_login_title")}
          </h2>
          <p className="text-sm text-stone-600 font-sans leading-relaxed mb-4">
            {t("cloud.area_login_desc")}
          </p>
          <span className="text-[11px] uppercase tracking-widest text-[#0B1E3F] group-hover:text-[#C19A6B]">
            {t("auth.login_cta")} →
          </span>
        </Link>

        <Link
          to={registerTo}
          data-testid="cloud-area-register"
          className="group rounded-2xl border border-stone-200 bg-[#f7f4ef] p-6 hover:border-[#0B1E3F] hover:shadow-[0_16px_36px_rgba(11,30,63,0.1)] transition"
        >
          <p className="text-[10px] uppercase tracking-[0.28em] text-[#1F6B5C] mb-2">
            {t("cloud.area_register_tag")}
          </p>
          <h2
            className="text-xl text-[#0B1E3F] mb-2 tracking-tight"
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            {t("cloud.area_register_title")}
          </h2>
          <p className="text-sm text-stone-600 font-sans leading-relaxed mb-4">
            {t("cloud.area_register_desc")}
          </p>
          <span className="text-[11px] uppercase tracking-widest text-[#0B1E3F] group-hover:text-[#C19A6B]">
            {t("auth.register_cta")} →
          </span>
        </Link>
      </section>
      <p className="text-center text-xs text-stone-500 font-sans pb-12 px-5">
        {t("cloud.area_agency_hint")}{" "}
        <Link to={`/${lang}/login?from=app&next=${encodeURIComponent(`/${lang}/app/dashboard`)}`} className="underline text-[#0B1E3F]">
          {t("cloud.area_agency_login")}
        </Link>
        {" · "}
        <Link to={`/${lang}/register`} className="underline text-[#0B1E3F]">
          {t("cloud.area_agency_register")}
        </Link>
      </p>
    </div>
  );
}

function AreaPwaInstallStrip({ lang }) {
  const { t } = useTranslation();
  const { installed, canPrompt, iosHint, promptInstall } = usePwaInstall();
  const [msg, setMsg] = useState("");

  if (installed) return null;

  const onInstall = async () => {
    setMsg("");
    const res = await promptInstall();
    if (res.ok) {
      setMsg(t("cloud.pwa.done", "Perfetto — ImmobilCloud è tra le tue app."));
      return;
    }
    if (iosHint || res.reason === "ios") {
      setMsg(
        t(
          "cloud.pwa.ios_hint",
          "Su iPhone: tocca Condividi (□↑) in basso → Aggiungi a Home."
        )
      );
      return;
    }
    setMsg(
      t(
        "cloud.pwa.browser_hint",
        "Apri questa pagina in Chrome sul telefonino, poi tocca Installa."
      )
    );
  };

  return (
    <div
      data-testid="cloud-area-pwa-strip"
      className="max-w-2xl mx-auto px-5 mt-6 rounded-2xl border border-[#C19A6B]/35 bg-[#0B1E3F] text-white px-5 py-4 flex flex-col sm:flex-row sm:items-center gap-3"
    >
      <div className="min-w-0 flex-1">
        <p className="text-[10px] uppercase tracking-[0.28em] text-[#C19A6B] mb-1">
          {t("cloud.pwa.eyebrow", "Telefonino")}
        </p>
        <p className="text-sm text-white/90">
          {t(
            "cloud.area_pwa_strip",
            "Vuoi l’icona tra le app? Un tocco su Installa (su iPhone: guida nella pagina Scarica app)."
          )}
        </p>
        {msg ? (
          <p className="mt-2 text-xs text-[#E8D5B5]" data-testid="cloud-area-pwa-msg">
            {msg}
          </p>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-2 shrink-0">
        {iosHint ? (
          <Link
            to={`/${lang}/cloud/app`}
            className="px-4 py-2 rounded-lg bg-[#C19A6B] text-[#0B1E3F] text-[11px] uppercase tracking-widest"
            data-testid="cloud-area-pwa-ios-guide"
          >
            {t("cloud.pwa.cta_ios_guide", "Come installare")}
          </Link>
        ) : (
          <button
            type="button"
            data-testid="cloud-area-pwa-install"
            onClick={onInstall}
            className="px-4 py-2 rounded-lg bg-[#C19A6B] text-[#0B1E3F] text-[11px] uppercase tracking-widest"
          >
            {canPrompt
              ? t("cloud.pwa.cta_install", "Installa ImmobilCloud")
              : t("cloud.pwa.cta_install", "Installa ImmobilCloud")}
          </button>
        )}
      </div>
    </div>
  );
}
