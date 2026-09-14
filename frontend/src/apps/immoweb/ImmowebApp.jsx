import React from "react";
import { useTranslation } from "react-i18next";
import HealthBadge from "../../shared/components/HealthBadge";
import TopNav from "../../shared/components/TopNav";
import Brand from "../../shared/components/Brand";

export default function ImmowebApp() {
  const { t } = useTranslation();

  return (
    <div
      data-testid="immoweb-app"
      className="min-h-screen bg-stone-100 text-stone-900 overflow-x-hidden"
      style={{ fontFamily: "'Fraunces', Georgia, serif" }}
    >
      <TopNav current="app" theme="light" suffix="app" />

      <section className="px-5 sm:px-8 md:px-12 lg:px-16 py-16 md:py-20 lg:py-24 max-w-screen-2xl mx-auto">
        <div className="max-w-5xl">
          <p className="text-[10px] sm:text-xs font-sans uppercase tracking-[0.3em] text-amber-700 mb-4 md:mb-6">
            <Brand>ImmoWeb — B2B Agency CRM</Brand>
          </p>
          <h1 className="text-4xl sm:text-5xl md:text-5xl lg:text-6xl leading-[1.05] tracking-tight mb-8 md:mb-10 text-stone-900 break-words">
            {t("immoweb.tagline")}
          </h1>
          <p className="text-base sm:text-lg font-sans text-stone-600 max-w-2xl mb-8 md:mb-12 leading-relaxed">
            {t("landing.pillar_app_desc")}
          </p>
          <div className="inline-flex items-center gap-4 bg-white border border-stone-300 px-4 sm:px-6 py-3 max-w-full">
            <HealthBadge app="app" label="ImmoWeb API" />
          </div>
        </div>
      </section>

      <footer className="border-t border-stone-300">
        <div className="max-w-screen-2xl mx-auto px-5 sm:px-8 md:px-12 lg:px-16 py-6 md:py-8 text-[10px] sm:text-xs font-sans uppercase tracking-widest text-stone-500">
          © 2026 <Brand>ImmoWeb</Brand> · Coming soon: M2
        </div>
      </footer>
    </div>
  );
}
