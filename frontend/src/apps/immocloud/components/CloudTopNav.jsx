import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "../../../shared/components/LanguageSwitcher";
import NotificationBell from "../../../shared/components/NotificationBell";
import { useAuth } from "../../../shared/lib/auth";

/* CloudTopNav — B2C-specific nav: Cerca casa · Valutatore · Mutui · Vendi · Area riservata */
export default function CloudTopNav() {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);
  const { user } = useAuth();
  const loggedIn = Boolean(user && user.id);
  return (
    <header className="sticky top-0 z-40 backdrop-blur-md bg-[#fbf9f5]/90 border-b border-stone-200/80">
      <div className="flex items-center justify-between px-5 sm:px-8 md:px-12 lg:px-16 py-4 max-w-screen-2xl mx-auto gap-4">
        <Link
          to={`/${lang}/cloud`}
          data-testid="cloud-topnav-logo"
          className="text-xl md:text-2xl tracking-tight font-medium text-[#0B1E3F]"
          style={{ fontFamily: "'Fraunces', Georgia, serif" }}
        >
          ImmobilCloud<sup className="text-[10px] text-[#C19A6B] ml-0.5">™</sup>
        </Link>
        <nav className="hidden md:flex items-center gap-6 text-[11px] uppercase tracking-[0.18em]">
          <Link to={`/${lang}/cloud/search`} data-testid="cloud-nav-search" className="text-stone-600 hover:text-[#0B1E3F] transition">
            {t("cloud.nav_search")}
          </Link>
          <Link to={`/${lang}/cloud/valutatore`} data-testid="cloud-nav-valuator" className="text-stone-600 hover:text-[#0B1E3F] transition">
            {t("cloud.nav_valuator")}
          </Link>
          <Link to={`/${lang}/cloud/mutui`} data-testid="cloud-nav-mutui" className="text-stone-600 hover:text-[#0B1E3F] transition">
            {t("cloud.nav_mutui")}
          </Link>
          <Link to={`/${lang}/cloud/visura`} data-testid="cloud-nav-visura" className="text-stone-600 hover:text-[#0B1E3F] transition">
            Visura
          </Link>
          <Link to={`/${lang}/cloud/register?intent=sell`} data-testid="cloud-nav-sell" className="text-stone-600 hover:text-[#0B1E3F] transition">
            {t("cloud.nav_sell")}
          </Link>
        </nav>
        <div className="flex items-center gap-3">
          {loggedIn && <NotificationBell />}
          <Link
            to={loggedIn ? `/${lang}/cloud/account` : `/${lang}/cloud/register`}
            data-testid="cloud-nav-area"
            className="px-4 py-2 text-[11px] uppercase tracking-[0.18em] bg-[#0B1E3F] text-white rounded-lg hover:bg-[#C19A6B] transition"
          >
            {loggedIn ? (t("cloud.nav_account") || "Account") : t("cloud.nav_area")}
          </Link>
          <LanguageSwitcher />
        </div>
      </div>
    </header>
  );
}
