import React, { useState } from "react";
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
  const [open, setOpen] = useState(false);
  const sellTo = loggedIn && user?.account_type === "b2c"
    ? `/${lang}/cloud/account/sell`
    : `/${lang}/cloud/register?intent=sell`;
  const links = [
    { to: `/${lang}/cloud/search`, testid: "cloud-nav-search", label: t("cloud.nav_search") },
    { to: `/${lang}/cloud/valutatore`, testid: "cloud-nav-valuator", label: t("cloud.nav_valuator") },
    { to: `/${lang}/cloud/mutui`, testid: "cloud-nav-mutui", label: t("cloud.nav_mutui") },
    { to: `/${lang}/cloud/visura`, testid: "cloud-nav-visura", label: t("cloud.nav_visura") },
    { to: sellTo, testid: "cloud-nav-sell", label: t("cloud.nav_sell") },
    { to: `/${lang}/legal`, testid: "cloud-nav-legal", label: t("cloud.nav_legal") },
  ];
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
          {links.map((l) => (
            <Link key={l.testid} to={l.to} data-testid={l.testid} className="text-stone-600 hover:text-[#0B1E3F] transition">
              {l.label}
            </Link>
          ))}
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
          <button
            type="button"
            data-testid="cloud-nav-menu"
            aria-expanded={open}
            aria-label="Menu"
            className="md:hidden px-3 py-2 text-[11px] uppercase tracking-[0.18em] border border-stone-300 rounded-lg text-[#0B1E3F]"
            onClick={() => setOpen((v) => !v)}
          >
            Menu
          </button>
        </div>
      </div>
      {open && (
        <nav
          data-testid="cloud-nav-mobile"
          className="md:hidden border-t border-stone-200 px-5 py-3 flex flex-col gap-3 text-[11px] uppercase tracking-[0.18em] bg-[#fbf9f5]"
        >
          {links.map((l) => (
            <Link
              key={`m-${l.testid}`}
              to={l.to}
              data-testid={`${l.testid}-mobile`}
              className="text-stone-700 py-1"
              onClick={() => setOpen(false)}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}
