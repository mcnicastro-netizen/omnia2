import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import HealthBadge from "../../shared/components/HealthBadge";
import TopNav from "../../shared/components/TopNav";
import Brand from "../../shared/components/Brand";
import OmniaLogo from "../../shared/components/OmniaLogo";

/**
 * OMNIA Landing — fully responsive (mobile/tablet/desktop).
 */
export default function LandingApp() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const pillars = [
    {
      key: "cloud",
      title: t("landing.pillar_cloud_title"),
      desc: t("landing.pillar_cloud_desc"),
      to: `/${lang}/cloud`,
      tag: "B2C",
    },
    {
      key: "app",
      title: t("landing.pillar_app_title"),
      desc: t("landing.pillar_app_desc"),
      to: `/${lang}/app`,
      tag: "B2B",
    },
    {
      key: "learn",
      title: t("landing.pillar_learn_title"),
      desc: t("landing.pillar_learn_desc"),
      to: `/${lang}/learn`,
      tag: "LMS",
    },
  ];

  return (
    <div
      data-testid="landing-app"
      className="min-h-screen bg-stone-50 text-stone-900 overflow-x-hidden"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      <TopNav current="landing" theme="light" />

      {/* Hero */}
      <section className="px-5 sm:px-8 md:px-12 lg:px-16 py-16 md:py-20 lg:py-24 max-w-screen-2xl mx-auto grid md:grid-cols-12 gap-10 md:gap-12">
        <div className="md:col-span-7 min-w-0">
          <div className="mb-8 md:mb-10" data-testid="landing-hero-logo">
            <OmniaLogo variant="full" size="xl" />
          </div>
          <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-stone-500 mb-4 md:mb-6">
            <Brand>Real estate · Ecosystem · 2026</Brand>
          </p>
          <h1 className="text-4xl sm:text-5xl md:text-5xl lg:text-6xl leading-[1.05] tracking-tight mb-6 md:mb-8 break-words">
            {t("landing.hero_title")}
          </h1>
          <p className="text-lg sm:text-xl md:text-xl lg:text-2xl font-light text-stone-600 mb-8 md:mb-12 max-w-xl">
            {t("landing.hero_subtitle")}
          </p>
          <a
            data-testid="landing-cta"
            href={`/${lang}/cloud`}
            className="inline-block bg-stone-900 text-stone-50 px-6 md:px-8 py-3 md:py-4 text-xs sm:text-sm font-sans uppercase tracking-widest hover:bg-stone-700 transition"
          >
            {t("landing.hero_cta")} →
          </a>
        </div>
        <aside className="md:col-span-5 md:pt-8 lg:pt-10 min-w-0">
          <div className="border-l border-stone-300 pl-6 space-y-3 text-sm font-sans text-stone-600">
            <p className="uppercase tracking-widest text-stone-400 text-xs mb-4">
              System status
            </p>
            <HealthBadge app="global" label="API" />
            <HealthBadge app="cloud" label="ImmobilCloud" />
            <HealthBadge app="app" label="ImmoWeb" />
            <HealthBadge app="learn" label="Academy" />
          </div>
        </aside>
      </section>

      {/* Pillars */}
      <section className="px-5 sm:px-8 md:px-12 lg:px-16 pb-20 md:pb-24 lg:pb-32 max-w-screen-2xl mx-auto grid md:grid-cols-3 gap-6 md:gap-8 lg:gap-12">
        {pillars.map((p) => (
          <Link
            key={p.key}
            to={p.to}
            data-testid={`pillar-${p.key}`}
            className="group block p-6 md:p-7 lg:p-8 bg-white border border-stone-200 hover:border-stone-900 transition"
          >
            <p className="text-xs font-sans uppercase tracking-[0.3em] text-stone-400 mb-3 md:mb-4">
              <Brand>{p.tag}</Brand>
            </p>
            <h2 className="text-2xl md:text-2xl lg:text-3xl tracking-tight mb-3 group-hover:translate-x-1 transition-transform">
              <Brand>{p.title}</Brand>
            </h2>
            <p className="text-stone-600 leading-relaxed font-sans text-sm md:text-base">
              {p.desc}
            </p>
            <span className="inline-block mt-5 md:mt-6 text-xs sm:text-sm font-sans uppercase tracking-widest text-stone-900">
              {t("common.next")} →
            </span>
          </Link>
        ))}
      </section>

      <footer className="border-t border-stone-200">
        <div className="max-w-screen-2xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 py-6 md:py-8 text-[10px] sm:text-xs font-sans uppercase tracking-widest text-stone-500 flex flex-col sm:flex-row gap-3 sm:gap-6 sm:justify-between sm:items-center">
          <span className="flex items-center gap-2">
            <OmniaLogo variant="mark" size="sm" />
            © 2026 <Brand>OMNIA Real Estate Lab</Brand>
          </span>
          <div className="flex flex-wrap gap-4 sm:gap-6">
            <Link
              to={`/${lang}/domain-sovereignty-policy`}
              className="hover:text-stone-900 underline decoration-transparent hover:decoration-current transition"
              data-testid="footer-domain-sovereignty-link"
            >
              🛡️ {t("domain_vault.policy_link")}
            </Link>
            <Link
              to={`/${lang}/verifica-dominio`}
              className="hover:text-stone-900 underline decoration-transparent hover:decoration-current transition"
            >
              {t("domain_vault.existing_domain_verify_cta")}
            </Link>
          </div>
          <Brand className="truncate">omniarealestateecosystem.it</Brand>
        </div>
      </footer>
    </div>
  );
}
