import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "./LanguageSwitcher";
import MobileNav from "./MobileNav";
import Brand from "./Brand";
import OmniaLogo from "./OmniaLogo";

/**
 * Shared top navigation across Landing, App, Learn.
 *
 * Home (landing): logo + Cerca casa · Vendi casa · Area riservata
 * App / Learn: logo + prodotti (+ suffix opzionale)
 */
export default function TopNav({ current = "landing", theme = "light", suffix = null }) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const isLanding = current === "landing";

  const themes = {
    light: {
      wrapper: "border-b border-stone-200 bg-stone-50/95",
      brand: "text-stone-900",
      suffix: "text-stone-400",
      link: "text-stone-600 hover:text-stone-900",
      linkActive: "text-stone-900 font-semibold",
      cta: "bg-stone-900 text-stone-50 hover:bg-stone-700",
      back: "text-stone-500 hover:text-stone-900",
    },
    dark: {
      wrapper: "border-b border-stone-800 bg-[#0e1419]/95",
      brand: "text-stone-100",
      suffix: "text-stone-500",
      link: "text-stone-400 hover:text-stone-100",
      linkActive: "text-stone-100 font-semibold",
      cta: "bg-stone-100 text-stone-900 hover:bg-white",
      back: "text-stone-500 hover:text-stone-200",
    },
    cream: {
      wrapper: "border-b border-amber-900/20 bg-[#fdf6e3]/95",
      brand: "text-stone-900",
      suffix: "text-amber-700",
      link: "text-stone-700 hover:text-amber-800",
      linkActive: "text-amber-800 font-semibold",
      cta: "bg-amber-800 text-amber-50 hover:bg-amber-900",
      back: "text-stone-600 hover:text-amber-800",
    },
  };
  const c = themes[theme] || themes.light;

  const landingItems = [
    {
      key: "search",
      to: `/${lang}/cloud/search`,
      label: t("cloud.nav_search"),
      testid: "topnav-search",
    },
    {
      key: "sell",
      to: `/${lang}/cloud/register?intent=sell`,
      label: t("cloud.nav_sell"),
      testid: "topnav-sell",
    },
  ];

  const productItems = [
    { key: "cloud", to: `/${lang}/cloud`, label: t("nav.immocloud"), testid: "topnav-cloud" },
    { key: "app", to: `/${lang}/app`, label: t("nav.immoweb"), testid: "topnav-app" },
  ];

  const navItems = isLanding ? landingItems : productItems;
  const ctaTo = isLanding ? `/${lang}/cloud/register` : `/${lang}/login`;
  const ctaLabel = isLanding ? t("cloud.nav_area") : t("nav.login");
  const ctaTestId = isLanding ? "topnav-area" : "topnav-login";

  const mobileLinks = [
    ...(isLanding ? [] : [{ to: `/${lang}`, label: t("nav.back_to_home") }]),
    ...navItems.map((n) => ({ to: n.to, label: n.label })),
    { to: ctaTo, label: ctaLabel },
  ];

  return (
    <header className={`sticky top-0 z-40 backdrop-blur ${c.wrapper}`}>
      <div className="flex items-center justify-between px-5 sm:px-8 md:px-12 lg:px-16 py-4 md:py-5 max-w-screen-2xl mx-auto gap-4">
        <div className="flex items-center gap-4 md:gap-6 min-w-0">
          {!isLanding && (
            <Link
              to={`/${lang}`}
              data-testid="topnav-back"
              className={`hidden md:inline-flex items-center gap-1 text-xs font-sans uppercase tracking-widest ${c.back} transition`}
              title={t("nav.back_to_home")}
            >
              <span aria-hidden="true">←</span>
              <span>{t("common.back")}</span>
            </Link>
          )}

          <Link
            to={`/${lang}`}
            data-testid="topnav-logo"
            className={`inline-flex items-center gap-2 min-w-0 ${c.brand}`}
            aria-label="OMNIA"
          >
            <OmniaLogo
              variant="full"
              size="md"
              inverted={theme === "dark"}
            />
            {suffix && (
              <span
                className={`hidden sm:inline text-sm font-sans tracking-widest uppercase ${c.suffix}`}
                style={{ fontFamily: "'Fraunces', Georgia, serif" }}
              >
                <span className={c.suffix}>·</span>{" "}
                <Brand className={`font-light ${c.suffix}`}>{suffix}</Brand>
              </span>
            )}
          </Link>
        </div>

        <nav className="hidden lg:flex items-center gap-6 text-sm font-sans uppercase tracking-widest">
          {navItems.map((n) => (
            <Link
              key={n.key}
              to={n.to}
              data-testid={n.testid}
              className={`transition ${current === n.key ? c.linkActive : c.link}`}
            >
              {n.label}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-3 md:gap-4">
          <Link
            to={ctaTo}
            data-testid={ctaTestId}
            className={`px-4 py-2 text-xs font-sans uppercase tracking-widest transition ${c.cta}`}
          >
            {ctaLabel}
          </Link>
          <LanguageSwitcher />
        </div>

        <MobileNav lang={lang} links={mobileLinks} theme={theme} />
      </div>
    </header>
  );
}
