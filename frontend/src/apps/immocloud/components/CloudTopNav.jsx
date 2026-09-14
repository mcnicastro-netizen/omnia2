import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "../../../shared/components/LanguageSwitcher";

/* CloudTopNav — B2C-specific nav: Cerca casa · Valutatore · Mutui · Vendi · Area riservata */
export default function CloudTopNav() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  return (
    <header className="sticky top-0 z-40 backdrop-blur bg-[#fbf9f5]/95 border-b border-stone-200">
      <div className="flex items-center justify-between px-5 sm:px-8 md:px-12 lg:px-16 py-4 max-w-screen-2xl mx-auto gap-4">
        <Link to={`/${lang}/cloud`} data-testid="cloud-topnav-logo"
          className="text-xl md:text-2xl tracking-tight font-medium text-stone-900"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}>
          ImmobilCloud<sup className="text-[10px] text-stone-400 ml-0.5">™</sup>
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-sm uppercase tracking-widest">
          <Link to={`/${lang}/cloud/search`} data-testid="cloud-nav-search" className="text-stone-600 hover:text-stone-900">
            {t("cloud.nav_search")}
          </Link>
          <Link to={`/${lang}/cloud/valutatore`} data-testid="cloud-nav-valuator" className="text-stone-600 hover:text-stone-900">
            {t("cloud.nav_valuator")}
          </Link>
          <Link to={`/${lang}/cloud/mutui`} data-testid="cloud-nav-mutui" className="text-stone-600 hover:text-stone-900">
            {t("cloud.nav_mutui")}
          </Link>
          <Link to={`/${lang}/cloud/register?intent=sell`} data-testid="cloud-nav-sell" className="text-stone-600 hover:text-stone-900">
            {t("cloud.nav_sell")}
          </Link>
        </nav>
        <div className="flex items-center gap-3">
          <Link to={`/${lang}/cloud/register`} data-testid="cloud-nav-area"
            className="px-4 py-2 text-xs uppercase tracking-widest bg-[#0B1E3F] text-white rounded hover:bg-[#C19A6B] transition">
            {t("cloud.nav_area")}
          </Link>
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
