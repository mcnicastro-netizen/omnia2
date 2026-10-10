import React from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import HealthBadge from "../../shared/components/HealthBadge";
import TopNav from "../../shared/components/TopNav";
import Brand from "../../shared/components/Brand";

/**
 * Omnia Academy — vetrina "coming soon" (S6 / C1).
 * Raggiungibile via URL diretto; fuori pitch commerciale finché M6 non esiste.
 */
export default function AcademyApp() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  return (
    <div
      data-testid="academy-app"
      className="min-h-screen bg-[#fdf6e3] text-stone-900 overflow-x-hidden"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      <TopNav current="learn" theme="cream" suffix="learn" />

      <section className="px-5 sm:px-8 md:px-12 lg:px-16 py-16 md:py-20 lg:py-24 max-w-screen-2xl mx-auto">
        <div className="max-w-5xl">
          <p
            className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-amber-800 mb-4 md:mb-6"
            data-testid="academy-eyebrow"
          >
            <Brand>Omnia Academy · Coming soon</Brand>
          </p>
          <h1
            className="text-4xl sm:text-5xl md:text-5xl lg:text-6xl leading-[1.05] tracking-tight mb-8 md:mb-10 break-words"
            data-testid="academy-title"
          >
            {t("academy.tagline")}
          </h1>
          <p
            className="text-base sm:text-lg font-sans text-stone-700 max-w-2xl mb-6 md:mb-8 leading-relaxed"
            data-testid="academy-desc"
          >
            {t("landing.pillar_learn_desc")}
          </p>
          <p className="text-sm font-sans text-stone-600 max-w-2xl mb-8 md:mb-12 leading-relaxed">
            Oggi l&apos;offerta commerciale OMNIA è{" "}
            <Brand>ImmobilCloud</Brand> (portale B2C) + <Brand>ImmoWeb</Brand>{" "}
            (gestionale AI). Academy arriverà con M6.
          </p>
          <div className="flex flex-wrap items-center gap-4 mb-8">
            <Link
              to={`/${lang}/cloud`}
              data-testid="academy-cta-cloud"
              className="inline-block bg-amber-800 text-amber-50 px-5 py-3 text-xs font-sans uppercase tracking-widest hover:bg-amber-900 transition"
            >
              ImmobilCloud
            </Link>
            <Link
              to={`/${lang}/app`}
              data-testid="academy-cta-app"
              className="inline-block border border-amber-900/30 px-5 py-3 text-xs font-sans uppercase tracking-widest text-stone-800 hover:border-amber-800 transition"
            >
              ImmoWeb
            </Link>
          </div>
          <div className="inline-flex items-center gap-4 bg-white/60 border border-amber-900/20 px-4 sm:px-6 py-3 max-w-full">
            <HealthBadge app="learn" label="Academy API" />
          </div>
        </div>
      </section>

      <footer className="border-t border-amber-900/20">
        <div
          className="max-w-screen-2xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 py-6 md:py-8 text-[10px] sm:text-xs font-sans uppercase tracking-widest text-stone-600"
          data-testid="academy-footer"
        >
          © 2026 <Brand>Omnia Academy</Brand> · Coming soon: M6 · fuori pitch GTM
        </div>
      </footer>
    </div>
  );
}
