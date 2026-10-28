import React, { useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../../../shared/lib/auth";
import CloudPageHero from "../components/CloudPageHero";

/**
 * Area riservata ImmobilCloud — ingresso chiaro: Accedi | Crea account.
 * Evita di mandare chi ha già un account dritto sul form di registrazione.
 */
export default function CloudAreaPage() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const nav = useNavigate();
  const { user } = useAuth();
  const [params] = useSearchParams();
  const intent = params.get("intent") || "";
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
        subtitle={t("cloud.area_subtitle")}
        image="/cloud/scout.jpg"
        compact
      />
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
