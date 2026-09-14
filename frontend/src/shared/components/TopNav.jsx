import React from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "./LanguageSwitcher";
import MobileNav from "./MobileNav";
import Brand from "./Brand";

/**
 * Shared top navigation across all 4 OMNIA apps (Landing, Cloud, App, Learn).
 *
 * Props:
 * - current: "landing" | "cloud" | "app" | "learn" — highlights active page
 * - theme:   "light"   | "dark"  | "cream"          — color scheme variant
 * - suffix:  optional label appended to OMNIA logo (e.g. "cloud", "app", "learn")
 */
export default function TopNav({ current = "landing", theme = "light", suffix = null }) {
  const { t, i18n } = useTranslation();
  const lang = (i18n.language || "it").slice(0, 2);

  const isLanding = current === "landing";

  // Color variants per theme
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

  const navItems = [
    { key: "cloud", to: `/${lang}/cloud`, label: t("nav.immocloud") },
    { key: "app", to: `/${lang}/app`, label: t("nav.immoweb") },
    { key: "learn", to: `/${lang}/learn`, label: t("nav.academy") },
  ];

  // For mobile menu — include all items + back if internal
  const mobileLinks = [
    ...(isLanding ? [] : [{ to: `/${lang}`, label: t("nav.back_to_home") }]),
    ...navItems.map((n) => ({ to: n.to, label: n.label })),
    { to: `/${lang}/login`, label: t("nav.login") },
  ];

  return (
    <header className={`sticky top-0 z-40 backdrop-blur ${c.wrapper}`}>
      <div className="flex items-center justify-between px-5 sm:px-8 md:px-12 lg:px-16 py-4 md:py-5 max-w-screen-2xl mx-auto gap-4">
        {/* LEFT — Logo + optional back arrow */}
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
            className={`text-xl md:text-2xl tracking-tight font-medium truncate ${c.brand}`}
            style={{ fontFamily: "'Fraunces', Georgia, serif" }}
          >
            <Brand>OMNIA</Brand>
            {suffix && (
              <>
                <span className={c.suffix}>·</span>
                <Brand className={`font-light ${c.suffix}`}>{suffix}</Brand>
              </>
            )}
          </Link>
        </div>

        {/* CENTER — Cross-app nav (desktop only) */}
        <nav className="hidden lg:flex items-center gap-6 text-sm font-sans uppercase tracking-widest">
          {navItems.map((n) => (
            <Link
              key={n.key}
              to={n.to}
              data-testid={`topnav-${n.key}`}
              className={`transition ${current === n.key ? c.linkActive : c.link}`}
            >
              {n.label}
            </Link>
          ))}
        </nav>

        {/* RIGHT — Login CTA + lang switcher (desktop) */}
        <div className="hidden md:flex items-center gap-3 md:gap-4">
          <Link
            to={`/${lang}/login`}
            data-testid="topnav-login"
            className={`px-4 py-2 text-xs font-sans uppercase tracking-widest transition ${c.cta}`}
          >
            {t("nav.login")}
          </Link>
          <LanguageSwitcher />
        </div>

        {/* MOBILE hamburger */}
        <MobileNav lang={lang} links={mobileLinks} theme={theme} />
      </div>
    </header>
  );
}
